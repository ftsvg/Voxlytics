import time
from typing import Optional, Iterable

from core.database import ensure_cursor, async_ensure_cursor, Cursor, Historical
from core.api.helpers import PlayerInfo


class HistoricalHandler:
    def __init__(
        self,
        uuid: str | None = None,
        period: str = "daily"
    ) -> None:
        self._uuid = uuid
        self._period = period

    @ensure_cursor
    def get_historical(self, *, cursor: Cursor = None) -> Optional[Historical]:
        cursor.execute(
            "SELECT * FROM historical WHERE uuid=%s and period=%s",
            (
                self._uuid,
                self._period,
            ),
        )

        row = cursor.fetchone()
        return Historical(**row) if row else None


    @ensure_cursor
    def get_tacked_players(self, *, cursor: Cursor = None) -> Iterable[tuple[str, int]]:
        cursor.execute(
            "SELECT uuid, period, last_reset FROM historical"
        )
        rows = cursor.fetchall()
        return [(r["uuid"], r["period"], r["last_reset"]) for r in rows]


    @ensure_cursor
    def update_historical(self, player_data: PlayerInfo, *, cursor: Cursor = None) -> None:
        now = int(time.time())
        
        cursor.execute(
            """
            INSERT INTO historical (
                uuid, period, wins, weighted, kills, finals, beds, star, xp, last_reset
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                wins = %s,
                weighted = %s,
                kills = %s,
                finals = %s,
                beds = %s,
                star = %s,
                xp = %s,
                last_reset = %s
            """,
            (
                self._uuid,
                self._period,
                player_data.wins,
                player_data.weightedwins,
                player_data.kills,
                player_data.finals,
                player_data.beds,
                player_data.level,
                player_data.exp,
                now,

                # Duplicate values
                player_data.wins,
                player_data.weightedwins,
                player_data.kills,
                player_data.finals,
                player_data.beds,
                player_data.level,
                player_data.exp,
                now,
            ),
        )
