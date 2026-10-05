"""
Descarga y almacena en caché los encuentros de Pokémon Verde Hoja desde PokeAPI
para las 386 especies de la 3.ª Generación.
"""
import json
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import time

BASE_DIR = Path(__file__).resolve().parent.parent.parent
CACHE_DIR = BASE_DIR / "tracker" / "data" / "cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)
CACHE_FILE = CACHE_DIR / "encounters_leafgreen.json"


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
                    if vd.get('version', {}).get('name') == 'leafgreen':
                        for enc in vd.get('encounter_details', []):
                            method = enc.get('method', {}).get('name', 'walk')
                            encounters.append({
                                'area_raw': area_name,
                                'method_raw': method
                            })
            return nat_id, encounters
        except Exception as e:
            if attempt == 2:
                print(f"Error descargando encuentros para #{nat_id}: {e}")
                return nat_id, []
            time.sleep(1)


def main():
    print("Descargando encuentros oficiales de Pokémon Verde Hoja desde PokeAPI (386 especies)...")
    results = {}
    with ThreadPoolExecutor(max_workers=12) as executor:
        futures = {executor.submit(fetch_pokemon_encounters, nat_id): nat_id for nat_id in range(1, 387)}
        for future in as_completed(futures):
            nat_id, encs = future.result()
            results[str(nat_id)] = encs

    # Ordenar por id numérico
    sorted_results = {str(i): results.get(str(i), []) for i in range(1, 387)}

    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(sorted_results, f, ensure_ascii=False, indent=2)

    total_with_enc = sum(1 for enc in sorted_results.values() if enc)
    print(f"\n[OK] Guardados encuentros de 386 Pokémon en {CACHE_FILE}")
    print(f"Total especies con encuentros directos en Verde Hoja: {total_with_enc}")


if __name__ == "__main__":
    main()
