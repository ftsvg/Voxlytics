from core.database import ensure_cursor, Cursor, User


class UserHandler:
    def __init__(self, discord_id: int | None = None) -> None:
        self._discord_id = discord_id

    @ensure_cursor
    def link_player(self, uuid: str, *, cursor: Cursor = None) -> None:
        cursor.execute(
            """
            INSERT INTO users (discord_id, uuid)
            VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE 
                uuid = %s;
            """,
            (self._discord_id, uuid, uuid,)
        )


    @ensure_cursor
    def get_player(
        self,
        *,
        uuid: str | None = None,
        cursor: Cursor = None
    ) -> User | None:

        if self._discord_id is not None:
            cursor.execute(
                "SELECT discord_id, uuid FROM users WHERE discord_id=%s",
                (self._discord_id,)
            )
        elif uuid is not None:
            cursor.execute(
                "SELECT discord_id, uuid FROM users WHERE uuid=%s",
                (uuid,)
            )
        else:
            raise ValueError("Must provide uuid or discord_id")

        row = cursor.fetchone()
        return User(**row) if row else None
    

    @ensure_cursor
    def unlink_player(self, *, cursor: Cursor=None) -> None:
        cursor.execute("DELETE FROM users WHERE discord_id=%s", (self._discord_id,),)        
