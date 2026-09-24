import json
import logging
import os
import re
import time
import urllib.parse
import urllib.request
from typing import Any, Dict, Optional

from django.conf import settings
from django.core.management.base import BaseCommand
from tracker.models import Pokemon

logger = logging.getLogger(__name__)

# Mapeo de nombres especiales en títulos de WikiDex
WIKIDEX_TITLE_MAP = {
    29: "Nidoran hembra",
    32: "Nidoran macho",
    83: "Farfetch'd",
    122: "Mr. Mime",
    233: "Porygon2",
    250: "Ho-Oh",
}


def clean_wikitext_entry(text: str) -> str:
    """Limpia marcas de wikitexto, plantillas, enlaces y referencias HTML."""
    if not text:
        return ""

    # 1. Resolver {{NombreHaEs|Hispanoamérica|España}} -> tomar versión de España (segundo arg)
    m_haes = re.search(r"\{\{NombreHaEs\|([^|]+)(?:\|([^}]+))?\}\}", text, re.IGNORECASE)
    if m_haes:
        text = m_haes.group(2) if m_haes.group(2) else m_haes.group(1)

    # 2. Eliminar otras plantillas simples {{...}}
    text = re.sub(r"\{\{[^}]+\}\}", "", text)

    # 3. Eliminar enlaces de wiki [[Destino|Texto]] -> Texto, [[Texto]] -> Texto
    text = re.sub(r"\[\[(?:[^|\]]*\|)?([^\]]+)\]\]", r"\1", text)

    # 4. Eliminar referencias y etiquetas HTML <ref>...</ref>, <br>, etc.
    text = re.sub(r"<ref[^>]*>.*?</ref>", "", text, flags=re.DOTALL)
    text = re.sub(r"<[^>]+>", "", text)

    # 5. Normalizar espacios y saltos de línea
    text = text.replace("\n", " ").replace("\r", " ")
    text = " ".join(text.split())
    return text.strip()


def parse_pokedex_template(wikitext: str) -> Dict[str, str]:
    """Extrae y limpia todos los campos de la plantilla {{Pokédex}} de WikiDex."""
    m = re.search(r"\{\{Pokédex\s*\n(.*?)\n\}\}", wikitext, re.DOTALL | re.IGNORECASE)
    if not m:
        m = re.search(r"\{\{Pokédex\s*(.*?)\n\}\}", wikitext, re.DOTALL | re.IGNORECASE)
    if not m:
        return {}

    content = m.group(1)
    raw_entries: Dict[str, str] = {}
    lines = content.split("\n")
    current_key: Optional[str] = None
    current_val = []

    for line in lines:
        if line.startswith("|"):
            if current_key:
                raw_entries[current_key] = "\n".join(current_val).strip()
            parts = line[1:].split("=", 1)
            if len(parts) == 2:
                current_key = parts[0].strip().lower()
                current_val = [parts[1].strip()]
            else:
                current_key = None
                current_val = []
        elif current_key:
            current_val.append(line.strip())

    if current_key:
        raw_entries[current_key] = "\n".join(current_val).strip()

    cleaned = {k: clean_wikitext_entry(v) for k, v in raw_entries.items()}

    # Resolver referencias cruzadas (ej: | cristal = oro)
    for _ in range(3):
        for k, v in list(cleaned.items()):
            v_lower = v.lower()
            if v_lower in cleaned and cleaned[v_lower] != v:
                cleaned[k] = cleaned[v_lower]

    return cleaned


