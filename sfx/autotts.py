import contextlib
from typing import Optional

import discord
from redbot.core import commands
from redbot.core.commands import Context

from .abc import MixinMeta

class AutoTTSMixin(MixinMeta):
    async def get_user_autotts(self, user_id: int, channel_id: int) -> bool:
        """
        Get the AutoTTS status for a user in a specific channel.

        Returns:
            bool: True if AutoTTS is enabled for the user in the channel, False otherwise.
        """
        channel_settings = await self.config.channel_from_id(channel_id).all()
        return user_id in channel_settings["autotts_users"]

    async def set_user_autotts(self, user_id: int, channel_id: int, status: bool):
        """
        Set the AutoTTS status for a user in a specific channel.

        Args:
            user_id (int): The ID of the user.
            channel_id (int): The ID of the channel.
            status (bool): True to enable AutoTTS for the user in the channel, False to disable.
        """
        channel_settings = await self.config.channel_from_id(channel_id).all()
        autotts_users = channel_settings["autotts_users"]
        if status:
            if user_id not in autotts_users:
                autotts_users.append(user_id)
        else:
            if user_id in autotts_users:
                autotts_users.remove(user_id)
        await self.config.channel_from_id(channel_id).autotts_users.set(autotts_users)

    @commands.group(invoke_without_command=True)
    @commands.guild_only()
    async def autotts(self, ctx: Context):
        """
        Activa el comando para enviar mensajes TTS automáticamente.

        Si no está activado a nivel servidor, lo activará para ti.
        """
        toggle = await self.config.guild(ctx.guild).allow_autotts()
        user_autotts = await self.get_user_autotts(ctx.author.id, ctx.channel.id)
        if user_autotts:
            await self.set_user_autotts(ctx.author.id, ctx.channel.id, False)
            await ctx.send("Auto-TTS desactivado para este canal.")
        else:
            if not toggle:
                await ctx.send("AutoTTS is disallowed on this server.")
                return
            await self.set_user_autotts(ctx.author.id, ctx.channel.id, True)
            await ctx.send("Auto-TTS activado para este canal.")

    @autotts.command(name="server")
    @commands.admin_or_permissions(manage_guild=True)
    @commands.guild_only()
    async def autotts_server(self, ctx: Context):
        """Toggles the AutoTTS feature for the server."""
        toggle = await self.config.guild(ctx.guild).allow_autotts()
        if toggle:
            await self.config.guild(ctx.guild).allow_autotts.set(False)
            await ctx.send("AutoTTS is now disallowed for this server.")
        else:
            await self.config.guild(ctx.guild).allow_autotts.set(True)
            await ctx.send("AutoTTS is now allowed for this server.")

    @commands.Cog.listener(name="on_message_without_command")
    async def autotts_message_listener(self, message: discord.Message):
        if (
            not message.guild
            or message.author.bot
            or not await self.bot.allowed_by_whitelist_blacklist(who=message.author)
            or await self.bot.cog_disabled_in_guild(self, message.guild)
            or not await self.config.guild(message.guild).allow_autotts()
            or not message.author.voice
            or not message.author.voice.channel
            or not message.author.voice.channel.permissions_for(message.author).speak
            or not await self.can_tts(message)
        ):
            return

        user_autotts = await self.get_user_autotts(message.author.id, message.channel.id)
        if not user_autotts:
            return

        await self.play_tts(
            message.author,
            message.author.voice.channel,
            message.channel,
            "autotts",
            message.clean_content,
        )

    @commands.Cog.listener(name="on_voice_state_update")
    async def autotts_voice_listener(
        self,
        member: discord.Member,
        before: Optional[discord.VoiceChannel],
        after: Optional[discord.VoiceChannel],
    ):
        if (
            member.bot
            or not await self.bot.allowed_by_whitelist_blacklist(who=member)
            or await self.bot.cog_disabled_in_guild(self, member.guild)
        ):
            return

        user_autotts = await self.get_user_autotts(member.id, after.channel.id)
        if not user_autotts:
            return

        if before and not after:
            await self.set_user_autotts(member.id, before.id, False)
            embed = discord.Embed(
                title="AutoTTS Disabled",
                color=await self.bot.get_embed_color(member.guild),
            )
            embed.description = (
                f"You have left {before.mention} and therefore AutoTTS has been disabled for this channel.\n\n"
                f"If you would like to re-enable AutoTTS, please join a voice channel and rerun the autotts command."
            )
            with contextlib.suppress(discord.HTTPException):
                await member.send(embed=embed)