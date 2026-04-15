from core import get_xp_and_stars
from core.database import Historical
from core.api.helpers import PlayerInfo


class HistoricalStats:
    def __init__(
        self, 
        historical_data: Historical, 
        player_data: PlayerInfo
    ):
        self._historical_data = historical_data
        self._player_data = player_data

        p = self._player_data
        s = self._historical_data

        self.wins = int(p.wins) - int(s.wins)
        self.weighted = int(p.weightedwins) - int(s.weighted)
        self.kills = int(p.kills) - int(s.kills)
        self.finals = int(p.finals) - int(s.finals)
        self.beds = int(p.beds) - int(s.beds)

        self.exp_gained, self.stars_gained = get_xp_and_stars(
            old_level=int(s.star),
            old_xp=int(s.xp),
            new_level=int(p.level),
            new_xp=int(p.exp)
        )

        self.last_reset = s.last_reset