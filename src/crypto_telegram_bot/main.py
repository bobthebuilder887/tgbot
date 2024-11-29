import argparse
import asyncio
import datetime
import logging
import re
from typing import Literal

import pytz
from telethon import TelegramClient, events

from crypto_telegram_bot.config import ScriptConfig

# Set up logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    filename="tgbot.log",
    filemode="a",
)
logger = logging.getLogger(__name__)

parser = argparse.ArgumentParser(description="Crypto Telegram Bot")

parser.add_argument(
    "-c",
    "--config-path",
    type=str,
    default="config.json",
    help="config path, defaults to config.json",
)


args = parser.parse_args()

APE_CALL_CENTER = -1001938981479

AVAILABLE_CHAINS = ("ethereum", "solana", "base")

CFG = ScriptConfig.from_json(args.config_path)

MESSAGE_PATTERNS: list[str] = [
    TICKER := r"\$[A-z0-9]+",
    EVM := r"0x[a-fA-F0-9]{40}",
    SOL := r"[1-9A-HJ-NP-Za-km-z]{32,44}",
    SCAN := r"^/z",
    CHART := r"^/cc",
    MOVE := r"0x[a-fA-F0-9]{64}::[a-zA-Z0-9_]+::[a-zA-Z0-9_]+",
    TON := r"EQ[A-Za-z0-9_-]{46}",
]

IGNORE_CMDS: list[str] = [
    r"/s",
    r"/ask",
    r"/nh",
    r"/find",
    r"/first",
    r"/fa",
]

RICK_BOT: int = 6126376117
FIRST_TIME: str = r"💨 You are first"


IGNORED_IDS = CFG.ignored_ids

APE_CALL_CENTER = -1001938981479
PATTERN = r"# X Called:"
WIN_RATE = 40
parsed_cas = set()

IGNORE_CALLS = ("@wouldcalls",)


def find_ca(msg_str: str) -> str:
    ca = ""
    for line in msg_str.split("\n"):
        if "CA: " in line:
            ca = line.split()[-1].strip()
            break
    return ca


def find_chain(msg_str: str) -> str:
    chain = ""
    for line in msg_str.split("\n"):
        if "Chain" in line:
            chain = line.split()[-1].strip().lower()
            break
    return chain


def find_2x(msg_str: str) -> float:
    rate = 0
    for line in msg_str.split("\n"):
        if "2x Wins" in line:
            rate = line.split()[-2].strip("%")
            break
    return float(rate)


def find_caller(msg_str: str) -> str:
    caller = ""
    for line in msg_str.split("\n"):
        if "New from" in line:
            caller = line.split()[-2].strip()
    return caller


def parse_ape(message) -> tuple | Literal[False]:
    # Check if the msg is of a call
    text = message.raw_text
    if PATTERN not in text:
        return False

    # Find the contract
    ca = find_ca(text)

    # Find the chain and check if it is possible to buy
    chain = find_chain(text)
    if chain not in AVAILABLE_CHAINS:
        return False

    # Make sure the winrate is above 40% threshold
    rate = find_2x(text)
    if rate <= WIN_RATE:
        return False

    caller = find_caller(text)
    if caller in IGNORE_CALLS:
        return False

    return ca, chain, rate, caller


def get_entity_id(msg) -> int:
    user_id = getattr(getattr(msg, "from_id", -1), "user_id", -1)

    if user_id == -1:
        return getattr(getattr(msg, "from_id", -1), "channel_id", -1)
    else:
        return user_id


def get_fwd_id(msg) -> int:
    fwd_msg = getattr(msg, "fwd_from", -1)

    return get_entity_id(fwd_msg)


def check_time(start: int, end: int) -> bool:
    tz = pytz.timezone("UTC")
    now = datetime.datetime.now(tz)
    hour = now.hour
    return hour in range(start, end + 1)


client = TelegramClient(CFG.session_name, CFG.api_id, CFG.api_hash)


async def forward_eth(text: str, client, bot_id: int) -> None:
    ca = re.findall(rf"`{EVM}`", text)

    if not ca:
        return

    ca = ca[0].strip("`")

    await client.send_message(entity=bot_id, message=ca)
    bot_name = CFG.all_ids.get(bot_id, "unknown")
    logger.info(f"Contract ({ca}) forwarded to {bot_name} ({bot_id})")


async def forward_sol(text: str, client, bot_id: int) -> None:
    ca = re.findall(rf"`{SOL}`", text)

    if not ca:
        return

    ca = ca[0].strip("`")

    await client.send_message(entity=bot_id, message=ca)
    bot_name = CFG.all_ids.get(bot_id, "unknown")
    logger.info(f"Contract ({ca}) forwarded to {bot_name} ({bot_id})")


logging.info("Launching Tg Bot. The following settings are active:")


