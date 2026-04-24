import asyncio
from io import BytesIO

from discord.ext import commands, tasks
from discord import File, Embed

from core import logger, MAIN_COLOR
from core.guild import(
    GuildHandler,
    ServerConfigHandler,
    LastWeekHandler,
    get_current_week,
    generate_gxp_chart
)
from core.api.helpers import GuildInfo


class GxpChart(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client

        if not self.gxp_charts.is_running():
            self.gxp_charts.start()


    @tasks.loop(minutes=60)
    async def gxp_charts(self):
        try:
            current_week = get_current_week()

            last_handler = LastWeekHandler()
            last_week = await asyncio.to_thread(last_handler.get_last_week)

            if last_week and last_week.gxp_chart == current_week:
                return

            guild_handler = GuildHandler()

            tracked_guilds = await asyncio.to_thread(
                guild_handler.get_all_tracked_guilds
            )

            if not tracked_guilds:
                return

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

                    await asyncio.to_thread(
                        guild_handler.update_guild_xp,
                        guild.guild_id,
                        info.xp
                    )

                except Exception:
                    continue

            if not x:
                return

            image_bytes = await generate_gxp_chart(
                x,
                y,
                current_week,
                True
            )

            tracked_servers = await asyncio.to_thread(
                guild_handler.get_all_tracked_server_guilds
            )

            channels = {}

            for entry in tracked_servers:
                try:
                    config = await asyncio.to_thread(
                        ServerConfigHandler(entry.server_id).get_server_config
                    )

                    if not config or not config.chart_logs:
                        continue

                    channels[config.chart_logs] = entry.server_id

                except Exception:
                    continue

            for channel_id in channels.keys():
                try:
                    channel = await self.client.fetch_channel(channel_id)

                    embed = Embed(
                        title="Weekly GXP chart",
                        description="Weekly GXP chart is now running, chart will be sent here soon",
                        color=MAIN_COLOR
                    )

                    await channel.send(embed=embed)

                except Exception:
                    continue

            for channel_id in channels.keys():
                try:
                    channel = await self.client.fetch_channel(channel_id)

                    if image_bytes:
                        file = File(BytesIO(image_bytes), filename="gxpchart.png")
                        await channel.send(file=file)

                except Exception:
                    continue

            await asyncio.to_thread(last_handler.update_gxp_week)

        except Exception as e:
            logger.exception(f"GXP charts failed: {e}")


    @gxp_charts.before_loop
    async def before(self):
        await self.client.wait_until_ready()


async def setup(client: commands.Bot):
    await client.add_cog(GxpChart(client))