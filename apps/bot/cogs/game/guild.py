from typing import final, override
from datetime import datetime, timezone

from discord.ext import commands
from discord import app_commands, Interaction, File
from mcfetch import Player

from core import mojang_session, interaction_check, logger, ordinal
from core.api.helpers import GuildInfo
from core.render2 import RenderingClient, PlaceholderValues, TSpan


def safe_str(value):
    if value is None:
        return "N/A"
    return str(value)


@final
class GuildInfoRenderer(RenderingClient):
    def __init__(
        self,
        guild_data: GuildInfo,
        tag: str,
        owner_name: str,
        position: str,
    ):
        super().__init__(route="/guild")

        self._data = guild_data
        self._owner_name = owner_name
        self._position = position
        self._tag = tag

    @override
    def placeholder_values(self) -> PlaceholderValues:

        creation_ts = int(self._data.creation_time or 0)
        creation_date = datetime.fromtimestamp(creation_ts, tz=timezone.utc).strftime("%d/%m/%Y")

        text_placeholders = {
            "name#text": [
                TSpan(value=safe_str(self._data.name) + " ", fill="#FFFFFF"),
                TSpan(value=f"[{safe_str(self._tag).upper()}] ", fill="#AAAAAA"),
                TSpan(value=f"[{safe_str(self._data.id)}]", fill="#555555")
            ],
            "desc#text": safe_str(self._data.description),
            "original_owner#text": safe_str(self._owner_name),
            "creation_date#text": safe_str(creation_date),
            "pos#text": safe_str(self._position),
            "gxp#text": f"{int(self._data.xp or 0):,}",
            "member_count#text": [
                TSpan(value=f"{self._data.member_count or 0} ", fill="#55FF55"),
                TSpan(value="/ ", fill="#555555"),
                TSpan(value="50", fill="#55FFFF")
            ]
        }

        placeholder_values = PlaceholderValues.new(text=text_placeholders)
        placeholder_values.add_footer()

        return placeholder_values


class Guild(commands.Cog):
    def __init__(self, client):
        self.client: commands.Bot = client

    guild = app_commands.Group(
        name="guild",
        description="Guild related commands",
        allowed_contexts=app_commands.AppCommandContext(
            guild=True, dm_channel=True, private_channel=True
        ),
        allowed_installs=app_commands.AppInstallationType(
            guild=True, user=True
        )
    )

    @guild.command(
        name="info",
        description="View guild information for a specific guild"
    )
    @app_commands.describe(tag="The guild you want to view")
    async def info(self, interaction: Interaction, tag: str):
        await interaction.response.defer()
        try:
            result = await interaction_check(interaction.user.id, "guild_info")
            if result.status == "blacklisted":
                return await interaction.edit_original_response(content=result.message)

            data = await GuildInfo.fetch(tag)
            if not data:
                return await interaction.edit_original_response(content="Guild not found.")

            top = await GuildInfo.fetch_top_guilds(100)
            position = None

            if isinstance(top, dict):
                for i, g in enumerate(top.get("guilds", []), start=1):
                    if str(g.get("id")) == str(data.id):
                        position = i
                        break

            pos_text = f"{position}{ordinal(position)}" if position else "N/A"
            owner_name = Player(player=data.owner_uuid, requests_obj=mojang_session).name

            renderer = GuildInfoRenderer(
                guild_data=data,
                tag=tag,
                owner_name=owner_name,
                position=pos_text,
            )

            img_bytes = await renderer.render_to_buffer()

            await interaction.edit_original_response(
                attachments=[File(img_bytes, filename="guild_info.png")]
            )

        except Exception as error:
            logger.exception(f"Unhandled exception: {error}")
            await interaction.edit_original_response(
                content="Something went wrong. If this issue persists, please contact the **Voxlytics Dev Team**."
            )


async def setup(client: commands.Bot) -> None:
    await client.add_cog(Guild(client))