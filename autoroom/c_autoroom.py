"""The autoroom command."""
import datetime
from abc import ABC
from typing import Any

import discord
from redbot.core import commands
from redbot.core.utils.chat_formatting import error, humanize_timedelta

from .abc import MixinMeta
from .pcx_lib import Perms, SettingDisplay, delete

MAX_CHANNEL_NAME_LENGTH = 100

def is_admin_or_mod(ctx):
    return commands.mod_or_permissions(administrator=True)()

class AutoRoomCommands(MixinMeta, ABC):
    """The autoroom command."""

    @commands.group()
    @commands.guild_only()
    async def room(self, ctx: commands.Context) -> None:
        """Cambia los ajustes de tu chat de voz."""

    @room.command(name="settings", aliases=["about", "info"])
    async def autoroom_settings(self, ctx: commands.Context) -> None:
        """Muestra los ajustes actuales de la sala."""
        if not ctx.guild:
            return
        autoroom_channel, autoroom_info = await self._get_autoroom_channel_and_info(
            ctx, check_owner=False
        )
        if not autoroom_channel or not autoroom_info:
            return

        room_settings = SettingDisplay("Room Settings")
        owner = ctx.guild.get_member(autoroom_info["owner"])
        if owner:
            room_settings.add(
                "Owner",
                owner.display_name,
            )
        else:
            room_settings.add(
                "Mode",
                "Server Managed",
            )

        source_channel = ctx.guild.get_channel(autoroom_info["source_channel"])
        if isinstance(source_channel, discord.VoiceChannel):
            member_roles = self.get_member_roles(source_channel)

            access_text = ""
            if member_roles:
                for role in member_roles:
                    autoroom_type = self._get_autoroom_type(autoroom_channel, role)
                    if not access_text:
                        access_text = autoroom_type
                    elif access_text != autoroom_type:
                        # Multiple member roles present, and we can't determine the autoroom type
                        access_text = "custom"
                        break
            else:
                access_text = self._get_autoroom_type(
                    autoroom_channel, autoroom_channel.guild.default_role
                )
            access_text = access_text.capitalize()
            if member_roles:
                access_text += ", only certain roles"
            room_settings.add("Access", access_text)
            if member_roles:
                room_settings.add(
                    "Member Roles", ", ".join(role.name for role in member_roles)
                )

        room_settings.add(
            "Edad del canal",
            humanize_timedelta(
                timedelta=datetime.datetime.now(datetime.UTC)
                - autoroom_channel.created_at
            ),
        )

        access_settings = SettingDisplay("Ajustes de acceso actuales")
        allowed_members = []
        allowed_roles = []
        denied_members = []
        denied_roles = []
        for member_or_role in autoroom_channel.overwrites:
            if isinstance(member_or_role, discord.Role):
                if self.check_if_member_or_role_allowed(
                    autoroom_channel, member_or_role
                ):
                    allowed_roles.append(member_or_role)
                else:
                    denied_roles.append(member_or_role)
            elif isinstance(member_or_role, discord.Member):
                if self.check_if_member_or_role_allowed(
                    autoroom_channel, member_or_role
                ):
                    allowed_members.append(member_or_role)
                else:
                    denied_members.append(member_or_role)

        if denied_members:
            access_settings.add(
                "Miembros bloqueados",
                ", ".join(member.display_name for member in denied_members),
            )
        if denied_roles:
            access_settings.add(
                "Roles bloqueados", ", ".join(role.name for role in denied_roles)
            )

        await ctx.send(str(room_settings.display(access_settings)))