class Command(BaseCommand):
    help = "Extrae y consolida descripciones oficiales de la Pokédex en español desde WikiDex de forma segura y con rate-limiting."

    def add_arguments(self, parser):
        parser.add_argument("--start", type=int, default=1, help="Número nacional inicial (defecto: 1)")
        parser.add_argument("--end", type=int, default=251, help="Número nacional final (defecto: 251 para Gen 2)")
        parser.add_argument("--delay", type=float, default=0.25, help="Pausa en segundos entre peticiones (defecto: 0.25s)")
        parser.add_argument("--force-refresh", action="store_true", help="Ignora la caché local de WikiDex y vuelve a consultar.")
        parser.add_argument("--keep-raw-cache", action="store_true", help="Conserva el archivo intermedio de wikitext en disco tras finalizar.")

    def handle(self, *args, **options):
        start_num = options["start"]
        end_num = options["end"]
        delay = options["delay"]
        force_refresh = options["force_refresh"]

        self.stdout.write(self.style.NOTICE(f"Iniciando extracción de descripciones desde WikiDex (#{start_num} a #{end_num})..."))

        cache_dir = os.path.join(settings.BASE_DIR, "tracker", "data", "cache")
        flavor_dir = os.path.join(settings.BASE_DIR, "tracker", "data", "flavor_texts")
        os.makedirs(cache_dir, exist_ok=True)
        os.makedirs(flavor_dir, exist_ok=True)

        cache_file = os.path.join(cache_dir, "wikidex_pokedex_cache.json")
        cached_data: Dict[str, Dict[str, str]] = {}
        if os.path.exists(cache_file) and not force_refresh:
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    cached_data = json.load(f)
                self.stdout.write(self.style.SUCCESS(f"Se cargaron {len(cached_data)} entradas previas de la caché local."))
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"No se pudo leer la caché: {e}. Se reiniciará."))

        # Diccionarios finales para cada versión
        gold_catalog: Dict[str, Dict[str, str]] = {}
        silver_catalog: Dict[str, Dict[str, str]] = {}
        crystal_catalog: Dict[str, Dict[str, str]] = {}

        # Cargar archivos existentes si los hay para preservar datos fuera de rango
        for game_slug, cat in [("gold", gold_catalog), ("silver", silver_catalog), ("crystal", crystal_catalog)]:
            path = os.path.join(flavor_dir, f"{game_slug}_es.json")
            if os.path.exists(path):
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        cat.update(json.load(f))
                except Exception:
                    pass

        pokemon_list = Pokemon.objects.filter(
            national_number__gte=start_num, national_number__lte=end_num
        ).order_by("national_number")

        headers = {
            "User-Agent": "PokedexGlobal-Sync/1.0 (Educational/Personal Project; https://github.com/Gatozo/pokedexglobal)"
        }

        updated_count = 0
        total_pokes = len(pokemon_list)

        for idx, pokemon in enumerate(pokemon_list, start=1):
            nat_str = str(pokemon.national_number)
            entries: Dict[str, str] = {}

            if nat_str in cached_data and not force_refresh:
                entries = cached_data[nat_str]
            else:
                title = WIKIDEX_TITLE_MAP.get(pokemon.national_number, pokemon.display_name)
                # Formatear título para wiki
                title_clean = title.replace(" ", "_")
                quoted = urllib.parse.quote(title_clean)
                url = f"https://www.wikidex.net/api.php?action=parse&page={quoted}&prop=wikitext&format=json&redirects=1"

                retries = 3
                success = False
                for attempt in range(1, retries + 1):
                    try:
                        req = urllib.request.Request(url, headers=headers)
                        with urllib.request.urlopen(req, timeout=12) as response:
                            raw_json = json.loads(response.read().decode("utf-8"))
                            if "parse" in raw_json and "wikitext" in raw_json["parse"]:
                                wt = raw_json["parse"]["wikitext"]["*"]
                                entries = parse_pokedex_template(wt)
                                cached_data[nat_str] = entries
                                success = True
                                break
                            elif "error" in raw_json:
                                self.stdout.write(self.style.WARNING(f"Error WikiDex para #{pokemon.national_number} {title}: {raw_json['error'].get('info')}"))
                                break
                    except Exception as e:
                        wait_sec = attempt * 2
                        self.stdout.write(self.style.WARNING(f"Intento {attempt}/{retries} falló para #{pokemon.national_number} ({e}). Esperando {wait_sec}s..."))
                        time.sleep(wait_sec)

                if success:
                    updated_count += 1
                    # Guardar checkpoint cada 25 Pokémon
                    if updated_count % 25 == 0:
                        with open(cache_file, "w", encoding="utf-8") as f:
                            json.dump(cached_data, f, ensure_ascii=False, indent=2)
                        self.stdout.write(f"Checkpoint guardado: {idx}/{total_pokes} Pokémon procesados...")

                time.sleep(delay)

            # Extraer textos para Gen 2
            oro_text = entries.get("oro", "")
            plata_text = entries.get("plata", "")
            cristal_text = entries.get("cristal", "")

            # Si cristal no tiene texto directo pero oro/plata sí, no inventar; pero si es válido:
            if oro_text:
                gold_catalog[nat_str] = {
                    "name": pokemon.name,
                    "flavor_text_es": oro_text
                }
            if plata_text:
                silver_catalog[nat_str] = {
                    "name": pokemon.name,
                    "flavor_text_es": plata_text
                }
            if cristal_text:
                crystal_catalog[nat_str] = {
                    "name": pokemon.name,
                    "flavor_text_es": cristal_text
                }

        # Guardar caché final si fue solicitado explícitamente
        keep_raw = options.get("keep_raw_cache", False)
        if keep_raw:
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(cached_data, f, ensure_ascii=False, indent=2)
        elif os.path.exists(cache_file):
            try:
                os.remove(cache_file)
            except OSError:
                pass

        # Guardar catálogos finales en tracker/data/flavor_texts/
        gold_path = os.path.join(flavor_dir, "gold_es.json")
        with open(gold_path, "w", encoding="utf-8") as f:
            json.dump(gold_catalog, f, ensure_ascii=False, indent=2)
        self.stdout.write(self.style.SUCCESS(f"Guardado gold_es.json con {len(gold_catalog)} descripciones."))

        silver_path = os.path.join(flavor_dir, "silver_es.json")
        with open(silver_path, "w", encoding="utf-8") as f:
            json.dump(silver_catalog, f, ensure_ascii=False, indent=2)
        self.stdout.write(self.style.SUCCESS(f"Guardado silver_es.json con {len(silver_catalog)} descripciones."))

        crystal_path = os.path.join(flavor_dir, "crystal_es.json")
        with open(crystal_path, "w", encoding="utf-8") as f:
            json.dump(crystal_catalog, f, ensure_ascii=False, indent=2)
        self.stdout.write(self.style.SUCCESS(f"Guardado crystal_es.json con {len(crystal_catalog)} descripciones."))

        self.stdout.write(self.style.SUCCESS("¡Extracción y generación de catálogos completada con éxito!"))
