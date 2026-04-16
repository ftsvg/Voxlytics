import os
from discord.ext import commands
from discord import app_commands, Interaction
from dotenv import load_dotenv

from core import logger
from core.accounts import Account

load_dotenv()


class Blacklist(commands.Cog):
    def __init__(self, client):
        self.client: commands.Bot = client

    @app_commands.command(
        name="blacklist", description="Add or Remove a user from the blacklist."
    )
    @app_commands.describe(
        discord_id="The user to modify",
        blacklist="Add or Remove"
    )
    async def blacklist(
        self,
        interaction: Interaction,
        discord_id: str,
        blacklist: bool
    ):
        await interaction.response.defer(ephemeral=True)
        try:
            if interaction.user.id != int(os.environ.get("DEVELOPER_ID")):
                return await interaction.edit_original_response(
                    content="You do not have the permissions to execute this command."
                )
            
            try:
                user = await self.client.fetch_user(int(discord_id))
            except Exception:
                return await interaction.edit_original_response(
                    content="Invalid user or user not found."
                )

            if not user:
                return await interaction.edit_original_response(
                    content="Invalid user."
                )

            Account(discord_id).update_blacklist(blacklist)

            status_text = "blacklisted" if blacklist else "unblacklisted"

            return await interaction.edit_original_response(
                content=f"**{user.name}** has been `{status_text}`."
            )

        except Exception as error:
            logger.exception(f"Unhandled exception: {error}")

            await interaction.edit_original_response(
                content="Something went wrong. If this issue persists, please contact the **Voxlytics Dev Team**."
            )


async def setup(client: commands.Bot) -> None:
    await client.add_cog(Blacklist(client))
