"""
Script para compilar y generar los catálogos oficiales JSON de Pokémon Oro HeartGold
para PokedexGlobal a 0 ms SQL:
1. Pokédex Regional de Johto Actualizada: tracker/data/catalogs/heartgold.json (256 especies canónicas)
2. Pokédex Nacional: tracker/data/catalogs/heartgold_national.json (493 especies canónicas)
"""
import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pokedex.settings')
import django
django.setup()

import json
from tracker.utils import get_incense_for_baby

CACHE_DIR = BASE_DIR / "tracker" / "data" / "cache"
CATALOGS_DIR = BASE_DIR / "tracker" / "data" / "catalogs"
CATALOGS_DIR.mkdir(parents=True, exist_ok=True)

TYPE_NAMES_ES = {
    'normal': 'Normal', 'fire': 'Fuego', 'water': 'Agua', 'electric': 'Eléctrico',
    'grass': 'Planta', 'ice': 'Hielo', 'fighting': 'Lucha', 'poison': 'Veneno',
    'ground': 'Tierra', 'flying': 'Volador', 'psychic': 'Psíquico', 'bug': 'Bicho',
    'rock': 'Roca', 'ghost': 'Fantasma', 'dragon': 'Dragón', 'steel': 'Acero',
    'dark': 'Siniestro', 'fairy': 'Hada'
}

