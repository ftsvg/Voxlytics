from core import get_xp_and_stars
from core.api.helpers import PlayerInfo
from core.database.handlers import HistoricalSnapshot


class HistoricalStats:
    def __init__(
        self,
        snapshot: HistoricalSnapshot,
        player_data: PlayerInfo
    ):
        p = player_data
        s = snapshot

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

        self.snapshot_date = s.snapshot_date