from discord.ext import commands
from discord import app_commands, Interaction
from mcfetch import Player

from core import check_if_valid_ign, mojang_session, logger
from core.database.handlers import UserHandler


class Linking(commands.Cog):
    def __init__(self, client):
        self.client: commands.Bot = client


    @app_commands.command(
        name="link", 
        description="Link your account"
    )
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.describe(player="The player you want to link to")
    async def link(
        self,
        interaction: Interaction,
        player: str,
    ):
        await interaction.response.defer()
        try:
            if not (uuid := await check_if_valid_ign(interaction, player)):
                return None
            
            handler = UserHandler(interaction.user.id)
            handler.link_player(uuid)

            ign = Player(player=uuid, requests_obj=mojang_session).name

            await interaction.edit_original_response(
                content=f"You have successfully linked as **{ign}**."
            )

        except Exception as error:
            logger.exception(f"Unhandled exception: {error}")

            await interaction.edit_original_response(
                content="Something went wrong. If this issue persists, please contact the **Voxlytics Dev Team**."
            )


    @app_commands.command(
        name="unlink", 
        description="Unlink your account"
    )
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    @app_commands.allowed_installs(guilds=True, users=True)
    async def unlink(
        self, 
        interaction: Interaction
    ):
        await interaction.response.defer()
        try:
            handler = UserHandler(interaction.user.id)
            user = handler.get_player()

            if not user:
                return await interaction.edit_original_response(
                    content="You don't have an account linked! Use **/link** to link your account."
                )
            
            handler.unlink_player()

            await interaction.edit_original_response(
                content="You have been successfully unlinked."
            )


        except Exception as error:
            logger.exception(f"Unhandled exception: {error}")

            await interaction.edit_original_response(
                content="Something went wrong. If this issue persists, please contact the **Voxlytics Dev Team**."
            )


async def setup(client: commands.Bot) -> None:
    await client.add_cog(Linking(client))