JOHTO_KANTO_AREA_NAMES = {
    'azalea-town-area': 'Pueblo Azalea',
    'bell-tower-2f': 'Torre Campana (P2)',
    'bell-tower-3f': 'Torre Campana (P3)',
    'bell-tower-4f': 'Torre Campana (P4)',
    'bell-tower-5f': 'Torre Campana (P5)',
    'bell-tower-6f': 'Torre Campana (P6)',
    'bell-tower-7f': 'Torre Campana (P7)',
    'bell-tower-8f': 'Torre Campana (P8)',
    'bell-tower-9f': 'Torre Campana (P9)',
    'bell-tower-10f': 'Torre Campana (P10)',
    'bell-tower-roof': 'Torre Campana (Azotea - Ho-Oh)',
    'blackthorn-city-area': 'Ciudad Endrino',
    'burned-tower-1f': 'Torre Quemada (P1)',
    'burned-tower-b1f': 'Torre Quemada (Sótano B1)',
    'celadon-city-area': 'Ciudad Azulona',
    'celadon-city-prize-corner': 'Ciudad Azulona (Rincón de Premios)',
    'cerulean-cave-1f': 'Cueva Celeste (P1)',
    'cerulean-cave-2f': 'Cueva Celeste (P2)',
    'cerulean-cave-b1f': 'Cueva Celeste (Sótano B1 - Mewtwo)',
    'cerulean-city-area': 'Ciudad Celeste',
    'cherrygrove-city-area': 'Ciudad Cerezo',
    'cianwood-city-area': 'Ciudad Orquídea',
    'cinnabar-island-area': 'Isla Canela',
    'cliff-cave-area': 'Cueva Acantilado',
    'cliff-cave-inside': 'Cueva Acantilado (Interior)',
    'dark-cave-blackthorn-city-entrance': 'Cueva Oscura (Entrada Ciudad Endrino)',
    'dark-cave-route-31-entrance': 'Cueva Oscura (Entrada Ruta 31)',
    'dark-cave-route-45-entrance': 'Cueva Oscura (Entrada Ruta 45)',
    'digletts-cave-area': 'Cueva Diglett',
    'dragons-den-area': 'Guarida Dragón',
    'dragons-den-b1f': 'Guarida Dragón (Sótano)',
    'ecruteak-city-area': 'Ciudad Iris',
    'embedded-tower-area': 'Torre Oculta (Ruta 47)',
    'fuchsia-city-area': 'Ciudad Fucsia',
    'goldenrod-city-area': 'Ciudad Trigal',
    'ice-path-1f': 'Ruta Helada (P1)',
    'ice-path-b1f': 'Ruta Helada (Sótano B1)',
    'ice-path-b2f-mahogany-side': 'Ruta Helada (Sótano B2 Caoba)',
    'ice-path-b2f-blackthorn-side': 'Ruta Helada (Sótano B2 Endrino)',
    'ice-path-b3f': 'Ruta Helada (Sótano B3)',
    'ilex-forest-area': 'Encinar',
    'johto-route-29-area': 'Ruta 29',
    'johto-route-30-area': 'Ruta 30',
    'johto-route-31-area': 'Ruta 31',
    'johto-route-32-area': 'Ruta 32',
    'johto-route-33-area': 'Ruta 33',
    'johto-route-34-area': 'Ruta 34',
    'johto-route-35-area': 'Ruta 35',
    'johto-route-36-area': 'Ruta 36',
    'johto-route-37-area': 'Ruta 37',
    'johto-route-38-area': 'Ruta 38',
    'johto-route-39-area': 'Ruta 39',
    'johto-route-42-area': 'Ruta 42',
    'johto-route-43-area': 'Ruta 43',
    'johto-route-44-area': 'Ruta 44',
    'johto-route-45-area': 'Ruta 45',
    'johto-route-46-area': 'Ruta 46',
    'johto-route-47-area': 'Ruta 47',
    'johto-route-48-area': 'Ruta 48',
    'johto-sea-route-40-area': 'Ruta 40 (Ruta Marítima)',
    'johto-sea-route-41-area': 'Ruta 41 (Ruta Marítima)',
    'kanto-route-1-area': 'Ruta 1',
    'kanto-route-2-area': 'Ruta 2',
    'kanto-route-3-area': 'Ruta 3',
    'kanto-route-4-area': 'Ruta 4',
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
    'kanto-route-21-area': 'Ruta 21 (Ruta Marítima)',
    'kanto-route-22-area': 'Ruta 22',
    'kanto-route-24-area': 'Ruta 24',
    'kanto-route-25-area': 'Ruta 25',
    'kanto-route-26-area': 'Ruta 26',
    'kanto-route-27-area': 'Ruta 27',
    'kanto-route-28-area': 'Ruta 28',
    'kanto-sea-route-19-area': 'Ruta 19 (Ruta Marítima)',
    'kanto-sea-route-20-area': 'Ruta 20 (Ruta Marítima)',
    'kanto-victory-road-1f': 'Calle Victoria (P1)',
    'kanto-victory-road-2f': 'Calle Victoria (P2)',
    'kanto-victory-road-3f': 'Calle Victoria (P3)',
    'lake-of-rage-area': 'Lago de la Furia',
    'mt-moon-1f': 'Monte Moon (P1)',
    'mt-moon-2f': 'Monte Moon (P2)',
    'mt-mortar-1f-outside': 'Monte Mortero (Entrada P1)',
    'mt-mortar-1f-inside': 'Monte Mortero (Interior P1)',
    'mt-mortar-2f-inside': 'Monte Mortero (Interior P2)',
    'mt-mortar-b1f': 'Monte Mortero (Sótano B1)',
    'mt-silver-1f': 'Monte Plateado (P1)',
    'mt-silver-2f': 'Monte Plateado (P2)',
    'mt-silver-3f': 'Monte Plateado (P3)',
    'mt-silver-cave-room-1': 'Monte Plateado (Cueva Sala 1)',
    'mt-silver-cave-room-2': 'Monte Plateado (Cueva Sala 2)',
    'mt-silver-cave-room-3': 'Monte Plateado (Cima - Rojo)',
    'mt-silver-mountainside': 'Monte Plateado (Laderas)',
    'mt-silver-summit': 'Monte Plateado (Cima Exterior)',
    'national-park-area': 'Parque Nacional',
    'new-bark-town-area': 'Pueblo Primavera',
    'olivine-city-area': 'Ciudad Olivo',
    'pallet-town-area': 'Pueblo Paleta',
    'pewter-city-area': 'Ciudad Plateada',
    'pokeathlon-dome-area': 'Domo Pokéathlon',
    'power-plant-area': 'Central de Energía (Exterior)',
    'roaming-johto-area': 'Rutas de Johto (Errante)',
    'roaming-kanto-area': 'Rutas de Kanto (Errante)',
    'rock-tunnel-1f': 'Túnel Roca (P1)',
    'rock-tunnel-b1f': 'Túnel Roca (Sótano B1)',
    'ruins-of-alph-area': 'Ruinas Alfa (Exterior)',
    'ruins-of-alph-aerodactyl-chamber': 'Ruinas Alfa (Cámara de Aerodactyl)',
    'ruins-of-alph-ho-oh-chamber': 'Ruinas Alfa (Cámara de Ho-Oh)',
    'ruins-of-alph-kabuto-chamber': 'Ruinas Alfa (Cámara de Kabuto)',
    'ruins-of-alph-omanyte-chamber': 'Ruinas Alfa (Cámara de Omanyte)',
    'ruins-of-alph-inner-chamber': 'Ruinas Alfa (Cámara Principal)',
    'safari-zone-gate-area': 'Zona Safari (Bahía Blanca)',
    'saffron-city-area': 'Ciudad Azafrán',
    'seafoam-islands-1f': 'Islas Espuma (P1)',
    'seafoam-islands-b1f': 'Islas Espuma (Sótano B1)',
    'seafoam-islands-b2f': 'Islas Espuma (Sótano B2)',
    'seafoam-islands-b3f': 'Islas Espuma (Sótano B3)',
    'seafoam-islands-b4f': 'Islas Espuma (Sótano B4 - Articuno)',
    'sinjoh-ruins-area': 'Ruinas de Sinjoh',
    'slowpoke-well-1f': 'Pozo Slowpoke (P1)',
    'slowpoke-well-b1f': 'Pozo Slowpoke (Sótano B1)',
    'slowpoke-well-b2f': 'Pozo Slowpoke (Sótano B2)',
    'sprout-tower-1f': 'Torre Bellsprout (P1)',
    'sprout-tower-2f': 'Torre Bellsprout (P2)',
    'sprout-tower-3f': 'Torre Bellsprout (P3)',
    'team-rocket-hq-b1f': 'Guarida Team Rocket (Sótano B1)',
    'team-rocket-hq-b2f': 'Guarida Team Rocket (Sótano B2)',
    'team-rocket-hq-b3f': 'Guarida Team Rocket (Sótano B3)',
    'tohjo-falls-area': 'Cataratas Tohjo',
    'union-cave-1f': 'Cueva Unión (P1)',
    'union-cave-b1f': 'Cueva Unión (Sótano B1)',
    'union-cave-b2f': 'Cueva Unión (Sótano B2 - Lapras)',
    'vermilion-city-area': 'Ciudad Carmín',
    'violet-city-area': 'Ciudad Malva',
    'viridian-city-area': 'Ciudad Verde',
    'viridian-forest-area': 'Bosque Verde',
    'whirl-islands-1f': 'Islas Remolino (P1)',
    'whirl-islands-b1f': 'Islas Remolino (Sótano B1)',
    'whirl-islands-b2f': 'Islas Remolino (Sótano B2)',
    'whirl-islands-b3f': 'Islas Remolino (Sótano B3 - Lugia)',
}

