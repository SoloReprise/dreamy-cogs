from .unitecog import UniteCog
import unicodedata


async def setup(bot):
    await bot.add_cog(UniteCog(bot))