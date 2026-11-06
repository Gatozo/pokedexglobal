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
    'safari-zone-gate-area': 'Acceso al Safari',
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
        'cianwood-city-kirks-house': 'Ciudad Orquídea (Casa de Kirk)',
    'cianwood-city-pokemon-center': 'Ciudad Orquídea (Centro Pokémon)',
    'dark-cave-violet-city-entrance': 'Cueva Oscura (Entrada de Ciudad Malva)',
    'embedded-tower-kyogre-room': 'Torre Oculta (Sala de Kyogre)',
    'embedded-tower-rayquaza-room': 'Torre Oculta (Sala de Rayquaza)',
    'goldenrod-city-bills-house': 'Ciudad Trigal (Casa de Bill)',
    'goldenrod-city-department-store-5f': 'Centro Comercial de Ciudad Trigal (P5)',
    'goldenrod-city-game-corner': 'Casino de Ciudad Trigal',
    'goldenrod-city-north-gate': 'Ciudad Trigal (Paso Norte)',
    'ice-path-b2f': 'Ruta Helada (Sótano B2)',
    'johto-pokemart-area': 'Tienda Pokémon de Johto',
    'johto-route-47-cave-gate': 'Ruta 47 (Entrada de la Cueva)',
    'johto-route-47-inside-cave': 'Ruta 47 (Interior de la Cueva)',
    'johto-safari-zone-desert': 'Zona Safari (Desierto)',
    'johto-safari-zone-forest': 'Zona Safari (Arboleda)',
    'johto-safari-zone-marshland': 'Zona Safari (Albufera)',
    'johto-safari-zone-meadow': 'Zona Safari (Parterre)',
    'johto-safari-zone-mountain': 'Zona Safari (Montaña)',
    'johto-safari-zone-peak': 'Zona Safari (Peña)',
    'johto-safari-zone-plains': 'Zona Safari (Prado)',
    'johto-safari-zone-rocky-beach': 'Zona Safari (Laguna)',
    'johto-safari-zone-savannah': 'Zona Safari (Sabana)',
    'johto-safari-zone-swamp': 'Zona Safari (Lagos)',
    'johto-safari-zone-wasteland': 'Zona Safari (Páramo)',
    'johto-safari-zone-wetland': 'Zona Safari (Pantano)',
    'kanto-power-plant-area': 'Central de Energía',
    'kanto-route-2-north-towards-pewter-city': 'Ruta 2 (Norte hacia Ciudad Plateada)',
    'kanto-route-2-south-towards-viridian-city': 'Ruta 2 (Sur hacia Ciudad Verde)',
    'kanto-sea-route-21-area': 'Ruta 21 (Ruta Marítima)',
    'kanto-victory-road-1-1f': 'Calle Victoria (P1)',
    'kanto-victory-road-1-2f': 'Calle Victoria (P2)',
    'kanto-victory-road-1-3f': 'Calle Victoria (P3)',
    'mt-moon-mt-moon-square': 'Plaza del Monte Moon',
    'mt-mortar-1f': 'Monte Mortero (P1)',
    'mt-mortar-lower-cave': 'Monte Mortero (Cueva Inferior)',
    'mt-mortar-upper-cave': 'Monte Mortero (Cueva Superior)',
    'mt-silver-1f-top': 'Monte Plateado (P1 Superior)',
    'mt-silver-4f': 'Monte Plateado (P4)',
    'mt-silver-outside': 'Monte Plateado (Exterior)',
    'mt-silver-top': 'Cima del Monte Plateado',
    'olivine-city-gym': 'Gimnasio de Ciudad Olivo',
    'pewter-city-pewter-museum-of-science': 'Museo de la Ciencia de Ciudad Plateada',
    'ruins-of-alph-interior-a': 'Ruinas Alfa (Cámara A)',
    'ruins-of-alph-interior-b': 'Ruinas Alfa (Cámara B)',
    'ruins-of-alph-interior-c': 'Ruinas Alfa (Cámara C)',
    'ruins-of-alph-interior-d': 'Ruinas Alfa (Cámara D)',
    'ruins-of-alph-outside': 'Ruinas Alfa (Exterior)',
    'saffron-city-magnet-train-station': 'Estación del Magnetotrén de Ciudad Azafrán',
    'saffron-city-silph-co': 'Ciudad Azafrán (Silph S.A.)',
    'team-rocket-hq-area': 'Guarida del Team Rocket (Ciudad Caoba)',
    'unknown-all-bugs-area': 'Parque Nacional (Concurso de Captura de Bichos)',
    'unknown-all-poliwag-area': 'Ruta 30 / Ruta 31 (Encuentro especial)',
    'unknown-all-rattata-area': 'Ruta 29 / Ruta 30 (Llamada del Pokégear)',
    'vermilion-city-ss-anne-dock': 'Muelle del S.S. Aqua (Ciudad Carmín)',
    'violet-city-poke-mart': 'Ciudad Malva (Tienda Pokémon)',
    'violet-city-pokemon-center': 'Ciudad Malva (Centro Pokémon)',
    'whirl-islands-b3f': 'Islas Remolino (Sótano B3)',
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
    'unown', 'manaphy'
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
    380: {
        'type': 'legendary',
        'badge_label': 'Errante Exclusivo',
        'badge_color': 'blue',
        'summary': 'Pokémon errante exclusivo de HeartGold por las rutas de Kanto al Nivel 35 tras hablar con Máximo Peñas en Ciudad Carmín (al salir del Club de Fans Pokémon).',
        'locations': [
            {'area': 'Rutas de Kanto (Errante)', 'method': 'Pokémon errante tras evento de Máximo Peñas en Ciudad Carmín'}
        ]
    },
    381: {
        'type': 'event',
        'badge_label': 'Evento Especial',
        'badge_color': 'indigo',
        'summary': 'Encuentro estático al Nivel 40 en Ciudad Plateada mediante el evento del Misticristal, o por transferencia/intercambio desde SoulSilver.',
        'locations': [
            {'area': 'Ciudad Plateada (Museo)', 'method': 'Evento del Misticristal / Intercambio con SoulSilver'}
        ]
    },
    384: {
        'type': 'legendary',
        'badge_label': 'Legendario Especial',
        'badge_color': 'emerald',
        'summary': 'Encuentro en la Torre Oculta al Nivel 50 llevando la Esfera Verde (obtenida del Prof. Oak tras mostrarle a Kyogre de HeartGold y a Groudon de SoulSilver).',
        'locations': [
            {'area': 'Torre Oculta (Ruta 47)', 'method': 'Encuentro fijo a nivel 50 con Esfera Verde'}
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
        'badge_label': 'Regalo / Casino',
        'badge_color': 'amber',
        'summary': 'Regalo de Bill en Ciudad Trigal o canjeable por 6.666 fichas en el Casino de Azulona.',
        'locations': [
            {'area': 'Ciudad Trigal (Casa de Bill)', 'method': 'Regalo de Bill al Nivel 5 (tras conocerlo en el Centro Pokémon de Ciudad Iris)'},
            {'area': 'Ciudad Azulona (Rincón de Premios)', 'method': 'Premio del Casino (6.666 fichas)'},
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

    # Pidgeotto (#17) NO aparece en la Zona Safari (solo Pidgey)
    17: {
        'type': 'wild',
        'badge_label': 'Salvaje / Evolución',
        'badge_color': 'emerald',
        'summary': 'Salvaje en múltiples rutas de Johto y Kanto. También evolucionando de Pidgey al Nivel 18.',
        'locations': [
            {'area': 'Ruta 37', 'method': 'Hierba alta (Día)'},
            {'area': 'Ruta 43', 'method': 'Hierba alta (Mañana y Día)'},
            {'area': 'Ruta 2 (Norte hacia Ciudad Plateada)', 'method': 'Hierba alta (Mañana y Día)'},
            {'area': 'Ruta 2 (Sur hacia Ciudad Verde)', 'method': 'Hierba alta (Mañana y Día)'},
            {'area': 'Ruta 8', 'method': 'Hierba alta (Mañana y Día)'},
            {'area': 'Ruta 13', 'method': 'Hierba alta (Mañana y Día)'},
            {'area': 'Ruta 14', 'method': 'Hierba alta (Mañana y Día)'},
            {'area': 'Ruta 15', 'method': 'Hierba alta (Mañana y Día)'},
            {'area': 'Ruta 25', 'method': 'Hierba alta (Mañana y Día)'},
            {'area': 'Bosque Verde', 'method': 'Hierba alta (Mañana y Día)'},
            DAYCARE_LOCATION
        ]
    },

    # Zona Safari de Baoba (Bloques y Días)
    304: {
        'type': 'safari',
        'badge_label': 'Safari Baoba',
        'badge_color': 'slate',
        'summary': 'Zona Safari (Área Lagos con 24 Bloques de Peña, sin espera de días).',
        'locations': [
            {'area': 'Zona Safari (Lagos)', 'method': '24 Bloques Peña (Inmediato)'},
            DAYCARE_LOCATION
        ]
    },
    328: {
        'type': 'safari',
        'badge_label': 'Safari Baoba',
        'badge_color': 'amber',
        'summary': 'Zona Safari (Área Desierto con 25 Bloques de Peña y 30 días de espera de Baoba).',
        'locations': [
            {'area': 'Zona Safari (Desierto)', 'method': '25 Bloques Peña + 30 días de espera'},
            DAYCARE_LOCATION
        ]
    },
    371: {
        'type': 'safari',
        'badge_label': 'Safari Baoba',
        'badge_color': 'indigo',
        'summary': 'Zona Safari (Área Laguna con 9 Bloques Bosque y 19 Bloques Peña tras 110 días de espera de Baoba).',
        'locations': [
            {'area': 'Zona Safari (Laguna)', 'method': '9 Bloques Bosque + 19 Peña (110 días de espera)'},
            DAYCARE_LOCATION
        ]
    },
    374: {
        'type': 'safari',
        'badge_label': 'Safari Baoba',
        'badge_color': 'blue',
        'summary': 'Zona Safari (Área Arboleda con 21 Bloques de Peña y 70 días de espera de Baoba). También regalo de Steven Stone en su casa de Hoenn.',
        'locations': [
            {'area': 'Zona Safari (Arboleda)', 'method': '21 Bloques Peña + 70 días de espera'},
            DAYCARE_LOCATION
        ]
    },
    443: {
        'type': 'safari',
        'badge_label': 'Safari Baoba',
        'badge_color': 'blue',
        'summary': 'Zona Safari (Área Lagos con 13 Bloques Planicie y 17 Bloques Peña tras 100 días de espera de Baoba).',
        'locations': [
            {'area': 'Zona Safari (Lagos)', 'method': '13 Bloques Planicie + 17 Peña (100 días de espera)'},
            DAYCARE_LOCATION
        ]
    },
    447: {
        'type': 'safari',
        'badge_label': 'Safari Baoba',
        'badge_color': 'blue',
        'summary': 'Zona Safari (Área Parterre con 10 Bloques Bosque y 14 Bloques Peña tras 70 días de espera de Baoba).',
        'locations': [
            {'area': 'Zona Safari (Parterre)', 'method': '10 Bloques Bosque + 14 Peña (70 días de espera)'},
            DAYCARE_LOCATION
        ]
    },
    436: {
        'type': 'safari',
        'badge_label': 'Safari Baoba',
        'badge_color': 'indigo',
        'summary': 'Zona Safari (Área Peña con 18 Bloques Peña y 30 días de espera) o mediante sintonía de Sinnoh en la Radio.',
        'locations': [
            {'area': 'Zona Safari (Peña)', 'method': '18 Bloques Peña (30 días de espera)'},
            {'area': 'Ruta 33', 'method': 'Radio Pokégear (Sintonía de Sinnoh)'},
            {'area': 'Ruta 45', 'method': 'Radio Pokégear (Sintonía de Sinnoh)'},
            {'area': 'Pokéwalker (Senda Glacial)', 'method': 'Paseo en el Pokéwalker'},
            {'area': 'Pokéwalker (Vía Campeón)', 'method': 'Paseo en el Pokéwalker'},
            DAYCARE_LOCATION
        ]
    },
    449: {
        'type': 'safari',
        'badge_label': 'Safari Baoba',
        'badge_color': 'amber',
        'summary': 'Zona Safari (Área Desierto con 28 Bloques Peña, aparición inmediata).',
        'locations': [
            {'area': 'Zona Safari (Desierto)', 'method': '28 Bloques Peña (Inmediato)'},
            DAYCARE_LOCATION
        ]
    },
    451: {
        'type': 'safari',
        'badge_label': 'Safari Baoba',
        'badge_color': 'purple',
        'summary': 'Zona Safari (Área Páramo con 28 Bloques Peña, aparición inmediata).',
        'locations': [
            {'area': 'Zona Safari (Páramo)', 'method': '28 Bloques Peña (Inmediato)'},
            DAYCARE_LOCATION
        ]
    },
    455: {
        'type': 'wild',
        'badge_label': 'Salvaje / Safari',
        'badge_color': 'emerald',
        'summary': 'Salvaje en Encinar y Bosque Verde mediante sintonía de Sinnoh en la Radio. En la Zona Safari aparece en el Pantano con 25 Bloques Planicie (10 días de espera).',
        'locations': [
            {'area': 'Encinar', 'method': 'Radio Pokégear (Sintonía de Sinnoh)'},
            {'area': 'Bosque Verde', 'method': 'Radio Pokégear (Sintonía de Sinnoh)'},
            {'area': 'Zona Safari (Pantano)', 'method': '25 Bloques Planicie (10 días de espera)'},
            DAYCARE_LOCATION
        ]
    },

    # Especies de Johto/Kanto con encuentros mediante bloques de Baoba
    82: {
        'type': 'wild',
        'badge_label': 'Salvaje / Safari',
        'badge_color': 'slate',
        'summary': 'Salvaje en Cueva Celeste. En la Zona Safari aparece en el área Peña con 3 Bloques de Peña. También por intercambio en la Central de Energía.',
        'locations': [
            {'area': 'Cueva Celeste (P1, P2 y Sótano B1)', 'method': 'Encuentro en cueva'},
            {'area': 'Zona Safari (Peña)', 'method': '3 Bloques Peña (Inmediato)'},
            {'area': 'Central de Energía', 'method': 'Intercambio por un Dugtrio'},
            DAYCARE_LOCATION
        ]
    },
    110: {
        'type': 'safari',
        'badge_label': 'Safari Baoba / Evolución',
        'badge_color': 'purple',
        'summary': 'Zona Safari (Área Pantano con 8 Bloques de Planicie, aparición inmediata). También mediante evolución de Koffing (Nv. 35).',
        'locations': [
            {'area': 'Zona Safari (Pantano)', 'method': '8 Bloques Planicie (Inmediato)'},
            DAYCARE_LOCATION
        ]
    },
    112: {
        'type': 'safari',
        'badge_label': 'Safari Baoba / Evolución',
        'badge_color': 'amber',
        'summary': 'Zona Safari (Área Sabana con 10 Bloques de Planicie, aparición inmediata). También mediante evolución de Rhyhorn (Nv. 42).',
        'locations': [
            {'area': 'Zona Safari (Sabana)', 'method': '10 Bloques Planicie (Inmediato)'},
            DAYCARE_LOCATION
        ]
    },
    115: {
        'type': 'wild',
        'badge_label': 'Salvaje / Safari',
        'badge_color': 'amber',
        'summary': 'Salvaje en Túnel Roca. En la Zona Safari aparece de forma natural en el Páramo (Mañana y Día).',
        'locations': [
            {'area': 'Túnel Roca (Sótano B1)', 'method': 'Hierba alta'},
            {'area': 'Zona Safari (Páramo)', 'method': 'Hierba alta (Mañana y Día)'},
            DAYCARE_LOCATION
        ]
    },
    198: {
        'type': 'wild',
        'badge_label': 'Salvaje / Safari',
        'badge_color': 'indigo',
        'summary': 'Salvaje en Ruta 7 y 16 (Noche). En la Zona Safari aparece de forma natural en la Laguna (Noche, Surf) o mediante 10 Bloques de Agua.',
        'locations': [
            {'area': 'Ruta 7', 'method': 'Hierba alta (Noche)'},
            {'area': 'Ruta 16', 'method': 'Hierba alta (Noche)'},
            {'area': 'Zona Safari (Laguna)', 'method': 'Hierba alta (Noche), Surf'},
            {'area': 'Zona Safari (Laguna)', 'method': '10 Bloques Agua (Inmediato)'},
            DAYCARE_LOCATION
        ]
    },
    200: {
        'type': 'wild',
        'badge_label': 'Salvaje / Safari',
        'badge_color': 'indigo',
        'summary': 'Salvaje en Monte Plateado y Ruta 47 (Noche). En la Zona Safari aparece de forma natural en la Arboleda (Noche) o mediante 4 Bloques de Bosque.',
        'locations': [
            {'area': 'Ruta 47 (Interior de la Cueva)', 'method': 'Hierba alta (Noche)'},
            {'area': 'Monte Plateado', 'method': 'Hierba alta (Noche)'},
            {'area': 'Zona Safari (Arboleda)', 'method': 'Hierba alta (Noche)'},
            {'area': 'Zona Safari (Arboleda)', 'method': '4 Bloques Bosque (Inmediato)'},
            DAYCARE_LOCATION
        ]
    },
    202: {
        'type': 'wild',
        'badge_label': 'Salvaje / Safari',
        'badge_color': 'blue',
        'summary': 'Salvaje en Cueva Oscura y Cueva Celeste. En la Zona Safari aparece de forma natural en la Peña o mediante 5 Bloques de Peña.',
        'locations': [
            {'area': 'Cueva Oscura (Entrada Ciudad Endrino)', 'method': 'Hierba alta'},
            {'area': 'Cueva Celeste', 'method': 'Hierba alta'},
            {'area': 'Zona Safari (Peña)', 'method': 'Hierba alta'},
            {'area': 'Zona Safari (Peña)', 'method': '5 Bloques Peña (Inmediato)'},
            DAYCARE_LOCATION
        ]
    },
    228: {
        'type': 'wild',
        'badge_label': 'Salvaje / Safari',
        'badge_color': 'amber',
        'summary': 'Salvaje en Ruta 7 (Noche). En la Zona Safari aparece colocando 4 Bloques de Bosque en la Sabana.',
        'locations': [
            {'area': 'Ruta 7', 'method': 'Hierba alta (Noche)'},
            {'area': 'Zona Safari (Sabana)', 'method': '4 Bloques Bosque (Inmediato)'},
            DAYCARE_LOCATION
        ]
    },
    229: {
        'type': 'safari',
        'badge_label': 'Safari Baoba / Evolución',
        'badge_color': 'amber',
        'summary': 'Zona Safari (Área Prado con 10 Bloques de Peña, aparición inmediata). También mediante evolución de Houndour (Nv. 24).',
        'locations': [
            {'area': 'Zona Safari (Prado)', 'method': '10 Bloques Peña (Inmediato)'},
            DAYCARE_LOCATION
        ]
    },
    234: {
        'type': 'wild',
        'badge_label': 'Salvaje / Safari',
        'badge_color': 'emerald',
        'summary': 'Salvaje en Ruta 36 y Ruta 37. En la Zona Safari (Prado) aparece de forma natural (Noche, Nv. 17) o colocando 3 Bloques de Planicie (Noche, Nv. 40).',
        'locations': [
            {'area': 'Ruta 36', 'method': 'Hierba alta'},
            {'area': 'Ruta 37', 'method': 'Hierba alta'},
            {'area': 'Zona Safari (Prado)', 'method': 'Hierba alta (Noche)'},
            {'area': 'Zona Safari (Prado)', 'method': '3 Bloques Planicie (Noche)'},
            DAYCARE_LOCATION
        ]
    },
    246: {
        'type': 'wild',
        'badge_label': 'Salvaje / Safari',
        'badge_color': 'emerald',
        'summary': 'Salvaje en Monte Plateado. En la Zona Safari aparece de forma natural en la Montaña (Mañana y Día) o mediante 5 Bloques de Peña.',
        'locations': [
            {'area': 'Monte Plateado', 'method': 'Hierba alta'},
            {'area': 'Zona Safari (Montaña)', 'method': 'Hierba alta (Mañana y Día)'},
            {'area': 'Zona Safari (Montaña)', 'method': '5 Bloques Peña (Inmediato)'},
            DAYCARE_LOCATION
        ]
    },

    # --- ENCUENTROS ESPECIALES / INTERCAMBIOS IN-GAME / CASINOS ---
    25: {
        'type': 'wild',
        'badge_label': 'Salvaje / Intercambio',
        'badge_color': 'amber',
        'summary': 'Salvaje en Bosque Verde (hierba alta). También obtenible mediante intercambio con el Teniente Surge en la Estación del Magnetotrén de Ciudad Azafrán (intercambia su Pikachu por uno tuyo).',
        'locations': [
            {'area': 'Bosque Verde', 'method': 'Hierba alta (Mañana y Día)'},
            {'area': 'Estación del Magnetotrén de Ciudad Azafrán', 'method': 'Intercambio con Teniente Surge (por Pikachu)'},
            DAYCARE_LOCATION
        ]
    },
    21: {
        'type': 'wild',
        'badge_label': 'Salvaje / Regalo',
        'badge_color': 'emerald',
        'summary': 'Salvaje en múltiples rutas de Johto y Kanto. También regalo del guardia en el Paso Norte de Ciudad Trigal.',
        'locations': [
            {'area': 'Ruta 33', 'method': 'Hierba alta (Mañana y Día), Golpe Cabeza en árboles'},
            {'area': 'Ruta 42', 'method': 'Hierba alta (Mañana y Día), Golpe Cabeza en árboles'},
            {'area': 'Ruta 44', 'method': 'Golpe Cabeza en árboles'},
            {'area': 'Ruta 45', 'method': 'Golpe Cabeza en árboles'},
            {'area': 'Ruta 46', 'method': 'Hierba alta (Mañana y Día), Golpe Cabeza en árboles'},
            {'area': 'Ruta 47', 'method': 'Hierba alta'},
            {'area': 'Pueblo Azalea', 'method': 'Golpe Cabeza en árboles'},
            {'area': 'Ruta 3', 'method': 'Hierba alta (Mañana y Día)'},
            {'area': 'Ruta 4', 'method': 'Hierba alta (Mañana y Día)'},
            {'area': 'Ruta 7', 'method': 'Hierba alta (Mañana y Día), Golpe Cabeza en árboles'},
            {'area': 'Ruta 9', 'method': 'Hierba alta (Mañana y Día)'},
            {'area': 'Ruta 10', 'method': 'Hierba alta (Mañana y Día)'},
            {'area': 'Ruta 11', 'method': 'Golpe Cabeza en árboles'},
            {'area': 'Ruta 16', 'method': 'Golpe Cabeza en árboles'},
            {'area': 'Ruta 22', 'method': 'Hierba alta (Mañana y Día)'},
            {'area': 'Ciudad Azulona', 'method': 'Golpe Cabeza en árboles'},
            {'area': 'Ciudad Carmín', 'method': 'Golpe Cabeza en árboles'},
            {'area': 'Ciudad Trigal (Paso Norte)', 'method': 'Regalo del guardia con Carta (Spearow «ESPI» al Nv. 20; equípale la carta a otro Pokémon para quedártelo)'},
            {'area': 'Zona Safari (Pantano)', 'method': 'Hierba alta (Mañana y Día)'},
            {'area': 'Pokéwalker (Bosque Murmullos)', 'method': 'Paseo en el Pokéwalker'},
            DAYCARE_LOCATION
        ]
    },
    66: {
        'type': 'wild',
        'badge_label': 'Salvaje / Intercambio',
        'badge_color': 'emerald',
        'summary': 'Salvaje en Monte Mortero, Ruta 47 y Túnel Roca. También por intercambio en Ciudad Trigal (P5).',
        'locations': [
            {'area': 'Monte Mortero', 'method': 'Hierba alta / Encuentro en cueva'},
            {'area': 'Ruta 47 (Interior de la Cueva)', 'method': 'Hierba alta'},
            {'area': 'Túnel Roca', 'method': 'Hierba alta'},
            {'area': 'Centro Comercial de Ciudad Trigal (P5)', 'method': 'Intercambio por un Drowzee (Machop Machito)'},
            {'area': 'Zona Safari (Páramo)', 'method': 'Hierba alta (Mañana y Día)'},
            {'area': 'Pokéwalker (Camino Pedregoso)', 'method': 'Paseo en el Pokéwalker'},
            {'area': 'Pokéwalker (Cueva Sombría)', 'method': 'Paseo en el Pokéwalker'},
            {'area': 'Pokéwalker (Cueva del Terror)', 'method': 'Paseo en el Pokéwalker'},
            DAYCARE_LOCATION
        ]
    },
    82: {
        'type': 'wild',
        'badge_label': 'Salvaje / Intercambio',
        'badge_color': 'indigo',
        'summary': 'Salvaje en Cueva Celeste y Zona Safari. También por intercambio en la Central de Energía de Kanto a cambio de un Dugtrio, o evolucionando de Magnemite al Nivel 30.',
        'locations': [
            {'area': 'Cueva Celeste (P1, P2 y Sótano B1)', 'method': 'Encuentro en cueva'},
            {'area': 'Central de Energía', 'method': 'Intercambio por un Dugtrio'},
            {'area': 'Zona Safari (Peña)', 'method': 'Hierba alta'},
            {'area': 'Zona Safari (Montaña)', 'method': 'Hierba alta'}
        ]
    },
    85: {
        'type': 'wild',
        'badge_label': 'Salvaje / Intercambio',
        'badge_color': 'emerald',
        'summary': 'Salvaje en Rutas 26 y 28, Monte Plateado y Zona Safari. También por intercambio en Ciudad Endrino.',
        'locations': [
            {'area': 'Ruta 26', 'method': 'Hierba alta (Mañana y Día)'},
            {'area': 'Ruta 28', 'method': 'Hierba alta (Mañana y Día)'},
            {'area': 'Monte Plateado (Exterior)', 'method': 'Hierba alta (Mañana y Día)'},
            {'area': 'Ciudad Endrino', 'method': 'Intercambio por Dragonair hembra (Dodrio Doris)'},
            {'area': 'Zona Safari (Lagos)', 'method': 'Hierba alta'}
        ]
    },
    95: {
        'type': 'wild',
        'badge_label': 'Salvaje / Intercambio',
        'badge_color': 'emerald',
        'summary': 'Salvaje en Cueva Unión, Ruta 47, Túnel Roca y Calle Victoria. También por intercambio en Ciudad Malva.',
        'locations': [
            {'area': 'Cueva Unión', 'method': 'Encuentro en cuevas'},
            {'area': 'Ruta 47 (Interior de la Cueva)', 'method': 'Encuentro en cuevas'},
            {'area': 'Túnel Roca', 'method': 'Encuentro en cuevas'},
            {'area': 'Calle Victoria', 'method': 'Encuentro en cuevas'},
            {'area': 'Monte Plateado', 'method': 'Encuentro en cuevas'},
            {'area': 'Ciudad Malva', 'method': 'Intercambio por un Bellsprout (Onix Rocoso)'},
            {'area': 'Zona Safari (Páramo)', 'method': 'Hierba alta'},
            {'area': 'Pokéwalker (Camino Pedregoso)', 'method': 'Paseo en el Pokéwalker'},
            {'area': 'Pokéwalker (Cueva Sombría)', 'method': 'Paseo en el Pokéwalker'},
            {'area': 'Pokéwalker (Confín del Cielo)', 'method': 'Paseo en el Pokéwalker'},
            DAYCARE_LOCATION
        ]
    },
    100: {
        'type': 'wild',
        'badge_label': 'Salvaje / Intercambio',
        'badge_color': 'emerald',
        'summary': 'Salvaje en Ruta 10 y Zona Safari (Laguna). Trampa interactiva en la Guarida Rocket de Caoba. También por intercambio en Ciudad Olivo a cambio de un Krabby.',
        'locations': [
            {'area': 'Ruta 10', 'method': 'Hierba alta'},
            {'area': 'Zona Safari (Laguna)', 'method': 'Hierba alta'},
            {'area': 'Guarida del Team Rocket (Ciudad Caoba)', 'method': 'Trampa con forma de Poké Ball en el suelo'},
            {'area': 'Ciudad Olivo', 'method': 'Intercambio por un Krabby (Voltorb Billy)'},
            DAYCARE_LOCATION
        ]
    },
    101: {
        'type': 'wild',
        'badge_label': 'Salvaje / Interactivo',
        'badge_color': 'emerald',
        'summary': 'Salvaje en Cueva Celeste. Encuentro interactivo obligatorio combatiendo contra los 3 Electrode que alimentan el generador en la Guarida del Team Rocket en Caoba.',
        'locations': [
            {'area': 'Guarida del Team Rocket (Ciudad Caoba)', 'method': 'Encuentro interactivo (Generador Rocket a Nivel 23)'},
            {'area': 'Cueva Celeste (P1, P2 y Sótano B1)', 'method': 'Encuentro en cueva'}
        ]
    },
    74: {
        'type': 'wild',
        'badge_label': 'Salvaje',
        'badge_color': 'emerald',
        'summary': 'Común en cuevas, rutas montañosas y Ruinas Alfa. También encuentro trampa en Caoba.',
        'locations': [
            {'area': 'Cueva Oscura', 'method': 'Golpe Roca, Hierba alta'},
            {'area': 'Cueva Unión', 'method': 'Hierba alta'},
            {'area': 'Monte Mortero', 'method': 'Hierba alta'},
            {'area': 'Ruinas Alfa (Exterior)', 'method': 'Golpe Roca'},
            {'area': 'Ruta 45', 'method': 'Hierba alta'},
            {'area': 'Ruta 46', 'method': 'Hierba alta'},
            {'area': 'Ruta 47 (Interior de la Cueva)', 'method': 'Hierba alta'},
            {'area': 'Monte Moon', 'method': 'Hierba alta'},
            {'area': 'Túnel Roca', 'method': 'Golpe Roca, Hierba alta'},
            {'area': 'Calle Victoria', 'method': 'Golpe Roca'},
            {'area': 'Cueva Celeste', 'method': 'Golpe Roca'},
            {'area': 'Guarida del Team Rocket (Ciudad Caoba)', 'method': 'Trampa con forma de Poké Ball en el suelo'},
            {'area': 'Zona Safari (Peña)', 'method': 'Hierba alta'},
            {'area': 'Pokéwalker (Camino Pedregoso)', 'method': 'Paseo en el Pokéwalker'},
            {'area': 'Pokéwalker (Sendero Volcán)', 'method': 'Paseo en el Pokéwalker'},
            {'area': 'Pokéwalker (Confín del Cielo)', 'method': 'Paseo en el Pokéwalker'},
            DAYCARE_LOCATION
        ]
    },
    109: {
        'type': 'wild',
        'badge_label': 'Salvaje',
        'badge_color': 'emerald',
        'summary': 'Salvaje en Torre Quemada y Zona Safari. También encuentro trampa en la Guarida Rocket de Caoba.',
        'locations': [
            {'area': 'Torre Quemada (P1 y Sótano B1)', 'method': 'Encuentro en torre'},
            {'area': 'Guarida del Team Rocket (Ciudad Caoba)', 'method': 'Trampa con forma de Poké Ball en el suelo'},
            DAYCARE_LOCATION
        ]
    },
    111: {
        'type': 'wild',
        'badge_label': 'Salvaje / Intercambio',
        'badge_color': 'emerald',
        'summary': 'Salvaje en Calle Victoria y Zona Safari. También por intercambio con Brock en la Cueva Diglett a cambio de un Bonsly.',
        'locations': [
            {'area': 'Calle Victoria (P1, P2, P3)', 'method': 'Encuentro en cueva'},
            {'area': 'Cueva Diglett', 'method': 'Intercambio con Brock por Bonsly (con Colmillo Rayo)'},
            DAYCARE_LOCATION
        ]
    },
    178: {
        'type': 'trade',
        'badge_label': 'Intercambio NPC',
        'badge_color': 'amber',
        'summary': 'Inaccesible en estado salvaje en HeartGold. Obtenible mediante intercambio por un Haunter en el Centro Pokémon de Ciudad Plateada, o evolucionando de Natu al Nivel 25.',
        'locations': [
            {'area': 'Ciudad Plateada (Centro Pokémon)', 'method': 'Intercambio por un Haunter (Xatu Paulie)'}
        ]
    },
    208: {
        'type': 'wild',
        'badge_label': 'Salvaje / Intercambio',
        'badge_color': 'indigo',
        'summary': 'Salvaje en Monte Plateado y Ruta 47. También por intercambio con Yasmina o evolucionando de Onix.',
        'locations': [
            {'area': 'Monte Plateado (P2)', 'method': 'Encuentro en cuevas'},
            {'area': 'Ruta 47 (Interior de la Cueva)', 'method': 'Encuentro en cuevas'},
            {'area': 'Gimnasio de Ciudad Olivo', 'method': 'Intercambio con Yasmina (por cualquier Pokémon)'}
        ]
    },
    137: {
        'type': 'casino',
        'badge_label': 'Casino',
        'badge_color': 'amber',
        'summary': 'Premio canjeable por 9.999 fichas en el Rincón de Premios de Ciudad Azulona (también obtenible mediante crianza).',
        'locations': [
            {'area': 'Ciudad Azulona (Rincón de Premios)', 'method': 'Canje por 9.999 fichas del Casino'},
            DAYCARE_LOCATION
        ]
    },
    23: {
        'type': 'wild',
        'badge_label': 'Salvaje / Casino',
        'badge_color': 'emerald',
        'summary': 'Salvaje en la Zona Safari (Pantano) y canjeable por 700 fichas en el Casino de Ciudad Trigal (también obtenible mediante crianza).',
        'locations': [
            {'area': 'Zona Safari (Pantano)', 'method': 'Hierba alta (Mañana y Día)'},
            {'area': 'Casino de Ciudad Trigal', 'method': 'Premio del Casino (700 fichas)'},
            DAYCARE_LOCATION
        ]
    },
    63: {
        'type': 'wild',
        'badge_label': 'Salvaje / Casino',
        'badge_color': 'emerald',
        'summary': 'Salvaje en Rutas 34 y 35, rutas de Kanto y Zona Safari. También canjeable en el Casino de Ciudad Trigal.',
        'locations': [
            {'area': 'Ruta 34', 'method': 'Hierba alta'},
            {'area': 'Ruta 35', 'method': 'Hierba alta'},
            {'area': 'Ruta 5', 'method': 'Hierba alta'},
            {'area': 'Ruta 6', 'method': 'Hierba alta'},
            {'area': 'Ruta 8', 'method': 'Hierba alta'},
            {'area': 'Ruta 24', 'method': 'Hierba alta'},
            {'area': 'Ruta 25', 'method': 'Hierba alta'},
            {'area': 'Casino de Ciudad Trigal', 'method': 'Premio del Casino (200 fichas)'},
            {'area': 'Zona Safari (Prado)', 'method': 'Hierba alta'},
            {'area': 'Pokéwalker (Arrabal)', 'method': 'Paseo en el Pokéwalker'},
            DAYCARE_LOCATION
        ]
    },
    122: {
        'type': 'wild',
        'badge_label': 'Salvaje / Casino',
        'badge_color': 'emerald',
        'summary': 'Salvaje en Ruta 21 y Zona Safari (Arboleda). También canjeable por 3.333 fichas en el Rincón de Premios de Ciudad Azulona (también obtenible mediante crianza).',
        'locations': [
            {'area': 'Ruta 21 (Ruta Marítima)', 'method': 'Hierba alta'},
            {'area': 'Zona Safari (Arboleda)', 'method': 'Hierba alta'},
            {'area': 'Ciudad Azulona (Rincón de Premios)', 'method': 'Premio del Casino (3.333 fichas)'},
            DAYCARE_LOCATION
        ]
    },
    147: {
        'type': 'wild',
        'badge_label': 'Salvaje / Regalo',
        'badge_color': 'indigo',
        'summary': 'Salvaje en Guarida Dragón (Surf y Pesca) y Zona Safari. Regalo del Maestro Dragón tras derrotar a Débora (con Velocidad Extrema) o canjeable por 2.100 fichas en el Casino de Trigal.',
        'locations': [
            {'area': 'Guarida Dragón', 'method': 'Surf'},
            {'area': 'Guarida Dragón', 'method': 'Pesca (Caña Buena y Supercaña)'},
            {'area': 'Guarida Dragón (Templo)', 'method': 'Regalo del Maestro Dragón al Nv. 15 tras derrotar a Débora en el Gimnasio y responder a su prueba en el Santuario (con Velocidad Extrema si respondes con empatía)'},
            {'area': 'Casino de Ciudad Trigal', 'method': 'Premio del Casino (2.100 fichas)'},
            DAYCARE_LOCATION
        ]
    },
    72: {
        'type': 'wild',
        'badge_label': 'Salvaje',
        'badge_color': 'emerald',
        'summary': 'Abundante en estado salvaje mediante Surf y Pesca en rutas de Johto y Kanto.',
        'locations': [
            {'area': 'Ruta 32', 'method': 'Surf'},
            {'area': 'Ruta 32', 'method': 'Pesca (Caña Vieja, Buena y Supercaña)'},
            {'area': 'Ruta 34', 'method': 'Surf'},
            {'area': 'Ruta 40 (Ruta Marítima)', 'method': 'Surf'},
            {'area': 'Ruta 41 (Ruta Marítima)', 'method': 'Surf'},
            {'area': 'Ruta 41 (Ruta Marítima)', 'method': 'Pesca (Caña Buena y Vieja)'},
            {'area': 'Ruta 47', 'method': 'Surf'},
            {'area': 'Ruta 47', 'method': 'Pesca (Caña Buena y Vieja)'},
            {'area': 'Ciudad Cerezo', 'method': 'Surf'},
            {'area': 'Ciudad Olivo', 'method': 'Surf'},
            {'area': 'Ciudad Orquídea', 'method': 'Surf'},
            {'area': 'Islas Remolino', 'method': 'Surf'},
            {'area': 'Cueva Unión', 'method': 'Surf'},
            {'area': 'Ruta 12', 'method': 'Surf'},
            {'area': 'Ruta 12', 'method': 'Pesca (Caña Vieja, Buena y Supercaña)'},
            {'area': 'Ruta 13', 'method': 'Surf'},
            {'area': 'Ruta 13', 'method': 'Pesca (Caña Vieja, Buena y Supercaña)'},
            {'area': 'Ruta 19 (Ruta Marítima)', 'method': 'Surf'},
            {'area': 'Ruta 20 (Ruta Marítima)', 'method': 'Surf'},
            {'area': 'Ruta 20 (Ruta Marítima)', 'method': 'Pesca (Caña Buena y Vieja)'},
            {'area': 'Ruta 21 (Ruta Marítima)', 'method': 'Surf'},
            {'area': 'Ruta 21 (Ruta Marítima)', 'method': 'Pesca (Caña Buena y Vieja)'},
            {'area': 'Ruta 26', 'method': 'Surf'},
            {'area': 'Ruta 26', 'method': 'Pesca (Caña Buena y Vieja)'},
            {'area': 'Ruta 27', 'method': 'Surf'},
            {'area': 'Ruta 27', 'method': 'Pesca (Caña Buena y Vieja)'},
            {'area': 'Ciudad Carmín', 'method': 'Surf'},
            {'area': 'Ciudad Carmín', 'method': 'Pesca (Caña Buena y Vieja)'},
            {'area': 'Isla Canela', 'method': 'Surf'},
            {'area': 'Isla Canela', 'method': 'Pesca (Caña Buena y Vieja)'},
            {'area': 'Pueblo Paleta', 'method': 'Surf'},
            {'area': 'Pueblo Paleta', 'method': 'Pesca (Caña Buena y Vieja)'},
            {'area': 'Ciudad Orquídea (Centro Pokémon)', 'method': 'Regalo de emergencia anti-bloqueo (Nv. 15) si quedas atrapado en la isla sin Surf, Vuelo ni caña para pescar un Pokémon que aprenda Surf'},
            {'area': 'Pokéwalker (Mar Azul)', 'method': 'Paseo en el Pokéwalker'},
            DAYCARE_LOCATION
        ]
    },
    179: {
        'type': 'wild',
        'badge_label': 'Salvaje / Regalo',
        'badge_color': 'emerald',
        'summary': 'Salvaje en Rutas 32, 42 y 43 y Zona Safari. También huevo de regalo de Primo en Ciudad Malva.',
        'locations': [
            {'area': 'Ruta 32', 'method': 'Hierba alta'},
            {'area': 'Ruta 42', 'method': 'Hierba alta'},
            {'area': 'Ruta 43', 'method': 'Hierba alta'},
            {'area': 'Ciudad Malva (Centro Pokémon)', 'method': 'Huevo de regalo de Primo (Contraseña basada en tu ID)'},
            {'area': 'Pokéwalker (Senda Glacial)', 'method': 'Paseo en el Pokéwalker'},
            {'area': 'Pokéwalker (Gran Bosque)', 'method': 'Paseo en el Pokéwalker'},
            DAYCARE_LOCATION
        ]
    },
    194: {
        'type': 'wild',
        'badge_label': 'Salvaje / Regalo',
        'badge_color': 'emerald',
        'summary': 'Salvaje en Ruta 32, Ruinas Alfa, Cueva Unión y Ruta 47. También huevo de regalo en Ciudad Malva.',
        'locations': [
            {'area': 'Ruta 32', 'method': 'Hierba alta (Noche)'},
            {'area': 'Ruinas Alfa (Exterior)', 'method': 'Surf'},
            {'area': 'Cueva Unión', 'method': 'Surf'},
            {'area': 'Ruta 47', 'method': 'Hierba alta y Surf'},
            {'area': 'Ciudad Malva (Centro Pokémon)', 'method': 'Huevo de regalo de Primo (Contraseña basada en tu ID)'},
            {'area': 'Zona Safari (Pantano)', 'method': 'Hierba alta (Noche) / Surf'},
            {'area': 'Zona Safari (Parterre)', 'method': 'Hierba alta (Noche) / Surf'},
            {'area': 'Zona Safari (Albufera)', 'method': 'Hierba alta (Noche) / Surf'},
            {'area': 'Pokéwalker (Costa Bella)', 'method': 'Paseo en el Pokéwalker'},
            DAYCARE_LOCATION
        ]
    },
    218: {
        'type': 'wild',
        'badge_label': 'Salvaje / Regalo',
        'badge_color': 'emerald',
        'summary': 'Salvaje en Rutas 16, 17 y 18 (Camino de Bicis). También huevo de regalo de Primo en Ciudad Malva.',
        'locations': [
            {'area': 'Ruta 16', 'method': 'Hierba alta'},
            {'area': 'Ruta 17', 'method': 'Hierba alta'},
            {'area': 'Ruta 18', 'method': 'Hierba alta'},
            {'area': 'Ciudad Malva (Centro Pokémon)', 'method': 'Huevo de regalo de Primo (Contraseña basada en tu ID)'},
            {'area': 'Pokéwalker (Sendero Volcán)', 'method': 'Paseo en el Pokéwalker'},
            DAYCARE_LOCATION
        ]
    },

    # --- FÓSILES RESTANTES ---
    408: {
        'type': 'fossil',
        'badge_label': 'Fósil Cráneo',
        'badge_color': 'amber',
        'summary': 'Revivir el Fósil Cráneo (exclusivo de HeartGold rompiendo rocas con Golpe Roca en Ruinas Alfa y Cueva Acantilado tras obtener la Dex Nacional) en el Museo de Ciudad Plateada.',
        'locations': [
            {'area': 'Ruinas Alfa / Cueva Acantilado', 'method': 'Fósil Cráneo (Golpe Roca tras Dex Nacional)'},
            {'area': 'Ciudad Plateada (Museo)', 'method': 'Revitalización de Fósil Cráneo'},
            DAYCARE_LOCATION
        ]
    },
    140: {
        'type': 'trade',
        'badge_label': 'Exclusivo SoulSilver',
        'badge_color': 'sky',
        'summary': 'Inaccesible de forma directa en HeartGold (el Fósil Domo es exclusivo de SoulSilver por Golpe Roca). Requiere transferir el fósil o intercambiar con SoulSilver.',
        'locations': [
            {'area': 'Intercambio con SoulSilver / Parque Compi', 'method': 'Transferencia de Fósil Domo o Pokémon'},
            {'area': 'Ciudad Plateada (Museo)', 'method': 'Revitalización de Fósil Domo (si se transfiere)'},
            DAYCARE_LOCATION
        ]
    },
    141: {
        'type': 'trade',
        'badge_label': 'Exclusivo SoulSilver',
        'badge_color': 'sky',
        'summary': 'Inaccesible en estado salvaje en HeartGold. Requiere intercambiar con SoulSilver o evolucionar a Kabuto al Nivel 40.',
        'locations': [
            {'area': 'Intercambio con Pokémon Plata SoulSilver', 'method': 'Exclusivo de versión'}
        ]
    },
    345: {
        'type': 'trade',
        'badge_label': 'Exclusivo SoulSilver',
        'badge_color': 'sky',
        'summary': 'Inaccesible de forma directa en HeartGold (el Fósil Raíz es exclusivo de SoulSilver por Golpe Roca). Requiere transferir el fósil o intercambiar con SoulSilver.',
        'locations': [
            {'area': 'Intercambio con SoulSilver / Parque Compi', 'method': 'Transferencia de Fósil Raíz o Pokémon'},
            {'area': 'Ciudad Plateada (Museo)', 'method': 'Revitalización de Fósil Raíz (si se transfiere)'},
            DAYCARE_LOCATION
        ]
    },
    346: {
        'type': 'trade',
        'badge_label': 'Exclusivo SoulSilver',
        'badge_color': 'sky',
        'summary': 'Inaccesible en estado salvaje en HeartGold. Requiere intercambiar con SoulSilver o evolucionar a Lileep al Nivel 40.',
        'locations': [
            {'area': 'Intercambio con Pokémon Plata SoulSilver', 'method': 'Exclusivo de versión'}
        ]
    },
    410: {
        'type': 'trade',
        'badge_label': 'Exclusivo SoulSilver',
        'badge_color': 'sky',
        'summary': 'Inaccesible de forma directa en HeartGold (el Fósil Coraza es exclusivo de SoulSilver). Requiere transferir el fósil o intercambiar con SoulSilver.',
        'locations': [
            {'area': 'Intercambio con Pokémon Plata SoulSilver', 'method': 'Transferencia de Fósil Coraza o Pokémon'},
            {'area': 'Ciudad Plateada (Museo)', 'method': 'Revitalización de Fósil Coraza (si se transfiere)'},
            DAYCARE_LOCATION
        ]
    },
    411: {
        'type': 'trade',
        'badge_label': 'Exclusivo SoulSilver',
        'badge_color': 'sky',
        'summary': 'Inaccesible en estado salvaje en HeartGold. Requiere intercambiar con SoulSilver o evolucionar a Shieldon al Nivel 30.',
        'locations': [
            {'area': 'Intercambio con Pokémon Plata SoulSilver', 'method': 'Exclusivo de versión'}
        ]
    },

    # --- EVENTOS Y LEGENDARIOS ESPECIALES ---
    483: {
        'type': 'event',
        'badge_label': 'Ruinas de Sinjoh',
        'badge_color': 'indigo',
        'summary': 'Obtenible al Nivel 1 en las Ruinas de Sinjoh al acudir con Arceus y hablar con Cintia (sosteniendo la Diamansfera). Elige el círculo de la izquierda (azul).',
        'locations': [
            {'area': 'Ruinas de Sinjoh', 'method': 'Creación mística de Arceus a Nivel 1 (Diamansfera)'}
        ]
    },
    484: {
        'type': 'event',
        'badge_label': 'Ruinas de Sinjoh',
        'badge_color': 'indigo',
        'summary': 'Obtenible al Nivel 1 en las Ruinas de Sinjoh al acudir con Arceus y hablar con Cintia (sosteniendo la Lustresfera). Elige el círculo de la derecha (rosa).',
        'locations': [
            {'area': 'Ruinas de Sinjoh', 'method': 'Creación mística de Arceus a Nivel 1 (Lustresfera)'}
        ]
    },
    487: {
        'type': 'event',
        'badge_label': 'Ruinas de Sinjoh',
        'badge_color': 'indigo',
        'summary': 'Obtenible al Nivel 1 en su Forma Origen en las Ruinas de Sinjoh al acudir con Arceus y hablar con Cintia (sosteniendo la Griseosfera). Elige el círculo superior (rojo).',
        'locations': [
            {'area': 'Ruinas de Sinjoh', 'method': 'Creación mística de Arceus a Nivel 1 (Griseosfera)'}
        ]
    },
    489: {
        'type': 'baby',
        'badge_label': 'Crianza',
        'badge_color': 'pink',
        'summary': 'Obtenible mediante crianza en la Guardería de la Ruta 34 dejando a Manaphy (o a otro Phione) junto a Ditto. También transferible mediante intercambio desde Pokémon Diamante, Perla o Platino.',
        'locations': [
            {'area': 'Ruta 34 (Guardería Pokémon)', 'method': 'Crianza dejando a Manaphy o Phione con Ditto'},
            {'area': 'Intercambio con D/P/Pt', 'method': 'Intercambio desde Pokémon Diamante, Perla o Platino'}
        ]
    },
    490: {
        'type': 'event',
        'badge_label': 'Huevo Ranger',
        'badge_color': 'sky',
        'summary': 'Transferencia del Huevo de Manaphy desde Pokémon Ranger: Trazos de Luz. Se recibe hablando con el repartidor en cualquier Tienda Pokémon de Johto (también permite criar a Phione).',
        'locations': [
            {'area': 'Tienda Pokémon de Johto', 'method': 'Repartidor de evento (Transferencia desde Pokémon Ranger: Trazos de Luz)'}
        ],
        'historical_note': {
            'title': 'Nota Histórica • El Huevo de Manaphy y Pokémon Ranger',
            'icon_url': '/media/items/mystery-egg.png',
            'text': 'A diferencia de Pokémon Diamante, Perla y Platino (cuyo huevo podía transferirse desde el primer Pokémon Ranger mediante una contraseña offline permanente), en Pokémon Oro HeartGold y Plata SoulSilver la transferencia del Huevo de Manaphy requería la misión especial de Pokémon Ranger: Trazos de Luz. Dicha misión fue distribuida exclusivamente a través de la Conexión Wi-Fi de Nintendo por tiempo limitado entre octubre de 2010 y enero de 2011, por lo que tras el cierre de los servidores oficiales de Nintendo DS ya no es posible descargar la misión legítimamente.<br><br>Asimismo, aunque Manaphy pertenece al grupo de cría de agua y puede reproducirse con Ditto en la Guardería de la Ruta 34, de sus huevos siempre nacerá Phione, siendo imposible obtener un nuevo Manaphy mediante crianza.'
        }
    },
    493: {
        'type': 'event',
        'badge_label': 'Evento Especial',
        'badge_color': 'indigo',
        'summary': 'Inaccesible en estado salvaje. Requiere distribución oficial de evento de Nintendo (o intercambio con D/P/Pt). Activa el evento místico de las Ruinas de Sinjoh al llevarlo como acompañante.',
        'locations': [
            {'area': 'Evento oficial de Nintendo / D/P/Pt', 'method': 'Distribución oficial de evento (activa Ruinas de Sinjoh)'}
        ]
    },
    383: {
        'type': 'legendary',
        'badge_label': 'Exclusivo SoulSilver',
        'badge_color': 'rose',
        'summary': 'Legendario exclusivo de Pokémon Plata SoulSilver en la Torre Oculta (Ruta 47) con la Esfera Roja. Requiere intercambio para registrarlo en HeartGold (y desbloquear a Rayquaza).',
        'locations': [
            {'area': 'Intercambio con Pokémon Plata SoulSilver', 'method': 'Legendario exclusivo de versión'}
        ]
    },

    # --- EXCLUSIVOS DE SOULSILVER ---
    37: {
        'type': 'trade',
        'badge_label': 'Exclusivo SoulSilver',
        'badge_color': 'sky',
        'summary': 'Exclusivo de Pokémon Plata SoulSilver (Rutas 7, 8, 36, 37, 48). Requiere intercambio para conseguirlo en HeartGold (también obtenible mediante crianza).',
        'locations': [
            {'area': 'Intercambio con Pokémon Plata SoulSilver', 'method': 'Exclusivo de versión'},
            DAYCARE_LOCATION
        ]
    },
    38: {
        'type': 'evolution',
        'badge_label': 'Exclusivo SoulSilver',
        'badge_color': 'sky',
        'summary': 'Exclusivo de Pokémon Plata SoulSilver. Evoluciona de Vulpix usando Piedra Fuego (requiere intercambio desde SoulSilver).',
        'locations': [
            {'area': 'Intercambio con Pokémon Plata SoulSilver', 'method': 'Evolución de Vulpix transferido'}
        ]
    },
    52: {
        'type': 'trade',
        'badge_label': 'Exclusivo SoulSilver',
        'badge_color': 'sky',
        'summary': 'Exclusivo de Pokémon Plata SoulSilver (Rutas 5, 6, 7, 8, 38, 39). Requiere intercambio para conseguirlo en HeartGold (también obtenible mediante crianza).',
        'locations': [
            {'area': 'Intercambio con Pokémon Plata SoulSilver', 'method': 'Exclusivo de versión'},
            DAYCARE_LOCATION
        ]
    },
    53: {
        'type': 'evolution',
        'badge_label': 'Exclusivo SoulSilver',
        'badge_color': 'sky',
        'summary': 'Exclusivo de Pokémon Plata SoulSilver. Evoluciona de Meowth al Nivel 28 (requiere intercambio desde SoulSilver).',
        'locations': [
            {'area': 'Intercambio con Pokémon Plata SoulSilver', 'method': 'Evolución de Meowth transferido'}
        ]
    },
    165: {
        'type': 'trade',
        'badge_label': 'Exclusivo SoulSilver',
        'badge_color': 'sky',
        'summary': 'Exclusivo de Pokémon Plata SoulSilver (Rutas 30, 31, 37 por la mañana). Requiere intercambio para conseguirlo en HeartGold (también obtenible mediante crianza).',
        'locations': [
            {'area': 'Intercambio con Pokémon Plata SoulSilver', 'method': 'Exclusivo de versión'},
            DAYCARE_LOCATION
        ]
    },
    166: {
        'type': 'evolution',
        'badge_label': 'Exclusivo SoulSilver',
        'badge_color': 'sky',
        'summary': 'Exclusivo de Pokémon Plata SoulSilver. Evoluciona de Ledyba al Nivel 18 (requiere intercambio desde SoulSilver).',
        'locations': [
            {'area': 'Intercambio con Pokémon Plata SoulSilver', 'method': 'Evolución de Ledyba transferido'}
        ]
    },
    216: {
        'type': 'trade',
        'badge_label': 'Exclusivo SoulSilver',
        'badge_color': 'sky',
        'summary': 'Exclusivo de Pokémon Plata SoulSilver (Ruta 45, Cueva Oscura). Requiere intercambio para conseguirlo en HeartGold (también obtenible mediante crianza).',
        'locations': [
            {'area': 'Intercambio con Pokémon Plata SoulSilver', 'method': 'Exclusivo de versión'},
            DAYCARE_LOCATION
        ]
    },
    217: {
        'type': 'trade',
        'badge_label': 'Exclusivo SoulSilver',
        'badge_color': 'sky',
        'summary': 'Exclusivo de Pokémon Plata SoulSilver (Ruta 28, Monte Plateado). Requiere intercambio o evolucionar de Teddiursa al Nivel 30.',
        'locations': [
            {'area': 'Intercambio con Pokémon Plata SoulSilver', 'method': 'Exclusivo de versión'}
        ]
    },
    225: {
        'type': 'trade',
        'badge_label': 'Exclusivo SoulSilver',
        'badge_color': 'sky',
        'summary': 'Exclusivo de Pokémon Plata SoulSilver (Ruta Helada). Requiere intercambio para conseguirlo en HeartGold (también obtenible mediante crianza).',
        'locations': [
            {'area': 'Intercambio con Pokémon Plata SoulSilver', 'method': 'Exclusivo de versión'},
            DAYCARE_LOCATION
        ]
    },
    227: {
        'type': 'trade',
        'badge_label': 'Exclusivo SoulSilver',
        'badge_color': 'sky',
        'summary': 'Exclusivo de Pokémon Plata SoulSilver (Ruta 45). Requiere intercambio para conseguirlo en HeartGold (también obtenible mediante crianza).',
        'locations': [
            {'area': 'Intercambio con Pokémon Plata SoulSilver', 'method': 'Exclusivo de versión'},
            DAYCARE_LOCATION
        ]
    },
    303: {
        'type': 'trade',
        'badge_label': 'Exclusivo SoulSilver',
        'badge_color': 'sky',
        'summary': 'Exclusivo de Pokémon Plata SoulSilver (Manada en Ruta 9 tras Dex Nacional). Requiere intercambio para conseguirlo en HeartGold (también obtenible mediante crianza).',
        'locations': [
            {'area': 'Intercambio con Pokémon Plata SoulSilver', 'method': 'Exclusivo de versión'},
            DAYCARE_LOCATION
        ]
    },
    316: {
        'type': 'trade',
        'badge_label': 'Exclusivo SoulSilver',
        'badge_color': 'sky',
        'summary': 'Exclusivo de Pokémon Plata SoulSilver (Manada en Ruta 3 tras Dex Nacional). Requiere intercambio para conseguirlo en HeartGold (también obtenible mediante crianza).',
        'locations': [
            {'area': 'Intercambio con Pokémon Plata SoulSilver', 'method': 'Exclusivo de versión'},
            DAYCARE_LOCATION
        ]
    },
    317: {
        'type': 'evolution',
        'badge_label': 'Exclusivo SoulSilver',
        'badge_color': 'sky',
        'summary': 'Exclusivo de Pokémon Plata SoulSilver. Evoluciona de Gulpin al Nivel 26 (requiere intercambio desde SoulSilver).',
        'locations': [
            {'area': 'Intercambio con Pokémon Plata SoulSilver', 'method': 'Evolución de Gulpin transferido'}
        ]
    },

    # --- POKÉMON BEBÉ ESTÁNDAR (CRIANZA EN RUTA 34) ---
    173: {
        'type': 'baby',
        'badge_label': 'Crianza',
        'badge_color': 'pink',
        'summary': 'Pokémon bebé obtenible mediante crianza en la Guardería de la Ruta 34 dejando a Clefairy o Clefable, o en el Pokéwalker (Campo Amistad).',
        'locations': [
            {'area': 'Pokéwalker (Campo Amistad)', 'method': 'Paseo en el Pokéwalker'},
            DAYCARE_LOCATION
        ]
    },
    174: {
        'type': 'baby',
        'badge_label': 'Crianza',
        'badge_color': 'pink',
        'summary': 'Pokémon bebé obtenible mediante crianza en la Guardería de la Ruta 34 dejando a Jigglypuff o Wigglytuff, o en el Pokéwalker (Campo Amistad).',
        'locations': [
            {'area': 'Pokéwalker (Campo Amistad)', 'method': 'Paseo en el Pokéwalker'},
            DAYCARE_LOCATION
        ]
    },
    238: {
        'type': 'baby',
        'badge_label': 'Crianza',
        'badge_color': 'pink',
        'summary': 'Pokémon bebé obtenible mediante crianza en la Guardería de la Ruta 34 dejando a Jynx, o en el Pokéwalker (Cueva Sombría y Campo Amistad).',
        'locations': [
            {'area': 'Pokéwalker (Cueva Sombría)', 'method': 'Paseo en el Pokéwalker'},
            {'area': 'Pokéwalker (Campo Amistad)', 'method': 'Paseo en el Pokéwalker'},
            DAYCARE_LOCATION
        ]
    },
    239: {
        'type': 'baby',
        'badge_label': 'Crianza',
        'badge_color': 'pink',
        'summary': 'Pokémon bebé obtenible mediante crianza en la Guardería de la Ruta 34 dejando a Electabuzz o Electivire, o en el Pokéwalker (Urbanización y Campo Amistad).',
        'locations': [
            {'area': 'Pokéwalker (Urbanización)', 'method': 'Paseo en el Pokéwalker'},
            {'area': 'Pokéwalker (Campo Amistad)', 'method': 'Paseo en el Pokéwalker'},
            DAYCARE_LOCATION
        ]
    },
    240: {
        'type': 'baby',
        'badge_label': 'Crianza',
        'badge_color': 'pink',
        'summary': 'Pokémon bebé obtenible mediante crianza en la Guardería de la Ruta 34 dejando a Magmar o Magmortar, o en el Pokéwalker (Camino Pedregoso y Campo Amistad).',
        'locations': [
            {'area': 'Pokéwalker (Camino Pedregoso)', 'method': 'Paseo en el Pokéwalker'},
            {'area': 'Pokéwalker (Campo Amistad)', 'method': 'Paseo en el Pokéwalker'},
            DAYCARE_LOCATION
        ]
    },

    # --- POKÉMON BEBÉ CON INCIENSO (CRIANZA EN RUTA 34) ---
    360: {
        'type': 'baby',
        'badge_label': 'Crianza Incienso',
        'badge_color': 'pink',
        'summary': 'Pokémon bebé obtenible mediante crianza en la Guardería de la Ruta 34 dejando a Wobbuffet equipado con Incienso Lento.',
        'locations': [{'area': 'Ruta 34 (Guardería Pokémon)', 'method': 'Crianza con Incienso Lento'}]
    },
    438: {
        'type': 'baby',
        'badge_label': 'Crianza Incienso',
        'badge_color': 'pink',
        'summary': 'Pokémon bebé obtenible mediante crianza en la Guardería de la Ruta 34 dejando a Sudowoodo equipado con Incienso Roca, o en el Pokéwalker (Gran Bosque).',
        'locations': [
            {'area': 'Pokéwalker (Gran Bosque)', 'method': 'Paseo en el Pokéwalker'},
            {'area': 'Ruta 34 (Guardería Pokémon)', 'method': 'Crianza con Incienso Roca'}
        ]
    },
    439: {
        'type': 'baby',
        'badge_label': 'Crianza Incienso',
        'badge_color': 'pink',
        'summary': 'Pokémon bebé obtenible mediante crianza en la Guardería de la Ruta 34 dejando a Mr. Mime equipado con Incienso Raro, o en el Pokéwalker (Llano de Sinnoh).',
        'locations': [
            {'area': 'Pokéwalker (Llano de Sinnoh)', 'method': 'Paseo en el Pokéwalker'},
            {'area': 'Ruta 34 (Guardería Pokémon)', 'method': 'Crianza con Incienso Raro'}
        ]
    },
    440: {
        'type': 'baby',
        'badge_label': 'Crianza Incienso',
        'badge_color': 'pink',
        'summary': 'Pokémon bebé obtenible mediante crianza en la Guardería de la Ruta 34 dejando a Chansey o Blissey equipado con Incienso Suave, o en el Pokéwalker (Campo Amistad).',
        'locations': [
            {'area': 'Pokéwalker (Campo Amistad)', 'method': 'Paseo en el Pokéwalker'},
            {'area': 'Ruta 34 (Guardería Pokémon)', 'method': 'Crianza con Incienso Suave'}
        ]
    },
    446: {
        'type': 'baby',
        'badge_label': 'Crianza Incienso',
        'badge_color': 'pink',
        'summary': 'Pokémon bebé obtenible mediante crianza en la Guardería de la Ruta 34 dejando a Snorlax equipado con Incienso Lento, o en el Pokéwalker (Cueva Calma y Vía Campeón).',
        'locations': [
            {'area': 'Pokéwalker (Cueva Calma)', 'method': 'Paseo en el Pokéwalker'},
            {'area': 'Pokéwalker (Vía Campeón)', 'method': 'Paseo en el Pokéwalker'},
            {'area': 'Ruta 34 (Guardería Pokémon)', 'method': 'Crianza con Incienso Lento'}
        ]
    },
    458: {
        'type': 'baby',
        'badge_label': 'Crianza Incienso',
        'badge_color': 'pink',
        'summary': 'Pokémon bebé obtenible mediante crianza en la Guardería de la Ruta 34 dejando a Mantine equipado con Incienso Marino.',
        'locations': [{'area': 'Ruta 34 (Guardería Pokémon)', 'method': 'Crianza con Incienso Marino'}]
    },

    # --- ESPECIES NO AUTÓCTONAS DE HOENN / SINNOH (TRANSFERENCIA / POKÉWALKER) ---
    300: {
        'type': 'transfer',
        'badge_label': 'Transferir / Pokéwalker',
        'badge_color': 'rose',
        'summary': 'Inaccesible en estado salvaje en Johto y Kanto. Obtenible mediante transferencia desde Hoenn o Sinnoh vía Parque Compi, o en el Pokéwalker (Campo Amistad).',
        'locations': [
            {'area': 'Parque Compi / Intercambio', 'method': 'Transferencia desde Hoenn (GBA) o Sinnoh (NDS)'},
            {'area': 'Pokéwalker (Campo Amistad)', 'method': 'Paseo en el Pokéwalker'},
            DAYCARE_LOCATION
        ]
    },
    318: {
        'type': 'transfer',
        'badge_label': 'Transferir / Pokéwalker',
        'badge_color': 'rose',
        'summary': 'Inaccesible en estado salvaje en Johto y Kanto. Obtenible mediante transferencia desde Hoenn o Sinnoh vía Parque Compi, o en el Pokéwalker (Playa Cálida).',
        'locations': [
            {'area': 'Parque Compi / Intercambio', 'method': 'Transferencia desde Hoenn (GBA) o Sinnoh (NDS)'},
            {'area': 'Pokéwalker (Playa Cálida)', 'method': 'Paseo en el Pokéwalker'},
            DAYCARE_LOCATION
        ]
    },
    320: {
        'type': 'transfer',
        'badge_label': 'Transferir / Pokéwalker',
        'badge_color': 'rose',
        'summary': 'Inaccesible en estado salvaje en Johto y Kanto. Obtenible mediante transferencia desde Hoenn o Sinnoh vía Parque Compi, o en el Pokéwalker (Playa Cálida).',
        'locations': [
            {'area': 'Parque Compi / Intercambio', 'method': 'Transferencia desde Hoenn (GBA) o Sinnoh (NDS)'},
            {'area': 'Pokéwalker (Playa Cálida)', 'method': 'Paseo en el Pokéwalker'},
            DAYCARE_LOCATION
        ]
    },
    349: {
        'type': 'transfer',
        'badge_label': 'Transferir / Pokéwalker',
        'badge_color': 'rose',
        'summary': 'Inaccesible en estado salvaje en Johto y Kanto. Obtenible mediante transferencia desde R/S/E o D/P/Pt vía Parque Compi, o en el Pokéwalker (Cueva Calma).',
        'locations': [
            {'area': 'Parque Compi / Intercambio', 'method': 'Transferencia desde Hoenn (GBA) o Sinnoh (NDS)'},
            {'area': 'Pokéwalker (Cueva Calma)', 'method': 'Paseo en el Pokéwalker'},
            DAYCARE_LOCATION
        ]
    },
    351: {
        'type': 'transfer',
        'badge_label': 'Transferir / Pokéwalker',
        'badge_color': 'rose',
        'summary': 'Inaccesible en estado salvaje en Johto y Kanto. Obtenible mediante transferencia desde R/S/E o D/P/Pt vía Parque Compi, o en el Pokéwalker (Casa del Árbol).',
        'locations': [
            {'area': 'Parque Compi / Intercambio', 'method': 'Transferencia desde Hoenn (GBA) o Sinnoh (NDS)'},
            {'area': 'Pokéwalker (Casa del Árbol)', 'method': 'Paseo en el Pokéwalker'},
            DAYCARE_LOCATION
        ]
    },
    352: {
        'type': 'transfer',
        'badge_label': 'Transferir / Pokéwalker',
        'badge_color': 'rose',
        'summary': 'Inaccesible en estado salvaje en Johto y Kanto. Obtenible mediante transferencia desde R/S/E o D/P/Pt vía Parque Compi, o en el Pokéwalker (Casa del Árbol).',
        'locations': [
            {'area': 'Parque Compi / Intercambio', 'method': 'Transferencia desde Hoenn (GBA) o Sinnoh (NDS)'},
            {'area': 'Pokéwalker (Casa del Árbol)', 'method': 'Paseo en el Pokéwalker'},
            DAYCARE_LOCATION
        ]
    },
    357: {
        'type': 'transfer',
        'badge_label': 'Transferir / Pokéwalker',
        'badge_color': 'rose',
        'summary': 'Inaccesible en estado salvaje en Johto y Kanto. Obtenible mediante transferencia desde R/S/E o D/P/Pt vía Parque Compi, o en el Pokéwalker (Gran Bosque).',
        'locations': [
            {'area': 'Parque Compi / Intercambio', 'method': 'Transferencia desde Hoenn (GBA) o Sinnoh (NDS)'},
            {'area': 'Pokéwalker (Gran Bosque)', 'method': 'Paseo en el Pokéwalker'},
            DAYCARE_LOCATION
        ]
    },
    361: {
        'type': 'transfer',
        'badge_label': 'Transferir / Pokéwalker',
        'badge_color': 'rose',
        'summary': 'Inaccesible en estado salvaje en Johto y Kanto. Obtenible mediante transferencia desde R/S/E o D/P/Pt vía Parque Compi, o en el Pokéwalker (Senda Glacial).',
        'locations': [
            {'area': 'Parque Compi / Intercambio', 'method': 'Transferencia desde Hoenn (GBA) o Sinnoh (NDS)'},
            {'area': 'Pokéwalker (Senda Glacial)', 'method': 'Paseo en el Pokéwalker'},
            DAYCARE_LOCATION
        ]
    },
    422: {
        'type': 'transfer',
        'badge_label': 'Transferir / Pokéwalker',
        'badge_color': 'rose',
        'summary': 'Inaccesible en estado salvaje en Johto y Kanto. Obtenible mediante transferencia desde Pokémon Diamante, Perla o Platino, o en el Pokéwalker (Playa Tormenta).',
        'locations': [
            {'area': 'Intercambio con D/P/Pt', 'method': 'Intercambio desde Pokémon Diamante, Perla o Platino'},
            {'area': 'Pokéwalker (Playa Tormenta)', 'method': 'Paseo en el Pokéwalker'},
            DAYCARE_LOCATION
        ]
    },
    442: {
        'type': 'transfer',
        'badge_label': 'Transferir / Pokéwalker',
        'badge_color': 'rose',
        'summary': 'Inaccesible en estado salvaje en Johto y Kanto. Obtenible mediante transferencia desde Pokémon Diamante, Perla o Platino, o en el Pokéwalker (Cueva Calma).',
        'locations': [
            {'area': 'Intercambio con D/P/Pt', 'method': 'Intercambio desde Pokémon Diamante, Perla o Platino'},
            {'area': 'Pokéwalker (Cueva Calma)', 'method': 'Paseo en el Pokéwalker'},
            DAYCARE_LOCATION
        ]
    },
    456: {
        'type': 'transfer',
        'badge_label': 'Transferir / Pokéwalker',
        'badge_color': 'rose',
        'summary': 'Inaccesible en estado salvaje en Johto y Kanto. Obtenible mediante transferencia desde Pokémon Diamante, Perla o Platino, o en el Pokéwalker (Playa Tormenta).',
        'locations': [
            {'area': 'Intercambio con D/P/Pt', 'method': 'Intercambio desde Pokémon Diamante, Perla o Platino'},
            {'area': 'Pokéwalker (Playa Tormenta)', 'method': 'Paseo en el Pokéwalker'},
            DAYCARE_LOCATION
        ]
    },
    459: {
        'type': 'transfer',
        'badge_label': 'Transferir / Pokéwalker',
        'badge_color': 'rose',
        'summary': 'Inaccesible en estado salvaje en Johto y Kanto. Obtenible mediante transferencia desde Pokémon Diamante, Perla o Platino, o en el Pokéwalker (Senda Glacial).',
        'locations': [
            {'area': 'Intercambio con D/P/Pt', 'method': 'Intercambio desde Pokémon Diamante, Perla o Platino'},
            {'area': 'Pokéwalker (Senda Glacial)', 'method': 'Paseo en el Pokéwalker'},
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
    if 'swarm' in cond_names or 'swarm-yes' in cond_names:
        return 'Manada Pokémon (Aviso del Pokégear)'
    if 'bug-catching-contest-yes' in cond_names or method_raw == 'bug-catching-contest':
        return 'Concurso de Captura de Bichos'

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
        if 'headbutt-tree-special' in cond_names or 'headbutt-tree-rare' in cond_names or 'headbutt-tree-secret' in cond_names:
            return 'Golpe Cabeza (Árboles especiales)'
        return 'Golpe Cabeza en árboles'
    if method_raw == 'rock-smash':
        return 'Golpe Roca'
    if method_raw == 'bug-catching-contest':
        return 'Concurso de Captura de Bichos'
    if method_raw == 'npc-trade':
        if 'trade-pikachu' in cond_names:
            return 'Intercambio con Teniente Surge (por Pikachu)'
        if 'trade-drowzee' in cond_names:
            return 'Intercambio por un Drowzee (Machop Machito)'
        if 'trade-dugtrio' in cond_names:
            return 'Intercambio por un Dugtrio'
        if 'trade-dragonair' in cond_names:
            return 'Intercambio por Dragonair hembra (Dodrio Doris)'
        if 'trade-bellsprout' in cond_names:
            return 'Intercambio por un Bellsprout (Onix Rocoso)'
        if 'trade-krabby' in cond_names:
            return 'Intercambio por un Krabby (Voltorb Billy)'
        if 'trade-bonsly' in cond_names:
            return 'Intercambio con Brock (por Bonsly)'
        if 'trade-haunter' in cond_names:
            return 'Intercambio por un Haunter (Xatu Paulie)'
        if 'trade-forretress' in cond_names:
            return 'Intercambio con Máximo Peñas (por Forretress)'
        if 'trade-any-pokemon' in cond_names:
            return 'Intercambio con Yasmina (por cualquier Pokémon)'
        return 'Intercambio en el juego (NPC)'
    if method_raw == 'gift-egg':
        if 'other-correct-password' in cond_names:
            return 'Huevo de regalo de Primo (Contraseña de ID)'
        return 'Huevo de regalo'
    if method_raw == 'gift':
        coin_conds = [c for c in cond_names if 'coins' in c]
        if coin_conds:
            val = coin_conds[0].replace('coins-', '')
            return f'Premio del Casino ({val} fichas)'
        if 'story-progress-receive-tm-from-claire' in cond_names:
            return 'Regalo del Maestro Dragón (con Velocidad Extrema)'
        if any('fossil' in c for c in cond_names):
            return 'Revitalización de Fósil en Museo'
        return 'Regalo de NPC'
    if method_raw == 'static':
        if 'other-event-arceus-in-party' in cond_names:
            return 'Creación mística de Arceus a Nivel 1'
        return 'Encuentro interactivo / Trampa'
    if method_raw == 'pokemon-ranger':
        return 'Transferencia de Huevo desde Pokémon Ranger'
    if method_raw == 'squirt-bottle':
        return 'Interacción con Regadera'
    if method_raw == 'pokeflute':
        return 'Despertar con Flauta Pokémon'
    if method_raw == 'roaming-grass':
        return 'Pokémon errante (Hierba alta)'

    return method_raw.replace('-', ' ').capitalize()


def main():
    print("Iniciando compilación oficial de catálogos para Pokémon Oro HeartGold a 0 ms SQL...")

    with open(CACHE_DIR / "pokemon_493_species.json", "r", encoding="utf-8") as f:
        species_493 = json.load(f)

    with open(CACHE_DIR / "johto_updated_pokedex_256.json", "r", encoding="utf-8") as f:
        johto_256 = json.load(f)

    with open(CACHE_DIR / "encounters_heartgold.json", "r", encoding="utf-8") as f:
        encounters_hg = json.load(f)

    # Filtrar encuentros erróneos de la Zona Safari en la base de PokeAPI (ej: #17 Pidgeotto y #76 Golem)
    VALID_SAFARI_SPECIES_IDS = {
        16, 19, 20, 21, 22, 23, 24, 27, 28, 29, 30, 32, 33, 35, 39, 41, 42, 43, 44, 46, 47, 50, 
        54, 55, 60, 61, 63, 66, 67, 69, 70, 74, 75, 77, 79, 80, 81, 82, 83, 84, 85, 88, 89, 92, 
        93, 95, 96, 97, 98, 99, 100, 104, 105, 108, 109, 110, 111, 112, 113, 115, 118, 119, 122, 
        125, 126, 128, 129, 130, 131, 132, 147, 148, 161, 162, 179, 183, 187, 188, 189, 191, 194, 
        195, 198, 200, 202, 203, 213, 228, 229, 234, 235, 246, 263, 264, 270, 271, 273, 274, 283, 
        284, 285, 286, 288, 298, 299, 304, 305, 307, 308, 309, 310, 313, 314, 315, 324, 327, 328, 
        329, 331, 332, 335, 336, 337, 338, 339, 341, 353, 354, 355, 356, 358, 363, 364, 371, 372, 
        374, 375, 399, 403, 404, 406, 417, 418, 419, 433, 436, 437, 443, 447, 449, 451, 453, 455
    }
    for pid_str, elist in encounters_hg.items():
        if int(pid_str) not in VALID_SAFARI_SPECIES_IDS:
            encounters_hg[pid_str] = [e for e in elist if not e.get('area_raw', '').startswith('johto-safari-zone-')]

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
                surf_methods = [m for m in m_set if m == 'Surf']
                fish_methods = [m for m in m_set if 'Pesca' in m]
                other_methods = [m for m in m_set if m != 'Surf' and 'Pesca' not in m]

                if other_methods:
                    loc_list.append({
                        'area': a_name,
                        'method': ", ".join(sorted(other_methods))
                    })
                if surf_methods:
                    loc_list.append({
                        'area': a_name,
                        'method': 'Surf'
                    })
                if fish_methods:
                    order = {'caña vieja': 1, 'caña buena': 2, 'supercaña': 3}
                    clean_rods = []
                    for fm in fish_methods:
                        m_rod = re.search(r'\((.*?)\)', fm)
                        if m_rod:
                            clean_rods.append(m_rod.group(1).strip())
                        else:
                            clean_rods.append(fm)
                    clean_rods = list(dict.fromkeys(clean_rods))
                    clean_rods.sort(key=lambda x: order.get(x.lower(), 99))
                    if len(clean_rods) == 2:
                        fish_str = f"Pesca ({clean_rods[0]} y {clean_rods[1]})"
                    elif len(clean_rods) == 3:
                        fish_str = f"Pesca ({clean_rods[0]}, {clean_rods[1]} y {clean_rods[2]})"
                    else:
                        fish_str = f"Pesca ({', '.join(clean_rods)})"
                    loc_list.append({
                        'area': a_name,
                        'method': fish_str
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

            badge_label = 'Evolución'
            # Ajuste de evoluciones dependientes de Sinnoh ausentes en HGSS
            if nat_id == 462:
                summary = "Evoluciona de Magneton (al subir de nivel en un campo magnético del Monte Corona). Al no existir en Johto ni Kanto, requiere evolucionar en D/P/Pt y transferir a HeartGold."
                badge_label = 'Evolución (D/P/Pt)'
            elif nat_id == 476:
                summary = "Evoluciona de Nosepass (al subir de nivel en un campo magnético del Monte Corona). Al no existir en Johto ni Kanto, requiere evolucionar en D/P/Pt y transferir a HeartGold."
                badge_label = 'Evolución (D/P/Pt)'
            elif nat_id == 470:
                summary = "Evoluciona de Eevee (al subir de nivel cerca de la Roca Musgo). Al no existir en Johto ni Kanto, requiere evolucionar en D/P/Pt y transferir a HeartGold."
                badge_label = 'Evolución (D/P/Pt)'
            elif nat_id == 471:
                summary = "Evoluciona de Eevee (al subir de nivel cerca de la Roca Hielo). Al no existir en Johto ni Kanto, requiere evolucionar en D/P/Pt y transferir a HeartGold."
                badge_label = 'Evolución (D/P/Pt)'

            obt_info = {
                'type': 'evolution',
                'badge_label': badge_label,
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

            area_label = 'Intercambio con D/P/Pt' if nat_id > 386 else 'Parque Compi / Intercambio'
            locs = [{'area': area_label, 'method': f'Transferencia desde {origin}'}]
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

        # 3. Resolución universal del objeto evolutivo o incienso de crianza para la tarjeta y el modal
        item_slug_to_resolve = baby_incense_slug or (evo_info.get('item_slug') if evo_info else None) or obt_info.get('item_slug')
        if item_slug_to_resolve:
            from tracker.utils import resolve_evolution_stone
            evo_stone_obj = resolve_evolution_stone(item_slug=item_slug_to_resolve, game_slug="heartgold")
        else:
            evo_stone_obj = None

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
