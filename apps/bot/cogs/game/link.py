from discord.ext import commands
from discord import app_commands, Interaction
from mcfetch import Player

from core import check_if_valid_ign, interaction_check, mojang_session, logger
from core.database.handlers import UserHandler
from core.api.helpers import IntegrationInfo


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
            result = await interaction_check(interaction.user.id, 'link')
            if result.status == "blacklisted":
                return await interaction.edit_original_response(
                    content=result.message
                )

            if not (uuid := await check_if_valid_ign(interaction, player)):
                return None
            
            handler = UserHandler(interaction.user.id)
            user = handler.get_player()

            if user and user.discord_id:
                if not user.uuid:
                    return await interaction.edit_original_response(
                        content="You have invalid data linked. Please unlink and relink."
                    )
                ign = Player(player=user.uuid, requests_obj=mojang_session).name
                return await interaction.edit_original_response(
                    content=f"You are already linked as **{ign}**. Want to unlink? Run **/unlink**"
                )
            
            integration = await IntegrationInfo.fetch(
                uuid=uuid, discord_id=interaction.user.id
            )

            if (
                not isinstance(integration.discord_from_player, dict)
                or not isinstance(integration.player_from_discord, dict)
                or not integration.player_uuid
            ):
                content = (
                    f"Player Not Integrated To Voxyl Network!\n"
                    "- To successfully link your account, please ensure that "
                    "you're using the correct IGN and Discord account that is integrated to the Voxyl Network.\n"
                    "- Join the [Official Bedwarspractice Discord](<https://discord.gg/7Mt7T8hqr4>) and go into the integration channel."
                )

                return await interaction.edit_original_response(
                    content=content
                )
            
            if interaction.user.id != integration.discord_id:
                if not integration.player_uuid:
                    content = (
                        f"Player Not Integrated To Voxyl Network!\n"
                        "- To successfully link your account, please ensure that "
                        "you're using the correct IGN and Discord account that is integrated to the Voxyl Network.\n"
                        "- Join the [Official Bedwarspractice Discord](<https://discord.gg/7Mt7T8hqr4>) and go into the integration channel."
                    )
                    return await interaction.edit_original_response(content=content)

                ign = Player(player=integration.player_uuid, requests_obj=mojang_session).name

                return await interaction.edit_original_response(
                    content=f"You are integrated to **{ign}**. Run **/link {ign}** to link your account."
                )
            
            if not integration.player_uuid:
                content = (
                    f"Player Not Integrated To Voxyl Network!\n"
                    "- To successfully link your account, please ensure that "
                    "you're using the correct IGN and Discord account that is integrated to the Voxyl Network.\n"
                    "- Join the [Official Bedwarspractice Discord](<https://discord.gg/7Mt7T8hqr4>) and go into the integration channel."
                )
                return await interaction.edit_original_response(content=content)

            ign = Player(player=integration.player_uuid, requests_obj=mojang_session).name

            handler.link_player(uuid)

            return await interaction.edit_original_response(
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
            result = await interaction_check(interaction.user.id, 'unlink')
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