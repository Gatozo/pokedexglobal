import os
import sys
import json
import time
import concurrent.futures
from pathlib import Path
from django.core.management.base import BaseCommand
from django.db import transaction
from tracker.models import Game, Pokedex, PokedexEntry, Pokemon, Move
from tracker.utils import (
    safe_api_get, 
    resolve_flavor_text, 
    resolve_obtaining_info,
    extract_game_specific_data
)

CACHE_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "data", "cache"
)

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
    help = "Sincroniza y almacena de forma exhaustiva los datos de Pokédex, movimientos, biomas y encuentros con modo Offline-First."

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
            help="Fuerza la descarga desde PokeAPI incluso si los datos ya existen en la base de datos"
        )
        parser.add_argument(
            "--delay",
            type=float,
            default=0.05,
            help="Pausa voluntaria entre peticiones (por defecto: 0.05s)"
        )
        parser.add_argument(
            "--force-all",
            action="store_true",
            help="Fuerza la sobreescritura incluso en entradas marcadas como personalizadas (is_custom_override=True)"
        )
        parser.add_argument(
            "--local",
            action="store_true",
            help="Modo Offline-First: procesa y recomputa usando exclusivamente la base de datos local y caché (0 peticiones a Internet)"
        )

    def fetch_pokemon_api_data(self, pokemon_id: int, national_number: int, name: str, existing_species: dict, existing_encounters: list, existing_evo: dict, force: bool, local_only: bool, pacing_delay: float):
        """Obtiene species, encounters y evolution_chain respetando la caché local."""
        species_data = existing_species
        encounters_data = existing_encounters
        evo_chain_data = existing_evo

        if not local_only:
            # 1. Species data
            if force or not species_data:
                s_resp = safe_api_get(f"https://pokeapi.co/api/v2/pokemon-species/{national_number}/", pacing_delay=pacing_delay)
                if s_resp and s_resp.status_code == 200:
                    species_data = s_resp.json()

            # 2. Encounters data
            if force or not encounters_data:
                enc_resp = safe_api_get(f"https://pokeapi.co/api/v2/pokemon/{national_number}/encounters", pacing_delay=pacing_delay)
                if enc_resp and enc_resp.status_code == 200:
                    encounters_data = enc_resp.json()
                elif not encounters_data:
                    encounters_data = []

        # 3. Evolution chain url
        evo_chain_url = None
        if species_data and not evo_chain_data:
            evo_chain_url = species_data.get("evolution_chain", {}).get("url")

        return {
            "pokemon_id": pokemon_id,
            "national_number": national_number,
            "name": name,
            "species_data": species_data or {},
            "encounters_data": encounters_data or [],
            "evolution_chain_data": evo_chain_data or {},
            "evo_chain_url": evo_chain_url,
        }

    def handle(self, *args, **options):
        game_slug = options["game"]
        workers = options["workers"]
        force = options["force"]
        force_all = options["force_all"]
        local_only = options["local"]
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

        mode_desc = "Offline-First (Local)" if local_only else ("Fuerza descarga completa" if force else "Store-and-Verify (Caché local con fallback)")
        self.stdout.write(f"Iniciando procesamiento de {total} Pokémon en '{game.display_name}' [Modo: {mode_desc}]...")

        # 1. Obtener o consultar datos de cada Pokémon
        targets = [
            (
                entry.pokemon.id, 
                entry.pokemon.national_number, 
                entry.pokemon.name, 
                entry.pokemon.species_data,
                entry.pokemon.encounters_data,
                entry.pokemon.evolution_chain_data
            )
            for entry in entries
        ]

        fetched_data = []
        if local_only:
            for p_id, num, name, s_data, enc_data, evo_data in targets:
                fetched_data.append({
                    "pokemon_id": p_id,
                    "national_number": num,
                    "name": name,
                    "species_data": s_data or {},
                    "encounters_data": enc_data or [],
                    "evolution_chain_data": evo_data or {},
                    "evo_chain_url": None,
                })
        else:
            with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
                future_to_poke = {
                    executor.submit(self.fetch_pokemon_api_data, p_id, num, name, s_data, enc_data, evo_data, force, local_only, pacing_delay): num
                    for p_id, num, name, s_data, enc_data, evo_data in targets
                }
                done = 0
                for future in concurrent.futures.as_completed(future_to_poke):
                    res = future.result()
                    fetched_data.append(res)
                    done += 1
                    if done % 50 == 0 or done == total:
                        self.stdout.write(f"Datos consolidados: {done}/{total} Pokémon...")

        # 2. Descargar cadenas evolutivas faltantes si no es modo puramente local
        chains_cache = {}
        # Primero rellenar con lo que ya está en fetched_data
        for d in fetched_data:
            if d.get("evolution_chain_data"):
                url = d.get("species_data", {}).get("evolution_chain", {}).get("url")
                if url:
                    chains_cache[url] = d["evolution_chain_data"]

        missing_evo_urls = {
            d["evo_chain_url"] for d in fetched_data 
            if d.get("evo_chain_url") and d["evo_chain_url"] not in chains_cache
        }

        if missing_evo_urls and not local_only:
            self.stdout.write(f"Descargando {len(missing_evo_urls)} árboles evolutivos faltantes desde PokeAPI...")
            def fetch_chain(url):
                resp = safe_api_get(url, pacing_delay=pacing_delay)
                return url, (resp.json() if resp and resp.status_code == 200 else None)

            with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
                for url, chain_json in executor.map(fetch_chain, missing_evo_urls):
                    if chain_json:
                        chains_cache[url] = chain_json

        # 3. Cargar catálogo completo de movimientos para enriquecer game_data
        self.stdout.write("Cargando catálogo de movimientos...")
        moves_qs = Move.objects.all()
        moves_map = {
            m.name: {
                "display_name": m.display_name,
                "type": m.type,
                "power": m.power,
                "accuracy": m.accuracy,
                "pp": m.pp,
                "damage_class": m.damage_class,
                "effect_description": m.effect_description,
            }
            for m in moves_qs
        }

        # 4. Guardar en base de datos y generar copias locales de respaldo
        self.stdout.write("Procesando estadísticas, movimientos, descripciones y métodos de obtención...")
        data_by_id = {d["pokemon_id"]: d for d in fetched_data}
        skipped_custom = 0

        # Respaldos en disco para inspección/edición manual
        os.makedirs(CACHE_DIR, exist_ok=True)
        backup_encounters = {}
        backup_evo_chains = {}

        with transaction.atomic():
            for entry in entries:
                d = data_by_id.get(entry.pokemon_id)
                if not d:
                    continue

                pokemon = entry.pokemon
                species = d["species_data"] or pokemon.species_data or {}
                encounters = d["encounters_data"] or pokemon.encounters_data or []
                chain_url = d.get("evo_chain_url") or species.get("evolution_chain", {}).get("url")
                chain_data = d.get("evolution_chain_data") or chains_cache.get(chain_url) or pokemon.evolution_chain_data or {}

                # 1. Actualizar Pokemon global
                cat = extract_category(species)
                pokemon.species_data = species
                pokemon.encounters_data = encounters
                pokemon.evolution_chain_data = chain_data
                if cat:
                    pokemon.category = cat
                pokemon.save(update_fields=["species_data", "encounters_data", "evolution_chain_data", "category"])

                if encounters:
                    backup_encounters[pokemon.national_number] = encounters
                if chain_data and chain_url:
                    backup_evo_chains[chain_url] = chain_data

                # 2. Actualizar PokedexEntry específico del juego
                if entry.is_custom_override and not force_all:
                    skipped_custom += 1
                    continue

                # Extraer datos completos del juego (movimientos, stats Gen 1, crianza)
                game_data = extract_game_specific_data(
                    raw_pokemon_data=pokemon.raw_data or {},
                    species_data=species,
                    game_slug=game_slug,
                    generation=game.generation,
                    moves_map=moves_map
                )

                flavor = resolve_flavor_text(pokemon.national_number, game_slug, species_data=species)
                obtaining = resolve_obtaining_info(
                    national_number=pokemon.national_number,
                    pokemon_name=pokemon.name,
                    game_slug=game_slug,
                    encounters_data=encounters,
                    evolution_chain_data=chain_data,
                    generation=game.generation
                )

                entry.flavor_text = flavor
                entry.obtaining_info = obtaining
                entry.game_data = game_data
                entry.save(update_fields=["flavor_text", "obtaining_info", "game_data"])

        # Guardar archivos JSON de respaldo en cache
        if backup_encounters:
            enc_file = os.path.join(CACHE_DIR, f"encounters_{game_slug}.json")
            with open(enc_file, "w", encoding="utf-8") as f:
                json.dump(backup_encounters, f, ensure_ascii=False, indent=2)
        if backup_evo_chains:
            evo_file = os.path.join(CACHE_DIR, "evolution_chains.json")
            with open(evo_file, "w", encoding="utf-8") as f:
                json.dump(backup_evo_chains, f, ensure_ascii=False, indent=2)

        msg = f"¡Procesamiento finalizado con éxito! Se actualizaron {total - skipped_custom} entradas para '{game.display_name}'."
        if skipped_custom > 0:
            msg += f" ({skipped_custom} entradas con modificación manual fueron protegidas y conservadas)."
        self.stdout.write(self.style.SUCCESS(msg))
