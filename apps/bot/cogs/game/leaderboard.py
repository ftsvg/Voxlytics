import asyncio

from discord.ext import commands
from discord import app_commands, Interaction, File

from core.leaderboard import (
    PAGES,
    leaderboard_fetch_player_data,
    LeaderboardRenderer,
    LeaderboardView,
)
from core.api.helpers import LeaderboardInfo
from core import logger, interaction_check


class Leaderboard(commands.Cog):
    def __init__(self, client):
        self.client: commands.Bot = client

    leaderboard = app_commands.Group(
        name="leaderboard",
        description="Leaderboard related commands",
        allowed_contexts=app_commands.AppCommandContext(
            guild=True, dm_channel=True, private_channel=True
        ),
        allowed_installs=app_commands.AppInstallationType(guild=True, user=True),
    )

    async def _send_leaderboard(
        self,
        interaction: Interaction,
        lb_type: str,
        page: int,
        content: str | None = None
    ):
        data = await LeaderboardInfo.fetch_leaderboard(
            _type=lb_type,
            num=100,
        )

        if not isinstance(data, dict) or "players" not in data:
            return await interaction.edit_original_response(
                content="Failed to fetch leaderboard."
            )

        start_idx = (page - 1) * 10
        end_idx = start_idx + 10

        players = data["players"][start_idx:end_idx]

        results = await asyncio.gather(
            *[leaderboard_fetch_player_data(p) for p in players]
        )

        renderer = LeaderboardRenderer(
            players=results,
            lb_type=lb_type,
            page=page,
        )

        img_bytes = await renderer.render_to_buffer()

        view = LeaderboardView(
            data=data,
            lb_type=lb_type,
            page=page,
            owner_id=interaction.user.id,
            fetch_func=lambda players: asyncio.gather(
                *[leaderboard_fetch_player_data(p) for p in players]
            ),
        )

        msg = await interaction.edit_original_response(
            content=content,
            attachments=[File(img_bytes, filename="leaderboard.png")],
            view=view,
        )

        view.message = msg


    @leaderboard.command(name="level", description="Shows top 100 level leaderboard")
    @app_commands.describe(page="The page you want to view")
    @app_commands.choices(page=PAGES)
    async def level(self, interaction: Interaction, page: int = 1):
        await interaction.response.defer()
        try:
            content = None

            result = await interaction_check(interaction.user.id, 'compare')
            if result.status == "blacklisted":
                return await interaction.edit_original_response(
                    content=result.message
                )
            
            if result.status == "new_user":
                content = result.message

            await self._send_leaderboard(interaction, "level", page, content)

        except Exception as error:
            logger.exception(f"Unhandled exception: {error}")
            await interaction.edit_original_response(
                content="Something went wrong. If this issue persists, please contact the **Voxlytics Dev Team**."
            )


    @leaderboard.command(
        name="weightedwins",
        description="Shows top 100 weighted wins leaderboard",
    )
    @app_commands.describe(page="The page you want to view")
    @app_commands.choices(page=PAGES)
    async def weightedwins(self, interaction: Interaction, page: int = 1):
        await interaction.response.defer()
        try:
            content = None

            result = await interaction_check(interaction.user.id, 'compare')
            if result.status == "blacklisted":
                return await interaction.edit_original_response(
                    content=result.message
                )
            
            if result.status == "new_user":
                content = result.message

            await self._send_leaderboard(interaction, "weightedwins", page, content)

        except Exception as error:
            logger.exception(f"Unhandled exception: {error}")
            await interaction.edit_original_response(
                content="Something went wrong. If this issue persists, please contact the **Voxlytics Dev Team**."
            )


async def setup(client: commands.Bot) -> None:
    await client.add_cog(Leaderboard(client))
