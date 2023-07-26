import discord
from redbot.core import commands

class Meta(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Dictionary to store the Pokémon names and their corresponding thread IDs
    pokemon_threads = {
        'Absol': '1133814648311914698',
        'Duraludon': 'YOUR_DURALUDON_THREAD_ID',
        # Add more Pokémon and their thread IDs as needed
    }

    @commands.command()
    async def meta(self, ctx, *, pokemon_name):
        # Get the corresponding thread ID from the dictionary
        thread_id = self.pokemon_threads.get(pokemon_name.capitalize())

        if thread_id:
            # Construct a mention for the thread ID
            mention = f'<#{thread_id}>'
            await ctx.send(mention)
        else:
            await ctx.send(f"Sorry, I couldn't find the thread ID for {pokemon_name}.")

def setup(bot):
    bot.add_cog(Meta(bot))
