from discord.ext import commands
from discord import app_commands, Interaction, TextChannel, Embed

from core.api.helpers import GuildInfo
from core.guild import ServerConfigHandler, GuildHandler, TrackedServerGuilds
from core import logger, interaction_check, MAIN_COLOR


class GuildTracker(commands.Cog):
    def __init__(self, client):
        self.client: commands.Bot = client

    tracker = app_commands.Group(
        name="tracker", description="Tracker related commands"
    )

    @tracker.command(
        name="config",
        description="Configure this servers tracker settings"
    )
    @app_commands.describe(
        charts_channel="The channel where all xp/gxp charts get sent to"
    )
    async def config(
        self,
        interaction: Interaction,
        charts_channel: TextChannel
    ):
        await interaction.response.defer()
        try:
            result = await interaction_check(interaction.user.id, 'tracker_config')
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
            
            handler = ServerConfigHandler(interaction.guild.id)
            handler.update_server_config(charts_channel.id)
            
            return await interaction.edit_original_response(
                content="Successfully updated the tracked config."
            )


        except Exception as error:
            logger.exception(f"Unhandled exception: {error}")

            await interaction.edit_original_response(
                content="Something went wrong. If this issue persists, please contact the **Voxlytics Dev Team**."
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
            result = await interaction_check(interaction.user.id, 'tracker_config')
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
                content="Something went wrong. If this issue persists, please contact the **Voxlytics Dev Team**."
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
            result = await interaction_check(interaction.user.id, 'tracker_config')
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
                content="Something went wrong. If this issue persists, please contact the **Voxlytics Dev Team**."
            )


    @tracker.command(
        name="delete",
        description="Delete a tracked guild"
    )
    @app_commands.describe(tag="The guild you want to delete")
    async def delete(
        self,
        interaction: Interaction,
        tag: str
    ):
        await interaction.response.defer()
        try:
            result = await interaction_check(interaction.user.id, 'tracker_config')
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
                    content="You dont have any guilds currently tracked."
                )
            
            guild_info = await GuildInfo.fetch(tag)
            if not guild_info:
                return await interaction.edit_original_response(
                    content=f"**{tag}** was not found. Please enter a valid guild tag."
                )

            guild_id = guild_info.id
            tracked_ids = {g.guild_id for g in tracked_guilds}

            if guild_id not in tracked_ids:
                return await interaction.edit_original_response(
                    content="This guild is not currently being tracked"
                )
            
            config_handler.delete_tracked_server_guild(guild_id)

            return await interaction.edit_original_response(
                content=f"Successfully deleted **{guild_info.name} [{tag.upper()}]** from the tracked."
            )

        except Exception as error:
            logger.exception(f"Unhandled exception: {error}")

            await interaction.edit_original_response(
                content="Something went wrong. If this issue persists, please contact the **Voxlytics Dev Team**."
            )


    @tracker.command(
        name="settings",
        description="View this server's tracker configuration"
    )
    async def settings(self, interaction: Interaction):
        await interaction.response.defer()

        try:
            config_handler = ServerConfigHandler(interaction.guild.id)

            server_config = config_handler.get_server_config()
            tracked_guilds = config_handler.get_tracked_server_guilds()

            if not server_config:
                return await interaction.edit_original_response(
                    content="You have not configured the tracker yet. Use `/tracker config` first."
                )

            charts_channel = (
                f"<#{server_config.chart_logs}>"
                if server_config.chart_logs
                else "Not set"
            )

            embed = Embed(
                title=f"Tracker Settings for {interaction.guild.name}",
                description=(
                    f"> **Max guilds:** `{server_config.max_guilds}`\n"
                    f"> **Charts channel:** {charts_channel}"
                ),
                color=MAIN_COLOR
            )

            if not tracked_guilds:
                guilds_text = "Currently no tracked guilds."
            else:
                lines = []

                for g in tracked_guilds:
                    g: TrackedServerGuilds

                    guild_info = await GuildInfo.fetch(g.guild_id)
                    name = guild_info.name if guild_info else "Unknown"

                    logs = (
                        f"<#{g.log_channel_id}>"
                        if g.log_channel_id
                        else "*No logs channel set yet*"
                    )

                    lines.append(f"> **{name} ({g.guild_id})** {logs}")

                guilds_text = "\n".join(lines)

            embed.add_field(
                name="Tracked Guilds",
                value=guilds_text,
                inline=False
            )

            return await interaction.edit_original_response(embed=embed)

        except Exception as error:
            logger.exception(f"Unhandled exception: {error}")

            await interaction.edit_original_response(
                content="Something went wrong. If this issue persists, please contact the **Voxlytics Dev Team**."
            )

async def setup(client: commands.Bot) -> None:
    await client.add_cog(GuildTracker(client))
