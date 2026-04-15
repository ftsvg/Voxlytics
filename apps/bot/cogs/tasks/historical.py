import time
from discord.ext import commands, tasks

from core.database.handlers import HistoricalHandler
from core.api.helpers import PlayerInfo
from core import logger, PERIOD_SECONDS


class HistoricalResetTask(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.reset_loop.start()

    @tasks.loop(minutes=15)
    async def reset_loop(self):
        try:
            now = int(time.time())

            handler = HistoricalHandler()
            rows = handler.get_tacked_players()

            for uuid, period, last_reset in rows:
                interval = PERIOD_SECONDS.get(period)

                if not interval:
                    continue

                try:
                    last_reset = int(last_reset or 0)

                except (TypeError, ValueError):
                    last_reset = 0

                next_reset = last_reset + interval
                if now < next_reset:
                    continue

                player_data = await PlayerInfo.fetch(uuid)
                if not player_data:
                    continue

                HistoricalHandler(uuid, period).update_historical(player_data)

        except Exception:
            logger.exception("Unhandled exception in Historical reset task")


    @reset_loop.before_loop
    async def before_reset_loop(self):
        await self.bot.wait_until_ready()


async def setup(bot: commands.Bot):
    await bot.add_cog(HistoricalResetTask(bot))