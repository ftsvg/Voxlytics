from dataclasses import dataclass
from datetime import date


@dataclass(slots=True)
class ServerConfig:
    server_id: int
    chart_logs: int
    max_guilds: int


@dataclass(slots=True)
class TrackedServerGuilds:
    id: int
    server_id: int
    guild_id: int
    log_channel_id: int


@dataclass(slots=True)
class TrackedGuilds:
    guild_id: int
    guild_xp: int


@dataclass(slots=True)
class TrackedPlayers:
    uuid: str
    guild_id: int
    level: int
    xp: int
    highest_week: float


@dataclass(slots=True)
class PlayerPastWeeks:
    id: int
    uuid: str
    week: int
    stars: float


@dataclass(slots=True)
class LastWeekUpdates:
    id: int
    xp_chart: int
    gxp_chart: int

