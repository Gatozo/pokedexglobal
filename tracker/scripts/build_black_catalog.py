"""
Script para compilar los catálogos oficiales de Pokémon Negro:
- tracker/data/catalogs/black.json (Pokédex Regional de Teselia - 156 especies, #000 Victini a #155 Genesect)
- tracker/data/catalogs/black_national.json (Pokédex Nacional - 649 especies, #001 Bulbasaur a #649 Genesect)
Siguiendo rigurosamente la especificación guides/especificacion-pokemon-negro.md y la arquitectura maestro.
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

UNOVA_AREA_NAMES = {
    'abundant-shrine-area': 'Santuario Abundancia',
    'castelia-city-game-freak-hq-1f': 'Ciudad Porcelana (Sede de Game Freak)',
    'celestial-tower-2f': 'Torre de los Cielos (P2)',
    'celestial-tower-3f': 'Torre de los Cielos (P3)',
    'celestial-tower-4f': 'Torre de los Cielos (P4)',
    'celestial-tower-5f': 'Torre de los Cielos (Cima)',
    'challengers-cave-1f': 'Gruta Superación (P1)',
    'challengers-cave-b1f': 'Gruta Superación (Sótano B1)',
    'challengers-cave-b2f': 'Gruta Superación (Sótano B2)',
    'chargestone-cave-1f': 'Cueva Electrorroca (P1)',
    'chargestone-cave-b1f': 'Cueva Electrorroca (Sótano B1)',
    'chargestone-cave-b2f': 'Cueva Electrorroca (Sótano B2)',
    'cold-storage-area': 'Almacenes Frigoríficos',
    'desert-resort-area': 'Zona Desierto',
    'desert-resort-entrance': 'Zona Desierto (Entrada)',
    'dragonspiral-tower-1f': 'Torre Duodraco (P1)',
    'dragonspiral-tower-2f': 'Torre Duodraco (P2)',
    'dragonspiral-tower-7f': 'Torre Duodraco (Cima)',
    'dragonspiral-tower-entrance': 'Torre Duodraco (Entrada)',
    'dragonspiral-tower-outside': 'Torre Duodraco (Exterior)',
    'dreamyard-area': 'Solar de los Sueños',
    'dreamyard-b1f': 'Solar de los Sueños (Sótano)',
    'driftveil-city-area': 'Ciudad Fayenza',
    'driftveil-drawbridge-area': 'Puente Fayenza',
    'giant-chasm-area': 'Boquete Gigante (Exterior)',
    'giant-chasm-forest': 'Boquete Gigante (Bosque Interior)',
    'giant-chasm-forest-cave': 'Boquete Gigante (Cueva Central)',
    'giant-chasm-outside': 'Boquete Gigante (Entrada)',
    'guidance-chamber-area': 'Cueva Loza (Sala del Guía)',
    'icirrus-city-area': 'Ciudad Teja',
    'liberty-garden-lighthouse-basement': 'Isla Libertad (Sótano del Faro)',
    'lostlorn-forest-area': 'Bosque de los Perdidos',
    'marvelous-bridge-area': 'Puente Progreso',
    'mistralton-cave-area': 'Cueva Loza',
    'moor-of-icirrus-area': 'Pantano Teja',
    'nacrene-city-nacrene-museum': 'Museo de Ciudad Esmalte',
    'ns-castle-throne-room': 'Palacio de N (Sala del Trono)',
    'nuvema-town-area': 'Pueblo Arcilla',
    'p2-laboratory-area': 'Laboratorio P+P',
    'pinwheel-forest-inside': 'Bosque Azulejo (Interior)',
    'pinwheel-forest-outside': 'Bosque Azulejo (Exterior)',
    'pinwheel-forest-rumination-field': 'Bosque Azulejo (Claro Filosofía)',
    'relic-castle-a': 'Castillo Ancestral (P1)',
    'relic-castle-b': 'Castillo Ancestral (Sótano B1)',
    'relic-castle-c': 'Castillo Ancestral (Sótano B2-B4)',
    'relic-castle-d': 'Castillo Ancestral (Planta más profunda)',
    'striaton-city-area': 'Ciudad Gres',
    'trial-chamber-area': 'Calle Victoria (Cámara de Pruebas)',
    'twist-mountain-b1f-3f': 'Monte Tuerca',
    'undella-bay-area': 'Bahía Arenisca',
    'undella-town-area': 'Pueblo Arenisca',
    'unova-route-1-area': 'Ruta 1',
    'unova-route-2-area': 'Ruta 2',
    'unova-route-3-area': 'Ruta 3',
    'unova-route-4-area': 'Ruta 4',
    'unova-route-5-area': 'Ruta 5',
    'unova-route-6-area': 'Ruta 6',
    'unova-route-7-area': 'Ruta 7',
    'unova-route-8-area': 'Ruta 8',
    'unova-route-9-area': 'Ruta 9',
    'unova-route-10-area': 'Ruta 10',
    'unova-route-10-victory-road-gate': 'Ruta 10 (Puertas de las Medallas)',
    'unova-route-11-area': 'Ruta 11',
    'unova-route-12-area': 'Ruta 12',
    'unova-route-13-area': 'Ruta 13',
    'unova-route-14-area': 'Ruta 14',
    'unova-route-15-area': 'Ruta 15',
    'unova-route-16-area': 'Ruta 16',
    'unova-route-17-area': 'Ruta 17',
    'unova-route-18-area': 'Ruta 18',
    'unova-victory-road-outside': 'Calle Victoria (Ladera Exterior)',
    'unova-victory-road-1f-unknown-room': 'Calle Victoria (P1)',
    'unova-victory-road-4f-middle-room': 'Calle Victoria (P4)',
    'unova-victory-road-unknown-area-53': 'Calle Victoria (P2)',
    'unova-victory-road-unknown-area-54': 'Calle Victoria (P3)',
    'unova-victory-road-unknown-area-55': 'Calle Victoria (P4)',
    'unova-victory-road-unknown-area-57': 'Calle Victoria (P5)',
    'unova-victory-road-unknown-area-59': 'Calle Victoria (P6)',
    'unova-victory-road-unknown-area-60': 'Calle Victoria (P7)',
    'unova-victory-road-unknown-area-61': 'Calle Victoria (Cámara Oeste)',
    'unova-victory-road-unknown-area-62': 'Calle Victoria (Cámara Este)',
    'unova-victory-road-unknown-area-63': 'Calle Victoria (Túnel Inferior)',
    'unova-victory-road-unknown-area-64': 'Calle Victoria (Cima)',
    'unova-victory-road-unknown-area-65': 'Calle Victoria (Salida)',
    'unova-victory-road-unknown-area-66': 'Calle Victoria (Acceso Liga)',
    'village-bridge-area': 'Puente Villa',
    'wellspring-cave-area': 'Cueva Manantial',
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
    'regigigas', 'giratina', 'cresselia', 'phione', 'manaphy', 'darkrai',
    'shaymin', 'arceus',
    'victini', 'cobalion', 'terrakion', 'virizion', 'tornadus',
    'thundurus', 'reshiram', 'zekrom', 'landorus', 'kyurem',
    'keldeo', 'meloetta', 'genesect'
}

DAYCARE_LOCATION = {
    'area': 'Ruta 3 (Guardería Pokémon)',
    'method': 'Crianza de huevo'
}

SWARM_POKEMON_BLACK = {
    83: {'area': 'Ruta 1', 'desc': 'Manada diaria en la Ruta 1 tras obtener la Pokédex Nacional.'},
    360: {'area': 'Ruta 2', 'desc': 'Manada diaria en la Ruta 2 tras obtener la Pokédex Nacional.'},
    313: {'area': 'Ruta 3', 'desc': 'Manada diaria en la Ruta 3 tras obtener la Pokédex Nacional (Exclusivo de Pokémon Negro).'},
    449: {'area': 'Ruta 4', 'desc': 'Manada diaria en la Ruta 4 tras obtener la Pokédex Nacional.'},
    235: {'area': 'Ruta 5', 'desc': 'Manada diaria en la Ruta 5 tras obtener la Pokédex Nacional.'},
    311: {'area': 'Ruta 6', 'desc': 'Manada diaria en la Ruta 6 tras obtener la Pokédex Nacional (Exclusivo de Pokémon Negro).'},
    161: {'area': 'Ruta 7', 'desc': 'Manada diaria en la Ruta 7 tras obtener la Pokédex Nacional.'},
    453: {'area': 'Ruta 8', 'desc': 'Manada diaria en la Ruta 8 tras obtener la Pokédex Nacional.'},
    228: {'area': 'Ruta 9', 'desc': 'Manada diaria en la Ruta 9 tras obtener la Pokédex Nacional (Exclusivo de Pokémon Negro).'},
    236: {'area': 'Ruta 10', 'desc': 'Manada diaria en la Ruta 10 tras obtener la Pokédex Nacional.'},
    285: {'area': 'Ruta 11', 'desc': 'Manada diaria en la Ruta 11 tras obtener la Pokédex Nacional (Exclusivo de Pokémon Negro).'},
    84: {'area': 'Ruta 12', 'desc': 'Manada diaria en la Ruta 12 tras obtener la Pokédex Nacional.'},
    353: {'area': 'Ruta 13', 'desc': 'Manada diaria en la Ruta 13 tras obtener la Pokédex Nacional.'},
    193: {'area': 'Ruta 14', 'desc': 'Manada diaria en la Ruta 14 tras obtener la Pokédex Nacional.'},
    56: {'area': 'Ruta 15', 'desc': 'Manada diaria en la Ruta 15 tras obtener la Pokédex Nacional.'},
    204: {'area': 'Ruta 16', 'desc': 'Manada diaria en la Ruta 16 tras obtener la Pokédex Nacional.'},
    102: {'area': 'Ruta 18', 'desc': 'Manada diaria en la Ruta 18 tras obtener la Pokédex Nacional.'},
}

SPECIAL_OBTAINING = {
    # Iniciales de Teselia
    495: {
        'type': 'starter',
        'badge_label': 'Inicial',
        'badge_color': 'emerald',
        'summary': 'Elegir como regalo de la Profesora Encina en Pueblo Arcilla al comenzar tu aventura (también obtenible mediante crianza).',
        'locations': [
            {'area': 'Pueblo Arcilla (Regalo de Profesora Encina)', 'method': 'Elección de Inicial de Teselia'},
            DAYCARE_LOCATION
        ]
    },
    498: {
        'type': 'starter',
        'badge_label': 'Inicial',
        'badge_color': 'amber',
        'summary': 'Elegir como regalo de la Profesora Encina en Pueblo Arcilla al comenzar tu aventura (también obtenible mediante crianza).',
        'locations': [
            {'area': 'Pueblo Arcilla (Regalo de Profesora Encina)', 'method': 'Elección de Inicial de Teselia'},
            DAYCARE_LOCATION
        ]
    },
    501: {
        'type': 'starter',
        'badge_label': 'Inicial',
        'badge_color': 'sky',
        'summary': 'Elegir como regalo de la Profesora Encina en Pueblo Arcilla al comenzar tu aventura (también obtenible mediante crianza).',
        'locations': [
            {'area': 'Pueblo Arcilla (Regalo de Profesora Encina)', 'method': 'Elección de Inicial de Teselia'},
            DAYCARE_LOCATION
        ]
    },

    # Regalos y eventos especiales de Teselia
    511: {
        'type': 'gift',
        'badge_label': 'Regalo / Salvaje',
        'badge_color': 'emerald',
        'summary': 'Entregado por una chica en el Solar de los Sueños si tu inicial fue Oshawott. También aparece en hierba movediza del Bosque Azulejo y Bosque de los Perdidos (y mediante crianza).',
        'locations': [
            {'area': 'Solar de los Sueños', 'method': 'Regalo si elegiste a Oshawott'},
            {'area': 'Bosque Azulejo (Interior)', 'method': 'Hierba movediza'},
            {'area': 'Bosque de los Perdidos', 'method': 'Hierba movediza'},
            DAYCARE_LOCATION
        ]
    },
    513: {
        'type': 'gift',
        'badge_label': 'Regalo / Salvaje',
        'badge_color': 'amber',
        'summary': 'Entregado por una chica en el Solar de los Sueños si tu inicial fue Snivy. También aparece en hierba movediza del Bosque Azulejo y Bosque de los Perdidos (y mediante crianza).',
        'locations': [
            {'area': 'Solar de los Sueños', 'method': 'Regalo si elegiste a Snivy'},
            {'area': 'Bosque Azulejo (Interior)', 'method': 'Hierba movediza'},
            {'area': 'Bosque de los Perdidos', 'method': 'Hierba movediza'},
            DAYCARE_LOCATION
        ]
    },
    515: {
        'type': 'gift',
        'badge_label': 'Regalo / Salvaje',
        'badge_color': 'sky',
        'summary': 'Entregado por una chica en el Solar de los Sueños si tu inicial fue Tepig. También aparece en hierba movediza del Bosque Azulejo y Bosque de los Perdidos (y mediante crianza).',
        'locations': [
            {'area': 'Solar de los Sueños', 'method': 'Regalo si elegiste a Tepig'},
            {'area': 'Bosque Azulejo (Interior)', 'method': 'Hierba movediza'},
            {'area': 'Bosque de los Perdidos', 'method': 'Hierba movediza'},
            DAYCARE_LOCATION
        ]
    },
    129: {
        'type': 'gift',
        'badge_label': 'Regalo / Pesca',
        'badge_color': 'sky',
        'summary': 'Comprado por 500 ₽ al vendedor de Magikarp en el Puente Progreso. También pescando con Supercaña en sombra del agua en la Reserva Natural (y mediante crianza).',
        'locations': [
            {'area': 'Puente Progreso', 'method': 'Comprado por 500 ₽ al vendedor'},
            DAYCARE_LOCATION
        ]
    },
    446: {
        'type': 'trade_npc',
        'badge_label': 'Intercambio NPC',
        'badge_color': 'indigo',
        'summary': 'Obtenible en Pueblo Arenisca intercambiando un Cinccino con Cinco durante el verano (también mediante crianza de Snorlax con Incienso Lento).',
        'locations': [
            {'area': 'Pueblo Arenisca (Solo en verano)', 'method': 'Intercambio NPC por Cinccino'}
        ]
    },
    479: {
        'type': 'trade_npc',
        'badge_label': 'Intercambio NPC',
        'badge_color': 'amber',
        'summary': 'Obtenible en la caravana de la Ruta 15 intercambiando un Ditto con una entrenadora (sus formas alternas se activan en las cajas del Centro Comercial R9).',
        'locations': [
            {'area': 'Ruta 15 (Caravana)', 'method': 'Intercambio NPC por Ditto'}
        ]
    },
    548: {
        'type': 'trade_npc',
        'badge_label': 'Intercambio NPC',
        'badge_color': 'emerald',
        'summary': 'En Pokémon Negro, una chica en Ciudad Esmalte te cambia su Petilil por tu Cottonee salvaje, permitiendo obtener a Petilil y Lilligant en esta edición (también por crianza).',
        'locations': [
            {'area': 'Ciudad Esmalte', 'method': 'Intercambio NPC por Cottonee'},
            DAYCARE_LOCATION
        ]
    },
    550: {
        'type': 'wild',
        'badge_label': 'Salvaje / Forma',
        'badge_color': 'sky',
        'summary': 'Forma Raya Roja salvaje en lagos y rutas de Teselia surfeando. La Forma Raya Azul se obtiene por intercambio NPC en Ciudad Fayenza entregando un Minccino.',
        'locations': [
            {'area': 'Ruta 1', 'method': 'Surf / Pesca con Supercaña'},
            {'area': 'Ruta 3', 'method': 'Surf / Pesca con Supercaña'},
            {'area': 'Ciudad Fayenza', 'method': 'Intercambio NPC (Forma Raya Azul por Minccino)'},
            DAYCARE_LOCATION
        ]
    },
    555: {
        'type': 'wild',
        'badge_label': 'Especial / Salvaje',
        'badge_color': 'amber',
        'summary': 'Evoluciona de Darumaka al Nv. 35. Además, 5 estatuas de Darmanitan en la entrada del Castillo Ancestral despiertan entregando un Furiazafrán, poseyendo la habilidad Modo Daruma.',
        'locations': [
            {'area': 'Castillo Ancestral (Entrada)', 'method': 'Estatuas que despiertan con Furiazafrán (Modo Daruma)'},
            {'area': 'Ruta 4', 'method': 'Evolución de Darumaka (Nv. 35)'}
        ]
    },
    518: {
        'type': 'wild',
        'badge_label': 'Encuentro Fijo / Piedra',
        'badge_color': 'purple',
        'summary': 'Evoluciona de Munna usando Piedra Lunar. Además, aparece un Musharna fijo todos los viernes en el sótano del Solar de los Sueños con su habilidad oculta Telepatía.',
        'locations': [
            {'area': 'Solar de los Sueños (Sótano)', 'method': 'Encuentro fijo los viernes (con Telepatía)'},
            {'area': 'Solar de los Sueños', 'method': 'Hierba movediza'}
        ]
    },
    570: {
        'type': 'gift',
        'badge_label': 'Orbe Reluciente',
        'badge_color': 'purple',
        'summary': 'Entregado en un edificio de Ciudad Porcelana al llevar en el equipo al Celebi transferido mediante el Orbe Reluciente (también por crianza).',
        'locations': [
            {'area': 'Ciudad Porcelana', 'method': 'Evento con Celebi vía Orbe Reluciente'},
            DAYCARE_LOCATION
        ]
    },
    571: {
        'type': 'wild',
        'badge_label': 'Orbe Reluciente',
        'badge_color': 'purple',
        'summary': 'Evoluciona de Zorua al Nv. 30. Además, aparece en el Bosque de los Perdidos como una mujer que te desafía si llevas a Raikou, Entei o Suicune variocolor del evento.',
        'locations': [
            {'area': 'Bosque de los Perdidos', 'method': 'Encuentro especial con Bestia Variocolor de evento'},
            {'area': 'Ciudad Porcelana', 'method': 'Evolución de Zorua (Nv. 30)'}
        ]
    },
    636: {
        'type': 'gift',
        'badge_label': 'Huevo Regalo',
        'badge_color': 'amber',
        'summary': 'Huevo entregado por un Entrenador Guay en una cabaña de la Ruta 18 (también obtenible mediante crianza).',
        'locations': [
            {'area': 'Ruta 18 (Cabaña)', 'method': 'Huevo entregado por Entrenador Guay'},
            DAYCARE_LOCATION
        ]
    },
    637: {
        'type': 'wild',
        'badge_label': 'Encuentro Fijo / Nivel',
        'badge_color': 'amber',
        'summary': 'Evoluciona de Larvesta al Nv. 59. Además, aparece como encuentro fijo a Nivel 70 en la cámara más profunda del Castillo Ancestral en el post-game.',
        'locations': [
            {'area': 'Castillo Ancestral (Planta más profunda)', 'method': 'Encuentro fijo a Nivel 70 en el post-game'},
            {'area': 'Ruta 18', 'method': 'Evolución de Larvesta (Nv. 59)'}
        ]
    },

    # Fósiles de Teselia
    564: {
        'type': 'fossil',
        'badge_label': 'Fósil Tapa',
        'badge_color': 'blue',
        'summary': 'Revivir del Fósil Tapa (elegido de una mochilera en el Castillo Ancestral) en el Museo de Ciudad Esmalte (también por crianza).',
        'locations': [
            {'area': 'Castillo Ancestral', 'method': 'Elección de Fósil Tapa'},
            {'area': 'Museo de Ciudad Esmalte', 'method': 'Restauración de Fósil Tapa'},
            DAYCARE_LOCATION
        ]
    },
    566: {
        'type': 'fossil',
        'badge_label': 'Fósil Pluma',
        'badge_color': 'amber',
        'summary': 'Revivir del Fósil Pluma (elegido de una mochilera en el Castillo Ancestral) en el Museo de Ciudad Esmalte (también por crianza).',
        'locations': [
            {'area': 'Castillo Ancestral', 'method': 'Elección de Fósil Pluma'},
            {'area': 'Museo de Ciudad Esmalte', 'method': 'Restauración de Fósil Pluma'},
            DAYCARE_LOCATION
        ]
    },

    # Fósiles clásicos en Monte Tuerca
    138: {
        'type': 'fossil',
        'badge_label': 'Fósil Hélix',
        'badge_color': 'blue',
        'summary': 'Restaurar en el Museo de Ciudad Esmalte tras recibir el Fósil Hélix de un obrero en el Monte Tuerca en el post-game (también por crianza).',
        'locations': [
            {'area': 'Monte Tuerca', 'method': 'Fósil Hélix diario entregado por obrero'},
            {'area': 'Museo de Ciudad Esmalte', 'method': 'Restauración de Fósil Hélix'},
            DAYCARE_LOCATION
        ]
    },
    140: {
        'type': 'fossil',
        'badge_label': 'Fósil Domo',
        'badge_color': 'blue',
        'summary': 'Restaurar en el Museo de Ciudad Esmalte tras recibir el Fósil Domo de un obrero en el Monte Tuerca en el post-game (también por crianza).',
        'locations': [
            {'area': 'Monte Tuerca', 'method': 'Fósil Domo diario entregado por obrero'},
            {'area': 'Museo de Ciudad Esmalte', 'method': 'Restauración de Fósil Domo'},
            DAYCARE_LOCATION
        ]
    },
    142: {
        'type': 'fossil',
        'badge_label': 'Ámbar Viejo',
        'badge_color': 'amber',
        'summary': 'Restaurar en el Museo de Ciudad Esmalte tras recibir el Ámbar Viejo de un obrero en el Monte Tuerca en el post-game (también por crianza).',
        'locations': [
            {'area': 'Monte Tuerca', 'method': 'Ámbar Viejo diario entregado por obrero'},
            {'area': 'Museo de Ciudad Esmalte', 'method': 'Restauración de Ámbar Viejo'},
            DAYCARE_LOCATION
        ]
    },
    345: {
        'type': 'fossil',
        'badge_label': 'Fósil Raíz',
        'badge_color': 'emerald',
        'summary': 'Restaurar en el Museo de Ciudad Esmalte tras recibir el Fósil Raíz de un obrero en el Monte Tuerca en el post-game (también por crianza).',
        'locations': [
            {'area': 'Monte Tuerca', 'method': 'Fósil Raíz diario entregado por obrero'},
            {'area': 'Museo de Ciudad Esmalte', 'method': 'Restauración de Fósil Raíz'},
            DAYCARE_LOCATION
        ]
    },
    347: {
        'type': 'fossil',
        'badge_label': 'Fósil Garra',
        'badge_color': 'amber',
        'summary': 'Restaurar en el Museo de Ciudad Esmalte tras recibir el Fósil Garra de un obrero en el Monte Tuerca en el post-game (también por crianza).',
        'locations': [
            {'area': 'Monte Tuerca', 'method': 'Fósil Garra diario entregado por obrero'},
            {'area': 'Museo de Ciudad Esmalte', 'method': 'Restauración de Fósil Garra'},
            DAYCARE_LOCATION
        ]
    },
    408: {
        'type': 'fossil',
        'badge_label': 'Fósil Cráneo',
        'badge_color': 'blue',
        'summary': 'Restaurar en el Museo de Ciudad Esmalte tras recibir el Fósil Cráneo de un obrero en el Monte Tuerca en el post-game (también por crianza).',
        'locations': [
            {'area': 'Monte Tuerca', 'method': 'Fósil Cráneo diario entregado por obrero'},
            {'area': 'Museo de Ciudad Esmalte', 'method': 'Restauración de Fósil Cráneo'},
            DAYCARE_LOCATION
        ]
    },
    410: {
        'type': 'fossil',
        'badge_label': 'Fósil Coraza',
        'badge_color': 'zinc',
        'summary': 'Restaurar en el Museo de Ciudad Esmalte tras recibir el Fósil Coraza de un obrero en el Monte Tuerca en el post-game (también por crianza).',
        'locations': [
            {'area': 'Monte Tuerca', 'method': 'Fósil Coraza diario entregado por obrero'},
            {'area': 'Museo de Ciudad Esmalte', 'method': 'Restauración de Fósil Coraza'},
            DAYCARE_LOCATION
        ]
    },

    # Legendarios y singulares de Teselia en Pokémon Negro
    494: {
        'type': 'mythical',
        'badge_label': 'Evento Singular',
        'badge_color': 'amber',
        'summary': 'Encuentro a Nv. 15 en el sótano del faro de Isla Libertad, accesible en barco desde Ciudad Porcelana con el Ticket Libertad de evento.',
        'locations': [
            {'area': 'Isla Libertad (Sótano del Faro)', 'method': 'Evento con Ticket Libertad (Nv. 15)'}
        ]
    },
    638: {
        'type': 'legendary',
        'badge_label': 'Legendario',
        'badge_color': 'teal',
        'summary': 'Encuentro fijo a Nv. 42 en la Sala del Guía dentro de la Cueva Loza (requiere Surf y Fuerza). Desbloquea a Terrakion y Virizion.',
        'locations': [
            {'area': 'Cueva Loza (Sala del Guía)', 'method': 'Encuentro fijo a Nivel 42'}
        ]
    },
    639: {
        'type': 'legendary',
        'badge_label': 'Legendario',
        'badge_color': 'amber',
        'summary': 'Encuentro fijo a Nv. 42 en la Cámara de Pruebas de la Calle Victoria, tras haber interactuado con Cobalion en Cueva Loza.',
        'locations': [
            {'area': 'Calle Victoria (Cámara de Pruebas)', 'method': 'Encuentro fijo a Nivel 42'}
        ]
    },
    640: {
        'type': 'legendary',
        'badge_label': 'Legendario',
        'badge_color': 'emerald',
        'summary': 'Encuentro fijo a Nv. 42 en el Claro Filosofía del Bosque Azulejo, tras haber interactuado con Cobalion en Cueva Loza.',
        'locations': [
            {'area': 'Bosque Azulejo (Claro Filosofía)', 'method': 'Encuentro fijo a Nivel 42'}
        ]
    },
    641: {
        'type': 'legendary',
        'badge_label': 'Exclusivo Negro',
        'badge_color': 'emerald',
        'summary': 'Pokémon legendario errante a Nv. 40 por las rutas de Teselia tras el evento de la tormenta en la Ruta 7. Exclusivo de Pokémon Negro.',
        'locations': [
            {'area': 'Rutas de Teselia', 'method': 'Pokémon errante (Nv. 40) tras evento en Ruta 7'}
        ]
    },
    643: {
        'type': 'legendary',
        'badge_label': 'Exclusivo Negro',
        'badge_color': 'slate',
        'summary': 'Captura obligatoria a Nv. 50 en el Palacio de N durante el clímax de la historia principal (o en la Torre Duodraco si las cajas estaban llenas).',
        'locations': [
            {'area': 'Palacio de N (Sala del Trono)', 'method': 'Captura en la historia principal (Nv. 50)'},
            {'area': 'Torre Duodraco (Cima)', 'method': 'Reaparición si el equipo y cajas estaban llenos'}
        ]
    },
    645: {
        'type': 'legendary',
        'badge_label': 'Legendario',
        'badge_color': 'amber',
        'summary': 'Encuentro fijo a Nv. 70 en el Santuario Abundancia llevando en el equipo a Tornadus y a Thundurus (transferido de Pokémon Blanco).',
        'locations': [
            {'area': 'Santuario Abundancia', 'method': 'Encuentro fijo a Nv. 70 llevando a Tornadus y Thundurus'}
        ]
    },
    646: {
        'type': 'legendary',
        'badge_label': 'Legendario',
        'badge_color': 'cyan',
        'summary': 'Encuentro fijo a Nv. 75 en la cueva central del Boquete Gigante en el post-game de Teselia.',
        'locations': [
            {'area': 'Boquete Gigante (Cueva Central)', 'method': 'Encuentro fijo a Nivel 75'}
        ]
    },
    647: {
        'type': 'mythical',
        'badge_label': 'Evento Singular',
        'badge_color': 'sky',
        'summary': 'Pokémon singular de evento de 5.ª Generación. En el Claro Filosofía del Bosque Azulejo aprende Espada Santa junto a los Espadachines Místicos.',
        'locations': [
            {'area': 'Evento Oficial de Distribución', 'method': 'Tarjeta Misteriosa Wi-Fi'}
        ]
    },
    648: {
        'type': 'mythical',
        'badge_label': 'Evento Singular',
        'badge_color': 'pink',
        'summary': 'Pokémon singular de evento de 5.ª Generación. En el bar de Ciudad Porcelana un guitarrista le enseña Canto Arcaico, permitiéndole cambiar a Forma Danza.',
        'locations': [
            {'area': 'Evento Oficial de Distribución', 'method': 'Tarjeta Misteriosa Wi-Fi'}
        ]
    },
    649: {
        'type': 'mythical',
        'badge_label': 'Evento Singular',
        'badge_color': 'purple',
        'summary': 'Pokémon singular de evento de 5.ª Generación. En el Laboratorio P+P de la Ruta 18 un científico entrega los cartuchos Piro, Hidro, Fulgor y Crio.',
        'locations': [
            {'area': 'Evento Oficial de Distribución', 'method': 'Tarjeta Misteriosa Wi-Fi'}
        ]
    },
}


def format_wild_method(method_raw: str, conditions: list, area_clean: str) -> str:
    if 'swarm-yes' in conditions:
        return 'Manada diaria'
    if method_raw == 'dark-grass':
        return 'Hierba oscura (Combates dobles)'
    if method_raw == 'grass-spots':
        return 'Hierba movediza'
    if method_raw == 'cave-spots':
        return 'Nube de polvo'
    if method_raw == 'bridge-spots':
        return 'Sombra en el puente'
    if method_raw == 'surf':
        return 'Surf'
    if method_raw == 'surf-spots':
        return 'Surf en sombra del agua'
    if method_raw == 'super-rod':
        return 'Supercaña'
    if method_raw == 'super-rod-spots':
        return 'Supercaña en sombra del agua'
    if method_raw == 'walk':
        if any(c in area_clean.lower() for c in ['cueva', 'monte', 'torre', 'sótano', 'gruta', 'boquete', 'castillo', 'palacio', 'cámara', 'sala']):
            return 'Caminando'
        return 'Hierba alta'
    return 'Salvaje'


def main():
    print("Iniciando compilación oficial de catálogos para Pokémon Negro...")

    with open(CACHE_DIR / "pokemon_649_species.json", "r", encoding="utf-8") as f:
        species_649 = json.load(f)

    with open(CACHE_DIR / "encounters_black.json", "r", encoding="utf-8") as f:
        encounters_black = json.load(f)

    with open(CACHE_DIR / "wikidex_black_descriptions.json", "r", encoding="utf-8") as f:
        descriptions = json.load(f)

    with open(CACHE_DIR / "unova_pokedex_156.json", "r", encoding="utf-8") as f:
        unova_156 = json.load(f)

    with open(CACHE_DIR / "gen5_evolutions.json", "r", encoding="utf-8") as f:
        gen5_evos = json.load(f)

    with open(BASE_DIR / "tracker" / "data" / "evolution_stones.json", "r", encoding="utf-8") as f:
        evolution_stones = json.load(f)

    from tracker.exclusives import VERSION_TRANSFERS_CATALOG, VERSION_TRANSFERS_META, VERSION_EXCLUSIVES_CATALOG
    black_transfers = set(VERSION_TRANSFERS_CATALOG.get("black", []))
    black_origins = VERSION_TRANSFERS_META.get("black", {}).get("origins", {})
    white_exclusives = set(VERSION_EXCLUSIVES_CATALOG.get("white", []))

    def build_entry(nat_id: int, entry_num: int, is_regional: bool, unique_id: int, display_number_override: str = None):
        sp = species_649[str(nat_id)]
        flavor = descriptions.get(str(nat_id), "")
        sp_name = sp['name'].lower()
        egg_groups = sp.get('egg_groups', [])
        evo_info = gen5_evos.get(str(nat_id))

        is_baby = sp_name in BABY_NAMES
        is_incense_parent = sp_name in INCENSE_PARENTS_THAT_HATCH
        is_evolution = (evo_info is not None) and not is_incense_parent

        # Regla Universal de Crianza
        if sp_name in NON_BREEDABLE_NAMES or nat_id in {494, 638, 639, 640, 641, 642, 643, 644, 645, 646, 647, 648, 649}:
            is_hatchable = False
        elif ('no-eggs' in egg_groups) and not is_baby:
            is_hatchable = False
        elif is_baby or is_incense_parent:
            is_hatchable = True
        elif is_evolution:
            is_hatchable = False
        else:
            is_hatchable = True

        raw_encs = encounters_black.get(str(nat_id), [])
        evo_stone_obj = None

        if nat_id in SPECIAL_OBTAINING:
            obt_info = json.loads(json.dumps(SPECIAL_OBTAINING[nat_id]))
        elif raw_encs:
            # Procesar encuentros salvajes agrupados por área limpia
            area_methods = {}
            for e in raw_encs:
                area_key = e.get('area_raw', '')
                if 'team-flare' in area_key:
                    continue
                clean_area = UNOVA_AREA_NAMES.get(area_key, area_key.replace('-', ' ').title())
                meth_desc = format_wild_method(e.get('method_raw', 'walk'), e.get('conditions', []), clean_area)
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

            if nat_id in SWARM_POKEMON_BLACK:
                sw_info = SWARM_POKEMON_BLACK[nat_id]
                summary = f"{sw_info['desc']} (también obtenible mediante crianza)." if is_hatchable else sw_info['desc']
            elif num_zones == 1:
                summary = f"Salvaje en {zone_names[0]}."
            elif num_zones == 2:
                summary = f"Salvaje en {zone_names[0]} y {zone_names[1]}."
            elif num_zones <= 4:
                summary = f"Salvaje en {', '.join(zone_names[:-1])} y {zone_names[-1]}."
            else:
                summary = f"Salvaje en múltiples zonas de Teselia, incluyendo {zone_names[0]}, {zone_names[1]} y {zone_names[2]}."

            if is_hatchable and nat_id not in SWARM_POKEMON_BLACK:
                summary += " También obtenible mediante crianza en la Guardería de la Ruta 3."

            obt_info = {
                'type': 'wild',
                'badge_label': 'Salvaje',
                'badge_color': 'emerald',
                'summary': summary,
                'locations': loc_list
            }
        elif is_evolution and evo_info:
            from_name = evo_info.get('from_name', '')
            cond = evo_info.get('condition', '')
            summary = f"Evoluciona de {from_name} ({cond})."
            item_slug = evo_info.get('item_slug')
            loc_list = [{'area': 'Evolución', 'method': summary}]
            if is_hatchable:
                loc_list.append(DAYCARE_LOCATION)
            obt_info = {
                'type': 'evolution',
                'badge_label': 'Evolución',
                'badge_color': 'purple',
                'summary': summary,
                'locations': loc_list,
                'item_slug': item_slug,
                'evolution_info': {
                    'from': from_name,
                    'text': evo_info.get('text', summary),
                    'trigger': evo_info.get('trigger', 'level-up'),
                    'condition': cond,
                    'item_slug': item_slug,
                }
            }
        elif nat_id in white_exclusives:
            summary = "Inaccesible en estado salvaje en Pokémon Negro. Exclusivo de Pokémon Blanco (requiere intercambio o conexión Entralink con el Bosque Blanco)."
            loc_list = [{'area': 'Intercambio con Pokémon Blanco', 'method': 'Exclusivo de versión'}]
            if is_hatchable:
                loc_list.append(DAYCARE_LOCATION)
            obt_info = {
                'type': 'transfer',
                'badge_label': 'Edición Blanco',
                'badge_color': 'sky',
                'summary': summary,
                'locations': loc_list
            }
        elif nat_id in black_transfers:
            origin_desc = black_origins.get(nat_id, "Poké Transfer (Ruta 15)")
            summary = f"Inaccesible en estado salvaje en Teselia. Reclutar mediante {origin_desc} desde cartuchos de 4.ª Generación."
            loc_list = [{'area': 'Laboratorio Transfer (Ruta 15)', 'method': f"{origin_desc}"}]
            if is_hatchable:
                loc_list.append(DAYCARE_LOCATION)
            obt_info = {
                'type': 'transfer',
                'badge_label': 'Poké Transfer',
                'badge_color': 'amber',
                'summary': summary,
                'locations': loc_list
            }
        else:
            summary = "Obtención mediante crianza o evento especial en Teselia."
            loc_list = [DAYCARE_LOCATION] if is_hatchable else [{'area': 'Teselia', 'method': 'Especial'}]
            obt_info = {
                'type': 'other',
                'badge_label': 'Crianza',
                'badge_color': 'zinc',
                'summary': summary,
                'locations': loc_list
            }

        # Conservar metadatos de evolución universalmente para cualquier especie que evolucione de otra
        if evo_info and 'evolution_info' not in obt_info:
            obt_info['evolution_info'] = {
                'from': evo_info.get('from_name'),
                'text': evo_info.get('text', ''),
                'trigger': evo_info.get('trigger', 'level-up'),
                'condition': evo_info.get('condition', ''),
                'item_slug': evo_info.get('item_slug'),
            }

        # Inciensos de crianza si aplica
        baby_incense_slug = get_incense_for_baby(sp_name)
        new_locations = []
        has_daycare = False
        for loc in obt_info.get('locations', []):
            if 'Guardería' in loc.get('area', ''):
                has_daycare = True
                if baby_incense_slug:
                    incense_name = evolution_stones.get(baby_incense_slug, {}).get('name_es', 'Incienso')
                    new_locations.append({
                        'area': 'Ruta 3 (Guardería Pokémon)',
                        'method': f"Crianza con {incense_name}"
                    })
                else:
                    new_locations.append({'area': 'Ruta 3 (Guardería Pokémon)', 'method': loc.get('method', 'Crianza de huevo')})
            else:
                new_locations.append({'area': loc.get('area', ''), 'method': loc.get('method', '')})

        if is_hatchable and not has_daycare:
            if baby_incense_slug:
                incense_name = evolution_stones.get(baby_incense_slug, {}).get('name_es', 'Incienso')
                new_locations.append({
                    'area': 'Ruta 3 (Guardería Pokémon)',
                    'method': f"Crianza con {incense_name}"
                })
            else:
                new_locations.append({
                    'area': 'Ruta 3 (Guardería Pokémon)',
                    'method': 'Crianza de huevo'
                })

        obt_info['locations'] = new_locations

        item_slug_to_resolve = baby_incense_slug or (evo_info.get('item_slug') if evo_info else None) or obt_info.get('item_slug')
        if item_slug_to_resolve:
            evo_stone_obj = resolve_evolution_stone(item_slug=item_slug_to_resolve, game_slug="black")
        else:
            evo_stone_obj = None

        p_type = sp['primary_type']
        s_type = sp['secondary_type']

        # Formato de display_number
        if display_number_override:
            disp_num = display_number_override
        else:
            disp_num = f"{entry_num:03d}"

        entry = {
            "id": unique_id,
            "entry_number": entry_num,
            "display_number": disp_num,
            "game_slug": "black",
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
            "game_sprite_url": f"/media/pokemon/sprites/black/{nat_id}.png",
            "game_sprite_shiny_url": f"/media/pokemon/sprites/black_shiny/{nat_id}.png",
            "game_sprite_back_url": f"/media/pokemon/sprites/black/back/{nat_id}.png",
            "game_sprite_shiny_back_url": f"/media/pokemon/sprites/black_shiny/back/{nat_id}.png",
            "modern_sprite_shiny_url": f"/media/pokemon/artwork/shiny/{nat_id}.png",
            "modal_retro_sprite_url": f"/media/pokemon/sprites/black_animated/{nat_id}.gif",
            "modal_retro_sprite_shiny_url": f"/media/pokemon/sprites/black_animated_shiny/{nat_id}.gif",
            "modal_retro_sprite_back_url": f"/media/pokemon/sprites/black_animated/back/{nat_id}.gif",
            "modal_retro_sprite_shiny_back_url": f"/media/pokemon/sprites/black_animated_shiny/back/{nat_id}.gif",
            "pc_icon_url": f"/media/pokemon/icons/gen5/{nat_id}.png",
            "cry_url": f"/media/pokemon/cries/legacy/{nat_id}.ogg",
            "flavor_text": flavor,
            "obtaining_info": obt_info,
            "evolution_stone": evo_stone_obj,
            "game_data": {
                "generation": 5,
                "game_slug": "black",
                "game_name": "Pokémon Negro",
                "is_regional": is_regional
            }
        }
        return entry

    # 1. Compilar Pokédex Regional de Teselia (black.json - 156 Pokémon)
    # Índice 0: Victini (#000 Teselia / #494 Nacional, id: 8000, entry_number: 494, display_number: "000")
    # Índices 1..155: Snivy (#001) a Genesect (#155), id: 8001..8155, entry_number: 1..155, display_number: "001".."155"
    print("Compilando Pokédex Regional de Teselia (156 entradas)...")
    black_regional_catalog = []

    # Entrada 0: Victini
    victini_nat = int(unova_156.get("0", 494))
    victini_entry = build_entry(
        nat_id=victini_nat,
        entry_num=494,
        is_regional=True,
        unique_id=8000,
        display_number_override="000"
    )
    black_regional_catalog.append(victini_entry)

    # Entradas 1..155
    for reg_num in range(1, 156):
        nat_id = int(unova_156[str(reg_num)])
        unique_id = 8000 + reg_num
        disp_override = f"{reg_num:03d}"
        black_regional_catalog.append(build_entry(
            nat_id=nat_id,
            entry_num=reg_num,
            is_regional=True,
            unique_id=unique_id,
            display_number_override=disp_override
        ))

    regional_file = CATALOGS_DIR / "black.json"
    with open(regional_file, "w", encoding="utf-8") as f:
        json.dump(black_regional_catalog, f, ensure_ascii=False, indent=2)
    print(f"[OK] Guardado {regional_file} con {len(black_regional_catalog)} entradas.")

    # 2. Compilar Pokédex Nacional de Teselia (black_national.json - 649 Pokémon)
    print("Compilando Pokédex Nacional de Pokémon Negro (649 entradas)...")
    black_national_catalog = []
    for nat_num in range(1, 650):
        unique_id = 8200 + nat_num
        black_national_catalog.append(build_entry(
            nat_id=nat_num,
            entry_num=nat_num,
            is_regional=False,
            unique_id=unique_id,
            display_number_override=f"{nat_num:03d}"
        ))

    national_file = CATALOGS_DIR / "black_national.json"
    with open(national_file, "w", encoding="utf-8") as f:
        json.dump(black_national_catalog, f, ensure_ascii=False, indent=2)
    print(f"[OK] Guardado {national_file} con {len(black_national_catalog)} entradas.")


if __name__ == "__main__":
    main()
