from discord.ext import commands
from discord import app_commands, Interaction

from core import historical_interaction, logger, PERIODS, interaction_check
from core.database.handlers import UserHandler, HistoricalHandler
from core.api.helpers import PlayerInfo


class Historical(commands.Cog):
    def __init__(self, client):
        self.client: commands.Bot = client

    historical = app_commands.Group(
        name="historical", 
        description="Historical related commands",
        allowed_contexts=app_commands.AppCommandContext(guild=True, dm_channel=True, private_channel=True),
        allowed_installs=app_commands.AppInstallationType(guild=True, user=True)
    )


    @historical.command(
        name="daily", 
        description="View the daily stats of a player"
    )
    @app_commands.describe(
        player="The player you want to view"
    )
    async def daily(self, interaction: Interaction, player: str = None):
        await interaction.response.defer()
        await historical_interaction(interaction, "daily", player)


    @historical.command(
        name="weekly", 
        description="View the weekly stats of a player"
    )
    @app_commands.describe(
        player="The player you want to view"
    )
    async def weekly(self, interaction: Interaction, player: str = None):
        await interaction.response.defer()
        await historical_interaction(interaction, "weekly", player)


    @historical.command(
        name="monthly", 
        description="View the monthly stats of a player"
    )
    @app_commands.describe(
        player="The player you want to view"
    )
    async def monthly(self, interaction: Interaction, player: str = None):
        await interaction.response.defer()
        await historical_interaction(interaction, "monthly", player)


    @historical.command(
        name="yearly", 
        description="View the yearly stats of a player"
    )
    @app_commands.describe(player="The player you want to view")
    async def yearly(self, interaction: Interaction, player: str = None):
        await interaction.response.defer()
        await historical_interaction(interaction, "yearly", player)

    
    @historical.command(
        name="reset",
        description="Reset your historical stats"
    )
    async def reset(
        self, interaction: Interaction
    ):
        await interaction.response.defer()
        try:
            result = await interaction_check(interaction.user.id, 'compare')
            if result.status == "blacklisted":
                return await interaction.edit_original_response(
                    content=result.message
                )

            user_handler = UserHandler(interaction.user.id)
            user = user_handler.get_player()

            if not user:
                return await interaction.edit_original_response(
                    content="You don't have an account linked! Use **/link** to link your account."
                )
            uuid = user.uuid
            player_data = await PlayerInfo.fetch(uuid)

            for p in PERIODS:
                HistoricalHandler(uuid, p).update_historical(player_data)
        
            return await interaction.edit_original_response(
                content=f"Historical stats have been reset."
            )                

        except Exception as error:
            logger.exception(f"Unhandled exception: {error}")

            await interaction.edit_original_response(
                content="Something went wrong. If this issue persists, please contact the **Voxlytics Dev Team**."
            )


async def setup(client: commands.Bot) -> None:
    await client.add_cog(Historical(client)) 