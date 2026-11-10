"""
Script para sincronizar las descripciones oficiales en español de Pokémon Plata SoulSilver
desde la API de WikiDex, preservando la variante canónica oficial de los cartuchos en España.
Genera: tracker/data/cache/wikidex_soulsilver_descriptions.json
"""
import json
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path

# Reutilizamos las funciones de limpieza de HeartGold
from sync_heartgold_descriptions import (
    extract_pokedex_template, 
    parse_template_fields, 
    resolve_field_text, 
    fetch_wikidex_batch, 
    CUSTOM_TITLES
)

BASE_DIR = Path(__file__).resolve().parent.parent.parent
CACHE_DIR = BASE_DIR / "tracker" / "data" / "cache"

PRIMARY_KEYS = [
    "plata soulsilver",
    "plata-soulsilver",
    "soulsilver",
    "ss",
    "plata"
]

FALLBACK_KEYS = [
    "oro heartgold",
    "oro-heartgold",
    "heartgold",
    "hg",
    "cristal",
    "plata",
    "oro",
    "platino",
    "diamante",
    "perla"
]

def main():
    force_all = "--force" in sys.argv
    print("Iniciando sincronización oficial de descripciones de Pokémon Plata SoulSilver...")

    species_file = CACHE_DIR / "pokemon_493_species.json"
    if not species_file.exists():
        print(f"ERROR: No se encontró {species_file}")
        return

    with open(species_file, "r", encoding="utf-8") as f:
        species_493 = json.load(f)

    cache_output = CACHE_DIR / "wikidex_soulsilver_descriptions.json"
    descriptions = {}
    if cache_output.exists() and not force_all:
        try:
            with open(cache_output, "r", encoding="utf-8") as f:
                descriptions = json.load(f)
            print(f"Caché previa encontrada con {len(descriptions)} descripciones.")
        except Exception:
            descriptions = {}

    to_fetch = []
    title_to_id = {}
    for nat_id in range(1, 494):
        s_id = str(nat_id)
        if s_id not in descriptions or not descriptions[s_id] or force_all:
            raw_name = species_493.get(s_id, {}).get("name", "")
            title = CUSTOM_TITLES.get(nat_id, raw_name.capitalize())
            to_fetch.append(title)
            title_to_id[title.lower()] = nat_id

    if not to_fetch:
        print("Todas las descripciones ya están descargadas en caché.")
        return

    print(f"Se descargarán descripciones para {len(to_fetch)} especies en lotes de 40...")
    batch_size = 40
    for i in range(0, len(to_fetch), batch_size):
        batch = to_fetch[i:i+batch_size]
        print(f"Procesando lote {i//batch_size + 1}/{(len(to_fetch)-1)//batch_size + 1}...")
        try:
            res = fetch_wikidex_batch(batch)
            query_res = res.get("query", {})
            normalized = {item["to"]: item["from"] for item in query_res.get("normalized", [])}
            redirects = {item["to"]: item["from"] for item in query_res.get("redirects", [])}
            pages = query_res.get("pages", {})

            for page_id, page in pages.items():
                title = page.get("title", "")
                orig_title = redirects.get(title, title)
                orig_title = normalized.get(orig_title, orig_title)
                nat_id = title_to_id.get(orig_title.lower()) or title_to_id.get(title.lower())

                if not nat_id:
                    continue

                revisions = page.get("revisions", [])
                if not revisions:
                    continue

                slots = revisions[0].get("slots", {})
                main_slot = slots.get("main", {})
                content = main_slot.get("*", "")

                tpl = extract_pokedex_template(content)
                if not tpl:
                    continue

                fields = parse_template_fields(tpl)

                text = ""
                for pk in PRIMARY_KEYS:
                    if pk in fields:
                        text = resolve_field_text(fields, pk)
                        if text:
                            break

                if not text:
                    for fk in FALLBACK_KEYS:
                        if fk in fields:
                            text = resolve_field_text(fields, fk)
                            if text:
                                break

                if text:
                    descriptions[str(nat_id)] = text

        except Exception as e:
            print(f"Error procesando lote: {e}")

    with open(cache_output, "w", encoding="utf-8") as f:
        json.dump(descriptions, f, indent=2, ensure_ascii=False)

    print(f"Sincronización completada: {len(descriptions)} descripciones oficiales en {cache_output}")


if __name__ == "__main__":
    main()
