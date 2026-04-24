import time
from typing import Optional
from dataclasses import dataclass

from core.database import ensure_cursor, Cursor


@dataclass
class AccountData:
    discord_id: int
    created_at: int
    blacklisted: bool


class Account:
    def __init__(self, discord_id: int):
        self._discord_id = discord_id

    @ensure_cursor
    def create(
        self,
        *,
        cursor: Cursor = None
    ) -> None:
        cursor.execute(
            "SELECT * FROM accounts WHERE discord_id=%s",
            (self._discord_id,)
        )
        if cursor.fetchone() is not None:
            return

        cursor.execute(
            "INSERT INTO accounts (discord_id, created_at, blacklisted) VALUES (%s, %s, %s)",
            (self._discord_id, int(time.time()), False)
        )

    
    @ensure_cursor
    def get_account(self, *, cursor: Cursor) -> Optional[AccountData]:
        cursor.execute("SELECT * FROM accounts WHERE discord_id=%s", (self._discord_id,))

        row = cursor.fetchone()
        return AccountData(**row) if row else None

    
    @ensure_cursor
    def update_blacklist(self, blacklisted: bool = False, *, cursor: Cursor = None) -> None:
        cursor.execute(
            """
            INSERT INTO accounts (discord_id, created_at, blacklisted)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE 
                blacklisted = %s
            """,
            (self._discord_id, int(time.time()), blacklisted, blacklisted,)
        )




