from typing import Optional

from core.database import ensure_cursor, Cursor, Milestone


class MilestoneHandler:
    def __init__(self, discord_id: int, uuid: str) -> None:
        self._discord_id = discord_id
        self._uuid = uuid
        

    @ensure_cursor
    def update_milestone(
        self,
        type: str,
        value: int,
        threshold: int,
        *, 
        cursor: Cursor=None
    ) -> None:
        
        cursor.execute(
            """
            INSERT INTO milestones (discord_id, uuid, type, value, threshold)
            VALUES (%s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                value=VALUES(value),
                threshold=VALUES(threshold),
                notified=FALSE;
            """,
            (self._discord_id, self._uuid, type, value, threshold)
        )

    
    @ensure_cursor
    def get_milestone(
        self,
        type: str, 
        *,
        cursor: Cursor
    ) -> Optional[Milestone]:
        
        cursor.execute(
            "SELECT * FROM milestones WHERE discord_id=%s AND uuid=%s AND type=%s",
            (self._discord_id, self._uuid, type,)
        )

        row = cursor.fetchone()
        return Milestone(**row) if row else None
    

    @ensure_cursor
    def set_notified(self, type: str, *, cursor: Cursor=None) -> None:
        cursor.execute(
            """
            UPDATE milestones
            SET notified=TRUE
            WHERE discord_id=%s AND uuid=%s AND type=%s
            """,
            (self._discord_id, self._uuid, type,)
        )


    @staticmethod
    @ensure_cursor
    def get_active_milestones(*, cursor: Cursor=None) -> list[Milestone]:
        cursor.execute(
            "SELECT * FROM milestones WHERE notified=FALSE"
        )
        return [Milestone(**row) for row in cursor.fetchall()]


    @ensure_cursor
    def get_all_milestones(self, *, cursor: Cursor = None) -> list[Milestone]:
        cursor.execute(
            "SELECT * FROM milestones WHERE discord_id=%s",
            (self._discord_id,)
        )
        return [Milestone(**row) for row in cursor.fetchall()]
    

    @ensure_cursor
    def remove_milestone(
        self,
        type: str,
        *,
        cursor: Cursor = None
    ) -> bool:
        
        cursor.execute(
            """
            DELETE FROM milestones
            WHERE discord_id=%s AND uuid=%s AND type=%s
            """,
            (self._discord_id, self._uuid, type)
        )

        return cursor.rowcount > 0