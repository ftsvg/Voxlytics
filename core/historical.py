from typing import final, override

import mcfetch
from discord import Interaction, File

from core import mojang_session
from core.calc import HistoricalStats
from core.api.helpers import PlayerInfo
from core.api import SKINS_API
from core.render2 import RenderingClient, PlaceholderValues
from core import logger, fetch_player
from core.database.handlers import HistoricalHandler


PERIODS = ['daily', 'weekly', 'monthly', 'yearly']
PERIOD_SECONDS = {
    "daily": 86400,
    "weekly": 86400 * 7,
    "monthly": 86400 * 30,
    "yearly": 86400 * 365,
}


@final
class HistoricalStatsRenderer(RenderingClient):
    def __init__(
        self, 
        skin_model_bytes: bytes,
        username: str,
        player_uuid: str,
        data: PlayerInfo,
        historical: HistoricalStats,
        period: str = "Daily"
    ):
        super().__init__(route="/session")

        self._skin_model_bytes = skin_model_bytes
        self._username = username
        self._player_uuid = player_uuid
        self._data = data
        self._historical = historical
        self._period = period


    @override
    def placeholder_values(self) -> PlaceholderValues:

        text_placeholders = {
            "title#text": f"{self._period.title()} Stats",
            "wins#text": f"{self._historical.wins:,}",
            "weighted#text": f"{self._historical.weighted:,}",
            "kills#text": f"{self._historical.kills:,}",
            "finals#text": f"{self._historical.finals:,}",
            "beds#text": f"{self._historical.beds:,}",

            "levels_gained#text": f"{self._historical.stars_gained:,}",
            "xp_gained#text": f"{self._historical.exp_gained:,}",
        }

        placeholder_values = PlaceholderValues.new(text=text_placeholders)
        placeholder_values.add_skin_model(self._skin_model_bytes)
        placeholder_values.add_footer()
        placeholder_values.add_progress_bar(self._data.level, self._data.exp)
        placeholder_values.add_current_and_next_level(int(self._data.level))
        placeholder_values.ad_displayname_star(self._username, self._data.role, self._data.level)
        placeholder_values.add_progress_text(self._data.level, self._data.exp)

        return placeholder_values
    

async def historical_interaction(
    interaction: Interaction,
    period: str,
    player: str | None    
) -> None:
    try:
        if not (result := await fetch_player(interaction, player)):
            return None

        uuid, player_data = result

        skin_model = await SKINS_API.fetch_skin_model(uuid)
        name = mcfetch.Player(player=uuid, requests_obj=mojang_session).name

        historical_handler = HistoricalHandler(uuid, period)
        historical_data = historical_handler.get_historical()

        if not historical_data:
            for p in PERIODS:
                HistoricalHandler(uuid, p).update_historical(player_data)
        
            return await interaction.edit_original_response(
                content=f"Historical stats for **{name}** will now be tracked."
            )
        
        historical_stats = HistoricalStats(historical_data, player_data)

        renderer = HistoricalStatsRenderer(
            skin_model,
            name,
            uuid,
            player_data,
            historical_stats,
            period
        )

        img_bytes = await renderer.render_to_buffer()
        
        reset = historical_data.last_reset
        next_reset = reset + PERIOD_SECONDS[period]

        await interaction.edit_original_response(
            content=f"<a:mc_clock:1494030376505708575> Resets in <t:{next_reset}:R>",
            attachments=[File(img_bytes, filename=f"historical_{period}.png")]
        )       

    except Exception as error:
        logger.exception(f"Unhandled exception: {error}")

        await interaction.edit_original_response(
            content="Something went wrong. If this issue persists, please contact the **Voxlytics Dev Team**."
        )