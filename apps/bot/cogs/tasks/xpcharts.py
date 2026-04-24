import asyncio
from io import BytesIO

from discord.ext import commands, tasks
from discord import File, Embed

from core import logger, MAIN_COLOR, get_stars_gained
from core.guild import (
    GuildHandler,
    TrackedPlayers,
    ServerConfigHandler,
    LastWeekHandler,
    get_current_week,
    generate_xp_chart
)
from core.api.helpers import PlayerInfo



class WeeklyCharts(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client
        self.semaphore = asyncio.Semaphore(10)

        if not self.weekly_charts.is_running():
            self.weekly_charts.start()

    async def fetch_player_safe(self, player: TrackedPlayers):
        try:
            async with self.semaphore:
                stats = await PlayerInfo.fetch(player.uuid)
                return player, stats
        except Exception:
            return player, None

    @tasks.loop(minutes=60)
    async def weekly_charts(self):
        try:
            current_week = get_current_week()
            guild_handler = GuildHandler()
            last_week_handler = LastWeekHandler()

            last_week = await asyncio.to_thread(
                last_week_handler.get_last_week
            )

            if last_week and last_week.xp_chart >= current_week:
                return

            players = await asyncio.to_thread(
                guild_handler.get_all_players
            )

            if not players:
                return

            tracked_servers = await asyncio.to_thread(
                guild_handler.get_all_tracked_server_guilds
            )

            guild_ids_with_updates = {p.guild_id for p in players if p.guild_id}
            notified_channels = set()

            for entry in tracked_servers:
                if entry.guild_id not in guild_ids_with_updates:
                    continue

                try:
                    config = await asyncio.to_thread(
                        ServerConfigHandler(entry.server_id).get_server_config
                    )
                    if not config or not config.chart_logs:
                        continue

                    if config.chart_logs in notified_channels:
                        continue

                    channel = await self.client.fetch_channel(
                        config.chart_logs
                    )

                    embed = Embed(
                        title="Weekly XP charts",
                        description=(
                            "Weekly XP charts is now running, charts for your "
                            "tracked guilds will be sent soon."
                        ),
                        color=MAIN_COLOR
                    )

                    await channel.send(embed=embed)
                    notified_channels.add(config.chart_logs)

                except Exception:
                    continue

            guild_map: dict[int, list[TrackedPlayers]] = {}
            for player in players:
                guild_map.setdefault(player.guild_id, []).append(player)

            for guild_id, guild_players in guild_map.items():
                tasks_list = [
                    self.fetch_player_safe(player)
                    for player in guild_players
                ]

                results = await asyncio.gather(*tasks_list)

                x, y, colors = [], [], []
                db_tasks = []

                for player, stats in results:
                    if not stats:
                        continue

                    try:
                        gained = get_stars_gained(
                            player.level,
                            player.xp,
                            stats.level,
                            stats.exp
                        )

                        x.append(stats.last_login_name)
                        y.append(gained)
                        colors.append(
                            "#1685F8" if gained >= 2 else "#F32C55"
                        )

                        db_tasks.append(
                            asyncio.to_thread(
                                guild_handler.update_player,
                                player.uuid,
                                stats.level,
                                stats.exp
                            )
                        )

                        db_tasks.append(
                            asyncio.to_thread(
                                guild_handler.insert_player_past_week,
                                player.uuid,
                                current_week,
                                gained
                            )
                        )

                    except Exception:
                        continue

                if db_tasks:
                    await asyncio.gather(
                        *db_tasks,
                        return_exceptions=True
                    )

                if not x:
                    continue

                image_bytes = await generate_xp_chart(
                    x,
                    y,
                    colors,
                    guild_id,
                    current_week
                )

                for entry in tracked_servers:
                    if entry.guild_id != guild_id:
                        continue

                    try:
                        config = await asyncio.to_thread(
                            ServerConfigHandler(
                                entry.server_id
                            ).get_server_config
                        )
                        if not config or not config.chart_logs:
                            continue

                        channel = await self.client.fetch_channel(
                            config.chart_logs
                        )

                        if image_bytes:
                            file = File(
                                BytesIO(image_bytes),
                                filename="xpchart.png"
                            )
                            await channel.send(file=file)

                    except Exception:
                        continue

            await asyncio.to_thread(
                last_week_handler.update_xp_week
            )

        except Exception as e:
            logger.exception(f"Weekly charts failed: {e}")

    @weekly_charts.before_loop
    async def before(self):
        await self.client.wait_until_ready()


async def setup(client: commands.Bot):
    await client.add_cog(WeeklyCharts(client))