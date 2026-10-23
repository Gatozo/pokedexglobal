"""
Script para compilar los catálogos oficiales de Pokémon Perla:
- tracker/data/catalogs/pearl.json (Pokédex Regional de Sinnoh - 151 especies)
- tracker/data/catalogs/pearl_national.json (Pokédex Nacional - 493 especies)
Siguiendo rigurosamente la guía guides/especificacion-pokemon-perla.md y el estándar maestro.
"""
import json
import os
import re
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "pokedex.settings")

import django
django.setup()

from tracker.utils import resolve_evolution_stone, get_incense_for_baby

CACHE_DIR = BASE_DIR / "tracker" / "data" / "cache"
CATALOGS_DIR = BASE_DIR / "tracker" / "data" / "catalogs"

TYPE_NAMES_ES = {
    "normal": "Normal",
    "fire": "Fuego",
    "water": "Agua",
    "grass": "Planta",
    "electric": "Eléctrico",
    "ice": "Hielo",
    "fighting": "Lucha",
    "poison": "Veneno",
    "ground": "Tierra",
    "flying": "Volador",
    "psychic": "Psíquico",
    "bug": "Bicho",
    "rock": "Roca",
    "ghost": "Fantasma",
    "dragon": "Dragón",
    "steel": "Acero",
    "dark": "Siniestro",
}

