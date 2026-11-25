"""
Descarga y estructura las cadenas de evolución de la 5.ª Generación desde PokeAPI
y las almacena en caché en tracker/data/cache/gen5_evolutions.json.
Copia las cadenas previas de gen4_evolutions.json y actualiza:
- Cadenas de evolución de Teselia (494 a 649).
- Milotic (350): usando Escama Bella por intercambio.
- Leafeon / Glaceon: Bosque Azulejo / Monte Tuerca.
- Magnezone / Probopass: Cueva Electrorroca.
- Karrablast / Shelmet: intercambio mutuo.
"""
import json
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
CACHE_DIR = BASE_DIR / "tracker" / "data" / "cache"
SOURCE_FILE = CACHE_DIR / "gen4_evolutions.json"
CACHE_FILE = CACHE_DIR / "gen5_evolutions.json"

ITEM_NAME_ES = {
    'shiny-stone': 'Piedra Día',
    'dusk-stone': 'Piedra Noche',
    'dawn-stone': 'Piedra Alba',
    'oval-stone': 'Piedra Oval',
    'protector': 'Protector',
    'electirizer': 'Electrizador',
    'magmarizer': 'Magmatizador',
    'dubious-disc': 'Disco Extraño',
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
    'prism-scale': 'Escama Bella',
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
        detail = details[0]
        trigger = detail.get('trigger', {}).get('name', 'level-up')
        min_level = detail.get('min_level')
        item = detail.get('item')
        held_item = detail.get('held_item')
        time_of_day = detail.get('time_of_day')
        location = detail.get('location')
        known_move = detail.get('known_move')
        min_happiness = detail.get('min_happiness')
        gender = detail.get('gender')
        trade_species = detail.get('trade_species')

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
                if 'pinwheel' in loc_name or 'eterna' in loc_name:
                    condition_parts.append("al subir de nivel cerca de la Roca Musgo (Bosque Azulejo)")
                elif 'twist-mountain' in loc_name or 'snowpoint' in loc_name or 'route-217' in loc_name:
                    condition_parts.append("al subir de nivel cerca de la Roca Hielo (Monte Tuerca)")
                elif 'chargestone' in loc_name or 'coronet' in loc_name:
                    condition_parts.append("al subir de nivel en la Cueva Electrorroca (campo magnético)")
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
            if trade_species:
                tr_name = trade_species.get('name', '').capitalize()
                condition_parts.append(f"por intercambio con {tr_name}")
            elif held_item:
                item_slug = held_item['name']
                item_name = ITEM_NAME_ES.get(item_slug, item_slug.replace('-', ' ').capitalize())
                condition_parts.append(f"por intercambio equipado con {item_name}")
            else:
                condition_parts.append("por intercambio")

        # Ajustes específicos canónicos para Teselia
        if current_id == 589:  # Escavalier
            condition_parts = ["por intercambio con Shelmet"]
        elif current_id == 617:  # Accelgor
            condition_parts = ["por intercambio con Karrablast"]
        elif current_id == 350:  # Milotic
            trigger = "trade"
            condition_parts = ["por intercambio equipado con Escama Bella (o Belleza alta de 4.ª Gen)"]
            item_slug = 'prism-scale'
        elif current_id == 106:  # Hitmonlee
            condition_parts = ["Nivel 20 con Ataque > Defensa"]
        elif current_id == 107:  # Hitmonchan
            condition_parts = ["Nivel 20 con Defensa > Ataque"]
        elif current_id == 237:  # Hitmontop
            condition_parts = ["Nivel 20 con Ataque = Defensa"]
        elif current_id == 226:  # Mantine
            condition_parts = ["al subir de nivel con Remoraid en el equipo"]
        elif current_id in (266, 268):  # Silcoon / Cascoon
            condition_parts = ["Nivel 7 según valor de personalidad"]
        elif current_id == 292:  # Shedinja
            condition_parts = ["al evolucionar Nincada (Nv. 20) con hueco en el equipo y Poké Ball en la bolsa"]

        if parent_id == 29:
            parent_name = "Nidoran♀"
        elif parent_id == 32:
            parent_name = "Nidoran♂"
        elif parent_id == 439:
            parent_name = "Mime Jr."

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
    print("Compilando cadenas de evolución para la 5.ª Generación...")
    all_evos = {}

    if SOURCE_FILE.exists():
        with open(SOURCE_FILE, "r", encoding="utf-8") as f:
            all_evos = json.load(f)
        print(f"Cargadas {len(all_evos)} evoluciones previas desde {SOURCE_FILE.name}")

    # Cadenas únicas de Gen 5 (494..649) más Milotic (350)
    chain_urls = set()
    with ThreadPoolExecutor(max_workers=20) as ex:
        for url in ex.map(get_chain_url, list(range(494, 650)) + [350]):
            if url:
                chain_urls.add(url)

    print(f"Total cadenas únicas a procesar: {len(chain_urls)}")

    def process_chain(url):
        data = fetch_json(url)
        return parse_evolution_node(data['chain'])

    with ThreadPoolExecutor(max_workers=10) as ex:
        for res in ex.map(process_chain, chain_urls):
            all_evos.update(res)

    # Actualizaciones de ubicación Teselia para Leafeon, Glaceon, Magnezone, Probopass
    if '470' in all_evos:  # Leafeon
        all_evos['470']['condition'] = "al subir de nivel cerca de la Roca Musgo (Bosque Azulejo)"
        all_evos['470']['text'] = f"Evoluciona de Eevee ({all_evos['470']['condition']})"
    if '471' in all_evos:  # Glaceon
        all_evos['471']['condition'] = "al subir de nivel cerca de la Roca Hielo (Monte Tuerca)"
        all_evos['471']['text'] = f"Evoluciona de Eevee ({all_evos['471']['condition']})"
    if '462' in all_evos:  # Magnezone
        all_evos['462']['condition'] = "al subir de nivel en la Cueva Electrorroca (campo magnético)"
        all_evos['462']['text'] = f"Evoluciona de Magneton ({all_evos['462']['condition']})"
    if '476' in all_evos:  # Probopass
        all_evos['476']['condition'] = "al subir de nivel en la Cueva Electrorroca (campo magnético)"
        all_evos['476']['text'] = f"Evoluciona de Nosepass ({all_evos['476']['condition']})"

    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(all_evos, f, ensure_ascii=False, indent=2)

    print(f"[OK] Guardadas {len(all_evos)} evoluciones en {CACHE_FILE.name}")


if __name__ == "__main__":
    main()
