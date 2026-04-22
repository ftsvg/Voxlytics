import os
from typing import Optional
from dataclasses import dataclass

from core.database import Cursor, ensure_cursor


@dataclass(slots=True)
class BackgroundUserConfig:
    discord_id: int
    background_id: int


class BackgroundHandler:
    def __init__(self, discord_id: int):
        self.discord_id = discord_id


    @ensure_cursor
    def get_background_config(self, *, cursor: Cursor=None) -> Optional[BackgroundUserConfig]:
        cursor.execute(
            "SELECT * FROM backgrounds WHERE discord_id=%s", (self.discord_id,)
        )

        row = cursor.fetchone()
        return BackgroundUserConfig(**row) if row else None


    @ensure_cursor
    def update_background(self, background_id: int, *, cursor: Cursor=None) -> None:
        cursor.execute(
            """
            INSERT INTO backgrounds (discord_id, background_id)
            VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE background_id = VALUES(background_id);
            """,
            (self.discord_id, background_id,)
        )


def load_background_for_user(discord_id: int) -> bytes:
    handler = BackgroundHandler(discord_id)
    bg = handler.get_background_config()

    background_id = bg.background_id if bg else 1
    bg_path = f"./assets/bg/{background_id}.png"

    if not os.path.exists(bg_path):
        raise Exception(f"No such theme at '{bg_path}'")
    
    with open(bg_path, "rb") as img_file:
        return img_file.read()