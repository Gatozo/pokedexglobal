"""
Script para compilar los catálogos oficiales de Pokémon Esmeralda (Gen 3):
1. emerald.json (Pokédex Regional de Hoenn: 202 Pokémon, numeración 1 a 202)
2. emerald_national.json (Pokédex Nacional de Esmeralda: 386 Pokémon, numeración 1 a 386)

Sigue rigurosamente la especificación en guides/especificacion-nuevo-juego.md:
- 100% toponimia y métodos en español oficial (HOENN_AREAS_ES).
- No re-descarga de iconos ni activos existentes.
- Respeto del canon oficial de Pokémon Esmeralda:
  * Mascota de portada: Rayquaza (Pilar Celeste Nivel 70).
  * Doble legendario: Tanto Groudon (Cueva Terra) como Kyogre (Cueva Marina) son capturables al Nivel 70 en el postgame.
  * Latias y Latios: Elección de color tras la Liga (errante por Hoenn) y el otro en Isla del Sur (Ticket Eón) o intercambio.
  * Pokémon ausentes de Hoenn en Esmeralda (exclusivos de Rubí/Zafiro): Surskit, Masquerain, Meditite, Medicham, Roselia, Zangoose y Lunatone.
  * Especies de Johto salvajes en postgame: Expansión de Zona Safari (Áreas 5 y 6), Cueva Taller (Smeargle), Túnel del Desierto (Ditto), Frente de Batalla (Sudowoodo) e iniciales de Johto de regalo del Prof. Abedul.
"""
import os
import sys
import json
import re
import copy
from pathlib import Path

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

# Traducción oficial de áreas de Hoenn (incluyendo áreas exclusivas de Esmeralda)
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
    'cave-of-origin-b4f': 'Cueva del Origen (Profundidades)',

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

    # Zona Safari de Hoenn (Áreas principales y expansión postgame de Johto)
    'hoenn-safari-zone-area': 'Zona Safari (Hoenn)',
    'hoenn-safari-zone-expansion-south': 'Zona Safari (Expansión Johto Sur)',
    'hoenn-safari-zone-expansion-north': 'Zona Safari (Expansión Johto Norte)',
    'hoenn-safari-zone-neacro-bike-area': 'Zona Safari (Noreste Bici Acrobática)',
    'hoenn-safari-zone-se-area': 'Zona Safari (Sureste)',
    'hoenn-safari-zone-sw-area': 'Zona Safari (Suroeste)',
    'hoenn-safari-zone-nw-area': 'Zona Safari (Noroeste)',

    # Nao Abandonada y Malvalona Nueva
    'abandoned-ship-area': 'Nao Abandonada (Interior / Surf)',
    'abandoned-ship-captain-office': 'Nao Abandonada (Camarote del Capitán)',
    'abandoned-ship-corridors-b1f': 'Nao Abandonada (Sótano)',
    'abandoned-ship-hidden-rooms': 'Nao Abandonada (Salas Sumergidas)',
    'new-mauville-area': 'Malvalona Nueva (Interior)',
    'new-mauville-entrance': 'Malvalona Nueva (Entrada)',
    'new-mauville-inside': 'Malvalona Nueva (Interior)',

    # Exclusivos de Esmeralda (Nuevas mazmorras y áreas)
    'artisan-cave-area': 'Cueva Taller (Frente de Batalla)',
    'artisan-cave-1f': 'Cueva Taller (P1)',
    'artisan-cave-b1f': 'Cueva Taller (S1)',
    'desert-underpass-area': 'Túnel del Desierto (Ruta 114)',
    'hoenn-battle-frontier-area': 'Frente de Batalla',
    'battle-frontier-area': 'Frente de Batalla',
    'marine-cave-area': 'Cueva Marina (Kyogre)',
    'terra-cave-area': 'Cueva Terra (Groudon)',
    'mirage-tower-area': 'Torre Espejismo (Ruta 111)',
    'mirage-tower-1f': 'Torre Espejismo (P1)',
    'mirage-tower-2f': 'Torre Espejismo (P2)',
    'mirage-tower-3f': 'Torre Espejismo (P3)',
    'mirage-tower-4f': 'Torre Espejismo (Cima Fósil)',
    'magma-hideout-area': 'Guarida Magma (Desfiladero)',
    'magma-hideout-1f': 'Guarida Magma (Desfiladero P1)',
    'magma-hideout-2f': 'Guarida Magma (Desfiladero P2)',
    'magma-hideout-3f': 'Guarida Magma (Desfiladero P3)',
    'magma-hideout-4f': 'Guarida Magma (Desfiladero P4)',

    # Eventos e Islas Especiales
    'mirage-island-area': 'Isla Espejismo (Ruta 130)',
    'southern-island-area': 'Isla del Sur (Evento Ticket Eón)',
    'team-aqua-hideout-area': 'Guarida Aqua (Ciudad Calagua)',
    'faraway-island-area': 'Isla Suprema (Evento Mapa Viejo - Mew)',
    'birth-island-area': 'Isla Origen (Evento Ori-Ticket - Deoxys)',
    'navel-rock-area': 'Roca Ombligo (Evento Ticket Místico - Lugia/Ho-Oh)',
    'hoenn-altering-cave-area': 'Cueva Cambiante (Ruta 103)',
    'altering-cave-area': 'Cueva Cambiante (Ruta 103)'
}

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
    text = re.sub(r"\{\{(?:NombreHaEs|n)\|([^|]+)(?:\|([^}]+))?\}*", lambda m: m.group(2) or m.group(1), text)
    text = re.sub(r"\{\{[^}]+\}\}", "", text)
    text = re.sub(r"\[\[(?:[^|\]]*\|)?([^\]]+)\]\]", r"\1", text)
    text = re.sub(r"<ref[^>]*>.*?</ref>", "", text, flags=re.DOTALL)
    text = re.sub(r"<[^>]+>", "", text)
    return text.strip()


