from discord.ext import commands
from discord import app_commands, Interaction, TextChannel

from core.api.helpers import GuildInfo
from core.guild import ServerConfigHandler, GuildHandler
from core import logger, interaction_check, fetch_player, mojang_session

from core.guild import TrackerSettingsComponent
import mcfetch


class GuildTracker(commands.Cog):
    def __init__(self, client):
        self.client: commands.Bot = client

    tracker = app_commands.Group(
        name="tracker", description="Tracker related commands"
    )

    @tracker.command(
        name="settings",
        description="View this server's tracker configuration"
    )
    async def settings(self, interaction: Interaction):
        await interaction.response.defer()
        try:
            result = await interaction_check(
                discord_id=interaction.user.id,
                guild_id=interaction.guild.id,
                role_ids=[role.id for role in interaction.user.roles],
                command_name='tracker_settings',
            )
            
            if result.status == "blacklisted":
                return await interaction.edit_original_response(
                    content=result.message
                )           

            if not interaction.user.guild_permissions.administrator:
                return await interaction.edit_original_response(
                    content=(
                        "You don't have the permissions to execute this command. Please ask a server admin to configure the tracker settings."
                    )
                )
            
            ServerConfigHandler(interaction.guild.id).ensure_server_config()

            view = await TrackerSettingsComponent.create(
                interaction.guild.id,
                interaction.user.id
            )

            await interaction.edit_original_response(
                view=view
            )

        except Exception as error:
            logger.exception(f"Unhandled exception: {error}")

            await interaction.edit_original_response(
                content="Something went wrong. If this issue persists, please contact a **Shine Administrator**."
            )        


    @tracker.command(
        name="add",
        description="Add a guild to this servers guild tracker"
    )
    @app_commands.describe(
        tag="The guild you want to start tracking",
        logs_channel="The channel where join/leave logs get sent to."
    )
    async def add(
        self,
        interaction: Interaction,
        tag: str,
        logs_channel: TextChannel = None
    ):
        await interaction.response.defer()
        try:
            result = await interaction_check(
                discord_id=interaction.user.id,
                guild_id=interaction.guild.id,
                role_ids=[role.id for role in interaction.user.roles],
                command_name='tracker_add',
            )
            
            if result.status == "blacklisted":
                return await interaction.edit_original_response(
                    content=result.message
                )            

            if not interaction.user.guild_permissions.administrator:
                return await interaction.edit_original_response(
                    content=(
                        "You don't have the permissions to execute this command. Please ask a server admin to configure the tracker settings."
                    )
                )
            
            config_handler = ServerConfigHandler(interaction.guild.id)
            server_config = config_handler.get_server_config()

            if not server_config:
                return await interaction.edit_original_response(
                    content="You must first run the `/tracker config` command in order to add guilds."
                )

            total_tracked_guilds = config_handler.get_tracked_guild_count()

            if total_tracked_guilds >= server_config.max_guilds:
                return await interaction.edit_original_response(
                    content=(
                        "You already reached the tracked guilds limit.\n"
                        "- Use `/tracker update` to update a tracked guild or request more guild slots in the [support server](<https://voxlytics.net/discord>)."
                    )
                )
            
            guild_info = await GuildInfo.fetch(tag)
            if not guild_info:
                return await interaction.edit_original_response(
                    content="Guild not found. Please enter a valid guild tag and try again."
                )
            
            tracked_guilds = config_handler.get_tracked_server_guilds()
            if any(g.guild_id == guild_info.id for g in tracked_guilds):
                return await interaction.edit_original_response(
                    content="You are already tracking this guild."
                )

            config_handler.insert_tracked_server_guilds(
                guild_info.id, logs_channel.id if logs_channel else None
            )


            guild_handler = GuildHandler(guild_info.id)
            guild_handler.insert_guild(guild_info.id, guild_info.xp)
            await guild_handler.insert_guild_players(guild_info.members)
            
            return await interaction.edit_original_response(
                content=f"**{guild_info.name} [{tag.upper()}]** has successfully been added to the tracker."
            )

        except Exception as error:
            logger.exception(f"Unhandled exception: {error}")

            await interaction.edit_original_response(
                content="Something went wrong. If this issue persists, please contact a **Shine Administrator**."
            ) 


    @tracker.command(
        name="update",
        description="Update a tracked guilds config"
    )
    @app_commands.describe(
        tag="The guild you want to update",
        new_guild="The guild you want to start tracking",
        logs_channel="The channel where join/leave logs get sent to."
    )
    async def update(
        self,
        interaction: Interaction,
        tag: str,
        new_guild: str | None = None,
        logs_channel: TextChannel | None = None
    ):
        await interaction.response.defer()
        try:
            result = await interaction_check(
                discord_id=interaction.user.id,
                guild_id=interaction.guild.id,
                role_ids=[role.id for role in interaction.user.roles],
                command_name='tracker_update',
            )
            
            if result.status == "blacklisted":
                return await interaction.edit_original_response(
                    content=result.message
                )           

            if not interaction.user.guild_permissions.administrator:
                return await interaction.edit_original_response(
                    content=(
                        "You don't have the permissions to execute this command. Please ask a server admin to configure the tracker settings."
                    )
                )
            
            config_handler = ServerConfigHandler(interaction.guild.id)
            tracked_guilds = config_handler.get_tracked_server_guilds()

            if not tracked_guilds:
                return await interaction.edit_original_response(
                    content="You must first run the `/tracker add` command in order to update guilds."
                )
            
            guild_info = await GuildInfo.fetch(tag)
            if not guild_info:
                return await interaction.edit_original_response(
                    content=f"**{tag}** was not found. Please enter a valid guild tag."
                )
            
            old_guild_id = guild_info.id

            new_guild_id = None
            new_guild_info = None

            if new_guild:
                new_guild_info = await GuildInfo.fetch(new_guild)
                if not new_guild_info:
                    return await interaction.edit_original_response(
                        content=f"**{new_guild}** was not found. Please enter a valid guild tag."
                    )
                
                new_guild_id = new_guild_info.id

            tracked_ids = {g.guild_id for g in tracked_guilds}

            if old_guild_id not in tracked_ids:
                return await interaction.edit_original_response(
                    content="This guild is not currently being tracked and cannot be updated."
                )

            if new_guild_id is not None:
                if old_guild_id == new_guild_id:
                    return await interaction.edit_original_response(
                        content="You cannot update a guild to itself."
                    )

                if new_guild_id in tracked_ids:
                    return await interaction.edit_original_response(
                        content="New guild is already being tracked."
                    )

            if new_guild_id is None and logs_channel is None:
                return await interaction.edit_original_response(
                    content="You must provide either a new guild or a logs channel to update."
                )

            config_handler.update_tracked_server_guild(
                old_guild_id,
                new_guild_id=new_guild_id,
                log_channel_id=logs_channel.id if logs_channel else None
            )

            if new_guild_id is not None:
                guild_handler = GuildHandler(new_guild_id)
                guild_handler.insert_guild(new_guild_id, new_guild_info.xp)
                await guild_handler.insert_guild_players(new_guild_info.members)

            return await interaction.edit_original_response(
                content="Successfully updated the servers tracked guilds configuration."
            )

        except Exception as error:
            logger.exception(f"Unhandled exception: {error}")

            await interaction.edit_original_response(
                content="Something went wrong. If this issue persists, please contact a **Shine Administrator**."
            )


    @tracker.command(
        name="add-player",
        description="Add a player to the tracker"
    )
    @app_commands.describe(
        player="The player you want to track"
    )
    async def add_player(
        self,
        interaction: Interaction,
        player: str
    ):
        await interaction.response.defer()

        try:
            result = await interaction_check(
                discord_id=interaction.user.id,
                guild_id=interaction.guild.id,
                role_ids=[role.id for role in interaction.user.roles],
                command_name='tracker_add_player',
            )
            
            if result.status == "blacklisted":
                return await interaction.edit_original_response(
                    content=result.message
                )

            if not interaction.user.guild_permissions.administrator:
                return await interaction.edit_original_response(
                    content=(
                        "You don't have the permissions to execute this command. Please ask a server admin to configure the tracker settings."
                    )
                )

            if not (result := await fetch_player(interaction, player)):
                return None

            uuid, player_data = result
            name = mcfetch.Player(player=uuid, requests_obj=mojang_session).name            

            guild_handler = GuildHandler()

            tracked_player = guild_handler.get_player(uuid)
            if tracked_player:
                return await interaction.edit_original_response(
                    content="This player is already being tracked."
                )

            guild_id = player_data.guild_id if player_data.guild_id else None
            await guild_handler.insert_player(uuid, guild_id)

            await interaction.edit_original_response(
                content=f"**{name}** has successfully been added to the tracker."
            )

        except Exception as error:
            logger.exception(f"Unhandled exception: {error}")

            await interaction.edit_original_response(
                content="Something went wrong. If this issue persists, please contact a **Shine Administrator**."
            )


async def setup(client: commands.Bot) -> None:
    await client.add_cog(GuildTracker(client))
