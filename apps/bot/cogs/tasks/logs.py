import asyncio
import time

from discord.ext import commands, tasks
from discord import TextChannel, Embed

from core.api.helpers import GuildInfo, PlayerInfo
from core import logger, COLOR_GREEN, COLOR_RED
from core.guild import GuildHandler, TrackedServerGuilds


class GuildLogs(commands.Cog):
    def __init__(self, client: commands.Bot) -> None:
        self.client = client
        self._channel_cache: dict[int, TextChannel] = {}
        self._channel_cache_expiry: dict[int, float] = {}
        self._cache_ttl = 300
        self._send_semaphore = asyncio.Semaphore(5)
        self._send_delay = 0.2

        if not self.guild_logs.is_running():
            self.guild_logs.start()


    async def get_channel_cached(self, channel_id: int) -> TextChannel | None:
        now = time.time()

        if (
            channel_id in self._channel_cache and
            self._channel_cache_expiry.get(channel_id, 0) > now
        ):
            return self._channel_cache[channel_id]

        try:
            channel = await self.client.fetch_channel(channel_id)
            self._channel_cache[channel_id] = channel
            self._channel_cache_expiry[channel_id] = now + self._cache_ttl
            return channel
        except Exception:
            return None


    async def safe_send(self, channel: TextChannel, embed: Embed):
        async with self._send_semaphore:
            try:
                await channel.send(embed=embed)
                await asyncio.sleep(self._send_delay)
            except Exception:
                pass


    @tasks.loop(minutes=15)
    async def guild_logs(self):
        try:
            guild_handler = GuildHandler()

            tracked_guilds = await asyncio.to_thread(
                guild_handler.get_all_tracked_guilds
            )
            
            tracked_server_guilds = await asyncio.to_thread(
                guild_handler.get_all_tracked_server_guilds
            )
            
            guild_to_servers: dict[int, list] = {}

            for entry in tracked_server_guilds:
                guild_to_servers.setdefault(entry.guild_id, []).append(entry)

            guild_infos = await asyncio.gather(
                *(GuildInfo.fetch(g.guild_id) for g in tracked_guilds),
                return_exceptions=True
            )

            for i, guild in enumerate(tracked_guilds):
                info = guild_infos[i]

                if isinstance(info, Exception) or not info or info.members is None:
                    continue

                new_members = [u["uuid"].replace("-", "") for u in info.members]

                old_members_raw = await asyncio.to_thread(
                    GuildHandler(guild.guild_id).get_old_guild_members
                )

                old_members = [
                    u.replace("-", "") for u in (old_members_raw or [])
                ]

                joined_uuids = list(set(new_members) - set(old_members))
                left_uuids = list(set(old_members) - set(new_members))

                joined_infos = await asyncio.gather(
                    *(PlayerInfo.fetch(uuid) for uuid in joined_uuids),
                    return_exceptions=True
                )

                left_infos = await asyncio.gather(
                    *(PlayerInfo.fetch(uuid) for uuid in left_uuids),
                    return_exceptions=True
                )

                server_entries = guild_to_servers.get(guild.guild_id, [])
                if not server_entries:
                    continue

                channels: list[TextChannel] = []

                for entry in server_entries:
                    entry: TrackedServerGuilds

                    if not entry.log_channel_id:
                        continue

                    channel = await self.get_channel_cached(entry.log_channel_id)
                    if channel:
                        channels.append(channel)

                if not channels:
                    continue

                for idx, player_info in enumerate(joined_infos):
                    if isinstance(player_info, Exception):
                        continue

                    ign = player_info.last_login_name
                    if not ign:
                        continue

                    embed = Embed(color=COLOR_GREEN)
                    embed.set_author(
                        name=f"{ign} joined the guild",
                        icon_url=f"https://cravatar.eu/helmavatar/{joined_uuids[idx]}/64"
                    )

                    await asyncio.gather(
                        *(self.safe_send(channel, embed) for channel in channels),
                        return_exceptions=True
                    )

                    exists = await asyncio.to_thread(
                        GuildHandler().get_player,
                        joined_uuids[idx]
                    )

                    if exists:
                        await asyncio.to_thread(
                            GuildHandler().set_guild,
                            joined_uuids[idx],
                            guild.guild_id
                        )
                    else:
                        await GuildHandler(guild.guild_id).insert_player(
                            joined_uuids[idx],
                            guild.guild_id
                        )

                for idx, player_info in enumerate(left_infos):
                    if isinstance(player_info, Exception):
                        continue

                    ign = player_info.last_login_name
                    if not ign:
                        continue

                    embed = Embed(color=COLOR_RED)
                    embed.set_author(
                        name=f"{ign} left (or was kicked) from the guild",
                        icon_url=f"https://cravatar.eu/helmavatar/{left_uuids[idx]}/64"
                    )

                    await asyncio.gather(
                        *(self.safe_send(channel, embed) for channel in channels),
                        return_exceptions=True
                    )

                    await asyncio.to_thread(
                        GuildHandler().set_guild,
                        left_uuids[idx],
                        None
                    )

        except Exception as error:
            logger.exception(f"Unhandled exception: {error}")

    @guild_logs.before_loop
    async def before(self):
        await self.client.wait_until_ready()


async def setup(client: commands.Bot):
    await client.add_cog(GuildLogs(client))