"""
Script para compilar los catálogos oficiales de Pokémon Rubí (Gen 3):
1. ruby.json (Pokédex Regional de Hoenn: 202 Pokémon, numeración 1 a 202)
2. ruby_national.json (Pokédex Nacional de Rubí: 386 Pokémon, numeración 1 a 386)

Descarga o carga de caché:
- Textos de Pokédex oficiales en español desde WikiDex API.
- Encuentros y rutas en español oficial para Hoenn.
- Métodos especiales de obtención y transferencias externas (FRLG, Colosseum, XD, Esmeralda).
"""
import os
import sys
import json
import re
import urllib.request
import urllib.parse
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR))
CACHE_DIR = BASE_DIR / "tracker" / "data" / "cache"
CATALOGS_DIR = BASE_DIR / "tracker" / "data" / "catalogs"
CACHE_DIR.mkdir(parents=True, exist_ok=True)
CATALOGS_DIR.mkdir(parents=True, exist_ok=True)

# Mapeo oficial de tipos en español
TYPE_NAMES_ES = {
    'normal': 'Normal', 'fire': 'Fuego', 'water': 'Agua', 'grass': 'Planta',
    'electric': 'Eléctrico', 'ice': 'Hielo', 'fighting': 'Lucha', 'poison': 'Veneno',
    'ground': 'Tierra', 'flying': 'Volador', 'psychic': 'Psíquico', 'bug': 'Bicho',
    'rock': 'Roca', 'ghost': 'Fantasma', 'dragon': 'Dragón', 'steel': 'Acero',
    'dark': 'Siniestro', 'fairy': 'Hada'
}

