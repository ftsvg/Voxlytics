from typing import final, override

from discord.ext import commands
from discord import app_commands, Interaction, File

from core.render2 import PlaceholderValues, RenderingClient
from core.accounts import Usage
from core import logger, interaction_check


@final
class LactateLeaderboardRenderer(RenderingClient):
    def __init__(self, users: list[dict]):
        super().__init__(route="/leaderboard-lactate")
        self._users = users

    @override
    def placeholder_values(self) -> PlaceholderValues:
        placeholder_values = PlaceholderValues.new(text={})

        placeholder_values.text["title#text"] = "Leaderboard Lactate"
        placeholder_values.text["lb_type#text"] = "Lactates"

        for i in range(1, 11):
            if i <= len(self._users):
                user = self._users[i - 1]
                displayname = user["displayname"]
                value = f"{user['times_used']:,}"
            else:
                displayname = "No user yet"
                value = "0"

            placeholder_values.text[f"pos_{i}#text"] = f"#{i}"
            placeholder_values.text[f"pos_{i}#fill"] = {
                1: "#FFFF55",
                2: "#AAAAAA",
                3: "#FFAA00",
            }.get(i, "#FFFFFF")

            placeholder_values.text[f"displayname_{i}#text"] = displayname
            placeholder_values.text[f"displayname_{i}#fill"] = "#FFFFFF"
            placeholder_values.text[f"value_{i}#text"] = value

        placeholder_values.add_footer()

        return placeholder_values


class Lactate(commands.Cog):
    def __init__(self, client):
        self.client: commands.Bot = client

    lactate = app_commands.Group(
        name="lactate",
        description="Lactate related commands",
        allowed_contexts=app_commands.AppCommandContext(
            guild=True, dm_channel=True, private_channel=True
        ),
        allowed_installs=app_commands.AppInstallationType(guild=True, user=True),
    )


    @lactate.command(
        name="use", description="Lactate"
    )
    @app_commands.checks.cooldown(1, 10.0)
    async def use(self, interaction: Interaction):
        await interaction.response.defer()
        try:
            result = await interaction_check(interaction.user.id, 'lactate')
            if result.status == "blacklisted":
                return await interaction.edit_original_response(
                    content=result.message
                )

            return await interaction.edit_original_response(
                content="🥛 **You have lactated!**"
            )

        except Exception as error:
            logger.exception(f"Unhandled exception: {error}")

            await interaction.edit_original_response(
                content="Something went wrong. If this issue persists, please contact the **Voxlytics Dev Team**."
            )

        
    @lactate.command(
        name="leaderboard",
        description="Shows lactate leaderboard",
    )
    async def leaderboard(self, interaction: Interaction):
        await interaction.response.defer()

        try:
            result = await interaction_check(interaction.user.id, 'lactate_leaderboard')
            if result.status == "blacklisted":
                return await interaction.edit_original_response(
                    content=result.message
                )


            usage_list = Usage().get_top_lactate_users()

            if not usage_list:
                return await interaction.edit_original_response(
                    content="No lactate data found."
                )

            users = []

            for entry in usage_list:
                user = self.client.get_user(entry.discord_id)

                if not user:
                    try:
                        user = await self.client.fetch_user(entry.discord_id)
                    except:
                        displayname = f"Unknown ({entry.discord_id})"
                    else:
                        displayname = user.display_name
                else:
                    displayname = user.display_name

                users.append({
                    "displayname": displayname,
                    "times_used": entry.times_used
                })

            renderer = LactateLeaderboardRenderer(users=users)
            
            background_img = renderer.bg(interaction.user.id)
            img_bytes = await renderer.render_to_buffer(background_img)

            await interaction.edit_original_response(
                attachments=[File(img_bytes, filename="lactate_leaderboard.png")]
            )

        except Exception as error:
            logger.exception(f"Unhandled exception: {error}")

            await interaction.edit_original_response(
                content="Something went wrong. If this issue persists, please contact the **Voxlytics Dev Team**."
            )


    @use.error
    async def use_error(self, interaction: Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.CommandOnCooldown):
            return await interaction.response.send_message(
                f"You're on cooldown! Try again in **{error.retry_after:.1f}s**",
            )


async def setup(client: commands.Bot) -> None:
    await client.add_cog(Lactate(client))
