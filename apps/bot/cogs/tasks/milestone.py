import time
from collections import defaultdict

from discord.ext import commands, tasks
from discord import Embed

from core.database import Milestone
from core.database.handlers import MilestoneHandler
from core.api.helpers import PlayerInfo
from core import logger, MAIN_COLOR


class MilestoneTask(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client
        self.loop.start()

    @tasks.loop(seconds=120)
    async def loop(self):
        try:
            milestones = MilestoneHandler.get_active_milestones()

            if not milestones:
                return

            grouped = defaultdict(list)
            for m in milestones:
                m: Milestone
                grouped[m.uuid].append(m)

            for uuid, player_milestones in grouped.items():
                player_stats = await PlayerInfo.fetch(uuid)
                if not player_stats:
                    continue

                stat_map = {
                    "wins": player_stats.wins,
                    "weightedwins": player_stats.weightedwins,
                    "kills": player_stats.kills,
                    "finals": player_stats.finals,
                    "beds": player_stats.beds,
                }

                for m in player_milestones:
                    m: Milestone

                    current = stat_map.get(m.type)
                    if current is None:
                        continue

                    remaining = m.value - current

                    if current < m.value and remaining <= m.threshold:
                        try:
                            user = self.client.get_user(m.discord_id) or await self.client.fetch_user(m.discord_id)

                            embed = Embed(
                                title="Milestone Notification",
                                description=f"You're only **{remaining:,} {m.type}** away from **{m.value:,}**!",
                                color=MAIN_COLOR
                            )

                            await user.send(embed=embed)

                            MilestoneHandler(m.discord_id, m.uuid).set_notified(m.type)

                        except Exception as error:
                            logger.exception(f"Failed to notify user {m.discord_id}: {error}")

        except Exception as error:
            logger.exception(f"Unhandled exception in milestone task {error}")


    @loop.before_loop
    async def before_loop(self):
        await self.client.wait_until_ready()


async def setup(client: commands.Bot):
    await client.add_cog(MilestoneTask(client))