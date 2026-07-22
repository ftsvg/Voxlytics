import json
import io
import discord
import mcfetch
from discord.ext import commands
from discord import app_commands, Interaction

from core import logger, mojang_session, fetch_player, interaction_check
from core.api.helpers import GuildInfo


class StatsRaw(commands.Cog):
    def __init__(self, client):
        self.client: commands.Bot = client

    @app_commands.command(
        name="player_raw_stats",
        description="Shows a player's raw stats"
    )
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.describe(player="The player you want to view")
    async def raw_stats(
        self,
        interaction: Interaction,
        player: str = None,
    ):
        await interaction.response.defer()

        try:
            result = await interaction_check(
                discord_id=interaction.user.id,
                guild_id=interaction.guild.id,
                role_ids=[role.id for role in interaction.user.roles],
                command_name='stats_raw',
            )
            
            if result.status == "blacklisted":
                return await interaction.edit_original_response(
                    content=result.message
                )

            if not (result := await fetch_player(interaction, player)):
                return

            uuid, player_data = result
            name = mcfetch.Player(player=uuid, requests_obj=mojang_session).name

            guild_info = None
            if player_data.guild_id:
                guild_info = await GuildInfo.fetch(player_data.guild_id)

            raw_data = {
                "uuid": uuid,
                "username": name,
                "basic_info": {
                    "lastLoginName": player_data.last_login_name,
                    "lastLoginTime": player_data.last_login_time,
                    "role": player_data.role,
                },
                "overall_stats": {
                    "level": player_data.level,
                    "exp": player_data.exp,
                    "weightedwins": player_data.weightedwins,
                },
                "game_stats": {
                    "overall_wins": player_data.wins,
                    "overall_kills": player_data.kills,
                    "overall_finals": player_data.finals,
                    "overall_beds": player_data.beds,
                    "mode_stats": {
                        mode_name: {
                            stat_name: stat_value
                            for stat_name, stat_value in mode_data.items()
                            if stat_name in {"wins", "kills", "finals", "beds"}
                        }
                        for mode_name, mode_data in player_data.mode_stats.items()
                        if isinstance(mode_data, dict)
                    },
                },
                "player_guild": {
                    "guildRole": player_data.guild_role,
                    "joinTime": player_data.guild_join_time,
                    "guildId": player_data.guild_id,
                    "guild_info": {
                        "id": guild_info.id,
                        "name": guild_info.name,
                        "description": guild_info.description,
                        "gxp": guild_info.xp,
                        "memberCount": guild_info.member_count,
                        "ownerUUID": str(guild_info.owner_uuid).replace("-", ""),
                        "creationTime": guild_info.creation_time,
                    } if guild_info else None,
                },
            }

            json_data = json.dumps(raw_data, indent=4)

            file = discord.File(
                io.BytesIO(json_data.encode("utf-8")),
                filename=f"{name}.json"
            )

            await interaction.edit_original_response(
                attachments=[file]
            )

        except Exception as error:
            logger.exception("Unhandled exception: %s", error)
            await interaction.edit_original_response(
                content="Something went wrong. If this issue persists, please contact a **Shine Administrator**."
            )


async def setup(client: commands.Bot) -> None:
    await client.add_cog(StatsRaw(client))