BABY_NAMES = {
    'pichu', 'cleffa', 'igglybuff', 'togepi', 'tyrogue', 'smoochum',
    'elekid', 'magby', 'azurill', 'wynaut', 'budew', 'chingling',
    'bonsly', 'mime-jr', 'happiny', 'munchlax', 'riolu', 'mantyke'
}

INCENSE_PARENTS_THAT_HATCH = {
    'marill', 'wobbuffet', 'roselia', 'chimecho', 'sudowoodo',
    'mr-mime', 'chansey', 'snorlax', 'mantine'
}

NON_BREEDABLE_NAMES = {
    'articuno', 'zapdos', 'moltres', 'mewtwo', 'mew',
    'raikou', 'entei', 'suicune', 'lugia', 'ho-oh', 'celebi',
    'regirock', 'regice', 'registeel', 'latias', 'latios',
    'kyogre', 'groudon', 'rayquaza', 'jirachi', 'deoxys',
    'uxie', 'mesprit', 'azelf', 'dialga', 'palkia', 'heatran',
    'regigigas', 'giratina', 'cresselia', 'darkrai', 'shaymin', 'arceus',
    'unown'
}

DAYCARE_LOCATION = {
    'area': 'Ruta 34 (Guardería Pokémon)',
    'method': 'Crianza de huevo'
}

