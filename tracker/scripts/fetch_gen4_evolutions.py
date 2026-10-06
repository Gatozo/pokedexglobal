"""
Descarga y estructura las cadenas de evolución de la 4.ª Generación desde PokeAPI
y las almacena en caché en tracker/data/cache/gen4_evolutions.json.
"""
import json
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
CACHE_DIR = BASE_DIR / "tracker" / "data" / "cache"
CACHE_FILE = CACHE_DIR / "gen4_evolutions.json"

ITEM_NAME_ES = {
    'shiny-stone': 'Piedra Día',
    'dusk-stone': 'Piedra Noche',
    'dawn-stone': 'Piedra Alba',
    'oval-stone': 'Piedra Oval',
    'protector': 'Protector',
    'electirizer': 'Electirizador',
    'magmarizer': 'Magmatizador',
    'dubious-disc': 'Discoxtraño',
    'reaper-cloth': 'Tela Terrible',
    'razor-claw': 'Garra Afilada',
    'razor-fang': 'Colmillo Agudo',
    'deep-sea-tooth': 'Diente Marino',
    'deep-sea-scale': 'Escama Marina',
    'dragon-scale': 'Escama Dragón',
    'kings-rock': 'Roca del Rey',
    'metal-coat': 'Revestimiento Metálico',
    'up-grade': 'Mejora',
    'fire-stone': 'Piedra Fuego',
    'water-stone': 'Piedra Agua',
    'thunder-stone': 'Piedra Trueno',
    'leaf-stone': 'Piedra Hoja',
    'moon-stone': 'Piedra Lunar',
    'sun-stone': 'Piedra Solar',
}

MOVE_NAME_ES = {
    'ancient-power': 'Poder Pasado',
    'double-hit': 'Doble Golpe',
    'rollout': 'Desenrollar',
    'mimic': 'Mimético',
}


def fetch_json(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 PokedexGlobal/1.0'})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode('utf-8'))


def parse_evolution_node(node, parent_id=None, parent_name=None, evo_dict=None):
    if evo_dict is None:
        evo_dict = {}

    species_url = node['species']['url']
    current_id = int(species_url.strip('/').split('/')[-1])
    current_name = node['species']['name'].capitalize()

    details = node.get('evolution_details', [])
    if details and parent_id is not None:
        # Use first detail applicable
        detail = details[0]
        trigger = detail.get('trigger', {}).get('name', 'level-up')
        min_level = detail.get('min_level')
        item = detail.get('item')
        held_item = detail.get('held_item')
        time_of_day = detail.get('time_of_day')
        location = detail.get('location')
        known_move = detail.get('known_move')
        min_happiness = detail.get('min_happiness')
        gender = detail.get('gender')  # 1 = female, 2 = male

        condition_parts = []
        item_slug = None

        if trigger == 'level-up':
            if min_level:
                condition_parts.append(f"Nivel {min_level}")
            elif item:
                item_name = ITEM_NAME_ES.get(item['name'], item['name'].replace('-', ' ').capitalize())
                item_slug = item['name']
                condition_parts.append(f"usando {item_name}")
            elif held_item:
                item_name = ITEM_NAME_ES.get(held_item['name'], held_item['name'].replace('-', ' ').capitalize())
                item_slug = held_item['name']
                tod = f" por la {time_of_day}" if time_of_day else ""
                condition_parts.append(f"equipado con {item_name} al subir de nivel{tod}")
            elif location:
                loc_name = location['name']
                if 'eterna-forest' in loc_name:
                    condition_parts.append("al subir de nivel cerca de la Roca Musgo (Bosque Vetusto)")
                elif 'route-217' in loc_name or 'snowpoint' in loc_name:
                    condition_parts.append("al subir de nivel cerca de la Roca Hielo (Ruta 217)")
                elif 'coronet' in loc_name:
                    condition_parts.append("al subir de nivel en el Monte Corona (campo magnético)")
                else:
                    condition_parts.append(f"al subir de nivel en {loc_name}")
            elif known_move:
                move_es = MOVE_NAME_ES.get(known_move['name'], known_move['name'].replace('-', ' ').capitalize())
                condition_parts.append(f"al subir de nivel conociendo {move_es}")
            elif min_happiness:
                tod = " durante el día" if time_of_day == 'day' else (" durante la noche" if time_of_day == 'night' else "")
                condition_parts.append(f"por amistad{tod}")
            elif time_of_day:
                tod = "durante el día" if time_of_day == 'day' else ("durante la noche" if time_of_day == 'night' else time_of_day)
                condition_parts.append(f"al subir de nivel {tod}")

            if gender == 1:
                condition_parts.append("(hembra)")
            elif gender == 2:
                condition_parts.append("(macho)")

        elif trigger == 'use-item':
            if item:
                item_slug = item['name']
                item_name = ITEM_NAME_ES.get(item_slug, item_slug.replace('-', ' ').capitalize())
                gen_text = " (macho)" if gender == 2 else (" (hembra)" if gender == 1 else "")
                condition_parts.append(f"usando {item_name}{gen_text}")

        elif trigger == 'trade':
            if held_item:
                item_slug = held_item['name']
                item_name = ITEM_NAME_ES.get(item_slug, item_slug.replace('-', ' ').capitalize())
                condition_parts.append(f"por intercambio equipado con {item_name}")
            else:
                condition_parts.append("por intercambio")

        cond_text = ", ".join(condition_parts) if condition_parts else "por condición especial"
        evo_dict[str(current_id)] = {
            'from_id': parent_id,
            'from_name': parent_name,
            'to_id': current_id,
            'to_name': current_name,
            'trigger': trigger,
            'condition': cond_text,
            'text': f"Evoluciona de {parent_name} ({cond_text})",
            'item_slug': item_slug
        }

    for evolves_to in node.get('evolves_to', []):
        parse_evolution_node(evolves_to, current_id, current_name, evo_dict)

    return evo_dict


def get_chain_url(i):
    sp_url = f"https://pokeapi.co/api/v2/pokemon-species/{i}/"
    try:
        data = fetch_json(sp_url)
        return data.get('evolution_chain', {}).get('url')
    except Exception as e:
        print(f"Error {i}: {e}")
        return None


def main():
    print("Extrayendo cadenas de evolución para las especies de 4.ª Generación...")
    chain_urls = set()
    with ThreadPoolExecutor(max_workers=20) as ex:
        for url in ex.map(get_chain_url, range(387, 494)):
            if url:
                chain_urls.add(url)

    print(f"Total cadenas únicas: {len(chain_urls)}")
    all_evos = {}

    def process_chain(url):
        data = fetch_json(url)
        return parse_evolution_node(data['chain'])

    with ThreadPoolExecutor(max_workers=10) as ex:
        for res in ex.map(process_chain, chain_urls):
            all_evos.update(res)

    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(all_evos, f, ensure_ascii=False, indent=2)

    print(f"[OK] Guardadas {len(all_evos)} evoluciones en {CACHE_FILE}")


if __name__ == "__main__":
    main()
