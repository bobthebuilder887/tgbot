import dataclasses
import json
from pathlib import Path
from typing import NamedTuple, Self


class TgId(NamedTuple):
    id: int
    name: str


@dataclasses.dataclass
class ScriptConfig:
    api_id: int
    api_hash: str
    session_name: str
    test_session_name: str
    source_groups: list[TgId]
    source_channels: list[TgId]
    ignore_ids: list[TgId]
    fwd_group: TgId
    sol_bot_1: TgId
    sol_bot_2: TgId
    evm_bot_1: TgId
    evm_bot_2: TgId
    all_ids: dict = dataclasses.field(init=False)

    def __post_init__(self):
        self.all_ids = {}

        for g in self.source_groups:
            self.all_ids[g.id] = g.name

        for c in self.source_channels:
            self.all_ids[c.id] = c.name

        for i in self.ignore_ids:
            self.all_ids[i.id] = i.name

        self.all_ids[self.sol_bot_1.id] = self.sol_bot_1.name
        self.all_ids[self.sol_bot_2.id] = self.sol_bot_2.name
        self.all_ids[self.evm_bot_1.id] = self.evm_bot_1.name
        self.all_ids[self.evm_bot_2.id] = self.evm_bot_2.name

        self.all_ids[self.fwd_group.id] = self.fwd_group.name

    @property
    def tracked_ids(self) -> list[int]:
        return [t.id for t in self.source_channels + self.source_groups]

    @property
    def ignored_ids(self) -> list[int]:
        return [t.id for t in self.ignore_ids]

    @classmethod
    def from_json(cls, path: Path = Path("config.json")) -> Self:
        with open(path, "r") as json_file:
            cfg = json.loads(json_file.read())

        ignore_ids = [TgId(**u) for u in cfg["Groups"]["ignore_ids"]]
        source_channels = [TgId(**u) for u in cfg["Groups"]["source_channels"]]
        source_groups = [TgId(**u) for u in cfg["Groups"]["source_groups"]]

        return cls(
            api_id=cfg["Telegram"]["api_id"],
            api_hash=cfg["Telegram"]["api_hash"],
            session_name=cfg["Telegram"]["session_name"],
            test_session_name=cfg["Telegram"]["test_session_name"],
            source_groups=source_groups,
            source_channels=source_channels,
            ignore_ids=ignore_ids,
            fwd_group=TgId(**cfg["Groups"]["fwd_group"]),
            sol_bot_1=TgId(**cfg["Bots"]["sol_bot_1"]),
            sol_bot_2=TgId(**cfg["Bots"]["sol_bot_2"]),
            evm_bot_1=TgId(**cfg["Bots"]["evm_bot_1"]),
            evm_bot_2=TgId(**cfg["Bots"]["evm_bot_2"]),
        )


def auth_cli():
    import argparse

    from telethon.sync import TelegramClient

    parser = argparse.ArgumentParser(description="Authorize TelegramClient")
    parser.add_argument(
        "-c",
        "--config-path",
        type=str,
        default="config.json",
        help="config path, defaults to config.json",
    )
    parser.add_argument(
        "-s",
        "--session-name",
        type=str,
        default="",
        help="Session name, defaults to config main session",
    )
    args = parser.parse_args()

    CFG = ScriptConfig.from_json(Path(args.config_path))

    client = TelegramClient(CFG.session_name, CFG.api_id, CFG.api_hash)
    client.start()
    client.disconnect()
