from dataclasses import dataclass
from typing import Literal

from core.accounts import Account, AccountData, Usage

Status = Literal["ok", "new_user", "blacklisted"]


@dataclass(slots=True)
class InteractionResult:
    status: Status
    message: str


async def interaction_check(
    discord_id: int,
    command_name: str,
) -> InteractionResult:

    account_handler = Account(discord_id)
    account: AccountData = account_handler.get_account()

    if not account:
        account_handler.create()
        return InteractionResult(
            status="new_user",
            message=(
                "Hey there! It looks like this is your first time here. 👋\n"
                "If you need help getting started, check out `/help`."
            )
        )
    
    if account.blacklisted:
        return InteractionResult(
            status="blacklisted",
            message=(
                "Your account is currently blacklisted from using Voxlytics commands.\n"
                "- If you think this is an error, you can submit an [appeal here](<https://voxlytics.net/discord>)"
            )
        )
    
    Usage(discord_id, command_name).update_usage()

    return InteractionResult(
        status="ok",
        message=None
    )