SPECIAL_OBTAINING = {
    # Iniciales de Johto
    152: {
        'type': 'starter',
        'badge_label': 'Inicial',
        'badge_color': 'emerald',
        'summary': 'Elegir en el laboratorio del Profesor Elm en Pueblo Primavera al inicio de la aventura (también obtenible por crianza).',
        'locations': [
            {'area': 'Pueblo Primavera (Laboratorio de Elm)', 'method': 'Elección de Inicial de Johto'},
            DAYCARE_LOCATION
        ]
    },
    155: {
        'type': 'starter',
        'badge_label': 'Inicial',
        'badge_color': 'amber',
        'summary': 'Elegir en el laboratorio del Profesor Elm en Pueblo Primavera al inicio de la aventura (también obtenible por crianza).',
        'locations': [
            {'area': 'Pueblo Primavera (Laboratorio de Elm)', 'method': 'Elección de Inicial de Johto'},
            DAYCARE_LOCATION
        ]
    },
    158: {
        'type': 'starter',
        'badge_label': 'Inicial',
        'badge_color': 'cyan',
        'summary': 'Elegir en el laboratorio del Profesor Elm en Pueblo Primavera al inicio de la aventura (también obtenible por crianza).',
        'locations': [
            {'area': 'Pueblo Primavera (Laboratorio de Elm)', 'method': 'Elección de Inicial de Johto'},
            DAYCARE_LOCATION
        ]
    },

    # Iniciales de Kanto
    1: {
        'type': 'starter',
        'badge_label': 'Regalo Post-Game',
        'badge_color': 'emerald',
        'summary': 'Regalo del Profesor Oak en su laboratorio de Pueblo Paleta tras derrotar a Rojo en el Monte Plateado (también obtenible por crianza).',
        'locations': [
            {'area': 'Pueblo Paleta (Laboratorio de Oak)', 'method': 'Regalo Post-Game (Inicial de Kanto)'},
            DAYCARE_LOCATION
        ]
    },
    4: {
        'type': 'starter',
        'badge_label': 'Regalo Post-Game',
        'badge_color': 'amber',
        'summary': 'Regalo del Profesor Oak en su laboratorio de Pueblo Paleta tras derrotar a Rojo en el Monte Plateado (también obtenible por crianza).',
        'locations': [
            {'area': 'Pueblo Paleta (Laboratorio de Oak)', 'method': 'Regalo Post-Game (Inicial de Kanto)'},
            DAYCARE_LOCATION
        ]
    },
    7: {
        'type': 'starter',
        'badge_label': 'Regalo Post-Game',
        'badge_color': 'cyan',
        'summary': 'Regalo del Profesor Oak en su laboratorio de Pueblo Paleta tras derrotar a Rojo en el Monte Plateado (también obtenible por crianza).',
        'locations': [
            {'area': 'Pueblo Paleta (Laboratorio de Oak)', 'method': 'Regalo Post-Game (Inicial de Kanto)'},
            DAYCARE_LOCATION
        ]
    },

    # Iniciales de Hoenn
    252: {
        'type': 'starter',
        'badge_label': 'Regalo Post-Game',
        'badge_color': 'emerald',
        'summary': 'Regalo de Máximo Peñas en el vestíbulo de Silph S.A. en Ciudad Azafrán tras vencer a Rojo (también obtenible por crianza).',
        'locations': [
            {'area': 'Ciudad Azafrán (Silph S.A.)', 'method': 'Regalo de Máximo Peñas (Inicial de Hoenn)'},
            DAYCARE_LOCATION
        ]
    },
    255: {
        'type': 'starter',
        'badge_label': 'Regalo Post-Game',
        'badge_color': 'amber',
        'summary': 'Regalo de Máximo Peñas en el vestíbulo de Silph S.A. en Ciudad Azafrán tras vencer a Rojo (también obtenible por crianza).',
        'locations': [
            {'area': 'Ciudad Azafrán (Silph S.A.)', 'method': 'Regalo de Máximo Peñas (Inicial de Hoenn)'},
            DAYCARE_LOCATION
        ]
    },
    258: {
        'type': 'starter',
        'badge_label': 'Regalo Post-Game',
        'badge_color': 'cyan',
        'summary': 'Regalo de Máximo Peñas en el vestíbulo de Silph S.A. en Ciudad Azafrán tras vencer a Rojo (también obtenible por crianza).',
        'locations': [
            {'area': 'Ciudad Azafrán (Silph S.A.)', 'method': 'Regalo de Máximo Peñas (Inicial de Hoenn)'},
            DAYCARE_LOCATION
        ]
    },

    # Fósiles
    138: {
        'type': 'fossil',
        'badge_label': 'Fósil Hélix',
        'badge_color': 'amber',
        'summary': 'Revivir el Fósil Hélix (exclusivo de HeartGold rompiendo rocas con Golpe Roca en las Ruinas Alfa) en el Museo de Ciudad Plateada.',
        'locations': [
            {'area': 'Ruinas Alfa / Cueva Acantilado', 'method': 'Fósil Hélix (Golpe Roca)'},
            {'area': 'Ciudad Plateada (Museo)', 'method': 'Revitalización de fósil'},
            DAYCARE_LOCATION
        ]
    },
    347: {
        'type': 'fossil',
        'badge_label': 'Fósil Garra',
        'badge_color': 'amber',
        'summary': 'Revivir el Fósil Garra (exclusivo de HeartGold rompiendo rocas con Golpe Roca en las Ruinas Alfa) en el Museo de Ciudad Plateada.',
        'locations': [
            {'area': 'Ruinas Alfa / Cueva Acantilado', 'method': 'Fósil Garra (Golpe Roca)'},
            {'area': 'Ciudad Plateada (Museo)', 'method': 'Revitalización de fósil'},
            DAYCARE_LOCATION
        ]
    },
    142: {
        'type': 'fossil',
        'badge_label': 'Ámbar Viejo',
        'badge_color': 'amber',
        'summary': 'Revivir el Ámbar Viejo (obtenible usando Golpe Roca en las Ruinas Alfa tras surf) en el Museo de Ciudad Plateada.',
        'locations': [
            {'area': 'Ruinas Alfa (Cámaras Posteriores)', 'method': 'Ámbar Viejo (Golpe Roca)'},
            {'area': 'Ciudad Plateada (Museo)', 'method': 'Revitalización de fósil'},
            DAYCARE_LOCATION
        ]
    },

    # Legendarios Principales
    250: {
        'type': 'legendary',
        'badge_label': 'Mascota Oficial',
        'badge_color': 'amber',
        'summary': 'Encuentro obligatorio de historia en la Azotea de la Torre Campana al Nivel 45 llevando la Campana Clara y el Ala Arcoíris.',
        'locations': [
            {'area': 'Torre Campana (Azotea)', 'method': 'Encuentro fijo a nivel 45 (Ala Arcoíris)'}
        ]
    },
    249: {
        'type': 'legendary',
        'badge_label': 'Legendario Post-Game',
        'badge_color': 'slate',
        'summary': 'Encuentro post-game en las profundidades de las Islas Remolino (Sótano B3) al Nivel 70 tras recibir el Ala Plateada en Ciudad Plateada.',
        'locations': [
            {'area': 'Islas Remolino (Sótano B3)', 'method': 'Encuentro fijo a nivel 70 con Ala Plateada'}
        ]
    },
    382: {
        'type': 'legendary',
        'badge_label': 'Legendario Exclusivo',
        'badge_color': 'blue',
        'summary': 'Encuentro exclusivo de HeartGold en la Torre Oculta de la Ruta 47 al Nivel 50 tras recibir la Esfera Azul de Mr. Pokémon.',
        'locations': [
            {'area': 'Ruta 47 (Torre Oculta)', 'method': 'Encuentro legendario a nivel 50 (Esfera Azul)'}
        ]
    },
    381: {
        'type': 'legendary',
        'badge_label': 'Errante Exclusivo',
        'badge_color': 'blue',
        'summary': 'Pokémon errante exclusivo de HeartGold por las rutas de Kanto al Nivel 35 tras hablar con Máximo Peñas en Ciudad Azafrán.',
        'locations': [
            {'area': 'Rutas de Kanto (Errante)', 'method': 'Pokémon errante tras evento de Máximo Peñas'}
        ]
    },
    243: {
        'type': 'legendary',
        'badge_label': 'Errante',
        'badge_color': 'amber',
        'summary': 'Deambula libremente por las rutas de hierba de Johto al Nivel 40 tras liberarlo en el sótano de la Torre Quemada.',
        'locations': [
            {'area': 'Rutas de Johto (Errante)', 'method': 'Pokémon errante tras liberar en Torre Quemada'}
        ]
    },
    244: {
        'type': 'legendary',
        'badge_label': 'Errante',
        'badge_color': 'red',
        'summary': 'Deambula libremente por las rutas de hierba de Johto al Nivel 40 tras liberarlo en el sótano de la Torre Quemada.',
        'locations': [
            {'area': 'Rutas de Johto (Errante)', 'method': 'Pokémon errante tras liberar en Torre Quemada'}
        ]
    },
    245: {
        'type': 'legendary',
        'badge_label': 'Legendario Estático',
        'badge_color': 'cyan',
        'summary': 'Encuentro estático al Nivel 40 en el Cabo Celeste (Ruta 25) tras seguirlo por diversas rutas de Johto y Kanto con Eusine.',
        'locations': [
            {'area': 'Ruta 25 (Cabo Celeste)', 'method': 'Encuentro fijo a nivel 40 tras evento de Eusine'}
        ]
    },
    144: {
        'type': 'legendary',
        'badge_label': 'Legendario',
        'badge_color': 'cyan',
        'summary': 'Encuentro estático en el nivel más profundo de las Islas Espuma al Nivel 50.',
        'locations': [{'area': 'Islas Espuma (Sótano B4)', 'method': 'Encuentro estático a nivel 50'}]
    },
    145: {
        'type': 'legendary',
        'badge_label': 'Legendario',
        'badge_color': 'amber',
        'summary': 'Encuentro estático en el exterior de la Central de Energía en Kanto al Nivel 50 tras restaurar el generador.',
        'locations': [{'area': 'Central de Energía (Exterior)', 'method': 'Encuentro estático a nivel 50'}]
    },
    146: {
        'type': 'legendary',
        'badge_label': 'Legendario',
        'badge_color': 'red',
        'summary': 'Encuentro estático en el interior del Monte Plateado al Nivel 50 tras usar Cascada y Treparrocas.',
        'locations': [{'area': 'Monte Plateado (Interior de la Cueva)', 'method': 'Encuentro estático a nivel 50'}]
    },
    150: {
        'type': 'legendary',
        'badge_label': 'Legendario',
        'badge_color': 'purple',
        'summary': 'Encuentro estático en lo más profundo de la Cueva Celeste en Kanto al Nivel 70 tras obtener las 16 medallas.',
        'locations': [{'area': 'Cueva Celeste (Sótano B1)', 'method': 'Encuentro estático a nivel 70'}]
    },

    # Pichu Picorejita
    172: {
        'type': 'baby',
        'badge_label': 'Bebé / Forma Especial',
        'badge_color': 'amber',
        'summary': 'Forma estándar mediante crianza en Ruta 34. Forma Pichu Picorejita obtenible en el Santuario del Encinar con el Pichu Color Pikachu.',
        'locations': [
            DAYCARE_LOCATION,
            {'area': 'Santuario del Encinar', 'method': 'Evento In-Game (Pichu Picorejita con Pichu Color Pikachu)'}
        ]
    },

    # Eevee, Sudowoodo, Togepi, Shuckle, Tyrogue, Lapras, Snorlax, Gyarados
    133: {
        'type': 'gift',
        'badge_label': 'Regalo',
        'badge_color': 'amber',
        'summary': 'Regalo de Bill en su casa de Ciudad Iris tras conocerlo en el Centro Pokémon de Ciudad Trigal (también por crianza).',
        'locations': [
            {'area': 'Ciudad Iris (Casa de Bill)', 'method': 'Regalo NPC'},
            DAYCARE_LOCATION
        ]
    },
    185: {
        'type': 'interactable',
        'badge_label': 'Interactivo',
        'badge_color': 'amber',
        'summary': 'Bloquea el camino entre Ciudad Malva y Ciudad Trigal en la Ruta 36; riégalo con la Regadera para combatir a nivel 20.',
        'locations': [
            {'area': 'Ruta 36', 'method': 'Interacción con Regadera al Nivel 20'},
            DAYCARE_LOCATION
        ]
    },
    175: {
        'type': 'baby',
        'badge_label': 'Huevo Regalo',
        'badge_color': 'indigo',
        'summary': 'El ayudante de Elm te entrega su huevo en la Tienda Pokémon de Ciudad Malva tras derrotar a Pegaso.',
        'locations': [
            {'area': 'Ciudad Malva (Tienda Pokémon)', 'method': 'Huevo misterioso entregado por el ayudante de Elm'},
            DAYCARE_LOCATION
        ]
    },
    213: {
        'type': 'gift',
        'badge_label': 'Regalo NPC',
        'badge_color': 'amber',
        'summary': 'Regalo de un entrenador en Ciudad Orquídea para protegerlo de un ladrón (también por crianza o Golpe Roca en Cianwood).',
        'locations': [
            {'area': 'Ciudad Orquídea', 'method': 'Regalo temporal de entrenador / Golpe Roca'},
            DAYCARE_LOCATION
        ]
    },
    236: {
        'type': 'baby',
        'badge_label': 'Regalo Kárate',
        'badge_color': 'red',
        'summary': 'Regalo del Rey Kárate Kiyo en las profundidades del Monte Mortero tras vencerlo en combate con un espacio libre en el equipo.',
        'locations': [
            {'area': 'Monte Mortero (Sótano Central)', 'method': 'Regalo del Rey Kárate Kiyo'},
            DAYCARE_LOCATION
        ]
    },
    131: {
        'type': 'interactable',
        'badge_label': 'Viernes',
        'badge_color': 'cyan',
        'summary': 'Aparece nadando en el agua del sótano B2 de la Cueva Unión exclusivamente los viernes al Nivel 20.',
        'locations': [
            {'area': 'Cueva Unión (Sótano B2)', 'method': 'Encuentro fijo de Surf los viernes'},
            DAYCARE_LOCATION
        ]
    },
    143: {
        'type': 'interactable',
        'badge_label': 'Interactivo',
        'badge_color': 'slate',
        'summary': 'Bloquea el acceso este de Ciudad Carmín; sintoniza la Flauta Pokémon en la Radio del Pokégear para despertarlo al Nivel 50.',
        'locations': [
            {'area': 'Ciudad Carmín (Acceso Este)', 'method': 'Despertar con Flauta Pokémon en el Pokégear'},
            DAYCARE_LOCATION
        ]
    },
    130: {
        'type': 'interactable',
        'badge_label': 'Gyarados Rojo',
        'badge_color': 'red',
        'summary': 'Gyarados variocolor (rojo) estático al Nivel 30 nadando en el centro del Lago de la Furia.',
        'locations': [
            {'area': 'Lago de la Furia', 'method': 'Encuentro fijo de historia al Nivel 30 (Shiny garantizado)'}
        ]
    },

    # Zona Safari de Baoba (Bloques y Días)
    304: {
        'type': 'safari',
        'badge_label': 'Safari Baoba',
        'badge_color': 'slate',
        'summary': 'Zona Safari (Área Montaña con 24 Bloques de Roca, sin espera de días).',
        'locations': [
            {'area': 'Zona Safari (Montaña)', 'method': '24 Bloques Roca (Inmediato)'},
            DAYCARE_LOCATION
        ]
    },
    328: {
        'type': 'safari',
        'badge_label': 'Safari Baoba',
        'badge_color': 'amber',
        'summary': 'Zona Safari (Área Desierto con 25 Bloques de Roca y 30 días de espera de Baoba).',
        'locations': [
            {'area': 'Zona Safari (Desierto)', 'method': '25 Bloques Roca + 30 días de espera'},
            DAYCARE_LOCATION
        ]
    },
    371: {
        'type': 'safari',
        'badge_label': 'Safari Baoba',
        'badge_color': 'indigo',
        'summary': 'Zona Safari (Área Humedal con 9 Bloques Llanura y 19 Bloques Roca tras 110 días de espera de Baoba).',
        'locations': [
            {'area': 'Zona Safari (Humedal)', 'method': '9 Bloques Llanura + 19 Roca (110 días de espera)'},
            DAYCARE_LOCATION
        ]
    },
    374: {
        'type': 'safari',
        'badge_label': 'Safari Baoba',
        'badge_color': 'blue',
        'summary': 'Zona Safari (Área Terreno Baldío con 21 Bloques de Roca y 70 días de espera de Baoba). También regalo de Steven Stone en su casa de Hoenn.',
        'locations': [
            {'area': 'Zona Safari (Terreno Baldío)', 'method': '21 Bloques Roca + 70 días de espera'},
            DAYCARE_LOCATION
        ]
    },
    443: {
        'type': 'safari',
        'badge_label': 'Safari Baoba',
        'badge_color': 'blue',
        'summary': 'Zona Safari (Área Humedal con 13 Bloques Llanura y 17 Bloques Roca tras 100 días de espera de Baoba).',
        'locations': [
            {'area': 'Zona Safari (Humedal)', 'method': '13 Bloques Llanura + 17 Roca (100 días de espera)'},
            DAYCARE_LOCATION
        ]
    },
    447: {
        'type': 'safari',
        'badge_label': 'Safari Baoba',
        'badge_color': 'blue',
        'summary': 'Zona Safari (Área Jardín con 10 Bloques Llanura y 14 Bloques Roca tras 70 días de espera de Baoba).',
        'locations': [
            {'area': 'Zona Safari (Jardín)', 'method': '10 Bloques Llanura + 14 Roca (70 días de espera)'},
            DAYCARE_LOCATION
        ]
    },
    436: {
        'type': 'safari',
        'badge_label': 'Safari Baoba',
        'badge_color': 'indigo',
        'summary': 'Zona Safari (Área Montaña con 18 Bloques Roca y 30 días de espera) o mediante sintonía de Sinnoh en la Radio.',
        'locations': [
            {'area': 'Zona Safari (Montaña)', 'method': '18 Bloques Roca (30 días de espera)'},
            {'area': 'Ruta 33 / Ruta 45', 'method': 'Radio Pokégear (Sintonía de Sinnoh)'},
            DAYCARE_LOCATION
        ]
    },
    449: {
        'type': 'safari',
        'badge_label': 'Safari Baoba',
        'badge_color': 'amber',
        'summary': 'Zona Safari (Área Desierto con 28 Bloques Roca, aparición inmediata).',
        'locations': [
            {'area': 'Zona Safari (Desierto)', 'method': '28 Bloques Roca (Inmediato)'},
            DAYCARE_LOCATION
        ]
    },
    451: {
        'type': 'safari',
        'badge_label': 'Safari Baoba',
        'badge_color': 'purple',
        'summary': 'Zona Safari (Área Pantano con 28 Bloques Roca, aparición inmediata).',
        'locations': [
            {'area': 'Zona Safari (Pantano)', 'method': '28 Bloques Roca (Inmediato)'},
            DAYCARE_LOCATION
        ]
    },
    455: {
        'type': 'safari',
        'badge_label': 'Safari Baoba',
        'badge_color': 'emerald',
        'summary': 'Zona Safari (Área Pantano con 25 Bloques Llanura y 10 días de espera de Baoba).',
        'locations': [
            {'area': 'Zona Safari (Pantano)', 'method': '25 Bloques Llanura (10 días de espera)'},
            DAYCARE_LOCATION
        ]
    },
}


