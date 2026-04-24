import asyncio
from typing import Optional

from core.api.helpers import PlayerInfo
from core.database import ensure_cursor, Cursor, async_ensure_cursor
from .models import *
from .helpers import get_current_week


class ServerConfigHandler:
    def __init__(self, server_id: int) -> None:
        self._server_id = server_id

    @ensure_cursor
    def update_server_config(
        self,
        chart_logs: int,
        *, 
        cursor: Cursor=None
    ):
        cursor.execute(
            """
            INSERT INTO server_config (server_id, chart_logs)
            VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE
                chart_logs = %s
            """,
            (self._server_id, chart_logs, chart_logs,)
        )

    @ensure_cursor
    def get_server_config(self, *, cursor: Cursor=None) -> Optional[ServerConfig]:
        cursor.execute(
            "SELECT * FROM server_config WHERE server_id=%s", (self._server_id,)
        )

        row = cursor.fetchone()
        return ServerConfig(**row) if row else None

    @ensure_cursor
    def insert_tracked_server_guilds(
        self,
        guild_id: int,
        log_channel_id: int | None = None,
        *,
        cursor: Cursor = None
    ):
        cursor.execute(
            """
            INSERT INTO tracked_server_guilds (server_id, guild_id, log_channel_id)
            VALUES (%s, %s, %s)
            """,
            (self._server_id, guild_id, log_channel_id)
        )

    @ensure_cursor
    def update_tracked_server_guild(
        self,
        old_guild_id: int,
        new_guild_id: int | None = None,
        log_channel_id: int | None = None,
        *,
        cursor: Cursor = None
    ):
        updates = []
        values = []

        if new_guild_id is not None:
            updates.append("guild_id = %s")
            values.append(new_guild_id)

        if log_channel_id is not None:
            updates.append("log_channel_id = %s")
            values.append(log_channel_id)

        if not updates:
            return

        values.extend([self._server_id, old_guild_id])

        query = f"""
            UPDATE tracked_server_guilds
            SET {', '.join(updates)}
            WHERE server_id = %s
            AND guild_id = %s
        """

        cursor.execute(query, tuple(values))

    @ensure_cursor
    def delete_tracked_server_guild(
        self,
        guild_id: int,
        *,
        cursor: Cursor = None
    ):
        cursor.execute(
            """
            DELETE FROM tracked_server_guilds
            WHERE server_id = %s
            AND guild_id = %s
            """,
            (self._server_id, guild_id)
        )

    @ensure_cursor
    def get_tracked_guild_count(
        self,
        *,
        cursor: Cursor = None
    ) -> int:
        cursor.execute(
            """
            SELECT COUNT(*) AS total
            FROM tracked_server_guilds
            WHERE server_id = %s
            """,
            (self._server_id,)
        )

        row = cursor.fetchone()
        return row["total"] if row else 0
    
    @ensure_cursor
    def get_tracked_server_guilds(self, *, cursor: Cursor) -> list[TrackedServerGuilds]:
        cursor.execute(
            "SELECT * FROM tracked_server_guilds WHERE server_id=%s",
            (self._server_id,)
        )

        rows = cursor.fetchall()
        return [TrackedServerGuilds(**row) for row in rows] if rows else []


