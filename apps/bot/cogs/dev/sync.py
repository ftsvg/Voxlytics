import os
from discord.ext import commands

from core import logger

DEVELOPER_ID = int(os.environ.get("DEVELOPER_ID", "0"))
ORIGINAL_OWNER = int(os.environ.get("ORIGINAL_OWNER", "0"))

AUTHORIZED_USERS = {DEVELOPER_ID, ORIGINAL_OWNER}


def is_authorized():
    async def predicate(ctx: commands.Context):
        return await ctx.bot.is_owner(ctx.author) or ctx.author.id in AUTHORIZED_USERS
    return commands.check(predicate)


class Sync(commands.Cog):
    def __init__(self, client: commands.Bot) -> None:
        self.client = client

    @commands.command(name="sync", aliases=["s"])
    @is_authorized()
    async def sync_commands(self, ctx: commands.Context):
        try:
            await self.client.tree.sync()
            await ctx.reply("Successfully synced slash commands.")

        except Exception as error:
            logger.exception(error)
            await ctx.reply("Failed to sync slash commands.")


async def setup(client: commands.Bot) -> None:
    await client.add_cog(Sync(client))