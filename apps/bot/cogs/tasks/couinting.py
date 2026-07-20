import os

import discord
from discord.ext import commands
from discord import app_commands, Interaction, Embed

from core.database.handlers import CountingHandler
from core import COLOR_GREEN, COLOR_RED


class Counting(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client

    @app_commands.command(
        name="counting",
        description="Enable or disable automatic counting."
    )
    @app_commands.describe(enabled="Enable or Disable")
    async def counting(
        self,
        interaction: Interaction,
        enabled: bool
    ):
        await interaction.response.defer(ephemeral=True)

        if not interaction.user.guild_permissions.administrator:
            return await interaction.edit_original_response(
                content="You do not have permission to execute this command."
            )

        CountingHandler(interaction.guild.id).set_counting(enabled)

        status = "**enabled**" if enabled else "**disabled**"

        await interaction.edit_original_response(
            content=f"Successfully {status} automatic counting."
        )

        counting_channel_id = int(os.environ["COUNTING_CHANNEL"])
        channel = interaction.guild.get_channel(counting_channel_id)

        if channel is None:
            channel = await interaction.guild.fetch_channel(counting_channel_id)

        if enabled:
            description = (
                f"Automatic Counting has been enabled by "
                f"{interaction.user.mention}.\n\n"
                "I will now automatically add +1 to the count."
            )
            color = COLOR_GREEN
        else:
            description = (
                f"Automatic Counting has been disabled by "
                f"{interaction.user.mention}."
            )
            color = COLOR_RED

        await channel.send(
            embed=Embed(description=description, color=color)
        )

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        if message.guild is None:
            return

        counting_channel_id = int(os.environ["COUNTING_CHANNEL"])

        if message.channel.id != counting_channel_id:
            return

        counting_data = CountingHandler(message.guild.id).get_counting()

        if counting_data is None or not counting_data.enabled:
            return

        try:
            current_count = int(message.content.strip())
        except ValueError:
            return

        await message.channel.send(str(current_count + 1))


async def setup(client: commands.Bot):
    await client.add_cog(Counting(client))