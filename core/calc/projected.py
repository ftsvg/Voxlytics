from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from core.database import Session
from core.api.helpers import PlayerInfo

from .session import SessionStats


@dataclass
class ProjectedResult:
    wins: int
    kills: int
    finals: int
    beds: int
    weightedwins: int


class ProjectedStats:
    def __init__(
        self,
        session_data: Session,
        player_data: PlayerInfo,
        target_level: int
    ):
        self._session = session_data
        self._player = player_data
        self._target_level = target_level

        session = SessionStats(self._session, self._player)

        self.gained = {
            "wins": session.wins,
            "kills": session.kills,
            "finals": session.finals,
            "beds": session.beds,
            "weightedwins": session.weighted,
        }

        self.levels_gained = session.levels
        self.levels_remaining = max(self._target_level - self._player.level, 0)

        self.start_time = self._session.start_time

        self.projected = None
        self.projected_date = None


    def calculate(self):
        divisor = self.levels_gained if self.levels_gained > 0 else 1

        def scale(stat: str) -> int:
            per_level = self.gained[stat] / divisor
            return int(getattr(self._player, stat) + per_level * self.levels_remaining)

        self.projected = ProjectedResult(
            wins=scale("wins"),
            kills=scale("kills"),
            finals=scale("finals"),
            beds=scale("beds"),
            weightedwins=scale("weightedwins"),
        )

        now = datetime.now(timezone.utc)
        start = datetime.fromtimestamp(self.start_time, tz=timezone.utc)

        elapsed_days = max((now - start).total_seconds() / 86400, 0.01)

        stars_gained = self.levels_gained if self.levels_gained > 0 else 1
        stars_per_day = stars_gained / elapsed_days
        days_to_go = self.levels_remaining / stars_per_day

        projected = now + timedelta(days=days_to_go)
        self.projected_date = projected.strftime("%d/%m/%Y")