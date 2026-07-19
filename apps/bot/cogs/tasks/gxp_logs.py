import asyncio
import os
from calendar import monthrange
from datetime import date, datetime, time, timedelta, timezone

from discord import Embed
from discord.ext import commands, tasks

from core import COLOR_GREEN, logger
from core.api.helpers import GuildInfo
from core.guild import GuildHandler, TrackedGuildSnapshotHandler


REPORT_CHANNEL_ID = int(os.environ.get("GXP_LOGS_CHANNEL", "0"))


def subtract_month(value: date) -> date:
    year = value.year
    month = value.month - 1

    if month == 0:
        month = 12
        year -= 1

    day = min(value.day, monthrange(year, month)[1])

    return date(year, month, day)


class GuildSnapshots(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client

        if not self.guild_snapshots.is_running():
            self.guild_snapshots.start()

    async def get_report_channel(self):
        channel = self.client.get_channel(REPORT_CHANNEL_ID)

        if channel is not None:
            return channel

        try:
            return await self.client.fetch_channel(REPORT_CHANNEL_ID)
        except Exception:
            logger.exception(
                f"Failed to fetch guild report channel "
                f"{REPORT_CHANNEL_ID}"
            )
            return None

    async def update_tracked_guilds(self) -> None:
        guild_handler = GuildHandler()

        tracked_guilds = await asyncio.to_thread(
            guild_handler.get_all_tracked_guilds
        )

        if not tracked_guilds:
            return

        guild_infos = await asyncio.gather(
            *(
                GuildInfo.fetch(guild.guild_id)
                for guild in tracked_guilds
            ),
            return_exceptions=True,
        )

        for guild, guild_info in zip(tracked_guilds, guild_infos):
            if isinstance(guild_info, Exception) or not guild_info:
                continue

            try:
                await asyncio.to_thread(
                    guild_handler.update_guild_xp,
                    guild.guild_id,
                    guild_info.xp,
                )
            except Exception:
                logger.exception(
                    f"Failed to update guild XP for "
                    f"{guild.guild_id}"
                )

    async def create_report_embed(
        self,
        title: str,
        current_date: date,
        previous_date: date,
    ) -> Embed | None:
        snapshot_handler = TrackedGuildSnapshotHandler()

        differences = await asyncio.to_thread(
            snapshot_handler.get_snapshot_differences,
            current_date,
            previous_date,
        )

        if not differences:
            return None

        differences.sort(
            key=lambda snapshot: snapshot.gained_gxp,
            reverse=True,
        )

        differences = differences[:25]

        guild_infos = await asyncio.gather(
            *(
                GuildInfo.fetch(snapshot.guild_id)
                for snapshot in differences
            ),
            return_exceptions=True,
        )

        previous_timestamp = int(
            datetime.combine(
                previous_date,
                time.min,
                tzinfo=timezone.utc,
            ).timestamp()
        )

        current_timestamp = int(
            datetime.combine(
                current_date,
                time.min,
                tzinfo=timezone.utc,
            ).timestamp()
        )

        lines = [
            (
                f"<t:{previous_timestamp}:D> to "
                f"<t:{current_timestamp}:D>"
            ),
            "",
        ]

        for position, (snapshot, guild_info) in enumerate(
            zip(differences, guild_infos),
            start=1,
        ):
            if isinstance(guild_info, Exception) or not guild_info:
                guild_name = str(snapshot.guild_id)
            else:
                guild_name = guild_info.name

            guild_name = " ".join(guild_name.split())
            guild_name = guild_name.replace(" ", "\u00a0")

            lines.append(
                f"**{position}.\u00a0{guild_name}**"
                f"\u00a0`+{snapshot.gained_gxp:,}\u00a0GXP`"
            )

        return Embed(
            title=title,
            description="\n".join(lines),
            color=COLOR_GREEN,
        )

    async def send_report(
        self,
        report_type: str,
        title: str,
        current_date: date,
        previous_date: date,
    ) -> None:
        snapshot_handler = TrackedGuildSnapshotHandler()

        was_sent = await asyncio.to_thread(
            snapshot_handler.report_was_sent,
            report_type,
            current_date,
        )

        if was_sent:
            return

        previous_exists = await asyncio.to_thread(
            snapshot_handler.has_snapshots,
            previous_date,
        )

        if not previous_exists:
            return

        embed = await self.create_report_embed(
            title,
            current_date,
            previous_date,
        )

        if embed is None:
            return

        channel = await self.get_report_channel()

        if channel is None:
            return

        try:
            await channel.send(embed=embed)
        except Exception:
            logger.exception(
                f"Failed to send {report_type} guild report "
                f"to channel {REPORT_CHANNEL_ID}"
            )
            return

        await asyncio.to_thread(
            snapshot_handler.mark_report_sent,
            report_type,
            current_date,
        )

    @tasks.loop(hours=1)
    async def guild_snapshots(self) -> None:
        try:
            today = date.today()
            yesterday = today - timedelta(days=1)
            last_week = today - timedelta(days=7)
            last_month = subtract_month(today)

            snapshot_handler = TrackedGuildSnapshotHandler()

            today_exists = await asyncio.to_thread(
                snapshot_handler.has_snapshots,
                today,
            )

            if not today_exists:
                await self.update_tracked_guilds()

                await asyncio.to_thread(
                    snapshot_handler.insert_snapshots,
                    today,
                )

            await self.send_report(
                "daily",
                "Daily Guild GXP",
                today,
                yesterday,
            )

            await self.send_report(
                "weekly",
                "Weekly Guild GXP",
                today,
                last_week,
            )

            await self.send_report(
                "monthly",
                "Monthly Guild GXP",
                today,
                last_month,
            )
        except Exception as error:
            logger.exception(
                f"Guild snapshot task failed: {error}"
            )

    @guild_snapshots.before_loop
    async def before_guild_snapshots(self) -> None:
        await self.client.wait_until_ready()

    def cog_unload(self) -> None:
        self.guild_snapshots.cancel()


async def setup(client: commands.Bot) -> None:
    await client.add_cog(GuildSnapshots(client))