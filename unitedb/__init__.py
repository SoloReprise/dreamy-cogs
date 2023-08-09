from .unitecog import UniteCog
import unicodedata
from unidecode import unidecode

async def setup(bot):
    await bot.add_cog(UniteCog(bot))