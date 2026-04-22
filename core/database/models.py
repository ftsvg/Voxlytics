from typing import Any
from dataclasses import dataclass


@dataclass(slots=True)
class User:
    discord_id: int
    uuid: str


@dataclass(slots=True)
class Session:
    uuid: str
    wins: str
    weighted: str
    kills: int
    finals: int
    beds: int
    star: int
    xp: int
    start_time: int


@dataclass(slots=True)
class Historical:
    uuid: str
    period: str
    wins: str
    weighted: str
    kills: int
    finals: int
    beds: int
    star: int
    xp: int
    last_reset: int


@dataclass(slots=True)
class LeaderboardChannel:
    guild_id: int
    channel_id: int


@dataclass(slots=True)
class LeaderboardSnapshot:
    type: str
    data: dict[str, Any]
    updated_at: int


@dataclass(slots=True)
class Milestone:
    id: int
    discord_id: int
    uuid: str
    type: str
    value: int
    threshold: int
    notified: bool