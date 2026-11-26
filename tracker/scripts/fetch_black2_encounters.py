"""
Descarga y almacena en caché:
1. El orden canónico de la Pokédex Regional expandida de Teselia 2 (301 especies, PokeAPI: updated-unova)
   -> tracker/data/cache/unova_updated_pokedex_301.json
2. Los encuentros oficiales de Pokémon Negro 2 (version == 'black-2') para las 649 especies
   -> tracker/data/cache/encounters_black-2.json
"""
import json
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
CACHE_DIR = BASE_DIR / "tracker" / "data" / "cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)
DEX_CACHE_FILE = CACHE_DIR / "unova_updated_pokedex_301.json"
ENCOUNTERS_CACHE_FILE = CACHE_DIR / "encounters_black-2.json"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) PokedexGlobal/1.0"


def fetch_updated_unova_dex():
    if DEX_CACHE_FILE.exists() and DEX_CACHE_FILE.stat().st_size > 0:
        with open(DEX_CACHE_FILE, "r", encoding="utf-8") as f:
            existing = json.load(f)
        if len(existing) == 301:
            print(f"[SKIP] {DEX_CACHE_FILE.name} ya existe con {len(existing)} entradas.")
            return

    print("Descargando Pokédex Regional de Teselia 2 (301 especies, updated-unova) desde PokeAPI...")
    url = "https://pokeapi.co/api/v2/pokedex/updated-unova/"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=20) as resp:
        data = json.loads(resp.read().decode("utf-8"))

    unova_301 = {}
    for entry in data.get("pokemon_entries", []):
        entry_num = str(entry["entry_number"])
        species_url = entry["pokemon_species"]["url"]
        nat_id = int(species_url.strip("/").split("/")[-1])
        unova_301[entry_num] = nat_id

    with open(DEX_CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(unova_301, f, indent=2, ensure_ascii=False)
    print(f"[OK] {len(unova_301)} entradas guardadas en {DEX_CACHE_FILE.name}")


def fetch_pokemon_encounters(nat_id: int):
    url = f"https://pokeapi.co/api/v2/pokemon/{nat_id}/encounters"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})

    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode("utf-8"))

            encounters = []
            for item in data:
                area_name = item.get("location_area", {}).get("name", "")
                for vd in item.get("version_details", []):
                    if vd.get("version", {}).get("name") == "black-2":
                        for enc in vd.get("encounter_details", []):
                            method = enc.get("method", {}).get("name", "walk")
                            conds = [c.get("name") for c in enc.get("condition_values", [])]
                            encounters.append({
                                "area_raw": area_name,
                                "method_raw": method,
                                "conditions": conds,
                            })
            return nat_id, encounters
        except Exception as e:
            if attempt == 2:
                print(f"Error descargando encuentros para #{nat_id}: {e}")
                return nat_id, []
            time.sleep(1)


def main():
    fetch_updated_unova_dex()

    print("Descargando encuentros oficiales de Pokémon Negro 2 desde PokeAPI (649 especies)...")
    results = {}
    with ThreadPoolExecutor(max_workers=16) as executor:
        futures = {executor.submit(fetch_pokemon_encounters, nat_id): nat_id for nat_id in range(1, 650)}
        for future in as_completed(futures):
            nat_id, encs = future.result()
            results[str(nat_id)] = encs

    sorted_results = {str(i): results.get(str(i), []) for i in range(1, 650)}

    with open(ENCOUNTERS_CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(sorted_results, f, ensure_ascii=False, indent=2)
    with_encs = sum(1 for v in sorted_results.values() if v)
    print(f"[OK] Encuentros de Pokémon Negro 2 guardados en {ENCOUNTERS_CACHE_FILE.name} ({with_encs}/649 especies con encuentros)")


if __name__ == "__main__":
    main()
