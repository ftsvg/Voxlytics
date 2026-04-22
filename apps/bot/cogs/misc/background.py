import os
from dotenv import load_dotenv

from discord.ext import commands
from discord import app_commands, Interaction, Attachment

from core.database.handlers import UserHandler
from core import logger, interaction_check
from core.render2 import BackgroundHandler

load_dotenv()


class Backgrounds(commands.Cog):
    def __init__(self, client):
        self.client: commands.Bot = client

    background = app_commands.Group(
        name="background",
        description="Background related commands",
        allowed_contexts=app_commands.AppCommandContext(
            guild=True, dm_channel=True, private_channel=True
        ),
        allowed_installs=app_commands.AppInstallationType(guild=True, user=True),
    )


    @background.command(
        name="set",
        description="Set your background image"
    )
    @app_commands.choices(
        background=[
            app_commands.Choice(name="Default (BWP Lobby)", value=1),
            app_commands.Choice(name="Statue (VoidFight Map)", value=2),
            app_commands.Choice(name="Oak Lodge", value=3),
            app_commands.Choice(name="Windmill", value=4),
            app_commands.Choice(name="Pondsai (PearlFight Map)", value=5),
        ]
    )
    @app_commands.describe(background="The background image you want to select")
    async def set(
        self, 
        interaction: Interaction,
        background: app_commands.Choice[int]
    ):
        await interaction.response.defer()
        try:
            result = await interaction_check(interaction.user.id, 'background_set')
            if result.status == "blacklisted":
                return await interaction.edit_original_response(
                    content=result.message
                )

            handler = UserHandler(interaction.user.id)
            user = handler.get_player()

            if not user:
                return await interaction.edit_original_response(
                    content="You don't have an account linked! Use **/link** to link your account."
                )
            
            BackgroundHandler(interaction.user.id).update_background(background.value)

            await interaction.edit_original_response(
                content=f"Background updated to **{background.name}**!"
            )

        except Exception as error:
            logger.exception(f"Unhandled exception: {error}")

            await interaction.edit_original_response(
                content="Something went wrong. If this issue persists, please contact the **Voxlytics Dev Team**."
            )


    @background.command(
        name="request",
        description="Request a custom background"
    )
    @app_commands.describe(background_image="Upload your background image")
    async def request(
        self, 
        interaction: Interaction,
        background_image: Attachment
    ):
        await interaction.response.defer()
        try:
            result = await interaction_check(interaction.user.id, 'background_set')
            if result.status == "blacklisted":
                return await interaction.edit_original_response(
                    content=result.message
                )

            handler = UserHandler(interaction.user.id)
            user = handler.get_player()

            if not user:
                return await interaction.edit_original_response(
                    content="You don't have an account linked! Use **/link** to link your account."
                )
            
            file = await background_image.to_file()
            channel = self.client.get_channel(int(os.getenv("REQUEST_CHANNEL")))

            await channel.send(
                content=f"New background request from **{interaction.user}**!",
                file=file
            )

            await interaction.edit_original_response(
                content=f"Background image requested successfully!"
            )

        except Exception as error:
            logger.exception(f"Unhandled exception: {error}")

            await interaction.edit_original_response(
                content="Something went wrong. If this issue persists, please contact the **Voxlytics Dev Team**."
            )


async def setup(client: commands.Bot) -> None:
    await client.add_cog(Backgrounds(client))
