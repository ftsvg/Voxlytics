
import os
from dotenv import load_dotenv
from discord.ui import View, Modal, button, Button, TextInput
from discord import ButtonStyle, Interaction, Embed
import mcfetch

from core.database.handlers import ApplicationsHandler
from core import mojang_session, MAIN_COLOR
from core.api.helpers import PlayerInfo

load_dotenv()


class ApplicationView(View):
    def __init__(self):
        super().__init__(timeout=None)


    @button(label="Apply Here!", style=ButtonStyle.blurple, custom_id="apps_btn")
    async def apps_btn(self, interaction: Interaction, button: Button):
        handler = ApplicationsHandler(interaction.user.id)

        has_applied = handler.get_application()
        if has_applied:
            return await interaction.response.send_message(
                content="You already have a pending application.",
                ephemeral=True
            )

        await interaction.response.send_modal(
            GuildApplicationModal()
        )

        
class GuildApplicationModal(Modal, title="Guild Application"):
    username = TextInput(
        label="Your minecraft username.",
        placeholder="Enter your username...",
        max_length=16,
        required=True
    )

    current_guild = TextInput(
        label="Your current guild",
        placeholder="Enter your current guild..."
    )

    stars_a_week = TextInput(
        label="Stars a week",
        placeholder="Enter your average star gain per week...",
        required=True,
    )

    async def on_submit(self, interaction: Interaction):

        uuid = mcfetch.Player(
            player=self.username.value,
            requests_obj=mojang_session,
        ).uuid

        if not uuid:
            return await interaction.response.send_message(
                content=f"**{self.username.value}** does not exist. Please enter a valid username.",
                ephemeral=True
            )

        name = mcfetch.Player(
            player=uuid,
            requests_obj=mojang_session,
        ).name

        player_info = await PlayerInfo.fetch(uuid)
        if not player_info:
            return await interaction.response.send_message(
                content=f"Failed to fetch data for {name}. Please try again later.",
                ephemeral=True
            )

        embed = Embed(
            title="New Application",
            description=(
                "**Application Info**\n"
                f"- Username: `{name}`\n"
                f"- Current Guild: `{self.current_guild.value if self.current_guild.value else 'Not Given'}`\n"
                f"- Stars A week: `{self.stars_a_week.value}`\n\n"
                "**Player Stats**\n"
                f"- Level: `{player_info.level:,}`\n"
                f"- Wins: `{player_info.wins:,}`\n"
                f"- Weighted Wins: `{player_info.weightedwins:,}`\n"
                f"- Kills `{player_info.kills:,}`\n"
                f"- Finals `{player_info.finals:,}`\n"
                f"- Beds `{player_info.beds:,}`\n"
            ),
            color=MAIN_COLOR
        )
        embed.set_footer(text=f"Submitted by {interaction.user.name} ({interaction.user.id})")
        embed.set_thumbnail(url=interaction.user.avatar.url if interaction.user.avatar else None)

        applications_channel = await interaction.guild.fetch_channel(
            os.getenv("APPLICATIONS_CHANNEL")
        )

        ApplicationsHandler(interaction.user.id).new_application()

        await applications_channel.send(embed=embed)
        await interaction.response.send_message(
            "Your application was successfully submitted!",
            ephemeral=True,
        )