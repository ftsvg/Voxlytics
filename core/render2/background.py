import os
from typing import Optional
from dataclasses import dataclass

from core.database import Cursor, ensure_cursor


@dataclass(slots=True)
class BackgroundUserConfig:
    discord_id: int
    background_id: int


@dataclass(slots=True)
class AllBackgrounds:
    id: int
    name: str
    extension: str


class BackgroundHandler:
    def __init__(self, discord_id: int | None = None):
        self.discord_id = discord_id

    @ensure_cursor
    def get_background_config(self, *, cursor: Cursor = None) -> Optional[BackgroundUserConfig]:
        cursor.execute(
            "SELECT * FROM backgrounds WHERE discord_id=%s",
            (self.discord_id,)
        )

        row = cursor.fetchone()
        return BackgroundUserConfig(**row) if row else None

    @ensure_cursor
    def update_background(self, background_id: int, *, cursor: Cursor = None) -> None:
        cursor.execute(
            """
            INSERT INTO backgrounds (discord_id, background_id)
            VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE
                background_id=VALUES(background_id)
            """,
            (self.discord_id, background_id)
        )

    @ensure_cursor
    def get_background(self, background_id: int, *, cursor: Cursor = None) -> AllBackgrounds | None:
        cursor.execute(
            "SELECT * FROM all_backgrounds WHERE id=%s",
            (background_id,)
        )

        row = cursor.fetchone()
        return AllBackgrounds(**row) if row else None

    @ensure_cursor
    def get_all_backgrounds(self, *, cursor: Cursor = None) -> list[AllBackgrounds]:
        cursor.execute(
            "SELECT * FROM all_backgrounds ORDER BY id"
        )

        return [AllBackgrounds(**row) for row in cursor.fetchall()]

    @ensure_cursor
    def upload_background(
        self,
        name: str,
        extension: str,
        *,
        cursor: Cursor = None
    ) -> None:
        cursor.execute(
            """
            INSERT INTO all_backgrounds (name, extension)
            VALUES (%s, %s)
            """,
            (name, extension)
        )

    @ensure_cursor
    def delete_background(
        self,
        background_id: int,
        *,
        cursor: Cursor = None
    ) -> bool:
        cursor.execute(
            """
            UPDATE backgrounds
            SET background_id=1
            WHERE background_id=%s
            """,
            (background_id,)
        )

        cursor.execute(
            """
            DELETE FROM all_backgrounds
            WHERE id=%s
            """,
            (background_id,)
        )

        return cursor.rowcount > 0


def load_background_for_user(discord_id: int) -> bytes:
    handler = BackgroundHandler(discord_id)
    config = handler.get_background_config()

    background_id = config.background_id if config else 1
    background = handler.get_background(background_id)

    if background is None:
        background = handler.get_background(1)

    bg_path = f"./assets/bg/{background.id}.{background.extension}"

    if not os.path.exists(bg_path):
        raise FileNotFoundError(bg_path)

    with open(bg_path, "rb") as fp:
        return fp.read()