class GuildHandler:
    def __init__(self, guild_id: int | None = None) -> None:
        self._guild_id = guild_id

    @ensure_cursor
    def insert_guild(
        self,
        guild_id: int,
        guild_gxp: int,
        *,
        cursor: Cursor=None
    ) -> None:
        cursor.execute(
            """
            INSERT IGNORE INTO tracked_guilds (guild_id, guild_xp)
            VALUES (%s, %s)
            """,
            (guild_id, guild_gxp)
        )


    @async_ensure_cursor
    async def insert_guild_players(
        self,
        players: list,
        *,
        cursor: Cursor
    ) -> None:
        semaphore = asyncio.Semaphore(10)

        async def process_player(player):
            async with semaphore:
                uuid: str = player["uuid"]
                uuid = uuid.replace("-", "")
                
                player_data = await PlayerInfo.fetch(uuid)
                if not player_data:
                    return None

                return (
                    player_data.uuid.replace("-", ""),
                    self._guild_id,
                    player_data.level,
                    player_data.exp,
                    0.0
                )

        results = await asyncio.gather(*(process_player(p) for p in players))
        values = [r for r in results if r is not None]

        if not values:
            return

        cursor.executemany(
            """
            INSERT IGNORE INTO tracked_players 
            (uuid, guild_id, level, xp, highest_week)
            VALUES (%s, %s, %s, %s, %s)
            """,
            values
        )


    @ensure_cursor
    def set_guild(
        self,
        uuid: str,
        guild_id: int, 
        *,
        cursor: Cursor = None
    ) -> None:
        cursor.execute(
            "UPDATE tracked_players SET guild_id=%s WHERE uuid=%s",
            (guild_id, uuid,)
        )


    @ensure_cursor
    def get_all_tracked_guilds(self, *, cursor: Cursor=None) -> list[TrackedGuilds]:
        cursor.execute("SELECT * FROM tracked_guilds")

        rows = cursor.fetchall()
        return [TrackedGuilds(**row) for row in rows] if rows else []
    

    @ensure_cursor
    def get_all_tracked_server_guilds(self, *, cursor: Cursor=None) -> list[TrackedServerGuilds]:
        cursor.execute("SELECT * FROM tracked_server_guilds")

        rows = cursor.fetchall()
        return [TrackedServerGuilds(**row) for row in rows] if rows else []


    @ensure_cursor
    def get_old_guild_members(self, *, cursor: Cursor = None) -> list[str]:
        if not self._guild_id:
            return []

        cursor.execute(
            """
            SELECT uuid FROM tracked_players
            WHERE guild_id = %s
            """,
            (self._guild_id,)
        )

        rows = cursor.fetchall()
        return [row["uuid"] for row in rows] if rows else []


    @ensure_cursor
    def get_player(self, uuid: str, *, cursor: Cursor = None):
        cursor.execute(
            "SELECT uuid FROM tracked_players WHERE uuid = %s",
            (uuid,)
        )
        return cursor.fetchone()


    @ensure_cursor
    def get_player_full(
        self,
        uuid: str,
        *,
        cursor: Cursor = None
    ) -> TrackedPlayers | None:
        cursor.execute(
            """
            SELECT *
            FROM tracked_players
            WHERE uuid = %s
            """,
            (uuid,)
        )

        row = cursor.fetchone()
        return TrackedPlayers(**row) if row else None


    @async_ensure_cursor
    async def insert_player(
        self,
        uuid: str,
        guild_id: int,
        *,
        cursor: Cursor
    ):
        uuid = uuid.replace("-", "")

        player_data = await PlayerInfo.fetch(uuid)
        if not player_data:
            return

        cursor.execute(
            """
            INSERT INTO tracked_players 
            (uuid, guild_id, level, xp, highest_week)
            VALUES (%s, %s, %s, %s, 0.0)
            """,
            (
                player_data.uuid.replace("-", ""),
                guild_id,
                player_data.level,
                player_data.exp
            )
        )


    @ensure_cursor
    def get_all_players(self, *, cursor: Cursor):
        cursor.execute(
            """
            SELECT * FROM tracked_players
            WHERE guild_id IS NOT NULL
            """
        )

        rows = cursor.fetchall()
        return [TrackedPlayers(**row) for row in rows] if rows else []


    @ensure_cursor
    def get_guild_players(self, guild_id: int, *, cursor: Cursor):
        cursor.execute(
            """
            SELECT * FROM tracked_players
            WHERE guild_id = %s
            """,
            (guild_id,)
        )

        rows = cursor.fetchall()
        return [TrackedPlayers(**row) for row in rows] if rows else []


    @ensure_cursor
    def update_player(
        self,
        uuid: str,
        level: int,
        xp: int,
        *,
        cursor: Cursor
    ):
        cursor.execute(
            """
            UPDATE tracked_players
            SET level = %s, xp = %s
            WHERE uuid = %s
            """,
            (level, xp, uuid)
        )


    @ensure_cursor
    def insert_player_past_week(
        self,
        uuid: str,
        week: int,
        stars: float,
        *,
        cursor: Cursor
    ):
        cursor.execute(
            """
            INSERT INTO player_past_weeks (uuid, week, stars)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE
                stars = VALUES(stars)
            """,
            (uuid, week, stars)
        )
        
        
    @ensure_cursor
    def update_guild_xp(
        self,
        guild_id: int,
        guild_xp: int,
        *,
        cursor: Cursor
    ):
        cursor.execute(
            """
            UPDATE tracked_guilds
            SET guild_xp = %s
            WHERE guild_id = %s
            """,
            (guild_xp, guild_id)
        )
        

    @ensure_cursor
    def get_player_past_weeks(
        self,
        uuid: str,
        *,
        cursor: Cursor
    ) -> list[float]:
        cursor.execute(
            """
            SELECT stars FROM player_past_weeks
            WHERE uuid = %s
            ORDER BY week DESC
            LIMIT 5
            """,
            (uuid,)
        )

        rows = cursor.fetchall()
        return [row["stars"] for row in rows] if rows else []


    @ensure_cursor
    def get_player_highest_week(
        self,
        uuid: str,
        *,
        cursor: Cursor
    ) -> float:
        cursor.execute(
            """
            SELECT MAX(stars) AS highest
            FROM player_past_weeks
            WHERE uuid = %s
            """,
            (uuid,)
        )

        row = cursor.fetchone()
        return float(row["highest"]) if row and row["highest"] is not None else 0.0


class LastWeekHandler:
    @ensure_cursor
    def get_last_week(self, *, cursor: Cursor = None) -> Optional[LastWeekUpdates]:
        cursor.execute("SELECT * FROM last_week_updates WHERE id = 1")
        row = cursor.fetchone()
        return LastWeekUpdates(**row) if row else None


    @ensure_cursor
    def update_xp_week(self, *, cursor: Cursor = None):
        cursor.execute(
            """
            UPDATE last_week_updates
            SET xp_chart = %s
            WHERE id = 1
            """,
            (get_current_week(),)
        )


    @ensure_cursor
    def update_gxp_week(self, *, cursor: Cursor = None):
        cursor.execute(
            """
            UPDATE last_week_updates
            SET gxp_chart = %s
            WHERE id = 1
            """,
            (get_current_week(),)
        )