# Traducción oficial de áreas de Hoenn
HOENN_AREAS_ES = {
    # Rutas terrestres y marítimas
    'hoenn-route-101-area': 'Ruta 101',
    'hoenn-route-102-area': 'Ruta 102',
    'hoenn-route-103-area': 'Ruta 103',
    'hoenn-route-104-area': 'Ruta 104',
    'hoenn-route-105-area': 'Ruta 105',
    'hoenn-route-106-area': 'Ruta 106',
    'hoenn-route-107-area': 'Ruta 107',
    'hoenn-route-108-area': 'Ruta 108',
    'hoenn-route-109-area': 'Ruta 109',
    'hoenn-route-110-area': 'Ruta 110',
    'hoenn-route-111-area': 'Ruta 111 (Desierto)',
    'hoenn-route-112-area': 'Ruta 112',
    'hoenn-route-113-area': 'Ruta 113 (Ceniza)',
    'hoenn-route-114-area': 'Ruta 114',
    'hoenn-route-115-area': 'Ruta 115',
    'hoenn-route-116-area': 'Ruta 116',
    'hoenn-route-117-area': 'Ruta 117',
    'hoenn-route-118-area': 'Ruta 118',
    'hoenn-route-119-area': 'Ruta 119',
    'hoenn-route-119-weather-institute': 'Ruta 119 (Instituto Meteorológico)',
    'hoenn-route-120-area': 'Ruta 120',
    'hoenn-route-121-area': 'Ruta 121',
    'hoenn-route-122-area': 'Ruta 122',
    'hoenn-route-123-area': 'Ruta 123',
    'hoenn-route-124-area': 'Ruta 124 (Superficie)',
    'hoenn-route-124-underwater': 'Ruta 124 (Buceo / Fondo marino)',
    'hoenn-route-125-area': 'Ruta 125',
    'hoenn-route-126-area': 'Ruta 126 (Superficie)',
    'hoenn-route-126-underwater': 'Ruta 126 (Buceo / Fondo marino)',
    'hoenn-route-127-area': 'Ruta 127',
    'hoenn-route-128-area': 'Ruta 128',
    'hoenn-route-129-area': 'Ruta 129',
    'hoenn-route-130-area': 'Ruta 130',
    'hoenn-route-131-area': 'Ruta 131',
    'hoenn-route-132-area': 'Ruta 132 (Corrientes)',
    'hoenn-route-133-area': 'Ruta 133 (Corrientes)',
    'hoenn-route-134-area': 'Ruta 134 (Cámara Sellada)',
    'roaming-hoenn-area': 'Rutas de Hoenn (Errante)',

    # Ciudades y Pueblos
    'petalburg-city-area': 'Ciudad Petalia (Pesca / Surf)',
    'slateport-city-area': 'Ciudad Portual (Pesca / Surf)',
    'lilycove-city-area': 'Ciudad Calagua (Pesca / Surf)',
    'mossdeep-city-area': 'Ciudad Algaria (Pesca / Surf)',
    'mossdeep-city-stevens-house': 'Ciudad Algaria (Casa de Máximo)',
    'sootopolis-city-area': 'Ciudad Arrecípolis (Pesca / Surf)',
    'pacifidlog-town-area': 'Pueblo Oromar (Pesca / Surf)',
    'dewford-town-area': 'Pueblo Azuliza (Pesca / Surf)',
    'ever-grande-city-area': 'Ciudad Colosalia (Pesca / Surf)',
    'lavaridge-town-area': 'Pueblo Lavacalda (Aguas termales)',
    'rustboro-city-area': 'Ciudad Férrica',
    'fortree-city-area': 'Ciudad Arborada',
    'hoenn-pokecenter-area': 'Centro Pokémon (Distribución / Evento)',

    # Mazmorras y Cuevas
    'petalburg-woods-area': 'Bosque Petalia',
    'rusturf-tunnel-area': 'Túnel Férrfundido',
    'granite-cave-1f': 'Cueva Granito (P1)',
    'granite-cave-1fsmall-room': 'Cueva Granito (P1 Sala Interior)',
    'granite-cave-b1f': 'Cueva Granito (Sótano 1)',
    'granite-cave-b2f': 'Cueva Granito (Sótano 2)',
    'fiery-path-area': 'Senda Ígnea',
    'jagged-pass-area': 'Desfiladero',
    'mt-chimney-area': 'Monte Cenizo',
    'desert-ruins-area': 'Ruinas del Desierto (Ruta 111)',
    'island-cave-area': 'Cueva Insular (Ruta 105)',
    'ancient-tomb-area': 'Tumba Antigua (Ruta 120)',

    # Cascada Meteoro
    'meteor-falls-area': 'Cascada Meteoro (Entrada)',
    'meteor-falls-1f-1r': 'Cascada Meteoro (Entrada)',
    'meteor-falls-1f-2r': 'Cascada Meteoro (Interior)',
    'meteor-falls-back': 'Cascada Meteoro (Interior)',
    'meteor-falls-b1f': 'Cascada Meteoro (Sótano 1)',
    'meteor-falls-b1f-1r': 'Cascada Meteoro (Profundidades)',
    'meteor-falls-b1f-2r': 'Cascada Meteoro (Sala de Bagon)',
    'meteor-falls-backsmall-room': 'Cascada Meteoro (Sala de Bagon)',

    # Monte Pírico
    'mt-pyre-1f': 'Monte Pírico (Interior P1)',
    'mt-pyre-2f': 'Monte Pírico (Interior P2)',
    'mt-pyre-3f': 'Monte Pírico (Interior P3)',
    'mt-pyre-4f': 'Monte Pírico (Interior P4)',
    'mt-pyre-5f': 'Monte Pírico (Interior P5)',
    'mt-pyre-6f': 'Monte Pírico (Interior P6)',
    'mt-pyre-outside': 'Monte Pírico (Exterior)',
    'mt-pyre-exterior': 'Monte Pírico (Exterior)',
    'mt-pyre-summit': 'Monte Pírico (Cima)',

    # Cueva Cardumen
    'shoal-cave-high-tide': 'Cueva Cardumen (Marea Alta)',
    'shoal-cave-low-tide': 'Cueva Cardumen (Marea Baja)',
    'shoal-cave-low-tide-entrance-room': 'Cueva Cardumen (Marea Baja Entrada)',
    'shoal-cave-low-tide-ice-room': 'Cueva Cardumen (Sala Hielo)',
    'shoal-cave-high-tide-entrance': 'Cueva Cardumen (Marea Alta Entrada)',
    'shoal-cave-b1f': 'Cueva Cardumen (Sótano 1)',
    'shoal-cave-b2f': 'Cueva Cardumen (Sótano 2)',
    'shoal-cave-b3f': 'Cueva Cardumen (Sala Hielo)',

    # Cueva del Origen
    'cave-of-origin-entrance': 'Cueva del Origen (Entrada)',
    'cave-of-origin-1f': 'Cueva del Origen (P1)',
    'cave-of-origin-b1f': 'Cueva del Origen (S1)',
    'cave-of-origin-b2f': 'Cueva del Origen (S2)',
    'cave-of-origin-b3f': 'Cueva del Origen (S3)',
    'cave-of-origin-b4f': 'Cueva del Origen (Groudon)',

    # Caverna Abisal
    'seafloor-cavern-area': 'Caverna Abisal',
    'seafloor-cavern-entrance': 'Caverna Abisal (Entrada)',
    'seafloor-cavern-room-1': 'Caverna Abisal (Sala 1)',
    'seafloor-cavern-room-2': 'Caverna Abisal (Sala 2)',
    'seafloor-cavern-room-3': 'Caverna Abisal (Sala 3)',
    'seafloor-cavern-room-4': 'Caverna Abisal (Sala 4)',
    'seafloor-cavern-room-5': 'Caverna Abisal (Sala 5)',
    'seafloor-cavern-room-6': 'Caverna Abisal (Sala 6)',
    'seafloor-cavern-room-7': 'Caverna Abisal (Sala 7)',
    'seafloor-cavern-room-8': 'Caverna Abisal (Sala 8)',
    'seafloor-cavern-room-9': 'Caverna Abisal (Fondo)',

    # Pilar Celeste
    'sky-pillar-1f': 'Pilar Celeste (P1)',
    'sky-pillar-2f': 'Pilar Celeste (P2)',
    'sky-pillar-3f': 'Pilar Celeste (P3)',
    'sky-pillar-4f': 'Pilar Celeste (P4)',
    'sky-pillar-5f': 'Pilar Celeste (P5)',
    'sky-pillar-top': 'Pilar Celeste (Cima Rayquaza)',
    'sky-pillar-apex': 'Pilar Celeste (Cima Rayquaza)',

    # Calle Victoria
    'victory-road-1f': 'Calle Victoria (P1)',
    'victory-road-b1f': 'Calle Victoria (S1)',
    'victory-road-b2f': 'Calle Victoria (S2)',
    'hoenn-victory-road-1f': 'Calle Victoria (P1)',
    'hoenn-victory-road-b1f': 'Calle Victoria (S1)',
    'hoenn-victory-road-b2f': 'Calle Victoria (S2)',

    # Zona Safari
    'hoenn-safari-zone-area': 'Zona Safari (Hoenn)',
    'hoenn-safari-zone-northeast': 'Zona Safari (Noreste - Bici Acrobática)',
    'hoenn-safari-zone-neacro-bike-area': 'Zona Safari (Noreste - Bici Acrobática)',
    'hoenn-safari-zone-north': 'Zona Safari (Norte)',
    'hoenn-safari-zone-northwest': 'Zona Safari (Noroeste - Bici Carrera)',
    'hoenn-safari-zone-nwmach-bike-area': 'Zona Safari (Noroeste - Bici Carrera)',
    'hoenn-safari-zone-southeast': 'Zona Safari (Sureste)',
    'hoenn-safari-zone-se': 'Zona Safari (Sureste)',
    'hoenn-safari-zone-south': 'Zona Safari (Sur)',
    'hoenn-safari-zone-southwest': 'Zona Safari (Suroeste)',
    'hoenn-safari-zone-sw': 'Zona Safari (Suroeste)',

    # Naufragio y Malvalona
    'abandoned-ship-area': 'Naufragio (Interior / Surf)',
    'abandoned-ship-captain-office': 'Naufragio (Camarote del Capitán)',
    'abandoned-ship-corridors-b1f': 'Naufragio (Sótano)',
    'abandoned-ship-hidden-rooms': 'Naufragio (Salas Sumergidas)',
    'new-mauville-area': 'Malvalona Nueva (Interior)',
    'new-mauville-entrance': 'Malvalona Nueva (Entrada)',
    'new-mauville-inside': 'Malvalona Nueva (Interior)',

    # Eventos e Islas Especiales
    'mirage-island-area': 'Isla Espejismo (Ruta 130)',
    'southern-island-area': 'Isla del Sur (Evento Ticket Eón)',
    'team-magma-hideout-area': 'Guarida Magma (Ciudad Calagua)'
}

# Traducción de métodos de encuentro
METHOD_NAMES_ES = {
    'walk': 'Hierba alta',
    'surf': 'Surfeando (Agua)',
    'old-rod': 'Caña Vieja',
    'good-rod': 'Caña Buena',
    'super-rod': 'Supercaña',
    'rock-smash': 'Golpe Roca',
    'headbutt': 'Golpe Cabeza',
    'cave': 'Cueva',
    'gift': 'Regalo',
    'trade': 'Intercambio',
    'underwater': 'Buceando',
    'seaweed': 'Hierba submarina (Algas)',
    'devon-scope': 'Detector Devon',
    'feebas-tile-fishing': 'Pesca en casilla especial de Feebas',
    'gift-egg': 'Huevo de regalo',
    'npc-trade': 'Intercambio con NPC',
    'roaming-grass': 'Legendario errante (Hierba)',
    'roaming-water': 'Legendario errante (Agua)',
    'static': 'Encuentro estático',
    'pokemon-channel-pal': 'Pokémon Channel (Europa / Australia)',
    'colosseum-bonus-disc-us': 'Disco bonus Colosseum (EE.UU.)',
    'colosseum-bonus-disc-jpn': 'Disco bonus Colosseum (Japón)'
}

