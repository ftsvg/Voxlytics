from discord.ext import commands
from discord import app_commands, Interaction

from core import historical_interaction


class Historical(commands.Cog):
    def __init__(self, client):
        self.client = client

    @app_commands.command(
        name="historical",
        description="View historical stats"
    )
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.describe(player="The player you want to view")
    async def historical(
        self,
        interaction: Interaction,
        player: str | None = None
    ):
        await interaction.response.defer()
        await historical_interaction(
            interaction, "today", player
        )


async def setup(client: commands.Bot) -> None:
    await client.add_cog(Historical(client)) 