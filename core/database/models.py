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