def format_wild_method(method_raw: str, conditions: list) -> str:
    cond_names = set(conditions or [])
    if 'radio-hoenn' in cond_names:
        return 'Radio Pokégear (Sintonía de Hoenn)'
    if 'radio-sinnoh' in cond_names:
        return 'Radio Pokégear (Sintonía de Sinnoh)'
    if 'swarm' in cond_names:
        return 'Manada Pokémon (Aviso del Pokégear)'

    if method_raw == 'walk':
        if 'time-morning' in cond_names:
            return 'Hierba alta (Mañana)'
        if 'time-day' in cond_names:
            return 'Hierba alta (Día)'
        if 'time-night' in cond_names:
            return 'Hierba alta (Noche)'
        return 'Hierba alta'
    if method_raw == 'surf':
        return 'Surf'
    if method_raw == 'old-rod':
        return 'Pesca (Caña Vieja)'
    if method_raw == 'good-rod':
        return 'Pesca (Caña Buena)'
    if method_raw == 'super-rod':
        return 'Pesca (Supercaña)'
    if method_raw == 'headbutt':
        return 'Golpe Cabeza en árboles'
    if method_raw == 'rock-smash':
        return 'Golpe Roca'
    if method_raw == 'bug-catching-contest':
        return 'Concurso de Captura de Bichos'

    return method_raw.replace('-', ' ').capitalize()