SINNOH_AREA_NAMES = {
    'acuity-lakefront-area': 'Orilla Agudeza',
    'canalave-city-area': 'Ciudad Canal',
    'celestic-town-area': 'Pueblo Caelestis',
    'eterna-city-area': 'Ciudad Vetusta',
    'eterna-city-eterna-condominiums': 'Ciudad Vetusta (Condominios Vetusta)',
    'eterna-forest-area': 'Bosque Vetusto',
    'floaroma-meadow-area': 'Prado Aromaflor',
    'flower-paradise-area': 'Paraíso Floral',
    'fuego-ironworks-area': 'Forja Fuego',
    'great-marsh-area-1': 'Gran Pantano (Zona 1)',
    'great-marsh-area-2': 'Gran Pantano (Zona 2)',
    'great-marsh-area-3': 'Gran Pantano (Zona 3)',
    'great-marsh-area-4': 'Gran Pantano (Zona 4)',
    'great-marsh-area-5': 'Gran Pantano (Zona 5)',
    'great-marsh-area-6': 'Gran Pantano (Zona 6)',
    'hearthome-city-area': 'Ciudad Corazón',
    'hearthome-city-west-gate': 'Paso Oeste de Ciudad Corazón',
    'iron-island-1f': 'Isla Hierro (P1)',
    'iron-island-area': 'Isla Hierro (Exterior)',
    'iron-island-b1f-left': 'Isla Hierro (Sótano B1)',
    'iron-island-b1f-right': 'Isla Hierro (Sótano B1)',
    'iron-island-b2f-left': 'Isla Hierro (Sótano B2)',
    'iron-island-b2f-right': 'Isla Hierro (Sótano B2)',
    'iron-island-b3f': 'Isla Hierro (Sótano B3)',
    'lake-acuity-area': 'Lago Agudeza',
    'lake-acuity-cavern': 'Caverna Agudeza',
    'lake-valor-area': 'Lago Valor',
    'lake-valor-cavern': 'Caverna Valor',
    'lake-verity-after-galactic-intervention': 'Lago Veraz',
    'lake-verity-before-galactic-intervention': 'Lago Veraz',
    'lost-tower-1f': 'Torre Perdida (P1)',
    'lost-tower-2f': 'Torre Perdida (P2)',
    'lost-tower-3f': 'Torre Perdida (P3)',
    'lost-tower-4f': 'Torre Perdida (P4)',
    'lost-tower-5f': 'Torre Perdida (P5)',
    'maniac-tunnel-26-plus-different-unown-caught': 'Túnel Ruinamaníaco (26+ Unown)',
    'mt-coronet-1f-from-exterior': 'Monte Corona (P1)',
    'mt-coronet-1f-route-207': 'Monte Corona (Entrada Ruta 207)',
    'mt-coronet-1f-route-211': 'Monte Corona (Entrada Ruta 211)',
    'mt-coronet-1f-route-216': 'Monte Corona (Entrada Ruta 216)',
    'mt-coronet-2f': 'Monte Corona (P2)',
    'mt-coronet-3f': 'Monte Corona (P3)',
    'mt-coronet-4f': 'Monte Corona (P4)',
    'mt-coronet-4f-small-room': 'Monte Corona (P4 Cámara)',
    'mt-coronet-5f': 'Monte Corona (P5)',
    'mt-coronet-6f': 'Monte Corona (P6)',
    'mt-coronet-b1f': 'Monte Corona (Sótano B1)',
    'mt-coronet-exterior-blizzard': 'Monte Corona (Cima / Ventisca)',
    'mt-coronet-exterior-snowfall': 'Monte Corona (Laderas Nevadas)',
    'newmoon-island-area': 'Isla Lunanueva',
    'old-chateau-2f': 'Vieja Mansión (P2)',
    'old-chateau-2f-left-room': 'Vieja Mansión (Habitación Oeste)',
    'old-chateau-2f-leftmost-room': 'Vieja Mansión (Habitación Esquina)',
    'old-chateau-2f-middle-room': 'Vieja Mansión (Habitación Central)',
    'old-chateau-2f-private-room': 'Vieja Mansión (Habitación Privada)',
    'old-chateau-2f-right-room': 'Vieja Mansión (Habitación del Cuadro)',
    'old-chateau-2f-rightmost-room': 'Vieja Mansión (Habitación Televisión)',
    'old-chateau-dining-room': 'Vieja Mansión (Comedor)',
    'old-chateau-entrance': 'Vieja Mansión (Entrada)',
    'oreburgh-city-north-west-house': 'Ciudad Pirita (Casa Noroeste)',
    'oreburgh-city-oreburgh-mining-museum': 'Museo Minero de Ciudad Pirita',
    'oreburgh-gate-1f': 'Puerta Pirita (P1)',
    'oreburgh-gate-b1f': 'Puerta Pirita (Sótano B1)',
    'oreburgh-mine-1f': 'Mina Pirita (P1)',
    'oreburgh-mine-b1f': 'Mina Pirita (Sótano B1)',
    'pastoria-city-area': 'Ciudad Pradera',
    'ravaged-path-area': 'Senda Desolada',
    'resort-area-area': 'Zona Descanso',
    'roaming-sinnoh-area': 'Rutas de Sinnoh (Errante)',
    'ruin-maniac-cave-0-9-different-unown-caught': 'Cueva Ruinamaníaco (Entrada)',
    'ruin-maniac-cave-10-25-different-unown-caught': 'Cueva Ruinamaníaco (Profunda)',
    'sendoff-spring-area': 'Fuente Despedida',
    'sinnoh-hall-of-origin-1-area': 'Sala del Origen',
    'sinnoh-pokemart-area': 'Tienda Pokémon',
    'sinnoh-pokemon-league-area': 'Liga Pokémon (Cascadas)',
    'sinnoh-route-201-area': 'Ruta 201',
    'sinnoh-route-202-area': 'Ruta 202',
    'sinnoh-route-203-area': 'Ruta 203',
    'sinnoh-route-204-north-towards-floaroma-town': 'Ruta 204 (Norte)',
    'sinnoh-route-204-south-towards-jubilife-city': 'Ruta 204 (Sur)',
    'sinnoh-route-205-east-towards-eterna-city': 'Ruta 205 (Este)',
    'sinnoh-route-205-south-towards-floaroma-town': 'Ruta 205 (Sur)',
    'sinnoh-route-206-area': 'Ruta 206 (Camino de Bicis)',
    'sinnoh-route-207-area': 'Ruta 207',
    'sinnoh-route-208-area': 'Ruta 208',
    'sinnoh-route-209-area': 'Ruta 209',
    'sinnoh-route-210-south-towards-solaceon-town': 'Ruta 210 (Sur)',
    'sinnoh-route-210-west-towards-celestic-town': 'Ruta 210 (Norte)',
    'sinnoh-route-211-east-towards-celestic-town': 'Ruta 211 (Este)',
    'sinnoh-route-211-west-towards-eterna-city': 'Ruta 211 (Oeste)',
    'sinnoh-route-212-east-towards-pastoria-city': 'Ruta 212 (Sur)',
    'sinnoh-route-212-north-towards-hearthome-city': 'Ruta 212 (Norte)',
    'sinnoh-route-213-area': 'Ruta 213',
    'sinnoh-route-214-area': 'Ruta 214',
    'sinnoh-route-215-area': 'Ruta 215',
    'sinnoh-route-216-area': 'Ruta 216',
    'sinnoh-route-217-area': 'Ruta 217',
    'sinnoh-route-218-area': 'Ruta 218',
    'sinnoh-route-219-area': 'Ruta 219',
    'sinnoh-route-221-area': 'Ruta 221',
    'sinnoh-route-222-area': 'Ruta 222',
    'sinnoh-route-224-area': 'Ruta 224',
    'sinnoh-route-225-area': 'Ruta 225',
    'sinnoh-route-227-area': 'Ruta 227',
    'sinnoh-route-228-area': 'Ruta 228',
    'sinnoh-route-229-area': 'Ruta 229',
    'sinnoh-sea-route-220-area': 'Ruta 220 (Ruta Marítima)',
    'sinnoh-sea-route-223-area': 'Ruta 223 (Ruta Marítima)',
    'sinnoh-sea-route-226-area': 'Ruta 226 (Ruta Marítima)',
    'sinnoh-sea-route-226-island-house': 'Ruta 226 (Casa del Maestro)',
    'sinnoh-sea-route-230-area': 'Ruta 230 (Ruta Marítima)',
    'sinnoh-victory-road-1f': 'Calle Victoria (P1)',
    'sinnoh-victory-road-2f': 'Calle Victoria (P2)',
    'sinnoh-victory-road-b1f': 'Calle Victoria (Sótano B1)',
    'sinnoh-victory-road-inside': 'Calle Victoria (Interior)',
    'sinnoh-victory-road-inside-b1f': 'Calle Victoria (Interior Sótano)',
    'sinnoh-victory-road-inside-exit': 'Calle Victoria (Salida)',
    'snowpoint-city-north-west-house': 'Ciudad Puntaneva (Casa Noroeste)',
    'snowpoint-temple-1f': 'Templo Puntaneva (P1)',
    'snowpoint-temple-b1f': 'Templo Puntaneva (Sótano B1)',
    'snowpoint-temple-b2f': 'Templo Puntaneva (Sótano B2)',
    'snowpoint-temple-b3f': 'Templo Puntaneva (Sótano B3)',
    'snowpoint-temple-b4f': 'Templo Puntaneva (Sótano B4)',
    'snowpoint-temple-b5f': 'Templo Puntaneva (Sótano B5)',
    'solaceon-ruins-1f': 'Ruinas Sosiego (P1)',
    'solaceon-ruins-2f': 'Ruinas Sosiego (P2)',
    'solaceon-ruins-b1f-a': 'Ruinas Sosiego (Sótano B1)',
    'solaceon-ruins-b1f-b': 'Ruinas Sosiego (Sótano B1)',
    'solaceon-ruins-b1f-c': 'Ruinas Sosiego (Sótano B1)',
    'solaceon-ruins-b2f-a': 'Ruinas Sosiego (Sótano B2)',
    'solaceon-ruins-b2f-b': 'Ruinas Sosiego (Sótano B2)',
    'solaceon-ruins-b2f-c': 'Ruinas Sosiego (Sótano B2)',
    'solaceon-ruins-b3f-a': 'Ruinas Sosiego (Sótano B3)',
    'solaceon-ruins-b3f-b': 'Ruinas Sosiego (Sótano B3)',
    'solaceon-ruins-b3f-c': 'Ruinas Sosiego (Sótano B3)',
    'solaceon-ruins-b3f-d': 'Ruinas Sosiego (Sótano B3)',
    'solaceon-ruins-b3f-e': 'Ruinas Sosiego (Sótano B3)',
    'solaceon-ruins-b4f-a': 'Ruinas Sosiego (Sótano B4)',
    'solaceon-ruins-b4f-b': 'Ruinas Sosiego (Sótano B4)',
    'solaceon-ruins-b4f-c': 'Ruinas Sosiego (Sótano B4)',
    'solaceon-ruins-b4f-d': 'Ruinas Sosiego (Sótano B4)',
    'solaceon-ruins-b5f': 'Ruinas Sosiego (Cámara Final)',
    'spear-pillar-area': 'Columna Lanza',
    'stark-mountain-area': 'Montaña Dura (Exterior)',
    'stark-mountain-entrance': 'Montaña Dura (Entrada)',
    'stark-mountain-heatran-chamber': 'Montaña Dura (Cámara de Heatran)',
    'stark-mountain-inside': 'Montaña Dura (Interior)',
    'sunyshore-city-area': 'Ciudad Marina',
    'trophy-garden-area': 'Jardín Trofeo',
    'turnback-cave-after-pillar-3': 'Cueva Retorno (Cámara Giratina)',
    'turnback-cave-before-pillar-1': 'Cueva Retorno (Pilar 1)',
    'turnback-cave-between-pillars-1-and-2': 'Cueva Retorno (Pilar 2)',
    'turnback-cave-between-pillars-2-and-3': 'Cueva Retorno (Pilar 3)',
    'turnback-cave-pillar-1': 'Cueva Retorno (Pilar 1)',
    'turnback-cave-pillar-2': 'Cueva Retorno (Pilar 2)',
    'turnback-cave-pillar-3': 'Cueva Retorno (Pilar 3)',
    'twinleaf-town-area': 'Pueblo Hojaverde',
    'valley-windworks-area': 'Valle Eólico',
    'valor-lakefront-area': 'Orilla Valor',
    'wayward-cave-1f': 'Cueva Extravío (P1)',
    'wayward-cave-b1f': 'Cueva Extravío (Sótano B1 - Gible)',
}

