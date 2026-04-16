from typing import final, override

import mcfetch
from discord.ext import commands
from discord import app_commands, Interaction, File

from core import mojang_session, interaction_check
from core.calc import SessionStats
from core.api.helpers import PlayerInfo
from core.api import SKINS_API
from core.render2 import RenderingClient, PlaceholderValues
from core import logger, fetch_player
from core.database.handlers import UserHandler, SessionHandler


@final
class SessionStatsRenderer(RenderingClient):
    def __init__(
        self, 
        skin_model_bytes: bytes,
        username: str,
        player_uuid: str,
        data: PlayerInfo,
        session: SessionStats,
    ):
        super().__init__(route="/session")

        self._skin_model_bytes = skin_model_bytes
        self._username = username
        self._player_uuid = player_uuid
        self._data = data
        self._session = session

    @override
    def placeholder_values(self) -> PlaceholderValues:

        text_placeholders = {
            "title#text": f"Session Stats",
            "wins#text": f"{self._session.wins:,}",
            "weighted#text": f"{self._session.weighted:,}",
            "kills#text": f"{self._session.kills:,}",
            "finals#text": f"{self._session.finals:,}",
            "beds#text": f"{self._session.beds:,}",

            "levels_gained#text": f"{self._session.stars_gained:,}",
            "xp_gained#text": f"{self._session.exp_gained:,}",
        }

        placeholder_values = PlaceholderValues.new(text=text_placeholders)
        placeholder_values.add_skin_model(self._skin_model_bytes)
        placeholder_values.add_footer()
        placeholder_values.add_progress_bar(self._data.level, self._data.exp)
        placeholder_values.add_current_and_next_level(int(self._data.level))
        placeholder_values.ad_displayname_star(self._username, self._data.role, self._data.level)
        placeholder_values.add_progress_text(self._data.level, self._data.exp)

        return placeholder_values


class Session(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client

    session = app_commands.Group(
        name="session",
        description="View and manage sessions",
        allowed_contexts=app_commands.AppCommandContext(guild=True, dm_channel=True, private_channel=True),
        allowed_installs=app_commands.AppInstallationType(guild=True, user=True)
    )


    @session.command(
        name="view",
        description="View a player's session"
    )
    @app_commands.describe(player="The player you want to view")
    async def view(
        self, 
        interaction: Interaction,
        player: str | None = None
    ):
        await interaction.response.defer()
        try:
            result = await interaction_check(interaction.user.id, 'session_view')
            if result.status == "blacklisted":
                return await interaction.edit_original_response(
                    content=result.message
                )
                
            handler = UserHandler(interaction.user.id)
            user = handler.get_player()

            if not user:
                return await interaction.edit_original_response(
                    content="You don't have an account linked! Use **/link** to link your account."
                )
            
            if not (result := await fetch_player(interaction, player)):
                return None

            uuid, player_data = result
            
            session_handler = SessionHandler(uuid)
            session = session_handler.get_session()

            if not session:
                session_handler.update_session(player_data)
                session = session_handler.get_session()
            
            skin_model = await SKINS_API.fetch_skin_model(uuid)
            name = mcfetch.Player(
                player=uuid, requests_obj=mojang_session
            ).name

            session_stats = SessionStats(session, player_data)

            renderer = SessionStatsRenderer(
                skin_model,
                name,
                uuid,
                player_data,
                session_stats,
            )

            img_bytes = await renderer.render_to_buffer()
            start_time = session.start_time

            await interaction.edit_original_response(
                content=f"<a:mc_clock:1494030376505708575> Started on <t:{start_time}:F>",
                attachments=[File(img_bytes, filename=f"session.png")]
            )            
            
        except Exception as error:
            logger.exception(f"Unhandled exception: {error}")

            await interaction.edit_original_response(
                content="Something went wrong. If this issue persists, please contact the **Voxlytics Dev Team**."
            )


    @session.command(
        name="reset", 
        description="Resets your session"
    )
    async def reset(
        self, 
        interaction: Interaction, 
    ):
        await interaction.response.defer()
        try:
            result = await interaction_check(interaction.user.id, 'session_reset')
            if result.status == "blacklisted":
                return await interaction.edit_original_response(
                    content=result.message
                )

            handler = UserHandler(interaction.user.id)
            user = handler.get_player()

            if not user:
                return await interaction.edit_original_response(
                    content="You don't have an account linked! Use **/link** to link your account."
                )
            
            session_handler = SessionHandler(user.uuid)
            session = session_handler.get_session()

            if not session:
                return await interaction.edit_original_response(
                    content="You don't have an active session."
                )
            
            player_data: dict = await PlayerInfo.fetch(session.uuid)
            session_handler.update_session(player_data)
        
            await interaction.edit_original_response(
                content="Your session has successfully been reset."
            )

        except Exception as error:
            logger.exception(f"Unhandled exception: {error}")

            await interaction.edit_original_response(
                content="Something went wrong. If this issue persists, please contact the **Voxlytics Dev Team**."
            )

async def setup(client: commands.Bot) -> None:
    await client.add_cog(Session(client))