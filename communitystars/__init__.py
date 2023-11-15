from .communitystars import CommunityStars

async def setup(bot):
    await bot.add_cog(CommunityStars(bot))