if CFG.aggregate:
    # Aggregate all Channel and group contract posts (excludes specified users)
    channel_str = "\n".join(str(g) for g in CFG.source_channels)
    group_str = "\n".join(str(g) for g in CFG.source_groups)
    ignore_str = "\n".join(str(g) for g in CFG.ignore_ids)

    logging.info(f"\nAggregating all contracts to {CFG.fwd_group}")
    logging.info(f"from channels:{channel_str}")
    logging.info(f"from groups:{group_str}")
    logging.info(f"ignoring users:{ignore_str}")
    logging.info(f"Parsing APE CENTRE CALLS ABOVE {WIN_RATE}% 2x hitrate")

    @client.on(events.NewMessage(chats=CFG.tracked_ids))
    async def forward_messages(event):
        """
        Forward messages to fwd group that contain crypto-token related patterns
        """
        msg = event.message

        user_id = getattr(getattr(msg, "from_id", False), "user_id", False)
        if user_id in CFG.ignored_ids:
            return

        for cmd in IGNORE_CMDS:
            if msg.text.startswith(cmd):
                return

        for pattern in MESSAGE_PATTERNS:
            if re.search(pattern, msg.text):
                await client.forward_messages(CFG.fwd_group.id, msg)
                logger.info(f"Message forwarded to {CFG.fwd_group}: {msg.text}")
                break

    @client.on(
        events.NewMessage(
            chats=APE_CALL_CENTER,
        )
    )
    async def auto_fwd_ape(event) -> None:
        msg = event.message
        ape = parse_ape(msg)
        if not ape:
            return
        else:
            ca, chain, rate, caller = ape
            await client.send_message(
                entity=CFG.fwd_group.id,
                message=f"New call from Ape's Call Center:\nCaller: {caller}\nChain: {chain}\n2X last 7d: {rate}%\nCA: {ca}",
            )


if CFG.fwd_aggregate:
    # Strategy that forwards all fresh contracts from wfwd group at specified times
    logging.info(f"\nForwarding all fresh contracts from {CFG.fwd_group}")
    logging.info(f"- Forwarding from {CFG.start_h_utc} to {CFG.end_h_utc}")
    logging.info(f"- Forwarding to {CFG.sol_bot_1} and {CFG.evm_bot_1}\n")

    @client.on(
        events.NewMessage(
            chats=CFG.fwd_group.id,
            from_users=RICK_BOT,
        )
    )
    async def auto_buy_rick(event) -> None:
        """
        Forward new sol and evm contracts from fwd group to tg bots
        """
        if not check_time(start=CFG.start_h_utc, end=CFG.end_h_utc):
            return

        if FIRST_TIME not in event.message.raw_text:
            return

        logger.info(f"First time ca detected in {CFG.fwd_group}:\n{event.message.raw_text}")

        tasks = [
            forward_eth(event.message.text, client=client, bot_id=CFG.evm_bot_1.id),
            forward_sol(event.message.text, client=client, bot_id=CFG.sol_bot_1.id),
        ]

        await asyncio.gather(*tasks)


if CFG.fwd_bots:
    # Strategy that forwards all fresh contracts of whitelisted users from source groups
    group_str = "\n".join(str(g) for g in CFG.source_groups)
    user_str = "\n".join(str(u) for u in CFG.always_forward)
    logging.info(f"Forwarding fresh contracts from whitelisted users in: {group_str}")
    logging.info(f"- Forwarding from users: {user_str}")
    logging.info(f"- Forwarding to {CFG.sol_bot_2} and {CFG.evm_bot_2}\n")

    @client.on(
        events.NewMessage(
            chats=[g.id for g in CFG.source_groups],
            from_users=RICK_BOT,
        )
    )
    async def auto_buy_whitelist(event) -> None:
        """
        fwd contracts to auto buy new whitelisted user shills
        """
        if FIRST_TIME not in event.message.raw_text:
            return

        reply_msg = await event.message.get_reply_message()
        user_id = get_entity_id(reply_msg)

        if user_id not in CFG.fwd_ids and check_time(
            start=CFG.start_h_utc,
            end=CFG.end_h_utc,
        ):
            return
        user_name = CFG.all_ids.get(user_id, "unknown")
        group_name = CFG.all_ids.get(event.message.chat_id, "unknown")
        chat_id = event.message.chat_id
        logger.info(
            f"First time ca post detected by {user_name} ({user_id}) in {group_name} ({chat_id})")

        tasks = [
            forward_eth(event.message.text, client=client, bot_id=CFG.evm_bot_2.id),
            forward_sol(event.message.text, client=client, bot_id=CFG.sol_bot_2.id),
        ]

        await asyncio.gather(*tasks)


def main() -> None:
    with client:
        client.run_until_disconnected()


if __name__ == "__main__":
    main()
