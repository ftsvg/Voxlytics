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

        self.player_info = player_info
        self.overall_stats = overall_stats
        self.game_stats = game_stats
        self.guild_info = guild_info

        self.last_login_name = (player_info.get("lastLoginName") if isinstance(player_info, dict) else None)
        self.last_login_time = (player_info.get("lastLoginTime") if isinstance(player_info, dict) else None)
        self.role = player_info.get("role") if isinstance(player_info, dict) else None

        self.level = (overall_stats.get("level") if isinstance(overall_stats, dict) else 0)
        self.exp = overall_stats.get("exp") if isinstance(overall_stats, dict) else 0
        self.weightedwins = (overall_stats.get("weightedwins") if isinstance(overall_stats, dict) else 0)

        stats = game_stats.get("stats") if isinstance(game_stats, dict) else None

        self.wins = sum(s.get("wins", 0) for s in stats.values()) if stats else 0
        self.kills = sum(s.get("kills", 0) for s in stats.values()) if stats else 0
        self.finals = sum(s.get("finals", 0) for s in stats.values()) if stats else 0
        self.beds = sum(s.get("beds", 0) for s in stats.values()) if stats else 0

        self.guild_role = (guild_info.get("guildRole") if isinstance(guild_info, dict) else None)
        self.guild_join_time = (guild_info.get("joinTime") if isinstance(guild_info, dict) else None)
        self.guild_id = (guild_info.get("guildId") if isinstance(guild_info, dict) else None)

    @classmethod
    async def fetch(cls, uuid: str) -> "PlayerInfo":
        results = await asyncio.gather(
            API.request(VoxylApiEndpoint.PLAYER_INFO, uuid=uuid),
            API.request(VoxylApiEndpoint.PLAYER_OVERALL, uuid=uuid),
            API.request(VoxylApiEndpoint.PLAYER_STATS, uuid=uuid),
            API.request(VoxylApiEndpoint.PLAYER_GUILD, uuid=uuid),
        )

        return cls(uuid, *results)
