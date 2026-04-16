from typing import final, override, Literal

from mcfetch import Player
from discord.ext import commands
from discord import app_commands, Interaction, File

from core import logger, fetch_player, mojang_session, interaction_check
from core.render2 import RenderingClient, PlaceholderValues, TSpan
from core.api.helpers import PlayerInfo
from core.api import SKINS_API
from core.database.handlers import SessionHandler
from core.calc import ProjectedStats


def generate_projected_text(
    key: Literal["wins", "weighted", "levels", "kills", "finals", "beds"],
    value_1: int,
    value_2: int,
    value_fill: str
) -> None:
    
    stat_diff = int(value_2 - value_1)

    value_text = [
        TSpan(value=f"{value_1:,}", fill=value_fill),
        TSpan(value=" / ", fill="#AAAAAA"),
        TSpan(value=f"{value_2:,}", fill=value_fill),
    ]

    if stat_diff == 0:
        diff_text = "+0"
        diff_fill = "#55FF55"
    else:
        diff_text = f"{'+' if stat_diff > 0 else '-'}{abs(stat_diff):,}"
        diff_fill = (
            "#55FF55" if stat_diff > 0
            else "#FF5555"
        )

    return {
        f"{key}_value#text": value_text,
        f"{key}_value#fill": value_fill,
        f"{key}_diff#text": diff_text,
        f"{key}_diff#fill": diff_fill,
    }


@final
class ProjectedStatsRenderer(RenderingClient):
    def __init__(
        self, 
        skin_model_bytes: bytes,
        username: str,
        player_uuid: str,
        data: PlayerInfo,
        projected_stats: ProjectedStats
    ):
        super().__init__(route="/projected")

        self._skin_model_bytes = skin_model_bytes
        self._username = username
        self._player_uuid = player_uuid
        self._data = data
        self._pj = projected_stats

    @override
    def placeholder_values(self) -> PlaceholderValues:
        self._pj.calculate()

        text_placeholders = {
            "date#text": f"{self._pj.projected_date}",
        }
        text_placeholders.update(
            generate_projected_text("wins", self._data.wins, self._pj.projected.wins, "#55FF55")
        )
        text_placeholders.update(
            generate_projected_text("weighted", self._data.weightedwins, self._pj.projected.weightedwins, "#5555FF")
        )
        text_placeholders.update(
            generate_projected_text("levels", self._data.level, self._pj._target_level, "#55FFFF")
        )
        text_placeholders.update(
            generate_projected_text("kills", self._data.kills, self._pj.projected.kills, "#FF55FF")
        )
        text_placeholders.update(
            generate_projected_text("finals", self._data.finals, self._pj.projected.finals, "#FF5555")
        )
        text_placeholders.update(
            generate_projected_text("beds", self._data.beds, self._pj.projected.beds, "#FFFF55")
        )

        placeholder_values = PlaceholderValues.new(text=text_placeholders)
        placeholder_values.add_skin_model(self._skin_model_bytes)
        placeholder_values.add_current_level(int(self._pj._target_level))
        placeholder_values.ad_displayname_star(self._username, self._data.role, self._data.level)
        placeholder_values.add_footer()

        return placeholder_values


class Prestige(commands.Cog):
    def __init__(self, client):
        self.client: commands.Bot = client


    @app_commands.command(
        name="prestige", 
        description="Get your projected stats based on a session"
    )
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.describe(
        level="The level to get projected stats for",
        player="The player you want to view",
    )
    async def prestige(
        self, 
        interaction: Interaction,
        level: int,
        player: str = None
    ):
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

            if not (result := await fetch_player(interaction, player)):
                return None

            uuid, player_data = result

            session_handler = SessionHandler(uuid)
            session = session_handler.get_session()

            if not session:
                session_handler.update_session(player_data)
                return await interaction.edit_original_response(
                    content="No active session was found for this player.\n- A new session has been started automatically."
                )
            
            player_level  = player_data.level

            if player_level > 9999:
                return await interaction.edit_original_response(
                    content="Level cannot be higher than **9999**"
                )
            
            if level <= player_level:
                return await interaction.edit_original_response(
                    content=f"Level must be higher than the player's current level."
                )
            
            skin_model = await SKINS_API.fetch_skin_model(uuid)
            name = Player(player=uuid, requests_obj=mojang_session).name
            
            projected_stats = ProjectedStats(session, player_data, level)
            gained = projected_stats.gained

            if (
                gained["wins"] < 10 and gained["kills"] < 10 and gained["weightedwins"] < 10
            ):
                return await interaction.edit_original_response(
                    content="This player must first play a few games."
                )
            
            renderer = ProjectedStatsRenderer(
                skin_model,
                name,
                uuid,
                player_data,
                projected_stats,
            )

            img_bytes = await renderer.render_to_buffer()
            await interaction.edit_original_response(
                content=content,
                attachments=[File(img_bytes, filename=f"projected.png")]
            )            

        except Exception as error:
            logger.exception("Unhandled exception: %s", error)
            await interaction.edit_original_response(
                content="Something went wrong. If this issue persists, please contact the **Voxlytics Dev Team**."
            ) 


async def setup(client: commands.Bot) -> None:
    await client.add_cog(Prestige(client))