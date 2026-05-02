import logging
from typing import Optional, Tuple

import discord
from redbot.core import Config, commands

log = logging.getLogger("red.dreamy-cogs.checkin")


CHECKMARK_EMOJI = "\u2705"
BULLET = "\u2022"
DEFAULT_START_TEXT = "Saturday @ 4:00 PM UTC (1:00 PM your local time)"
DEFAULT_END_TEXT = "Saturday @ 4:45 PM UTC (1:45 PM your local time)"


class CheckIn(commands.Cog):
    """Check-in posts that assign a configured role through a checkmark reaction."""

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=5260110405302026)
        self.config.register_guild(role_id=None, messages={})

    async def red_delete_data_for_user(self, **kwargs):
        """Nothing to delete."""
        return

    @commands.guild_only()
    @commands.group(name="checkin", aliases=["check-in", "ci"], invoke_without_command=True)
    async def checkin(self, ctx: commands.Context):
        """Configure and publish check-in posts."""
        await ctx.send_help(ctx.command)

    @checkin.command(name="rol", aliases=["role", "setrole", "asignarrol"])
    @commands.admin_or_permissions(manage_roles=True)
    async def set_checkin_role(self, ctx: commands.Context, role: discord.Role):
        """Set the role members receive when they react to a check-in post."""
        if role == ctx.guild.default_role:
            await ctx.send("Ese rol no se puede usar para check-in.")
            return

        me = ctx.guild.me
        if not me.guild_permissions.manage_roles:
            await ctx.send("Necesito el permiso `Manage Roles` para asignar ese rol.")
            return

        if role >= me.top_role:
            await ctx.send(
                "No puedo asignar ese rol porque esta a mi altura o por encima de mi rol mas alto."
            )
            return

        await self.config.guild(ctx.guild).role_id.set(role.id)
        await ctx.send(f"Rol de check-in guardado: `{role.name}`.")

    @checkin.command(name="mensaje", aliases=["post", "send", "enviar"])
    @commands.admin_or_permissions(manage_messages=True)
    async def send_checkin_message(
        self,
        ctx: commands.Context,
        channel: discord.TextChannel,
        *,
        times: Optional[str] = None,
    ):
        """Send the check-in message to a channel.

        Optionally pass custom times separated by `|`.
        Example: [p]checkin mensaje #canal Saturday @ 4:00 PM UTC (...) | Saturday @ 4:45 PM UTC (...)
        """
        role = await self._get_configured_role(ctx.guild)
        if role is None:
            await ctx.send("Primero configura el rol con `checkin rol @Checked-in`.")
            return

        if role >= ctx.guild.me.top_role:
            await ctx.send(
                "El rol configurado esta a mi altura o por encima de mi rol mas alto. "
                "Mueve mi rol por encima del rol de check-in."
            )
            return

        missing = self._missing_channel_permissions(channel)
        if missing:
            await ctx.send(
                f"Me faltan permisos en {channel.mention}: `{', '.join(missing)}`."
            )
            return

        try:
            start_text, end_text = self._parse_times(times)
        except ValueError as exc:
            await ctx.send(str(exc))
            return

        content = self._build_message(start_text, end_text, role)
        message = await channel.send(
            content,
            allowed_mentions=discord.AllowedMentions.none(),
        )
        await message.add_reaction(CHECKMARK_EMOJI)

        async with self.config.guild(ctx.guild).messages() as messages:
            messages[str(message.id)] = {
                "channel_id": channel.id,
                "role_id": role.id,
                "active": True,
            }

        await ctx.send(f"Mensaje de check-in enviado en {channel.mention}.")

    @checkin.command(name="cerrar", aliases=["close", "end"])
    @commands.admin_or_permissions(manage_messages=True)
    async def close_checkin_message(self, ctx: commands.Context, message_id: int):
        """Disable a check-in post so new reactions no longer assign the role."""
        async with self.config.guild(ctx.guild).messages() as messages:
            data = messages.get(str(message_id))
            if data is None:
                await ctx.send("No tengo registrado ese mensaje como check-in.")
                return

            data["active"] = False

        await ctx.send("Check-in cerrado. Las nuevas reacciones ya no daran el rol.")

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        if payload.guild_id is None or payload.user_id == self.bot.user.id:
            return

        if str(payload.emoji) != CHECKMARK_EMOJI:
            return

        guild = self.bot.get_guild(payload.guild_id)
        if guild is None:
            return

        messages = await self.config.guild(guild).messages()
        message_config = messages.get(str(payload.message_id))
        if not message_config or not message_config.get("active", True):
            return

        role_id = message_config.get("role_id") or await self.config.guild(guild).role_id()
        role = guild.get_role(role_id)
        if role is None:
            log.warning("Configured check-in role %s was not found in guild %s", role_id, guild.id)
            return

        member = payload.member or guild.get_member(payload.user_id)
        if member is None:
            try:
                member = await guild.fetch_member(payload.user_id)
            except discord.HTTPException:
                log.warning("Could not fetch check-in member %s in guild %s", payload.user_id, guild.id)
                return

        if member.bot or role in member.roles:
            return

        me = guild.me
        if not me.guild_permissions.manage_roles or role >= me.top_role:
            log.warning("Missing role permissions for check-in role %s in guild %s", role.id, guild.id)
            return

        try:
            await member.add_roles(role, reason="Check-in reaction")
        except discord.HTTPException:
            log.exception("Could not add check-in role %s to member %s", role.id, member.id)

    async def _get_configured_role(self, guild: discord.Guild) -> Optional[discord.Role]:
        role_id = await self.config.guild(guild).role_id()
        if role_id is None:
            return None
        return guild.get_role(role_id)

    @staticmethod
    def _build_message(start_text: str, end_text: str, role: discord.Role) -> str:
        return (
            f"Check-in Starts: {start_text}\n"
            f"Check-in Ends: {end_text}\n\n"
            "**WHEN THE CHECK-IN STARTS:**\n\n"
            f"{BULLET} **A CHECKMARK EMOJI REACTION WILL APPEAR ON THIS POST**\n\n"
            f"{BULLET} **CLICK ON IT __ONCE__ TO CHECK-IN**\n\n"
            f"{BULLET} **YOU WILL GET ASSIGNED THE @{role.name} ROLE**"
        )

    @staticmethod
    def _parse_times(times: Optional[str]) -> Tuple[str, str]:
        if not times:
            return DEFAULT_START_TEXT, DEFAULT_END_TEXT

        if "|" not in times:
            raise ValueError(
                "Usa `|` para separar inicio y fin. Ejemplo: "
                "`checkin mensaje #canal Saturday @ 4:00 PM UTC (...) | "
                "Saturday @ 4:45 PM UTC (...)`"
            )

        start_text, end_text = (part.strip() for part in times.split("|", 1))
        if not start_text or not end_text:
            raise ValueError("El texto de inicio y fin no puede estar vacio.")

        return start_text, end_text

    def _missing_channel_permissions(self, channel: discord.TextChannel) -> list[str]:
        perms = channel.permissions_for(channel.guild.me)
        missing = []
        if not perms.view_channel:
            missing.append("View Channel")
        if not perms.send_messages:
            missing.append("Send Messages")
        if not perms.add_reactions:
            missing.append("Add Reactions")
        if not perms.read_message_history:
            missing.append("Read Message History")
        return missing
