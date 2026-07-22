import time
from typing import Optional, Literal, Sequence
from dataclasses import dataclass

from core.database import ensure_cursor, Cursor


BlacklistTarget = Literal["user", "role"]


@dataclass(slots=True)
class AccountData:
    discord_id: int
    created_at: int


@dataclass(slots=True)
class BlacklistData:
    id: int
    guild_id: int
    target_type: BlacklistTarget
    target_id: int


class Account:
    def __init__(self, discord_id: int):
        self._discord_id = discord_id

    @ensure_cursor
    def create(self, *, cursor: Cursor = None,) -> bool:
        cursor.execute(
            """
            INSERT IGNORE INTO accounts (
                discord_id,
                created_at
            )
            VALUES (%s, %s)
            """,
            (
                self._discord_id,
                int(time.time()),
            ),
        )

        return cursor.rowcount > 0

    @ensure_cursor
    def get_account(
        self,
        *,
        cursor: Cursor = None,
    ) -> Optional[AccountData]:
        cursor.execute(
            """
            SELECT
                discord_id,
                created_at
            FROM accounts
            WHERE discord_id = %s
            """,
            (self._discord_id,),
        )

        row = cursor.fetchone()

        return AccountData(**row) if row else None
    

class Blacklist:
    def __init__(
        self,
        target_id: int,
        target_type: BlacklistTarget,
        guild_id: int = 0,
    ):
        self._target_id = target_id
        self._target_type = target_type
        self._guild_id = guild_id

    @ensure_cursor
    def add(
        self,
        *,
        cursor: Cursor = None,
    ) -> bool:
        cursor.execute(
            """
            INSERT IGNORE INTO blacklists (
                guild_id,
                target_type,
                target_id
            )
            VALUES (%s, %s, %s)
            """,
            (
                self._guild_id,
                self._target_type,
                self._target_id,
            ),
        )

        return cursor.rowcount > 0

    @ensure_cursor
    def remove(
        self,
        *,
        cursor: Cursor = None,
    ) -> bool:
        cursor.execute(
            """
            DELETE FROM blacklists
            WHERE guild_id = %s
              AND target_type = %s
              AND target_id = %s
            """,
            (
                self._guild_id,
                self._target_type,
                self._target_id,
            ),
        )

        return cursor.rowcount > 0

    @ensure_cursor
    def get(
        self,
        *,
        cursor: Cursor = None,
    ) -> Optional[BlacklistData]:
        cursor.execute(
            """
            SELECT
                id,
                guild_id,
                target_type,
                target_id
            FROM blacklists
            WHERE guild_id = %s
              AND target_type = %s
              AND target_id = %s
            LIMIT 1
            """,
            (
                self._guild_id,
                self._target_type,
                self._target_id,
            ),
        )

        row = cursor.fetchone()

        return BlacklistData(**row) if row else None

    @staticmethod
    @ensure_cursor
    def find_match(
        discord_id: int,
        guild_id: int,
        role_ids: Sequence[int],
        *,
        cursor: Cursor = None,
    ) -> Optional[BlacklistData]:
        role_ids = list({int(role_id) for role_id in role_ids})

        cursor.execute(
            """
            SELECT
                id,
                guild_id,
                target_type,
                target_id
            FROM blacklists
            WHERE target_type = 'user'
            AND target_id = %s
            AND guild_id IN (0, %s)
            LIMIT 1
            """,
            (
                discord_id,
                guild_id,
            ),
        )

        row = cursor.fetchone()

        if row:
            return BlacklistData(**row)

        if not role_ids:
            return None

        placeholders = ", ".join(["%s"] * len(role_ids))

        cursor.execute(
            f"""
            SELECT
                id,
                guild_id,
                target_type,
                target_id
            FROM blacklists
            WHERE target_type = 'role'
            AND guild_id = %s
            AND target_id IN ({placeholders})
            LIMIT 1
            """,
            (
                guild_id,
                *role_ids,
            ),
        )

        row = cursor.fetchone()

        return BlacklistData(**row) if row else None