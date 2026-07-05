from discord import (
    ButtonStyle,
    ChannelType,
    Interaction,
    SeparatorSpacing,
)
from discord.ui import (
    ActionRow,
    Button,
    ChannelSelect,
    Container,
    LayoutView,
    Section,
    Separator,
    TextDisplay,
)

from core import logger
from core.api.helpers import GuildInfo
from core.guild import ServerConfigHandler, TrackedServerGuilds


class DeleteGuildButton(Button):
    def __init__(
        self,
        guild_id: int,
        tracked_guild_id: int,
        guild_name: str,
        org_user: int,
    ):
        self.guild_id = guild_id
        self.tracked_guild_id = tracked_guild_id
        self.guild_name = guild_name
        self.org_user = org_user

        super().__init__(
            label="Delete",
            style=ButtonStyle.danger,
        )

    async def callback(self, interaction: Interaction):
        try:
            if interaction.user.id != self.org_user:
                return await interaction.response.send_message(
                    "You cannot use this button.",
                    ephemeral=True,
                )

            handler = ServerConfigHandler(self.guild_id)

            handler.delete_tracked_server_guild(
                self.tracked_guild_id
            )

            updated_view = await TrackerSettingsComponent.create(
                self.guild_id,
                self.org_user,
            )

            await interaction.response.edit_message(
                view=updated_view
            )

        except Exception as error:
            logger.exception(
                f"Unhandled exception: {error}"
            )

            await interaction.response.send_message(
                "Something went wrong.",
                ephemeral=True,
            )


class ChartsChannelSelect(ChannelSelect):
    def __init__(
        self,
        guild_id: int,
        org_user: int,
    ):
        self.guild_id = guild_id
        self.org_user = org_user

        super().__init__(
            placeholder="Select charts channel",
            channel_types=[ChannelType.text],
            min_values=1,
            max_values=1,
        )

    async def callback(self, interaction: Interaction):
        try:
            if interaction.user.id != self.org_user:
                return await interaction.response.send_message(
                    "You cannot use this dropdown.",
                    ephemeral=True,
                )

            selected_channel = self.values[0]
            handler = ServerConfigHandler(self.guild_id)
            handler.update_server_config(selected_channel.id)

            updated_view = await TrackerSettingsComponent.create(
                self.guild_id,
                self.org_user,
            )

            await interaction.response.edit_message(view=updated_view)

        except Exception as error:
            logger.exception(f"Unhandled exception: {error}")

            await interaction.response.send_message(
                "Something went wrong.",
                ephemeral=True,
            )


class TrackerSettingsComponent(LayoutView):
    @classmethod
    async def create(
        cls,
        guild_id: int,
        org_user: int,
    ):
        self = cls.__new__(cls)

        super(cls, self).__init__(
            timeout=None
        )

        settings_handler = ServerConfigHandler(
            guild_id
        )

        guild_config = (
            settings_handler.get_server_config()
        )

        tracked_guilds = (
            settings_handler.get_tracked_server_guilds()
        )

        total_tracked_guilds = (
            settings_handler.get_tracked_guild_count()
        )

        container = Container()

        container.add_item(
            TextDisplay(
                content=(
                    "## Tracker Settings\n"
                    "Manage this server's tracker configuration."
                )
            )
        )

        container.add_item(
            Separator()
        )

        container.add_item(TextDisplay(content="## Tracked Guilds"))

        if not tracked_guilds:
            container.add_item(
                TextDisplay(
                    content="> No guilds currently tracked"
                )
            )
        else:
            for index, guild in enumerate(
                tracked_guilds,
                start=1,
            ):
                guild: TrackedServerGuilds
                guild_info = await GuildInfo.fetch(guild.guild_id)

                guild_name = (guild_info.name if guild_info else "Api Fail")
                logs = f"<#{guild.log_channel_id}>"if guild.log_channel_id else "`Not set`"
                

                container.add_item(
                    Section(
                        TextDisplay(
                            content=(
                                f"**Guild ({index})**\n"
                                f"> Name: `{guild_name} ({guild.guild_id})`\n"
                                f"> Logs channel: {logs}"
                            )
                        ),
                        accessory=DeleteGuildButton(
                            guild_id,
                            guild.guild_id,
                            guild_name,
                            org_user,
                        ),
                    )
                )

        container.add_item(
            Separator(
                spacing=SeparatorSpacing.large
            )
        )

        charts_channel = (
            f"<#{guild_config.chart_logs}>"
            if guild_config.chart_logs != 0
            else "`Not set`"
        )

        container.add_item(
            TextDisplay(
                content=(
                    f"## Tracker Settings\n"
                    f"> Charts channel: {charts_channel}\n"
                    f"> Tracked count: `{total_tracked_guilds:,}/{guild_config.max_guilds:,}`\n"
                )
            )
        )

        container.add_item(
            ActionRow(
                ChartsChannelSelect(
                    guild_id,
                    org_user,
                )
            )
        )

        self.add_item(container)

        return self