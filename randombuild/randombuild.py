import discord
from discord.ext import commands
from redbot.core import Config, commands
import random

class RandomBuild(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

        # Data
        self.pokemon = [
            'Absol', 'Aegislash', 'Azumarill', 'Blastoise', 'Blissey', 'Buzzwole',
            'Chandelure', 'Charizard', 'Cinderace', 'Clefable', 'Comfey', 'Cramorant',
            'Crustle', 'Decidueye', 'Delphox', 'Dodrio', 'Dragapult', 'Dragonite',
            'Duraludon', 'Eldegoss', 'Espeon', 'Garchomp', 'Gardevoir', 'Gengar',
            'Glaceon', 'Goodra', 'Greedent', 'Greninja', 'Hoopa', 'Inteleon',
            'Lapras', 'Leafeon', 'Lucario', 'Machamp', 'Mamoswine', 'Mewtwo X',
            'Mewtwo Y', 'Mr. Mime', 'Ninetales', 'Pikachu', 'Sableye', 'Slowbro',
            'Snorlax', 'Sylveon', 'Talonflame', 'Trevenant', 'Tsareena', 'Tyranitar',
            'Umbreon', 'Venusaur', 'Wiglytuff', 'Zacian', 'Zeraora', 'Zoroark', 'Scizor', 'Scyther',
            'Urshifu Estilo Brusco', 'Urshifu Estilo Fluido'
        ]
        self.banned_pokemon = []  # List to store banned Pokémon
        
        self.moves = {
            'Absol': [['Tajo Umbrío', 'Persecución'], ['Psicocorte', 'Golpe Bajo']],
            'Aegislash': [['Espada Santa', 'Garra Umbría'], ['Cabeza de Hierro', 'Vastaguardia']],
            'Azumarill': [['Torbellino', 'Acua Cola'], ['Carantoña', 'Hidropulso']],
            'Blastoise': [['Hidrobomba', 'Salpicar'], ['Surf', 'Giro Rápido']],
            'Blissey': [['Amortiguador', 'Velo Sagrado'], ['Bomba Huevo', 'Refuerzo']],
            'Buzzwole': [['Chupavidas', 'Fuerza Bruta'], ['Plancha', 'Antiaéreo']],
            'Chandelure': [['Lanzallamas', 'Sofoco'], ['Poltergeist', 'Sellar']],
            'Charizard': [['Lanzallamas', 'Puño Fuego'], ['Llamarada', 'Envite Ígneo']],
            'Cinderace': [['Balón Ígneo', 'Patada Ígnea'], ['Nitrocarga', 'Amago']],
            'Clefable': [['Luz Lunar', 'Beso Drenaje'], ['Gravedad', 'Señuelo']],
            'Comfey': [['Cura Floral', 'Beso Dulce'], ['Hoja Mágica', 'Hierba Lazo']],
            'Cramorant': [['Vendaval', 'Tajo Aéreo'], ['Surf', 'Buceo']],
            'Crustle': [['Tumba Rocas', 'Rompecoraza'], ['Trampa Rocas', 'Tijera X']],
            'Decidueye': [['Hoja Afilada', 'Puntada Sombría'], ['Lluevehojas', 'Sombra Vil']],
            'Delphox': [['Llamarada', 'Llama Embrujada'], ['Giro Fuego', 'Nitrocarga']],
            'Dodrio': [['Triataque', 'Pico Taladro'], ['Agilidad', 'Patada Salto']],
            'Dragapult': [['Danza Dragón', 'Golpe Fantasma'], ['Dragoaliento', 'Bola Sombra']],
            'Dragonite': [['Danza Dragón', 'Velocidad Extrema'], ['Hiperrayo', 'Enfado']],
            'Duraludon': [['Foco Resplandor', 'Pulso Dragón'], ['Cola Dragón', 'Trampa Rocas']],
            'Eldegoss': [['Bola de Polen', 'Ciclón de Hojas'], ['Rizo Algodón', 'Esporagodón']],
            'Espeon': [['Psicocarga', 'Poder Reserva'], ['Psicorrayo', 'Premonición']],
            'Garchomp': [['Excavar', 'Carga Dragón'], ['Terremoto', 'Garra Dragón']],
            'Gardevoir': [['Psicocarga', 'Premonición'], ['Psíquico', 'Fuerza Lunar']],
            'Gengar': [['Comesueños', 'Infortunio'], ['Bola Sombra', 'Bomba Lodo']],
            'Glaceon': [['Carámbano', 'Viento Hielo'], ['Canto Helado', 'Liofilización']],
            'Goodra': [['Agua Lodosa', 'Pulso Dragón'], ['Latigazo', 'Bomba Ácida']],
            'Greedent': [['Atiborramiento', 'Antojo'], ['Semilladora', 'Eructo']],
            'Greninja': [['Doble Equipo', 'Pantalla Humo'], ['Shuriken de Agua', 'Surf']],
            'Hoopa': [['Paso Dimensional', 'Truco'], ['Golpe Fantasma', 'Bola Sombra']],
            'Inteleon': [['Aguijón Letal', 'Acróbata'], ['Disparo Certero', 'Hidroariete']],
            'Lapras': [['Hidropulso', 'Canto Mortal'], ['Rayo Burbuja', 'Rayo Hielo']],
            'Leafeon': [['Hoja Afilada', 'Cuchillada Solar'], ['Golpe Aéreo', 'Hoja Aguda']],
            'Lucario': [['Velocidad Extrema', 'Puño Incremento'], ['Ataque Óseo', 'A Bocajarro']],
            'Machamp': [['Puño Dinámico', 'Sumisión'], ['A Bocajarro', 'Tajo Cruzado']],
            'Mamoswine': [['Chuzos', 'Colmillo Hielo'], ['Fuerza Equina', 'Terremoto']],
            'Mewtwo X': [['Premonición', 'Onda Mental'], ['Recuperación', 'Teletransporte']],
            'Mewtwo Y': [['Premonición', 'Onda Mental'], ['Recuperación', 'Teletransporte']],
            'Mr. Mime': [['Confusión', 'Psíquico'], ['Barrera', 'Cambiafuerza']],
            'Ninetales': [['Alud', 'Brillo Mágico'], ['Ventisca', 'Velo Aurora']],
            'Pikachu': [['Bola Voltio', 'Trueno'], ['Placaje Eléctrico', 'Rayo']],
            'Sableye': [['Desarme', 'Sombra Vil'], ['Finta', 'Rayo Confuso']],
            'Slowbro': [['Escaldar', 'Surf'], ['Amnesia', 'Telequinesis']],
            'Snorlax': [['Cuerpo Pesado', 'Azote'], ['Bloqueo', 'Bostezo']],
            'Sylveon': [['Llama Embrujada', 'Vozarrón'], ['Beso Drenaje', 'Paz Mental']],
            'Talonflame': [['Nitrocarga', 'Golpe Aéreo'], ['Vuelo', 'Pájaro Osado']],
            'Trevenant': [['Mazazo', 'Maldición'], ['Asta Drenaje', 'Divide Dolor']],
            'Tsareena': [['Triple Axel', 'Pisotón'], ['Patada Tropical', 'Fitoimpulso']],
            'Tyranitar': [['Pulso Umbrío', 'Roca Afilada'], ['Poder Pasado', 'Bucle Arena']],
            'Umbreon': [['Mal de Ojo', 'Juego Sucio'], ['Deseo', 'Alarido']],
            'Venusaur': [['Bomba Lodo', 'Gigadrenado'], ['Rayo Solar', 'Danza Pétalo']],
            'Wiglytuff': [['Rodar', 'Canto'], ['Doble Bofetón', 'Brillo Mágico']],
            'Zacian': [['Garra Metal', 'Espada Santa'], ['Agilidad', 'Carantoña']],
            'Zeraora': [['Voltiocambio', 'Chispa'], ['Chispazo', 'Voltio Cruel']],
            'Zoroark': [['Tajo Umbrío', 'Finta'], ['Garra Umbría', 'Corte']],
            'Scizor': [['Puño Bala'], ['Doble Golpe', 'Danza Espada']],
            'Scyther': [['Ala Bis'], ['Doble Golpe', 'Danza Espada']],
            'Urshifu Estilo Brusco': [['Golpe Oscuro'], ['Golpe Mordaza']],
            'Urshifu Estilo Fluido': [['Azote Torrencial'], ['Hidroariete']],
            'Mew': [
                ['Bola Voltio', 'Rayo Solar', 'Surf'], 
                ['Motivación', 'Pantalla de Luz', 'Agilidad']
            ]
                }
        
        self.combat_item = ['Poción', 'Ataque X', 'Velocidad X', 'Cola Skitty', 'Botón Escape', 'Humo Ralentizador', 'Cura Total', 'Apuratantos', 'Muñeco Shedinja']
        
        self.equipment_items = ['Cinta Fuerte', 'Periscopio', 'Garra Afilada', 'Cascabel Concha', 'Gafas Especiales', 'Energáfono', 'Gafas Elección', 'Pañuelo Combo', 'Corona Drenaje', 'Cuchara Peculiar', 'Brazalete Condena', 'Incienso Condena', 'Cinta Focus', 'Casco Dentado', 'Restos', 'Chaleco Asalto', 'Seguro Debilidad', 'Rodillera Escudo', 'Galleta Æos', 'Pesas Ofensivas', 'Gafas de Asalto', 'Piedra Pómez', 'Barrera Auxiliar', 'Repartir Experiencia', 'Cinta Rescate']
        
        self.line = ['Top', 'Bot', 'Jungla']

    @commands.command(name='randombuild', aliases=['rb'])
    async def random_build(self, ctx):
        # Ensure the chosen Pokemon is not banned
        available_pokemon = [p for p in self.pokemon if p not in self.banned_pokemon]
        
        if not available_pokemon:
            await ctx.send("All Pokémon are currently banned!")
            return

        chosen_pokemon = random.choice(available_pokemon)

        if chosen_pokemon == "Mew":
            first_set_moves = self.moves[chosen_pokemon][0]
            second_set_moves = self.moves[chosen_pokemon][1]
            
            num_moves_first_set = random.randint(1, len(first_set_moves))
            num_moves_second_set = random.randint(1, len(second_set_moves))

            chosen_moves = random.sample(first_set_moves, num_moves_first_set) + random.sample(second_set_moves, num_moves_second_set)
        else:
            chosen_moves = [random.choice(pair) for pair in self.moves[chosen_pokemon]]
        
        chosen_combat_item = random.choice(self.combat_item)
        
        if chosen_pokemon == 'Zacian':
            chosen_equipment = ['Espada Oxidada'] + random.sample([item for item in self.equipment_items if item != 'Espada Oxidada'], 2)
        else:
            chosen_equipment = random.sample(self.equipment_items, 3)  # This picks 3 unique items
        
        chosen_line = random.choice(self.line)
        
        message = (f"¡Hola, {ctx.author.mention}! Esta será tu build. ¡Prepara a tu Pokémon!\n\n"
                f"**Pokémon**: {chosen_pokemon}\n"
                f"**Movimientos**: {', '.join(chosen_moves)}\n"
                f"**Objeto de combate**: {chosen_combat_item}\n"
                f"**Objetos de equipo**: {', '.join(chosen_equipment)}\n"
                f"**Línea**: {chosen_line}")
        
        await ctx.send(message)

    @commands.group(name='randombuildset', aliases=['rbset'])
    @commands.has_permissions(administrator=True)
    async def randombuildset(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send("Comando no válido. Utiliza `ban`, `unban` o `list`.")

    @randombuildset.command(name='ban')
    async def ban(self, ctx, pokemon_name: str):
        if pokemon_name in self.pokemon and pokemon_name not in self.banned_pokemon:
            self.banned_pokemon.append(pokemon_name)
            await ctx.send(f"{pokemon_name} ha sido excluido del generador aleatorio!")
        else:
            await ctx.send(f"{pokemon_name} ya está excluido o no es un Pokémon válido.")

    @randombuildset.command(name='unban')
    async def unban(self, ctx, pokemon_name: str):
        if pokemon_name in self.banned_pokemon:
            self.banned_pokemon.remove(pokemon_name)
            await ctx.send(f"{pokemon_name} ha sido reintegrado al generador aleatorio!")
        else:
            await ctx.send(f"{pokemon_name} no está excluido del generador aleatorio.")

    @randombuildset.command(name='list')
    async def list_banned(self, ctx):
        if self.banned_pokemon:
            await ctx.send(f"Pokémon excluidos: {', '.join(self.banned_pokemon)}")
        else:
            await ctx.send("No hay Pokémon excluidos en este momento.")

