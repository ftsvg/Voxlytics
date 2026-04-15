import os

from discord import Intents
from discord.ext import commands

from core import logger


intents = Intents.all()
intents.message_content = True

class Client(commands.AutoShardedBot):
    def __init__(
        self, *, intents: Intents = intents
    ):
        super().__init__(
            intents=intents,
            command_prefix=commands.when_mentioned_or('!')
        )


    async def setup_hook(self):
        for folder in os.listdir("apps/bot/cogs"):
            for cog in os.listdir(f"apps/bot/cogs/{folder}"):
                if cog.endswith(".py"):
                    try:
                        await self.load_extension(name=f"apps.bot.cogs.{folder}.{cog[:-3]}")
                        logger.info(f"Loaded: {cog[:-3]} cog")

                    except commands.errors.ExtensionNotFound:
                        logger.error(f"Failed to load {cog[:-3]}")


    async def on_ready(self):
        logger.info(f'Logged in as {self.user} (ID: {self.user.id})')