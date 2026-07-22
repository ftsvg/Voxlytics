from dataclasses import dataclass

from core.database import ensure_cursor, Cursor


@dataclass(slots=True)
class Application:
    discord_id: int


class ApplicationsHandler:
    def __init__(self, discord_id: int):
        self.discord_id = discord_id

    @ensure_cursor
    def new_application(
        self,
        *,
        cursor: Cursor = None,
    ) -> bool:
        try:
            cursor.execute(
                """
                INSERT INTO applications (discord_id)
                VALUES (%s)
                """,
                (self.discord_id,),
            )
        except Exception:
            return False

        return cursor.rowcount > 0

    @ensure_cursor
    def get_application(
        self,
        *,
        cursor: Cursor = None,
    ) -> Application | None:
        cursor.execute(
            """
            SELECT discord_id
            FROM applications
            WHERE discord_id = %s
            """,
            (self.discord_id,),
        )

        result = cursor.fetchone()

        return Application(**result) if result else None

    @ensure_cursor
    def remove_application(
        self,
        *,
        cursor: Cursor = None,
    ) -> bool:
        cursor.execute(
            """
            DELETE FROM applications
            WHERE discord_id = %s
            """,
            (self.discord_id,),
        )

        return cursor.rowcount > 0