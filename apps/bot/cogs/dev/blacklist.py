import os

from discord import app_commands, Interaction, Member, Role
from discord.ext import commands
from dotenv import load_dotenv

from core import logger
from core.accounts import Blacklist as BlacklistHandler


load_dotenv()

DEVELOPER_ID = int(os.environ.get("DEVELOPER_ID", "0"))


class Blacklist(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client

    @app_commands.command(
        name="blacklist",
        description="Add or remove a user or role from the blacklist.",
    )
    @app_commands.describe(
        target="The user or role to modify",
        blacklisted="Whether the target should be blacklisted",
    )
    @app_commands.guild_only()
    async def blacklist(
        self,
        interaction: Interaction,
        target: Member | Role,
        blacklisted: bool,
    ):
        await interaction.response.defer(ephemeral=True)

        try:
            if interaction.user.id != DEVELOPER_ID:
                return await interaction.edit_original_response(
                    content="You do not have permission to execute this command."
                )

            if isinstance(target, Role):
                if target.is_default():
                    return await interaction.edit_original_response(
                        content="You cannot blacklist the `@everyone` role."
                    )

                handler = BlacklistHandler(
                    target_id=target.id,
                    target_type="role",
                    guild_id=interaction.guild.id,
                )

                target_name = f"@{target.name}"
                target_type = "role"

            else:
                if target.bot:
                    return await interaction.edit_original_response(
                        content="You cannot blacklist a bot account."
                    )

                handler = BlacklistHandler(
                    target_id=target.id,
                    target_type="user",
                    guild_id=0,
                )

                target_name = target.name
                target_type = "user"

            if blacklisted:
                changed = handler.add()
                status = "blacklisted"

                if not changed:
                    return await interaction.edit_original_response(
                        content=(
                            f"The {target_type} **{target_name}** is already "
                            "blacklisted."
                        )
                    )

            else:
                changed = handler.remove()
                status = "unblacklisted"

                if not changed:
                    return await interaction.edit_original_response(
                        content=(
                            f"The {target_type} **{target_name}** is not "
                            "currently blacklisted."
                        )
                    )

            await interaction.edit_original_response(
                content=(
                    f"The {target_type} **{target_name}** has been "
                    f"`{status}`."
                )
            )

        except Exception:
            logger.exception("Unhandled exception in blacklist command")

            await interaction.edit_original_response(
                content=(
                    "Something went wrong. If this issue persists, please "
                    "contact a **Shine Administrator**."
                )
            )


async def setup(client: commands.Bot) -> None:
    await client.add_cog(Blacklist(client))