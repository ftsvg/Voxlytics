import time

from core.database import ensure_cursor, async_ensure_cursor, Cursor, Session
from core.api.helpers import PlayerInfo


class SessionHandler:
    def __init__(self, uuid: str) -> None:
        self._uuid = uuid

    @ensure_cursor
    def get_session(self, *, cursor: Cursor=None) -> Session | None:
        cursor.execute(
            "SELECT * FROM sessions WHERE uuid=%s", (self._uuid,)
        )

        row = cursor.fetchone()
        return Session(**row) if row else None
    

    @ensure_cursor
    def update_session(self, player_data: PlayerInfo, *, cursor: Cursor = None) -> None:
        now = int(time.time())
        
        cursor.execute(
            """
            INSERT INTO sessions (
                uuid, wins, weighted, kills, finals, beds, star, xp, start_time
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                wins = %s,
                weighted = %s,
                kills = %s,
                finals = %s,
                beds = %s,
                star = %s,
                xp = %s,
                start_time = %s
            """,
            (
                self._uuid,
                player_data.wins,
                player_data.weightedwins,
                player_data.kills,
                player_data.finals,
                player_data.beds,
                player_data.level,
                player_data.exp,
                now,

                # Duplicate data
                player_data.wins,
                player_data.weightedwins,
                player_data.kills,
                player_data.finals,
                player_data.beds,
                player_data.level,
                player_data.exp,
                now
            )
        )