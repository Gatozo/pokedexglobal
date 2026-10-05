"""
Script para compilar los catálogos oficiales de Pokémon Verde Hoja (Gen 3):
1. leafgreen.json (Pokédex Regional de Kanto: 151 Pokémon, numeración 1 a 151)
2. leafgreen_national.json (Pokédex Nacional de Verde Hoja: 386 Pokémon, numeración 1 a 386)

Descarga o carga de caché:
- Textos de Pokédex oficiales en español desde WikiDex API (wikidex_leafgreen_descriptions.json).
- Encuentros y rutas en español oficial para Kanto y las Islas Sétima en Verde Hoja (encounters_leafgreen.json).
- Métodos especiales de obtención, intercambios NPC exclusivos de Verde Hoja, crianza en Isla Quarta y transferencias externas.
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

# Traducción oficial de áreas de Kanto y de las Islas Sétima en Verde Hoja
KANTO_SEVII_AREAS_ES = {
    # Rutas terrestres y marítimas de Kanto
    'kanto-route-1-area': 'Ruta 1',
    'kanto-route-2-north-towards-pewter-city': 'Ruta 2 (Norte)',
    'kanto-route-2-south-towards-viridian-city': 'Ruta 2 (Sur)',
    'kanto-route-3-area': 'Ruta 3',
    'kanto-route-3-pokemon-center': 'Ruta 3 (Centro Pokémon)',
    'kanto-route-4-area': 'Ruta 4',
    'kanto-route-4-pokemon-center': 'Ruta 4 (Centro Pokémon)',
    'kanto-route-5-area': 'Ruta 5',
    'kanto-route-6-area': 'Ruta 6',
    'kanto-route-7-area': 'Ruta 7',
    'kanto-route-8-area': 'Ruta 8',
    'kanto-route-9-area': 'Ruta 9',
    'kanto-route-10-area': 'Ruta 10',
    'kanto-route-11-area': 'Ruta 11',
    'kanto-route-12-area': 'Ruta 12',
    'kanto-route-13-area': 'Ruta 13',
    'kanto-route-14-area': 'Ruta 14',
    'kanto-route-15-area': 'Ruta 15',
    'kanto-route-16-area': 'Ruta 16',
    'kanto-route-17-area': 'Ruta 17 (Camino de Bicis)',
    'kanto-route-18-area': 'Ruta 18',
    'kanto-sea-route-19-area': 'Ruta 19 (Ruta Marítima)',
    'kanto-sea-route-20-area': 'Ruta 20 (Ruta Marítima)',
    'kanto-sea-route-21-area': 'Ruta 21 (Ruta Marítima)',
    'kanto-route-22-area': 'Ruta 22',
    'kanto-route-23-area': 'Ruta 23',
    'kanto-route-24-area': 'Ruta 24 (Puente Pepita)',
    'kanto-route-25-area': 'Ruta 25',
    'roaming-kanto-area': 'Rutas de Kanto (Errante)',

    # Ciudades y Edificios de Kanto
    'pallet-town-area': 'Pueblo Paleta',
    'viridian-city-area': 'Ciudad Verde',
    'cerulean-city-area': 'Ciudad Celeste',
    'vermilion-city-area': 'Ciudad Carmín',
    'ss-anne-area': 'S.S. Anne (Barco)',
    'celadon-city-area': 'Ciudad Azulona',
    'celadon-city-celadon-mansion': 'Mansión Azulona',
    'celadon-city-prize-corner': 'Casino de Ciudad Azulona',
    'saffron-city-fighting-dojo': 'Ciudad Azafrán (Dojo Kárate)',
    'saffron-city-silph-co-7f': 'Silph S.A. (Planta 7)',
    'fuchsia-city-area': 'Ciudad Fucsia',
    'cinnabar-island-area': 'Isla Canela',
    'cinnabar-island-cinnabar-lab': 'Isla Canela (Laboratorio)',
    'kanto-pokecenter-area': 'Centro Pokémon (Transferencia GameCube)',

    # Mazmorras y Cuevas de Kanto
    'viridian-forest-area': 'Bosque Verde',
    'digletts-cave-area': 'Cueva Diglett',
    'mt-moon-1f': 'Monte Moon (P1)',
    'mt-moon-b1f': 'Monte Moon (S1)',
    'mt-moon-b2f': 'Monte Moon (S2)',
    'rock-tunnel-1f': 'Túnel Roca (P1)',
    'rock-tunnel-b1f': 'Túnel Roca (S1)',
    'kanto-power-plant-area': 'Central de Energía',
    'pokemon-tower-3f': 'Torre Pokémon (P3)',
    'pokemon-tower-4f': 'Torre Pokémon (P4)',
    'pokemon-tower-5f': 'Torre Pokémon (P5)',
    'pokemon-tower-6f': 'Torre Pokémon (P6)',
    'pokemon-tower-7f': 'Torre Pokémon (P7)',
    'kanto-safari-zone-middle': 'Zona Safari (Centro)',
    'kanto-safari-zone-area-1-east': 'Zona Safari (Área 1 Este)',
    'kanto-safari-zone-area-2-north': 'Zona Safari (Área 2 Norte)',
    'kanto-safari-zone-area-3-west': 'Zona Safari (Área 3 Oeste)',
    'seafoam-islands-1f': 'Islas Espuma (P1)',
    'seafoam-islands-b1f': 'Islas Espuma (S1)',
    'seafoam-islands-b2f': 'Islas Espuma (S2)',
    'seafoam-islands-b3f': 'Islas Espuma (S3)',
    'seafoam-islands-b4f': 'Islas Espuma (S4)',
    'pokemon-mansion-1f': 'Mansión Pokémon (P1)',
    'pokemon-mansion-2f': 'Mansión Pokémon (P2)',
    'pokemon-mansion-3f': 'Mansión Pokémon (P3)',
    'pokemon-mansion-b1f': 'Mansión Pokémon (S1)',
    'kanto-victory-road-1-1f': 'Calle Victoria (P1)',
    'kanto-victory-road-1-2f': 'Calle Victoria (P2)',
    'kanto-victory-road-1-3f': 'Calle Victoria (P3)',
    'cerulean-cave-1f': 'Cueva Celeste (P1)',
    'cerulean-cave-2f': 'Cueva Celeste (P2)',
    'cerulean-cave-b1f': 'Cueva Celeste (S1)',

    # Archipiélago Sétima (Islas Sete)
    'one-island-area': 'Isla Prima (Pueblo)',
    'kindle-road-area': 'Camino Candente (Isla Prima)',
    'treasure-beach-area': 'Playa Tesoro (Isla Prima)',
    'mt-ember-outside': 'Monte Ascuas (Exterior)',
    'mt-ember-summit': 'Monte Ascuas (Cima)',
    'mt-ember-inside': 'Monte Ascuas (Interior)',

    'two-island-area': 'Isla Secunda (Pueblo)',
    'cape-brink-area': 'Cabo Extremo (Isla Secunda)',

    'three-island-area': 'Isla Tera (Pueblo)',
    'bond-bridge-area': 'Puente Unión (Isla Tera)',
    'berry-forest-area': 'Bosque Baya (Isla Tera)',
    'three-isle-port-area': 'Puerto Tri-Isla (Isla Tera)',

    'four-island-area': 'Isla Quarta (Pueblo)',
    'icefall-cave-front': 'Cueva Glaciada (Entrada)',
    'icefall-cave-inner': 'Cueva Glaciada (Interior)',
    'icefall-cave-back': 'Cueva Glaciada (Fondo)',

    'five-island-area': 'Isla Inta (Pueblo)',
    'five-isle-meadow-area': 'Prado Isla Inta (Isla Inta)',
    'memorial-pillar-area': 'Pilar Recuerdo (Isla Inta)',
    'water-labyrinth-area': 'Laberinto de Agua (Isla Inta)',
    'resort-gorgeous-area': 'Lugar de Recreo (Isla Inta)',
    'lost-cave-room-1': 'Cueva Perdida (Sala 1)',
    'lost-cave-room-2': 'Cueva Perdida (Sala 2)',
    'lost-cave-room-3': 'Cueva Perdida (Sala 3)',
    'lost-cave-room-4': 'Cueva Perdida (Sala 4)',
    'lost-cave-room-5': 'Cueva Perdida (Sala 5)',
    'lost-cave-room-6': 'Cueva Perdida (Sala 6)',
    'lost-cave-room-7': 'Cueva Perdida (Sala 7)',
    'lost-cave-room-8': 'Cueva Perdida (Sala 8)',
    'lost-cave-room-9': 'Cueva Perdida (Sala 9)',
    'lost-cave-room-10': 'Cueva Perdida (Sala 10)',
    'lost-cave-item-rooms': 'Cueva Perdida (Salas Ocultas)',

    'green-path-area': 'Vía Verde (Isla Exta)',
    'water-path-area': 'Vía Acuática (Isla Exta)',
    'ruin-valley-area': 'Valle Ruinas (Isla Exta)',
    'outcast-island-area': 'Isla Intempesta (Isla Exta)',
    'pattern-bush-area': 'Bosque Recinto (Isla Exta)',
    'kanto-altering-cave-a': 'Cueva Cambiante (Isla Exta)',
    'kanto-altering-cave-b': 'Cueva Cambiante (Isla Exta)',
    'kanto-altering-cave-c': 'Cueva Cambiante (Isla Exta)',
    'kanto-altering-cave-d': 'Cueva Cambiante (Isla Exta)',
    'kanto-altering-cave-e': 'Cueva Cambiante (Isla Exta)',
    'kanto-altering-cave-f': 'Cueva Cambiante (Isla Exta)',
    'kanto-altering-cave-g': 'Cueva Cambiante (Isla Exta)',
    'kanto-altering-cave-h': 'Cueva Cambiante (Isla Exta)',
    'kanto-altering-cave-i': 'Cueva Cambiante (Isla Exta)',

    'trainer-tower-area': 'Torre Desafío (Isla Sétima)',
    'canyon-entrance-area': 'Entrada al Cañón (Isla Sétima)',
    'sevault-canyon-area': 'Cañón Sétano (Isla Sétima)',
    'tanoby-ruins-area': 'Ruinas Sete (Isla Sétima)',
    'monean-chamber-area': 'Cámara Anémuna (Ruinas Sete)',
    'liptoo-chamber-area': 'Cámara Tulipdos (Ruinas Sete)',
    'weepth-chamber-area': 'Cámara Trisante (Ruinas Sete)',
    'dilford-chamber-area': 'Cámara Quarciso (Ruinas Sete)',
    'scufib-chamber-area': 'Cámara Seiris (Ruinas Sete)',
    'rixy-chamber-area': 'Cámara Hibinca (Ruinas Sete)',
    'viapos-chamber-area': 'Cámara Pasiete (Ruinas Sete)',

    # Islas de Evento Mítico
    'navel-rock-area': 'Roca Ombligo (Ticket Místico)',
    'birth-island-area': 'Isla Origen (Ori-Ticket / Deoxys)'
}

# Traducción de métodos de encuentro
METHOD_NAMES_ES = {
    'walk': 'Hierba alta / Terreno',
    'surf': 'Surfeando (Agua)',
    'old-rod': 'Caña Vieja',
    'good-rod': 'Caña Buena',
    'super-rod': 'Supercaña',
    'rock-smash': 'Golpe Roca',
    'cave': 'Cueva',
    'gift': 'Regalo',
    'trade': 'Intercambio',
    'gift-egg': 'Huevo de regalo',
    'static': 'Encuentro estático',
    'roaming-grass': 'Legendario errante (Hierba)',
    'roaming-water': 'Legendario errante (Agua)',
    'headbutt': 'Golpe Cabeza',
    'colosseum-bonus-disc-jpn': 'Disco Bonus Colosseum (Japón)'
}

EVO_ITEMS_ES = {
    'fire-stone': 'Piedra Fuego',
    'water-stone': 'Piedra Agua',
    'thunder-stone': 'Piedra Trueno',
    'leaf-stone': 'Piedra Hoja',
    'moon-stone': 'Piedra Lunar',
    'sun-stone': 'Piedra Solar',
    'kings-rock': 'Roca del Rey',
    'metal-coat': 'Revestimiento Metálico',
    'dragon-scale': 'Escama Dragón',
    'up-grade': 'Mejora',
    'deep-sea-tooth': 'Diente Marino',
    'deep-sea-scale': 'Escama Marina',
    'sea-incense': 'Incienso Marino',
    'lax-incense': 'Incienso Suave'
}


def build_catalogs():
    print("Compilando catálogos oficiales de Pokémon Verde Hoja...")

    with open(CACHE_DIR / "pokemon_386_species.json", "r", encoding="utf-8") as f:
        species_386 = json.load(f)

    with open(CACHE_DIR / "wikidex_leafgreen_descriptions.json", "r", encoding="utf-8") as f:
        wikidex_descriptions = json.load(f)

    with open(CACHE_DIR / "encounters_leafgreen.json", "r", encoding="utf-8") as f:
        encounters_leafgreen = json.load(f)

    with open(BASE_DIR / "tracker" / "data" / "evolution_stones.json", "r", encoding="utf-8") as f:
        stones_catalog = json.load(f)

    with open(CACHE_DIR / "evolution_chains.json", "r", encoding="utf-8") as f:
        evo_chains_raw = json.load(f)

    valid_gen3_names = {sp['name'].lower() for sp in species_386.values()}

    evo_map = {}
    for chain_id, chain_data in evo_chains_raw.items():
        chain = chain_data.get('chain', {})
        def parse_chain(node, from_name=None):
            curr_name = node.get('species', {}).get('name', '').lower()
            if curr_name not in valid_gen3_names:
                return

            evo_details = node.get('evolution_details', [])
            if evo_details and from_name and from_name in valid_gen3_names:
                det = evo_details[0]
                trigger = det.get('trigger', {}).get('name', 'level-up')
                min_level = det.get('min_level')
                item = det.get('item', {}).get('name') if det.get('item') else None
                held_item = det.get('held_item', {}).get('name') if det.get('held_item') else None
                min_happiness = det.get('min_happiness')
                time_of_day = det.get('time_of_day', '')
                min_beauty = det.get('min_beauty')

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
                    cond = "Subir de nivel con 170+ de Belleza (requiere transferencia a Rubí, Zafiro o Esmeralda para darle Pokécubos)"
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

    # Intercambios canónicos con NPCs en Pokémon Verde Hoja
    INGAME_TRADES_LEAFGREEN = {
        32: {
            'type': 'trade_npc',
            'badge_label': 'Intercambio NPC',
            'badge_color': 'indigo',
            'summary': 'Intercambio en la caseta de la Ruta 5: entrega un Nidoran♀ a cambio de Nidoran♂ (con el mote «Nidrán») (también obtenible mediante crianza).',
            'locations': [{'area': 'Ruta 5 (Caseta)', 'method': 'Intercambio por Nidoran♀'}, {'area': 'Isla Quarta (Guardería Pokémon)', 'method': 'Crianza de huevo'}]
        },
        33: {
            'type': 'trade_npc',
            'badge_label': 'Intercambio NPC',
            'badge_color': 'indigo',
            'summary': 'Intercambio en la caseta de la Ruta 11: entrega un Nidorina a cambio de Nidorino (con el mote «Nidrino»).',
            'locations': [{'area': 'Ruta 11 (Caseta)', 'method': 'Intercambio por Nidorina'}]
        },
        83: {
            'type': 'trade_npc',
            'badge_label': 'Intercambio NPC',
            'badge_color': 'indigo',
            'summary': 'Intercambio en Ciudad Carmín: entrega un Spearow a cambio de Farfetch\'d (con el mote «Farfi») (también obtenible mediante crianza).',
            'locations': [{'area': 'Ciudad Carmín', 'method': 'Intercambio por Spearow'}, {'area': 'Isla Quarta (Guardería Pokémon)', 'method': 'Crianza de huevo'}]
        },
        86: {
            'type': 'trade_npc',
            'badge_label': 'Intercambio NPC',
            'badge_color': 'indigo',
            'summary': 'Intercambio en el Laboratorio de Isla Canela: entrega un Ponyta a cambio de Seel (con el mote «Sailor») (también salvaje en Islas Espuma y Cueva Glaciada o mediante crianza).',
            'locations': [{'area': 'Isla Canela (Laboratorio)', 'method': 'Intercambio por Ponyta'}, {'area': 'Isla Quarta (Guardería Pokémon)', 'method': 'Crianza de huevo'}]
        },
        101: {
            'type': 'trade_npc',
            'badge_label': 'Intercambio NPC',
            'badge_color': 'indigo',
            'summary': 'Intercambio en el Laboratorio de Isla Canela: entrega un Raichu a cambio de Electrode (con el mote «Doris») (también salvaje en Central de Energía y Cueva Celeste).',
            'locations': [{'area': 'Isla Canela (Laboratorio)', 'method': 'Intercambio por Raichu'}]
        },
        108: {
            'type': 'trade_npc',
            'badge_label': 'Intercambio NPC',
            'badge_color': 'indigo',
            'summary': 'Intercambio en la caseta de la Ruta 18: entrega un Slowbro a cambio de Lickitung (con el mote «Lickitito») (también obtenible mediante crianza).',
            'locations': [{'area': 'Ruta 18 (Caseta)', 'method': 'Intercambio por Slowbro'}, {'area': 'Isla Quarta (Guardería Pokémon)', 'method': 'Crianza de huevo'}]
        },
        114: {
            'type': 'trade_npc',
            'badge_label': 'Intercambio NPC',
            'badge_color': 'indigo',
            'summary': 'Intercambio en el Laboratorio de Isla Canela: entrega un Venonat a cambio de Tangela (con el mote «Tangeny») (también salvaje en Ruta 21 y Playa Tesoro o mediante crianza).',
            'locations': [{'area': 'Isla Canela (Laboratorio)', 'method': 'Intercambio por Venonat'}, {'area': 'Isla Quarta (Guardería Pokémon)', 'method': 'Crianza de huevo'}]
        },
        122: {
            'type': 'trade_npc',
            'badge_label': 'Intercambio NPC',
            'badge_color': 'indigo',
            'summary': 'Intercambio en la caseta de la Ruta 2: entrega un Abra a cambio de Mr. Mime (con el mote «Mimien») (también obtenible mediante crianza).',
            'locations': [{'area': 'Ruta 2 (Caseta)', 'method': 'Intercambio por Abra'}, {'area': 'Isla Quarta (Guardería Pokémon)', 'method': 'Crianza de huevo'}]
        },
        124: {
            'type': 'trade_npc',
            'badge_label': 'Intercambio NPC',
            'badge_color': 'indigo',
            'summary': 'Intercambio en Ciudad Celeste: entrega un Poliwhirl a cambio de Jynx (con el mote «Zynx») (también obtenible mediante crianza).',
            'locations': [{'area': 'Ciudad Celeste', 'method': 'Intercambio por Poliwhirl'}, {'area': 'Isla Quarta (Guardería Pokémon)', 'method': 'Crianza de huevo'}]
        },
    }

    # Tratamientos especiales de obtención en Verde Hoja
    SPECIAL_OBT_LEAFGREEN = {
        # Iniciales de Kanto
        1: {
            'type': 'starter',
            'badge_label': 'Inicial',
            'badge_color': 'emerald',
            'summary': 'Elegir en la mesa del Profesor Oak en su Laboratorio de Pueblo Paleta (también obtenible mediante crianza).',
            'locations': [{'area': 'Pueblo Paleta (Laboratorio Oak)', 'method': 'Elección de Inicial de Kanto'}, {'area': 'Isla Quarta (Guardería Pokémon)', 'method': 'Crianza de huevo'}]
        },
        4: {
            'type': 'starter',
            'badge_label': 'Inicial',
            'badge_color': 'orange',
            'summary': 'Elegir en la mesa del Profesor Oak en su Laboratorio de Pueblo Paleta (también obtenible mediante crianza).',
            'locations': [{'area': 'Pueblo Paleta (Laboratorio Oak)', 'method': 'Elección de Inicial de Kanto'}, {'area': 'Isla Quarta (Guardería Pokémon)', 'method': 'Crianza de huevo'}]
        },
        7: {
            'type': 'starter',
            'badge_label': 'Inicial',
            'badge_color': 'blue',
            'summary': 'Elegir en la mesa del Profesor Oak en su Laboratorio de Pueblo Paleta (también obtenible mediante crianza).',
            'locations': [{'area': 'Pueblo Paleta (Laboratorio Oak)', 'method': 'Elección de Inicial de Kanto'}, {'area': 'Isla Quarta (Guardería Pokémon)', 'method': 'Crianza de huevo'}]
        },

        # Premios y compras
        106: {
            'type': 'gift',
            'badge_label': 'Premio Dojo',
            'badge_color': 'amber',
            'summary': 'Elegir entre Hitmonlee o Hitmonchan tras vencer al Maestro del Dojo Kárate en Ciudad Azafrán (también obtenible mediante crianza).',
            'locations': [{'area': 'Ciudad Azafrán (Dojo Kárate)', 'method': 'Premio tras vencer al Maestro del Dojo'}, {'area': 'Isla Quarta (Guardería Pokémon)', 'method': 'Crianza de huevo'}]
        },
        107: {
            'type': 'gift',
            'badge_label': 'Premio Dojo',
            'badge_color': 'amber',
            'summary': 'Elegir entre Hitmonlee o Hitmonchan tras vencer al Maestro del Dojo Kárate en Ciudad Azafrán (también obtenible mediante crianza).',
            'locations': [{'area': 'Ciudad Azafrán (Dojo Kárate)', 'method': 'Premio tras vencer al Maestro del Dojo'}, {'area': 'Isla Quarta (Guardería Pokémon)', 'method': 'Crianza de huevo'}]
        },
        129: {
            'type': 'gift',
            'badge_label': 'Comprado / Salvaje',
            'badge_color': 'blue',
            'summary': 'Comprado al vendedor ambulante en el Centro Pokémon de la Ruta 4 por 500₽, o salvaje pescando en cualquier masa de agua de Kanto y las Islas Sétima con Caña Vieja o Caña Buena (también obtenible mediante crianza).',
            'locations': [
                {'area': 'Ruta 4 (Centro Pokémon)', 'method': 'Comprado por 500₽'},
                {'area': 'Cualquier masa de agua (Kanto e Islas Sétima)', 'method': 'Pesca con Caña Vieja o Buena'},
                {'area': 'Isla Quarta (Guardería Pokémon)', 'method': 'Crianza de huevo'}
            ]
        },
        131: {
            'type': 'gift',
            'badge_label': 'Regalo Silph',
            'badge_color': 'blue',
            'summary': 'Regalo de un empleado en la 7.ª planta de Silph S.A. en Ciudad Azafrán mientras es asaltada por el Team Rocket (también salvaje en Cueva Glaciada o mediante crianza).',
            'locations': [{'area': 'Ciudad Azafrán (Silph S.A. P7)', 'method': 'Regalo de empleado de Silph S.A.'}, {'area': 'Cueva Glaciada (Isla Quarta)', 'method': 'Surfeando (Agua)'}, {'area': 'Isla Quarta (Guardería Pokémon)', 'method': 'Crianza de huevo'}]
        },
        133: {
            'type': 'gift',
            'badge_label': 'Regalo',
            'badge_color': 'amber',
            'summary': 'Poké Ball en la azotea de la Mansión Azulona en Ciudad Azulona entrando por la parte trasera (también obtenible mediante crianza).',
            'locations': [{'area': 'Ciudad Azulona (Mansión Azulona)', 'method': 'Poké Ball en el ático'}, {'area': 'Isla Quarta (Guardería Pokémon)', 'method': 'Crianza de huevo'}]
        },
        137: {
            'type': 'game_corner',
            'badge_label': 'Casino Azulona',
            'badge_color': 'pink',
            'summary': 'Canjeable en el Casino de Ciudad Azulona por 9.999 fichas.',
            'locations': [{'area': 'Casino de Ciudad Azulona', 'method': 'Premio por 9.999 fichas'}]
        },
        143: {
            'type': 'static',
            'badge_label': 'Estático Único',
            'badge_color': 'slate',
            'summary': 'Aparición estática única bloqueando el paso en la Ruta 12 y en la Ruta 16. Despiértalo tocando la Poké Flauta (también obtenible mediante crianza).',
            'locations': [{'area': 'Ruta 12', 'method': 'Despertar con Poké Flauta'}, {'area': 'Ruta 16', 'method': 'Despertar con Poké Flauta'}, {'area': 'Isla Quarta (Guardería Pokémon)', 'method': 'Crianza de huevo'}]
        },

        # Fósiles de Kanto
        138: {
            'type': 'fossil',
            'badge_label': 'Fósil Helix',
            'badge_color': 'amber',
            'summary': 'Revivir el Fósil Helix en el Laboratorio de Isla Canela al Nivel 5 (también obtenible mediante crianza). Se elige en el Monte Moon (S2) frente al Fósil Domo.',
            'locations': [{'area': 'Isla Canela (Laboratorio)', 'method': 'Revivir Fósil Helix'}, {'area': 'Monte Moon (S2)', 'method': 'Elección de fósil'}, {'area': 'Isla Quarta (Guardería Pokémon)', 'method': 'Crianza de huevo'}]
        },
        140: {
            'type': 'fossil',
            'badge_label': 'Fósil Domo',
            'badge_color': 'amber',
            'summary': 'Revivir el Fósil Domo en el Laboratorio de Isla Canela al Nivel 5 (también obtenible mediante crianza). Se elige en el Monte Moon (S2) frente al Fósil Helix.',
            'locations': [{'area': 'Isla Canela (Laboratorio)', 'method': 'Revivir Fósil Domo'}, {'area': 'Monte Moon (S2)', 'method': 'Elección de fósil'}, {'area': 'Isla Quarta (Guardería Pokémon)', 'method': 'Crianza de huevo'}]
        },
        142: {
            'type': 'fossil',
            'badge_label': 'Ámbar Viejo',
            'badge_color': 'amber',
            'summary': 'Revivir el Ámbar Viejo en el Laboratorio de Isla Canela al Nivel 5 (también obtenible mediante crianza). Obtenido en la parte trasera del Museo de Ciudad Plateada con Corte.',
            'locations': [{'area': 'Isla Canela (Laboratorio)', 'method': 'Revivir Ámbar Viejo'}, {'area': 'Ciudad Plateada (Museo)', 'method': 'Entrega de científico con MO Corte'}, {'area': 'Isla Quarta (Guardería Pokémon)', 'method': 'Crianza de huevo'}]
        },

        # Legendarios de Kanto
        144: {
            'type': 'legendary',
            'badge_label': 'Legendario',
            'badge_color': 'sky',
            'summary': 'Encuentro estático en el nivel más profundo de las Islas Espuma (Sótano B4) tras resolver el puzle de rocas y corrientes con Fuerza.',
            'locations': [{'area': 'Islas Espuma (S4)', 'method': 'Encuentro estático al Nivel 50'}]
        },
        145: {
            'type': 'legendary',
            'badge_label': 'Legendario',
            'badge_color': 'amber',
            'summary': 'Encuentro estático en la Central de Energía abandonada al final del laberinto interior.',
            'locations': [{'area': 'Central de Energía', 'method': 'Encuentro estático al Nivel 50'}]
        },
        146: {
            'type': 'legendary',
            'badge_label': 'Legendario',
            'badge_color': 'rose',
            'summary': 'Encuentro estático en la cima del volcán Monte Ascuas en Isla Prima tras apartar las rocas con Fuerza.',
            'locations': [{'area': 'Monte Ascuas (Cima)', 'method': 'Encuentro estático al Nivel 50'}]
        },
        150: {
            'type': 'legendary',
            'badge_label': 'Legendario',
            'badge_color': 'purple',
            'summary': 'Encuentro estático en la sala más profunda de la Cueva Celeste (S1) en Ciudad Celeste tras vencer al Alto Mando y reparar la máquina de redes de Celio.',
            'locations': [{'area': 'Cueva Celeste (S1)', 'method': 'Encuentro estático al Nivel 70'}]
        },
        151: {
            'type': 'mythical',
            'badge_label': 'Singular Evento',
            'badge_color': 'pink',
            'summary': 'Inaccesible en estado salvaje en Verde Hoja. Requiere distribución oficial de evento o transferencia desde Pokémon Esmeralda (Isla Suprema con Mapa Viejo).',
            'locations': [{'area': 'Transferencia externa (GBA)', 'method': 'Pokémon Esmeralda (Isla Suprema) o evento oficial'}]
        },

        # Perros Legendarios Errantes en Kanto (según inicial)
        243: {
            'type': 'legendary',
            'badge_label': 'Errante Kanto',
            'badge_color': 'amber',
            'summary': 'Legendario errante por las rutas de Kanto en el postgame si tu Pokémon inicial fue Squirtle (#007).',
            'locations': [{'area': 'Rutas de Kanto (Errante)', 'method': 'Errante por la hierba si elegiste a Squirtle'}]
        },
        244: {
            'type': 'legendary',
            'badge_label': 'Errante Kanto',
            'badge_color': 'rose',
            'summary': 'Legendario errante por las rutas de Kanto en el postgame si tu Pokémon inicial fue Bulbasaur (#001).',
            'locations': [{'area': 'Rutas de Kanto (Errante)', 'method': 'Errante por la hierba si elegiste a Bulbasaur'}]
        },
        245: {
            'type': 'legendary',
            'badge_label': 'Errante Kanto',
            'badge_color': 'sky',
            'summary': 'Legendario errante por las rutas de Kanto en el postgame si tu Pokémon inicial fue Charmander (#004).',
            'locations': [{'area': 'Rutas de Kanto (Errante)', 'method': 'Errante por la hierba si elegiste a Charmander'}]
        },

        # Regalo Huevo Togepi en Sevii
        175: {
            'type': 'gift',
            'badge_label': 'Huevo Regalo',
            'badge_color': 'pink',
            'summary': 'Huevo entregado por un caballero anciano en el Laberinto de Agua (Isla Inta) si tu Pokémon cabecera tiene máxima felicidad (también obtenible mediante crianza).',
            'locations': [{'area': 'Laberinto de Agua (Isla Inta)', 'method': 'Huevo de regalo'}, {'area': 'Isla Quarta (Guardería Pokémon)', 'method': 'Crianza de huevo'}]
        },

        # Eventos Insulares Místicos
        249: {
            'type': 'legendary',
            'badge_label': 'Evento Roca Ombligo',
            'badge_color': 'sky',
            'summary': 'Encuentro estático en el fondo de Roca Ombligo (Nivel 70) accesible en barco con el Ticket Místico de evento oficial.',
            'locations': [{'area': 'Roca Ombligo (Ticket Místico)', 'method': 'Encuentro estático al Nivel 70'}]
        },
        250: {
            'type': 'legendary',
            'badge_label': 'Evento Roca Ombligo',
            'badge_color': 'rose',
            'summary': 'Encuentro estático en la cima de Roca Ombligo (Nivel 70) accesible en barco con el Ticket Místico de evento oficial.',
            'locations': [{'area': 'Roca Ombligo (Ticket Místico)', 'method': 'Encuentro estático al Nivel 70'}]
        },
        251: {
            'type': 'mythical',
            'badge_label': 'Mítico / Disco Bonus',
            'badge_color': 'pink',
            'summary': 'Pokémon singular inaccesible de forma salvaje. Obtenible mediante transferencia con el Disco Bonus de Pokémon Colosseum (Japón) mediante cable GameCube-GBA (o distribución oficial de evento).',
            'locations': [{'area': 'Centro Pokémon (Transferencia GameCube)', 'method': 'Disco Bonus Colosseum (Japón)'}]
        },
        386: {
            'type': 'mythical',
            'badge_label': 'Evento Isla Origen',
            'badge_color': 'orange',
            'summary': 'Encuentro estático en Isla Origen tras resolver el enigma del triángulo negro, accesible en barco con el Ori-Ticket (Aurora Ticket). En Pokémon Verde Hoja adopta de forma nativa la Forma Defensa.',
            'locations': [{'area': 'Isla Origen (Ori-Ticket)', 'method': 'Encuentro estático (Forma Defensa al Nivel 30)'}]
        },

        # Exclusivos de Rojo Fuego (Inaccesibles en estado salvaje en Verde Hoja, requieren intercambio)
        23: {'type': 'trade', 'badge_label': 'Exclusivo Rojo Fuego', 'badge_color': 'rose', 'summary': 'Exclusivo de Pokémon Rojo Fuego (Ruta 4, 8, 9, 10, 11, 23). Requiere intercambio (también obtenible mediante crianza).', 'locations': [{'area': 'Intercambio con Pokémon Rojo Fuego', 'method': 'Exclusivo de versión'}, {'area': 'Isla Quarta (Guardería Pokémon)', 'method': 'Crianza de huevo'}]},
        24: {'type': 'trade', 'badge_label': 'Exclusivo Rojo Fuego', 'badge_color': 'rose', 'summary': 'Exclusivo de Pokémon Rojo Fuego. Evoluciona de Ekans al Nivel 22 o salvaje en Ruta 23 en Rojo Fuego.', 'locations': [{'area': 'Intercambio con Pokémon Rojo Fuego', 'method': 'Evolución de Ekans transferido'}]},
        43: {'type': 'trade', 'badge_label': 'Exclusivo Rojo Fuego', 'badge_color': 'rose', 'summary': 'Exclusivo de Pokémon Rojo Fuego (Ruta 5, 6, 7, 12, 13, 14, 15, 24, 25). Requiere intercambio (también obtenible mediante crianza).', 'locations': [{'area': 'Intercambio con Pokémon Rojo Fuego', 'method': 'Exclusivo de versión'}, {'area': 'Isla Quarta (Guardería Pokémon)', 'method': 'Crianza de huevo'}]},
        44: {'type': 'trade', 'badge_label': 'Exclusivo Rojo Fuego', 'badge_color': 'rose', 'summary': 'Exclusivo de Pokémon Rojo Fuego. Evoluciona de Oddish al Nivel 21 o salvaje en Ruta 12, 13, 14, 15 en Rojo Fuego.', 'locations': [{'area': 'Intercambio con Pokémon Rojo Fuego', 'method': 'Exclusivo de versión'}]},
        45: {'type': 'trade', 'badge_label': 'Exclusivo Rojo Fuego', 'badge_color': 'rose', 'summary': 'Exclusivo de Pokémon Rojo Fuego. Evoluciona de Gloom usando Piedra Hoja.', 'locations': [{'area': 'Intercambio con Pokémon Rojo Fuego', 'method': 'Evolución de Gloom transferido'}]},
        182: {'type': 'trade', 'badge_label': 'Exclusivo Rojo Fuego', 'badge_color': 'rose', 'summary': 'Exclusivo de Pokémon Rojo Fuego. Evoluciona de Gloom usando Piedra Solar.', 'locations': [{'area': 'Intercambio con Pokémon Rojo Fuego', 'method': 'Evolución de Gloom transferido'}]},
        54: {'type': 'trade', 'badge_label': 'Exclusivo Rojo Fuego', 'badge_color': 'rose', 'summary': 'Exclusivo de Pokémon Rojo Fuego (Ruta 4, 6, 12, 13, 24, 25, Islas Espuma, etc.). Requiere intercambio (también obtenible mediante crianza).', 'locations': [{'area': 'Intercambio con Pokémon Rojo Fuego', 'method': 'Exclusivo de versión'}, {'area': 'Isla Quarta (Guardería Pokémon)', 'method': 'Crianza de huevo'}]},
        55: {'type': 'trade', 'badge_label': 'Exclusivo Rojo Fuego', 'badge_color': 'rose', 'summary': 'Exclusivo de Pokémon Rojo Fuego. Evoluciona de Psyduck al Nivel 33 o salvaje en Rojo Fuego.', 'locations': [{'area': 'Intercambio con Pokémon Rojo Fuego', 'method': 'Exclusivo de versión'}]},
        58: {'type': 'trade', 'badge_label': 'Exclusivo Rojo Fuego', 'badge_color': 'rose', 'summary': 'Exclusivo de Pokémon Rojo Fuego (Ruta 7, 8). Requiere intercambio (también obtenible mediante crianza).', 'locations': [{'area': 'Intercambio con Pokémon Rojo Fuego', 'method': 'Exclusivo de versión'}, {'area': 'Isla Quarta (Guardería Pokémon)', 'method': 'Crianza de huevo'}]},
        59: {'type': 'trade', 'badge_label': 'Exclusivo Rojo Fuego', 'badge_color': 'rose', 'summary': 'Exclusivo de Pokémon Rojo Fuego. Evoluciona de Growlithe usando Piedra Fuego.', 'locations': [{'area': 'Intercambio con Pokémon Rojo Fuego', 'method': 'Evolución de Growlithe transferido'}]},
        90: {'type': 'trade', 'badge_label': 'Exclusivo Rojo Fuego', 'badge_color': 'rose', 'summary': 'Exclusivo de Pokémon Rojo Fuego (pescando con Supercaña en Carmín, Canela, Paleta, etc.). Requiere intercambio (también obtenible mediante crianza).', 'locations': [{'area': 'Intercambio con Pokémon Rojo Fuego', 'method': 'Exclusivo de versión'}, {'area': 'Isla Quarta (Guardería Pokémon)', 'method': 'Crianza de huevo'}]},
        91: {'type': 'trade', 'badge_label': 'Exclusivo Rojo Fuego', 'badge_color': 'rose', 'summary': 'Exclusivo de Pokémon Rojo Fuego. Evoluciona de Shellder usando Piedra Agua.', 'locations': [{'area': 'Intercambio con Pokémon Rojo Fuego', 'method': 'Evolución de Shellder transferido'}]},
        123: {'type': 'trade', 'badge_label': 'Exclusivo Rojo Fuego', 'badge_color': 'rose', 'summary': 'Exclusivo de Pokémon Rojo Fuego (Zona Safari y Casino de Azulona). Requiere intercambio (también obtenible mediante crianza).', 'locations': [{'area': 'Intercambio con Pokémon Rojo Fuego', 'method': 'Exclusivo de versión'}, {'area': 'Isla Quarta (Guardería Pokémon)', 'method': 'Crianza de huevo'}]},
        212: {'type': 'trade', 'badge_label': 'Exclusivo Rojo Fuego', 'badge_color': 'rose', 'summary': 'Exclusivo de Pokémon Rojo Fuego. Evoluciona de Scyther por intercambio equipado con Revestimiento Metálico.', 'locations': [{'area': 'Intercambio con Pokémon Rojo Fuego', 'method': 'Evolución de Scyther transferido'}]},
        125: {'type': 'trade', 'badge_label': 'Exclusivo Rojo Fuego', 'badge_color': 'rose', 'summary': 'Exclusivo de Pokémon Rojo Fuego (Central de Energía). Requiere intercambio (también obtenible mediante crianza).', 'locations': [{'area': 'Intercambio con Pokémon Rojo Fuego', 'method': 'Exclusivo de versión'}, {'area': 'Isla Quarta (Guardería Pokémon)', 'method': 'Crianza de huevo'}]},
        239: {'type': 'trade', 'badge_label': 'Exclusivo Rojo Fuego', 'badge_color': 'rose', 'summary': 'Exclusivo de Pokémon Rojo Fuego. Obtenible criando a Electabuzz en la Guardería de Isla Quarta (requiere transferir a Electabuzz desde Rojo Fuego).', 'locations': [{'area': 'Isla Quarta (Guardería Pokémon)', 'method': 'Crianza de Electabuzz'}]},
        194: {'type': 'trade', 'badge_label': 'Exclusivo Rojo Fuego', 'badge_color': 'rose', 'summary': 'Exclusivo de Pokémon Rojo Fuego (Isla Quarta y Valle Ruinas). Requiere intercambio (también obtenible mediante crianza).', 'locations': [{'area': 'Intercambio con Pokémon Rojo Fuego', 'method': 'Exclusivo de versión'}, {'area': 'Isla Quarta (Guardería Pokémon)', 'method': 'Crianza de huevo'}]},
        195: {'type': 'trade', 'badge_label': 'Exclusivo Rojo Fuego', 'badge_color': 'rose', 'summary': 'Exclusivo de Pokémon Rojo Fuego. Evoluciona de Wooper al Nivel 20.', 'locations': [{'area': 'Intercambio con Pokémon Rojo Fuego', 'method': 'Evolución de Wooper transferido'}]},
        198: {'type': 'trade', 'badge_label': 'Exclusivo Rojo Fuego', 'badge_color': 'rose', 'summary': 'Exclusivo de Pokémon Rojo Fuego (Cueva Perdida en Isla Inta). Requiere intercambio (también obtenible mediante crianza).', 'locations': [{'area': 'Intercambio con Pokémon Rojo Fuego', 'method': 'Exclusivo de versión (Cueva Perdida en RF)'}, {'area': 'Isla Quarta (Guardería Pokémon)', 'method': 'Crianza de huevo'}]},
        211: {'type': 'trade', 'badge_label': 'Exclusivo Rojo Fuego', 'badge_color': 'rose', 'summary': 'Exclusivo de Pokémon Rojo Fuego (pescando en Puerto Carmín e Isla Inta). Requiere intercambio (también obtenible mediante crianza).', 'locations': [{'area': 'Intercambio con Pokémon Rojo Fuego', 'method': 'Exclusivo de versión'}, {'area': 'Isla Quarta (Guardería Pokémon)', 'method': 'Crianza de huevo'}]},
        225: {'type': 'trade', 'badge_label': 'Exclusivo Rojo Fuego', 'badge_color': 'rose', 'summary': 'Exclusivo de Pokémon Rojo Fuego (Cueva Glaciada en Isla Quarta). Requiere intercambio (también obtenible mediante crianza).', 'locations': [{'area': 'Intercambio con Pokémon Rojo Fuego', 'method': 'Exclusivo de versión (Cueva Glaciada en RF)'}, {'area': 'Isla Quarta (Guardería Pokémon)', 'method': 'Crianza de huevo'}]},
        227: {'type': 'trade', 'badge_label': 'Exclusivo Rojo Fuego', 'badge_color': 'rose', 'summary': 'Exclusivo de Pokémon Rojo Fuego (Cañón Sétano en Isla Sétima). Requiere intercambio (también obtenible mediante crianza).', 'locations': [{'area': 'Intercambio con Pokémon Rojo Fuego', 'method': 'Exclusivo de versión (Isla Sétima en RF)'}, {'area': 'Isla Quarta (Guardería Pokémon)', 'method': 'Crianza de huevo'}]},
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

    def clean_wikitext_entry(text: str) -> str:
        if not text:
            return ""
        text = re.sub(r"\{\{(?:NombreHaEs|n)\|([^|]+)(?:\|([^}]+))?\}*", lambda m: m.group(2) or m.group(1), text)
        text = re.sub(r"\{\{[^}]+\}\}", "", text)
        text = re.sub(r"\[\[(?:[^|\]]*\|)?([^\]]+)\]\]", r"\1", text)
        text = re.sub(r"<ref[^>]*>.*?</ref>", "", text, flags=re.DOTALL)
        text = re.sub(r"<[^>]+>", "", text)
        text = text.replace("\n", " ").replace("\r", " ")
        return " ".join(text.split()).strip()

    STARTING_LEAFGREEN_ID = 2869

    def build_entry(nat_id, entry_num, is_national=False):
        sp = species_386.get(str(nat_id))
        if not sp:
            raise ValueError(f"Faltan datos de la especie {nat_id}")

        flavor = clean_wikitext_entry(wikidex_descriptions.get(str(nat_id), ""))
        sp_name = sp['name'].lower()
        evo_info = evo_map.get(sp_name)
        egg_groups = sp.get('egg_groups', [])

        is_baby = sp_name in BABY_NAMES
        is_incense_parent = sp_name in INCENSE_PARENTS_THAT_HATCH
        is_evolution = (evo_info is not None) and not is_incense_parent

        # Regla Universal de Crianza:
        # SOLO eclosionan formas base, bebés y padres sin incienso en Gen 3 (Marill, Wobbuffet).
        # Evolucionados, Legendarios, Singulares, Nidorina, Nidoqueen, Ditto y Unown NUNCA eclosionan.
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

        # Localizaciones crudas de PokeAPI para Verde Hoja
        locs_raw = encounters_leafgreen.get(str(nat_id), [])
        unique_locs = []
        seen_areas = set()
        for l in locs_raw:
            raw_method = l.get('method_raw', 'walk')
            # 1. Ignorar 'npc-trade' crudo de PokeAPI para evitar colisiones y duplicados
            # con el diccionario oficial curado de intercambios NPC (INGAME_TRADES_LEAFGREEN).
            if raw_method == 'npc-trade':
                continue

            # 2. Ignorar eventos externos replicables salvo Pikachu (#25)
            if raw_method == 'colosseum-bonus-disc-jpn' and nat_id != 25:
                continue

            raw_area = l.get('area_raw', '')
            area_translated = KANTO_SEVII_AREAS_ES.get(raw_area, raw_area.replace('-', ' ').title())
            method_translated = METHOD_NAMES_ES.get(raw_method, raw_method.replace('-', ' ').title())

            # Para premios canjeables del Casino de Azulona (Clefairy, Abra, Pinsir, Dratini)
            if raw_area == 'celadon-city-prize-corner':
                method_translated = 'Premio del Casino'

            k = (area_translated, method_translated)
            if k not in seen_areas:
                seen_areas.add(k)
                unique_locs.append({'area': area_translated, 'method': method_translated})

        is_in_kanto_dex = (nat_id <= 151)

        obt_info = {}
        if nat_id in SPECIAL_OBT_LEAFGREEN:
            obt_info = copy.deepcopy(SPECIAL_OBT_LEAFGREEN[nat_id])
        elif nat_id in INGAME_TRADES_LEAFGREEN:
            obt_info = copy.deepcopy(INGAME_TRADES_LEAFGREEN[nat_id])
            # Si la especie además posee encuentros salvajes auténticos (ej: Seel, Electrode, Tangela),
            # incorporar las zonas salvajes preservando el intercambio como método principal
            # y colocando la Guardería al final.
            if unique_locs:
                curated_locs = obt_info.get('locations', [])
                trade_locs = [l for l in curated_locs if 'crianza' not in l.get('method', '').lower()]
                daycare_locs = [l for l in curated_locs if 'crianza' in l.get('method', '').lower()]
                obt_info['locations'] = trade_locs + unique_locs + daycare_locs
        elif unique_locs:
            # Separar ubicaciones salvajes reales de eventos externos replicables o Casino
            true_wild_locs = [l for l in unique_locs if 'colosseum' not in l.get('method', '').lower() and 'casino' not in l.get('method', '').lower()]
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
        elif is_in_kanto_dex:
            obt_info = {
                'type': 'special',
                'summary': "Obtenible en la región de Kanto.",
                'locations': []
            }
        else:
            # Especie ausente en Kanto / Sevii (Transferencia externa requerida)
            transfer_origin = "Pokémon Rubí, Zafiro, Esmeralda o Nintendo GameCube"
            if 152 <= nat_id <= 160:
                transfer_origin = "Pokémon Esmeralda (regalo de Abedul) o Pokémon Colosseum"
            elif nat_id in [196, 197]:
                transfer_origin = "Pokémon Rubí, Zafiro o Esmeralda (evolución por felicidad con reloj día/noche)"
            elif 252 <= nat_id <= 384:
                transfer_origin = "Pokémon Rubí, Zafiro o Esmeralda (Hoenn)"
            elif nat_id == 385:
                transfer_origin = "Pokémon Channel o Disco Bonus de Pokémon Colosseum"

            if is_hatchable:
                obt_info = {
                    'type': 'transfer',
                    'summary': f"No disponible en estado salvaje en Kanto ni en las Islas Sétima. Requiere transferencia desde {transfer_origin} (también obtenible mediante crianza).",
                    'locations': [
                        {'area': 'Transferencia externa (GBA / GameCube)', 'method': transfer_origin},
                        {'area': 'Isla Quarta (Guardería Pokémon)', 'method': 'Crianza de huevo'}
                    ]
                }
            else:
                obt_info = {
                    'type': 'transfer',
                    'summary': f"No disponible en Kanto ni en las Islas Sétima. Requiere transferencia desde {transfer_origin}.",
                    'locations': [{'area': 'Transferencia externa (GBA / GameCube)', 'method': transfer_origin}]
                }

        # Regla Universal de Crianza: Solo aplicable si la especie PUEDE nacer de un huevo (is_hatchable).
        # NUNCA a formas evolucionadas como Charizard, Venusaur, Raichu, etc.
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
                    'area': 'Isla Quarta (Guardería Pokémon)',
                    'method': method_str
                })

            summary_text = obt_info.get('summary', '')
            if 'crianza' not in summary_text.lower():
                clean_clause = " (también obtenible mediante crianza)"
                if summary_text.endswith('.'):
                    obt_info['summary'] = summary_text[:-1] + clean_clause + "."
                else:
                    obt_info['summary'] = summary_text + clean_clause

        # Piedras u objetos evolutivos asociados
        evo_stone = None
        evo_item_slug = (evo_info.get('item_slug') if evo_info else None) or obt_info.get('item_slug')
        if evo_item_slug and evo_item_slug in stones_catalog:
            stone_data = copy.deepcopy(stones_catalog[evo_item_slug])
            stone_data['locations'] = stone_data.get('games', {}).get('leafgreen', [])
            evo_stone = stone_data

        b_color = obt_info.get('badge_color', 'blue')
        b_label = obt_info.get('badge_label', 'Salvaje')
        if obt_info.get('type') == 'wild':
            b_label = 'Salvaje'
            b_color = 'emerald'
        elif obt_info.get('type') == 'evolution':
            b_label = 'Evolución'
            b_color = 'indigo'
        elif obt_info.get('type') == 'transfer':
            b_label = 'Transferencia'
            b_color = 'violet'
        elif obt_info.get('type') == 'trade':
            b_label = 'Intercambio'
            b_color = 'indigo'

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
            pc_icon_url = "/media/pokemon/icons/gen3/10002.png"

        return {
            "id": STARTING_LEAFGREEN_ID + (nat_id - 1),
            "entry_number": entry_num,
            "game_slug": "leafgreen",
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
            "game_sprite_url": f"/media/pokemon/sprites/leafgreen/{nat_id}.png",
            "game_sprite_shiny_url": f"/media/pokemon/sprites/leafgreen_shiny/{nat_id}.png",
            "game_sprite_back_url": f"/media/pokemon/sprites/leafgreen/back/{nat_id}.png",
            "game_sprite_shiny_back_url": f"/media/pokemon/sprites/leafgreen_shiny/back/{nat_id}.png",
            "modern_sprite_shiny_url": f"/media/pokemon/artwork/shiny/{nat_id}.png",
            "modal_retro_sprite_url": f"/media/pokemon/sprites/leafgreen/{nat_id}.png",
            "modal_retro_sprite_shiny_url": f"/media/pokemon/sprites/leafgreen_shiny/{nat_id}.png",
            "modal_retro_sprite_back_url": f"/media/pokemon/sprites/leafgreen/back/{nat_id}.png",
            "modal_retro_sprite_shiny_back_url": f"/media/pokemon/sprites/leafgreen_shiny/back/{nat_id}.png",
            "pc_icon_url": pc_icon_url,
            "cry_url": f"/media/pokemon/cries/{nat_id}.ogg",
            "flavor_text": flavor,
            "obtaining_info": obt_info,
            "evolution_stone": evo_stone,
            "game_data": {
                "generation": 3,
                "game_slug": "leafgreen",
                "game_name": "Pokémon Verde Hoja",
                "is_regional": not is_national
            }
        }

    # 1. Compilar Pokédex Regional de Kanto (151 Pokémon)
    regional_catalog = []
    for nat_id in range(1, 152):
        entry = build_entry(nat_id, nat_id, is_national=False)
        regional_catalog.append(entry)

    with open(CATALOGS_DIR / "leafgreen.json", "w", encoding="utf-8") as f:
        json.dump(regional_catalog, f, ensure_ascii=False, indent=2)
    print(f"[OK] leafgreen.json generado con {len(regional_catalog)} entradas (Pokédex Regional de Kanto)")

    # 2. Compilar Pokédex Nacional (386 Pokémon)
    national_catalog = []
    for nat_id in range(1, 387):
        entry = build_entry(nat_id, nat_id, is_national=True)
        national_catalog.append(entry)

    with open(CATALOGS_DIR / "leafgreen_national.json", "w", encoding="utf-8") as f:
        json.dump(national_catalog, f, ensure_ascii=False, indent=2)
    print(f"[OK] leafgreen_national.json generado con {len(national_catalog)} entradas (Pokédex Nacional de Verde Hoja)")


if __name__ == '__main__':
    build_catalogs()
