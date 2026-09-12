import os
import time
from pathlib import Path
import concurrent.futures
import requests
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction
from tracker.models import Game, Pokedex, PokedexEntry, Pokemon, GAME_NAMES_ES


class Command(BaseCommand):
    help = "Importa una Pokédex y sus Pokémon desde PokeAPI a la base de datos local y almacena sus imágenes en media/."

    def add_arguments(self, parser):
        parser.add_argument(
            '--game',
            type=str,
            default='red',
            help='Slug del juego (ej: red, blue, firered, white, ultra-sun)'
        )
        parser.add_argument(
            '--game-name',
            type=str,
            default='',
            help='Nombre descriptivo del juego (opcional; se asigna automáticamente en español)'
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
        parser.add_argument(
            '--force-refresh',
            action='store_true',
            help='Fuerza la descarga de PokeAPI aunque el Pokémon ya exista en la base de datos'
        )

    def save_media_file(self, url, relative_path):
        """Descarga y guarda localmente un archivo en MEDIA_ROOT si no existe."""
        if not url:
            return None

        full_path = Path(settings.MEDIA_ROOT) / relative_path
        full_path.parent.mkdir(parents=True, exist_ok=True)

        if full_path.exists() and full_path.stat().st_size > 0:
            media_url = settings.MEDIA_URL.rstrip('/') + '/' + relative_path.replace('\\', '/')
            return media_url

        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        for attempt in range(3):
            try:
                resp = requests.get(url, headers=headers, timeout=12)
                if resp.status_code == 200 and len(resp.content) > 0:
                    with open(full_path, 'wb') as f:
                        f.write(resp.content)
                    media_url = settings.MEDIA_URL.rstrip('/') + '/' + relative_path.replace('\\', '/')
                    return media_url
            except Exception:
                time.sleep(0.3)

        return url

    def get_game_sprite(self, data, game_slug, generation):
        """Extrae el sprite específico del juego/generación (retro) si aplica (Gen 1-5)."""
        if generation > 5:
            return None

        versions = data.get('sprites', {}).get('versions', {})

        if generation == 1:
            gen1 = versions.get('generation-i', {})
            game_data = gen1.get('yellow', {}) if game_slug == 'yellow' else gen1.get('red-blue', {})
            return game_data.get('front_transparent') or game_data.get('front_default')

        elif generation == 2:
            gen2 = versions.get('generation-ii', {})
            game_data = gen2.get('crystal') or gen2.get('gold') or gen2.get('silver') or {}
            return game_data.get('front_transparent') or game_data.get('front_default')

        elif generation == 3:
            gen3 = versions.get('generation-iii', {})
            game_data = gen3.get('emerald') or gen3.get('firered-leafgreen') or gen3.get('ruby-sapphire') or {}
            return game_data.get('front_default')

        elif generation == 4:
            gen4 = versions.get('generation-iv', {})
            game_data = gen4.get('platinum') or gen4.get('heartgold-soulsilver') or gen4.get('diamond-pearl') or {}
            return game_data.get('front_default')

        elif generation == 5:
            gen5 = versions.get('generation-v', {})
            game_data = gen5.get('black-white', {})
            animated = game_data.get('animated', {}).get('front_default')
            return animated or game_data.get('front_default')

        return None

    def fetch_pokemon_details(self, entry, game_slug, generation, existing_pokemon=None, force_refresh=False):
        entry_number = entry['entry_number']
        species_name = entry['pokemon_species']['name']
        species_url = entry['pokemon_species']['url']
        
        # Extraer ID nacional de la URL de species: https://pokeapi.co/api/v2/pokemon-species/{id}/
        national_number = int(species_url.rstrip('/').split('/')[-1])
        
        # 1. Estrategia Local-First: Si ya existe en BD local con raw_data, reutilizar sin peticiones a la API
        if not force_refresh and existing_pokemon and existing_pokemon.raw_data:
            data = existing_pokemon.raw_data
            is_from_cache = True
        else:
            data = None
            is_from_cache = False
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
            for attempt in range(3):
                try:
                    resp = requests.get(f'https://pokeapi.co/api/v2/pokemon/{national_number}', headers=headers, timeout=12)
                    if resp.status_code == 200:
                        data = resp.json()
                        break
                    elif resp.status_code == 429:
                        time.sleep(1.5 * (attempt + 1))
                except Exception as e:
                    time.sleep(0.4)

        if data:
            try:
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
                remote_artwork_url = artwork_url or sprite_fallback
                shiny_url = data.get('sprites', {}).get('front_shiny')
                
                # Sprite retro específico del juego extraído de raw_data
                remote_game_sprite_url = self.get_game_sprite(data, game_slug, generation)

                # Descargar y almacenar localmente en media/ (si ya existe en disco retorna de inmediato)
                local_artwork_url = self.save_media_file(remote_artwork_url, f"pokemon/artwork/{national_number}.png")
                local_game_sprite_url = self.save_media_file(
                    remote_game_sprite_url, f"pokemon/sprites/{game_slug}/{national_number}.png"
                ) if remote_game_sprite_url else None

                return {
                    'entry_number': entry_number,
                    'national_number': national_number,
                    'name': species_name,
                    'display_name': species_name.replace('-', ' ').title(),
                    'primary_type': primary_type,
                    'secondary_type': secondary_type,
                    'sprite_url': local_artwork_url or remote_artwork_url,
                    'sprite_shiny_url': shiny_url,
                    'game_sprite_url': local_game_sprite_url or remote_game_sprite_url,
                    'height': data.get('height'),
                    'weight': data.get('weight'),
                    'raw_data': data,
                    'from_cache': is_from_cache,
                }
            except Exception as e:
                self.stderr.write(f"Error procesando {species_name}: {e}")

        # Fallback si falla la obtención de datos
        fallback_url = f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/{national_number}.png"
        return {
            'entry_number': entry_number,
            'national_number': national_number,
            'name': species_name,
            'display_name': species_name.replace('-', ' ').title(),
            'primary_type': getattr(existing_pokemon, 'primary_type', 'normal'),
            'secondary_type': getattr(existing_pokemon, 'secondary_type', None),
            'sprite_url': getattr(existing_pokemon, 'sprite_url', fallback_url),
            'sprite_shiny_url': getattr(existing_pokemon, 'sprite_shiny_url', None),
            'game_sprite_url': None,
            'height': getattr(existing_pokemon, 'height', None),
            'weight': getattr(existing_pokemon, 'weight', None),
            'raw_data': getattr(existing_pokemon, 'raw_data', {}),
            'from_cache': is_from_cache,
        }


    def handle(self, *args, **options):
        game_slug = options['game']
        game_name = options['game_name']
        generation = options['generation']
        pokedex_slug = options['pokedex']
        pokedex_name = options['pokedex_name']
        force_refresh = options.get('force_refresh', False)

        if not game_name:
            if game_slug in GAME_NAMES_ES:
                game_name = GAME_NAMES_ES[game_slug]
            else:
                try:
                    v_resp = requests.get(f'https://pokeapi.co/api/v2/version/{game_slug}', timeout=5)
                    if v_resp.status_code == 200:
                        es_names = [n['name'] for n in v_resp.json().get('names', []) if n.get('language', {}).get('name') == 'es']
                        if es_names:
                            game_name = f"Pokémon {es_names[0]}"
                except Exception:
                    pass
                if not game_name:
                    game_name = f"Pokémon {game_slug.replace('-', ' ').title()}"

        self.stdout.write(f"Iniciando importación para: {game_name} (Pokédex: {pokedex_name})...")

        # 1. Crear o recuperar el Juego
        game, created_game = Game.objects.get_or_create(
            slug=game_slug,
            defaults={'name': game_name, 'generation': generation}
        )
        if created_game:
            self.stdout.write(self.style.SUCCESS(f"Juego '{game.name}' creado."))
        else:
            if game.name != game_name:
                game.name = game_name
                game.save(update_fields=['name'])
                self.stdout.write(f"Juego actualizado con nombre en español: '{game.name}'.")
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

        # 4. Comprobación Local-First: Consultar en lote los Pokémon existentes en la base de datos local
        national_ids = []
        for entry in entries:
            species_url = entry.get('pokemon_species', {}).get('url', '')
            if species_url:
                try:
                    national_ids.append(int(species_url.rstrip('/').split('/')[-1]))
                except ValueError:
                    pass

        existing_pokemon_map = {
            p.national_number: p
            for p in Pokemon.objects.filter(national_number__in=national_ids)
        }
        cached_count = sum(1 for p in existing_pokemon_map.values() if p.raw_data)
        if not force_refresh and cached_count > 0:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Aceleración Local-First: {cached_count}/{total_entries} Pokémon se reutilizarán de la base de datos local (0 peticiones a la API)."
                )
            )

        # 5. Descargar/reutilizar detalles en paralelo (con 5 workers controlados)
        self.stdout.write("Procesando Pokémon (extrayendo sprites locales o descargando nuevos)...")
        detailed_pokemon = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            future_to_entry = {}
            for entry in entries:
                species_url = entry.get('pokemon_species', {}).get('url', '')
                nid = int(species_url.rstrip('/').split('/')[-1]) if species_url else 0
                existing_p = existing_pokemon_map.get(nid)
                future = executor.submit(
                    self.fetch_pokemon_details, entry, game_slug, generation, existing_p, force_refresh
                )
                future_to_entry[future] = entry

            completed = 0
            for future in concurrent.futures.as_completed(future_to_entry):
                res = future.result()
                if res:
                    detailed_pokemon.append(res)
                completed += 1
                if completed % 25 == 0 or completed == total_entries:
                    self.stdout.write(f"Procesados {completed}/{total_entries}...")

        from_cache_total = sum(1 for p in detailed_pokemon if p.get('from_cache'))
        from_api_total = len(detailed_pokemon) - from_cache_total
        self.stdout.write(f"Resumen de obtención: {from_cache_total} locales de BD, {from_api_total} descargados de PokeAPI.")

        # Ordenar por entry_number
        detailed_pokemon.sort(key=lambda x: x['entry_number'])

        # 6. Guardar en Base de Datos de forma transaccional
        self.stdout.write("Guardando en la base de datos PostgreSQL...")
        with transaction.atomic():
            saved_count = 0
            for item in detailed_pokemon:
                pokemon_defaults = {
                    'name': item['name'],
                    'display_name': item['display_name'],
                    'sprite_url': item['sprite_url'],
                    'sprite_shiny_url': item['sprite_shiny_url'],
                    'primary_type': item['primary_type'],
                    'secondary_type': item['secondary_type'],
                    'height': item['height'],
                    'weight': item['weight'],
                }
                if item.get('raw_data'):
                    pokemon_defaults['raw_data'] = item['raw_data']

                pokemon, _ = Pokemon.objects.update_or_create(
                    national_number=item['national_number'],
                    defaults=pokemon_defaults
                )

                PokedexEntry.objects.update_or_create(
                    pokedex=pokedex,
                    entry_number=item['entry_number'],
                    defaults={
                        'pokemon': pokemon,
                        'game_sprite_url': item['game_sprite_url'],
                    }
                )
                saved_count += 1


        self.stdout.write(
            self.style.SUCCESS(
                f"¡Importación completada exitosamente! Se procesaron {saved_count} Pokémon para {pokedex.name} ({game.name})."
            )
        )
