import json
from telethon.sync import TelegramClient
from telethon.tl.types import Channel, Chat


def get_telegram_groups(api_id, api_hash, phone_number, session_name):
    """
    Fetches all Telegram groups/channels and saves their info to a JSON file
    """

    # Create the client
    client = TelegramClient(session_name, api_id, api_hash)

    try:
        # Start the client
        client.start(phone=phone_number)
        print("Successfully connected to Telegram!")

        # Get all dialogs (chats, groups, channels)
        dialogs = client.get_dialogs()

        groups_data = []

        for dialog in dialogs:
            entity = dialog.entity

            # Check if it's a group or channel (not a private chat)
            if isinstance(entity, (Channel, Chat)):
                group_info = {
                    "id": entity.id,
                    "name": entity.title,
                    "type": "channel" if isinstance(entity, Channel) else "group",
                    "is_private": getattr(entity, "access_hash", None) is not None,
                    "participant_count": getattr(entity, "participants_count", "N/A"),
                }

                # Additional info for channels
                if isinstance(entity, Channel):
                    group_info["is_broadcast"] = entity.broadcast
                    group_info["is_megagroup"] = entity.megagroup
                    group_info["username"] = getattr(entity, "username", None)

                groups_data.append(group_info)
                print(f"Found: {group_info['name']} (ID: {group_info['id']})")

        # Save to JSON file
        with open("telegram_groups.json", "w", encoding="utf-8") as f:
            json.dump(groups_data, f, indent=2, ensure_ascii=False)

        print(f"\nSuccessfully saved {len(groups_data)} groups to 'telegram_groups.json'")

        return groups_data

    except Exception as e:
        print(f"An error occurred: {e}")
        return None

    finally:
        # Close the client
        client.disconnect()


def main():
    """
    Main function to run the script
    """
    print("Telegram Groups Extractor")
    print("=" * 30)

    # Load configuration from JSON file
    try:
        with open("config.json", "r", encoding="utf-8") as f:
            config = json.load(f)["Telegram"]

        api_id = config.get("api_id")
        api_hash = config.get("api_hash")
        phone_number = config.get("phone_number")
        session_name = config.get("session_name")

        # Validate required fields
        if not api_id or not api_hash or not phone_number:
            print("Error: Missing required fields in config.json")
            print("Required fields: api_id, api_hash, phone_number")
            return

    except FileNotFoundError:
        print("Error: config.json file not found!")
        print("Please create a config.json file with your Telegram API credentials.")
        print("Example format:")
        print("{")
        print('  "api_id": 12345678,')
        print('  "api_hash": "your_api_hash_here",')
        print('  "phone_number": "+1234567890"')
        print("}")
        return
    except json.JSONDecodeError:
        print("Error: Invalid JSON format in config.json")
        return
    except Exception as e:
        print(f"Error reading config file: {e}")
        return

    groups = get_telegram_groups(api_id, api_hash, phone_number, session_name)

    if groups:
        print(f"\nExtracted {len(groups)} groups/channels:")
        for group in groups[:5]:  # Show first 5 as preview
            print(f"- {group['name']} ({group['type']})")
        if len(groups) > 5:
            print(f"... and {len(groups) - 5} more")


if __name__ == "__main__":
    main()
