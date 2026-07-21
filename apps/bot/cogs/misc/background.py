import os
from dotenv import load_dotenv

from discord.ext import commands
from discord import app_commands, Interaction, Attachment, Embed

from core.database.handlers import UserHandler
from core import logger, interaction_check, MAIN_COLOR
from core.render2 import BackgroundHandler

from PIL import Image, ImageFilter
import io

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


    async def background_autocomplete(
        self,
        interaction: Interaction,
        current: str,
    ) -> list[app_commands.Choice[int]]:
        backgrounds = BackgroundHandler().get_all_backgrounds()

        return [
            app_commands.Choice(
                name=background.name,
                value=background.id
            )
            for background in backgrounds
            if current.lower() in background.name.lower()
        ][:25]


    @background.command(
        name="set",
        description="Set your background image"
    )
    @app_commands.describe(
        background="The background image you want to select"
    )
    @app_commands.autocomplete(
        background=background_autocomplete
    )
    async def set(
        self,
        interaction: Interaction,
        background: int,
    ):
        try:
            await interaction.response.defer()

            result = await interaction_check(
                interaction.user.id,
                "background_set"
            )

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

            background_handler = BackgroundHandler()

            background_info = background_handler.get_background(background)

            if background_info is None:
                return await interaction.edit_original_response(
                    content="That background no longer exists."
                )

            BackgroundHandler(interaction.user.id).update_background(background)

            await interaction.edit_original_response(
                content=f"Background updated to **{background_info.name}**!"
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
            result = await interaction_check(interaction.user.id, 'background_request')
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
                content="Background image requested successfully!"
            )

        except Exception as error:
            logger.exception(f"Unhandled exception: {error}")

            await interaction.edit_original_response(
                content="Something went wrong. If this issue persists, please contact the **Voxlytics Dev Team**."
            )

    @background.command(
        name="upload",
        description="Upload a new background"
    )
    @app_commands.describe(
        name="The background name",
        background_image="The background image"
    )
    async def upload(
        self,
        interaction: Interaction,
        name: str,
        background_image: Attachment
    ):
        await interaction.response.defer(ephemeral=True)

        if not interaction.user.guild_permissions.administrator:
            return await interaction.edit_original_response(
                content="You do not have permission to execute this command."
            )

        handler = BackgroundHandler()

        backgrounds = handler.get_all_backgrounds()

        next_id = 1 if not backgrounds else max(bg.id for bg in backgrounds) + 1

        extension = background_image.filename.rsplit(".", 1)[-1].lower()

        folder = "./assets/bg"
        os.makedirs(folder, exist_ok=True)

        data = await background_image.read()

        image = Image.open(io.BytesIO(data)).convert("RGB")
        image = image.filter(ImageFilter.GaussianBlur(radius=5))

        image.save(
            f"{folder}/{next_id}.{extension}"
        )

        handler.upload_background(
            name=name,
            extension=extension
        )

        await interaction.edit_original_response(
            content=f"Successfully uploaded **{name}** as background **#{next_id}**."
        )

    @background.command(
        name="list",
        description="List all available backgrounds"
    )
    async def list(
        self,
        interaction: Interaction
    ):
        await interaction.response.defer(ephemeral=True)

        if not interaction.user.guild_permissions.administrator:
            return await interaction.edit_original_response(
                content="You do not have permission to execute this command."
            )

        backgrounds = BackgroundHandler().get_all_backgrounds()

        if not backgrounds:
            return await interaction.edit_original_response(
                content="No backgrounds found."
            )

        embed=Embed(
            title="All Custom Backgrounds",
            description= "\n".join(
                f"**{background.id}.** {background.name}"
                for background in backgrounds
            ),
            color=MAIN_COLOR
        )

        await interaction.edit_original_response(
            embed=embed
        )

    @background.command(
        name="delete",
        description="Delete a background"
    )
    @app_commands.describe(
        background="The background to delete"
    )
    @app_commands.autocomplete(
        background=background_autocomplete
    )
    async def delete(
        self,
        interaction: Interaction,
        background: int
    ):
        await interaction.response.defer(ephemeral=True)

        if not interaction.user.guild_permissions.administrator:
            return await interaction.edit_original_response(
                content="You do not have permission to execute this command."
            )

        if background == 1:
            return await interaction.edit_original_response(
                content="You cannot delete the default background."
            )

        handler = BackgroundHandler()

        background_info = handler.get_background(background)

        if background_info is None:
            return await interaction.edit_original_response(
                content="That background does not exist."
            )

        file_path = f"./assets/bg/{background_info.id}.{background_info.extension}"

        if os.path.exists(file_path):
            os.remove(file_path)

        handler.delete_background(background)

        await interaction.edit_original_response(
            content=f"Successfully deleted **{background_info.name}**."
        )

async def setup(client: commands.Bot) -> None:
    await client.add_cog(Backgrounds(client))
