
import asyncio
from typing import List 

from mcfetch import Player
from discord import app_commands
from core.api import SKINS_API
from core.api.helpers import PlayerInfo
from core import mojang_session


PAGES: List[app_commands.Choice] = [
    app_commands.Choice(name=f"Page {i}", value=i) for i in range(1, 11)
]

async def leaderboard_fetch_player_data(player: dict) -> dict:
    uuid = str(player["uuid"]).replace("-", "")

    stats_task = PlayerInfo.fetch(uuid)

    ign_task = asyncio.to_thread(
        lambda: Player(player=uuid, requests_obj=mojang_session).name
    )

    skin_task = SKINS_API.fetch_skin_model(uuid, "face")

    stats, ign, skin = await asyncio.gather(
        stats_task,
        ign_task,
        skin_task
    )

    return {
        "uuid": uuid,
        "stats": stats,
        "ign": ign,
        "skin": skin,
    }