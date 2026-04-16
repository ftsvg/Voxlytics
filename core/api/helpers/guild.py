import asyncio
from typing import Any, Optional
from core.api import API, VoxylApiEndpoint


class GuildInfo:
    def __init__(
        self,
        tag_or_id: str,
        guild_info: dict | int | None,
        guild_members: dict | int | None,
    ):
        self.tag_or_id = str(tag_or_id)

        self.id = guild_info.get("id") if isinstance(guild_info, dict) else None
        self.name = guild_info.get("name") if isinstance(guild_info, dict) else None
        self.description = guild_info.get("desc") if isinstance(guild_info, dict) else None

        self.xp = guild_info.get("xp") if isinstance(guild_info, dict) else 0
        self.member_count = guild_info.get("num") if isinstance(guild_info, dict) else 0

        self.owner_uuid = guild_info.get("ownerUUID") if isinstance(guild_info, dict) else None
        self.creation_time = guild_info.get("time") if isinstance(guild_info, dict) else None

        self.members = guild_members.get("members", []) if isinstance(guild_members, dict) else []

    @classmethod
    async def fetch(cls, tag_or_id: str | int) -> Optional["GuildInfo"]:
        def normalize(value: str | int) -> str:
            value = str(value)
            return f"-{value}" if value.isdigit() else value

        identifier = normalize(tag_or_id)

        guild_info, guild_members = await asyncio.gather(
            API.request(VoxylApiEndpoint.GUILD_INFO, tag_or_id=identifier),
            API.request(VoxylApiEndpoint.GUILD_MEMBERS, tag_or_id=identifier),
        )

        if not isinstance(guild_info, dict) or "error" in guild_info:
            return None

        return cls(identifier, guild_info, guild_members)

    @staticmethod
    async def fetch_top_guilds(num: int = 100) -> Any:
        return await API.request(
            VoxylApiEndpoint.GUILD_TOP,
            num=num,
        )