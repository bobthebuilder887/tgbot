import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Union

from telethon import TelegramClient
from telethon.tl.functions.channels import GetFullChannelRequest
from telethon.tl.functions.messages import ExportChatInviteRequest, GetFullChatRequest
from telethon.tl.types import Channel, Chat, User

from crypto_telegram_bot.config import ScriptConfig

# Set up logging
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

cfg = ScriptConfig.from_json()
SESSION = cfg.test_session_name


class GroupLister:
    def __init__(self, api_id: str, api_hash: str):
        self.client = TelegramClient(SESSION, api_id, api_hash)

    async def start(self):
        """Start the client session"""
        await self.client.start()

    async def get_all_groups(self) -> List[Dict]:
        """
        Get all groups the user is part of, including private groups,
        supergroups, and channels
        """
        groups = []
        async for dialog in self.client.iter_dialogs():
            entity = dialog.entity

            # Skip users and bots
            if isinstance(entity, User):
                continue

            # Get basic info
            basic_info = {
                "id": entity.id,
                "name": dialog.name,
                "unread_count": dialog.unread_count,
                "last_message_date": dialog.date.isoformat() if dialog.date else None,
                "type": self._get_chat_type(entity),
                "member_count": 0,  # Will be updated if accessible
                "username": getattr(entity, "username", None),
                "invite_link": None,  # Will be updated if available
                "is_private": not bool(getattr(entity, "username", None)),
            }

            try:
                # Try to get full chat information
                if isinstance(entity, Channel):
                    full_chat = await self.client(GetFullChannelRequest(entity))
                    basic_info["member_count"] = full_chat.full_chat.participants_count

                    # Try to get invite link if it's private
                    if basic_info["is_private"]:
                        try:
                            invite_link = await self.client(ExportChatInviteRequest(entity))
                            basic_info["invite_link"] = invite_link.link
                        except Exception:
                            pass

                elif isinstance(entity, Chat):
                    full_chat = await self.client(GetFullChatRequest(entity.id))
                    basic_info["member_count"] = len(full_chat.participants.participants)

            except Exception as e:
                logger.warning(f"Couldn't get full info for {dialog.name}: {str(e)}")

            groups.append(basic_info)

        return groups

    def _get_chat_type(self, entity: Union[Channel, Chat]) -> str:
        """Determine the type of chat"""
        if isinstance(entity, Channel):
            return "channel" if entity.broadcast else "supergroup"
        return "group"

    async def export_groups(self, output_file: Optional[str] = None) -> None:
        """
        Export group information to a file
        """
        groups = await self.get_all_groups()

        # Sort groups by type and name
        groups.sort(key=lambda x: (x["type"], x["name"]))

        # Prepare output data
        output = {
            "export_date": datetime.now().isoformat(),
            "total_groups": len(groups),
            "private_groups": len([g for g in groups if g["is_private"]]),
            "public_groups": len([g for g in groups if not g["is_private"]]),
            "groups": groups,
        }

        # Default filename if none provided
        if not output_file:
            output_file = "telegram_groups.json"

        # Ensure the output directory exists
        Path(output_file).parent.mkdir(parents=True, exist_ok=True)

        # Write to file
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(output, f, indent=2, ensure_ascii=False)

        logger.info(f"Exported {len(groups)} groups to {output_file}")

        # Print summary
        print("\nGroup Summary:")
        print(f"Total Groups: {output['total_groups']}")
        print(f"Private Groups: {output['private_groups']}")
        print(f"Public Groups: {output['public_groups']}")
        print("\nGroups by Type:")

        # Count by type
        type_counts = {}
        for group in groups:
            type_counts[group["type"]] = type_counts.get(group["type"], 0) + 1

        for type_name, count in type_counts.items():
            print(f"{type_name.capitalize()}: {count}")


async def async_main():
    # Load config
    cfg = ScriptConfig.from_json(Path("config.json"))
    # Initialize and start the group lister
    lister = GroupLister(str(cfg.api_id), cfg.api_hash)
    await lister.start()
    # Export groups
    await lister.export_groups()


def main():
    asyncio.run(async_main())


if __name__ == "__main__":
    main()
