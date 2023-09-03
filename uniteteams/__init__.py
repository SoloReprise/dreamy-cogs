from .uniteteams import UniteTeams


async def setup(bot):
    await bot.add_cog(UniteTeams(bot))