def resolve_evolution_stone(item_slug: str, game_slug: str = "emerald"):
    stones_file = BASE_DIR / "tracker" / "data" / "evolution_stones.json"
    if not stones_file.exists():
        return None
    try:
        with open(stones_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        if item_slug in data:
            item_data = data[item_slug]
            game_locs = item_data.get("games", {}).get(game_slug, [])
            return {
                "slug": item_data.get("slug", item_slug),
                "name": item_data.get("name_es", item_slug.replace('-', ' ').title()),
                "icon_url": item_data.get("icon_url", f"/media/items/{item_slug}.png"),
                "description": item_data.get("description_es", ""),
                "locations": game_locs
            }
    except Exception as e:
        print(f"Error resolviendo objeto evolutivo {item_slug}: {e}")
    return None


def fetch_pokemon_386_species():
    cache_file = CACHE_DIR / "pokemon_386_species.json"
    if cache_file.exists():
        with open(cache_file, "r", encoding="utf-8") as f:
            return json.load(f)
    raise FileNotFoundError("pokemon_386_species.json no encontrado en caché.")


def fetch_emerald_encounters():
    cache_file = CACHE_DIR / "encounters_emerald.json"
    if cache_file.exists():
        with open(cache_file, "r", encoding="utf-8") as f:
            return json.load(f)
    raise FileNotFoundError("encounters_emerald.json no encontrado en caché.")


def fetch_wikidex_emerald_descriptions():
    cache_file = CACHE_DIR / "wikidex_emerald_descriptions.json"
    if cache_file.exists():
        with open(cache_file, "r", encoding="utf-8") as f:
            return json.load(f)
    raise FileNotFoundError("wikidex_emerald_descriptions.json no encontrado en caché.")


def main():
    print("Iniciando compilación de catálogos oficiales para Pokémon Esmeralda (emerald)...")
    species_386 = fetch_pokemon_386_species()
    encounters_emerald = fetch_emerald_encounters()
    wikidex_descriptions = fetch_wikidex_emerald_descriptions()

    with open(CACHE_DIR / "hoenn_pokedex_entries.json", "r", encoding="utf-8") as f:
        hoenn_pokedex_entries = json.load(f)

    with open(CACHE_DIR / "evolution_chains.json", "r", encoding="utf-8") as f:
        evolution_chains = json.load(f)

    # Construir mapa de evolución (restringido a especies presentes en Gen 3)
    valid_gen3_names = {sp['name'].lower() for sp in species_386.values()}
    evo_map = {}
    for chain_url, chain_data in evolution_chains.items():
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
                min_beauty = details.get('min_beauty')
                time_of_day = details.get('time_of_day')

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

            next_from = curr_name if curr_name in valid_gen3_names else None
            for child in node.get('evolves_to', []):
                parse_chain(child, next_from)

        parse_chain(chain)

    # Intercambios dentro del juego (In-Game Trades) en Esmeralda
    INGAME_TRADES_EMERALD = {
        273: {  # Seedot
            'type': 'trade',
            'summary': 'Intercambio dentro del juego en Ciudad Férrica entregando un Ralts (Kino / Makit, también salvaje en Hoenn y obtenible mediante crianza).',
            'locations': [
                {'area': 'Ciudad Férrica (Casa junto al Gimnasio)', 'method': 'Intercambio NPC por Ralts'},
                {'area': 'Ruta 117 (Guardería Pokémon)', 'method': 'Crianza de huevo'}
            ]
        },
        311: {  # Plusle
            'type': 'trade',
            'summary': 'Intercambio dentro del juego en Ciudad Arborada entregando un Volbeat (Paprún / Plusey, también salvaje en Hoenn y obtenible mediante crianza).',
            'locations': [
                {'area': 'Ciudad Arborada (Casa norte)', 'method': 'Intercambio NPC por Volbeat'},
                {'area': 'Ruta 117 (Guardería Pokémon)', 'method': 'Crianza de huevo'}
            ]
        },
        116: {  # Horsea
            'type': 'trade',
            'summary': 'Intercambio dentro del juego en Pueblo Oromar entregando un Bagon (Tico / Seadra, también salvaje pescando en Hoenn y obtenible mediante crianza).',
            'locations': [
                {'area': 'Pueblo Oromar (Casa sudoeste)', 'method': 'Intercambio NPC por Bagon'},
                {'area': 'Ruta 117 (Guardería Pokémon)', 'method': 'Crianza de huevo'}
            ]
        },
        52: {   # Meowth
            'type': 'trade',
            'summary': 'Intercambio dentro del juego en el Frente de Batalla entregando un Skitty (Miauchi / Meowth, también obtenible mediante crianza).',
            'locations': [
                {'area': 'Frente de Batalla (Cabaña este)', 'method': 'Intercambio NPC por Skitty'},
                {'area': 'Ruta 117 (Guardería Pokémon)', 'method': 'Crianza de huevo'}
            ]
        }
    }

    # Métodos especiales en Esmeralda
    SPECIAL_OBT_EMERALD = {
        # Iniciales de Hoenn
        252: {
            'type': 'starter',
            'summary': 'Pokémon Inicial de tipo Planta a elegir en el maletín del Profesor Abedul en la Ruta 101 (también obtenible mediante crianza).',
            'locations': [
                {'area': 'Ruta 101', 'method': 'Inicial de Hoenn (Regalo del Profesor Abedul)'},
                {'area': 'Ruta 117 (Guardería Pokémon)', 'method': 'Crianza de huevo'}
            ]
        },
        255: {
            'type': 'starter',
            'summary': 'Pokémon Inicial de tipo Fuego a elegir en el maletín del Profesor Abedul en la Ruta 101 (también obtenible mediante crianza).',
            'locations': [
                {'area': 'Ruta 101', 'method': 'Inicial de Hoenn (Regalo del Profesor Abedul)'},
                {'area': 'Ruta 117 (Guardería Pokémon)', 'method': 'Crianza de huevo'}
            ]
        },
        258: {
            'type': 'starter',
            'summary': 'Pokémon Inicial de tipo Agua a elegir en el maletín del Profesor Abedul en la Ruta 101 (también obtenible mediante crianza).',
            'locations': [
                {'area': 'Ruta 101', 'method': 'Inicial de Hoenn (Regalo del Profesor Abedul)'},
                {'area': 'Ruta 117 (Guardería Pokémon)', 'method': 'Crianza de huevo'}
            ]
        },

        # Iniciales de Johto (Regalo postgame por completar 200 de Hoenn)
        152: {
            'type': 'gift',
            'badge_label': 'Regalo Abedul',
            'badge_color': 'emerald',
            'summary': 'Regalo del Profesor Abedul en Villa Raíz a elegir entre Chikorita, Cyndaquil o Totodile tras completar las 200 especies de la Pokédex Regional de Hoenn (también obtenible mediante crianza o transferible desde Pokémon Colosseum).',
            'locations': [
                {'area': 'Villa Raíz (Laboratorio Abedul)', 'method': 'Premio por completar 200 Pokémon de Hoenn'},
                {'area': 'Ruta 117 (Guardería Pokémon)', 'method': 'Crianza de huevo'},
                {'area': 'Transferencia externa (GBA / GameCube)', 'method': 'Pokémon Colosseum'}
            ]
        },
        155: {
            'type': 'gift',
            'badge_label': 'Regalo Abedul',
            'badge_color': 'emerald',
            'summary': 'Regalo del Profesor Abedul en Villa Raíz a elegir entre Chikorita, Cyndaquil o Totodile tras completar las 200 especies de la Pokédex Regional de Hoenn (también obtenible mediante crianza o transferible desde Pokémon Colosseum).',
            'locations': [
                {'area': 'Villa Raíz (Laboratorio Abedul)', 'method': 'Premio por completar 200 Pokémon de Hoenn'},
                {'area': 'Ruta 117 (Guardería Pokémon)', 'method': 'Crianza de huevo'},
                {'area': 'Transferencia externa (GBA / GameCube)', 'method': 'Pokémon Colosseum'}
            ]
        },
        158: {
            'type': 'gift',
            'badge_label': 'Regalo Abedul',
            'badge_color': 'emerald',
            'summary': 'Regalo del Profesor Abedul en Villa Raíz a elegir entre Chikorita, Cyndaquil o Totodile tras completar las 200 especies de la Pokédex Regional de Hoenn (también obtenible mediante crianza o transferible desde Pokémon Colosseum).',
            'locations': [
                {'area': 'Villa Raíz (Laboratorio Abedul)', 'method': 'Premio por completar 200 Pokémon de Hoenn'},
                {'area': 'Ruta 117 (Guardería Pokémon)', 'method': 'Crianza de huevo'},
                {'area': 'Transferencia externa (GBA / GameCube)', 'method': 'Pokémon Colosseum'}
            ]
        },

        # Fósiles de Hoenn (Torre Espejismo y Túnel del Desierto)
        345: {
            'type': 'fossil',
            'summary': 'Revivir el Fósil Raíz en la 1.ª planta de Devon S.A. en Ciudad Férrica al Nivel 20 (también obtenible mediante crianza). En Esmeralda se elige en la Torre Espejismo (Ruta 111) y el otro fósil reaparece tras el Alto Mando en el Túnel del Desierto.',
            'locations': [
                {'area': 'Ciudad Férrica (Devon S.A.)', 'method': 'Revivir Fósil Raíz al Nivel 20'},
                {'area': 'Ruta 111 (Torre Espejismo)', 'method': 'Obtención de Fósil Raíz en la cima'},
                {'area': 'Ruta 114 (Túnel del Desierto)', 'method': 'Segundo fósil en el fondo del túnel tras el Alto Mando'},
                {'area': 'Ruta 117 (Guardería Pokémon)', 'method': 'Crianza de huevo'}
            ],
            'badge_color': 'amber',
            'badge_label': 'Fósil'
        },
        347: {
            'type': 'fossil',
            'summary': 'Revivir el Fósil Garra en la 1.ª planta de Devon S.A. en Ciudad Férrica al Nivel 20 (también obtenible mediante crianza). En Esmeralda se elige en la Torre Espejismo (Ruta 111) y el otro fósil reaparece tras el Alto Mando en el Túnel del Desierto.',
            'locations': [
                {'area': 'Ciudad Férrica (Devon S.A.)', 'method': 'Revivir Fósil Garra al Nivel 20'},
                {'area': 'Ruta 111 (Torre Espejismo)', 'method': 'Obtención de Fósil Garra en la cima'},
                {'area': 'Ruta 114 (Túnel del Desierto)', 'method': 'Segundo fósil en el fondo del túnel tras el Alto Mando'},
                {'area': 'Ruta 117 (Guardería Pokémon)', 'method': 'Crianza de huevo'}
            ],
            'badge_color': 'amber',
            'badge_label': 'Fósil'
        },

        # Regalos y eventos de Hoenn
        349: {
            'type': 'wild',
            'summary': 'Pesca con Caña en exactamente 6 casillas aleatorias de agua en la Ruta 119 (también obtenible mediante crianza).',
            'locations': [
                {'area': 'Ruta 119', 'method': 'Pesca en casilla especial de Feebas'},
                {'area': 'Ruta 117 (Guardería Pokémon)', 'method': 'Crianza de huevo'}
            ]
        },
        351: {
            'type': 'gift',
            'summary': 'Regalo de los científicos en la 1.ª planta del Instituto Meteorológico (Ruta 119) tras rescatarlos del Equipo Magma (también obtenible mediante crianza).',
            'locations': [
                {'area': 'Ruta 119 (Instituto Meteorológico)', 'method': 'Regalo tras vencer al Equipo Magma'},
                {'area': 'Ruta 117 (Guardería Pokémon)', 'method': 'Crianza de huevo'}
            ]
        },
        360: {
            'type': 'gift',
            'summary': 'Huevo entregado por una anciana junto a las aguas termales de Pueblo Lavacalda. También salvaje en Isla Espejismo o criando a Wobbuffet con Incienso Suave en la Guardería.',
            'locations': [
                {'area': 'Pueblo Lavacalda (Aguas termales)', 'method': 'Huevo de regalo'},
                {'area': 'Ruta 117 (Guardería Pokémon)', 'method': 'Crianza de Wobbuffet equipado con Incienso Suave'},
                {'area': 'Isla Espejismo (Ruta 130)', 'method': 'Hierba alta (Isla aleatoria)'}
            ],
            'item_slug': 'lax-incense',
            'badge_color': 'emerald',
            'badge_label': 'Huevo Regalo'
        },
        374: {'type': 'gift', 'summary': 'Poké Ball dejada por Máximo Peñas en su casa de Ciudad Algaria tras vencer al Alto Mando (también obtenible mediante crianza).', 'locations': [{'area': 'Ciudad Algaria (Casa de Máximo)', 'method': 'Regalo de Máximo en el postgame'}, {'area': 'Ruta 117 (Guardería Pokémon)', 'method': 'Crianza de huevo'}]},

        # Crianza e Inciensos
        298: {
            'type': 'breeding',
            'summary': 'Criar a Marill o Azumarill equipado con Incienso Marino en la Guardería Pokémon (Ruta 117).',
            'locations': [{'area': 'Ruta 117 (Guardería Pokémon)', 'method': 'Crianza con Incienso Marino'}],
            'item_slug': 'sea-incense',
            'badge_color': 'pink',
            'badge_label': 'Crianza'
        },
        172: {
            'type': 'breeding',
            'summary': 'Criar a Pikachu o Raichu en la Guardería Pokémon (Ruta 117). Pikachu es capturable en la Zona Safari.',
            'locations': [{'area': 'Ruta 117 (Guardería Pokémon)', 'method': 'Crianza en Guardería'}],
            'badge_color': 'pink',
            'badge_label': 'Crianza'
        },
        174: {
            'type': 'breeding',
            'summary': 'Criar a Jigglypuff o Wigglytuff en la Guardería Pokémon (Ruta 117). Jigglypuff es capturable en la Ruta 115.',
            'locations': [{'area': 'Ruta 117 (Guardería Pokémon)', 'method': 'Crianza en Guardería'}],
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

        # Especiales capturables en Esmeralda (Frente de Batalla y Túnel del Desierto)
        185: {
            'type': 'wild',
            'summary': 'Árbol extraño en la esquina sudeste del Frente de Batalla que cobra vida al regarlo con el Cubo Wailmer (Nivel 40).',
            'locations': [{'area': 'Frente de Batalla (Árbol Sudowoodo)', 'method': 'Estático al Nivel 40 con Cubo Wailmer'}],
            'badge_color': 'amber',
            'badge_label': 'Estático'
        },
        132: {
            'type': 'wild',
            'summary': 'Salvaje en el Túnel del Desierto (acceso a través de la cueva del Fosilmaníaco en la Ruta 114 tras derrotar al Alto Mando).',
            'locations': [{'area': 'Ruta 114 (Túnel del Desierto)', 'method': 'Hierba alta / Suelo de cueva tras el Alto Mando'}],
            'badge_color': 'indigo',
            'badge_label': 'Salvaje Postgame'
        },
        235: {
            'type': 'wild',
            'summary': 'Salvaje en la Cueva Taller (Artisan Cave) en el Frente de Batalla (bajo la Cueva del Sudowoodo).',
            'locations': [
                {'area': 'Frente de Batalla (Cueva Taller)', 'method': 'Salvaje en Cueva Taller (P1 y S1)'},
                {'area': 'Cueva Cambiante (Ruta 103)', 'method': 'Evento e-Reader inactivo'}
            ],
            'badge_color': 'indigo',
            'badge_label': 'Salvaje Postgame'
        },

        # Regis
        377: {
            'type': 'legendary',
            'badge_label': 'Legendario',
            'badge_color': 'purple',
            'summary': 'Ruinas del Desierto en la Ruta 111 al Nivel 40 (requiere abrir la Cámara Sellada en la Ruta 134 con Relicanth primero y Wailord al final, y en las Ruinas dar 2 pasos a la izquierda, 2 abajo y usar Golpe Roca).',
            'locations': [{'area': 'Ruta 111 (Ruinas del Desierto)', 'method': 'Legendario estático (Nivel 40)'}]
        },
        378: {
            'type': 'legendary',
            'badge_label': 'Legendario',
            'badge_color': 'purple',
            'summary': 'Cueva Insular en la Ruta 105 al Nivel 40 (requiere abrir la Cámara Sellada en la Ruta 134 con Relicanth y Wailord, y en la Cueva Insular recorrer el perímetro de la sala en sentido horario pegado a la pared).',
            'locations': [{'area': 'Ruta 105 (Cueva Insular)', 'method': 'Legendario estático (Nivel 40)'}]
        },
        379: {
            'type': 'legendary',
            'badge_label': 'Legendario',
            'badge_color': 'purple',
            'summary': 'Tumba Antigua en la Ruta 120 al Nivel 40 (requiere abrir la Cámara Sellada en la Ruta 134 con Relicanth y Wailord, y en la Tumba Antigua situarse en el centro de la sala y usar Destello).',
            'locations': [{'area': 'Ruta 120 (Tumba Antigua)', 'method': 'Legendario estático (Nivel 40)'}]
        },

        # Legendarios Errantes de Hoenn (Latias / Latios)
        380: {
            'type': 'legendary',
            'badge_label': 'Legendario',
            'badge_color': 'purple',
            'summary': 'Legendario errante por todo Hoenn al Nivel 40 si eliges "Rojo" al hablar con tu madre en Villa Raíz tras vencer al Alto Mando. Si eliges "Azul", aparece en la Isla del Sur (Nivel 50 con Rocío Bondad) mediante el evento del Ticket Eón.',
            'locations': [
                {'area': 'Rutas de Hoenn (Errante)', 'method': 'Salvaje errante tras elegir Rojo en televisión'},
                {'area': 'Isla del Sur (Evento Ticket Eón)', 'method': 'Estático Nivel 50 si elegiste Azul'}
            ]
        },
        381: {
            'type': 'legendary',
            'badge_label': 'Legendario',
            'badge_color': 'purple',
            'summary': 'Legendario errante por todo Hoenn al Nivel 40 si eliges "Azul" al hablar con tu madre en Villa Raíz tras vencer al Alto Mando. Si eliges "Rojo", aparece en la Isla del Sur (Nivel 50 con Rocío Bondad) mediante el evento del Ticket Eón.',
            'locations': [
                {'area': 'Rutas de Hoenn (Errante)', 'method': 'Salvaje errante tras elegir Azul en televisión'},
                {'area': 'Isla del Sur (Evento Ticket Eón)', 'method': 'Estático Nivel 50 si elegiste Rojo'}
            ]
        },

        # Legendarios principales de Esmeralda
        382: {
            'type': 'legendary',
            'badge_label': 'Legendario',
            'badge_color': 'purple',
            'summary': 'Cueva Marina al Nivel 70 en el postgame. El científico del Instituto Meteorológico en la Ruta 119 te indicará en qué ruta marítima hay lluvias torrenciales para localizar la entrada con Buceo.',
            'locations': [{'area': 'Rutas marinas de Hoenn (Cueva Marina)', 'method': 'Legendario estático al Nivel 70 (Instituto Meteorológico)'}]
        },
        383: {
            'type': 'legendary',
            'badge_label': 'Legendario',
            'badge_color': 'purple',
            'summary': 'Cueva Terra al Nivel 70 en el postgame. El científico del Instituto Meteorológico en la Ruta 119 te indicará en qué ruta terrestre hay una sequía abrasadora para localizar la entrada a la caverna.',
            'locations': [{'area': 'Rutas terrestres de Hoenn (Cueva Terra)', 'method': 'Legendario estático al Nivel 70 (Instituto Meteorológico)'}]
        },
        384: {
            'type': 'legendary',
            'badge_label': 'Legendario de Portada',
            'badge_color': 'emerald',
            'summary': 'Cima del Pilar Celeste en la Ruta 131 al Nivel 70. Despierta durante el clímax de la historia para apaciguar el cataclismo entre Groudon y Kyogre en Arrecípolis, pudiendo capturarse antes o después del Alto Mando.',
            'locations': [{'area': 'Ruta 131 (Pilar Celeste - Cima)', 'method': 'Legendario estático de portada al Nivel 70'}]
        },

        # Míticos y Singulares
        385: {
            'type': 'gift',
            'badge_label': 'Mítico / Evento',
            'badge_color': 'purple',
            'summary': 'Pokémon singular de evento oficial. Obtenible mediante transferencia desde Pokémon Channel (PAL) o disco bonus de Pokémon Colosseum (NTSC) mediante cable GameCube-GBA, o distribuido en eventos presenciales oficiales de Nintendo.',
            'locations': [
                {'area': 'Pokémon Channel (Europa/Australia)', 'method': 'Transferencia externa (GameCube a GBA)'},
                {'area': 'Pokémon Colosseum Bonus Disc (América/Japón)', 'method': 'Transferencia externa (GameCube a GBA)'},
                {'area': 'Evento oficial de Nintendo', 'method': 'Distribución presencial directa'}
            ]
        },
        386: {
            'type': 'legendary',
            'badge_label': 'Mítico / Evento',
            'badge_color': 'purple',
            'summary': 'Isla Origen al Nivel 30 salvaje tras resolver el puzle del triángulo negro mediante el evento oficial del Ori-Ticket (Aurora Ticket). En Pokémon Esmeralda adopta su Forma Velocidad.',
            'locations': [{'area': 'Isla Origen (Evento Ori-Ticket)', 'method': 'Salvaje estático Nivel 30 (Forma Velocidad)'}]
        },
        151: {
            'type': 'legendary',
            'badge_label': 'Mítico / Evento',
            'badge_color': 'purple',
            'summary': 'Isla Suprema (Faraway Island) al Nivel 30 salvaje en la espesura de la selva mediante el evento oficial del Mapa Viejo (exclusivo de Pokémon Esmeralda).',
            'locations': [{'area': 'Isla Suprema (Evento Mapa Viejo)', 'method': 'Salvaje estático Nivel 30 en la hierba profunda'}]
        },
        249: {
            'type': 'legendary',
            'badge_label': 'Legendario / Evento',
            'badge_color': 'purple',
            'summary': 'Roca Ombligo (Navel Rock) en el fondo de la caverna al Nivel 70 mediante el evento oficial del Ticket Místico (Mystic Ticket).',
            'locations': [{'area': 'Roca Ombligo (Evento Ticket Místico)', 'method': 'Salvaje estático al Nivel 70'}]
        },
        250: {
            'type': 'legendary',
            'badge_label': 'Legendario / Evento',
            'badge_color': 'purple',
            'summary': 'Roca Ombligo (Navel Rock) en la cima de la caverna al Nivel 70 mediante el evento oficial del Ticket Místico (Mystic Ticket).',
            'locations': [{'area': 'Roca Ombligo (Evento Ticket Místico)', 'method': 'Salvaje estático al Nivel 70'}]
        },

        # Exclusivos de Rubí y Zafiro (Ausentes en estado salvaje en Esmeralda)
        283: {
            'type': 'trade',
            'badge_label': 'Exclusivo Rubí / Zafiro',
            'badge_color': 'indigo',
            'summary': 'Ausente en estado salvaje en Pokémon Esmeralda (Ruta 102). Requiere intercambio desde Pokémon Rubí o Pokémon Zafiro (también obtenible mediante crianza).',
            'locations': [
                {'area': 'Intercambio con Pokémon Rubí o Zafiro', 'method': 'Exclusivo de versión (Ruta 102 en R/Z)'},
                {'area': 'Ruta 117 (Guardería Pokémon)', 'method': 'Crianza de huevo'}
            ]
        },
        284: {
            'type': 'trade',
            'badge_label': 'Exclusivo Rubí / Zafiro',
            'badge_color': 'indigo',
            'summary': 'Ausente en estado salvaje en Pokémon Esmeralda. Evoluciona de Surskit al Nivel 22 (requiere intercambio desde Rubí o Zafiro).',
            'locations': [{'area': 'Intercambio con Pokémon Rubí o Zafiro', 'method': 'Evolución de Surskit transferido'}]
        },
        307: {
            'type': 'trade',
            'badge_label': 'Exclusivo Rubí / Zafiro',
            'badge_color': 'indigo',
            'summary': 'Ausente en estado salvaje en Pokémon Esmeralda (eliminado de Monte Pírico y Calle Victoria). Requiere intercambio desde Pokémon Rubí o Pokémon Zafiro (también obtenible mediante crianza).',
            'locations': [
                {'area': 'Intercambio con Pokémon Rubí o Zafiro', 'method': 'Exclusivo de versión (Monte Pírico en R/Z)'},
                {'area': 'Ruta 117 (Guardería Pokémon)', 'method': 'Crianza de huevo'}
            ]
        },
        308: {
            'type': 'trade',
            'badge_label': 'Exclusivo Rubí / Zafiro',
            'badge_color': 'indigo',
            'summary': 'Ausente en estado salvaje en Pokémon Esmeralda. Evoluciona de Meditite al Nivel 37 (requiere intercambio desde Rubí o Zafiro).',
            'locations': [{'area': 'Intercambio con Pokémon Rubí o Zafiro', 'method': 'Evolución de Meditite transferido'}]
        },
        315: {
            'type': 'trade',
            'badge_label': 'Exclusivo Rubí / Zafiro',
            'badge_color': 'indigo',
            'summary': 'Ausente en estado salvaje en Pokémon Esmeralda (eliminado de la Ruta 117). Requiere intercambio desde Pokémon Rubí o Pokémon Zafiro (también obtenible mediante crianza).',
            'locations': [
                {'area': 'Intercambio con Pokémon Rubí o Zafiro', 'method': 'Exclusivo de versión (Ruta 117 en R/Z)'},
                {'area': 'Ruta 117 (Guardería Pokémon)', 'method': 'Crianza de huevo'}
            ]
        },
        335: {
            'type': 'trade',
            'badge_label': 'Exclusivo Rubí',
            'badge_color': 'rose',
            'summary': 'Exclusivo de Pokémon Rubí (Ruta 114). Inaccesible en estado salvaje en Esmeralda; requiere intercambio con un jugador de Rubí (también obtenible mediante crianza).',
            'locations': [
                {'area': 'Intercambio con Pokémon Rubí', 'method': 'Exclusivo de versión (Ruta 114 en Rubí)'},
                {'area': 'Ruta 117 (Guardería Pokémon)', 'method': 'Crianza de huevo'}
            ]
        },
        337: {
            'type': 'trade',
            'badge_label': 'Exclusivo Zafiro',
            'badge_color': 'blue',
            'summary': 'Exclusivo de Pokémon Zafiro (Cascada Meteoro). Inaccesible en estado salvaje en Esmeralda; requiere intercambio con un jugador de Zafiro (también obtenible mediante crianza).',
            'locations': [
                {'area': 'Intercambio con Pokémon Zafiro', 'method': 'Exclusivo de versión (Cascada Meteoro en Zafiro)'},
                {'area': 'Ruta 117 (Guardería Pokémon)', 'method': 'Crianza de huevo'}
            ]
        },
    }

    BABY_NAMES = {
        'pichu', 'cleffa', 'igglybuff', 'togepi', 'tyrogue',
        'smoochum', 'elekid', 'magby', 'azurill', 'wynaut'
    }
    INCENSE_PARENTS_THAT_HATCH = {'marill', 'wobbuffet'}
    NON_BREEDABLE_NAMES = {
        'nidorina', 'nidoqueen', 'ditto', 'unown',
        'articuno', 'zapdos', 'moltres', 'mewtwo', 'mew',
        'raikou', 'entei', 'suicune', 'lugia', 'ho-oh', 'celebi',
        'regirock', 'regice', 'registeel', 'latias', 'latios',
        'kyogre', 'groudon', 'rayquaza', 'jirachi', 'deoxys'
    }

    # Hoenn regional set
    hoenn_entry_by_nat = {}
    for item in hoenn_pokedex_entries:
        hoenn_num = item['entry_number']
        sp_url = item['pokemon_species']['url']
        nat_num = int(sp_url.rstrip('/').split('/')[-1])
        hoenn_entry_by_nat[nat_num] = hoenn_num

    hoenn_sorted = sorted(hoenn_pokedex_entries, key=lambda x: x['entry_number'])
    national_sorted_ids = list(range(1, 387))

    STARTING_EMERALD_ID = 1979

    def build_entry(nat_id, entry_num, is_national=False):
        sp = species_386.get(str(nat_id))
        if not sp:
            raise ValueError(f"Faltan datos de la especie {nat_id}")

        flavor = wikidex_descriptions.get(str(nat_id), "")
        sp_name = sp['name'].lower()
        evo_info = evo_map.get(sp_name)
        egg_groups = sp.get('egg_groups', [])

        is_baby = sp_name in BABY_NAMES
        is_incense_parent = sp_name in INCENSE_PARENTS_THAT_HATCH
        is_evolution = (evo_info is not None) and not is_incense_parent
        is_genderless = (sp.get('gender_rate') == -1) and not is_baby

        # Regla Canónica de Crianza Pokémon:
        # SOLO eclosionan de huevos las primeras etapas (formas base), especies de etapa única (sin evoluciones),
        # bebés Pokémon (fruto de criar a sus formas evolucionadas) y excepciones de incienso en Gen 3 (Marill y Wobbuffet).
        # Las formas evolucionadas (Grovyle, Mightyena, etc.), Legendarios/Míticos, Unown y Ditto NUNCA eclosionan de un huevo.
        if sp_name in NON_BREEDABLE_NAMES:
            is_hatchable = False
        elif ('no-eggs' in egg_groups) and not is_baby:
            is_hatchable = False
        elif is_baby or is_incense_parent:
            is_hatchable = True
        elif is_evolution:
            is_hatchable = False
        else:
            is_hatchable = True

        # Localizaciones crudas de PokeAPI para Esmeralda
        locs_raw = encounters_emerald.get(str(nat_id), [])
        unique_locs = []
        seen_areas = set()
        for l in locs_raw:
            raw_area = l.get('area_raw') or l.get('location')
            area_translated = HOENN_AREAS_ES.get(raw_area, l.get('area_es', raw_area))
            raw_method = l.get('method_raw') or l.get('method')
            method_translated = METHOD_NAMES_ES.get(raw_method, l.get('method_es', raw_method))
            k = (area_translated, method_translated)
            if k not in seen_areas:
                seen_areas.add(k)
                unique_locs.append({'area': area_translated, 'method': method_translated})

        is_in_hoenn = nat_id in hoenn_entry_by_nat

        obt_info = {}
        if nat_id in SPECIAL_OBT_EMERALD:
            obt_info = copy.deepcopy(SPECIAL_OBT_EMERALD[nat_id])
        elif nat_id in INGAME_TRADES_EMERALD:
            obt_info = copy.deepcopy(INGAME_TRADES_EMERALD[nat_id])
            if unique_locs:
                obt_info['locations'] = unique_locs + obt_info['locations']
        elif unique_locs:
            true_wild_locs = [l for l in unique_locs if 'colosseum' not in l.get('method', '').lower()]
            if not true_wild_locs:
                true_wild_locs = unique_locs

            num_wild = len(true_wild_locs)
            if num_wild == 1:
                summary = f"Salvaje en {true_wild_locs[0]['area']}."
            elif 2 <= num_wild <= 3:
                areas_str = ", ".join([l['area'] for l in true_wild_locs])
                summary = f"Salvaje en: {areas_str}."
            else:
                areas_str = ", ".join([l['area'] for l in true_wild_locs[:3]])
                summary = f"Salvaje en {num_wild} zonas (ej: {areas_str})."

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
                'summary': "Obtenible en la región de Hoenn.",
                'locations': []
            }
        else:
            # Pokémon no nativo de Hoenn (Pokédex Nacional de Esmeralda)
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
            elif is_hatchable:
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

        # Regla Universal de Crianza: Solo aplicable si la especie PUEDE nacer de un huevo (is_hatchable).
        # NUNCA a formas evolucionadas como Grovyle, Mightyena, etc.
        if is_hatchable:
            has_daycare = any('guardería' in l.get('area', '').lower() or 'crianza' in l.get('method', '').lower() for l in obt_info.get('locations', []))
            if not has_daycare:
                if sp_name == 'azurill':
                    method_str = 'Crianza con Incienso Marino'
                elif sp_name == 'wynaut':
                    method_str = 'Crianza con Incienso Suave'
                else:
                    method_str = 'Crianza de huevo'
                
                obt_info.setdefault('locations', []).append({
                    'area': 'Ruta 117 (Guardería Pokémon)',
                    'method': method_str
                })
            
            summ = obt_info.get('summary', '')
            summ_lower = summ.lower()
            if 'crianza' not in summ_lower and 'huevo' not in summ_lower and 'criar' not in summ_lower and 'eclosi' not in summ_lower:
                c_phrase = 'también obtenible mediante crianza'
                if summ.endswith(').'):
                    obt_info['summary'] = summ[:-2] + f", {c_phrase})."
                elif summ.endswith('.'):
                    obt_info['summary'] = summ[:-1] + f" ({c_phrase})."
                else:
                    obt_info['summary'] = summ + f" ({c_phrase})."

        # Especies con evento e-Reader programado internamente en Cueva Cambiante (evento inactivo)
        if nat_id in [179, 190, 204, 213, 216, 228, 234, 235]:
            has_altering = any('cueva cambiante' in l.get('area', '').lower() for l in obt_info.get('locations', []))
            if not has_altering:
                obt_info.setdefault('locations', []).append({
                    'area': 'Cueva Cambiante (Ruta 103)',
                    'method': 'Evento e-Reader inactivo'
                })

        # Piedra evolutiva u objeto especial / incienso de crianza
        evo_stone = None
        item_slug_to_resolve = (evo_info.get('item_slug') if evo_info else None) or obt_info.get('item_slug')
        if item_slug_to_resolve:
            evo_stone = resolve_evolution_stone(item_slug=item_slug_to_resolve, game_slug="emerald")

        if evo_info and 'evolution_info' not in obt_info:
            obt_info['evolution_info'] = evo_info

        type_badge_colors = {
            'starter': ('amber', 'Inicial'),
            'fossil': ('amber', 'Fósil'),
            'gift': ('emerald', 'Regalo'),
            'breeding': ('pink', 'Crianza'),
            'evolution': ('indigo', 'Evolución'),
            'trade': ('indigo', 'Intercambio'),
            'wild': ('emerald', 'Salvaje'),
            'legendary': ('purple', 'Legendario'),
            'special': ('sky', 'Especial'),
            'transfer': ('slate', 'Transferencia')
        }
        b_color, b_label = type_badge_colors.get(obt_info.get('type', 'wild'), ('emerald', 'Salvaje'))
        if 'badge_color' not in obt_info:
            obt_info['badge_color'] = b_color
        if 'badge_label' not in obt_info:
            obt_info['badge_label'] = b_label

        p_type = sp['primary_type']
        s_type = sp['secondary_type']

        pc_icon_url = f"/media/pokemon/icons/gen3/{nat_id}.png"
        if nat_id == 201:
            pc_icon_url = "/media/pokemon/icons/gen3/201-f.png"
        elif nat_id == 386:
            pc_icon_url = "/media/pokemon/icons/gen3/10003.png"

        sprite_suffix = "386-speed" if nat_id == 386 else str(nat_id)
        return {
            "id": STARTING_EMERALD_ID + (nat_id - 1),
            "entry_number": entry_num,
            "game_slug": "emerald",
            "pokemon": {
                "national_number": nat_id,
                "name": sp['name'],
                "display_name": sp['display_name'],
                "category": sp.get('category', ''),
                "height": sp.get('height', 0),
                "weight": sp.get('weight', 0),
                "sprite_url": f"/media/pokemon/artwork/{nat_id}.png",
                "sprite_shiny_url": None,
                "artwork_shiny_url": f"/media/pokemon/artwork/shiny/{nat_id}.png",
                "primary_type": p_type,
                "secondary_type": s_type
            },
            "primary_type": p_type,
            "primary_type_display": p_type.capitalize(),
            "primary_type_es": TYPE_NAMES_ES.get(p_type, p_type.capitalize()),
            "secondary_type": s_type,
            "secondary_type_display": s_type.capitalize() if s_type else "",
            "secondary_type_es": TYPE_NAMES_ES.get(s_type, s_type.capitalize()) if s_type else "",
            "game_sprite_url": f"/media/pokemon/sprites/emerald/{sprite_suffix}.png",
            "game_sprite_shiny_url": f"/media/pokemon/sprites/emerald_shiny/{sprite_suffix}.png",
            "game_sprite_back_url": f"/media/pokemon/sprites/emerald/back/{sprite_suffix}.png",
            "game_sprite_shiny_back_url": f"/media/pokemon/sprites/emerald_shiny/back/{sprite_suffix}.png",
            "modern_sprite_shiny_url": f"/media/pokemon/artwork/shiny/{nat_id}.png",
            "modal_retro_sprite_url": f"/media/pokemon/sprites/emerald_animated/{sprite_suffix}.gif",
            "modal_retro_sprite_shiny_url": f"/media/pokemon/sprites/emerald_animated_shiny/{sprite_suffix}.gif",
            "modal_retro_sprite_back_url": f"/media/pokemon/sprites/emerald/back/{sprite_suffix}.png",
            "modal_retro_sprite_shiny_back_url": f"/media/pokemon/sprites/emerald_shiny/back/{sprite_suffix}.png",
            "pc_icon_url": pc_icon_url,
            "cry_url": f"/media/pokemon/cries/{nat_id}.ogg",
            "flavor_text": flavor,
            "obtaining_info": obt_info,
            "evolution_stone": evo_stone,
            "game_data": {
                "generation": 3,
                "game_slug": "emerald",
                "game_name": "Pokémon Esmeralda",
                "is_regional": not is_national
            }
        }

    # 1. Compilar Pokédex Regional de Hoenn (202 Pokémon)
    regional_catalog = []
    for item in hoenn_sorted:
        hoenn_num = item['entry_number']
        nat_num = int(item['pokemon_species']['url'].rstrip('/').split('/')[-1])
        entry = build_entry(nat_num, hoenn_num, is_national=False)
        regional_catalog.append(entry)

    with open(CATALOGS_DIR / "emerald.json", "w", encoding="utf-8") as f:
        json.dump(regional_catalog, f, ensure_ascii=False, indent=2)
    print(f"[OK] emerald.json generado con {len(regional_catalog)} entradas (Pokédex Regional de Hoenn)")

    # 2. Compilar Pokédex Nacional (386 Pokémon)
    national_catalog = []
    for nat_id in national_sorted_ids:
        entry = build_entry(nat_id, nat_id, is_national=True)
        national_catalog.append(entry)

    with open(CATALOGS_DIR / "emerald_national.json", "w", encoding="utf-8") as f:
        json.dump(national_catalog, f, ensure_ascii=False, indent=2)
    print(f"[OK] emerald_national.json generado con {len(national_catalog)} entradas (Pokédex Nacional)")


if __name__ == '__main__':
    main()
