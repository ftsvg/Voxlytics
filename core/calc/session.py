from core import get_xp_and_stars
from core.database import Session
from core.api.helpers import PlayerInfo


class SessionStats:
    def __init__(
        self,
        session_data: Session, 
        player_data: PlayerInfo
    ):
        self._session_data = session_data
        self._player_data = player_data

        p = self._player_data
        s = self._session_data

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

        self.start_time = s.start_time

        self.levels = int(p.level) - int(s.star)