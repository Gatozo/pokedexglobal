"""
Script para compilar el catálogo de especies de 5.ª Generación (1 a 649).
Copia las 493 especies preexistentes desde pokemon_493_species.json y descarga
desde PokeAPI las 156 nuevas especies de Teselia (494 Victini a 649 Genesect)
con sus datos y nombres oficiales en español.
Genera: tracker/data/cache/pokemon_649_species.json
"""
import json
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import time

BASE_DIR = Path(__file__).resolve().parent.parent.parent
CACHE_DIR = BASE_DIR / "tracker" / "data" / "cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

SOURCE_493_FILE = CACHE_DIR / "pokemon_493_species.json"
TARGET_649_FILE = CACHE_DIR / "pokemon_649_species.json"


def fetch_species_data(nat_id: int):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) PokedexGlobal/1.0'}
    
    # 1. Obtener datos de /pokemon/{id}
    pk_url = f"https://pokeapi.co/api/v2/pokemon/{nat_id}"
    req_pk = urllib.request.Request(pk_url, headers=headers)
    pk_data = {}
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req_pk, timeout=15) as resp:
                pk_data = json.loads(resp.read().decode('utf-8'))
            break
        except Exception as e:
            if attempt == 2:
                print(f"Error descargando pokemon #{nat_id}: {e}")
                return nat_id, None
            time.sleep(1)

    # 2. Obtener datos de /pokemon-species/{id}
    sp_url = f"https://pokeapi.co/api/v2/pokemon-species/{nat_id}"
    req_sp = urllib.request.Request(sp_url, headers=headers)
    sp_data = {}
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req_sp, timeout=15) as resp:
                sp_data = json.loads(resp.read().decode('utf-8'))
            break
        except Exception as e:
            if attempt == 2:
                print(f"Error descargando species #{nat_id}: {e}")
                return nat_id, None
            time.sleep(1)

    # Extraer nombre en español
    display_name = pk_data.get('name', '').capitalize()
    for n in sp_data.get('names', []):
        if n.get('language', {}).get('name') == 'es':
            display_name = n.get('name')
            break

    # Extraer categoría en español
    category = "Pokémon"
    for g in sp_data.get('genera', []):
        if g.get('language', {}).get('name') == 'es':
            category = g.get('genus', 'Pokémon')
            break

    # Extraer tipos
    types = [t.get('type', {}).get('name') for t in sorted(pk_data.get('types', []), key=lambda x: x.get('slot', 1))]
    primary_type = types[0] if len(types) > 0 else 'normal'
    secondary_type = types[1] if len(types) > 1 else None

    # Extraer estadísticas
    stats = {}
    stat_total = 0
    stat_mapping = {
        'hp': 'hp',
        'attack': 'attack',
        'defense': 'defense',
        'special-attack': 'special_attack',
        'special-defense': 'special_defense',
        'speed': 'speed'
    }
    for s in pk_data.get('stats', []):
        raw_name = s.get('stat', {}).get('name')
        if raw_name in stat_mapping:
            val = s.get('base_stat', 0)
            stats[stat_mapping[raw_name]] = val
            stat_total += val
    stats['total'] = stat_total

    egg_groups = [eg.get('name') for eg in sp_data.get('egg_groups', [])]

    entry = {
        'national_number': nat_id,
        'name': pk_data.get('name', '').lower(),
        'display_name': display_name,
        'category': category,
        'height': pk_data.get('height', 0),
        'weight': pk_data.get('weight', 0),
        'primary_type': primary_type,
        'secondary_type': secondary_type,
        'stats': stats,
        'habitat': sp_data.get('habitat', {}).get('name') if sp_data.get('habitat') else 'unknown',
        'egg_groups': egg_groups,
        'gender_rate': sp_data.get('gender_rate', -1),
        'growth_rate': sp_data.get('growth_rate', {}).get('name', 'medium-fast'),
        'capture_rate': sp_data.get('capture_rate', 45),
        'base_happiness': sp_data.get('base_happiness', 70),
        'is_legendary': sp_data.get('is_legendary', False),
        'is_mythical': sp_data.get('is_mythical', False),
    }
    return nat_id, entry


def main():
    print("Iniciando compilación de datos de especies 1 a 649...")
    all_species = {}

    if SOURCE_493_FILE.exists():
        with open(SOURCE_493_FILE, 'r', encoding='utf-8') as f:
            all_species = json.load(f)
        print(f"Cargadas {len(all_species)} especies previas desde {SOURCE_493_FILE.name}")

    missing_ids = [i for i in range(494, 650) if str(i) not in all_species]
    if missing_ids:
        print(f"Descargando {len(missing_ids)} especies de Teselia (494..649) desde PokeAPI...")
        with ThreadPoolExecutor(max_workers=16) as executor:
            futures = {executor.submit(fetch_species_data, nat_id): nat_id for nat_id in missing_ids}
            for future in as_completed(futures):
                nat_id, entry = future.result()
                if entry:
                    all_species[str(nat_id)] = entry
                    print(f"  [+] #{nat_id:03d} {entry['display_name']} ({entry['primary_type']}/{entry['secondary_type'] or '-'})")

    # Ordenar numéricamente de 1 a 649
    sorted_species = {str(i): all_species[str(i)] for i in range(1, 650) if str(i) in all_species}

    with open(TARGET_649_FILE, 'w', encoding='utf-8') as f:
        json.dump(sorted_species, f, ensure_ascii=False, indent=2)

    print(f"\n[OK] Guardadas {len(sorted_species)} especies de Pokémon en {TARGET_649_FILE.name}")


if __name__ == "__main__":
    main()
