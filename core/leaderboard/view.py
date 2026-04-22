import discord
from discord import Interaction, File

from .renderer import LeaderboardRenderer


class LeaderboardSelect(discord.ui.Select):
    def __init__(self, view: "LeaderboardView"):
        options = [
            discord.SelectOption(label=f"Page {i}", value=str(i))
            for i in range(1, 11)
        ]

        super().__init__(
            placeholder=f"Page {view.page}/10",
            min_values=1,
            max_values=1,
            options=options,
        )

    async def callback(self, interaction: Interaction):
        view = self.view

        if interaction.user.id != view.owner_id:
            return await interaction.response.send_message(
                "This isn't your leaderboard.", ephemeral=True
            )

        page = int(self.values[0])

        await interaction.response.defer()

        view.page = page
        await view.update(interaction)


class LeaderboardView(discord.ui.View):
    def __init__(
        self,
        *,
        data: dict,
        lb_type: str,
        page: int,
        owner_id: int,
        fetch_func,
    ):
        super().__init__(timeout=180)

        self.data = data
        self.lb_type = lb_type
        self.page = page
        self.owner_id = owner_id
        self.fetch_func = fetch_func

        self.message: discord.Message | None = None

        self._build()

    def _build(self):
        self.clear_items()
        self.add_item(LeaderboardSelect(self))

    async def update(self, interaction: Interaction):
        start_idx = (self.page - 1) * 10
        end_idx = start_idx + 10

        players = self.data["players"][start_idx:end_idx]

        results = await self.fetch_func(players)

        renderer = LeaderboardRenderer(
            players=results,
            lb_type=self.lb_type,
            page=self.page,
        )

        background_img = renderer.bg(interaction.user.id)
        img_bytes = await renderer.render_to_buffer(background_img)

        self._build()

        await interaction.edit_original_response(
            attachments=[File(img_bytes, filename="leaderboard.png")],
            view=self,
        )

    async def on_timeout(self):
        self.clear_items()
        if self.message:
            await self.message.edit(view=None)