import discord
from discord import Interaction, File

from core.stats import MODE_SCHEMAS
from core.api.helpers import PlayerInfo

from .renderer import StatsRenderer


class StatsView(discord.ui.View):
    def __init__(
        self,
        interaction: Interaction,
        uuid: str,
        org_user: int,
        mode: str,
        player: PlayerInfo,
        skin_model: bytes,
        username: str,
        timeout: int = 180,
    ):
        super().__init__(timeout=timeout)

        self.interaction = interaction
        self.uuid = uuid
        self.org_user = org_user
        self.mode = mode
        self.player = player
        self.skin_model = skin_model
        self.username = username
        self.view_type = "combined"

        self._build()

    def _build(self):
        self.clear_items()

        self.add_item(self._mode_select())

        schema = MODE_SCHEMAS[self.mode]
        types = schema.types

        if len(types) > 1:
            if "combined" in types:
                self.add_item(self._button("Overall", "combined", discord.ButtonStyle.blurple))

            if "single" in types:
                self.add_item(self._button(types["single"], "single"))

            if "double" in types:
                self.add_item(self._button(types["double"], "double"))

    def _mode_select(self):
        select = discord.ui.Select(
            placeholder="Select Mode",
            options=[discord.SelectOption(label=m) for m in MODE_SCHEMAS],
        )

        async def callback(interaction: Interaction):
            await interaction.response.defer()
            self.mode = select.values[0]
            self.view_type = "combined"
            await self.refresh(interaction)

        select.callback = callback
        return select

    def _button(self, label: str, view_type: str, style: discord.ButtonStyle = discord.ButtonStyle.gray):
        button = discord.ui.Button(label=label, style=style)

        async def callback(interaction: Interaction):
            await interaction.response.defer()
            self.view_type = view_type
            await self.refresh(interaction)

        button.callback = callback
        return button

    async def refresh(self, interaction: Interaction):
        self._build()

        renderer = StatsRenderer(
            skin_model_bytes=self.skin_model,
            username=self.username,
            player_uuid=self.uuid,
            player=self.player,
            mode=self.mode,
            view=self.view_type,
        )

        buffer = await renderer.render_to_buffer()

        await interaction.edit_original_response(
            attachments=[File(buffer, filename=f"stats_{self.mode}.png")],
            view=self,
        )

    async def interaction_check(self, interaction: Interaction):
        return interaction.user.id == self.org_user

    async def on_timeout(self):
        self.clear_items()
        await self.interaction.edit_original_response(view=None)