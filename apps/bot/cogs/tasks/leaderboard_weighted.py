import asyncio
from discord import Embed
from discord.ext import commands, tasks

from mcfetch import Player
from core.database.handlers import LeaderboardHandler
from core.api.helpers import LeaderboardInfo
from core import logger, mojang_session, MAIN_COLOR


class WeightedWinsLeaderboardUpdates(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client
        self.db = LeaderboardHandler("weightedwins")
        self.update_message.start()

    @tasks.loop(minutes=1)
    async def update_message(self):
        try:
            latest = await LeaderboardInfo.fetch_leaderboard("weightedwins", num=100)
            if not latest:
                return

            old_snapshot = self.db.get_snapshot()
            old_lb = old_snapshot.data if old_snapshot else {}

            old_players = {p["uuid"]: p["position"] for p in old_lb.get("players", [])}
            new_players = {p["uuid"]: p["position"] for p in latest.get("players", [])}

            updates = [
                (uuid, old_players.get(uuid), new_pos)
                for uuid, new_pos in new_players.items()
                if old_players.get(uuid) is not None and old_players[uuid] != new_pos
            ]

            channels = self.db.get_channels()
            discord_channels = [
                self.client.get_channel(ch.channel_id) for ch in channels
            ]
            discord_channels = [c for c in discord_channels if c]

            for uuid, old_pos, new_pos in updates:
                name = await asyncio.to_thread(
                    Player,
                    player=uuid,
                    requests_obj=mojang_session
                )
                name = name.name
                skin_head = f"https://cravatar.eu/helmavatar/{uuid}/64"

                embed = Embed(
                    color=MAIN_COLOR,
                    description=f"`{name}` position updated: `{old_pos}` ➡ `{new_pos}`",
                )
                embed.set_author(
                    name="Weighted Wins Leaderboard Update", icon_url=skin_head
                )

                await asyncio.gather(*[ch.send(embed=embed) for ch in discord_channels])

            self.db.update_snapshot(latest)

        except Exception as error:
            logger.exception(
                f"Unhandled exception in Weighted Wins Leaderboard Updates task: {error}"
            )


    @update_message.before_loop
    async def before(self):
        await self.client.wait_until_ready()


async def setup(client: commands.Bot):
    await client.add_cog(WeightedWinsLeaderboardUpdates(client))
