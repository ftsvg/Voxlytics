from typing import final, override

from core import logger
from core.render2 import RenderingClient, PlaceholderValues
from core.api.helpers import PlayerInfo

from .schemas import MODE_SCHEMAS
from .utils import resolve_stats


@final
class StatsRenderer(RenderingClient):
    def __init__(
        self,
        skin_model_bytes: bytes,
        username: str,
        player_uuid: str,
        player: PlayerInfo,
        mode: str,
        view: str,
    ):
        self.schema = MODE_SCHEMAS[mode]

        super().__init__(route=self.schema.route)

        self.skin_model_bytes = skin_model_bytes
        self.username = username
        self.player_uuid = player_uuid
        self.player = player
        self.mode = mode
        self.view = view

        if mode == "Overall":
            self.stats = {
                "wins": player.wins,
                "kills": player.kills,
                "beds": player.beds,
                "finals": player.finals,
                "weighted": player.weightedwins,
            }
        else:
            self.stats = resolve_stats(player, self.schema.joins, view)

        self.stat_type = self.schema.types.get(view, "Overall")

    @override
    def placeholder_values(self) -> PlaceholderValues:
        stat_part = self.stat_type.lower()

        if self.mode == "Overall":
            title = f"{self.schema.title} Stats"
        else:
            title = f"{self.schema.title} ({stat_part.title()}) Stats"

        text = {
            "title#text": title,
        }

        for key in self.schema.stats:
            text[f"{key}#text"] = f"{self.stats.get(key, 0):,}"

        placeholder_values = PlaceholderValues.new(text=text)
        placeholder_values.add_skin_model(self.skin_model_bytes)
        placeholder_values.add_progress_bar(self.player.level, self.player.exp)
        placeholder_values.add_progress_text(self.player.level, self.player.exp)
        placeholder_values.add_current_and_next_level(int(self.player.level))
        placeholder_values.ad_displayname_star(self.username, self.player.role, self.player.level)
        placeholder_values.add_footer()

        return placeholder_values