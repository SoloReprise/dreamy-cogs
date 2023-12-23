from .mysterygift import MysteryGift


async def setup(bot):
    cog = MysteryGift(bot)
    r = bot.add_cog(cog)
    if r is not None:
        await r
