import discord
from discord.ext import commands
from redbot.core import Config, commands
import random
import re

def normalize_name(name):
    # Convert to lowercase only
    return name.lower()

class RandomBuild(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

        # Data
        self.pokemon = [
            'Absol', 'Aegislash', 'Azumarill', 'Blastoise', 'Blaziken', 'Blissey', 'Buzzwole',
            'Chandelure', 'Charizard', 'Cinderace', 'Clefable', 'Comfey', 'Cramorant',
            'Crustle', 'Decidueye', 'Delphox', 'Dodrio', 'Dragapult', 'Dragonite',
            'Duraludon', 'Eldegoss', 'Espeon', 'Garchomp', 'Gardevoir', 'Gengar',
            'Glaceon', 'Goodra', 'Greedent', 'Greninja', 'Hoopa', 'Inteleon',
            'Lapras', 'Leafeon', 'Lucario', 'Machamp', 'Mamoswine', 'Mewoscarada','Mewtwo X',
            'Mewtwo Y', 'Mimikyu', 'Mr. Mime', 'Ninetales', 'Pikachu', 'Sableye', 'Slowbro',
            'Snorlax', 'Sylveon', 'Talonflame', 'Trevenant', 'Tsareena', 'Tyranitar',
            'Umbreon', 'Venusaur', 'Wiglytuff', 'Zacian', 'Zeraora', 'Zoroark', 'Scizor', 'Scyther',
            'Urshifu', 'Mew', 
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
            'Meowscarada': [['Truco Floral', 'Tajo Umbrío'], ['Doble Equipo', 'Abrecaminos']],            
            'Mewtwo X': [['Premonición', 'Onda Mental'], ['Recuperación', 'Teletransporte']],
            'Mewtwo Y': [['Premonición', 'Onda Mental'], ['Recuperación', 'Teletransporte']],
            'Mimikyu': [['Carantoña', 'Garra Umbría'], ['Sombra Vil', 'Espacio Raro']],
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
            'Urshifu': {
                'Brusco': [['Golpe Oscuro'], ['Golpe Mordaza']],
                'Fluido': [['Azote Torrencial'], ['Hidroariete']]
            },
            'Mew': [
                ['Bola Voltio', 'Rayo Solar', 'Surf'], 
                ['Motivación', 'Pantalla de Luz', 'Agilidad']
            ],
            'Blaziken': [
                ['Patada Ígnea', 'Sofoco'], 
                ['Puño Fuego', 'Onda Certera']
            ],
                }
        
        self.combat_item = ['Poción', 'Ataque X', 'Velocidad X', 'Cola Skitty', 'Botón Escape', 'Humo Ralentizador', 'Cura Total', 'Apuratantos', 'Muñeco Shedinja']
        
        self.equipment_items = ['Cinta Fuerte', 'Periscopio', 'Garra Afilada', 'Cascabel Concha', 'Gafas Especiales', 'Energáfono', 'Gafas Elección', 'Pañuelo Combo', 'Corona Drenaje', 'Cuchara Peculiar', 'Brazalete Condena', 'Incienso Condena', 'Cinta Focus', 'Casco Dentado', 'Restos', 'Chaleco Asalto', 'Seguro Debilidad', 'Rodillera Escudo', 'Galleta Æos', 'Pesas Ofensivas', 'Gafas de Asalto', 'Piedra Pómez', 'Barrera Auxiliar', 'Repartir Experiencia', 'Capucha Rescate', 'Guardia Resonante', 'Colgante Carga']
        
        self.line = ['Top', 'Bot', 'Jungla']

    @commands.command(name='randombuild', aliases=['rb'])
    async def random_build(self, ctx, *args):
        specified_pokemon = " ".join(args).strip() if args else None

        if specified_pokemon:
            normalized_input = specified_pokemon.lower()

            # Handle special cases more robustly
            if "mewtwo" in normalized_input:
                if "x" in normalized_input:
                    matched_pokemon = "Mewtwo X"
                elif "y" in normalized_input:
                    matched_pokemon = "Mewtwo Y"
                else:
                    matched_pokemon = None
            elif "mew" == normalized_input:
                matched_pokemon = "Mew"
            else:
                # General matching logic for other Pokémon
                matched_pokemon = next((pokemon for pokemon in self.pokemon if normalized_input in pokemon.lower()), None)

            if not matched_pokemon:
                await ctx.send(f"¡El Pokémon {specified_pokemon} no es válido!")
                return
            elif matched_pokemon in self.banned_pokemon:
                await ctx.send(f"¡El Pokémon {matched_pokemon} está baneado!")
                return

            specified_pokemon = matched_pokemon
        else:
            # Ensure the chosen Pokemon is not banned
            available_pokemon = [p for p in self.pokemon if p not in self.banned_pokemon]
            
            if not available_pokemon:
                await ctx.send("¡Todos los Pokémon están actualmente baneados!")
                return

            specified_pokemon = random.choice(available_pokemon)

        if specified_pokemon == "Mew":
            first_set_moves = self.moves[specified_pokemon][0]
            second_set_moves = self.moves[specified_pokemon][1]
            
            num_moves_first_set = random.randint(1, len(first_set_moves))
            num_moves_second_set = random.randint(1, len(second_set_moves))

            chosen_moves = random.sample(first_set_moves, num_moves_first_set) + random.sample(second_set_moves, num_moves_second_set)
        elif specified_pokemon == "Blaziken":
            style = random.choice(["Estilo Puñetazo", "Estilo Patada", "Ambos estilos"])
            first_set_moves = self.moves[specified_pokemon][0]  # Onda Certera and Puño Fuego
            second_set_moves = self.moves[specified_pokemon][1]  # Patada Ígnea and Sofoco

            if style == "Estilo Puñetazo":
                chosen_moves = random.sample(first_set_moves, min(2, len(first_set_moves)))
            elif style == "Estilo Patada":
                chosen_moves = random.sample(second_set_moves, min(2, len(second_set_moves)))
            else:  # Ambos estilos
                chosen_moves = first_set_moves + second_set_moves
        elif specified_pokemon == "Urshifu":
            style = random.choice(["Brusco", "Fluido"])
            movesets = self.moves[specified_pokemon][style]
            
            # Assuming each moveset only has one move, so we take the first element
            chosen_moves = [moveset[0] for moveset in movesets]                
        else:
            chosen_moves = [random.choice(pair) for pair in self.moves[specified_pokemon]]
        
        chosen_combat_item = random.choice(self.combat_item)
        
        if specified_pokemon == 'Zacian':
            chosen_equipment = ['Espada Oxidada'] + random.sample([item for item in self.equipment_items if item != 'Espada Oxidada'], 2)
        else:
            chosen_equipment = random.sample(self.equipment_items, 3)  # This picks 3 unique items
        
        chosen_line = random.choice(self.line)
        
        # Construct the base message
        message = (f"¡Hola, {ctx.author.mention}! Esta será tu build. ¡Prepara a tu Pokémon!\n\n"
                f"**Pokémon**: {specified_pokemon}\n")

        # Add the style line only for Blaziken and Urshifu
        if specified_pokemon in ["Blaziken", "Urshifu"]:
            message += f"**Estilo**: {style}\n"

        # Continue with the rest of the message
        message += (f"**Movimientos**: {', '.join(chosen_moves)}\n"
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