def main():
    print("Iniciando compilación oficial de catálogos para Pokémon Oro HeartGold a 0 ms SQL...")

    with open(CACHE_DIR / "pokemon_493_species.json", "r", encoding="utf-8") as f:
        species_493 = json.load(f)

    with open(CACHE_DIR / "johto_updated_pokedex_256.json", "r", encoding="utf-8") as f:
        johto_256 = json.load(f)

    with open(CACHE_DIR / "encounters_heartgold.json", "r", encoding="utf-8") as f:
        encounters_hg = json.load(f)

    with open(CACHE_DIR / "wikidex_heartgold_descriptions.json", "r", encoding="utf-8") as f:
        descriptions_hg = json.load(f)

    with open(CACHE_DIR / "gen4_evolutions.json", "r", encoding="utf-8") as f:
        gen4_evos = json.load(f)

    with open(BASE_DIR / "tracker" / "data" / "evolution_stones.json", "r", encoding="utf-8") as f:
        evolution_stones = json.load(f)

    # Cargar transferencias desde exclusives.py
    from tracker.exclusives import VERSION_TRANSFERS_CATALOG, VERSION_TRANSFERS_META
    hg_transfers = set(VERSION_TRANSFERS_CATALOG.get("heartgold", []))
    hg_origins = VERSION_TRANSFERS_META.get("heartgold", {}).get("origins", {})

    def build_entry(nat_id: int, entry_num: int, is_regional: bool, unique_id: int):
        sp = species_493[str(nat_id)]
        flavor = descriptions_hg.get(str(nat_id), "")
        sp_name = sp['name'].lower()
        egg_groups = sp.get('egg_groups', [])
        evo_info = gen4_evos.get(str(nat_id))

        p_type = sp.get('primary_type', 'normal')
        s_type = sp.get('secondary_type', '') or ''

        is_baby = sp_name in BABY_NAMES
        is_incense_parent = sp_name in INCENSE_PARENTS_THAT_HATCH
        is_evolution = (evo_info is not None) and not is_incense_parent

        # Regla Universal de Crianza (Invariante 4)
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

        raw_encs = encounters_hg.get(str(nat_id), [])
        evo_stone_obj = None

        if nat_id in SPECIAL_OBTAINING:
            obt_info = json.loads(json.dumps(SPECIAL_OBTAINING[nat_id]))
        elif raw_encs:
            # Procesar encuentros salvajes agrupados
            area_methods = {}
            for e in raw_encs:
                area_key = e.get('area_raw', '')
                clean_area = JOHTO_KANTO_AREA_NAMES.get(area_key, area_key.replace('-', ' ').title())
                meth_desc = format_wild_method(e.get('method_raw', 'walk'), e.get('conditions', []))
                if clean_area not in area_methods:
                    area_methods[clean_area] = set()
                area_methods[clean_area].add(meth_desc)

            loc_list = []
            for a_name, m_set in area_methods.items():
                loc_list.append({
                    'area': a_name,
                    'method': ", ".join(sorted(list(m_set)))
                })

            if is_hatchable:
                loc_list.append(DAYCARE_LOCATION)

            num_zones = len(area_methods)
            zone_names = list(area_methods.keys())

            if num_zones == 1:
                summary = f"Salvaje en {zone_names[0]}."
            elif num_zones in (2, 3):
                summary = f"Salvaje en: {', '.join(zone_names)}."
            else:
                examples = ", ".join(zone_names[:3])
                summary = f"Salvaje en {num_zones} zonas (ej: {examples})."

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

        elif nat_id in hg_transfers:
            origin = hg_origins.get(nat_id, 'Intercambio con D/P/Pt o Parque Compi (GBA)')
            summary = f"Inaccesible en estado salvaje en Pokémon Oro HeartGold. Requiere {origin}."
            if is_hatchable:
                summary += " (también obtenible mediante crianza)."

            locs = [{'area': 'Parque Compi / Intercambio', 'method': f'Transferencia desde {origin}'}]
            if is_hatchable:
                locs.append(DAYCARE_LOCATION)

            obt_info = {
                'type': 'transfer',
                'badge_label': 'Transferir',
                'badge_color': 'purple',
                'summary': summary,
                'locations': locs
            }
        else:
            obt_info = {
                'type': 'event',
                'badge_label': 'Especial',
                'badge_color': 'slate',
                'summary': 'Obtención mediante evento especial, intercambio o distribución oficial.',
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
                        'area': 'Ruta 34 (Guardería Pokémon)',
                        'method': f"Crianza con {incense_name}"
                    })
                else:
                    new_locations.append(DAYCARE_LOCATION)
            else:
                new_locations.append(loc)

        if is_hatchable and not has_daycare:
            if baby_incense_slug:
                incense_name = evolution_stones.get(baby_incense_slug, {}).get('name_es', 'Incienso')
                new_locations.append({
                    'area': 'Ruta 34 (Guardería Pokémon)',
                    'method': f"Crianza con {incense_name}"
                })
            else:
                new_locations.append(DAYCARE_LOCATION)

        obt_info['locations'] = new_locations

        # 3. Resolver objeto evolutivo para el modal de piedras
        item_slug = obt_info.get('evolution_info', {}).get('item_slug')
        if item_slug and item_slug in evolution_stones:
            evo_stone_obj = {
                'slug': item_slug,
                'name_es': evolution_stones[item_slug].get('name_es', item_slug),
                'sprite_url': f"/media/items/{item_slug}.png",
                'locations': evolution_stones[item_slug].get('games', {}).get('heartgold', [])
            }

        # Construir entrada canónica de catálogo para PokedexGlobal
        entry = {
            "id": unique_id,
            "entry_number": entry_num,
            "game_slug": "heartgold",
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
            "game_sprite_url": f"/media/pokemon/sprites/heartgold/{nat_id}.png",
            "game_sprite_shiny_url": f"/media/pokemon/sprites/heartgold_shiny/{nat_id}.png",
            "game_sprite_back_url": f"/media/pokemon/sprites/heartgold/back/{nat_id}.png",
            "game_sprite_shiny_back_url": f"/media/pokemon/sprites/heartgold_shiny/back/{nat_id}.png",
            "modern_sprite_shiny_url": f"/media/pokemon/artwork/shiny/{nat_id}.png",
            "modal_retro_sprite_url": f"/media/pokemon/sprites/heartgold_animated/{nat_id}.png",
            "modal_retro_sprite_shiny_url": f"/media/pokemon/sprites/heartgold_animated_shiny/{nat_id}.png",
            "modal_retro_sprite_back_url": f"/media/pokemon/sprites/heartgold/back/{nat_id}.png",
            "modal_retro_sprite_shiny_back_url": f"/media/pokemon/sprites/heartgold_shiny/back/{nat_id}.png",
            "pc_icon_url": f"/media/pokemon/icons/gen4/{nat_id}.png",
            "cry_url": f"/media/pokemon/cries/legacy/{nat_id}.ogg",
            "flavor_text": flavor,
            "obtaining_info": obt_info,
            "evolution_stone": evo_stone_obj,
            "game_data": {
                "generation": 4,
                "game_slug": "heartgold",
                "game_name": "Pokémon Oro HeartGold",
                "is_regional": is_regional
            }
        }
        return entry

    # 1. Compilación de Pokédex Regional de Johto Actualizada (256 entradas)
    print("Compilando Pokédex Regional de Johto Actualizada en HeartGold (256 entradas)...")
    hg_regional_catalog = []
    for reg_num in range(1, 257):
        nat_id = int(johto_256[str(reg_num)])
        unique_id = 6000 + reg_num
        hg_regional_catalog.append(build_entry(nat_id, reg_num, is_regional=True, unique_id=unique_id))

    regional_file = CATALOGS_DIR / "heartgold.json"
    with open(regional_file, "w", encoding="utf-8") as f:
        json.dump(hg_regional_catalog, f, ensure_ascii=False, indent=2)
    print(f"[OK] Guardado {regional_file} con {len(hg_regional_catalog)} entradas.")

    # 2. Compilación de Pokédex Nacional de HeartGold (493 entradas)
    print("Compilando Pokédex Nacional de HeartGold (493 entradas)...")
    hg_national_catalog = []
    for nat_num in range(1, 494):
        unique_id = 6300 + nat_num
        hg_national_catalog.append(build_entry(nat_num, nat_num, is_regional=False, unique_id=unique_id))

    national_file = CATALOGS_DIR / "heartgold_national.json"
    with open(national_file, "w", encoding="utf-8") as f:
        json.dump(hg_national_catalog, f, ensure_ascii=False, indent=2)
    print(f"[OK] Guardado {national_file} con {len(hg_national_catalog)} entradas.")


if __name__ == "__main__":
    main()