#    @autoroom.command(name="name")
#    async def autoroom_name(self, ctx: commands.Context, *, name: str) -> None:
#        """Change the name of your AutoRoom. Only for amdins."""
#        if not ctx.guild:
#            return
#
#        if (
#            await self.is_mod_or_mod_role(ctx.author)
#            or await self.is_admin_or_admin_role(ctx.author)
#        ):
#            autoroom_channel, autoroom_info = await self._get_autoroom_channel_and_info(ctx)
#            if not autoroom_channel or not autoroom_info:
#                return
#
#            if len(name) > MAX_CHANNEL_NAME_LENGTH:
#                name = name[:MAX_CHANNEL_NAME_LENGTH]
#            if name != autoroom_channel.name:
#                bucket = self.bucket_autoroom_name.get_bucket(autoroom_channel)
#                if bucket:
#                    retry_after = bucket.update_rate_limit()
#                    if retry_after:
#                        per_display = bucket.per - self.extra_channel_name_change_delay
#                        hint_text = error(
#                            f"{ctx.message.author.mention}, you can only modify an AutoRoom name **{bucket.rate}** times "
#                            f"every **{humanize_timedelta(seconds=per_display)}** with this command. "
#                            f"You can try again in **{humanize_timedelta(seconds=max(1, int(min(per_display, retry_after))))}**."
#                            "\n\n"
#                            "Alternatively, you can modify the channel yourself by either right clicking the channel on "
#                            "desktop or by long pressing it on mobile."
#                        )
#                        if ctx.guild.mfa_level:
#                            hint_text += (
#                                " Do note that since this server has 2FA enabled, you will need it enabled "
#                                "on your account to modify the channel in this way."
#                            )
#                        hint = await ctx.send(hint_text)
#                        await delete(ctx.message, delay=30)
#                        await delete(hint, delay=30)
#                        return
#                    await autoroom_channel.edit(
#                        name=name, reason="AutoRoom: User edit room info"
#                    )
#            await ctx.tick()
#            await delete(ctx.message, delay=5)
#        else:
#            await ctx.send("Only administrators and moderators can change the autoroom name.")

#    @autoroom.command(name="bitrate", aliases=["kbps"])
#    async def autoroom_bitrate(self, ctx: commands.Context, kbps: int) -> None:
#        """Change the bitrate of your AutoRoom."""
#        if not ctx.guild:
#            return
#        autoroom_channel, autoroom_info = await self._get_autoroom_channel_and_info(ctx)
#        if not autoroom_channel or not autoroom_info:
#            return
#
#        bps = max(8000, min(int(ctx.guild.bitrate_limit), kbps * 1000))
#        if bps != autoroom_channel.bitrate:
#            await autoroom_channel.edit(
#                bitrate=bps, reason="AutoRoom: User edit room info"
#            )
#        await ctx.tick()
#        await delete(ctx.message, delay=5)

