from discord.ext import commands
from discord import app_commands, Interaction, Embed

from core import MAIN_COLOR
from core.database.handlers import UserHandler, MilestoneHandler
from core import logger, interaction_check
from core.api.helpers import PlayerInfo


class Milestones(commands.Cog):
    def __init__(self, client):
        self.client: commands.Bot = client

    milestone = app_commands.Group(
        name="milestone",
        description="Miletone related commands",
        allowed_contexts=app_commands.AppCommandContext(
            guild=True, dm_channel=True, private_channel=True
        ),
        allowed_installs=app_commands.AppInstallationType(guild=True, user=True),
    )


    @milestone.command(
        name="add",
        description="Add a new milestone"
    )
    @app_commands.choices(
        type=[
            app_commands.Choice(name="Wins", value="wins"),
            app_commands.Choice(name="Weighted Wins", value="weightedwins"),
            app_commands.Choice(name="Kills", value="kills"),
            app_commands.Choice(name="Finals", value="finals"),
            app_commands.Choice(name="Beds", value="beds"),
        ]
    )
    @app_commands.describe(
        type="The milestone type",
        value="The milestone you want to reach (e.g. 18000)",
        threshold="How close before the milestone to notify you (e.g. 50 = alert 50 away)"
    )
    async def add(
        self, 
        interaction: Interaction,
        type: app_commands.Choice[str],
        value: int,
        threshold: app_commands.Range[int, 15, None]
    ):
        await interaction.response.defer()
        try:
            result = await interaction_check(interaction.user.id, 'milestone_add')
            if result.status == "blacklisted":
                return await interaction.edit_original_response(
                    content=result.message
                )

            handler = UserHandler(interaction.user.id)
            user = handler.get_player()

            if not user:
                return await interaction.edit_original_response(
                    content="You don't have an account linked! Use **/link** to link your account."
                )
            
            uuid = user.uuid

            player_stats = await PlayerInfo.fetch(uuid)
            if not player_stats:
                return await interaction.edit_original_response(
                    content="Failed to fetch stats. If this issue persists, please contact the **Voxlytics Dev Team**."
                )
            
            if type.value == "wins":
                stat = player_stats.wins
            elif type.value == "weightedwins":
                stat = player_stats.weightedwins
            elif type.value == "kills":
                stat = player_stats.kills
            elif type.value == "finals":
                stat = player_stats.finals
            elif type.value == "beds":
                stat = player_stats.beds

            remaining = int(value - stat)

            if stat >= value:
                return await interaction.edit_original_response(
                    content=f"You've already reached **{value:,} {type.name.lower()}**!"
                )

            if remaining <= threshold:
                return await interaction.edit_original_response(
                    content=(
                        f"You're already within the notification range for **{value:,} {type.name.lower()}**!\n"
                        f"- Only {remaining:,} away, threshold is {threshold}\n"
                        f"- Try a smaller threshold or a higher milestone."
                    )
                )

            milestone_handler = MilestoneHandler(interaction.user.id, uuid)
            milestone_handler.update_milestone(
                type.value,
                value,
                threshold
            )

            return await interaction.edit_original_response(
                content=(
                    f"Milestone added! "
                    f"You'll be notified when you're within **{threshold}** of **{value:,}** {type.name.lower()}."
                )
            )

        except Exception as error:
            logger.exception(f"Unhandled exception: {error}")

            await interaction.edit_original_response(
                content="Something went wrong. If this issue persists, please contact the **Voxlytics Dev Team**."
            )


    @milestone.command(
        name="list",
        description="View your active milestones"
    )
    async def list(self, interaction: Interaction):
        await interaction.response.defer()

        try:
            result = await interaction_check(interaction.user.id, 'milestone_list')
            if result.status == "blacklisted":
                return await interaction.edit_original_response(
                    content=result.message
                )

            handler = UserHandler(interaction.user.id)
            user = handler.get_player()

            if not user:
                return await interaction.edit_original_response(
                    content="You don't have an account linked! Use **/link** to link your account."
                )
            
            uuid = user.uuid

            milestone_handler = MilestoneHandler(interaction.user.id, uuid)
            milestones = milestone_handler.get_all_milestones()

            if not milestones:
                return await interaction.edit_original_response(
                    content="You don't have any milestones set. Run `/milestone add` to add a milestone."
                )

            embed = Embed(
                title="Milestones",
                color=MAIN_COLOR
            )

            name_map = {
                "wins": "Wins",
                "weightedwins": "Weighted Wins",
                "kills": "Kills",
                "finals": "Final Kills",
                "beds": "Beds Broken",
            }

            for m in milestones:
                status = "Notified" if m.notified else "Pending"

                embed.add_field(
                    name=f"{name_map.get(m.type, m.type.capitalize())}",
                    value=(
                        f"> **Target:** `{m.value:,}`\n"
                        f"> **Threshold:** `{m.threshold:,}`\n"
                        f"> **Status:** `{status}`"
                    ),
                    inline=True
                )
            embed.set_footer(text="Use /milestone add to update a milestone")

            await interaction.edit_original_response(embed=embed)

        except Exception as error:
            logger.exception(f"Unhandled exception: {error}")

            await interaction.edit_original_response(
                content="Something went wrong. If this issue persists, please contact the **Voxlytics Dev Team**."
            )


    @milestone.command(
        name="remove",
        description="Remove a milestone"
    )
    @app_commands.choices(
        type=[
            app_commands.Choice(name="Wins", value="wins"),
            app_commands.Choice(name="Weighted Wins", value="weightedwins"),
            app_commands.Choice(name="Kills", value="kills"),
            app_commands.Choice(name="Finals", value="finals"),
            app_commands.Choice(name="Beds", value="beds"),
        ]
    )
    @app_commands.describe(
        type="The milestone type you want to remove"
    )
    async def remove(
        self,
        interaction: Interaction,
        type: app_commands.Choice[str]
    ):
        await interaction.response.defer()

        try:
            result = await interaction_check(interaction.user.id, 'milestone_remove')
            if result.status == "blacklisted":
                return await interaction.edit_original_response(
                    content=result.message
                )

            handler = UserHandler(interaction.user.id)
            user = handler.get_player()

            if not user:
                return await interaction.edit_original_response(
                    content="You don't have an account linked! Use **/link** to link your account."
                )
            
            uuid = user.uuid

            milestone_handler = MilestoneHandler(interaction.user.id, uuid)
            removed = milestone_handler.remove_milestone(type.value)

            if not removed:
                return await interaction.edit_original_response(
                    content=f"You don't have a {type.name.lower()} milestone set."
                )

            await interaction.edit_original_response(
                content=f"Successfully removed your {type.name.lower()} milestone."
            )

        except Exception as error:
            logger.exception(f"Unhandled exception: {error}")

            await interaction.edit_original_response(
                content="Something went wrong. If this issue persists, please contact the **Voxlytics Dev Team**."
            )


async def setup(client: commands.Bot) -> None:
    await client.add_cog(Milestones(client))
