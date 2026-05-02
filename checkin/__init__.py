from .checkin import CheckIn


async def setup(bot):
    await bot.add_cog(CheckIn(bot))
