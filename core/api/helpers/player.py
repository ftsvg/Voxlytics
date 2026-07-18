import asyncio
from core.api import API, VoxylApiEndpoint


class PlayerInfo:
    def __init__(
        self,
        uuid: str,
        player_info: dict | int,
        overall_stats: dict | int,
        game_stats: dict | int,
        guild_info: dict | int,
    ):
        self.uuid = uuid

        self.player_info = player_info if isinstance(player_info, dict) else {}
        self.overall_stats = overall_stats if isinstance(overall_stats, dict) else {}
        self.game_stats = game_stats if isinstance(game_stats, dict) else {}
        self.guild_info = guild_info if isinstance(guild_info, dict) else {}

        self.last_login_name = self.player_info.get("lastLoginName")
        self.last_login_time = self.player_info.get("lastLoginTime")
        self.role = self.player_info.get("role")

        self.level = self.overall_stats.get("level", 0)
        self.exp = self.overall_stats.get("exp", 0)
        self.weightedwins = self.overall_stats.get("weightedwins", 0)

        stats = self.game_stats.get("stats", {})
        self.mode_stats = stats if isinstance(stats, dict) else {}

        self.wins = sum(
            mode_stats.get("wins", 0)
            for mode_stats in self.mode_stats.values()
            if isinstance(mode_stats, dict)
        )

        self.kills = sum(
            mode_stats.get("kills", 0)
            for mode_stats in self.mode_stats.values()
            if isinstance(mode_stats, dict)
        )

        self.finals = sum(
            mode_stats.get("finals", 0)
            for mode_stats in self.mode_stats.values()
            if isinstance(mode_stats, dict)
        )

        self.beds = sum(
            mode_stats.get("beds", 0)
            for mode_stats in self.mode_stats.values()
            if isinstance(mode_stats, dict)
        )

        self.guild_role = self.guild_info.get("guildRole")
        self.guild_join_time = self.guild_info.get("joinTime")
        self.guild_id = self.guild_info.get("guildId")

    @classmethod
    async def fetch(cls, uuid: str) -> "PlayerInfo":
        results = await asyncio.gather(
            API.request(VoxylApiEndpoint.PLAYER_INFO, uuid=uuid),
            API.request(VoxylApiEndpoint.PLAYER_OVERALL, uuid=uuid),
            API.request(VoxylApiEndpoint.PLAYER_STATS, uuid=uuid),
            API.request(VoxylApiEndpoint.PLAYER_GUILD, uuid=uuid),
        )

        return cls(uuid, *results)