BABY_NAMES = {
    'pichu', 'cleffa', 'igglybuff', 'togepi', 'tyrogue',
    'smoochum', 'elekid', 'magby', 'azurill', 'wynaut',
    'budew', 'chingling', 'bonsly', 'mime-jr', 'happiny',
    'munchlax', 'riolu', 'mantyke'
}

INCENSE_PARENTS_THAT_HATCH = {
    'marill', 'wobbuffet', 'roselia', 'chimecho',
    'sudowoodo', 'mr-mime', 'chansey', 'snorlax', 'mantine'
}

NON_BREEDABLE_NAMES = {
    'nidorina', 'nidoqueen', 'ditto', 'unown',
    'articuno', 'zapdos', 'moltres', 'mewtwo', 'mew',
    'raikou', 'entei', 'suicune', 'lugia', 'ho-oh', 'celebi',
    'regirock', 'regice', 'registeel', 'latias', 'latios',
    'kyogre', 'groudon', 'rayquaza', 'jirachi', 'deoxys',
    'uxie', 'mesprit', 'azelf', 'dialga', 'palkia', 'heatran',
    'regigigas', 'giratina', 'cresselia', 'manaphy', 'darkrai',
    'shaymin', 'arceus'
}

DAYCARE_LOCATION = {
    'area': 'Pueblo Sosiego (Guardería Pokémon)',
    'method': 'Crianza de huevo'
}

