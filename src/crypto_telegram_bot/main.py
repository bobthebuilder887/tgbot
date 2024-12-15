import asyncio
import logging
import re
import sys
import threading
import time
from pathlib import Path

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

CFG = ScriptConfig.from_json(Path("config.json"))

CONTRACT_PATTERNS: dict[str, str] = {
    "EVM": (EVM := r"0x[a-fA-F0-9]{40}"),
    "SOL": (SOL := r"[1-9A-HJ-NP-Za-km-z]{32,44}"),
    "MOVE": (MOVE := r"0x[a-fA-F0-9]{64}::[a-zA-Z0-9_]+::[a-zA-Z0-9_]+"),
    "TON": (TON := r"EQ[A-Za-z0-9_-]{46}"),
    "XRP": (XRP := r"[A-F0-9]{40}\.r[1-9A-HJ-NP-Za-km-z]{24,34}"),
    "TRX": (TRX := r"T[A-Za-z1-9]{33}"),
}

COIN_PATTERNS: tuple[str, ...] = (
    SCAN := r"^/z",
    CHART := r"^/cc",
    TICKER := r"\$[A-z0-9]+",
)

ALL_PATTERNS = tuple(list(CONTRACT_PATTERNS.values()) + list(COIN_PATTERNS))

IGNORE_CMDS: tuple[str, ...] = (
    r"/s",
    r"/ask",
    r"/nh",
    r"/find",
    r"/first",
    r"/fa",
)

RICK_BOT: int = 6126376117
FIRST_TIME: str = r"💨 You are first"

# Store all contracts in one place
CONTRACTS_SEEN = set()
if Path("contracts_seen.txt").is_file():
    with open("contracts_seen.txt", "r") as f:
        CONTRACTS_SEEN.update(f.read().splitlines())


class Active:
    ACTIVE: bool = True


def update_ca_file() -> None:
    OLD_N_SEEN = len(CONTRACTS_SEEN)
    try:
        logger.info("THREAD IS ACTIVE")
        while Active.ACTIVE:
            N_SEEN = len(CONTRACTS_SEEN)
            if N_SEEN != OLD_N_SEEN:
                size = sys.getsizeof(CONTRACTS_SEEN)
                logger.info(f"{len(CONTRACTS_SEEN)} contracts seen ({size / 1000:.2f} kB)")
                if size > 10_000_000:
                    logger.warning("Contracts seen file is getting large!")
                with open("contracts_seen.txt", "w") as f:
                    f.write("\n".join(CONTRACTS_SEEN))
                OLD_N_SEEN = N_SEEN

            time.sleep(10)
    except Exception as e:
        logger.error(e)
    finally:
        logger.info("Contracts seen file update stopped")


def find_contracts(text: str) -> dict[str, set[str]]:
    new_ca_dict = dict()
    for chain, pattern in CONTRACT_PATTERNS.items():
        # Look for the rick contract line
        if FIRST_TIME in text:
            pattern = f"`{pattern}`"

        cas = set(ca.strip("`") for ca in re.findall(pattern=pattern, string=text))

        if cas:
            new_cas = cas.difference(CONTRACTS_SEEN)
            new_ca_dict[chain] = new_cas
            CONTRACTS_SEEN.update(new_cas)

    return new_ca_dict


client = TelegramClient(
    session=CFG.session_name,
    api_id=CFG.api_id,
    api_hash=CFG.api_hash,
)


BOTS = {
    "SOL": (CFG.sol_bot_1, CFG.sol_bot_2),
    "EVM": (CFG.evm_bot_1, CFG.evm_bot_2),
}


async def send_msg(text: str, client, entity_id: int) -> None:
    await client.send_message(entity=entity_id, message=text)
    bot_name = CFG.all_ids.get(entity_id, "unknown")
    logger.info(f"{text} sent to {bot_name} ({entity_id})")


async def fwd_msg(message, client) -> None:
    await client.forward_messages(CFG.fwd_group.id, message)
    logger.info(f"Message forwarded to {CFG.fwd_group}: {message.text}")


def schedule_forward_cas(message) -> list:
    tasks = []
    if not message.text:
        return tasks
    new_cas_dict = find_contracts(message.text)
    for chain, cas in new_cas_dict.items():
        if chain not in BOTS:
            continue
        # TODO: this can be where strategies go
        for ca in cas:
            tasks.append(send_msg(ca, client, BOTS[chain][0].id))
            # tasks.append(forward_msg(text, client, BOTS[chain][1]))
    return tasks


logging.info("Launching Tg Bot...")


@client.on(events.NewMessage(chats=CFG.tracked_ids))
async def forward_messages(event):
    """
    Forward messages to fwd group and bots that contain crypto-token related patterns
    """
    msg = event.message

    user_id = getattr(getattr(msg, "from_id", False), "user_id", False)
    if user_id in CFG.ignored_ids:
        return

    for cmd in IGNORE_CMDS:
        if msg.text.startswith(cmd):
            return

    tasks = schedule_forward_cas(msg)

    for pattern in ALL_PATTERNS:
        if re.findall(pattern=pattern, string=msg.text):
            tasks.append(fwd_msg(msg, client))
            break

    await asyncio.gather(*tasks)


@client.on(events.NewMessage(chats=CFG.fwd_group.id, from_users=RICK_BOT))
async def last_resort_fwd_bot(event):
    """
    If contract not detected in initial method, see if rick bot caught it in the fwd group
    """
    msg = event.message
    if FIRST_TIME in msg.text:
        tasks = schedule_forward_cas(msg)
        await asyncio.gather(*tasks)


def main() -> None:
    # thread for continously storing seen contracts
    thread = threading.Thread(target=update_ca_file)
    thread.start()

    try:
        with client:
            client.run_until_disconnected()
    except Exception as e:
        logger.error(e, exc_info=True)
    finally:
        logger.info("Tg Bot stopped")
        Active.ACTIVE = False
        thread.join()


if __name__ == "__main__":
    main()
