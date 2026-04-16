import asyncio
from typing import final, override, Literal
from dataclasses import dataclass

from mcfetch import Player
from discord.ext import commands
from discord import app_commands, Interaction, File

from core import fetch_player, logger, mojang_session, interaction_check
from core.render2 import RenderingClient, PlaceholderValues, TSpan
from core.api import SKINS_API
from core.api.helpers import PlayerInfo


@dataclass
class ComparePlayer:
    uuid: str
    name: str
    skin_model: bytes
    data: PlayerInfo


def generate_compare_text(
    key: Literal["wins", "weighted", "levels", "kills", "finals", "beds"],
    value_1: int,
    value_2: int,
    value_fill: str
) -> None:
    
    stat_diff = int(value_1 - value_2)

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
class CompareStatsRenderer(RenderingClient):
    def __init__(
        self, 
        player_1: ComparePlayer,
        player_2: ComparePlayer
    ):
        super().__init__(route="/compare")

        self._player_1 = player_1
        self._player_2 = player_2


    @override   
    def placeholder_values(self) -> PlaceholderValues:

        text_placeholders = {}
        text_placeholders.update(
            generate_compare_text("wins", self._player_1.data.wins, self._player_2.data.wins, "#55FF55")
        )
        text_placeholders.update(
            generate_compare_text("weighted", self._player_1.data.weightedwins, self._player_2.data.weightedwins, "#5555FF")
        )
        text_placeholders.update(
            generate_compare_text("levels", self._player_1.data.level, self._player_2.data.level, "#55FFFF")
        )
        text_placeholders.update(
            generate_compare_text("kills", self._player_1.data.kills, self._player_2.data.kills, "#FF55FF")
        )
        text_placeholders.update(
            generate_compare_text("finals", self._player_1.data.finals, self._player_2.data.finals, "#FF5555")
        )
        text_placeholders.update(
            generate_compare_text("beds", self._player_1.data.beds, self._player_2.data.beds, "#FFFF55")
        )

        placeholder_values = PlaceholderValues.new(text=text_placeholders)
        placeholder_values.add_skin_model(self._player_1.skin_model, placeholder_key="skin_1")
        placeholder_values.add_skin_model(self._player_2.skin_model, placeholder_key="skin_2")
        placeholder_values.ad_displayname_star(
            self._player_1.name, self._player_1.data.role, self._player_1.data.level, placeholder_key="displayname_1"
        )
        placeholder_values.ad_displayname_star(
            self._player_2.name, self._player_2.data.role, self._player_2.data.level, placeholder_key="displayname_2"
        )
        placeholder_values.add_footer()

        return placeholder_values


class Compare(commands.Cog):
    def __init__(self, client):
        self.client: commands.Bot = client


    async def _get_player_data(self, interaction, player):
        if not (result := await fetch_player(interaction, player)):
            return None

        uuid, player_data = result

        name = await asyncio.to_thread(
            lambda: Player(player=uuid, requests_obj=mojang_session).name
        )

        skin_model = await SKINS_API.fetch_skin_model(uuid)

        return {
            "uuid": uuid,
            "name": name,
            "player_data": player_data,
            "skin_model": skin_model,
        }


    @app_commands.command(
        name="compare", 
        description="Compare player's stats to another player's stats"
    )
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.describe(
        player_1="The primary player", 
        player_2="The secondary player"
    )
    async def compare(
        self, 
        interaction: Interaction, 
        player_1: str, 
        player_2: str = None
    ):
        await interaction.response.defer()

        try:
            result = await interaction_check(interaction.user.id, 'compare')
            if result.status == "blacklisted":
                return await interaction.edit_original_response(
                    content=result.message
                )

            results = await asyncio.gather(
                self._get_player_data(interaction, player_1),
                self._get_player_data(interaction, player_2),
            )

            if any(r is None for r in results):
                return

            p1, p2 = results

            player_1 = ComparePlayer(
                uuid=p1["uuid"],
                name=p1["name"],
                skin_model=p1["skin_model"],
                data=p1["player_data"],
            )

            player_2 = ComparePlayer(
                uuid=p2["uuid"],
                name=p2["name"],
                skin_model=p2["skin_model"],
                data=p2["player_data"],
            )

            renderer = CompareStatsRenderer(player_1, player_2)
            img_bytes = await renderer.render_to_buffer()

            await interaction.edit_original_response(
                attachments=[File(img_bytes, filename="compare.png")]
            )

        except Exception as error:
            logger.exception(f"Unhandled exception: {error}")

            await interaction.edit_original_response(
                content="Something went wrong. If this issue persists, please contact the **Voxlytics Dev Team**."
            )

async def setup(client: commands.Bot) -> None:
    await client.add_cog(Compare(client)) 