# Nombres en español para objetos evolutivos y condiciones
EVO_ITEMS_ES = {
    'deep-sea-tooth': 'Diente Marino',
    'deep-sea-scale': 'Escama Marina',
    'dragon-scale': 'Escama Dragón',
    'metal-coat': 'Revestimiento Metálico',
    'kings-rock': 'Roca del Rey',
    'upgrade': 'Mejora',
    'sun-stone': 'Piedra Solar',
    'moon-stone': 'Piedra Lunar',
    'fire-stone': 'Piedra Fuego',
    'thunder-stone': 'Piedra Trueno',
    'water-stone': 'Piedra Agua',
    'leaf-stone': 'Piedra Hoja',
    'soothe-bell': 'Campana Alivio',
    'mach-bike': 'Bici Carrera',
    'acro-bike': 'Bici Acrobática'
}


def clean_wikitext_entry(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r"\{\{NombreHaEs\|([^|]+)(?:\|([^}]+))?\}\}", lambda m: m.group(2) or m.group(1), text)
    text = re.sub(r"\{\{n\|([^|]+)(?:\|([^}]+))?\}\}", lambda m: m.group(2) or m.group(1), text)
    text = re.sub(r"\{\{[^}]+\}\}", "", text)
    text = re.sub(r"\[\[(?:[^|\]]*\|)?([^\]]+)\]\]", r"\1", text)
    text = re.sub(r"<ref[^>]*>.*?</ref>", "", text, flags=re.DOTALL)
    text = re.sub(r"<[^>]+>", "", text)
    text = text.replace("\n", " ").replace("\r", " ")
    return " ".join(text.split()).strip()


def fetch_wikidex_ruby_descriptions(species_data):
    cache_file = CACHE_DIR / "wikidex_ruby_descriptions.json"
    if cache_file.exists():
        with open(cache_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            if len(data) >= 380:
                print(f"[CACHE] Descripciones de WikiDex cargadas desde caché ({len(data)} entradas).")
                return data

    print("Extrayendo descripciones oficiales de Pokémon Rubí desde WikiDex API (por lotes)...")
    descriptions = {}
    if cache_file.exists():
        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                descriptions = json.load(f)
        except Exception:
            descriptions = {}

    custom_titles = {
        29: "Nidoran hembra", 32: "Nidoran macho", 83: "Farfetch'd", 122: "Mr. Mime",
        233: "Porygon2", 250: "Ho-Oh"
    }

    # Mapa de título normalizado a nat_id
    title_to_nat = {}
    items_to_fetch = []
    for k, v in species_data.items():
        nat_id = int(k)
        if str(nat_id) in descriptions:
            continue
        name = v['name']
        title = custom_titles.get(nat_id, name.capitalize())
        title_to_nat[title.lower()] = str(nat_id)
        items_to_fetch.append((nat_id, title))

    # Procesar en lotes de 25 títulos
    BATCH_SIZE = 25
    for idx in range(0, len(items_to_fetch), BATCH_SIZE):
        batch = items_to_fetch[idx:idx + BATCH_SIZE]
        titles_str = "|".join([b[1] for b in batch])
        url = f"https://www.wikidex.net/api.php?action=query&prop=revisions&titles={urllib.parse.quote(titles_str)}&rvprop=content&format=json"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode('utf-8'))
            pages = data.get('query', {}).get('pages', {})
            for page_id, page in pages.items():
                title = page.get('title', '')
                nat_id_str = title_to_nat.get(title.lower())
                if not nat_id_str:
                    # Intento de búsqueda inversa
                    for b_nat, b_title in batch:
                        if b_title.lower() == title.lower() or b_title.lower() in title.lower():
                            nat_id_str = str(b_nat)
                            break
                if not nat_id_str:
                    continue

                content = page.get('revisions', [{}])[0].get('*', '') if page.get('revisions') else ''
                # Buscar en plantilla Pokédex para rubí, zafiro, esmeralda, etc.
                for v in ['rubí', 'rubi', 'zafiro', 'esmeralda', 'rubí omega', 'zafiro alfa', 'rojo fuego', 'verde hoja']:
                    pattern = r'\|\s*' + re.escape(v) + r'\s*=\s*(.*?)(?=\r?\n\s*\||\r?\n\s*\}\}|\r|\n|$)'
                    m = re.search(pattern, content, re.IGNORECASE)
                    if m:
                        raw_val = m.group(1).strip()
                        if raw_val.lower() in ['rubí', 'rubi', 'zafiro', 'esmeralda', 'rojo fuego', 'verde hoja', 'oro', 'plata', 'cristal', 'oro heartgold', 'plata soulsilver', 'rubí omega', 'zafiro alfa']:
                            ref_pattern = r'\|\s*' + re.escape(raw_val) + r'\s*=\s*(.*?)(?=\r?\n\s*\||\r?\n\s*\}\}|\r|\n|$)'
                            m_ref = re.search(ref_pattern, content, re.IGNORECASE)
                            if m_ref:
                                raw_val = m_ref.group(1).strip()
                        val = clean_wikitext_entry(raw_val)
                        if val and len(val) > 10 and not val.lower().startswith('ver '):
                            descriptions[nat_id_str] = val
                            break
        except Exception as e:
            print(f"Error consultando lote WikiDex: {e}")

        # Guardar progreso incremental
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(descriptions, f, ensure_ascii=False, indent=2)

    print(f"Descripciones de WikiDex listas: {len(descriptions)} de 386")
    return descriptions


