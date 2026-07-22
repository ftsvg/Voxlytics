import os
from dotenv import load_dotenv

import mcfetch
from discord.ext import commands
from discord import app_commands, Interaction, ButtonStyle, SeparatorSpacing, TextStyle
from discord.ui import LayoutView, Container, Separator, Section, TextDisplay, Thumbnail, Modal, TextInput, Button, ActionRow

from core.api.helpers import PlayerInfo
from core import (
    mojang_session,
    interaction_check,
    logger,
    fetch_player,
    fetch_player_modal,
    get_stars_gained
)
from core.guild import GuildHandler

load_dotenv()


class CheckModal(Modal, title="Check Player"):
    ign = TextInput(
        label="Player",
        placeholder="Enter the player you want to view...",
        max_length=16,
        style=TextStyle.short
    )

    async def on_submit(self, interaction: Interaction):
        await interaction.response.defer()

        try:
            if not (res := await fetch_player_modal(interaction, str(self.ign))):
                return

            uuid, player_data = res
            guild_handler = GuildHandler()

            player_row = guild_handler.get_player_full(uuid)
            if not player_row:
                return await interaction.followup.send(
                    content="This player is not tracked.",
                    ephemeral=True
                )

            past_weeks = guild_handler.get_player_past_weeks(uuid)
            highest_week = guild_handler.get_player_highest_week(uuid)

            stars_gained = get_stars_gained(
                player_row.level,
                player_row.xp,
                player_data.level,
                player_data.exp
            )

            skin_head_url = f"https://nmsr.nickac.dev/face/{uuid}"

            name = mcfetch.Player(
                player=uuid,
                requests_obj=mojang_session
            ).name

            view = CheckComponent(
                interaction,
                uuid,
                name,
                skin_head_url,
                past_weeks,
                highest_week,
                stars_gained,
                player_row.level
            )

            await interaction.message.edit(view=view)

        except Exception as error:
            logger.exception(f"Modal error: {error}")

            return await interaction.followup.send(
                content="Something went wrong.", ephemeral=True
            )


class SetHighestWeekModal(Modal, title="Set Highest Week"):
    value = TextInput(
        label="Highest Week",
        placeholder="e.g. 125.50",
        required=True,
        max_length=10
    )

    def __init__(self, uuid: str):
        super().__init__()
        self.uuid = uuid

    async def on_submit(self, interaction: Interaction):
        try:
            value = float(str(self.value))

            guild_handler = GuildHandler()

            guild_handler.set_player_highest_week(
                self.uuid,
                value
            )

            player_row = guild_handler.get_player_full(self.uuid)

            if not player_row:
                return await interaction.response.send_message(
                    "This player is no longer tracked.",
                    ephemeral=True
                )

            player_data = await PlayerInfo.fetch(self.uuid)

            if not player_data:
                return await interaction.response.send_message(
                    "Failed to refresh player data.",
                    ephemeral=True
                )

            past_weeks = guild_handler.get_player_past_weeks(self.uuid)

            stars_gained = get_stars_gained(
                player_row.level,
                player_row.xp,
                player_data.level,
                player_data.exp
            )

            skin_head_url = f"https://cravatar.eu/helmavatar/{self.uuid}/64"

            name = mcfetch.Player(
                player=self.uuid,
                requests_obj=mojang_session
            ).name

            view = CheckComponent(
                interaction,
                self.uuid,
                name,
                skin_head_url,
                past_weeks,
                value,
                stars_gained,
                player_row.level
            )

            await interaction.response.edit_message(
                view=view
            )

            await interaction.followup.send(
                f"Highest week updated to `{value:.2f}✫`.",
                ephemeral=True
            )

        except ValueError:
            await interaction.response.send_message(
                "Please enter a valid number.",
                ephemeral=True
            )

        except Exception as error:
            logger.exception(error)

            await interaction.response.send_message(
                "Failed to update highest week.",
                ephemeral=True
            )


