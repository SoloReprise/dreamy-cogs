import discord
from redbot.core import commands

class Meta(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Dictionary to store the Pokémon names and their corresponding thread IDs
    pokemon_threads = {
        'Absol': '1127778997565145138',
        'Duraludon': '1127782566007681115',
        'Mewtwo X': '1131856477288669264',
        'Decidueye': '1127781402839093318',
        'Urshifu': '1127783042451247237',
        'Zeraora': '1127781895497850970',
        'Leafeon': '1127779402508410890',
        'Lucario': '1127779275244847214',
        'Dragonite': '1127777108920369173',
        'Mamoswine': '1127779702258552943',
        'Wigglytuff': '1127773781738389694',
        'Goodra': '1127780883001254008',
        'Zoroark': '1127779980269596705',
        'Chandelure': '1127780106669142037',
        'Umbreon': '1127777637796937790',
        'Inteleon': '1127782159256666275',
        'Slowbro': '1127774587791343697',
        'Gardevoir': '1127778711811399740',
        'Scizor': '1127778313801318400',
        'Scyther': '1127778313801318400',
        'Tsareena': '1127781520845836318',
        'Zacian': '1127782821642121256',
        'Dragapult': '1127782685872488488',
        'Cramorant': '1127782446000259122',
        'Eldegoss': '1127782321798520853',
        'Cinderace': '1127782021020790794',
        'Buzzwole': '1127781791265214564',
        'Comfey': '1127781665826152553',
        'Hoopa': '1127781272874397746',
        'Trevenant': '1127780987170988162',
        'Sylveon': '1127780768555466752',
        'Aegislash': '1127780627895300117',
        'Talonflame': '1127780502582079598',
        'Greninja': '1127780357262032908',
        'Delphox': '1127780244816920616',
        'Crustle': '1127779836291731467',
        'Glaceon': '1127779536533196800',
        'Garchomp': '1127779133477363712',
        'Sableye': '1127778858918223984',
        'Tyranitar': '1127778597776670841',
        'Blissey': '1127778462883663964',
        'Espeon': '1127777511619710986',
        'Azumarill': '1127777387967434752',
        'Mew': '1127777251451207760',
        'Snorlax': '1127776974610374676',
        'Lapras': '1127776831081304124',
        'Mr. Mime': '1127776324761702420',
        'Mr Mime': '1127776324761702420',
        'Gengar': '1127776152518398082',
        'Dodrio': '1127776041180614747',
        'Machamp': '1127774166586753144',
        'Ninetales': '1127773555455692940',
        'Ninetales de Alola': '1127773555455692940',
        'Clefable': '1127773194670047315',
        'Pikachu': '1127772842893778985',
        'Blastoise': '1127772248762224680',
        'Charizard': '1127772018494931014',
        'Venusaur': '1127771637056540744',
        # Add more Pokémon and their thread IDs as needed
    }

    @commands.command()
    async def meta(self, ctx, *, pokemon_name):
        """
        Encuentra el hilo del pokémon buscado en el foro de meta.
        """
        # Modify the input name to match dictionary key format
        modified_name = pokemon_name.title()

        # Get the corresponding thread ID from the dictionary
        thread_id = self.pokemon_threads.get(modified_name)

        if thread_id:
            # Construct a mention for the thread ID
            mention = f'<#{thread_id}>'
            await ctx.send(mention)
        else:
            await ctx.send(f"Sorry, I couldn't find the thread ID for {pokemon_name}.")