from enum import Enum
from datetime import date, timedelta
from dataclasses import dataclass

from core.database import ensure_cursor, Cursor
from core.api.helpers import PlayerInfo


@dataclass(slots=True)
class HistoricalSnapshot:
    uuid: str
    snapshot_date: date
    wins: int
    weighted: int
    kills: int
    finals: int
    beds: int
    star: int
    xp: int


@dataclass(slots=True)
class HistoricalPlayer:
    uuid: str


class HistoricalSnapshotHandler:
    def __init__(self, uuid: str):
        self.uuid = uuid

    @ensure_cursor
    def create_snapshot(
        self,
        player_data: PlayerInfo,
        *,
        cursor: Cursor = None
    ):
        cursor.execute(
            """
            INSERT INTO historical_snapshots (
                uuid,
                snapshot_date,
                wins,
                weighted,
                kills,
                finals,
                beds,
                star,
                xp
            )
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
            ON DUPLICATE KEY UPDATE
                wins=VALUES(wins),
                weighted=VALUES(weighted),
                kills=VALUES(kills),
                finals=VALUES(finals),
                beds=VALUES(beds),
                star=VALUES(star),
                xp=VALUES(xp)
            """,
            (
                self.uuid,
                date.today(),
                player_data.wins,
                player_data.weightedwins,
                player_data.kills,
                player_data.finals,
                player_data.beds,
                player_data.level,
                player_data.exp
            )
        )

    @ensure_cursor
    def get_snapshot(
        self,
        snapshot_date,
        *,
        cursor: Cursor = None
    ) -> HistoricalSnapshot | None:
        cursor.execute(
            """
            SELECT *
            FROM historical_snapshots
            WHERE uuid=%s
            AND snapshot_date=%s
            """,
            (
                self.uuid,
                snapshot_date
            )
        )

        row = cursor.fetchone()

        return HistoricalSnapshot(**row) if row else None
    

    @ensure_cursor
    def track_player(
        self,
        *,
        cursor: Cursor = None
    ) -> None:
        cursor.execute(
            """
            INSERT IGNORE INTO historical_players (
                uuid,
                tracked_since
            )
            VALUES (%s, %s)
            """,
            (
                self.uuid,
                date.today()
            )
        )


    @ensure_cursor
    def is_tracked(
        self,
        *,
        cursor: Cursor = None
    ) -> bool:
        cursor.execute(
            """
            SELECT 1
            FROM historical_players
            WHERE uuid=%s
            LIMIT 1
            """,
            (self.uuid,)
        )

        return cursor.fetchone() is not None    
    

    @ensure_cursor
    def get_all_players(
        self,
        *,
        cursor: Cursor = None
    ) -> list[str]:

        cursor.execute(
            """
            SELECT uuid
            FROM historical_players
            """
        )

        return [
            row["uuid"]
            for row in cursor.fetchall()
        ]
    

    @ensure_cursor
    def get_snapshot_for_period(
        self,
        period: str,
        *,
        cursor: Cursor = None
    ) -> HistoricalSnapshot | None:

        today = date.today()

        if period == "today":
            start_date = today
            end_date = today

        elif period == "yesterday":
            start_date = today - timedelta(days=1)
            end_date = start_date

        elif period == "weekly":
            start_date = today - timedelta(days=today.weekday())
            end_date = today

        elif period == "last_week":
            current_week_start = today - timedelta(days=today.weekday())
            start_date = current_week_start - timedelta(days=7)
            end_date = current_week_start - timedelta(days=1)

        elif period == "monthly":
            start_date = today.replace(day=1)
            end_date = today

        elif period == "last_month":
            current_month_start = today.replace(day=1)
            end_date = current_month_start - timedelta(days=1)
            start_date = end_date.replace(day=1)

        elif period == "yearly":
            start_date = today.replace(month=1, day=1)
            end_date = today

        elif period == "last_year":
            start_date = date(today.year - 1, 1, 1)
            end_date = date(today.year - 1, 12, 31)

        else:
            return None

        if period in ("today", "yesterday"):
            cursor.execute(
                """
                SELECT *
                FROM historical_snapshots
                WHERE uuid=%s
                AND snapshot_date=%s
                LIMIT 1
                """,
                (
                    self.uuid,
                    start_date
                )
            )
        else:
            cursor.execute(
                """
                SELECT *
                FROM historical_snapshots
                WHERE uuid=%s
                AND snapshot_date BETWEEN %s AND %s
                ORDER BY snapshot_date ASC
                LIMIT 1
                """,
                (
                    self.uuid,
                    start_date,
                    end_date
                )
            )

        row = cursor.fetchone()

        return HistoricalSnapshot(**row) if row else None