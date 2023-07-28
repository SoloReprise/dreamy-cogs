from typing import Any, List, Optional

import discord
from redbot.core import commands
from redbot.core.commands import Context
from redbot.core.utils import AsyncIter
from redbot.core.utils.menus import DEFAULT_CONTROLS, menu

from .abc import MixinMeta


class MyTTSCommand(MixinMeta):
    @commands.group()
    async def mytts(self, ctx: Context):
        """
        Configura tus opciones de TTS.
        """
        pass

    @mytts.command()
    async def voice(self, ctx: Context, voice: Optional[str] = None):
        """
        Cambia tu voz de TTS.
        Escribe {ctx.clean_prefix}tts --voices para ver las voces disponibles.
        Si no tienes voces personalizadas, te enseñará la voz por defecto.
        """

        current_voice = await self.config.user(ctx.author).voice()

        if not voice:
            await ctx.send(f"Tu voz actual es **{current_voice}**")
            return
        voice = voice.title()
        voice = self.get_voice(voice)
        if voice:
            await self.config.user(ctx.author).voice.set(voice["name"])
            await ctx.send(f"Tu nueva voz de TTS es: **{voice['name']}**")
        else:
            await ctx.send(
                f"Lo siento, esa voz no es válida. Puedes ver las voces mediante el comando `{ctx.clean_prefix}listvoices`."
            )

    @mytts.command()
    async def translate(self, ctx: Context):
        """
        Activa la traducción de TTS.
        """
        current_translate = await self.config.user(ctx.author).translate()

        if current_translate:
            await self.config.user(ctx.author).translate.set(False)
            await ctx.send("Traducción de TTS desactivada.")
        else:
            await self.config.user(ctx.author).translate.set(True)
            await ctx.send("Traducción de TTS activada.")

    @mytts.command()
    async def speed(self, ctx: Context, speed: float = 1.0):
        """
        Cambia la velocidad del TTS.

        La velocidad debe estar entre 0.5 y 10 (incluídos). El valor por defecto es 1.0.
        """
        if speed <= 0.5 or speed >= 10:
            await ctx.send("La velocidad debe estar entre 0.5 y 10.")
            return

        await self.config.user(ctx.author).speed.set(speed)
        await ctx.send(f"La velocidad de tu TTS ahora es {speed}.")
        return
