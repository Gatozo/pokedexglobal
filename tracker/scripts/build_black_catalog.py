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
    'giant-chasm-area': 'Boquete Gigante (Cueva de Entrada)',
    'giant-chasm-forest': 'Boquete Gigante (Bosque Interior)',
    'giant-chasm-forest-cave': 'Boquete Gigante (Cueva Central)',
    'giant-chasm-outside': 'Boquete Gigante (Exterior)',
    'guidance-chamber-area': 'Cueva Loza (Estancia Orientación)',
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
    'unova-route-10-victory-road-gate': 'Ruta 10 (Control de Medallas)',
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
    'unova-victory-road-unknown-area-53': 'Calle Victoria (P3)',
    'unova-victory-road-unknown-area-54': 'Calle Victoria (P2)',
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
        'badge_label': 'Regalo',
        'badge_color': 'sky',
        'summary': 'Comprado por 500 ₽ al vendedor de Magikarp en el Puente Progreso (también obtenible mediante crianza).',
        'locations': [
            {'area': 'Puente Progreso', 'method': 'Comprado por 500 ₽ al vendedor'},
            DAYCARE_LOCATION
        ]
    },
    446: {
        'type': 'trade_npc',
        'badge_label': 'Intercambio NPC',
        'badge_color': 'indigo',
        'summary': 'Obtenible en Pueblo Arenisca intercambiando un Cinccino con Ander durante el verano (mote: Tripón); también mediante crianza de Snorlax equipado con Incienso Lento.',
        'locations': [
            {'area': 'Pueblo Arenisca (Solo en verano)', 'method': 'Intercambio NPC (mote: Tripón) por Cinccino'}
        ]
    },
    479: {
        'type': 'trade_npc',
        'badge_label': 'Intercambio NPC',
        'badge_color': 'amber',
        'summary': 'Obtenible en la caravana de la Ruta 15 intercambiando un Ditto con una entrenadora (mote: Tecno). Sus formas alternas se activan en las cajas del almacén de la planta baja del Centro Comercial R9.',
        'locations': [
            {'area': 'Ruta 15 (Caravana)', 'method': 'Intercambio NPC (mote: Tecno) por Ditto'}
        ]
    },
    548: {
        'type': 'trade_npc',
        'badge_label': 'Intercambio NPC',
        'badge_color': 'emerald',
        'summary': 'En Pokémon Negro, una chica en Ciudad Esmalte te cambia su Petilil (mote: Florina) por tu Cottonee salvaje, permitiendo obtener a Petilil y Lilligant en esta edición (también por crianza).',
        'locations': [
            {'area': 'Ciudad Esmalte', 'method': 'Intercambio NPC (mote: Florina) por Cottonee'},
            DAYCARE_LOCATION
        ]
    },
    550: {
        'type': 'wild',
        'badge_label': 'Salvaje / Forma',
        'badge_color': 'sky',
        'summary': 'Forma Raya Roja salvaje de forma común surfeando y pescando por toda Teselia (la Forma Raya Azul aparece rara vez en sombras del agua). Además, puedes recibir un Basculin Forma Raya Roja (mote: Mordiscos) por intercambio NPC en Ciudad Fayenza entregando un Minccino (y también por crianza).',
        'locations': [
            {'area': 'Ciudad Fayenza', 'method': 'Intercambio NPC (Forma Raya Roja, mote: Mordiscos) por Minccino'},
            DAYCARE_LOCATION
        ]
    },
    555: {
        'type': 'wild',
        'badge_label': 'Especial / Salvaje',
        'badge_color': 'amber',
        'summary': 'Evoluciona de Darumaka al Nv. 35. Además, 5 estatuas de Darmanitan en la entrada del Castillo Ancestral despiertan entregando un Caramelo Furia, poseyendo la habilidad Modo Daruma.',
        'locations': [
            {'area': 'Castillo Ancestral (Entrada)', 'method': 'Estatuas que despiertan con Caramelo Furia (Modo Daruma)'}
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
        'badge_label': 'Trasladador PKMN',
        'badge_color': 'purple',
        'summary': 'No aparece salvaje en Pokémon Negro. Solo se obtiene a Nv. 10 en la sede de Game Freak en Ciudad Porcelana al llevar en el equipo al Celebi de evento transferido desde 4.ª Generación mediante el Trasladador PKMN (o por intercambio / crianza a partir de otro Zorua o Zoroark).',
        'locations': [
            {'area': 'Ciudad Porcelana (Sede de Game Freak)', 'method': 'Evento con Celebi vía Trasladador PKMN (Nv. 10)'},
            DAYCARE_LOCATION
        ]
    },
    571: {
        'type': 'event',
        'badge_label': 'Trasladador PKMN',
        'badge_color': 'purple',
        'summary': 'Evoluciona de Zorua al Nv. 30. En Pokémon Negro también aparece como encuentro único a Nv. 25 en la caravana del Bosque de los Perdidos si llevas en el equipo a Raikou, Entei o Suicune variocolor de evento transferidos desde 4.ª Generación vía Trasladador PKMN.',
        'locations': [
            {'area': 'Bosque de los Perdidos', 'method': 'Encuentro especial a Nv. 25 con Bestia Variocolor vía Trasladador PKMN'}
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
            {'area': 'Castillo Ancestral (Planta más profunda)', 'method': 'Encuentro fijo a Nivel 70 en el post-game'}
        ]
    },

    # Fósiles de Teselia (elección única por partida)
    564: {
        'type': 'fossil',
        'badge_label': 'Fósil Tapa',
        'badge_color': 'blue',
        'summary': 'Revivir en el Museo de Ciudad Esmalte el Fósil Tapa elegido de una mochilera en el Castillo Ancestral (elección única frente al Fósil Pluma por partida; también obtenible por crianza).',
        'locations': [
            {'area': 'Castillo Ancestral (P1)', 'method': 'Elección única de Fósil Tapa (Mochilera)'},
            {'area': 'Museo de Ciudad Esmalte', 'method': 'Restauración de Fósil Tapa'},
            DAYCARE_LOCATION
        ]
    },
    566: {
        'type': 'fossil',
        'badge_label': 'Fósil Pluma',
        'badge_color': 'amber',
        'summary': 'Revivir en el Museo de Ciudad Esmalte el Fósil Pluma elegido de una mochilera en el Castillo Ancestral (elección única frente al Fósil Tapa por partida; también obtenible por crianza).',
        'locations': [
            {'area': 'Castillo Ancestral (P1)', 'method': 'Elección única de Fósil Pluma (Mochilera)'},
            {'area': 'Museo de Ciudad Esmalte', 'method': 'Restauración de Fósil Pluma'},
            DAYCARE_LOCATION
        ]
    },

    # Fósiles clásicos en Monte Tuerca (post-game tras obtener la Pokédex Nacional)
    138: {
        'type': 'fossil',
        'badge_label': 'Fósil Hélix',
        'badge_color': 'blue',
        'summary': 'Restaurar en el Museo de Ciudad Esmalte tras recibir el Fósil Hélix al azar de un obrero en el Monte Tuerca (solo tras superar la Liga Pokémon y obtener la Pokédex Nacional; también por crianza).',
        'locations': [
            {'area': 'Monte Tuerca', 'method': 'Fósil aleatorio diario entregado por obrero (Post-game / Pokédex Nacional)'},
            {'area': 'Museo de Ciudad Esmalte', 'method': 'Restauración de Fósil Hélix'},
            DAYCARE_LOCATION
        ]
    },
    140: {
        'type': 'fossil',
        'badge_label': 'Fósil Domo',
        'badge_color': 'blue',
        'summary': 'Restaurar en el Museo de Ciudad Esmalte tras recibir el Fósil Domo al azar de un obrero en el Monte Tuerca (solo tras superar la Liga Pokémon y obtener la Pokédex Nacional; también por crianza).',
        'locations': [
            {'area': 'Monte Tuerca', 'method': 'Fósil aleatorio diario entregado por obrero (Post-game / Pokédex Nacional)'},
            {'area': 'Museo de Ciudad Esmalte', 'method': 'Restauración de Fósil Domo'},
            DAYCARE_LOCATION
        ]
    },
    142: {
        'type': 'fossil',
        'badge_label': 'Ámbar Viejo',
        'badge_color': 'amber',
        'summary': 'Restaurar en el Museo de Ciudad Esmalte tras recibir el Ámbar Viejo al azar de un obrero en el Monte Tuerca (solo tras superar la Liga Pokémon y obtener la Pokédex Nacional; también por crianza).',
        'locations': [
            {'area': 'Monte Tuerca', 'method': 'Fósil aleatorio diario entregado por obrero (Post-game / Pokédex Nacional)'},
            {'area': 'Museo de Ciudad Esmalte', 'method': 'Restauración de Ámbar Viejo'},
            DAYCARE_LOCATION
        ]
    },
    345: {
        'type': 'fossil',
        'badge_label': 'Fósil Raíz',
        'badge_color': 'emerald',
        'summary': 'Restaurar en el Museo de Ciudad Esmalte tras recibir el Fósil Raíz al azar de un obrero en el Monte Tuerca (solo tras superar la Liga Pokémon y obtener la Pokédex Nacional; también por crianza).',
        'locations': [
            {'area': 'Monte Tuerca', 'method': 'Fósil aleatorio diario entregado por obrero (Post-game / Pokédex Nacional)'},
            {'area': 'Museo de Ciudad Esmalte', 'method': 'Restauración de Fósil Raíz'},
            DAYCARE_LOCATION
        ]
    },
    347: {
        'type': 'fossil',
        'badge_label': 'Fósil Garra',
        'badge_color': 'amber',
        'summary': 'Restaurar en el Museo de Ciudad Esmalte tras recibir el Fósil Garra al azar de un obrero en el Monte Tuerca (solo tras superar la Liga Pokémon y obtener la Pokédex Nacional; también por crianza).',
        'locations': [
            {'area': 'Monte Tuerca', 'method': 'Fósil aleatorio diario entregado por obrero (Post-game / Pokédex Nacional)'},
            {'area': 'Museo de Ciudad Esmalte', 'method': 'Restauración de Fósil Garra'},
            DAYCARE_LOCATION
        ]
    },
    408: {
        'type': 'fossil',
        'badge_label': 'Fósil Cráneo',
        'badge_color': 'blue',
        'summary': 'Restaurar en el Museo de Ciudad Esmalte tras recibir el Fósil Cráneo al azar de un obrero en el Monte Tuerca (solo tras superar la Liga Pokémon y obtener la Pokédex Nacional; también por crianza).',
        'locations': [
            {'area': 'Monte Tuerca', 'method': 'Fósil aleatorio diario entregado por obrero (Post-game / Pokédex Nacional)'},
            {'area': 'Museo de Ciudad Esmalte', 'method': 'Restauración de Fósil Cráneo'},
            DAYCARE_LOCATION
        ]
    },
    410: {
        'type': 'fossil',
        'badge_label': 'Fósil Coraza',
        'badge_color': 'zinc',
        'summary': 'Restaurar en el Museo de Ciudad Esmalte tras recibir el Fósil Coraza al azar de un obrero en el Monte Tuerca (solo tras superar la Liga Pokémon y obtener la Pokédex Nacional; también por crianza).',
        'locations': [
            {'area': 'Monte Tuerca', 'method': 'Fósil aleatorio diario entregado por obrero (Post-game / Pokédex Nacional)'},
            {'area': 'Museo de Ciudad Esmalte', 'method': 'Restauración de Fósil Coraza'},
            DAYCARE_LOCATION
        ]
    },

    # Legendarios y singulares de Teselia en Pokémon Negro
    494: {
        'type': 'mythical',
        'badge_label': 'Evento Singular',
        'badge_color': 'amber',
        'summary': 'Encuentro a Nv. 15 en el sótano del faro de Isla Libertad, accesible en barco desde Ciudad Porcelana con el Ticket Libertad de evento (también repartido posteriormente vía Wi-Fi como Victini de la Película 14).',
        'locations': [
            {'area': 'Isla Libertad (Sótano del Faro)', 'method': 'Evento con Ticket Libertad (Nv. 15)'},
            {'area': 'Evento Oficial de Distribución', 'method': 'Tarjeta Misteriosa Wi-Fi (Película 14)'}
        ]
    },
    638: {
        'type': 'legendary',
        'badge_label': 'Legendario',
        'badge_color': 'teal',
        'summary': 'Encuentro fijo a Nv. 42 en la Estancia Orientación dentro de la Cueva Loza (requiere Surf y Fuerza). Desbloquea a Terrakion y Virizion.',
        'locations': [
            {'area': 'Cueva Loza (Estancia Orientación)', 'method': 'Encuentro fijo a Nivel 42'}
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
        'summary': 'Captura obligatoria a Nv. 50 en el Palacio de N durante el clímax de la historia principal (o en la Torre Duodraco si el equipo y cajas estaban llenos). Exclusivo de Pokémon Negro.',
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
        'summary': 'Inaccesible en estado salvaje; solo obtenible mediante distribución oficial de evento de 5.ª Generación (ej. Invierno 2013 por Wi-Fi) o intercambio. En el Pantano Teja aprende Sable Místico junto a Cobalion, Terrakion y Virizion.',
        'locations': [
            {'area': 'Evento Oficial de Distribución', 'method': 'Regalo Misterioso (ej. Wi-Fi INV2013 / evento presencial)'},
            {'area': 'Pantano Teja', 'method': 'Evento de historia para aprender Sable Místico'}
        ]
    },
    648: {
        'type': 'mythical',
        'badge_label': 'Evento Singular',
        'badge_color': 'pink',
        'summary': 'Inaccesible en estado salvaje; solo obtenible mediante distribución oficial de evento de 5.ª Generación (ej. Primavera 2013) o intercambio. En la cafetería La melodía del descanso de Ciudad Porcelana aprende Canto Arcaico, permitiéndole cambiar a Forma Danza en combate.',
        'locations': [
            {'area': 'Evento Oficial de Distribución', 'method': 'Regalo Misterioso (ej. distribución PRI2013)'},
            {'area': 'Ciudad Porcelana (La melodía del descanso)', 'method': 'Músico enseña Canto Arcaico'}
        ]
    },
    649: {
        'type': 'mythical',
        'badge_label': 'Evento Singular',
        'badge_color': 'purple',
        'summary': 'Inaccesible en estado salvaje; solo obtenible mediante distribución oficial de evento de 5.ª Generación (ej. Genesect Plasma por Wi-Fi en 2012) o intercambio. En el Laboratorio P+P de la Ruta 17 un científico entrega los cartuchos PiroROM y FulgoROM en Pokémon Negro.',
        'locations': [
            {'area': 'Evento Oficial de Distribución', 'method': 'Tarjeta Misteriosa Wi-Fi (ej. Genesect Plasma)'},
            {'area': 'Laboratorio P+P (Ruta 17)', 'method': 'Entrega de PiroROM y FulgoROM tras combate'}
        ]
    },
}


SEASON_KEYS_ORDER = ("season-spring", "season-summer", "season-autumn", "season-winter")
SEASON_LABELS_ES = {
    "season-spring": "Primavera",
    "season-summer": "Verano",
    "season-autumn": "Otoño",
    "season-winter": "Invierno",
}
SEASON_SHORT_KEY = {
    "season-spring": "spring",
    "season-summer": "summer",
    "season-autumn": "autumn",
    "season-winter": "winter",
}
SEASONAL_FORM_SPECIES_IDS = {585, 586}
SEASONAL_RATE_NOTES = {
    320: (
        "En Bahía Arenisca (Surf en sombra del agua) aparece todo el año (60% base), pero "
        "en Primavera, Verano y Otoño añade apariciones extra (+30%, hasta el 90% total); "
        "en Invierno disminuye su presencia al ser desplazado por Spheal y Sealeo."
    ),
    525: (
        "En el Monte Tuerca su tasa de aparición varía según la estación por los atajos de nieve: "
        "49% en Primavera y Otoño, 45% en Verano y 30% en Invierno."
    ),
    527: (
        "En el Monte Tuerca su tasa de encuentro se duplica en Verano (20%) frente a "
        "Primavera, Otoño e Invierno (10%)."
    ),
    531: (
        "En la hierba movediza de Ruta 6, Ruta 7 y Torre Duodraco su frecuencia aumenta "
        "en Invierno (+5% adicional: del 70% al 75% en Ruta 6 y del 85% al 90% en Ruta 7 y Torre Duodraco) "
        "al desaparecer Unfezant."
    ),
    533: (
        "En el Monte Tuerca su tasa de aparición disminuye en Invierno (10%) respecto a "
        "Primavera, Verano y Otoño (30%)."
    ),
    613: (
        "En Invierno es común en Monte Tuerca (45%) y además aparece en el exterior de Ruta 7 (30%) "
        "y Torre Duodraco (10%). En Primavera y Otoño baja al 10% en Monte Tuerca, y en Verano "
        "se vuelve muy raro (solo 4% en el interior del Monte Tuerca)."
    ),
    615: (
        "En el Monte Tuerca su tasa de encuentro es muy baja en Primavera, Verano y Otoño (1%), "
        "aumentando al 5% durante el Invierno."
    ),
}


BREEDING_PARENTS_BLACK = {
    13:  ("Kakuna o Beedrill (salvajes en Ruta 12)", "Kakuna / Beedrill"),
    19:  ("Raticate (salvaje en Solar de los Sueños)", "Raticate"),
    21:  ("Fearow (salvaje en Ruta 15)", "Fearow"),
    27:  ("Sandslash (salvaje en Castillo Ancestral)", "Sandslash"),
    41:  ("Golbat o Crobat (salvajes en Boquete Gigante y Ruta 13)", "Golbat / Crobat"),
    48:  ("Venomoth (salvaje en Solar de los Sueños)", "Venomoth"),
    54:  ("Golduck (salvaje en Puente Villa, Ruta 11 y Ruta 14)", "Golduck"),
    74:  ("Graveler (salvaje en Gruta Superación)", "Graveler"),
    77:  ("Rapidash (salvaje en Ruta 12)", "Rapidash"),
    104: ("Marowak (salvaje en Ruta 15)", "Marowak"),
    163: ("Noctowl (salvaje en Santuario Abundancia)", "Noctowl"),
    165: ("Ledian (salvaje en Solar de los Sueños)", "Ledian"),
    167: ("Ariados (salvaje en Solar de los Sueños)", "Ariados"),
    173: ("Clefairy o Clefable (salvajes en Boquete Gigante)", "Clefairy / Clefable"),
    174: ("Jigglypuff o Wigglytuff (salvajes en Ruta 14)", "Jigglypuff / Wigglytuff"),
    220: ("Piloswine o Mamoswine (salvajes en Boquete Gigante)", "Piloswine / Mamoswine"),
    238: ("Jynx (salvaje en Boquete Gigante)", "Jynx"),
    246: ("Pupitar o Tyranitar (salvajes en Ruta 15)", "Pupitar / Tyranitar"),
    276: ("Swellow (salvaje en Boquete Gigante y Ruta 13)", "Swellow"),
    333: ("Altaria (salvaje en Ruta 14)", "Altaria"),
    343: ("Claydol (salvaje en Castillo Ancestral)", "Claydol"),
    374: ("Metang o Metagross (salvajes en Boquete Gigante)", "Metang / Metagross"),
    399: ("Bibarel (salvaje en Puente Villa)", "Bibarel"),
    401: ("Kricketune (salvaje en Solar de los Sueños)", "Kricketune"),
    420: ("Cherrim (salvaje en Ruta 12)", "Cherrim"),
    425: ("Drifblim (salvaje en Boquete Gigante, Ruta 13 y Ruta 14)", "Drifblim"),
    433: ("Chimecho equipado con Incienso Puro (salvaje en Santuario Abundancia)", "Chimecho (con Incienso Puro)"),
    436: ("Bronzong (salvaje en Santuario Abundancia)", "Bronzong"),
}

_POSTGAME_FOSSIL_WORKER_TEXT = (
    "El obrero del Monte Tuerca (cerca de la salida hacia Ciudad Teja) solo entrega fósiles antiguos "
    "en el post-game tras superar la Liga Pokémon y obtener la Pokédex Nacional. Regala un único fósil "
    "al azar al día entre los 7 previos a Teselia (Hélix, Domo, Ámbar Viejo, Raíz, Garra, Cráneo y Coraza); "
    "puedes guardar antes de hablar con él para buscar el que te interese y luego revivirlo en el Museo de Ciudad Esmalte."
)

SPECIAL_NOTES_BLACK = {
    138: [{"title": "Fósil Diario de Post-game", "text": _POSTGAME_FOSSIL_WORKER_TEXT, "tag": "Monte Tuerca", "icon": "/media/items/helix-fossil.png"}],
    140: [{"title": "Fósil Diario de Post-game", "text": _POSTGAME_FOSSIL_WORKER_TEXT, "tag": "Monte Tuerca", "icon": "/media/items/dome-fossil.png"}],
    142: [{"title": "Fósil Diario de Post-game", "text": _POSTGAME_FOSSIL_WORKER_TEXT, "tag": "Monte Tuerca", "icon": "/media/items/old-amber.png"}],
    345: [{"title": "Fósil Diario de Post-game", "text": _POSTGAME_FOSSIL_WORKER_TEXT, "tag": "Monte Tuerca", "icon": "/media/items/root-fossil.png"}],
    347: [{"title": "Fósil Diario de Post-game", "text": _POSTGAME_FOSSIL_WORKER_TEXT, "tag": "Monte Tuerca", "icon": "/media/items/claw-fossil.png"}],
    408: [{"title": "Fósil Diario de Post-game", "text": _POSTGAME_FOSSIL_WORKER_TEXT, "tag": "Monte Tuerca", "icon": "/media/items/skull-fossil.png"}],
    410: [{"title": "Fósil Diario de Post-game", "text": _POSTGAME_FOSSIL_WORKER_TEXT, "tag": "Monte Tuerca", "icon": "/media/items/armor-fossil.png"}],
    564: [{
        "title": "Elección Única en Castillo Ancestral",
        "text": (
            "Durante la historia, una mochilera en el piso 1 del Castillo Ancestral te permite elegir únicamente "
            "un fósil por partida entre el Fósil Tapa (Tirtouga) y el Fósil Pluma (Archen). No se vuelve a entregar "
            "el otro fósil en esa partida, por lo que para completar ambos necesitas intercambio o crianza a partir de otro ejemplar."
        ),
        "tag": "Fósil Tapa",
        "icon": "/media/items/cover-fossil.png",
    }],
    566: [{
        "title": "Elección Única en Castillo Ancestral",
        "text": (
            "Durante la historia, una mochilera en el piso 1 del Castillo Ancestral te permite elegir únicamente "
            "un fósil por partida entre el Fósil Pluma (Archen) y el Fósil Tapa (Tirtouga). No se vuelve a entregar "
            "el otro fósil en esa partida, por lo que para completar ambos necesitas intercambio o crianza a partir de otro ejemplar."
        ),
        "tag": "Fósil Pluma",
        "icon": "/media/items/plume-fossil.png",
    }],
    570: [{
        "title": "Evento Exclusivo de 4.ª Generación",
        "text": (
            "En Pokémon Negro y Blanco originales no aparece salvaje ni te lo regalan de forma normal (a diferencia de "
            "Negro 2 y Blanco 2). Hablar con la chica en el edificio de Game Freak (Ciudad Porcelana) solo "
            "lo registra como visto (pensado para poder buscarlo en la GTS); para obtenerlo (Nv. 10, con Ilusión) es "
            "obligatorio transferir un Celebi de evento desde 4.ª Generación mediante el Trasladador PKMN (necesitas "
            "hueco en el equipo y una Poké Ball). Sin ese evento, la única alternativa es el intercambio o la crianza."
        ),
        "tag": "Trasladador PKMN",
        "icon": "/media/items/dusk-ball.png",
    }],
    571: [{
        "title": "Evento del Bosque de los Perdidos",
        "text": (
            "Zoroark no aparece de forma común en Teselia en Pokémon Negro y Blanco. Además de evolucionar a Zorua "
            "al Nv. 30, existe un encuentro especial en la caravana del Bosque de los Perdidos (Nv. 25, con Ilusión) "
            "que solo se activa llevando a Raikou, Entei o Suicune variocolor de evento transferidos desde "
            "4.ª Generación vía Trasladador PKMN; tras capturarlo, también permite obtener a Zorua mediante crianza."
        ),
        "tag": "Evento Especial",
        "icon": "/media/items/dusk-ball.png",
    }],
    # Eventos históricos, mecánicas en Teselia y transferencias de Legendarios y Singulares
    150: [{
        "title": "Evento Histórico • Mewtwo Primavera 2012",
        "text": (
            "Además de transferirlo desde 4.ª Generación vía Pokétransfer, Mewtwo fue repartido directamente en "
            "Pokémon Negro y Blanco mediante Regalo Misterioso Wi-Fi (evento Primavera 2012 / FEB2012, al Nv. 70 "
            "con Bola Voltio, Onda Mental y Roca del Rey; y en Japón vía Pokémon Smash! / Strongest Return)."
        ),
        "tag": "Evento Gen 5",
        "icon": "/media/items/cherish-ball.png",
    }],
    151: [{
        "title": "Nota de Transferencia • Mew",
        "text": (
            "Mew no contó con distribución oficial propia para Pokémon Negro y Blanco. La vía canónica en Teselia "
            "consiste en transferirlo mediante el Laboratorio de Pokétransfer (Ruta 15) desde un cartucho de 4.ª "
            "Generación (obtenido originalmente en My Pokémon Ranch, eventos Wi-Fi de 4.ª Gen o Esmeralda)."
        ),
        "tag": "Pokétransfer",
        "icon": "/media/items/cherish-ball.png",
    }],
    243: [{
        "title": "Desbloqueo Especial • Trasladador PKMN",
        "text": (
            "Si transfieres al Raikou variocolor de evento de 4.ª Generación (INV2011 / GAMESTP) mediante el "
            "Trasladador PKMN de Ciudad Porcelana (en lugar del Pokétransfer normal), desbloquearás el encuentro "
            "especial contra Zoroark (#571) al Nv. 25 en el Bosque de los Perdidos."
        ),
        "tag": "Trasladador PKMN",
        "icon": "/media/items/cherish-ball.png",
    }],
    244: [{
        "title": "Desbloqueo Especial • Trasladador PKMN",
        "text": (
            "Si transfieres al Entei variocolor de evento de 4.ª Generación (INV2011 / GAMESTP) mediante el "
            "Trasladador PKMN de Ciudad Porcelana (en lugar del Pokétransfer normal), desbloquearás el encuentro "
            "especial contra Zoroark (#571) al Nv. 25 en el Bosque de los Perdidos."
        ),
        "tag": "Trasladador PKMN",
        "icon": "/media/items/cherish-ball.png",
    }],
    245: [{
        "title": "Desbloqueo Especial • Trasladador PKMN",
        "text": (
            "Si transfieres al Suicune variocolor de evento de 4.ª Generación (INV2011 / GAMESTP) mediante el "
            "Trasladador PKMN de Ciudad Porcelana (en lugar del Pokétransfer normal), desbloquearás el encuentro "
            "especial contra Zoroark (#571) al Nv. 25 en el Bosque de los Perdidos."
        ),
        "tag": "Trasladador PKMN",
        "icon": "/media/items/cherish-ball.png",
    }],
    251: [{
        "title": "Desbloqueo Especial • Trasladador PKMN",
        "text": (
            "Aunque Celebi no tuvo reparto propio en Negro y Blanco, transferir un Celebi de evento de 4.ª Generación "
            "(INV2011 / Película 13) mediante el Trasladador PKMN de Ciudad Porcelana activa la entrega exclusiva "
            "de Zorua (#570) al Nv. 10 en la sede de Game Freak."
        ),
        "tag": "Trasladador PKMN",
        "icon": "/media/items/cherish-ball.png",
    }],
    382: [{
        "title": "Evento Histórico • Pokémon Center Fukuoka",
        "text": (
            "En Occidente solo puede conseguirse transfiriéndolo desde 4.ª Generación (HeartGold o juegos de GBA "
            "vía Parque Compi). De forma anecdótica, en Japón fue repartido presencialmente en Pokémon Center "
            "Fukuoka (2012, al Nv. 100) para ediciones de 5.ª Generación."
        ),
        "tag": "Evento Japón",
        "icon": "/media/items/cherish-ball.png",
    }],
    383: [{
        "title": "Evento Histórico • Pokémon Center Fukuoka",
        "text": (
            "En Occidente solo puede conseguirse transfiriéndolo desde 4.ª Generación (SoulSilver o juegos de GBA "
            "vía Parque Compi). De forma anecdótica, en Japón fue repartido presencialmente en Pokémon Center "
            "Fukuoka (2012, al Nv. 100) para ediciones de 5.ª Generación."
        ),
        "tag": "Evento Japón",
        "icon": "/media/items/cherish-ball.png",
    }],
    384: [{
        "title": "Evento Histórico • Rayquaza Variocolor (Japón)",
        "text": (
            "Además de transferirlo desde 4.ª Generación, en Japón se distribuyó en 2012 el famoso Rayquaza negro "
            "variocolor (15.º Aniversario / Pokémon + Nobunaga's Ambition) con el movimiento V de Fuego para "
            "juegos de 5.ª Generación."
        ),
        "tag": "Evento Japón",
        "icon": "/media/items/cherish-ball.png",
    }],
    385: [{
        "title": "Nota de Transferencia • Jirachi",
        "text": (
            "Jirachi no tuvo distribución internacional en Pokémon Negro y Blanco (en Japón recibió un reparto local "
            "en Pokémon Center Tohoku en 2013 al final de la 5.ª Generación). Su vía principal es el Pokétransfer "
            "desde 4.ª Generación (repartos VER2010 o transferencia previa desde Pokémon Channel / Colosseum)."
        ),
        "tag": "Pokétransfer",
        "icon": "/media/items/cherish-ball.png",
    }],
    386: [{
        "title": "Evento Deoxys Plasma y Cambio de Forma",
        "text": (
            "Además de transferirlo desde 4.ª Generación, Deoxys fue repartido en Pokémon Negro y Blanco vía Wi-Fi "
            "(Deoxys Plasma en verano de 2013, Nv. 100 con Vidasfera; y Deoxys Masuda en Japón). En el Museo de "
            "Ciudad Esmalte puedes examinar el meteorito expuesto para alternar entre sus 4 formas."
        ),
        "tag": "Evento y Formas",
        "icon": "/media/items/cherish-ball.png",
    }],
    483: [{
        "title": "Evento Histórico • Trío Creación Variocolor",
        "text": (
            "Además de transferirlo desde D/P/Pt o las Ruinas de Sinjoh (HG/SS), Dialga fue distribuido en su "
            "versión variocolor en tiendas oficiales durante el verano de 2013 (VER2013 / SUM2013) para juegos de "
            "5.ª Generación. El Trío Sombrío entrega su Diamansfera en el Puente Progreso en el post-game."
        ),
        "tag": "Evento Gen 5",
        "icon": "/media/items/adamant-orb.png",
    }],
    484: [{
        "title": "Evento Histórico • Trío Creación Variocolor",
        "text": (
            "Además de transferirlo desde D/P/Pt o las Ruinas de Sinjoh (HG/SS), Palkia fue distribuido en su "
            "versión variocolor en tiendas oficiales durante el verano de 2013 (VER2013 / SUM2013) para juegos de "
            "5.ª Generación. El Trío Sombrío entrega su Lustresfera en el Puente Progreso en el post-game."
        ),
        "tag": "Evento Gen 5",
        "icon": "/media/items/lustrous-orb.png",
    }],
    487: [{
        "title": "Evento Variocolor y Griseosfera en Teselia",
        "text": (
            "Además de transferirlo desde D/P/Pt o las Ruinas de Sinjoh (HG/SS), Giratina fue distribuido en su "
            "versión variocolor en tiendas oficiales durante 2013 (VER2013 / SUM2013) para juegos de 5.ª Generación. "
            "En el post-game, el Trío Sombrío te entrega la Griseosfera en el Puente Progreso para activar su Forma Origen."
        ),
        "tag": "Evento y Forma",
        "icon": "/media/items/griseous-orb.png",
    }],
    489: [{
        "title": "Crianza de Manaphy en Teselia",
        "text": (
            "Si ya has transferido un Manaphy desde 4.ª Generación, puedes dejarlo junto a Ditto en la Guardería de "
            "la Ruta 3 para obtener huevos de Phione directamente en Pokémon Negro (Phione nunca evoluciona a Manaphy)."
        ),
        "tag": "Crianza",
        "icon": "/media/items/mystery-egg.png",
    }],
    490: [{
        "title": "Nota Histórica • Manaphy y Phione",
        "text": (
            "Manaphy no se repartió directamente en Pokémon Negro y Blanco; debe transferirse desde 4.ª Generación "
            "(donde procedía del huevo especial de Pokémon Ranger o eventos Wi-Fi). Al criarlo con Ditto en la "
            "Guardería de la Ruta 3, sus huevos siempre eclosionan en Phione (#489)."
        ),
        "tag": "Pokétransfer",
        "icon": "/media/items/mystery-egg.png",
    }],
    491: [{
        "title": "Evento Histórico • Darkrai Mayo 2012",
        "text": (
            "Además de transferirlo desde 4.ª Generación (Tarjeta Miembro / eventos), Darkrai fue distribuido "
            "directamente en Pokémon Negro y Blanco vía Regalo Misterioso Wi-Fi (evento Mayo 2012 / 2012MAY, al "
            "Nv. 50 equipado con Baya Enigma; y en Japón durante el invierno 2010–2011)."
        ),
        "tag": "Evento Gen 5",
        "icon": "/media/items/cherish-ball.png",
    }],
    492: [{
        "title": "Evento en Japón y Flor Gracídea",
        "text": (
            "En Occidente requiere transferirse desde 4.ª Generación (Carta de Oak / eventos), aunque en Japón "
            "contó con un reparto local en los Pokémon Center (dic. 2011–ene. 2012). En Pokémon Negro, una chica "
            "en el Centro Pokémon de Pueblo Ladrillo te entrega la Gracídea para cambiarlo a Forma Cielo."
        ),
        "tag": "Evento y Forma",
        "icon": "/media/items/gracidea.png",
    }],
    493: [{
        "title": "Evento Histórico • Arceus de Pokémon Global Link",
        "text": (
            "Aunque su vía principal actual es transferirlo desde eventos de 4.ª Generación vía Pokétransfer "
            "(ya que la Flauta Azur jamás se distribuyó), Arceus también fue repartido oficialmente para Pokémon "
            "Negro y Blanco a través del Dream World / Pokémon Global Link tras ganar la encuesta mundial de "
            "popularidad (contraseña internacional «ARCEUSVOTE» en 2012, al Nv. 100 en Dream Ball; Japón 2010–2011). "
            "En Teselia, sus 16 Tablas se hallan en las Ruinas Submarinas y en la Ruta 13."
        ),
        "tag": "Evento PGL",
        "icon": "/media/items/dream-ball.png",
    }],
    494: [{
        "title": "Evento Histórico • Victini Película 14",
        "text": (
            "Además del Ticket Libertad de lanzamiento para capturarlo al Nv. 15 en Isla Libertad, Victini volvió "
            "a repartirse por Wi-Fi durante la promoción de la Película 14 (Nv. 50 con el movimiento exclusivo V de Fuego)."
        ),
        "tag": "Evento Gen 5",
        "icon": "/media/items/cherish-ball.png",
    }],
    643: [{
        "title": "Evento Histórico • Primavera 2012",
        "text": (
            "Durante la promoción Primavera 2012 (PRI2012 / SPR2012) vía Wi-Fi se repartió al dragón contrario "
            "a cada edición: Zekrom para Pokémon Negro y Reshiram para Pokémon Blanco (al Nv. 100 con movimientos especiales)."
        ),
        "tag": "Evento Gen 5",
        "icon": "/media/items/cherish-ball.png",
    }],
    644: [{
        "title": "Evento Histórico • Zekrom Primavera 2012",
        "text": (
            "Aunque Zekrom es exclusivo de Pokémon Blanco, en su época se distribuyó directamente para Pokémon Negro "
            "vía Wi-Fi mediante el evento Primavera 2012 (PRI2012 / SPR2012, al Nv. 100 con Gema Dragón)."
        ),
        "tag": "Evento Gen 5",
        "icon": "/media/items/cherish-ball.png",
    }],
    647: [{
        "title": "Evento en Pantano Teja • Sable Místico",
        "text": (
            "Keldeo fue repartido mediante Regalo Misterioso en eventos oficiales (ej. Wi-Fi Invierno 2013 / INV2013). "
            "Al llevarlo al Pantano Teja junto a Cobalion, Terrakion y Virizion en el equipo, un anciano narra su "
            "historia y Keldeo aprende Sable Místico (en Negro y Blanco originales aún no existe su Forma Brío)."
        ),
        "tag": "Evento Singular",
        "icon": "/media/items/cherish-ball.png",
    }],
    649: [{
        "title": "Cartuchos exclusivos por edición",
        "text": (
            "Genesect fue repartido vía Wi-Fi (Genesect Plasma, otoño de 2012). En el Laboratorio P+P de la Ruta 17, "
            "tras derrotar al científico llevando a Genesect en el equipo, en Pokémon Negro entrega únicamente el "
            "PiroROM (Fuego) y el FulgoROM (Eléctrico); HidroROM y CrioROM deben intercambiarse desde Pokémon Blanco."
        ),
        "tag": "Evento y Cartuchos",
        "icon": "/media/items/burn-drive.png",
    }],
}


def is_indoor_or_cave(area_clean: str) -> bool:
    area_lower = area_clean.lower()
    if any(ext in area_lower for ext in ('ladera exterior', 'torre duodraco (entrada)', 'torre duodraco (exterior)', 'boquete gigante (exterior)', 'bosque interior')):
        return False
    return any(
        k in area_lower
        for k in ('cueva', 'monte tuerca', 'gruta superación', 'castillo ancestral', 'palacio de n', 'torre de los cielos', 'torre duodraco', 'calle victoria', 'estancia orientación', 'cámara')
    )


def format_wild_method(method_raw: str, conditions: list, area_clean: str) -> str:
    if 'swarm-yes' in conditions:
        return 'Manada diaria'
    if method_raw == 'npc-trade':
        if 'trade-boldore' in conditions:
            return 'Intercambio NPC por Boldore'
        return 'Intercambio NPC'
    if method_raw == 'static':
        return 'Encuentro estático (Poké Ball camuflada)'
    if method_raw == 'dark-grass':
        return 'Hierba oscura (Combates dobles)'
    if method_raw == 'grass-spots':
        if is_indoor_or_cave(area_clean):
            return 'Nube de polvo'
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
        area_lower = area_clean.lower()
        if area_lower in ('ciudad teja', 'ruta 8', 'pantano teja'):
            return 'Caminando en charcos'
        if area_lower in ('ruta 4', 'zona desierto', 'zona desierto (entrada)'):
            return 'Caminando en la arena'
        if is_indoor_or_cave(area_clean):
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
        entry_seasons = set()
        if nat_id in SEASONAL_FORM_SPECIES_IDS:
            entry_seasons.update(("spring", "summer", "autumn", "winter"))

        def _collect_wild_locations():
            area_method_meta = {}
            for e in raw_encs:
                area_key = e.get('area_raw', '')
                if 'team-flare' in area_key:
                    continue
                if nat_id == 550 and area_key == 'driftveil-city-area':
                    continue
                conds = e.get('conditions', []) or []
                clean_area = UNOVA_AREA_NAMES.get(area_key, area_key.replace('-', ' ').title())
                meth_desc = format_wild_method(e.get('method_raw', 'walk'), conds, clean_area)
                bucket = area_method_meta.setdefault(clean_area, {}).setdefault(
                    meth_desc, {'always': False, 'seasons': set()}
                )
                s_conds = [c for c in conds if c in SEASON_LABELS_ES]
                if s_conds:
                    bucket['seasons'].update(s_conds)
                else:
                    bucket['always'] = True

            area_methods = {}
            for a_name, methods_dict in area_method_meta.items():
                area_methods[a_name] = set()
                for m_desc, meta in methods_dict.items():
                    s_set = meta['seasons']
                    if not meta['always'] and 0 < len(s_set) < 4:
                        ordered = [s for s in SEASON_KEYS_ORDER if s in s_set]
                        season_text = ", ".join(SEASON_LABELS_ES[s] for s in ordered)
                        area_methods[a_name].add(f"{m_desc} ({season_text})")
                        for s in ordered:
                            entry_seasons.add(SEASON_SHORT_KEY[s])
                    else:
                        area_methods[a_name].add(m_desc)
                        if s_set and nat_id in SEASONAL_RATE_NOTES:
                            for s in s_set:
                                entry_seasons.add(SEASON_SHORT_KEY[s])

            # Las manadas diarias de Gen 5 no siempre figuran en PokeAPI; registrar su ruta y método explícitamente
            if nat_id in SWARM_POKEMON_BLACK:
                sw_info = SWARM_POKEMON_BLACK[nat_id]
                area_methods.setdefault(sw_info['area'], set()).add('Manada diaria')

            loc_list = []
            for a_name, m_set in area_methods.items():
                loc_list.append({
                    'area': a_name,
                    'method': ", ".join(sorted(list(m_set)))
                })
            return area_methods, loc_list

        if nat_id in SPECIAL_OBTAINING:
            obt_info = json.loads(json.dumps(SPECIAL_OBTAINING[nat_id]))
            if nat_id == 550 and raw_encs:
                _, wild_locs = _collect_wild_locations()
                obt_info['locations'] = wild_locs + obt_info.get('locations', [])
        elif raw_encs or nat_id in SWARM_POKEMON_BLACK:
            area_methods, loc_list = _collect_wild_locations()

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

            if nat_id == 587:
                summary += " También es obtenible mediante intercambio NPC en una casa de la Ruta 7 entregando un Boldore."
            if is_hatchable and nat_id not in SWARM_POKEMON_BLACK:
                summary += " También obtenible mediante crianza en la Guardería de la Ruta 3."

            obt_info = {
                'type': 'wild',
                'badge_label': 'Salvaje',
                'badge_color': 'emerald',
                'summary': summary,
                'locations': loc_list
            }
            if entry_seasons:
                season_order = ["spring", "summer", "autumn", "winter"]
                obt_info['seasons'] = [s for s in season_order if s in entry_seasons]
        elif (is_evolution or (is_incense_parent and nat_id not in white_exclusives and nat_id not in black_transfers)) and evo_info:
            from_name = evo_info.get('from_name', '')
            cond = evo_info.get('condition', '')
            summary = f"Evoluciona de {from_name} ({cond})."
            item_slug = evo_info.get('item_slug')
            obt_info = {
                'type': 'evolution',
                'badge_label': 'Evolución',
                'badge_color': 'purple',
                'summary': summary,
                'locations': [],
                'item_slug': item_slug,
                'evolution_info': {
                    'from': from_name,
                    'text': evo_info.get('text', summary),
                    'trigger': evo_info.get('trigger', 'level-up'),
                    'condition': cond,
                    'item_slug': item_slug,
                }
            }
        elif nat_id in BREEDING_PARENTS_BLACK:
            parent_desc, loc_parents = BREEDING_PARENTS_BLACK[nat_id]
            summary = f"Inaccesible en estado salvaje; se obtiene mediante crianza de {parent_desc} en la Guardería de la Ruta 3."
            loc_list = [{'area': 'Ruta 3 (Guardería Pokémon)', 'method': f'Crianza de huevo ({loc_parents})'}]
            obt_info = {
                'type': 'other',
                'badge_label': 'Crianza',
                'badge_color': 'zinc',
                'summary': summary,
                'locations': loc_list
            }
        elif nat_id in white_exclusives:
            non_white_forest = {577, 627, 642, 644, 10, 46, 200, 261, 312, 314}
            if nat_id == 642:
                summary = "Inaccesible en estado salvaje en Pokémon Negro. Legendario errante exclusivo de Pokémon Blanco (requiere intercambio para registrarlo y desbloquear a Landorus en el Santuario Abundancia)."
            elif nat_id == 644:
                summary = "Inaccesible en estado salvaje en Pokémon Negro. Legendario de portada exclusivo de Pokémon Blanco (requiere intercambio; en su época también fue repartido por evento Wi-Fi Primavera 2012)."
            elif nat_id in non_white_forest:
                summary = "Inaccesible en estado salvaje en Pokémon Negro. Exclusivo de Pokémon Blanco (requiere intercambio)."
            else:
                summary = "Inaccesible en estado salvaje en Pokémon Negro. Exclusivo del Bosque Blanco de Pokémon Blanco (requiere intercambio o conexión mediante Zona Nexo con dicho bosque)."
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
            origin_desc = black_origins.get(nat_id, "Pokétransfer (Ruta 15)")
            transfer_event_summaries = {
                150: "Inaccesible en estado salvaje en Teselia. Su método principal consiste en transferirlo mediante Pokétransfer (Ruta 15) desde cartuchos de 4.ª Generación; en su época también se repartió por evento Wi-Fi (Primavera 2012).",
                151: "Inaccesible en estado salvaje en Teselia. Requiere transferirlo mediante Pokétransfer (Ruta 15) desde cartuchos de 4.ª Generación (My Pokémon Ranch o eventos previos).",
                243: "Inaccesible en estado salvaje en Teselia. Requiere transferirlo mediante Pokétransfer (Ruta 15) desde cartuchos de 4.ª Generación (el ejemplar variocolor de evento activa a Zoroark en el Trasladador PKMN).",
                244: "Inaccesible en estado salvaje en Teselia. Requiere transferirlo mediante Pokétransfer (Ruta 15) desde cartuchos de 4.ª Generación (el ejemplar variocolor de evento activa a Zoroark en el Trasladador PKMN).",
                245: "Inaccesible en estado salvaje en Teselia. Requiere transferirlo mediante Pokétransfer (Ruta 15) desde cartuchos de 4.ª Generación (el ejemplar variocolor de evento activa a Zoroark en el Trasladador PKMN).",
                251: "Inaccesible en estado salvaje en Teselia. Requiere transferirlo mediante Pokétransfer (Ruta 15) desde cartuchos de 4.ª Generación (un Celebi de evento vía Trasladador PKMN desbloquea a Zorua).",
                382: "Inaccesible en estado salvaje en Teselia. Su método principal consiste en transferirlo mediante Pokétransfer (Ruta 15) desde cartuchos de 4.ª Generación (también tuvo un reparto local en Japón en 2012).",
                383: "Inaccesible en estado salvaje en Teselia. Su método principal consiste en transferirlo mediante Pokétransfer (Ruta 15) desde cartuchos de 4.ª Generación (también tuvo un reparto local en Japón en 2012).",
                384: "Inaccesible en estado salvaje en Teselia. Su método principal consiste en transferirlo mediante Pokétransfer (Ruta 15) desde cartuchos de 4.ª Generación (también tuvo un reparto variocolor en Japón en 2012).",
                385: "Inaccesible en estado salvaje en Teselia. Requiere transferirlo mediante Pokétransfer (Ruta 15) desde cartuchos de 4.ª Generación (procedente de eventos o Pokémon Channel / Colosseum).",
                386: "Inaccesible en estado salvaje en Teselia. Su método principal consiste en transferirlo mediante Pokétransfer (Ruta 15) desde cartuchos de 4.ª Generación; también se repartió en Negro y Blanco vía Wi-Fi (Deoxys Plasma, 2013).",
                483: "Inaccesible en estado salvaje en Teselia. Su método principal consiste en transferirlo mediante Pokétransfer (Ruta 15) desde cartuchos de 4.ª Generación; también fue repartido variocolor en tiendas en 2013 (VER2013).",
                484: "Inaccesible en estado salvaje en Teselia. Su método principal consiste en transferirlo mediante Pokétransfer (Ruta 15) desde cartuchos de 4.ª Generación; también fue repartido variocolor en tiendas en 2013 (VER2013).",
                487: "Inaccesible en estado salvaje en Teselia. Su método principal consiste en transferirlo mediante Pokétransfer (Ruta 15) desde cartuchos de 4.ª Generación; también fue repartido variocolor en tiendas en 2013 (VER2013).",
                489: "Inaccesible en estado salvaje en Teselia. Requiere transferirlo mediante Pokétransfer (Ruta 15) desde cartuchos de 4.ª Generación, o criarlo con Ditto en la Guardería de la Ruta 3 a partir de un Manaphy transferido.",
                490: "Inaccesible en estado salvaje en Teselia. Requiere transferirlo mediante Pokétransfer (Ruta 15) desde cartuchos de 4.ª Generación (Huevo de Pokémon Ranger o eventos).",
                491: "Inaccesible en estado salvaje en Teselia. Su método principal consiste en transferirlo mediante Pokétransfer (Ruta 15) desde cartuchos de 4.ª Generación; también se repartió vía Wi-Fi en Negro y Blanco (Mayo 2012).",
                492: "Inaccesible en estado salvaje en Teselia. Su método principal consiste en transferirlo mediante Pokétransfer (Ruta 15) desde cartuchos de 4.ª Generación (tuvo un reparto local en Japón en 2011–2012).",
                493: "Inaccesible en estado salvaje en Teselia. Su método principal consiste en transferirlo mediante Pokétransfer (Ruta 15) desde cartuchos de 4.ª Generación; también se repartió en su época en Pokémon Negro y Blanco vía Pokémon Global Link (Dream World).",
            }
            summary = transfer_event_summaries.get(
                nat_id,
                f"Inaccesible en estado salvaje en Teselia. Requiere transferirlo mediante {origin_desc} desde cartuchos de 4.ª Generación."
            )
            loc_list = [{'area': 'Laboratorio de Pokétransfer (Ruta 15)', 'method': f"{origin_desc}"}]
            if nat_id == 489:
                loc_list.append(DAYCARE_LOCATION)
            elif is_hatchable:
                loc_list.append(DAYCARE_LOCATION)
            obt_info = {
                'type': 'transfer',
                'badge_label': 'Pokétransfer',
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
        baby_incense_slug = get_incense_for_baby(nat_id, generation=5)
        new_locations = []
        has_daycare = False
        incense_name = evolution_stones.get(baby_incense_slug, {}).get('name_es', 'Incienso') if baby_incense_slug else None
        for loc in obt_info.get('locations', []):
            if 'Guardería' in loc.get('area', ''):
                has_daycare = True
                if baby_incense_slug:
                    new_locations.append({
                        'area': 'Ruta 3 (Guardería Pokémon)',
                        'method': f"Crianza con {incense_name}"
                    })
                else:
                    new_locations.append({'area': 'Ruta 3 (Guardería Pokémon)', 'method': loc.get('method', 'Crianza de huevo')})
            else:
                new_locations.append({'area': loc.get('area', ''), 'method': loc.get('method', '')})

        if is_hatchable and not has_daycare and obt_info.get('type') != 'evolution':
            if baby_incense_slug:
                new_locations.append({
                    'area': 'Ruta 3 (Guardería Pokémon)',
                    'method': f"Crianza con {incense_name}"
                })
            else:
                new_locations.append({
                    'area': 'Ruta 3 (Guardería Pokémon)',
                    'method': 'Crianza de huevo'
                })

        if baby_incense_slug and incense_name and incense_name.lower() not in obt_info.get('summary', '').lower():
            cur_sum = obt_info.get('summary', '')
            if 'mediante crianza' in cur_sum:
                obt_info['summary'] = cur_sum.replace('mediante crianza', f'mediante crianza con {incense_name}', 1)
            elif has_daycare or is_hatchable:
                obt_info['summary'] = f"{cur_sum} También obtenible mediante crianza equipada con {incense_name}."

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

        entry_notes = []
        if nat_id in SPECIAL_NOTES_BLACK:
            entry_notes.extend(json.loads(json.dumps(SPECIAL_NOTES_BLACK[nat_id])))
        if nat_id in SEASONAL_RATE_NOTES:
            entry_notes.append({
                "title": "Tasa de Aparición Estacional",
                "text": SEASONAL_RATE_NOTES[nat_id],
                "tag": "Estaciones",
                "icon": "/media/items/journal.png",
            })

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
            "notes": entry_notes,
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
