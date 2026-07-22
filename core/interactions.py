from dataclasses import dataclass
from typing import Literal, Optional, Sequence

from core.accounts import Account, Usage, Blacklist


Status = Literal["ok", "new_user", "blacklisted"]


@dataclass(slots=True)
class InteractionResult:
    status: Status
    message: Optional[str] = None


async def interaction_check(
    discord_id: int,
    guild_id: int,
    role_ids: Sequence[int],
    command_name: str,
) -> InteractionResult:
    account_handler = Account(discord_id)
    account = account_handler.get_account()

    new_user = False

    if account is None:
        account_handler.create()
        new_user = True

    blacklist = Blacklist.find_match(
        discord_id=discord_id,
        guild_id=guild_id,
        role_ids=role_ids,
    )

    if blacklist is not None:
        return InteractionResult(
            status="blacklisted",
            message=(
                "Your account is currently blacklisted from using "
                "**Shine Bot** commands.\n"
                "- If you think this is an error, you can create a ticket."
                ""
            ),
        )

    Usage(discord_id, command_name).update_usage()

    return InteractionResult(
        status="new_user" if new_user else "ok",
    )