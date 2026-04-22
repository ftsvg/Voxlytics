import mcfetch
from discord.ext import commands
from discord import app_commands, Interaction, File

from core import logger, mojang_session, MODES, fetch_player, interaction_check
from core.api import SKINS_API
from core.stats import StatsRenderer, StatsView



class Stats(commands.Cog):
    def __init__(self, client):
        self.client: commands.Bot = client


    @app_commands.command(
        name="stats", 
        description="Shows players stats"
    )
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.choices(mode=MODES)
    @app_commands.describe(
        player="The player you want to view",
        mode="The mode you want to view"
    )
    async def stats(
        self, 
        interaction: Interaction, 
        player: str = None, 
        mode: str = "Overall"
    ):
        await interaction.response.defer()
        try:
            result = await interaction_check(interaction.user.id, 'stats')
            if result.status == "blacklisted":
                return await interaction.edit_original_response(
                    content=result.message
                )

            if not (result := await fetch_player(interaction, player)):
                return None

            uuid, player_data = result
            name = mcfetch.Player(player=uuid, requests_obj=mojang_session).name

            skin_model = await SKINS_API.fetch_skin_model(uuid)

            renderer = StatsRenderer(
                skin_model,
                name,
                uuid,
                player_data,
                mode,
                view="combined"
            )

            background_img = renderer.bg(interaction.user.id)
            img_bytes = await renderer.render_to_buffer(background_img)

            view = StatsView(
                interaction=interaction,
                uuid=uuid,
                org_user=interaction.user.id,
                mode=mode,
                player=player_data,
                skin_model=skin_model,
                username=name,
            )

            await interaction.edit_original_response(
                content=f"Last login time: <t:{player_data.last_login_time}:R>",
                attachments=[File(img_bytes, filename=f"stats_{mode}.png")],
                view=view,
            ) 

        except Exception as error:
            logger.exception("Unhandled exception: %s", error)
            await interaction.edit_original_response(
                content="Something went wrong. If this issue persists, please contact the **Voxlytics Dev Team**."
            ) 


async def setup(client: commands.Bot) -> None:
    await client.add_cog(Stats(client))