from typing import final, override
from enum import Enum
from datetime import date, timedelta

import mcfetch
from discord import Interaction, File, SelectOption
from discord.ui import Select, View

from core import mojang_session, interaction_check
from core.calc import HistoricalStats
from core.api.helpers import PlayerInfo
from core.api import SKINS_API
from core.render2 import RenderingClient, PlaceholderValues
from core import logger, fetch_player
from core.database.handlers import HistoricalSnapshotHandler


class HistoricalPeriod(str, Enum):
    TODAY = "today"
    YESTERDAY = "yesterday"
    WEEKLY = "weekly"
    LAST_WEEK = "last_week"
    MONTHLY = "monthly"
    LAST_MONTH = "last_month"
    YEARLY = "yearly"
    LAST_YEAR = "last_year"


class HistoricalPeriodSelect(Select):
    def __init__(
        self,
        uuid: str,
        player_data: PlayerInfo,
        player: str | None
    ):
        handler = HistoricalSnapshotHandler(uuid)

        options = []

        periods = [
            ("today", "Today"),
            ("yesterday", "Yesterday"),
            ("weekly", "Weekly"),
            ("last_week", "Last Week"),
            ("monthly", "Monthly"),
            ("last_month", "Last Month"),
            ("yearly", "Yearly"),
            ("last_year", "Last Year"),
        ]

        today = date.today()

        for period_value, label in periods:
            if period_value == "today":
                label = f"{label} ({today:%b %d})"

            elif period_value == "yesterday":
                yesterday = today - timedelta(days=1)
                label = f"{label} ({yesterday:%b %d})"

            elif period_value == "weekly":
                week_start = today - timedelta(days=today.weekday())
                week_end = week_start + timedelta(days=6)

                label = (
                    f"{label} "
                    f"({week_start:%b %d} - {week_end:%b %d})"
                )

            elif period_value == "last_week":
                current_week_start = today - timedelta(days=today.weekday())

                week_start = current_week_start - timedelta(days=7)
                week_end = week_start + timedelta(days=6)

                label = (
                    f"{label} "
                    f"({week_start:%b %d} - {week_end:%b %d})"
                )

            elif period_value == "monthly":
                label = f"{label} ({today:%B})"

            elif period_value == "last_month":
                last_month = today.replace(day=1) - timedelta(days=1)
                label = f"{label} ({last_month:%B})"

            elif period_value == "yearly":
                label = f"{label} ({today:%Y})"

            elif period_value == "last_year":
                label = f"{label} ({today.year - 1})"

            snapshot = handler.get_snapshot_for_period(period_value)

            if snapshot:
                stats = HistoricalStats(
                    snapshot,
                    player_data
                )

                description = (
                    f"+{stats.stars_gained:,}✫, "
                    f"+{stats.wins:,} wins, "
                    f"+{stats.weighted:,} weightedwins"
                )
            else:
                description = (
                    "+0.0✫, "
                    "+0 wins, "
                    "+0 weightedwins"
                )

            options.append(
                SelectOption(
                    label=label,
                    value=period_value,
                    description=description
                )
            )

        super().__init__(
            placeholder="Select a period",
            min_values=1,
            max_values=1,
            options=options
        )

        self.uuid = uuid
        self.player_data = player_data
        self.player = player

    async def callback(self, interaction: Interaction):
        await interaction.response.defer()

        await historical_interaction(
            interaction,
            self.values[0],
            self.player
        )


class HistoricalView(View):
    def __init__(
        self,
        uuid: str,
        player_data: PlayerInfo,
        player: str | None
    ):
        super().__init__(timeout=300)

        self.add_item(
            HistoricalPeriodSelect(
                uuid,
                player_data,
                player
            )
        )


@final
class HistoricalStatsRenderer(RenderingClient):
    def __init__(
        self,
        skin_model_bytes: bytes,
        username: str,
        player_uuid: str,
        data: PlayerInfo,
        historical: HistoricalStats,
        period: str = "Today"
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
            "title#text": f"{self._period.replace('_', ' ').title()} Stats",
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


async def historical_interaction(
    interaction: Interaction,
    period: str,
    player: str | None
) -> None:
    try:
        result = await interaction_check(
            discord_id=interaction.user.id,
            guild_id=interaction.guild.id,
            role_ids=[role.id for role in interaction.user.roles],
            command_name='historical',
        )
            
        if result.status == "blacklisted":
            return await interaction.edit_original_response(
                content=result.message
            )

        if not (result := await fetch_player(interaction, player)):
            return

        uuid, player_data = result

        skin_model = await SKINS_API.fetch_skin_model(uuid)
        name = mcfetch.Player(
            player=uuid,
            requests_obj=mojang_session
        ).name

        historical_handler = HistoricalSnapshotHandler(uuid)

        if not historical_handler.is_tracked():
            historical_handler.track_player()
            historical_handler.create_snapshot(player_data)


        historical_data = historical_handler.get_snapshot_for_period(period)

        if historical_data:
            historical_stats = HistoricalStats(
                historical_data,
                player_data
            )
        else:
            class ZeroHistoricalStats:
                wins = 0
                weighted = 0
                kills = 0
                finals = 0
                beds = 0
                stars_gained = 0
                exp_gained = 0

            historical_stats = ZeroHistoricalStats()

        renderer = HistoricalStatsRenderer(
            skin_model,
            name,
            uuid,
            player_data,
            historical_stats,
            period
        )

        background_img = renderer.bg(interaction.user.id)
        img_bytes = await renderer.render_to_buffer(background_img)

        view = HistoricalView(
            uuid,
            player_data,
            player
        )

        await interaction.edit_original_response(
            attachments=[
                File(
                    img_bytes,
                    filename=f"historical_{period}.png"
                )
            ],
            view=view
        )

    except Exception as error:
        logger.exception(f"Unhandled exception: {error}")

        await interaction.edit_original_response(
            content=(
                "Something went wrong. If this issue persists, "
                "please contact the **Voxlytics Dev Team**."
            )
        )