SPECIAL_OBTAINING = {
    # Iniciales de Sinnoh
    387: {
        'type': 'starter',
        'badge_label': 'Inicial',
        'badge_color': 'emerald',
        'summary': 'Elegir en el maletín del Profesor Serbal en el Lago Veraz al inicio de la aventura (también obtenible mediante crianza).',
        'locations': [
            {'area': 'Lago Veraz (Maletín de Serbal)', 'method': 'Elección de Inicial de Sinnoh'},
            DAYCARE_LOCATION
        ]
    },
    390: {
        'type': 'starter',
        'badge_label': 'Inicial',
        'badge_color': 'amber',
        'summary': 'Elegir en el maletín del Profesor Serbal en el Lago Veraz al inicio de la aventura (también obtenible mediante crianza).',
        'locations': [
            {'area': 'Lago Veraz (Maletín de Serbal)', 'method': 'Elección de Inicial de Sinnoh'},
            DAYCARE_LOCATION
        ]
    },
    393: {
        'type': 'starter',
        'badge_label': 'Inicial',
        'badge_color': 'sky',
        'summary': 'Elegir en el maletín del Profesor Serbal en el Lago Veraz al inicio de la aventura (también obtenible mediante crianza).',
        'locations': [
            {'area': 'Lago Veraz (Maletín de Serbal)', 'method': 'Elección de Inicial de Sinnoh'},
            DAYCARE_LOCATION
        ]
    },

    # Huevos y Regalos en Sinnoh
    440: {
        'type': 'gift',
        'badge_label': 'Huevo Regalo',
        'badge_color': 'pink',
        'summary': 'Huevo entregado por un montañero en el acceso este de Ciudad Corazón (también obtenible mediante crianza).',
        'locations': [
            {'area': 'Ciudad Corazón (Acceso Este)', 'method': 'Huevo entregado por un montañero'},
            DAYCARE_LOCATION
        ]
    },
    447: {
        'type': 'gift',
        'badge_label': 'Huevo Regalo',
        'badge_color': 'indigo',
        'summary': 'Huevo entregado por Quinoa en la salida de Isla Hierro tras acompañarle a derrotar a los reclutas del Equipo Galaxia (también obtenible mediante crianza).',
        'locations': [
            {'area': 'Isla Hierro (Salida)', 'method': 'Huevo entregado por Quinoa'},
            DAYCARE_LOCATION
        ]
    },
    133: {
        'type': 'gift',
        'badge_label': 'Regalo Postgame',
        'badge_color': 'amber',
        'summary': 'Entregado por Tecla en su casa de Ciudad Corazón tras obtener la Pokédex Nacional (también obtenible mediante crianza o en el Jardín Trofeo).',
        'locations': [
            {'area': 'Ciudad Corazón (Casa de Tecla)', 'method': 'Regalo de Tecla tras obtener Pokédex Nacional'},
            {'area': 'Jardín Trofeo', 'method': 'Hierba alta (Mención del Sr. Fortuny)'},
            DAYCARE_LOCATION
        ]
    },
    175: {
        'type': 'gift',
        'badge_label': 'Huevo Regalo',
        'badge_color': 'pink',
        'summary': 'Huevo entregado por Cintia en Ciudad Vetusta tras derrotar a Venus en el Edificio Galaxia (también obtenible mediante crianza).',
        'locations': [
            {'area': 'Ciudad Vetusta (Edificio Galaxia)', 'method': 'Huevo entregado por Cintia'},
            DAYCARE_LOCATION
        ]
    },

    # Fósil Exclusivo de Pokémon Perla
    410: {
        'type': 'fossil',
        'badge_label': 'Fósil Exclusivo',
        'badge_color': 'pink',
        'summary': 'Revivir del Fósil Coraza en el Museo Minero de Ciudad Pirita. Exclusivo de Pokémon Perla excavando en el Subsuelo de Sinnoh (también obtenible mediante crianza).',
        'locations': [
            {'area': 'Subsuelo de Sinnoh', 'method': 'Excavación de Fósil Coraza'},
            {'area': 'Ciudad Pirita (Museo Minero)', 'method': 'Restauración de Fósil Coraza'},
            DAYCARE_LOCATION
        ]
    },

    # Fósiles de Kanto y Hoenn en el Subsuelo de Sinnoh
    138: {
        'type': 'fossil',
        'badge_label': 'Fósil',
        'badge_color': 'sky',
        'summary': 'Revivir del Fósil Hélix en el Museo Minero de Ciudad Pirita. Excavar en el Subsuelo de Sinnoh tras obtener la Pokédex Nacional (también obtenible mediante crianza).',
        'locations': [
            {'area': 'Subsuelo de Sinnoh', 'method': 'Excavación de Fósil Hélix'},
            {'area': 'Ciudad Pirita (Museo Minero)', 'method': 'Restauración de Fósil Hélix'},
            DAYCARE_LOCATION
        ]
    },
    140: {
        'type': 'fossil',
        'badge_label': 'Fósil',
        'badge_color': 'amber',
        'summary': 'Revivir del Fósil Domo en el Museo Minero de Ciudad Pirita. Excavar en el Subsuelo de Sinnoh tras obtener la Pokédex Nacional (más común en Perla; también obtenible mediante crianza).',
        'locations': [
            {'area': 'Subsuelo de Sinnoh', 'method': 'Excavación de Fósil Domo'},
            {'area': 'Ciudad Pirita (Museo Minero)', 'method': 'Restauración de Fósil Domo'},
            DAYCARE_LOCATION
        ]
    },
    142: {
        'type': 'fossil',
        'badge_label': 'Fósil',
        'badge_color': 'purple',
        'summary': 'Revivir del Ámbar Viejo en el Museo Minero de Ciudad Pirita. Excavar en el Subsuelo de Sinnoh tras obtener la Pokédex Nacional (también obtenible mediante crianza).',
        'locations': [
            {'area': 'Subsuelo de Sinnoh', 'method': 'Excavación de Ámbar Viejo'},
            {'area': 'Ciudad Pirita (Museo Minero)', 'method': 'Restauración de Ámbar Viejo'},
            DAYCARE_LOCATION
        ]
    },
    345: {
        'type': 'fossil',
        'badge_label': 'Fósil',
        'badge_color': 'emerald',
        'summary': 'Revivir del Fósil Raíz en el Museo Minero de Ciudad Pirita. Excavar en el Subsuelo de Sinnoh tras obtener la Pokédex Nacional (más común en Perla; también obtenible mediante crianza).',
        'locations': [
            {'area': 'Subsuelo de Sinnoh', 'method': 'Excavación de Fósil Raíz'},
            {'area': 'Ciudad Pirita (Museo Minero)', 'method': 'Restauración de Fósil Raíz'},
            DAYCARE_LOCATION
        ]
    },
    347: {
        'type': 'fossil',
        'badge_label': 'Fósil',
        'badge_color': 'orange',
        'summary': 'Revivir del Fósil Garra en el Museo Minero de Ciudad Pirita. Excavar en el Subsuelo de Sinnoh tras obtener la Pokédex Nacional (también obtenible mediante crianza).',
        'locations': [
            {'area': 'Subsuelo de Sinnoh', 'method': 'Excavación de Fósil Garra'},
            {'area': 'Ciudad Pirita (Museo Minero)', 'method': 'Restauración de Fósil Garra'},
            DAYCARE_LOCATION
        ]
    },

    # Legendarios Autóctonos de Sinnoh en Pokémon Perla
    480: {
        'type': 'legendary',
        'badge_label': 'Legendario',
        'badge_color': 'amber',
        'summary': 'Encuentro estático en la Caverna Agudeza en el centro del Lago Agudeza al Nivel 50 tras resolver el evento de la Columna Lanza.',
        'locations': [{'area': 'Caverna Agudeza (Lago Agudeza)', 'method': 'Encuentro estático al Nivel 50'}]
    },
    481: {
        'type': 'legendary',
        'badge_label': 'Errante',
        'badge_color': 'rose',
        'summary': 'Interaccionar en la Caverna Veraz para registrar su avistamiento; a partir de ese momento recorre libremente las rutas de Sinnoh al Nivel 50 (rastreable con la función Marcamapa del Poké-reloj).',
        'locations': [{'area': 'Rutas de Sinnoh (Errante)', 'method': 'Pokémon errante al Nivel 50'}]
    },
    482: {
        'type': 'legendary',
        'badge_label': 'Legendario',
        'badge_color': 'sky',
        'summary': 'Encuentro estático en la Caverna Valor en el centro del Lago Valor al Nivel 50 tras resolver el evento de la Columna Lanza.',
        'locations': [{'area': 'Caverna Valor (Lago Valor)', 'method': 'Encuentro estático al Nivel 50'}]
    },
    484: {
        'type': 'legendary',
        'badge_label': 'Legendario de Portada',
        'badge_color': 'pink',
        'summary': 'Encuentro estático en la Columna Lanza en la cima del Monte Corona al Nivel 47. Mascota legendaria de portada exclusiva de Pokémon Perla.',
        'locations': [{'area': 'Columna Lanza (Monte Corona)', 'method': 'Legendario estático de portada al Nivel 47'}]
    },
    485: {
        'type': 'legendary',
        'badge_label': 'Legendario',
        'badge_color': 'rose',
        'summary': 'Encuentro estático en la cámara más profunda de la Montaña Dura al Nivel 70 tras devolver la Piedra Magma junto a Bulgur.',
        'locations': [{'area': 'Montaña Dura (Cámara de Heatran)', 'method': 'Encuentro estático al Nivel 70'}]
    },
    486: {
        'type': 'legendary',
        'badge_label': 'Legendario',
        'badge_color': 'slate',
        'summary': 'Encuentro estático en el piso B5F del Templo Puntaneva al Nivel 70 tras transferir y llevar en el equipo a Regirock, Regice y Registeel.',
        'locations': [{'area': 'Templo Puntaneva (Sótano B5)', 'method': 'Encuentro estático al Nivel 70 (Requiere trío Regi)'}]
    },
    487: {
        'type': 'legendary',
        'badge_label': 'Legendario',
        'badge_color': 'purple',
        'summary': 'Encuentro estático en la cámara final de la Cueva Retorno (vía Vía Manantial) al Nivel 70 tras superar los tres pilares en menos de 30 salas.',
        'locations': [{'area': 'Cueva Retorno (Cámara Giratina)', 'method': 'Encuentro estático al Nivel 70'}]
    },
    488: {
        'type': 'legendary',
        'badge_label': 'Errante',
        'badge_color': 'indigo',
        'summary': 'Interaccionar en la Isla Plenilunio tras curar la pesadilla del hijo de Marinero en Ciudad Canal; recorre las rutas de Sinnoh al Nivel 50.',
        'locations': [{'area': 'Rutas de Sinnoh (Errante)', 'method': 'Pokémon errante al Nivel 50 tras visitar Isla Plenilunio'}]
    },
    479: {
        'type': 'legendary',
        'badge_label': 'Vieja Mansión',
        'badge_color': 'indigo',
        'summary': 'Interactuar con el televisor encendido en la Habitación Televisión de la Vieja Mansión (Bosque Vetusto) entre las 20:00 y las 03:59 tras obtener la Pokédex Nacional.',
        'locations': [{'area': 'Vieja Mansión (Televisor)', 'method': 'Encuentro nocturno al Nivel 15 tras Pokédex Nacional'}]
    },

    # Singulares y Eventos Oficiales de Sinnoh
    490: {
        'type': 'event',
        'badge_label': 'Huevo Ranger',
        'badge_color': 'sky',
        'summary': 'Eclosiona del Huevo de Manaphy transferido desde el videojuego Pokémon Ranger para Nintendo DS tras completar la misión especial de la Red Ranger (también puede criar a Phione).',
        'locations': [{'area': 'Transferencia Pokémon Ranger', 'method': 'Huevo especial transferido desde Pokémon Ranger'}, DAYCARE_LOCATION]
    },
    489: {
        'type': 'breeding',
        'badge_label': 'Cría de Manaphy',
        'badge_color': 'sky',
        'summary': 'Eclosiona de un huevo resultante de criar a Manaphy con Ditto en la Guardería de Pueblo Sosiego (Phione nunca puede evolucionar a Manaphy).',
        'locations': [DAYCARE_LOCATION]
    },
    491: {
        'type': 'event',
        'badge_label': 'Evento de Distribución',
        'badge_color': 'purple',
        'summary': 'Obtención mediante distribución oficial de Nintendo o evento de la Tarjeta del Miembro para acceder a la Isla Lunanueva.',
        'locations': [{'area': 'Isla Lunanueva', 'method': 'Evento oficial con Tarjeta del Miembro'}]
    },
    492: {
        'type': 'event',
        'badge_label': 'Evento de Distribución',
        'badge_color': 'emerald',
        'summary': 'Obtención mediante distribución oficial de Nintendo o evento de la Carta de Oak para acceder al Paraíso Floral vía Vía Costera.',
        'locations': [{'area': 'Paraíso Floral', 'method': 'Evento oficial con Carta de Oak'}]
    },
    493: {
        'type': 'event',
        'badge_label': 'Evento de Distribución',
        'badge_color': 'amber',
        'summary': 'Obtención mediante eventos oficiales de distribución de Nintendo (Arceus de película / Toys "R" Us). La Flauta Azur jamás fue distribuida oficialmente.',
        'locations': [{'area': 'Distribución oficial de Nintendo', 'method': 'Evento oficial de distribución / Regalo Misterioso'}],
        'historical_note': {
            'title': 'La Flauta Azur y la Sala del Origen',
            'tag': 'Curiosidad Canónica',
            'icon': '/media/items/rule-book.png',
            'text': 'Aunque en el código interno de Pokémon Diamante, Perla y Platino existe el evento para acceder a la Sala del Origen en la cima de la Columna Lanza tocando la <strong>Flauta Azur</strong> y enfrentarse a Arceus salvaje al Nivel 80, este objeto clave <strong>jamás fue distribuido oficialmente en ningún país del mundo</strong>. Junichi Masuda confirmó que el evento fue descartado por considerarse demasiado confuso para los jugadores. Por tanto, la captura salvaje en la Sala del Origen nunca fue un método legítimo en esta generación: la única vía legal en estas ediciones fue recibirlo en distribuciones oficiales de Nintendo o mediante intercambio.'
        }
    },

    # Exclusivos de Pokémon Diamante (Requieren Intercambio con Diamante en Perla)
    408: {
        'type': 'trade',
        'badge_label': 'Exclusivo Diamante',
        'badge_color': 'blue',
        'summary': 'Exclusivo de Pokémon Diamante (revivir del Fósil Cráneo en Museo Minero de Ciudad Pirita). En Pokémon Perla requiere intercambio con otro jugador (también obtenible mediante crianza).',
        'locations': [
            {'area': 'Intercambio con Pokémon Diamante', 'method': 'Exclusivo de versión (Fósil Cráneo en Diamante)'},
            DAYCARE_LOCATION
        ]
    },
    409: {
        'type': 'trade',
        'badge_label': 'Exclusivo Diamante',
        'badge_color': 'blue',
        'summary': 'Exclusivo de Pokémon Diamante. Evoluciona de Cranidos al Nivel 30 (requiere intercambio desde Pokémon Diamante).',
        'locations': [{'area': 'Intercambio con Pokémon Diamante', 'method': 'Evolución de Cranidos transferido'}]
    },
    434: {
        'type': 'trade',
        'badge_label': 'Exclusivo Diamante',
        'badge_color': 'blue',
        'summary': 'Exclusivo de Pokémon Diamante (salvaje en Rutas 206, 214 y 221). En Pokémon Perla requiere intercambio con otro jugador (también obtenible mediante crianza).',
        'locations': [
            {'area': 'Intercambio con Pokémon Diamante', 'method': 'Exclusivo de versión (Rutas 206, 214 y 221 en Diamante)'},
            DAYCARE_LOCATION
        ]
    },
    435: {
        'type': 'trade',
        'badge_label': 'Exclusivo Diamante',
        'badge_color': 'blue',
        'summary': 'Exclusivo de Pokémon Diamante (salvaje en Rutas 221 y 225 o evolucionando de Stunky al Nivel 34). En Pokémon Perla requiere intercambio.',
        'locations': [{'area': 'Intercambio con Pokémon Diamante', 'method': 'Exclusivo de versión'}]
    },
    198: {
        'type': 'trade',
        'badge_label': 'Exclusivo Diamante',
        'badge_color': 'blue',
        'summary': 'Exclusivo de Pokémon Diamante (salvaje en Bosque Vetusto y Torre Perdida por la noche). En Pokémon Perla requiere intercambio (también obtenible mediante crianza).',
        'locations': [
            {'area': 'Intercambio con Pokémon Diamante', 'method': 'Exclusivo de versión (Bosque Vetusto en Diamante)'},
            DAYCARE_LOCATION
        ]
    },
    430: {
        'type': 'trade',
        'badge_label': 'Exclusivo Diamante',
        'badge_color': 'blue',
        'summary': 'Exclusivo de Pokémon Diamante. Evoluciona de Murkrow usando Piedra Noche (requiere intercambio desde Pokémon Diamante).',
        'locations': [{'area': 'Intercambio con Pokémon Diamante', 'method': 'Evolución de Murkrow transferido'}]
    },
    483: {
        'type': 'trade',
        'badge_label': 'Exclusivo Diamante',
        'badge_color': 'blue',
        'summary': 'Exclusivo de Pokémon Diamante (encuentro estático en la Columna Lanza al Nivel 47). En Pokémon Perla requiere intercambio con un jugador de Diamante.',
        'locations': [{'area': 'Intercambio con Pokémon Diamante', 'method': 'Legendario exclusivo de portada de Diamante'}]
    },
    86: {
        'type': 'trade',
        'badge_label': 'Exclusivo Diamante',
        'badge_color': 'blue',
        'summary': 'Exclusivo de Pokémon Diamante (salvaje en Rutas 226 y 230 con Surf). En Pokémon Perla requiere intercambio (también obtenible mediante crianza).',
        'locations': [{'area': 'Intercambio con Pokémon Diamante', 'method': 'Exclusivo de versión'}, DAYCARE_LOCATION]
    },
    87: {
        'type': 'trade',
        'badge_label': 'Exclusivo Diamante',
        'badge_color': 'blue',
        'summary': 'Exclusivo de Pokémon Diamante (salvaje en Rutas 226 y 230 o evolución al Nivel 34). En Pokémon Perla requiere intercambio.',
        'locations': [{'area': 'Intercambio con Pokémon Diamante', 'method': 'Exclusivo de versión'}]
    },
    123: {
        'type': 'trade',
        'badge_label': 'Exclusivo Diamante',
        'badge_color': 'blue',
        'summary': 'Exclusivo de Pokémon Diamante (salvaje en Ruta 229). En Pokémon Perla requiere intercambio (también obtenible mediante crianza).',
        'locations': [{'area': 'Intercambio con Pokémon Diamante', 'method': 'Exclusivo de versión'}, DAYCARE_LOCATION]
    },
    212: {
        'type': 'trade',
        'badge_label': 'Exclusivo Diamante',
        'badge_color': 'blue',
        'summary': 'Exclusivo de Pokémon Diamante. Evoluciona de Scyther por intercambio equipado con Revestimiento Metálico.',
        'locations': [{'area': 'Intercambio con Pokémon Diamante', 'method': 'Evolución de Scyther transferido'}]
    },
    261: {
        'type': 'trade',
        'badge_label': 'Exclusivo Diamante',
        'badge_color': 'blue',
        'summary': 'Exclusivo de Pokémon Diamante (salvaje en Ruta 214 con Poké Radar). En Pokémon Perla requiere intercambio (también obtenible mediante crianza).',
        'locations': [{'area': 'Intercambio con Pokémon Diamante', 'method': 'Exclusivo de versión'}, DAYCARE_LOCATION]
    },
    262: {
        'type': 'trade',
        'badge_label': 'Exclusivo Diamante',
        'badge_color': 'blue',
        'summary': 'Exclusivo de Pokémon Diamante (salvaje en Rutas 214 y 215 con Poké Radar o al Nivel 18). En Pokémon Perla requiere intercambio.',
        'locations': [{'area': 'Intercambio con Pokémon Diamante', 'method': 'Exclusivo de versión'}]
    },
    304: {
        'type': 'trade',
        'badge_label': 'Exclusivo Diamante',
        'badge_color': 'blue',
        'summary': 'Exclusivo de Pokémon Diamante (salvaje en Forja Fuego con Poké Radar). En Pokémon Perla requiere intercambio (también obtenible mediante crianza).',
        'locations': [{'area': 'Intercambio con Pokémon Diamante', 'method': 'Exclusivo de versión'}, DAYCARE_LOCATION]
    },
    305: {
        'type': 'trade',
        'badge_label': 'Exclusivo Diamante',
        'badge_color': 'blue',
        'summary': 'Exclusivo de Pokémon Diamante. Evoluciona de Aron al Nivel 32.',
        'locations': [{'area': 'Intercambio con Pokémon Diamante', 'method': 'Evolución de Aron transferido'}]
    },
    306: {
        'type': 'trade',
        'badge_label': 'Exclusivo Diamante',
        'badge_color': 'blue',
        'summary': 'Exclusivo de Pokémon Diamante. Evoluciona de Lairon al Nivel 42.',
        'locations': [{'area': 'Intercambio con Pokémon Diamante', 'method': 'Evolución de Lairon transferido'}]
    },
    246: {
        'type': 'trade',
        'badge_label': 'Exclusivo Diamante',
        'badge_color': 'blue',
        'summary': 'Exclusivo de Pokémon Diamante (salvaje en Ruta 207 con Poké Radar). En Pokémon Perla requiere intercambio (también obtenible mediante crianza).',
        'locations': [{'area': 'Intercambio con Pokémon Diamante', 'method': 'Exclusivo de versión'}, DAYCARE_LOCATION]
    },
    247: {
        'type': 'trade',
        'badge_label': 'Exclusivo Diamante',
        'badge_color': 'blue',
        'summary': 'Exclusivo de Pokémon Diamante. Evoluciona de Larvitar al Nivel 30.',
        'locations': [{'area': 'Intercambio con Pokémon Diamante', 'method': 'Evolución de Larvitar transferido'}]
    },
    248: {
        'type': 'trade',
        'badge_label': 'Exclusivo Diamante',
        'badge_color': 'blue',
        'summary': 'Exclusivo de Pokémon Diamante. Evoluciona de Pupitar al Nivel 55.',
        'locations': [{'area': 'Intercambio con Pokémon Diamante', 'method': 'Evolución de Pupitar transferido'}]
    },
    352: {
        'type': 'trade',
        'badge_label': 'Exclusivo Diamante',
        'badge_color': 'blue',
        'summary': 'Exclusivo de Pokémon Diamante (salvaje en Ruta 210 norte con Poké Radar). En Pokémon Perla requiere intercambio (también obtenible mediante crianza).',
        'locations': [{'area': 'Intercambio con Pokémon Diamante', 'method': 'Exclusivo de versión'}, DAYCARE_LOCATION]
    },

    # Gengar: Evolución por intercambio y salvaje por Inserción Dual (Cualquier GBA)
    94: {
        'type': 'evolution',
        'badge_label': 'Evolución',
        'badge_color': 'indigo',
        'summary': 'Evoluciona de Haunter por intercambio. También aparece en estado salvaje en la Vieja Mansión (Habitación del Cuadro) insertando cualquier cartucho de GBA en la Ranura 2 de NDS.',
        'locations': [
            {'area': 'Vieja Mansión (Habitación del Cuadro)', 'method': 'Inserción Dual (Cualquier GBA)'}
        ],
        'evolution_info': {
            'from': 'Haunter',
            'text': 'Evoluciona de Haunter (por intercambio)',
            'trigger': 'trade',
            'condition': 'por intercambio',
            'item_slug': None
        }
    },
}


