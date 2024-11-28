import argparse
import logging

from telethon.sync import TelegramClient
from telethon.tl.functions.channels import GetFullChannelRequest
from telethon.tl.types import Channel, Chat, InputPeerChannel, PeerChannel, User

from crypto_telegram_bot.config import ScriptConfig

# Set up logging
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.WARNING)
logger = logging.getLogger(__name__)


def get_chat_info(client, chat_identifier) -> dict:
    """
    Get information about a chat/channel/user from various identifiers

    Args:
        chat_identifier (str): Can be:
            - Username (@username)
            - Invite link (https://t.me/...)
            - Chat ID (-100...)
            - Raw channel ID (without -100)
    """
    try:
        # Clean up the input
        chat_identifier = chat_identifier.strip()

        # Handle different types of identifiers
        entity = None

        try:
            # First try direct channel ID approach
            if chat_identifier.startswith("-100"):
                channel_id = int(chat_identifier[4:])
                entity = client.get_entity(PeerChannel(channel_id))
            elif chat_identifier.isdigit():
                # If just numbers are provided, assume it's a channel ID without -100
                channel_id = int(chat_identifier)
                entity = client.get_entity(PeerChannel(channel_id))
            elif chat_identifier.startswith("https://t.me/"):
                # Handle invite links
                entity = client.get_entity(chat_identifier)
            else:
                # Try as username or other identifier
                entity = client.get_entity(chat_identifier)

        except ValueError as e:
            # If the first attempt fails, try alternative approaches
            if "Could not find the input entity" in str(e):
                try:
                    # Try constructing peer manually
                    if chat_identifier.startswith("-100"):
                        channel_id = int(chat_identifier[4:])
                        access_hash = 0  # We don't know the access_hash
                        input_peer = InputPeerChannel(channel_id, access_hash)
                        entity = client.get_entity(input_peer)
                except Exception as inner_e:
                    logger.error(f"Failed to get entity using alternative method: {inner_e}")
                    raise
            else:
                raise

        if entity:
            if isinstance(entity, (Channel, Chat)):
                try:
                    # Try to get full chat information
                    if isinstance(entity, Channel):
                        full_chat = client(GetFullChannelRequest(entity))
                        participants_count = full_chat.full_chat.participants_count
                    else:
                        # For regular groups, we might need different approach
                        participants_count = None
                except Exception as e:
                    logger.warning(f"Couldn't get participant count: {e}")
                    participants_count = None

                result = {
                    "id": f"-100{entity.id}" if isinstance(entity, Channel) else f"-{entity.id}",
                    "title": entity.title,
                    "type": _get_chat_type(entity),
                    "username": getattr(entity, "username", None),
                    "participants_count": participants_count,
                    "broadcast": getattr(entity, "broadcast", False),
                    "megagroup": getattr(entity, "megagroup", False),
                    "is_private": not bool(getattr(entity, "username", None)),
                }
            elif isinstance(entity, User):
                result = {
                    "id": entity.id,
                    "first_name": entity.first_name,
                    "last_name": entity.last_name,
                    "username": entity.username,
                    "type": "user",
                    "is_private": True,
                }
            else:
                result = {}

            return result

    except Exception as e:
        logger.error(f"Error getting chat info: {str(e)}")
        return {}
    return {}


def _get_chat_type(entity):
    """Determine the type of chat"""
    if isinstance(entity, Channel):
        return "channel" if entity.broadcast else "supergroup"
    return "group"


def get_user_info_cli():
    parser = argparse.ArgumentParser(description="Telegram ID Helper")

    parser.add_argument(
        "-c",
        "--config-path",
        type=str,
        default="config.json",
        help="config path, defaults to config.json",
    )

    args = parser.parse_args()
    cfg = ScriptConfig.from_json(args.config_path)

    print("Telegram ID Helper:")
    try:
        with TelegramClient(cfg.test_session_name, cfg.api_id, cfg.api_hash) as client:
            while True:
                chat_identifier = input("\nEnter chat identifier (ID, username, or link): ")
                result = get_chat_info(client, chat_identifier)
                if result:
                    print("\nResults:")
                    for key, value in result.items():
                        print(f"{key}: {value}")
                else:
                    print("\nCould not find chat/channel/user with that identifier")
    except KeyboardInterrupt:
        pass