class CheckComponent(LayoutView):
    def __init__(
        self,
        interaction: Interaction,
        uuid: str,
        username: str,
        skin_head_url: str,
        past_weeks: list[float],
        highest_week: float,
        stars_gained: float,
        start_level: int
    ):
        super().__init__(timeout=None)

        self.owner_id = interaction.user.id
        self.uuid = uuid

        avg = round(sum(past_weeks) / len(past_weeks), 2) if len(past_weeks) > 0 else 0

        weeks = (past_weeks + [0] * 8)[:8]
        row1 = ", ".join(f"`{week:.2f}✫`" for week in weeks[:4])
        row2 = ", ".join(f"`{week:.2f}✫`" for week in weeks[4:])

        container = Container()
        container.add_item(
            TextDisplay(content=f"## {username}'s Weekly Stats")
        )
        container.add_item(Separator(spacing=SeparatorSpacing.large))
        container.add_item(
            Section(
                TextDisplay(
                    content=(
                        f"**Current Week Stats**\n"
                        f"> Level: `{start_level}` `(+{stars_gained:.2f}✫)`\n"
                        f"**Overall Statistics**\n"
                        f"> Highest week: `{highest_week:.2f}✫`\n"
                        f"> Average week: `{avg:.2f}✫`\n"
                        f"**Past Weeks**\n"
                        f"> {row1}\n"
                        f"> {row2}"
                    )
                ),
                accessory=Thumbnail(skin_head_url)
            )
        )
        container.add_item(Separator(spacing=SeparatorSpacing.large))
        row = ActionRow()

        search_button = Button(
            style=ButtonStyle.blurple,
            label="Check Player"
        )

        highest_button = Button(
            style=ButtonStyle.gray,
            label="Set Highest Week"
        )

        async def search_callback(interaction: Interaction):
            if interaction.user.id != self.owner_id:
                return await interaction.response.send_message(
                    "In order to search for players you will have to execute the command yourself.",
                    ephemeral=True
                )

            await interaction.response.send_modal(CheckModal())


        async def highest_callback(interaction: Interaction):
            if interaction.user.id != int(os.getenv("DEVELOPER_ID")):
                return await interaction.response.send_message(
                    "",
                    ephemeral=True
                )

            await interaction.response.send_modal(
                SetHighestWeekModal(self.uuid)
            )

        search_button.callback = search_callback
        highest_button.callback = highest_callback

        row.add_item(search_button)
        row.add_item(highest_button)
        container.add_item(row)

        container.add_item(Separator(spacing=SeparatorSpacing.large))
        container.add_item(
            TextDisplay(
                content=f"-# Requested by **{interaction.user.name}**"
            )
        )
        
        self.add_item(container)


class Check(commands.Cog):
    def __init__(self, client):
        self.client: commands.Bot = client

    @app_commands.command(
        name="check",
        description="View xp progress and weekly stats for any player"
    )
    @app_commands.describe(player="The player you want to view")
    async def check(
        self,
        interaction: Interaction,
        player: str | None = None
    ):
        await interaction.response.defer()

        try:
            result = await interaction_check(
                discord_id=interaction.user.id,
                guild_id=interaction.guild.id,
                role_ids=[role.id for role in interaction.user.roles],
                command_name='check',
            )

            if result.status == "blacklisted":
                return await interaction.edit_original_response(
                    content=result.message
                )

            if not (res := await fetch_player(interaction, player)):
                return

            uuid, player_data = res
            guild_handler = GuildHandler()

            player_row = guild_handler.get_player_full(uuid)
            if not player_row:
                return await interaction.edit_original_response(
                    content="This player is not tracked."
                )

            past_weeks = guild_handler.get_player_past_weeks(uuid)
            highest_week = guild_handler.get_player_highest_week(uuid)

            stars_gained = get_stars_gained(
                player_row.level,
                player_row.xp,
                player_data.level,
                player_data.exp
            )

            skin_head_url = f"https://nmsr.nickac.dev/face/{uuid}"
            
            name = mcfetch.Player(player=uuid, requests_obj=mojang_session).name

            view = CheckComponent(
                interaction,
                uuid,
                name,
                skin_head_url,
                past_weeks,
                highest_week,
                stars_gained,
                player_row.level
            )

            await interaction.edit_original_response(
                view=view
            )

        except Exception as error:
            logger.exception(f"Unhandled exception: {error}")

            await interaction.edit_original_response(
                content="Something went wrong. If this issue persists, please contact a **Shine Administrator**."
            )


async def setup(client: commands.Bot) -> None:
    await client.add_cog(Check(client))