def format_wild_method(method_raw: str, conditions: list) -> str:
    """Traduce métodos crudos de PokeAPI al castellano oficial canónico."""
    dual_map = {
        'slot2-firered': 'Inserción Dual (GBA: Pokémon Rojo Fuego)',
        'slot2-leafgreen': 'Inserción Dual (GBA: Pokémon Verde Hoja)',
        'slot2-ruby': 'Inserción Dual (GBA: Pokémon Rubí)',
        'slot2-sapphire': 'Inserción Dual (GBA: Pokémon Zafiro)',
        'slot2-emerald': 'Inserción Dual (GBA: Pokémon Esmeralda)',
    }
    for cond in conditions:
        if cond in dual_map:
            return dual_map[cond]

    if 'radar-on' in conditions or 'radar' in conditions or any('radar' in c for c in conditions):
        return 'Poké Radar'
    if 'swarm-yes' in conditions or 'swarm' in conditions or any('swarm' in c for c in conditions):
        return 'Manada diaria'

    if method_raw == 'walk':
        return 'Hierba alta / Terreno'
    if method_raw == 'surf':
        return 'Navegando con Surf'
    if method_raw == 'old-rod':
        return 'Pescando (Caña Vieja)'
    if method_raw == 'good-rod':
        return 'Pescando (Caña Buena)'
    if method_raw == 'super-rod':
        return 'Pescando (Supercaña)'
    if method_raw == 'rock-smash':
        return 'Golpe Roca'
    if method_raw == 'headbutt':
        return 'Golpe Cabeza'
    if method_raw == 'only-one':
        return 'Encuentro estático'
    if method_raw == 'gift':
        return 'Regalo in-game'
    if method_raw == 'honey-tree':
        return 'Árboles de Miel'
    if method_raw in ('dark-grass', 'grass'):
        return 'Hierba alta / Terreno'
    if method_raw == 'npc-trade':
        trade_desc_map = {
            'trade-buizel': 'Intercambio in-game (por Buizel)',
            'trade-machop': 'Intercambio in-game (por Machop)',
            'trade-medicham': 'Intercambio in-game (por Medicham con Piedra Eterna)',
            'trade-finneon': 'Intercambio in-game (por Finneon)',
        }
        for cond, desc in trade_desc_map.items():
            if cond in conditions:
                return desc
        return 'Intercambio in-game (NPC)'
    return 'Salvaje'


