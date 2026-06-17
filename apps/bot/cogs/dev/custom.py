import os
import base64  
import discord
from discord import app_commands, Interaction
from discord.ext import commands
from discord.http import Route
from dotenv import load_dotenv

from core import logger

load_dotenv()

class Customize(commands.Cog):
    def __init__(self, client):
        self.client: commands.Bot = client

    customize = app_commands.Group(
        name="customize",
        description="customize related commands."
    )

    @customize.command(
        name="set", 
        description="Change the bots nickname and avatar."
    )
    @app_commands.describe(
        nickname="The new nickname",
        avatar="The custom profile picture file (Image/GIF)"
    )
    async def customize_set(
        self,
        interaction: Interaction,
        nickname: str,
        avatar: discord.Attachment
    ):
        await interaction.response.defer(ephemeral=True)
        
        try:
            developer_id = os.environ.get("DEVELOPER_ID")
            if not developer_id or interaction.user.id != int(developer_id):
                return await interaction.edit_original_response(
                    content="You do not have the permissions to execute this command."
                )

            avatar_bytes = await avatar.read()
            b64_encoded = base64.b64encode(avatar_bytes).decode('utf-8')
            avatar_data = f"data:{avatar.content_type};base64,{b64_encoded}"

            payload = {
                "nick": nickname,
                "avatar": avatar_data
            }

            route = Route(
                "PATCH", 
                "/guilds/{guild_id}/members/@me", 
                guild_id=interaction.guild_id
            )
            
            await self.client.http.request(route, json=payload)
            
            return await interaction.edit_original_response(
                content=f"Successfully updated the nickname and profile picture."
            )

        except discord.HTTPException as http_err:
            logger.error(f"Discord API Error: {http_err.text}")

            await interaction.edit_original_response(
                content=f"Failed to communicate with Discord:\n ```{http_err.text}```"
            )
        except Exception as error:
            logger.exception(f"Unhandled profile setup exception: {error}")
            await interaction.edit_original_response(
                content="Something went wrong while executing this configuration."
            )


    @customize.command(
        name="reset", 
        description="Reset the bots avatar and nickname to the original."
    )
    async def customize_reset(self, interaction: Interaction):
        await interaction.response.defer(ephemeral=True)
        
        try:
            developer_id = os.environ.get("DEVELOPER_ID")
            if not developer_id or interaction.user.id != int(developer_id):
                return await interaction.edit_original_response(
                    content="You do not have the permissions to execute this command."
                )

            payload = {
                "nick": None,
                "avatar": None
            }

            route = Route(
                "PATCH", 
                "/guilds/{guild_id}/members/@me", 
                guild_id=interaction.guild_id
            )
            
            await self.client.http.request(route, json=payload)
            
            return await interaction.edit_original_response(
                content=f"Successfully reverted the nickname and avatar to the original."
            )

        except discord.HTTPException as http_err:
            logger.error(f"Discord API Error: {http_err.text}")
            await interaction.edit_original_response(
                content=f"Failed to communicate with Discord:\n ```{http_err.text}```"
            )
        except Exception as error:
            logger.exception(f"Unhandled profile reset exception: {error}")
            await interaction.edit_original_response(
                content="Something went wrong while executing this configuration reset."
            )

async def setup(client: commands.Bot) -> None:
    await client.add_cog(Customize(client))