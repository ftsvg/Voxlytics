import time
import json
from typing import Optional, Any, Dict, List

from core.database import (
    ensure_cursor,
    Cursor,
    LeaderboardSnapshot,
    LeaderboardChannel,
)


class LeaderboardHandler:
    def __init__(self, type: str = "level") -> None:
        self._type = type

    @ensure_cursor
    def get_channels(self, *, cursor: Cursor = None) -> List[LeaderboardChannel]:
        cursor.execute("SELECT guild_id, channel_id FROM leaderboard_channels")

        rows = cursor.fetchall()
        return [
            LeaderboardChannel(guild_id=r["guild_id"], channel_id=r["channel_id"])
            for r in rows
        ]


    @ensure_cursor
    def update_channel(
        self, guild_id: int, channel_id: int, *, cursor: Cursor = None
    ) -> None:
        cursor.execute(
            """
            INSERT INTO leaderboard_channels (guild_id, channel_id)
            VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE
                channel_id=%s
            """,
            (guild_id, channel_id, channel_id,)
        )


    @ensure_cursor
    def update_snapshot(self, data: Dict[str, Any], *, cursor: Cursor = None) -> None:
        cursor.execute(
            """
            INSERT INTO leaderboard_snapshot (type, data, updated_at)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE
                data=%s,
                updated_at=%s
            """,
            (
                self._type,
                json.dumps(data),
                int(time.time()),

                # Duplicate data
                json.dumps(data),
                int(time.time()),
            ),
        )


    @ensure_cursor
    def get_snapshot(self, *, cursor: Cursor = None) -> Optional[LeaderboardSnapshot]:
        cursor.execute(
            "SELECT type, data, updated_at FROM leaderboard_snapshot WHERE type=%s",
            (self._type,),
        )
        row = cursor.fetchone()

        if not row:
            return None

        data = row["data"]
        if isinstance(data, str):
            data = json.loads(data)

        return LeaderboardSnapshot(
            type=row["type"],
            data=data,
            updated_at=row["updated_at"]
        )
