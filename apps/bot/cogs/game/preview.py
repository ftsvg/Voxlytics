import asyncio
from io import BytesIO

from discord.ext import commands
from discord import app_commands, Interaction, File

from core import logger, interaction_check, get_stars_gained
from core.guild import (
    GuildHandler,
    ServerConfigHandler,
    generate_xp_chart,
    generate_gxp_chart,
    get_current_week,
    TrackedGuilds,
    TrackedPlayers
)
from core.api.helpers import GuildInfo, PlayerInfo


class Preview(commands.Cog):
    def __init__(self, client):
        self.client: commands.Bot = client

    preview = app_commands.Group(
        name="preview",
        description="Preview related commands"
    )

    @preview.command(
        name="xp",
        description="Preview XP chart for a tracked guild"
    )
    @app_commands.describe(tag="The guild you want to preview")
    async def xp(self, interaction: Interaction, tag: str):
        await interaction.response.defer()

        try:
            result = await interaction_check(interaction.user.id, "tracker_config")
            if result.status == "blacklisted":
                return await interaction.edit_original_response(content=result.message)

            config_handler = ServerConfigHandler(interaction.guild.id)
            tracked = config_handler.get_tracked_server_guilds()

            if not tracked:
                return await interaction.edit_original_response(
                    content="You don't have any tracked guilds. Use `/tracker add` first."
                )

            guild_info = await GuildInfo.fetch(tag)
            if not guild_info:
                return await interaction.edit_original_response(
                    content=f"**{tag.upper()}** does not exist."
                )

            if not any(g.guild_id == guild_info.id for g in tracked):
                return await interaction.edit_original_response(
                    content="This guild is not tracked in this server."
                )

            guild_handler = GuildHandler(guild_info.id)
            players = guild_handler.get_guild_players(guild_info.id)

            if not players:
                return await interaction.edit_original_response(
                    content="No players found for this guild."
                )

            x, y, colors = [], [], []

            for player in players:
                player: TrackedPlayers
                
                try:
                    stats = await PlayerInfo.fetch(player.uuid)
                    if not stats or not stats.last_login_name:
                        continue

                    gained = get_stars_gained(
                        player.level,
                        player.xp,
                        stats.level,
                        stats.exp
                    )

                    x.append(stats.last_login_name)
                    y.append(gained)
                    colors.append("#1685F8" if gained >= 2 else "#F32C55")

                except Exception:
                    continue

            if not x:
                return await interaction.edit_original_response(
                    content="No valid player data found."
                )

            image_bytes = await generate_xp_chart(
                x,
                y,
                colors,
                guild_info.id,
                get_current_week(),
                True
            )

            return await interaction.edit_original_response(
                attachments=[File(BytesIO(image_bytes), filename="xpchart.png")]
            )

        except Exception as error:
            logger.exception(f"Unhandled exception: {error}")
            await interaction.edit_original_response(
                content="Something went wrong."
            )


    @preview.command(
        name="gxp",
        description="Preview global GXP chart for tracked guilds"
    )
    async def gxp(self, interaction: Interaction):
        await interaction.response.defer()

        try:
            result = await interaction_check(interaction.user.id, "tracker_config")
            if result.status == "blacklisted":
                return await interaction.edit_original_response(content=result.message)

            config_handler = ServerConfigHandler(interaction.guild.id)
            tracked = config_handler.get_tracked_server_guilds()

            if not tracked:
                return await interaction.edit_original_response(
                    content="You don't have any tracked guilds. Use `/tracker add` first."
                )

            guild_handler = GuildHandler()
            tracked_guilds = await asyncio.to_thread(
                guild_handler.get_all_tracked_guilds
            )

            if not tracked_guilds:
                return await interaction.edit_original_response(
                    content="No tracked guild data found."
                )

            guild_infos = await asyncio.gather(
                *(GuildInfo.fetch(g.guild_id) for g in tracked_guilds),
                return_exceptions=True
            )

            x, y = [], []

            for guild, info in zip(tracked_guilds, guild_infos):
                if isinstance(info, Exception) or not info:
                    continue

                try:
                    gained = info.xp - guild.guild_xp

                    x.append(info.name)
                    y.append(gained)

                except Exception:
                    continue

            if not x:
                return await interaction.edit_original_response(
                    content="No valid guild data found."
                )

            image_bytes = await generate_gxp_chart(
                x,
                y,
                get_current_week(),
                True
            )

            return await interaction.edit_original_response(
                attachments=[File(BytesIO(image_bytes), filename="gxpchart.png")]
            )

        except Exception as error:
            logger.exception(f"Unhandled exception: {error}")
            await interaction.edit_original_response(
                content="Something went wrong."
            )
        

async def setup(client: commands.Bot) -> None:
    await client.add_cog(Preview(client))