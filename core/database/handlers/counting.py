from dataclasses import dataclass

from core.database import ensure_cursor, Cursor


@dataclass(slots=True)
class CountingData:
    guild_id: int
    enabled: bool


class CountingHandler:
    def __init__(self, guild_id: int):
        self.guild_id = guild_id

    @ensure_cursor
    def set_counting(
        self,
        enabled: bool,
        *,
        cursor: Cursor = None
    ):
        cursor.execute(
            """
            INSERT INTO counting (guild_id, enabled)
            VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE 
                enabled=VALUES(enabled)
            """,
            (self.guild_id, enabled,)
        )

    @ensure_cursor
    def get_counting(self, *, cursor: Cursor=None) -> CountingData | None:
        cursor.execute(
            "SELECT * FROM counting WHERE guild_id=%s", (self.guild_id,)
        )
        result = cursor.fetchone()

        return CountingData(**result) if result else None


