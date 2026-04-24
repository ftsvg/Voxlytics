from typing import final, override

import mcfetch
from discord.ext import commands
from discord import app_commands, Interaction, File

from core import (
    mojang_session,
    interaction_check,
    logger,
    fetch_player,
    get_stars_gained
)
from core.api.helpers import PlayerInfo
from core.api import SKINS_API
from core.render2 import RenderingClient, PlaceholderValues
from core.guild import GuildHandler


def get_week_color(value: float) -> str:
    if value < 1:
        return "#FF5555"
    elif value < 2:
        return "#FFAA00"
    return "#55FF55"


@final
class CheckRenderer(RenderingClient):
    def __init__(
        self,
        skin_model_bytes: bytes,
        username: str,
        player_data: PlayerInfo,
        past_weeks: list[float],
        highest_week: float,
        stars_gained: float,
        start_level: int
    ):
        super().__init__(route="/check")

        self._skin = skin_model_bytes
        self._username = username
        self._data = player_data
        self._past_weeks = past_weeks
        self._highest_week = highest_week
        self._stars_gained = stars_gained
        self._start_level = start_level

    @override
    def placeholder_values(self) -> PlaceholderValues:
        weeks = (self._past_weeks + [0, 0, 0, 0, 0])[:5]

        avg = round(sum(self._past_weeks) / len(self._past_weeks), 2) if self._past_weeks else 0

        placeholder_values = PlaceholderValues.new(text={
            "title_1#text": "Current Week Stats",
            "title_2#text": "Overall Statistics",
            "title_3#text": "Past Weeks (Recent - Oldest week)",
            
            "level#text": f"{self._start_level}",
            "stars_gained#text": f"{self._stars_gained:.2f}✫",
            "highest_week#text": f"{self._highest_week:.2f}✫",
            "average_week#text": f"{avg:.2f}✫",

            "week_1#text": f"{weeks[0]:.2f}✫",
            "week_2#text": f"{weeks[1]:.2f}✫",
            "week_3#text": f"{weeks[2]:.2f}✫",
            "week_4#text": f"{weeks[3]:.2f}✫",
            "week_5#text": f"{weeks[4]:.2f}✫",

            "week_1#fill": get_week_color(weeks[0]),
            "week_2#fill": get_week_color(weeks[1]),
            "week_3#fill": get_week_color(weeks[2]),
            "week_4#fill": get_week_color(weeks[3]),
            "week_5#fill": get_week_color(weeks[4]),
        })

        placeholder_values.add_skin_model(self._skin)
        placeholder_values.add_footer()
        placeholder_values.add_progress_bar(self._data.level, self._data.exp)
        placeholder_values.add_current_and_next_level(int(self._data.level))
        placeholder_values.ad_displayname_star(
            self._username,
            self._data.role,
            self._data.level
        )
        placeholder_values.add_progress_text(
            self._data.level,
            self._data.exp
        )

        return placeholder_values


class Check(commands.Cog):
    def __init__(self, client):
        self.client: commands.Bot = client

    @app_commands.command(
        name="check",
        description="View xp progress and weekly stats for any player"
    )
    @app_commands.describe(player="The player you want to view")
    async def check(
        self,
        interaction: Interaction,
        player: str | None = None
    ):
        await interaction.response.defer()

        try:
            result = await interaction_check(interaction.user.id, "check")
            if result.status == "blacklisted":
                return await interaction.edit_original_response(
                    content=result.message
                )

            if not (res := await fetch_player(interaction, player)):
                return

            uuid, player_data = res

            guild_handler = GuildHandler()

            player_row = guild_handler.get_player_full(uuid)
            if not player_row:
                return await interaction.edit_original_response(
                    content="This player is not tracked."
                )

            past_weeks = guild_handler.get_player_past_weeks(uuid)
            highest_week = guild_handler.get_player_highest_week(uuid)

            stars_gained = get_stars_gained(
                player_row.level,
                player_row.xp,
                player_data.level,
                player_data.exp
            )

            skin = await SKINS_API.fetch_skin_model(uuid)
            name = mcfetch.Player(
                player=uuid,
                requests_obj=mojang_session
            ).name

            renderer = CheckRenderer(
                skin,
                name,
                player_data,
                past_weeks,
                highest_week,
                stars_gained,
                player_row.level
            )

            bg = renderer.bg(interaction.user.id)
            img_bytes = await renderer.render_to_buffer(bg)

            await interaction.edit_original_response(
                attachments=[File(img_bytes, filename="check.png")]
            )

        except Exception as error:
            logger.exception(f"Unhandled exception: {error}")

            await interaction.edit_original_response(
                content="Something went wrong. If this issue persists, please contact the **Voxlytics Dev Team**."
            )


async def setup(client: commands.Bot) -> None:
    await client.add_cog(Check(client))