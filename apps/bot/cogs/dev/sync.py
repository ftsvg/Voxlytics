from discord.ext import commands

from core import logger


class Sync(commands.Cog):
    def __init__(self, client: commands.Bot) -> None:
        self.client = client

    @commands.command(name='sync')
    @commands.is_owner()
    async def sync_commands(self, ctx: commands.Context):
        try:
            await self.client.tree.sync()
            await ctx.message.reply(
                content="Successfully synced slash commands."
            )
        
        except Exception as error:
            logger.exception(error)


async def setup(client: commands.Bot) -> None:
    await client.add_cog(Sync(client))