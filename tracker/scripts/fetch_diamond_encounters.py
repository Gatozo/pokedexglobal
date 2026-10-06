"""
Descarga y almacena en caché los encuentros de Pokémon Diamante desde PokeAPI
para las 493 especies de la 4.ª Generación.
"""
import json
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import time

BASE_DIR = Path(__file__).resolve().parent.parent.parent
CACHE_DIR = BASE_DIR / "tracker" / "data" / "cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)
CACHE_FILE = CACHE_DIR / "encounters_diamond.json"


def fetch_pokemon_encounters(nat_id: int):
    url = f"https://pokeapi.co/api/v2/pokemon/{nat_id}/encounters"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) PokedexGlobal/1.0'}
    req = urllib.request.Request(url, headers=headers)
    
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode('utf-8'))
            
            encounters = []
            for item in data:
                area_name = item.get('location_area', {}).get('name', '')
                for vd in item.get('version_details', []):
                    if vd.get('version', {}).get('name') == 'diamond':
                        for enc in vd.get('encounter_details', []):
                            method = enc.get('method', {}).get('name', 'walk')
                            conds = [c.get('name') for c in enc.get('condition_values', [])]
                            encounters.append({
                                'area_raw': area_name,
                                'method_raw': method,
                                'conditions': conds
                            })
            return nat_id, encounters
        except Exception as e:
            if attempt == 2:
                print(f"Error descargando encuentros para #{nat_id}: {e}")
                return nat_id, []
            time.sleep(1)


def main():
    print("Descargando encuentros oficiales de Pokémon Diamante desde PokeAPI (493 especies)...")
    results = {}
    with ThreadPoolExecutor(max_workers=14) as executor:
        futures = {executor.submit(fetch_pokemon_encounters, nat_id): nat_id for nat_id in range(1, 494)}
        for future in as_completed(futures):
            nat_id, encs = future.result()
            results[str(nat_id)] = encs

    sorted_results = {str(i): results.get(str(i), []) for i in range(1, 494)}

    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(sorted_results, f, ensure_ascii=False, indent=2)

    total_with_enc = sum(1 for enc in sorted_results.values() if enc)
    print(f"\n[OK] Guardados encuentros de 493 Pokémon en {CACHE_FILE.name}")
    print(f"Total especies con encuentros directos en Diamante: {total_with_enc}")


if __name__ == "__main__":
    main()