def main():
    print("Iniciando compilación oficial de catálogos para Pokémon Perla...")

    with open(CACHE_DIR / "pokemon_493_species.json", "r", encoding="utf-8") as f:
        species_493 = json.load(f)

    with open(CACHE_DIR / "encounters_pearl.json", "r", encoding="utf-8") as f:
        encounters_pearl = json.load(f)

    with open(CACHE_DIR / "wikidex_pearl_descriptions.json", "r", encoding="utf-8") as f:
        descriptions = json.load(f)

    with open(CACHE_DIR / "sinnoh_pokedex_151.json", "r", encoding="utf-8") as f:
        sinnoh_151 = json.load(f)

    with open(CACHE_DIR / "gen4_evolutions.json", "r", encoding="utf-8") as f:
        gen4_evos = json.load(f)

    with open(BASE_DIR / "tracker" / "data" / "evolution_stones.json", "r", encoding="utf-8") as f:
        evolution_stones = json.load(f)

    # Cargar transferencias desde exclusives.py
    from tracker.exclusives import VERSION_TRANSFERS_CATALOG, VERSION_TRANSFERS_META
    pearl_transfers = set(VERSION_TRANSFERS_CATALOG.get("pearl", []))
    pearl_origins = VERSION_TRANSFERS_META.get("pearl", {}).get("origins", {})

    def build_entry(nat_id: int, entry_num: int, is_regional: bool, unique_id: int):
        sp = species_493[str(nat_id)]
        flavor = descriptions.get(str(nat_id), "")
        sp_name = sp['name'].lower()
        egg_groups = sp.get('egg_groups', [])
        evo_info = gen4_evos.get(str(nat_id))

        is_baby = sp_name in BABY_NAMES
        is_incense_parent = sp_name in INCENSE_PARENTS_THAT_HATCH
        is_evolution = (evo_info is not None) and not is_incense_parent

        # Regla Universal de Crianza
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

        raw_encs = encounters_pearl.get(str(nat_id), [])
        evo_stone_obj = None

        if nat_id in SPECIAL_OBTAINING:
            obt_info = json.loads(json.dumps(SPECIAL_OBTAINING[nat_id]))
        elif raw_encs:
            # Procesar encuentros salvajes agrupados
            area_methods = {}
            for e in raw_encs:
                area_key = e.get('area_raw', '')
                clean_area = SINNOH_AREA_NAMES.get(area_key, area_key.replace('-', ' ').title())
                meth_desc = format_wild_method(e.get('method_raw', 'walk'), e.get('conditions', []))
                if clean_area not in area_methods:
                    area_methods[clean_area] = set()
                area_methods[clean_area].add(meth_desc)

            loc_list = []
            for a_name, m_set in area_methods.items():
                non_dual = [m for m in m_set if not m.startswith('Inserción Dual')]
                dual = [m for m in m_set if m.startswith('Inserción Dual')]
                if non_dual and dual:
                    final_methods = sorted(non_dual)
                elif dual:
                    if len(dual) >= 5:
                        final_methods = ['Inserción Dual (Cualquier GBA)']
                    else:
                        final_methods = sorted(dual)
                else:
                    final_methods = sorted(list(m_set))

                loc_list.append({
                    'area': a_name,
                    'method': ", ".join(final_methods)
                })

            if is_hatchable:
                loc_list.append(DAYCARE_LOCATION)

            num_zones = len(area_methods)
            zone_names = list(area_methods.keys())

            # Detectar si requiere dual-slot como método exclusivo
            all_conditions = [e.get('conditions', []) for e in raw_encs]
            has_clean_wild = any(not any('slot2-' in c for c in conds) for conds in all_conditions)
            dual_slots_found = set()
            for conds in all_conditions:
                for c in conds:
                    if 'slot2-' in c:
                        dual_slots_found.add(c)

            dual_note = ""
            if dual_slots_found and not has_clean_wild:
                if 'slot2-firered' in dual_slots_found and len(dual_slots_found) == 1:
                    dual_note = " (requiere cartucho de Pokémon Rojo Fuego en Ranura 2 de NDS)"
                elif 'slot2-leafgreen' in dual_slots_found and len(dual_slots_found) == 1:
                    dual_note = " (requiere cartucho de Pokémon Verde Hoja en Ranura 2 de NDS)"
                elif 'slot2-ruby' in dual_slots_found and len(dual_slots_found) == 1:
                    dual_note = " (requiere cartucho de Pokémon Rubí en Ranura 2 de NDS)"
                elif 'slot2-sapphire' in dual_slots_found and len(dual_slots_found) == 1:
                    dual_note = " (requiere cartucho de Pokémon Zafiro en Ranura 2 de NDS)"
                elif 'slot2-emerald' in dual_slots_found and len(dual_slots_found) == 1:
                    dual_note = " (requiere cartucho de Pokémon Esmeralda en Ranura 2 de NDS)"
                else:
                    dual_note = " (requiere cartucho de GBA compatible en Ranura 2 de NDS)"

            if num_zones == 1:
                summary = f"Salvaje en {zone_names[0]}{dual_note}."
            elif num_zones in (2, 3):
                summary = f"Salvaje en: {', '.join(zone_names)}{dual_note}."
            else:
                examples = ", ".join(zone_names[:3])
                summary = f"Salvaje en {num_zones} zonas (ej: {examples}){dual_note}."

            if is_hatchable:
                summary = summary.rstrip('.') + " (también obtenible mediante crianza)."

            obt_info = {
                'type': 'wild',
                'badge_label': 'Salvaje',
                'badge_color': 'emerald',
                'summary': summary,
                'locations': loc_list
            }

        elif evo_info:
            cond_str = evo_info.get('condition', '')
            item_slug = evo_info.get('item_slug')
            summary = evo_info.get('text', '')

            obt_info = {
                'type': 'evolution',
                'badge_label': 'Evolución',
                'badge_color': 'indigo',
                'summary': summary,
                'locations': [],
                'evolution_info': {
                    'from': evo_info.get('from_name'),
                    'text': summary,
                    'trigger': evo_info.get('trigger', 'level-up'),
                    'condition': cond_str,
                    'item_slug': item_slug
                }
            }

        elif nat_id in pearl_transfers:
            origin = pearl_origins.get(nat_id, 'Cartuchos de GBA (RSE/FRLG)')
            summary = f"Inaccesible en estado salvaje en Pokémon Perla. Requiere transferir desde {origin} mediante el Parque Compi (Ruta 221) o mediante intercambio con otras ediciones"
            if is_hatchable:
                summary += " (también obtenible mediante crianza)."
            else:
                summary += "."

            locs = [{'area': 'Parque Compi (Ruta 221)', 'method': f'Transferencia desde {origin}'}]
            if is_hatchable:
                locs.append(DAYCARE_LOCATION)

            obt_info = {
                'type': 'transfer',
                'badge_label': 'Parque Compi',
                'badge_color': 'amber',
                'summary': summary,
                'locations': locs
            }
        else:
            obt_info = {
                'type': 'event',
                'badge_label': 'Especial',
                'badge_color': 'slate',
                'summary': 'Obtención mediante distribución oficial o evento de Nintendo.',
                'locations': []
            }

        # 1. Conservar metadatos de evolución universalmente
        if evo_info and 'evolution_info' not in obt_info:
            obt_info['evolution_info'] = {
                'from': evo_info.get('from_name'),
                'text': evo_info.get('text', ''),
                'trigger': evo_info.get('trigger', 'level-up'),
                'condition': evo_info.get('condition', ''),
                'item_slug': evo_info.get('item_slug')
            }

        # 2. Manejo universal de Inciensos de Crianza para Bebés (Gen 3 a Gen 8)
        baby_incense_slug = get_incense_for_baby(nat_id, generation=4)
        
        raw_locations = obt_info.get('locations', [])
        new_locations = []
        has_daycare = False
        for loc in raw_locations:
            if 'guardería' in loc.get('area', '').lower() or 'guarderia' in loc.get('area', '').lower():
                has_daycare = True
                if baby_incense_slug:
                    incense_name = evolution_stones.get(baby_incense_slug, {}).get('name_es', 'Incienso')
                    new_locations.append({
                        'area': 'Pueblo Sosiego (Guardería Pokémon)',
                        'method': f"Crianza con {incense_name}"
                    })
                else:
                    new_locations.append({
                        'area': 'Pueblo Sosiego (Guardería Pokémon)',
                        'method': 'Crianza de huevo'
                    })
            else:
                new_locations.append({'area': loc.get('area', ''), 'method': loc.get('method', '')})

        if is_hatchable and not has_daycare:
            if baby_incense_slug:
                incense_name = evolution_stones.get(baby_incense_slug, {}).get('name_es', 'Incienso')
                new_locations.append({
                    'area': 'Pueblo Sosiego (Guardería Pokémon)',
                    'method': f"Crianza con {incense_name}"
                })
            else:
                new_locations.append({
                    'area': 'Pueblo Sosiego (Guardería Pokémon)',
                    'method': 'Crianza de huevo'
                })

        obt_info['locations'] = new_locations

        # 3. Resolución universal del objeto evolutivo o incienso
        item_slug_to_resolve = baby_incense_slug or (evo_info.get('item_slug') if evo_info else None) or obt_info.get('item_slug')
        if item_slug_to_resolve:
            evo_stone_obj = resolve_evolution_stone(item_slug=item_slug_to_resolve, game_slug="pearl")
        else:
            evo_stone_obj = None

        p_type = sp['primary_type']
        s_type = sp['secondary_type']

        entry = {
            "id": unique_id,
            "entry_number": entry_num,
            "game_slug": "pearl",
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
            "game_sprite_url": f"/media/pokemon/sprites/pearl/{nat_id}.png",
            "game_sprite_shiny_url": f"/media/pokemon/sprites/pearl_shiny/{nat_id}.png",
            "game_sprite_back_url": f"/media/pokemon/sprites/pearl/back/{nat_id}.png",
            "game_sprite_shiny_back_url": f"/media/pokemon/sprites/pearl_shiny/back/{nat_id}.png",
            "modern_sprite_shiny_url": f"/media/pokemon/artwork/shiny/{nat_id}.png",
            "modal_retro_sprite_url": f"/media/pokemon/sprites/pearl_animated/{nat_id}.png",
            "modal_retro_sprite_shiny_url": f"/media/pokemon/sprites/pearl_animated_shiny/{nat_id}.png",
            "modal_retro_sprite_back_url": f"/media/pokemon/sprites/pearl/back/{nat_id}.png",
            "modal_retro_sprite_shiny_back_url": f"/media/pokemon/sprites/pearl_shiny/back/{nat_id}.png",
            "pc_icon_url": f"/media/pokemon/icons/gen4/{nat_id}.png",
            "cry_url": f"/media/pokemon/cries/legacy/{nat_id}.ogg",
            "flavor_text": flavor,
            "obtaining_info": obt_info,
            "evolution_stone": evo_stone_obj,
            "game_data": {
                "generation": 4,
                "game_slug": "pearl",
                "game_name": "Pokémon Perla",
                "is_regional": is_regional
            }
        }
        return entry

    # 1. Compilar Pokédex Regional (pearl.json - 151 Pokémon)
    print("Compilando Pokédex Regional de Sinnoh en Perla (151 entradas)...")
    pearl_regional_catalog = []
    for reg_num in range(1, 152):
        nat_id = int(sinnoh_151[str(reg_num)])
        unique_id = 4000 + reg_num
        pearl_regional_catalog.append(build_entry(nat_id, reg_num, is_regional=True, unique_id=unique_id))

    regional_file = CATALOGS_DIR / "pearl.json"
    with open(regional_file, "w", encoding="utf-8") as f:
        json.dump(pearl_regional_catalog, f, ensure_ascii=False, indent=2)
    print(f"[OK] Guardado {regional_file} con {len(pearl_regional_catalog)} entradas.")

    # 2. Compilar Pokédex Nacional (pearl_national.json - 493 Pokémon)
    print("Compilando Pokédex Nacional de Perla (493 entradas)...")
    pearl_national_catalog = []
    for nat_num in range(1, 494):
        unique_id = 4200 + nat_num
        pearl_national_catalog.append(build_entry(nat_num, nat_num, is_regional=False, unique_id=unique_id))

    national_file = CATALOGS_DIR / "pearl_national.json"
    with open(national_file, "w", encoding="utf-8") as f:
        json.dump(pearl_national_catalog, f, ensure_ascii=False, indent=2)
    print(f"[OK] Guardado {national_file} con {len(pearl_national_catalog)} entradas.")


if __name__ == "__main__":
    main()