#    @autoroom.command(name="users", aliases=["userlimit"])
#    async def autoroom_users(self, ctx: commands.Context, user_limit: int) -> None:
#        """Change the user limit of your AutoRoom."""
#        autoroom_channel, autoroom_info = await self._get_autoroom_channel_and_info(ctx)
#        if not autoroom_channel or not autoroom_info:
#            return
#
#        limit = max(0, min(99, user_limit))
#        if limit != autoroom_channel.user_limit:
#            await autoroom_channel.edit(
#                user_limit=limit, reason="AutoRoom: User edit room info"
#            )
#        await ctx.tick()
#        await delete(ctx.message, delay=5)

    @room.command()
    async def claim(self, ctx: commands.Context) -> None:
        """Reclama la pertenencia de la Sala."""
        if not ctx.guild:
            return
        new_owner = ctx.message.author
        if not isinstance(new_owner, discord.Member):
            return
        autoroom_channel, autoroom_info = await self._get_autoroom_channel_and_info(
            ctx, check_owner=False
        )
        if not autoroom_channel or not autoroom_info:
            return
        bucket = self.bucket_autoroom_owner_claim.get_bucket(autoroom_channel)
        old_owner = ctx.guild.get_member(autoroom_info["owner"])
        denied_message = ""

        if (
            not await self.is_mod_or_mod_role(new_owner)
            and not await self.is_admin_or_admin_role(new_owner)
            and new_owner != ctx.guild.owner
        ):
            if old_owner and old_owner in autoroom_channel.members:
                denied_message = (
                    "solo puedes obtener la propiedad de una sala si el anterior dueño de la sala se ha ido de ella"
                )
            elif bucket:
                retry_after = bucket.update_rate_limit()
                if retry_after:
                    denied_message = f"debes esperar **{humanize_timedelta(seconds=max(retry_after, 1))}** antes de reclamar la propiedad, en caso de que el anterior dueño vuelva"

        if denied_message:
            hint = await ctx.send(
                error(f"{ctx.message.author.mention}, {denied_message}")
            )
            await delete(ctx.message, delay=10)
            await delete(hint, delay=10)
            return

        perms = Perms(autoroom_channel.overwrites)
        if old_owner:
            perms.overwrite(old_owner, self.perms_public)
        perms.update(new_owner, self.perms_autoroom_owner)
        if perms.modified:
            await autoroom_channel.edit(
                overwrites=perms.overwrites if perms.overwrites else {},
                reason="Sala: Se ha cambiado la propiedad",
            )
        await self.config.channel(autoroom_channel).owner.set(new_owner.id)
        if bucket:
            bucket.reset()
        await ctx.tick()
        await delete(ctx.message, delay=5)

    @room.command()
    async def move(self, ctx: commands.Context, member: discord.Member) -> None:
        """Mueve a una persona a tu sala si está en la sala específica."""
        if not ctx.guild:
            return

        # Check if the command author is the owner of the AutoRoom
        autoroom_channel, autoroom_info = await self._get_autoroom_channel_and_info(
            ctx, check_owner=True
        )
        if not autoroom_channel or not autoroom_info:
            return

        # The specific voice channel ID to check
        specific_voice_channel_id = 1127625556247203863
        specific_voice_channel = ctx.guild.get_channel(specific_voice_channel_id)

        # Check if the member is in the specific voice channel
        if not specific_voice_channel or member.voice.channel != specific_voice_channel:
            await ctx.send("La persona que quieres mover no está en la sala específica.")
            return

        # Check if the member is a moderator, administrator, or if they're trying to move one
        if (
            await self.is_mod_or_mod_role(member)
            or await self.is_admin_or_admin_role(member)
            or member == ctx.guild.owner
        ):
            await ctx.send("Mods, administradores o dueños del servidor no pueden ser movidos.")
            return

        # Move the member to the AutoRoom
        try:
            await member.move_to(autoroom_channel)
            await ctx.send(f"{member.display_name} ha sido movido a tu sala.")
        except discord.Forbidden:
            await ctx.send("No tengo permisos para mover miembros.")
        except discord.HTTPException:
            await ctx.send("Hubo un fallo al mover al miembro.")

    @room.command()
    async def name(self, ctx: commands.Context, *, new_name: str) -> None:
        """Cambia el nombre de tu sala de voz."""
        if not ctx.guild:
            return

        # Check if the command author is the owner of the AutoRoom
        autoroom_channel, autoroom_info = await self._get_autoroom_channel_and_info(
            ctx, check_owner=True
        )
        if not autoroom_channel or not autoroom_info:
            return

        # Validate and set the new name
        full_new_name = f"◇║{new_name}"
        try:
            await autoroom_channel.edit(name=full_new_name)
            await ctx.send(f"El nombre de la sala ha sido cambiado a: {full_new_name}")
        except discord.Forbidden:
            await ctx.send("No tengo permisos para cambiar el nombre de la sala.")
        except discord.HTTPException:
            await ctx.send("¡Oops! Hubo un error al cambiar el nombre de la sala.")

    @room.command()
    async def size(self, ctx: commands.Context, size: int) -> None:
        """Cambia el límite de usuarios de tu sala de voz."""
        if not ctx.guild:
            return

        # Check if the command author is the owner of the AutoRoom
        autoroom_channel, autoroom_info = await self._get_autoroom_channel_and_info(
            ctx, check_owner=True
        )
        if not autoroom_channel or not autoroom_info:
            return

        # Check if the provided size is valid
        if size < 0 or size > 99:  # Discord's maximum user limit for voice channels is 99
            await ctx.send("Por favor, introduce un número válido entre 0 y 99.")
            return

        # If size is 0, remove the user limit
        new_user_limit = None if size == 0 else size

        try:
            await autoroom_channel.edit(user_limit=new_user_limit)
            if new_user_limit:
                await ctx.send(f"El límite de usuarios de la sala se ha establecido en {new_user_limit}.")
            else:
                await ctx.send("El límite de usuarios de la sala ha sido eliminado.")
        except discord.Forbidden:
            await ctx.send("No tengo permisos para cambiar el límite de usuarios de la sala.")
        except discord.HTTPException:
            await ctx.send("Hubo un error al cambiar el límite de usuarios de la sala.")

    @room.command()
    async def public(self, ctx: commands.Context) -> None:
        """Haz tu sala pública."""
        await self._process_allow_deny(ctx, self.perms_public)

    @room.command()
    async def locked(self, ctx: commands.Context) -> None:
        """Bloquea tu sala (será privada, pero nadie podrá unirse)."""
        await self._process_allow_deny(ctx, self.perms_locked)

    @room.command()
    async def private(self, ctx: commands.Context) -> None:
        """Haz tu sala privada."""
        await self._process_allow_deny(ctx, self.perms_private)

