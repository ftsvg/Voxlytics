import asyncio
from core.api import API, VoxylApiEndpoint


class IntegrationInfo:
    def __init__(
        self,
        discord_from_player: dict | int | None,
        player_from_discord: dict | int | None,
    ):
        self.discord_from_player = discord_from_player
        self.player_from_discord = player_from_discord

        self.discord_id = (
            int(discord_from_player.get("id"))
            if isinstance(discord_from_player, dict)
            and discord_from_player.get("id") is not None
            else None
        )

        self.player_uuid = (
            player_from_discord.get("uuid")
            if isinstance(player_from_discord, dict)
            else None
        )

    @classmethod
    async def fetch(
        cls,
        *,
        uuid: str | None = None,
        discord_id: int | None = None,
    ) -> "IntegrationInfo":

        tasks = [
            API.request(VoxylApiEndpoint.DISCORD_FROM_PLAYER, uuid=uuid)
            if uuid is not None
            else asyncio.sleep(0, result=None),

            API.request(VoxylApiEndpoint.PLAYER_FROM_DISCORD, discord_id=str(discord_id))
            if discord_id is not None
            else asyncio.sleep(0, result=None),
        ]

        discord_from_player, player_from_discord = await asyncio.gather(*tasks)

        return cls(
            discord_from_player,
            player_from_discord,
        )