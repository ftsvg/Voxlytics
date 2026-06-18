import asyncio

from datetime import datetime, date
from discord.ext import tasks, commands

from core import logger
from core.api.helpers import PlayerInfo
from core.database.handlers import HistoricalSnapshotHandler


class SnapshotTask(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client
        self.snapshot_loop.start()

    @tasks.loop(hours=24)
    async def snapshot_loop(self):
        try:
            uuids = HistoricalSnapshotHandler(None).get_all_players()

            logger.info(
                f"Creating snapshots for {len(uuids)} players."
            )

            for uuid in uuids:
                try:
                    player_data = await PlayerInfo.fetch(uuid)

                    if not player_data:
                        continue

                    HistoricalSnapshotHandler(
                        uuid
                    ).create_snapshot(player_data)

                except Exception:
                    logger.exception(
                        f"Failed snapshot for {uuid}"
                    )

        except Exception:
            logger.exception(
                "Unhandled exception in snapshot loop."
            )

    @snapshot_loop.before_loop
    async def before_loop(self):
        await self.client.wait_until_ready()

        now = datetime.now()

        midnight = datetime.combine(
            date.today(),
            datetime.min.time()
        )

        seconds_until_next_midnight = (
            midnight.timestamp()
            + 86400
            - now.timestamp()
        )

        await asyncio.sleep(
            seconds_until_next_midnight
        )


async def setup(client: commands.Bot):
    await client.add_cog(
        SnapshotTask(client)
    )