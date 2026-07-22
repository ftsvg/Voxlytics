import asyncio
from discord.ext import commands
from discord import app_commands, Interaction, Embed, TextChannel, HTTPException, Member

from core import MAIN_COLOR, ApplicationView, COLOR_GREEN
from core.database.handlers import ApplicationsHandler


class Applications(commands.Cog):
    def __init__(self, client):
        self.client: commands.Bot = client

    application = app_commands.Group(
        name="application",
        description="Application related commands"
    )

    @application.command(
        name="panel",
        description="Setup the applications panel."
    )
    @app_commands.describe(channel="The channel where the panel will get sent to.")
    async def panel(self, interaction: Interaction, channel: TextChannel):
        await interaction.response.defer(ephemeral=True)

        if not interaction.user.guild_permissions.administrator:
            return await interaction.edit_original_response(
                content="You do not have the permissions to execute this command."
            )

        embed = Embed(
            title="Guild Applications",
            description=(
                "Click on the button below to create a guild application."
                "\n\n*Only serious applications will be reviewed by staff!*"
            ),
            color=MAIN_COLOR
        )

        await channel.send(embed=embed, view=ApplicationView())
        await interaction.edit_original_response(
            content=f"Successfully sent applications menu to {channel.mention}."
        )

    @application.command(
        name="manage",
        description="Accept or deny a guild application."
    )
    @app_commands.describe(
        member="The member whose application you want to manage.",
        accepted="Whether to accept or deny the application."
    )
    async def manage(
        self,
        interaction: Interaction,
        member: Member,
        accepted: bool,
    ):
        await interaction.response.defer(ephemeral=True)

        if not interaction.user.guild_permissions.administrator:
            return await interaction.edit_original_response(
                content="You do not have the permissions to execute this command."
            )

        handler = ApplicationsHandler(member.id)
        application = await asyncio.to_thread(handler.get_application)

        if application is None:
            return await interaction.edit_original_response(
                content=f"{member.mention} does not have a pending application."
            )

        removed = await asyncio.to_thread(handler.remove_application)

        if not removed:
            return await interaction.edit_original_response(
                content="Failed to remove the application from the database."
            )

        if accepted:
            try:
                embed = Embed(
                    title="Application Accepted",
                    description=(
                        "Congratulations! Your application for **Shine** "
                        "has been accepted. A staff member will get in contact with you soon."
                    ),
                    color=COLOR_GREEN,
                )
                await member.send(embed=embed)

            except HTTPException:
                pass

        await interaction.edit_original_response(
            content=(
                f"Successfully {'accepted' if accepted else 'denied'} "
                f"{member.mention}'s application."
            )
        )

async def setup(client: commands.Bot) -> None:
    await client.add_cog(Applications(client))
