import concurrent.futures
import requests
from django.core.management.base import BaseCommand
from django.db import transaction
from tracker.models import Game, Pokedex, PokedexEntry, Pokemon


class Command(BaseCommand):
    help = "Importa una Pokédex y sus Pokémon desde PokeAPI a la base de datos local."

    def add_arguments(self, parser):
        parser.add_argument(
            '--game',
            type=str,
            default='red',
            help='Slug del juego (ej: red, blue, firered)'
        )
        parser.add_argument(
            '--game-name',
            type=str,
            default='Pokémon Red',
            help='Nombre descriptivo del juego'
        )
        parser.add_argument(
            '--generation',
            type=int,
            default=1,
            help='Generación del juego (1, 2, 3...)'
        )
        parser.add_argument(
            '--pokedex',
            type=str,
            default='kanto',
            help='Nombre o slug de la Pokédex en PokeAPI (ej: kanto)'
        )
        parser.add_argument(
            '--pokedex-name',
            type=str,
            default='Pokédex Regional de Kanto',
            help='Nombre descriptivo de la Pokédex'
        )

    def fetch_pokemon_details(self, entry):
        entry_number = entry['entry_number']
        species_name = entry['pokemon_species']['name']
        species_url = entry['pokemon_species']['url']
        
        # Extraer ID nacional de la URL de species: https://pokeapi.co/api/v2/pokemon-species/{id}/
        national_number = int(species_url.rstrip('/').split('/')[-1])
        
        try:
            # Obtener datos de tipos y sprites desde el endpoint de pokemon
            resp = requests.get(f'https://pokeapi.co/api/v2/pokemon/{national_number}', timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                types = [t['type']['name'] for t in data.get('types', [])]
                primary_type = types[0] if types else 'normal'
                secondary_type = types[1] if len(types) > 1 else None
                
                # Sprites de alta definición (Artwork oficial) con fallback al sprite estándar
                artwork_url = (
                    data.get('sprites', {})
                    .get('other', {})
                    .get('official-artwork', {})
                    .get('front_default')
                )
                sprite_fallback = f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/{national_number}.png"
                sprite_url = artwork_url or sprite_fallback
                shiny_url = data.get('sprites', {}).get('front_shiny')
                
                return {
                    'entry_number': entry_number,
                    'national_number': national_number,
                    'name': species_name,
                    'display_name': species_name.replace('-', ' ').title(),
                    'primary_type': primary_type,
                    'secondary_type': secondary_type,
                    'sprite_url': sprite_url,
                    'sprite_shiny_url': shiny_url,
                    'height': data.get('height'),
                    'weight': data.get('weight'),
                }
        except Exception as e:
            self.stderr.write(f"Error descargando detalles de {species_name}: {e}")

        # Fallback si falla el detalle específico
        return {
            'entry_number': entry_number,
            'national_number': national_number,
            'name': species_name,
            'display_name': species_name.replace('-', ' ').title(),
            'primary_type': 'normal',
            'secondary_type': None,
            'sprite_url': f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/{national_number}.png",
            'sprite_shiny_url': None,
            'height': None,
            'weight': None,
        }

    def handle(self, *args, **options):
        game_slug = options['game']
        game_name = options['game_name']
        generation = options['generation']
        pokedex_slug = options['pokedex']
        pokedex_name = options['pokedex_name']

        self.stdout.write(f"Iniciando importación para: {game_name} (Pokédex: {pokedex_name})...")

        # 1. Crear o recuperar el Juego
        game, created_game = Game.objects.get_or_create(
            slug=game_slug,
            defaults={'name': game_name, 'generation': generation}
        )
        if created_game:
            self.stdout.write(self.style.SUCCESS(f"Juego '{game.name}' creado."))
        else:
            self.stdout.write(f"Juego existente: '{game.name}'.")

        # 2. Crear o recuperar la Pokédex
        pokedex, created_dex = Pokedex.objects.get_or_create(
            game=game,
            slug=pokedex_slug,
            defaults={
                'name': pokedex_name,
                'is_national': False,
                'pokeapi_name': pokedex_slug
            }
        )
        if created_dex:
            self.stdout.write(self.style.SUCCESS(f"Pokédex '{pokedex.name}' creada."))
        else:
            self.stdout.write(f"Pokédex existente: '{pokedex.name}'.")

        # 3. Consultar PokeAPI para la Pokédex
        pokedex_url = f"https://pokeapi.co/api/v2/pokedex/{pokedex_slug}/"
        self.stdout.write(f"Consultando PokeAPI en {pokedex_url}...")

        try:
            resp = requests.get(pokedex_url, timeout=15)
            resp.raise_for_status()
            pokeapi_data = resp.json()
        except requests.RequestException as e:
            self.stderr.write(self.style.ERROR(f"Error al conectar con PokeAPI: {e}"))
            return

        entries = pokeapi_data.get('pokemon_entries', [])
        total_entries = len(entries)
        self.stdout.write(f"Se encontraron {total_entries} entradas en la Pokédex.")

        # 4. Descargar detalles en paralelo
        self.stdout.write("Descargando detalles (tipos, imágenes) concurrentemente...")
        detailed_pokemon = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            future_to_entry = {executor.submit(self.fetch_pokemon_details, entry): entry for entry in entries}
            completed = 0
            for future in concurrent.futures.as_completed(future_to_entry):
                res = future.result()
                if res:
                    detailed_pokemon.append(res)
                completed += 1
                if completed % 25 == 0 or completed == total_entries:
                    self.stdout.write(f"Descargados {completed}/{total_entries}...")

        # Ordenar por entry_number
        detailed_pokemon.sort(key=lambda x: x['entry_number'])

        # 5. Guardar en Base de Datos de forma transaccional
        self.stdout.write("Guardando en la base de datos PostgreSQL...")
        with transaction.atomic():
            saved_count = 0
            for item in detailed_pokemon:
                pokemon, _ = Pokemon.objects.update_or_create(
                    national_number=item['national_number'],
                    defaults={
                        'name': item['name'],
                        'display_name': item['display_name'],
                        'sprite_url': item['sprite_url'],
                        'sprite_shiny_url': item['sprite_shiny_url'],
                        'primary_type': item['primary_type'],
                        'secondary_type': item['secondary_type'],
                        'height': item['height'],
                        'weight': item['weight'],
                    }
                )

                PokedexEntry.objects.update_or_create(
                    pokedex=pokedex,
                    entry_number=item['entry_number'],
                    defaults={
                        'pokemon': pokemon
                    }
                )
                saved_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"¡Importación completada exitosamente! Se procesaron {saved_count} Pokémon para {pokedex.name} ({game.name})."
            )
        )