#    @room.command(aliases=["add"])
#    async def allow(
#        self, ctx: commands.Context, member_or_role: discord.Role | discord.Member
#    ) -> None:
#        """Allow a user (or role) into your AutoRoom."""
#        await self._process_allow_deny(
#            ctx, self.perms_public, member_or_role=member_or_role
#        )

    @room.command(aliases=["ban", "block"])
    async def deny(
        self, ctx: commands.Context, member_or_role: discord.Role | discord.Member
    ) -> None:
        """Bloquea a un usuario (o rol) de entrar en tu Sala.

        Si el usuario (o usuarios con el rol) están en la sala, serán desconectados.
        """
        if not ctx.guild:
            return
        if await self._process_allow_deny(
            ctx, self.perms_private, member_or_role=member_or_role
        ):
            channel = self._get_current_voice_channel(ctx.message.author)
            if not channel or not channel.permissions_for(ctx.guild.me).move_members:
                return
            for member in channel.members:
                if not channel.permissions_for(member).connect:
                    await member.move_to(None, reason="AutoRoom: Deny user")

    async def _process_allow_deny(
        self,
        ctx: commands.Context,
        perm_overwrite: dict[str, bool],
        *,
        member_or_role: discord.Role | discord.Member | None = None,
    ) -> bool:
        """Actually do channel edit for allow/deny."""
        if not ctx.guild:
            return False
        autoroom_channel, autoroom_info = await self._get_autoroom_channel_and_info(ctx)
        if not autoroom_channel or not autoroom_info:
            return False

        if not autoroom_channel.permissions_for(autoroom_channel.guild.me).manage_roles:
            hint = await ctx.send(
                error(
                    f"{ctx.message.author.mention}, I do not have the required permissions to do this. "
                    "Please let the staff know about this!"
                )
            )
            await delete(ctx.message, delay=10)
            await delete(hint, delay=10)
            return False

        source_channel = ctx.guild.get_channel(autoroom_info["source_channel"])
        if not isinstance(source_channel, discord.VoiceChannel):
            hint = await ctx.send(
                error(
                    f"{ctx.message.author.mention}, it seems like the AutoRoom Source this AutoRoom was made from "
                    "no longer exists. Because of that, I can no longer modify this AutoRoom."
                )
            )
            await delete(ctx.message, delay=10)
            await delete(hint, delay=10)
            return False

        # Gather member roles and determine the lowest ranked member role
        member_roles = self.get_member_roles(source_channel)
        lowest_member_role = 999999999999
        for role in member_roles:
            lowest_member_role = min(lowest_member_role, role.position)

        denied_message = ""
        to_modify = [member_or_role]
        if not member_or_role:
            # Public/locked/private command
            to_modify = member_roles or [source_channel.guild.default_role]
        elif False not in perm_overwrite.values():
            # If we are allowing a bot role, allow it
            if isinstance(
                member_or_role, discord.Role
            ) and member_or_role in await self.get_bot_roles(ctx.guild):
                pass
            # Allow a specific user
            # - check if they have "connect" perm in the source channel
            # - works for both deny everyone with allowed roles/users, and allow everyone with denied roles/users
            # Allow a specific role
            # - Make sure that the role isn't specifically denied on the source channel
            elif not self.check_if_member_or_role_allowed(
                source_channel, member_or_role
            ):
                user_role = "user"
                them_it = "them"
                if isinstance(member_or_role, discord.Role):
                    user_role = "role"
                    them_it = "it"
                denied_message = (
                    f"since that {user_role} is not allowed to connect to the AutoRoom Source "
                    f"that this AutoRoom was made from, I can't allow {them_it} here either."
                )
            # Allow a specific role part 2
            # - Check that the role is equal to or above the lowest allowed (member) role on the source channel
            elif (
                isinstance(member_or_role, discord.Role)
                and member_roles
                and member_or_role.position < lowest_member_role
            ):
                denied_message = "this AutoRoom is using member roles, so I can't allow a lower hierarchy role."
        # Deny a specific user
        # - check that they aren't a mod/admin/owner/autoroom owner/bot itself, then deny user
        # Deny a specific role
        # - Check that it isn't a mod/admin role, then deny role
        elif member_or_role == ctx.guild.me:
            denied_message = "¿Por qué iba a prohibirme a mí entrar en la sala?"
        elif member_or_role == ctx.message.author:
            denied_message = "¡No seas tan dure contigo misme! ¡Esta sala es tuya!"
        elif member_or_role == ctx.guild.owner:
            denied_message = (
                "No puedo prohibirle a mi dueño entrar en la Sala... "
                "Lo siento, pero va contra mi programación de Spribotito."
            )
        elif await self.is_admin_or_admin_role(member_or_role):
            role_suffix = " role" if isinstance(member_or_role, discord.Role) else ""
            denied_message = f"that's an admin{role_suffix}, so I can't deny them from entering your AutoRoom."
        elif await self.is_mod_or_mod_role(member_or_role):
            role_suffix = " role" if isinstance(member_or_role, discord.Role) else ""
            denied_message = f"that's a moderator{role_suffix}, so I can't deny them from entering your AutoRoom."

        if denied_message:
            hint = await ctx.send(
                error(f"{ctx.message.author.mention}, {denied_message}")
            )
            await delete(ctx.message, delay=10)
            await delete(hint, delay=10)
            return False

        perms = Perms(autoroom_channel.overwrites)
        for target in to_modify:
            if isinstance(target, discord.Member | discord.Role):
                perms.update(target, perm_overwrite)
        if perms.modified:
            await autoroom_channel.edit(
                overwrites=perms.overwrites if perms.overwrites else {},
                reason="Sala: Permisos cambiados",
            )
        await ctx.tick()
        await delete(ctx.message, delay=5)
        return True

    @staticmethod
    def _get_current_voice_channel(
        member: discord.Member | discord.User,
    ) -> discord.VoiceChannel | None:
        """Get the members current voice channel, or None if not in a voice channel."""
        if (
            isinstance(member, discord.Member)
            and member.voice
            and isinstance(member.voice.channel, discord.VoiceChannel)
        ):
            return member.voice.channel
        return None

    async def _get_autoroom_channel_and_info(
        self, ctx: commands.Context, *, check_owner: bool = True
    ) -> tuple[discord.VoiceChannel | None, dict[str, Any] | None]:
        autoroom_channel = self._get_current_voice_channel(ctx.message.author)
        autoroom_info = await self.get_autoroom_info(autoroom_channel)
        if not autoroom_info:
            hint = await ctx.send(
                error(f"{ctx.message.author.mention}, no estás en una Sala.")
            )
            await delete(ctx.message, delay=5)
            await delete(hint, delay=5)
            return None, None
        if check_owner and ctx.message.author.id != autoroom_info["owner"]:
            reason_server = ""
            if not autoroom_info["owner"]:
                reason_server = " (it is a server AutoRoom)"
            hint = await ctx.send(
                error(
                    f"{ctx.message.author.mention}, no tienes la propiedad de esta Sala{reason_server}."
                )
            )
            await delete(ctx.message, delay=10)
            await delete(hint, delay=10)
            return None, None
        return autoroom_channel, autoroom_info

    @staticmethod
    def _get_autoroom_type(autoroom: discord.VoiceChannel, role: discord.Role) -> str:
        """Get the type of access a role has in an AutoRoom (public, locked, private, etc)."""
        view_channel = role.permissions.view_channel
        connect = role.permissions.connect
        if role in autoroom.overwrites:
            overwrites_allow, overwrites_deny = autoroom.overwrites[role].pair()
            if overwrites_allow.view_channel:
                view_channel = True
            if overwrites_allow.connect:
                connect = True
            if overwrites_deny.view_channel:
                view_channel = False
            if overwrites_deny.connect:
                connect = False
        if not view_channel and not connect:
            return "private"
        if view_channel and not connect:
            return "locked"
        return "public"
