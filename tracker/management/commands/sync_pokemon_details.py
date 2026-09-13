import os
import sys
import time
import concurrent.futures
from pathlib import Path
from django.core.management.base import BaseCommand
from django.db import transaction
from tracker.models import Game, Pokedex, PokedexEntry, Pokemon
from tracker.utils import safe_api_get, resolve_flavor_text, resolve_obtaining_info

def extract_category(species_data: dict) -> str:
    """Extrae el género/categoría del Pokémon en español con fallback a inglés."""
    if not species_data:
        return ""
    genera = species_data.get("genera", [])
    for g in genera:
        if g.get("language", {}).get("name") == "es":
            return g.get("genus", "")
    for g in genera:
        if g.get("language", {}).get("name") == "en":
            return g.get("genus", "")
    return ""

class Command(BaseCommand):
    help = "Sincroniza descripciones de Pokédex, categorías y métodos de obtención para un juego específico."

    def add_arguments(self, parser):
        parser.add_argument(
            "--game",
            type=str,
            default="red",
            help="Slug del juego a sincronizar (ej: red, blue, yellow)"
        )
        parser.add_argument(
            "--workers",
            type=int,
            default=5,
            help="Número de hilos concurrentes para peticiones a PokeAPI (por defecto: 5)"
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help="Fuerza la descarga incluso si species_data ya existe"
        )
        parser.add_argument(
            "--delay",
            type=float,
            default=0.05,
            help="Pausa voluntaria entre peticiones (por defecto: 0.05s)"
        )

    def fetch_pokemon_api_data(self, pokemon_id: int, national_number: int, name: str, existing_species: dict, force: bool, pacing_delay: float):
        """Descarga species y encounters para un Pokémon."""
        # 1. Species data
        species_data = existing_species
        if force or not species_data:
            s_resp = safe_api_get(f"https://pokeapi.co/api/v2/pokemon-species/{national_number}/", pacing_delay=pacing_delay)
            if s_resp and s_resp.status_code == 200:
                species_data = s_resp.json()

        # 2. Encounters data
        enc_resp = safe_api_get(f"https://pokeapi.co/api/v2/pokemon/{national_number}/encounters", pacing_delay=pacing_delay)
        encounters_data = enc_resp.json() if enc_resp and enc_resp.status_code == 200 else []

        # 3. Evolution chain url
        evo_chain_url = None
        if species_data:
            evo_chain_url = species_data.get("evolution_chain", {}).get("url")

        return {
            "pokemon_id": pokemon_id,
            "national_number": national_number,
            "name": name,
            "species_data": species_data,
            "encounters_data": encounters_data,
            "evo_chain_url": evo_chain_url,
        }

    def handle(self, *args, **options):
        game_slug = options["game"]
        workers = options["workers"]
        force = options["force"]
        pacing_delay = options["delay"]

        try:
            game = Game.objects.get(slug=game_slug)
        except Game.DoesNotExist:
            self.stderr.write(self.style.ERROR(f"El juego con slug '{game_slug}' no existe en la base de datos."))
            return

        entries = PokedexEntry.objects.filter(pokedex__game=game).select_related("pokemon").order_by("entry_number")
        total = entries.count()
        if total == 0:
            self.stdout.write(self.style.WARNING(f"No se encontraron entradas de Pokédex para el juego '{game.display_name}'."))
            return

        self.stdout.write(f"Iniciando sincronización para {total} Pokémon en '{game.display_name}' ({workers} hilos)...")

        targets = [
            (entry.pokemon.id, entry.pokemon.national_number, entry.pokemon.name, entry.pokemon.species_data)
            for entry in entries
        ]

        fetched_data = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
            future_to_poke = {
                executor.submit(self.fetch_pokemon_api_data, p_id, num, name, s_data, force, pacing_delay): num
                for p_id, num, name, s_data in targets
            }
            done = 0
            for future in concurrent.futures.as_completed(future_to_poke):
                res = future.result()
                fetched_data.append(res)
                done += 1
                if done % 25 == 0 or done == total:
                    self.stdout.write(f"Descargados datos de PokeAPI: {done}/{total}...")

        # 2. Recolectar y descargar cadenas de evolución únicas necesarias
        evo_urls = {d["evo_chain_url"] for d in fetched_data if d["evo_chain_url"]}
        self.stdout.write(f"Descargando {len(evo_urls)} árboles evolutivos únicos...")

        chains_cache = {}
        def fetch_chain(url):
            resp = safe_api_get(url, pacing_delay=pacing_delay)
            return url, (resp.json() if resp and resp.status_code == 200 else None)

        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
            for url, chain_json in executor.map(fetch_chain, evo_urls):
                if chain_json:
                    chains_cache[url] = chain_json

        self.stdout.write("Procesando descripciones y métodos de obtención...")

        # 3. Guardar en base de datos de forma atómica
        poke_updates = []
        entry_updates = []

        data_by_id = {d["pokemon_id"]: d for d in fetched_data}

        with transaction.atomic():
            for entry in entries:
                d = data_by_id.get(entry.pokemon_id)
                if not d:
                    continue

                species = d["species_data"] or {}
                encounters = d["encounters_data"] or []
                chain_url = d["evo_chain_url"]
                chain_data = chains_cache.get(chain_url)

                # Actualizar Pokemon global
                cat = extract_category(species)
                pokemon = entry.pokemon
                pokemon.species_data = species
                if cat:
                    pokemon.category = cat
                pokemon.save(update_fields=["species_data", "category"])

                # Actualizar PokedexEntry específico del juego
                flavor = resolve_flavor_text(pokemon.national_number, game_slug, species_data=species)
                obtaining = resolve_obtaining_info(
                    national_number=pokemon.national_number,
                    pokemon_name=pokemon.name,
                    game_slug=game_slug,
                    encounters_data=encounters,
                    evolution_chain_data=chain_data
                )

                entry.flavor_text = flavor
                entry.obtaining_info = obtaining
                entry.save(update_fields=["flavor_text", "obtaining_info"])

        self.stdout.write(
            self.style.SUCCESS(
                f"¡Sincronización finalizada con éxito! Se actualizaron {total} entradas para '{game.display_name}'."
            )
        )
