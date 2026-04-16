from dataclasses import dataclass

from core.database import ensure_cursor, Cursor


@dataclass(slots=True)
class CommandUsage:
    command: str
    discord_id: int
    times_used: int


class Usage:
    def __init__(
        self,
        discord_id: int | None = None,
        command: str | None = None
    ) -> None:
        self._discord_id = discord_id
        self._command = command

    @ensure_cursor
    def update_usage(self, *, cursor: Cursor=None):
        cursor.execute(
            """
            INSERT INTO command_usage (command, discord_id, times_used)
            VALUES (%s, %s, 1)
            ON DUPLICATE KEY UPDATE times_used = times_used + 1
            """,
            (self._command, self._discord_id,)
        )


    @ensure_cursor
    def get_usage(self, *, cursor: Cursor = None) -> list[CommandUsage]:
        cursor.execute("SELECT command, discord_id, times_used FROM command_usage")
        rows = cursor.fetchall()

        if not rows:
            return []

        return [
            CommandUsage(
                command=row["command"],
                discord_id=row["discord_id"],
                times_used=row["times_used"]
            )
            for row in rows
        ]


    @ensure_cursor
    def get_top_lactate_users(self, *, cursor: Cursor = None) -> list[CommandUsage]:
        cursor.execute(
            """
            SELECT command, discord_id, times_used
            FROM command_usage
            WHERE command = %s
            ORDER BY times_used DESC
            LIMIT 10
            """,
            ("lactate",)
        )
        rows = cursor.fetchall()

        if not rows:
            return []

        return [
            CommandUsage(
                command=row["command"],
                discord_id=row["discord_id"],
                times_used=row["times_used"]
            )
            for row in rows
        ]