def fetch_pokemon_386_species():
    cache_file = CACHE_DIR / "pokemon_386_species.json"
    all_species = {}
    if cache_file.exists():
        with open(cache_file, "r", encoding="utf-8") as f:
            all_species = json.load(f)

    # 1. Cargar especies 1..251 desde crystal.json si faltan
    crystal_file = CATALOGS_DIR / "crystal.json"
    if crystal_file.exists():
        with open(crystal_file, "r", encoding="utf-8") as f:
            crystal_entries = json.load(f)
        for ce in crystal_entries:
            pk = ce.get("pokemon", {})
            nat_id = pk.get("national_number")
            if nat_id and str(nat_id) not in all_species:
                gd = ce.get("game_data", {})
                sm = gd.get("species_metrics", {})
                all_species[str(nat_id)] = {
                    'national_number': nat_id,
                    'name': pk.get("name"),
                    'display_name': pk.get("display_name"),
                    'category': pk.get("category", "Pokémon"),
                    'height': pk.get("height", 0),
                    'weight': pk.get("weight", 0),
                    'primary_type': ce.get("primary_type"),
                    'secondary_type': ce.get("secondary_type"),
                    'stats': gd.get("stats", {}),
                    'habitat': sm.get("habitat", "unknown"),
                    'egg_groups': sm.get("egg_groups", []),
                    'gender_rate': sm.get("gender_rate", -1),
                    'growth_rate': sm.get("growth_rate", "medium"),
                    'capture_rate': sm.get("capture_rate", 45),
                    'base_happiness': sm.get("base_happiness", 70),
                    'is_legendary': nat_id in [144, 145, 146, 150, 243, 244, 245, 249, 250],
                    'is_mythical': nat_id in [151, 251],
                }

    # 2. Descargar únicamente los faltantes (252..386) desde PokeAPI
    missing = [i for i in range(1, 387) if str(i) not in all_species]
    if missing:
        print(f"Descargando metadatos para {len(missing)} especies restantes (Gen 3) desde PokeAPI...")
        def fetch_one(nat_id):
            url_sp = f"https://pokeapi.co/api/v2/pokemon-species/{nat_id}/"
            url_pk = f"https://pokeapi.co/api/v2/pokemon/{nat_id}/"
            req_sp = urllib.request.Request(url_sp, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
            req_pk = urllib.request.Request(url_pk, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
            try:
                with urllib.request.urlopen(req_sp, timeout=12) as r1, urllib.request.urlopen(req_pk, timeout=12) as r2:
                    sp = json.loads(r1.read().decode('utf-8'))
                    pk = json.loads(r2.read().decode('utf-8'))

                genera_es = next((g['genus'] for g in sp.get('genera', []) if g['language']['name'] == 'es'), 'Pokémon')
                types = [t['type']['name'] for t in sorted(pk.get('types', []), key=lambda x: x['slot'])]
                type1 = types[0]
                type2 = types[1] if len(types) > 1 else None

                stats_dict = {s['stat']['name']: s['base_stat'] for s in pk.get('stats', [])}
                stats = {
                    'hp': stats_dict.get('hp', 0),
                    'attack': stats_dict.get('attack', 0),
                    'defense': stats_dict.get('defense', 0),
                    'special_attack': stats_dict.get('special-attack', 0),
                    'special_defense': stats_dict.get('special-defense', 0),
                    'speed': stats_dict.get('speed', 0),
                    'total': sum(stats_dict.values())
                }

                habitat = sp.get('habitat', {}).get('name') if sp.get('habitat') else 'unknown'
                egg_groups = [eg['name'] for eg in sp.get('egg_groups', [])]

                return str(nat_id), {
                    'national_number': nat_id,
                    'name': sp['name'],
                    'display_name': sp['name'].replace('-', ' ').title(),
                    'category': genera_es,
                    'height': pk.get('height', 0),
                    'weight': pk.get('weight', 0),
                    'primary_type': type1,
                    'secondary_type': type2,
                    'stats': stats,
                    'habitat': habitat,
                    'egg_groups': egg_groups,
                    'gender_rate': sp.get('gender_rate', -1),
                    'growth_rate': sp.get('growth_rate', {}).get('name', 'medium'),
                    'capture_rate': sp.get('capture_rate', 45),
                    'base_happiness': sp.get('base_happiness', 70),
                    'is_legendary': sp.get('is_legendary', False),
                    'is_mythical': sp.get('is_mythical', False),
                }
            except Exception as e:
                print(f"Error fetching #{nat_id}: {e}")
                return str(nat_id), None

        with ThreadPoolExecutor(max_workers=8) as executor:
            futures = [executor.submit(fetch_one, i) for i in missing]
            for f in futures:
                k, v = f.result()
                if v:
                    all_species[k] = v

        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(all_species, f, ensure_ascii=False, indent=2)

    return all_species


def fetch_ruby_encounters(hoenn_nat_ids):
    cache_file = CACHE_DIR / "encounters_ruby.json"
    if cache_file.exists():
        with open(cache_file, "r", encoding="utf-8") as f:
            return json.load(f)

    print(f"Descargando tablas de encuentros de Pokémon Rubí para los {len(hoenn_nat_ids)} Pokémon de Hoenn...")
    all_encounters = {}

    def fetch_one(nat_id):
        url = f"https://pokeapi.co/api/v2/pokemon/{nat_id}/encounters"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
        try:
            with urllib.request.urlopen(req, timeout=12) as resp:
                data = json.loads(resp.read().decode('utf-8'))
            
            ruby_locs = []
            for item in data:
                area_name = item.get('location_area', {}).get('name', '')
                for vd in item.get('version_details', []):
                    if vd.get('version', {}).get('name') == 'ruby':
                        for enc in vd.get('encounter_details', []):
                            method = enc.get('method', {}).get('name', 'walk')
                            ruby_locs.append({
                                'area_raw': area_name,
                                'method_raw': method,
                                'area_es': HOENN_AREAS_ES.get(area_name, area_name.replace('-', ' ').title()),
                                'method_es': METHOD_NAMES_ES.get(method, method.replace('-', ' ').title())
                            })
            return str(nat_id), ruby_locs
        except Exception:
            return str(nat_id), []

    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = [executor.submit(fetch_one, i) for i in hoenn_nat_ids]
        for f in futures:
            k, v = f.result()
            all_encounters[k] = v

    with open(cache_file, "w", encoding="utf-8") as f:
        json.dump(all_encounters, f, ensure_ascii=False, indent=2)

    return all_encounters


def build_catalogs():
    # 1. Cargar Hoenn Pokedex order (202 entries)
    hoenn_pokedex_cache = CACHE_DIR / "hoenn_pokedex_entries.json"
    if not hoenn_pokedex_cache.exists():
        url = "https://pokeapi.co/api/v2/pokedex/hoenn"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode('utf-8'))
        with open(hoenn_pokedex_cache, "w", encoding="utf-8") as f:
            json.dump(data['pokemon_entries'], f, indent=2)

    with open(hoenn_pokedex_cache, "r", encoding="utf-8") as f:
        hoenn_entries_raw = json.load(f)

    # Mapa de número nacional -> número de Hoenn
    hoenn_num_by_nat = {}
    for item in hoenn_entries_raw:
        hoenn_num = item['entry_number']
        sp_url = item['pokemon_species']['url']
        nat_num = int(sp_url.rstrip('/').split('/')[-1])
        hoenn_num_by_nat[nat_num] = hoenn_num

    species_map = fetch_pokemon_386_species()
    desc_map = fetch_wikidex_ruby_descriptions(species_map)
    enc_map = fetch_ruby_encounters(list(hoenn_num_by_nat.keys()))

    # Inicializar resolver de piedras
    from tracker.utils import resolve_evolution_stone

    # Cargar cadenas evolutivas
    with open(CACHE_DIR / "evolution_chains.json", "r", encoding="utf-8") as f:
        chains = json.load(f)

    # Construir mapa de evolución (restringido a especies presentes en Gen 3)
    valid_gen3_names = {sp['name'].lower() for sp in species_map.values()}
    evo_map = {}
    for chain_url, chain_data in chains.items():
        chain = chain_data.get('chain', {})
        def parse_chain(node, from_name=None):
            curr_name = node['species']['name'].lower()
            if from_name and from_name.lower() in valid_gen3_names and curr_name in valid_gen3_names:
                details = node.get('evolution_details', [{}])[0] if node.get('evolution_details') else {}
                trigger = details.get('trigger', {}).get('name', 'level-up')
                min_level = details.get('min_level')
                item = details.get('item', {}).get('name') if details.get('item') else None
                held_item = details.get('held_item', {}).get('name') if details.get('held_item') else None
                min_happiness = details.get('min_happiness')
                time_of_day = details.get('time_of_day')
                min_beauty = details.get('min_beauty')

                cond = ""
                item_display = EVO_ITEMS_ES.get(item, item.replace('-', ' ').title()) if item else None
                held_item_display = EVO_ITEMS_ES.get(held_item, held_item.replace('-', ' ').title()) if held_item else None
                if trigger == 'use-item' and item:
                    cond = f"usando {item_display}"
                elif trigger == 'trade':
                    if held_item:
                        cond = f"Intercambio equipado con {held_item_display}"
                    else:
                        cond = "Intercambio con otro entrenador"
                elif trigger == 'shed':
                    cond = "Nivel 20 (hueco libre y Poké Ball en mochila)"
                elif min_beauty:
                    cond = "Subir de nivel con 170+ de Belleza (dándole Pokécubos Azules o Índigo)"
                elif min_happiness:
                    tod = " (Día)" if time_of_day == "day" else " (Noche)" if time_of_day == "night" else (f" ({time_of_day})" if time_of_day else "")
                    cond = f"Felicidad alta{tod}"
                elif min_level:
                    if curr_name == 'hitmonlee':
                        cond = f"Nivel {min_level} (Ataque > Defensa)"
                    elif curr_name == 'hitmonchan':
                        cond = f"Nivel {min_level} (Ataque < Defensa)"
                    elif curr_name == 'hitmontop':
                        cond = f"Nivel {min_level} (Ataque = Defensa)"
                    elif curr_name in ['silcoon', 'cascoon']:
                        cond = f"Nivel {min_level} (según personalidad)"
                    else:
                        cond = f"Nivel {min_level}"
                else:
                    cond = "Condición especial"

                evo_map[curr_name] = {
                    'from': from_name.capitalize(),
                    'text': f"Evoluciona de {from_name.capitalize()} ({cond})",
                    'trigger': trigger,
                    'condition': cond,
                    'item_slug': item or held_item
                }

            # Si curr_name no pertenece a Gen 3 (ej: Budew), sus descendientes no tienen un padre válido en Gen 3
            next_from = curr_name if curr_name in valid_gen3_names else None
            for child in node.get('evolves_to', []):
                parse_chain(child, next_from)

        parse_chain(chain)

    # Tratamientos especiales de obtención en Rubí
    SPECIAL_OBT_RUBY = {
        # Iniciales
        252: {'type': 'starter', 'summary': 'Elegir en la bolsa del Profesor Abedul en la Ruta 101 al salvarlo (también obtenible mediante crianza).', 'locations': [{'area': 'Ruta 101', 'method': 'Inicial de Hoenn'}, {'area': 'Ruta 117 (Guardería Pokémon)', 'method': 'Crianza de huevo'}]},
        255: {'type': 'starter', 'summary': 'Elegir en la bolsa del Profesor Abedul en la Ruta 101 al salvarlo (también obtenible mediante crianza).', 'locations': [{'area': 'Ruta 101', 'method': 'Inicial de Hoenn'}, {'area': 'Ruta 117 (Guardería Pokémon)', 'method': 'Crianza de huevo'}]},
        258: {'type': 'starter', 'summary': 'Elegir en la bolsa del Profesor Abedul en la Ruta 101 al salvarlo (también obtenible mediante crianza).', 'locations': [{'area': 'Ruta 101', 'method': 'Inicial de Hoenn'}, {'area': 'Ruta 117 (Guardería Pokémon)', 'method': 'Crianza de huevo'}]},
        # Fósiles
        345: {'type': 'fossil', 'summary': 'Elegir el Fósil Raíz en el desierto de la Ruta 111 y revivirlo en Devon S.A. (Ciudad Férrica, también obtenible mediante crianza).', 'locations': [{'area': 'Ruta 111 (Desierto) / Ciudad Férrica', 'method': 'Revivir Fósil Raíz'}, {'area': 'Ruta 117 (Guardería Pokémon)', 'method': 'Crianza de huevo'}]},
        347: {'type': 'fossil', 'summary': 'Elegir el Fósil Garra en el desierto de la Ruta 111 y revivirlo en Devon S.A. (Ciudad Férrica, también obtenible mediante crianza).', 'locations': [{'area': 'Ruta 111 (Desierto) / Ciudad Férrica', 'method': 'Revivir Fósil Garra'}, {'area': 'Ruta 117 (Guardería Pokémon)', 'method': 'Crianza de huevo'}]},
        # Regalos NPC
        351: {'type': 'gift', 'summary': 'Regalo de los científicos del Instituto Meteorológico en la Ruta 119 tras vencer al Equipo Magma (también obtenible mediante crianza).', 'locations': [{'area': 'Ruta 119 (Instituto Meteorológico)', 'method': 'Regalo de científicos'}, {'area': 'Ruta 117 (Guardería Pokémon)', 'method': 'Crianza de huevo'}]},
        360: {
            'type': 'gift',
            'summary': 'Huevo entregado por una anciana en las aguas termales de Pueblo Lavacalda. También salvaje en Isla Espejismo o criando a Wobbuffet con Incienso Suave en la Guardería.',
            'locations': [
                {'area': 'Pueblo Lavacalda (Aguas termales)', 'method': 'Huevo de anciana'},
                {'area': 'Ruta 117 (Guardería Pokémon)', 'method': 'Crianza con Incienso Suave'},
                {'area': 'Isla Espejismo (Ruta 130)', 'method': 'Hierba alta (Isla aleatoria)'}
            ],
            'item_slug': 'lax-incense',
            'badge_color': 'emerald',
            'badge_label': 'Huevo Regalo'
        },
        374: {'type': 'gift', 'summary': 'Poké Ball dejada por Máximo Peñas en su casa de Ciudad Algaria tras vencer al Alto Mando (también obtenible mediante crianza).', 'locations': [{'area': 'Ciudad Algaria (Casa de Máximo)', 'method': 'Regalo de Máximo en el postgame'}, {'area': 'Ruta 117 (Guardería Pokémon)', 'method': 'Crianza de huevo'}]},
        # Crianza con Incienso y Bebés de Hoenn
        298: {
            'type': 'breeding',
            'summary': 'Criar a Marill o Azumarill equipado con Incienso Marino en la Guardería Pokémon (Ruta 117).',
            'locations': [
                {'area': 'Ruta 117 (Guardería Pokémon)', 'method': 'Crianza con Incienso Marino'}
            ],
            'item_slug': 'sea-incense',
            'badge_color': 'pink',
            'badge_label': 'Crianza'
        },
        172: {
            'type': 'breeding',
            'summary': 'Criar a Pikachu o Raichu en la Guardería Pokémon (Ruta 117). Pikachu es capturable en la Zona Safari.',
            'locations': [
                {'area': 'Ruta 117 (Guardería Pokémon)', 'method': 'Crianza en Guardería'}
            ],
            'badge_color': 'pink',
            'badge_label': 'Crianza'
        },
        174: {
            'type': 'breeding',
            'summary': 'Criar a Jigglypuff o Wigglytuff en la Guardería Pokémon (Ruta 117). Jigglypuff es capturable en la Ruta 115.',
            'locations': [
                {'area': 'Ruta 117 (Guardería Pokémon)', 'method': 'Crianza en Guardería'}
            ],
            'badge_color': 'pink',
            'badge_label': 'Crianza'
        },
        # Evolución especial
        292: {
            'type': 'evolution',
            'summary': 'Aparece en el equipo al evolucionar a Nincada a Ninjask en el nivel 20 (requiere un hueco libre en el equipo y una Poké Ball común en la mochila).',
            'locations': [],
            'evolution_info': {
                'from': 'Nincada',
                'text': 'Evoluciona de Nincada en Nivel 20 (con hueco libre en equipo y una Poké Ball)',
                'trigger': 'shed',
                'condition': 'Nivel 20 (hueco libre y Poké Ball en mochila)',
                'item_slug': None
            },
            'badge_color': 'indigo',
            'badge_label': 'Evolución'
        },
        # Legendarios y Míticos de Hoenn (Alineados con WikiDex)
        377: {
            'type': 'legendary',
            'badge_label': 'Legendario',
            'badge_color': 'purple',
            'summary': 'Ruinas del Desierto en la Ruta 111 al Nivel 40 (requiere abrir la Cámara Sellada en la Ruta 134 con Relicanth primero y Wailord al final del equipo, y en la sala de Regirock dar 2 pasos a la derecha, 2 abajo y usar Fuerza).',
            'locations': [{'area': 'Ruta 111 (Ruinas del Desierto)', 'method': 'Legendario estático (Nivel 40)'}]
        },
        378: {
            'type': 'legendary',
            'badge_label': 'Legendario',
            'badge_color': 'purple',
            'summary': 'Cueva Insular en la Ruta 105 al Nivel 40 (requiere abrir la Cámara Sellada en la Ruta 134 con Relicanth y Wailord, y en la Cueva Insular esperar quieto 2 minutos frente al muro Braille).',
            'locations': [{'area': 'Ruta 105 (Cueva Insular)', 'method': 'Legendario estático (Nivel 40)'}]
        },
        379: {
            'type': 'legendary',
            'badge_label': 'Legendario',
            'badge_color': 'purple',
            'summary': 'Tumba Antigua en la Ruta 120 al Nivel 40 (requiere abrir la Cámara Sellada en la Ruta 134 con Relicanth y Wailord, y en la Tumba Antigua situarse en el centro de la sala y usar Vuelo).',
            'locations': [{'area': 'Ruta 120 (Tumba Antigua)', 'method': 'Legendario estático (Nivel 40)'}]
        },
        380: {
            'type': 'trade',
            'badge_label': 'Intercambio / Evento',
            'badge_color': 'indigo',
            'summary': 'Legendario errante exclusivo de Pokémon Zafiro. En Pokémon Rubí se obtiene mediante intercambio con Zafiro/Esmeralda, o de forma salvaje en la Isla del Sur (Nivel 50, equipado con Rocío Bondad) mediante el evento oficial del Ticket Eón.',
            'locations': [
                {'area': 'Isla del Sur (Evento Ticket Eón)', 'method': 'Salvaje estático al Nivel 50 con Ticket Eón'},
                {'area': 'Intercambio con Pokémon Zafiro', 'method': 'Intercambio de versión (donde es errante)'}
            ]
        },
        381: {
            'type': 'legendary',
            'badge_label': 'Legendario',
            'badge_color': 'purple',
            'summary': 'Legendario errante salvaje por todo Hoenn al Nivel 40 tras vencer al Alto Mando (aparece de forma automática en Rubí sin tener que elegir color en la televisión, a diferencia de Esmeralda).',
            'locations': [{'area': 'Rutas de Hoenn (Errante)', 'method': 'Salvaje errante tras el Alto Mando'}]
        },
        382: {
            'type': 'trade',
            'badge_label': 'Exclusivo Zafiro',
            'badge_color': 'blue',
            'summary': 'Pokémon Legendario de portada exclusivo de Pokémon Zafiro (Cueva del Origen). En Pokémon Rubí solo se puede obtener mediante intercambio desde Pokémon Zafiro o Pokémon Esmeralda.',
            'locations': [{'area': 'Intercambio con Pokémon Zafiro', 'method': 'Exclusivo de versión (Cueva del Origen en Zafiro)'}]
        },
        383: {
            'type': 'legendary',
            'badge_label': 'Legendario',
            'badge_color': 'purple',
            'summary': 'Cueva del Origen en Ciudad Arrecípolis al Nivel 45 durante la crisis climática del Equipo Magma.',
            'locations': [{'area': 'Ciudad Arrecípolis (Cueva del Origen)', 'method': 'Legendario estático de portada (Nivel 45)'}]
        },
        384: {
            'type': 'legendary',
            'badge_label': 'Legendario',
            'badge_color': 'purple',
            'summary': 'Cima del Pilar Celeste en la Ruta 131 al Nivel 70 (requiere la Bici Carrera para cruzar el suelo agrietado).',
            'locations': [{'area': 'Ruta 131 (Pilar Celeste)', 'method': 'Legendario estático (Nivel 70)'}]
        },
        385: {
            'type': 'gift',
            'badge_label': 'Mítico / Evento',
            'badge_color': 'purple',
            'summary': 'Pokémon singular de evento oficial. Obtenible mediante transferencia desde Pokémon Channel (versión europea/australiana) o desde el disco bonus de Pokémon Colosseum (versión estadounidense/japonesa) a través del cable GameCube-GBA. También distribuido en eventos presenciales oficiales de Nintendo.',
            'locations': [
                {'area': 'Pokémon Channel (Europa/Australia)', 'method': 'Transferencia externa (GameCube a GBA)'},
                {'area': 'Pokémon Colosseum Bonus Disc (América/Japón)', 'method': 'Transferencia externa (GameCube a GBA)'},
                {'area': 'Evento oficial de Nintendo', 'method': 'Distribución presencial directa'}
            ]
        },
        386: {
            'type': 'trade',
            'badge_label': 'Intercambio / Evento',
            'badge_color': 'indigo',
            'summary': 'Inaccesible salvaje en Rubí (la Isla Origen no existe en esta versión). Obtenible únicamente mediante intercambio desde Pokémon Rojo Fuego, Verde Hoja o Esmeralda (o mediante evento presencial oficial de Nintendo). En Rubí adopta su Forma Normal.',
            'locations': [
                {'area': 'Intercambio externo (GBA)', 'method': 'Intercambio desde Rojo Fuego, Verde Hoja o Esmeralda'},
                {'area': 'Evento presencial de Nintendo', 'method': 'Distribución oficial por cable link'}
            ]
        },
        # Peculiares
        349: {'type': 'wild', 'summary': 'Pesca con Caña en exactamente 6 casillas aleatorias de agua en la Ruta 119.', 'locations': [{'area': 'Ruta 119', 'method': 'Pesca en casilla especial de Feebas'}]},
        350: {'type': 'evolution', 'summary': 'Evoluciona de Feebas al alcanzar 170+ de Belleza dándole Pokécubos Azules/Índigo y subiendo 1 nivel.', 'locations': []},
        # Exclusivos de Zafiro
        270: {'type': 'trade', 'badge_label': 'Exclusivo Zafiro', 'badge_color': 'blue', 'summary': 'Exclusivo de Pokémon Zafiro (Ruta 102 y Ruta 114). Requiere intercambio con otra consola (también obtenible mediante crianza).', 'locations': [{'area': 'Intercambio con Pokémon Zafiro', 'method': 'Exclusivo de versión'}, {'area': 'Ruta 117 (Guardería Pokémon)', 'method': 'Crianza de huevo'}]},
        271: {'type': 'trade', 'badge_label': 'Exclusivo Zafiro', 'badge_color': 'blue', 'summary': 'Exclusivo de Pokémon Zafiro (Ruta 114). Requiere intercambio o evolucionar de Lotad.', 'locations': [{'area': 'Intercambio con Pokémon Zafiro', 'method': 'Exclusivo de versión'}]},
        272: {'type': 'trade', 'badge_label': 'Exclusivo Zafiro', 'badge_color': 'blue', 'summary': 'Exclusivo de Pokémon Zafiro. Evoluciona de Lombre usando Piedra Agua.', 'locations': [{'area': 'Intercambio con Pokémon Zafiro', 'method': 'Exclusivo de versión'}]},
        302: {'type': 'trade', 'badge_label': 'Exclusivo Zafiro', 'badge_color': 'blue', 'summary': 'Exclusivo de Pokémon Zafiro (Cueva Granito, Cueva del Origen, Calle Victoria). Requiere intercambio con otra consola (también obtenible mediante crianza).', 'locations': [{'area': 'Intercambio con Pokémon Zafiro', 'method': 'Exclusivo de versión'}, {'area': 'Ruta 117 (Guardería Pokémon)', 'method': 'Crianza de huevo'}]},
        336: {'type': 'trade', 'badge_label': 'Exclusivo Zafiro', 'badge_color': 'blue', 'summary': 'Exclusivo de Pokémon Zafiro (Ruta 114). Requiere intercambio con otra consola (también obtenible mediante crianza).', 'locations': [{'area': 'Intercambio con Pokémon Zafiro', 'method': 'Exclusivo de versión'}, {'area': 'Ruta 117 (Guardería Pokémon)', 'method': 'Crianza de huevo'}]},
        337: {'type': 'trade', 'badge_label': 'Exclusivo Zafiro', 'badge_color': 'blue', 'summary': 'Exclusivo de Pokémon Zafiro (Cascada Meteoro). Requiere intercambio con otra consola (también obtenible mediante crianza).', 'locations': [{'area': 'Intercambio con Pokémon Zafiro', 'method': 'Exclusivo de versión'}, {'area': 'Ruta 117 (Guardería Pokémon)', 'method': 'Crianza de huevo'}]},
    }

    # Intercambios NPC en Rubí
    INGAME_TRADES_RUBY = {
        296: {'type': 'trade_npc', 'summary': 'Intercambio en Ciudad Férrica: una chica te da a Makuhita (MAKU) a cambio de un Slakoth.', 'locations': [{'area': 'Ciudad Férrica', 'method': 'Intercambio NPC por Slakoth'}]},
        300: {'type': 'trade_npc', 'summary': 'Intercambio en Pueblo Verdegal: un hombre te da a Skitty (SKITY) a cambio de un Pikachu.', 'locations': [{'area': 'Pueblo Verdegal', 'method': 'Intercambio NPC por Pikachu'}]},
        311: {'type': 'trade_npc', 'summary': 'Intercambio en Ciudad Arborada: un chico te da a Plusle (PLUS) a cambio de un Volbeat.', 'locations': [{'area': 'Ciudad Arborada', 'method': 'Intercambio NPC por Volbeat'}]},
        116: {'type': 'trade_npc', 'summary': 'Intercambio en Pueblo Oromar: una chica te da a Horsea (SEA) a cambio de un Bagon.', 'locations': [{'area': 'Pueblo Oromar', 'method': 'Intercambio NPC por Bagon'}]},
    }

    hoenn_catalog_entries = []
    national_catalog_entries = []

    # ID base para Rubí: 1207 en adelante (red 1..151, blue 152..302, yellow 303..453, gold 454..704, silver 705..955, crystal 956..1206)
    STARTING_RUBY_ID = 1207

    for nat_id in range(1, 387):
        entry_id = STARTING_RUBY_ID + (nat_id - 1)
        sp = species_map[str(nat_id)]
        name = sp['name']
        display_name = sp['display_name']
        p_type = sp['primary_type']
        s_type = sp['secondary_type']

        # Descripción
        flavor_text = desc_map.get(str(nat_id), "")
        if not flavor_text:
            flavor_text = f"{display_name} es una especie de Pokémon de tipo {TYPE_NAMES_ES.get(p_type)}."

        # Evolución
        evo_info = evo_map.get(name)

        # Obtención
        is_in_hoenn = nat_id in hoenn_num_by_nat
        hoenn_number = hoenn_num_by_nat.get(nat_id)

        raw_locs = enc_map.get(str(nat_id), [])
        unique_locs = []
        seen_areas = set()
        for l in raw_locs:
            raw_area = l.get('area_raw') or l.get('area_es')
            area_translated = HOENN_AREAS_ES.get(raw_area, l.get('area_es', raw_area))
            raw_method = l.get('method_raw') or l.get('method_es')
            method_translated = METHOD_NAMES_ES.get(raw_method, l.get('method_es', raw_method))
            k = (area_translated, method_translated)
            if k not in seen_areas:
                seen_areas.add(k)
                unique_locs.append({'area': area_translated, 'method': method_translated})

        obt_info = {}
        if nat_id in SPECIAL_OBT_RUBY:
            obt_info = SPECIAL_OBT_RUBY[nat_id]
        elif nat_id in INGAME_TRADES_RUBY and not unique_locs:
            obt_info = INGAME_TRADES_RUBY[nat_id]
        elif unique_locs:
            areas_str = ", ".join([l['area'] for l in unique_locs[:3]])
            summary = f"Salvaje en {len(unique_locs)} zona(s) de Hoenn (ej: {areas_str})."
            obt_info = {
                'type': 'wild',
                'summary': summary,
                'locations': unique_locs
            }
        elif evo_info:
            obt_info = {
                'type': 'evolution',
                'summary': evo_info['text'],
                'locations': [],
                'evolution_info': evo_info
            }
        elif is_in_hoenn:
            obt_info = {
                'type': 'special',
                'summary': f"Obtenible en la región de Hoenn.",
                'locations': []
            }
        else:
            # Pokémon no nativo de Hoenn (Pokédex Nacional)
            transfer_origin = "Pokémon Rojo Fuego / Verde Hoja o Pokémon Colosseum"
            if nat_id in [1, 2, 3, 4, 5, 6, 7, 8, 9, 144, 145, 146, 150]:
                transfer_origin = "Transferencia desde Pokémon Rojo Fuego o Pokémon Verde Hoja"
            elif nat_id in [152, 153, 154, 155, 156, 157, 158, 159, 160, 243, 244, 245, 250]:
                transfer_origin = "Transferencia desde Pokémon Colosseum (GameCube)"
            elif nat_id == 249:
                transfer_origin = "Transferencia desde Pokémon XD: Gale of Darkness (GameCube)"
            elif nat_id == 151:
                transfer_origin = "Evento oficial Isla Suprema (Mapa Viejo)"
            elif nat_id == 251:
                transfer_origin = "Disco bonus de Pokémon Colosseum (Japón) o evento"

            egg_groups = sp.get('egg_groups', [])
            can_breed = ('no-eggs' not in egg_groups) and ('ditto' not in egg_groups)

            if nat_id in [173, 175, 236, 238, 239, 240]:
                obt_info = {
                    'type': 'transfer',
                    'summary': f"No disponible salvaje en Hoenn. Requiere {transfer_origin} (también obtenible mediante crianza).",
                    'locations': [
                        {'area': 'Transferencia externa (GBA / GameCube)', 'method': transfer_origin},
                        {'area': 'Ruta 117 (Guardería Pokémon)', 'method': 'Crianza de huevo'}
                    ],
                    'badge_color': 'pink',
                    'badge_label': 'Crianza / Transfer'
                }
            elif can_breed:
                obt_info = {
                    'type': 'transfer',
                    'summary': f"No disponible en estado salvaje en Hoenn. Requiere {transfer_origin} (también obtenible mediante crianza).",
                    'locations': [
                        {'area': 'Transferencia externa (GBA / GameCube)', 'method': transfer_origin},
                        {'area': 'Ruta 117 (Guardería Pokémon)', 'method': 'Crianza de huevo'}
                    ]
                }
            else:
                obt_info = {
                    'type': 'transfer',
                    'summary': f"No disponible en Hoenn. Requiere {transfer_origin}. No es posible transferir desde Gen 1 o Gen 2.",
                    'locations': [{'area': 'Transferencia externa (GBA / GameCube)', 'method': transfer_origin}]
                }

        # Piedra evolutiva u objeto especial / incienso de crianza
        evo_stone = None
        item_slug_to_resolve = (evo_info.get('item_slug') if evo_info else None) or obt_info.get('item_slug')
        if item_slug_to_resolve:
            evo_stone = resolve_evolution_stone(item_slug=item_slug_to_resolve, game_slug="ruby")

        # Ajuste de evolución si existe
        if evo_info and 'evolution_info' not in obt_info:
            obt_info['evolution_info'] = evo_info

        # Badge colors
        type_badge_colors = {
            'starter': ('amber', 'Inicial'),
            'legendary': ('purple', 'Legendario'),
            'fossil': ('amber', 'Fósil'),
            'gift': ('emerald', 'Regalo'),
            'evolution': ('indigo', 'Evolución'),
            'trade': ('blue', 'Intercambio'),
            'trade_npc': ('sky', 'Intercambio NPC'),
            'wild': ('emerald', 'Salvaje'),
            'breeding': ('pink', 'Crianza'),
            'contest': ('emerald', 'Parque Nacional'),
            'transfer': ('rose', 'Transferencia'),
            'special': ('slate', 'Especial')
        }
        b_color, b_label = type_badge_colors.get(obt_info.get('type', 'wild'), ('slate', 'Hoenn'))
        if 'badge_color' not in obt_info:
            obt_info['badge_color'] = b_color
        if 'badge_label' not in obt_info:
            obt_info['badge_label'] = b_label

        entry_base = {
            "id": entry_id,
            "entry_number": nat_id, # por defecto nacional
            "game_slug": "ruby",
            "pokemon": {
                "national_number": nat_id,
                "name": name,
                "display_name": display_name,
                "category": sp['category'],
                "height": sp['height'],
                "weight": sp['weight'],
                "sprite_url": f"/media/pokemon/artwork/{nat_id}.png",
                "sprite_shiny_url": f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/shiny/{nat_id}.png" if nat_id != 201 else "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/shiny/201-f.png",
                "artwork_shiny_url": f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/shiny/{nat_id}.png" if nat_id != 201 else "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/shiny/201-f.png",
                "primary_type": p_type,
                "secondary_type": s_type
            },
            "primary_type": p_type,
            "primary_type_display": p_type,
            "primary_type_es": TYPE_NAMES_ES.get(p_type, p_type.capitalize()),
            "secondary_type": s_type,
            "secondary_type_display": s_type,
            "secondary_type_es": TYPE_NAMES_ES.get(s_type, s_type.capitalize()) if s_type else None,
            "game_sprite_url": f"/media/pokemon/sprites/ruby/{nat_id}.png",
            "game_sprite_shiny_url": f"/media/pokemon/sprites/ruby_shiny/{nat_id}.png",
            "game_sprite_back_url": f"/media/pokemon/sprites/ruby/back/{nat_id}.png",
            "game_sprite_shiny_back_url": f"/media/pokemon/sprites/ruby_shiny/back/{nat_id}.png",
            "modern_sprite_shiny_url": f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/shiny/{nat_id}.png" if nat_id != 201 else "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/shiny/201-f.png",
            "modal_retro_sprite_url": f"/media/pokemon/sprites/ruby/{nat_id}.png",
            "modal_retro_sprite_shiny_url": f"/media/pokemon/sprites/ruby_shiny/{nat_id}.png",
            "modal_retro_sprite_back_url": f"/media/pokemon/sprites/ruby/back/{nat_id}.png",
            "modal_retro_sprite_shiny_back_url": f"/media/pokemon/sprites/ruby_shiny/back/{nat_id}.png",
            "pc_icon_url": f"/media/pokemon/icons/gen3/{nat_id}.png",
            "cry_url": f"/media/pokemon/cries/legacy/{nat_id}.ogg",
            "flavor_text": flavor_text,
            "obtaining_info": obt_info,
            "evolution_stone": evo_stone,
            "game_data": {
                "moves": {"machine": []},
                "stats": sp['stats'],
                "generation": 3,
                "version_group": "ruby-sapphire",
                "species_metrics": {
                    "habitat": sp['habitat'],
                    "egg_groups": sp['egg_groups'],
                    "gender_rate": sp['gender_rate'],
                    "growth_rate": sp['growth_rate'],
                    "capture_rate": sp['capture_rate'],
                    "base_happiness": sp['base_happiness']
                }
            }
        }

        # 1. Agregar a Pokédex Nacional
        entry_national = dict(entry_base)
        entry_national["entry_number"] = nat_id
        national_catalog_entries.append(entry_national)

        # 2. Agregar a Pokédex Regional de Hoenn si pertenece
        if is_in_hoenn:
            entry_hoenn = json.loads(json.dumps(entry_base))
            entry_hoenn["entry_number"] = hoenn_number
            hoenn_catalog_entries.append(entry_hoenn)

    # Ordenar Pokédex Regional de Hoenn por número de Hoenn (1..202)
    hoenn_catalog_entries.sort(key=lambda x: x["entry_number"])

    # Guardar ambos catálogos
    with open(CATALOGS_DIR / "ruby.json", "w", encoding="utf-8") as f:
        json.dump(hoenn_catalog_entries, f, ensure_ascii=False, indent=2)

    with open(CATALOGS_DIR / "ruby_national.json", "w", encoding="utf-8") as f:
        json.dump(national_catalog_entries, f, ensure_ascii=False, indent=2)

    print(f"[OK] ruby.json generado con {len(hoenn_catalog_entries)} entradas (Pokédex Regional de Hoenn)")
    print(f"[OK] ruby_national.json generado con {len(national_catalog_entries)} entradas (Pokédex Nacional)")


if __name__ == "__main__":
    build_catalogs()
