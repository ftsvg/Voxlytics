from discord.ext import commands
from discord import app_commands, Interaction, TextChannel

from core import logger, interaction_check
from core.database.handlers import LeaderboardHandler


class Updates(commands.Cog):
    def __init__(self, client):
        self.client: commands.Bot = client

    @app_commands.command(
        name="updates", description="Setup leaderboard updates channel"
    )
    @app_commands.describe(channel="Channel where leaderboard updates will be sent")
    async def updates(self, interaction: Interaction, channel: TextChannel):
        await interaction.response.defer()
        try:
            result = await interaction_check(interaction.user.id, 'updates')
            if result.status == "blacklisted":
                return await interaction.edit_original_response(
                    content=result.message
                )

            if not interaction.user.guild_permissions.administrator:
                return await interaction.edit_original_response(
                    content=(
                        "You don't have the permissions to execute this command. Please ask a server admin to configure the **Leaderboard Updates Channel**"
                    )
                )

            LeaderboardHandler().update_channel(interaction.guild.id, channel.id)
            return await interaction.edit_original_response(
                content=f"Leaderboard updates channel set to: {channel.mention}"
            )

        except Exception as error:
            logger.exception(f"Unhandled exception: {error}")

            await interaction.edit_original_response(
                content="Something went wrong. If this issue persists, please contact the **Voxlytics Dev Team**."
            )


async def setup(client: commands.Bot) -> None:
    await client.add_cog(Updates(client))
