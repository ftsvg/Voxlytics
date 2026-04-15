from typing import final, override

from core.render2 import RenderingClient, PlaceholderValues
from core.api.helpers import PlayerInfo


@final
class LeaderboardRenderer(RenderingClient):
    def __init__(
        self,
        players: list[dict],
        lb_type: str,
        page: int,
    ):
        super().__init__(route="/leaderboard")

        self._players = players
        self._lb_type = lb_type
        self._page = page

    @override
    def placeholder_values(self) -> PlaceholderValues:
        placeholder_values = PlaceholderValues.new(text={})

        display_lb_type = {
            "level": "Level",
            "weightedwins": "Weighted Wins",
        }.get(self._lb_type, self._lb_type.title())

        placeholder_values.text["title#text"] = f"Leaderboard {display_lb_type}"
        placeholder_values.text["lb_type#text"] = display_lb_type

        start_rank = (self._page - 1) * 10

        for i, player in enumerate(self._players, start=1):
            rank = start_rank + i

            stats: PlayerInfo = player["stats"]
            ign = player["ign"]
            skin = player["skin"]

            placeholder_values.text[f"pos_{i}#text"] = f"#{rank}"
            placeholder_values.text[f"pos_{i}#fill"] = {
                1: "#FFFF55",
                2: "#AAAAAA",
                3: "#FFAA00",
            }.get(rank, "#FFFFFF")

            value = (
                stats.level
                if self._lb_type.lower() == "level"
                else stats.weightedwins
            )

            placeholder_values.text[f"value_{i}#text"] = f"{value:,}"


            placeholder_values.ad_displayname_star(
                ign, stats.role, stats.level, placeholder_key=f"displayname_{i}"
            )
            placeholder_values.add_skin_model(skin, f"head_{i}")

        placeholder_values.add_footer()

        return placeholder_values