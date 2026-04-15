from typing import Optional, Tuple
from discord import Interaction
import mcfetch

from core import mojang_session
from core.api.helpers import PlayerInfo
from .database.handlers import UserHandler


async def not_exist_message(interaction: Interaction, player: str) -> None:
    await interaction.edit_original_response(
        content=f"**{player}** does not exist! Please provide a valid player."
    )


async def check_if_ever_played(
    interaction: Interaction,
    player: PlayerInfo
) -> bool:
    if isinstance(player.player_info, dict) and "error" in player.player_info:
        err = player.player_info["error"]

        if err == 429:
            await interaction.edit_original_response(
                content="We are being rate limited. Please try again later."
            )
            return False

        await interaction.edit_original_response(content="Failed to fetch player data.")
        return False

    if player.last_login_time is None:
        await interaction.edit_original_response(
            content="This player has never played on **bedwarspractice.club** before."
        )
        return False

    return True


async def check_if_linked(
    interaction: Interaction,
    player: Optional[str],
) -> Optional[str]:
    if player is None:
        linked = UserHandler(interaction.user.id).get_player()

        if linked:
            player = mcfetch.Player(
                player=linked.uuid,
                requests_obj=mojang_session,
            ).name

        if not player:
            await interaction.edit_original_response(
                content="You are not linked! Either specify a player or link your account using **/link**"
            )
            return None

    return player



async def check_if_valid_ign(
    interaction: Interaction,
    player: str | None,
) -> str | None:
    if not player or not isinstance(player, str):
        await not_exist_message(interaction, player)
        return None

    if len(player) > 16:
        await not_exist_message(interaction, player)
        return None

    try:
        uuid = mcfetch.Player(
            player=player,
            requests_obj=mojang_session,
        ).uuid 

    except Exception:
        await interaction.edit_original_response(
            content="Mojang API failed. Please try again."
        )
        return None

    if not uuid:
        await not_exist_message(interaction, player)
        return None

    return uuid


async def fetch_player(
    interaction: Interaction,
    player: Optional[str],
) -> Optional[Tuple[str, PlayerInfo]]:
    try:
        if not (player := await check_if_linked(interaction, player)):
            return None

        if not (uuid := await check_if_valid_ign(interaction, player)):
            return None

        player_obj = await PlayerInfo.fetch(uuid)

        if not await check_if_ever_played(interaction, player_obj):
            return None

        return uuid, player_obj

    except Exception:
        await interaction.edit_original_response(
            content="The API is currently down. If this issue persists, please contact the **VoxStats Dev Team**."
        )
        return None
