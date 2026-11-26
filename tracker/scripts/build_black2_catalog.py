"""
Script para compilar los catálogos oficiales de Pokémon Negro 2:
- tracker/data/catalogs/black-2.json (Pokédex Regional de Teselia 2 - 301 especies, #000 Victini a #300 Genesect, IDs 10000..10300)
- tracker/data/catalogs/black-2_national.json (Pokédex Nacional - 649 especies, #001 Bulbasaur a #649 Genesect, IDs 10401..11049)
Siguiendo rigurosamente guides/especificacion-pokemon-negro-2.md y la guía técnica maestra.
"""
import json
import os
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

UNOVA2_AREA_NAMES = {
    'abundant-shrine-area': 'Santuario Abundancia',
    'abundant-shrine-hidden-grotto-near-youngster': 'Santuario Abundancia (Claro Oculto Oeste)',
    'abundant-shrine-hidden-grotto-shrine': 'Santuario Abundancia (Claro Oculto Norte)',
    'accumula-town-area': 'Pueblo Terracota',
    'aspertia-city-area': 'Ciudad Engobe',
    'castelia-city-area': 'Ciudad Porcelana',
    'castelia-sewers-area': 'Cloacas Porcelana',
    'castelia-sewers-unknown-area-38': 'Cloacas Porcelana',
    'celestial-tower-2f': 'Torre de los Cielos (P2)',
    'celestial-tower-3f': 'Torre de los Cielos (P3)',
    'celestial-tower-4f': 'Torre de los Cielos (P4)',
    'celestial-tower-5f': 'Torre de los Cielos (Cima)',
    'chargestone-cave-1f': 'Cueva Electrorroca (P1)',
    'chargestone-cave-b1f': 'Cueva Electrorroca (S1)',
    'chargestone-cave-b2f': 'Cueva Electrorroca (S2)',
    'clay-tunnel-area': 'Túnel Yakón',
    'desert-resort-area': 'Zona Desierto',
    'desert-resort-entrance': 'Zona Desierto (Entrada)',
    'dragonspiral-tower-1f': 'Torre Duodraco (P1)',
    'dragonspiral-tower-2f': 'Torre Duodraco (P2)',
    'dragonspiral-tower-7f': 'Torre Duodraco (Cima)',
    'dragonspiral-tower-entrance': 'Torre Duodraco (Entrada)',
    'dragonspiral-tower-outside': 'Torre Duodraco (Exterior)',
    'dreamyard-area': 'Solar de los Sueños',
    'dreamyard-b1f': 'Solar de los Sueños (S1)',
    'driftveil-city-area': 'Ciudad Fayenza',
    'driftveil-drawbridge-area': 'Puente Fayenza',
    'floccesy-ranch-hidden-grotto': 'Rancho Ocre (Claro Oculto)',
    'floccesy-ranch-inner': 'Rancho Ocre',
    'floccesy-ranch-outer': 'Rancho Ocre',
    'floccesy-town-area': 'Pueblo Ocre',
    'giant-chasm-area': 'Boquete Gigante (Cueva de Entrada)',
    'giant-chasm-forest': 'Boquete Gigante (Bosque Interior)',
    'giant-chasm-forest-cave': 'Boquete Gigante (Cráter)',
    'giant-chasm-hidden-grotto': 'Boquete Gigante (Claro Oculto)',
    'giant-chasm-outside': 'Boquete Gigante (Exterior)',
    'glacier-room-area': 'Ruinas Subterráneas (Cámara Iceberg)',
    'guidance-chamber-area': 'Cueva Loza (Estancia Orientación)',
    'humilau-city-area': 'Ciudad Marga',
    'icirrus-city-area': 'Ciudad Teja',
    'iron-room-area': 'Ruinas Subterráneas (Cámara Hierro)',
    'lostlorn-forest-area': 'Bosque de los Perdidos',
    'lostlorn-forest-hidden-grotto': 'Bosque de los Perdidos (Claro Oculto)',
    'marvelous-bridge-area': 'Puente Progreso',
    'mistralton-cave-area': 'Cueva Loza',
    'moor-of-icirrus-area': 'Pantano Teja',
    'nacrene-city-nacrene-museum': 'Museo de Ciudad Esmalte',
    'nacrene-city-west-gate': 'Ciudad Esmalte (Acceso Oeste)',
    'nature-sanctuary-area': 'Reserva Natural',
    'p2-laboratory-area': 'Laboratorio P+P',
    'pinwheel-forest-hidden-grotto-inner-area': 'Bosque Azulejo (Claro Oculto Interior)',
    'pinwheel-forest-hidden-grotto-outer-area': 'Bosque Azulejo (Claro Oculto Exterior)',
    'pinwheel-forest-inside': 'Bosque Azulejo (Interior)',
    'pinwheel-forest-outside': 'Bosque Azulejo (Exterior)',
    'relic-castle-a': 'Castillo Ancestral (P1)',
    'relic-castle-c': 'Castillo Ancestral (S2-S4)',
    'relic-castle-d': 'Castillo Ancestral (Planta más profunda)',
    'relic-passage-castelia-sewers-entrance': 'Pasadizo Ancestral (Cloacas Porcelana)',
    'relic-passage-pwt-entrance': 'Pasadizo Ancestral (Acceso PWT)',
    'relic-passage-relic-castle-entrance': 'Pasadizo Ancestral (Castillo Ancestral)',
    'reversal-mountain-b1f': 'Montaña Reversia (Interior)',
    'reversal-mountain-unknown-area-48': 'Montaña Reversia (Exterior)',
    'reversal-mountain-unknown-area-49': 'Montaña Reversia (Interior)',
    'reversal-mountain-unknown-area-50': 'Montaña Reversia (Interior)',
    'reversal-mountain-unknown-area-51': 'Montaña Reversia (Interior)',
    'reversal-mountain-unknown-area-52': 'Montaña Reversia (Interior)',
    'reversal-mountain-unknown-area-53': 'Montaña Reversia (Interior)',
    'reversal-mountain-unknown-area-54': 'Montaña Reversia (Interior)',
    'reversal-mountain-unknown-area-55': 'Montaña Reversia (Interior)',
    'reversal-mountain-unknown-area-56': 'Montaña Reversia (Interior)',
    'reversal-mountain-unknown-area-57': 'Montaña Reversia (Interior)',
    'reversal-mountain-unknown-area-58': 'Montaña Reversia (Interior)',
    'reversal-mountain-unknown-area-59': 'Montaña Reversia (Interior)',
    'reversal-mountain-unknown-area-60': 'Montaña Reversia (Interior)',
    'rocky-mountain-room-area': 'Ruinas Subterráneas (Cámara Pico Roca)',
    'seaside-cave-1f': 'Gruta Marina (P1)',
    'seaside-cave-b1f': 'Gruta Marina (S1)',
    'strange-house-1f': 'Villa Horroris (P1)',
    'strange-house-b1f': 'Villa Horroris (S1)',
    'striaton-city-area': 'Ciudad Gres',
    'twist-mountain-b1f-3f': 'Monte Tuerca',
    'twist-mountain-b4f': 'Monte Tuerca (S4)',
    'undella-bay-area': 'Bahía Arenisca',
    'undella-town-area': 'Pueblo Arenisca',
    'underground-ruins-area': 'Ruinas Subterráneas',
    'unova-route-1-area': 'Ruta 1',
    'unova-route-2-area': 'Ruta 2',
    'unova-route-2-hidden-grotto': 'Ruta 2 (Claro Oculto)',
    'unova-route-3-area': 'Ruta 3',
    'unova-route-3-hidden-grotto-dark-grass': 'Ruta 3 (Claro Oculto Norte)',
    'unova-route-3-hidden-grotto-pond': 'Ruta 3 (Claro Oculto Lago)',
    'unova-route-4-area': 'Ruta 4',
    'unova-route-5-area': 'Ruta 5',
    'unova-route-5-hidden-grotto': 'Ruta 5 (Claro Oculto)',
    'unova-route-6-area': 'Ruta 6',
    'unova-route-6-hidden-grotto-mistralton-cave': 'Ruta 6 (Claro Oculto Cueva Loza)',
    'unova-route-6-hidden-grotto-near-pokemon-breeder': 'Ruta 6 (Claro Oculto Norte)',
    'unova-route-6-weather-institute': 'Ruta 6 (Centro de Estudios Estacionales)',
    'unova-route-7-area': 'Ruta 7',
    'unova-route-7-hidden-grotto': 'Ruta 7 (Claro Oculto)',
    'unova-route-8-area': 'Ruta 8',
    'unova-route-9-area': 'Ruta 9',
    'unova-route-9-hidden-grotto': 'Ruta 9 (Claro Oculto)',
    'unova-route-11-area': 'Ruta 11',
    'unova-route-12-area': 'Ruta 12',
    'unova-route-13-area': 'Ruta 13',
    'unova-route-13-hidden-grotto-giant-chasm': 'Ruta 13 (Claro Oculto Norte)',
    'unova-route-13-hidden-grotto-stairs': 'Ruta 13 (Claro Oculto Escaleras)',
    'unova-route-14-area': 'Ruta 14',
    'unova-route-15-area': 'Ruta 15',
    'unova-route-16-area': 'Ruta 16',
    'unova-route-17-area': 'Ruta 17',
    'unova-route-18-area': 'Ruta 18',
    'unova-route-18-hidden-grotto': 'Ruta 18 (Claro Oculto)',
    'unova-route-19-area': 'Ruta 19',
    'unova-route-20-area': 'Ruta 20',
    'unova-route-21-area': 'Ruta 21',
    'unova-route-22-area': 'Ruta 22',
    'unova-route-22-hidden-grotto': 'Ruta 22 (Claro Oculto)',
    'unova-route-23-area': 'Ruta 23',
    'unova-route-23-hidden-grotto': 'Ruta 23 (Claro Oculto)',
    'unova-victory-road-2-unknown-area-71': 'Calle Victoria (Interior)',
    'unova-victory-road-2-unknown-area-72': 'Calle Victoria (Exterior)',
    'unova-victory-road-2-unknown-area-73': 'Calle Victoria (Exterior)',
    'unova-victory-road-2-unknown-area-74': 'Calle Victoria (Interior)',
    'unova-victory-road-2-unknown-area-75': 'Calle Victoria (Interior)',
    'unova-victory-road-2-unknown-area-76': 'Calle Victoria (Exterior)',
    'unova-victory-road-2-unknown-area-77': 'Calle Victoria (Interior)',
    'unova-victory-road-2-unknown-area-78': 'Calle Victoria (Interior)',
    'unova-victory-road-2-unknown-area-79': 'Calle Victoria (Exterior)',
    'unova-victory-road-2-unknown-area-80': 'Calle Victoria (Interior)',
    'unova-victory-road-7f': 'Calle Victoria (Interior)',
    'village-bridge-area': 'Puente Villa',
    'virbank-city-area': 'Ciudad Hormigón',
    'virbank-complex-inner': 'Polígono Hormigón (Interior)',
    'virbank-complex-outer': 'Polígono Hormigón (Exterior)',
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
    'regigigas', 'giratina', 'cresselia', 'manaphy', 'darkrai',
    'shaymin', 'arceus',
    'victini', 'cobalion', 'terrakion', 'virizion', 'tornadus',
    'thundurus', 'reshiram', 'zekrom', 'landorus', 'kyurem',
    'keldeo', 'meloetta', 'genesect'
}

DAYCARE_LOCATION = {
    'area': 'Ruta 3 (Guardería Pokémon)',
    'method': 'Crianza de huevo'
}

# 19 Manadas Diarias de Pokémon Negro 2 (4 exclusivas de Negro 2 + 15 compartidas con Blanco 2)
SWARM_POKEMON_BLACK2 = {
    # 4 exclusivas de Pokémon Negro 2
    313: {'area': 'Ruta 3', 'desc': 'Manada diaria en la Ruta 3 tras superar la Liga Pokémon (exclusivo salvaje de Negro 2; al criarlo con Ditto en 5.ª Gen también puede producir huevos de Illumise).'},
    311: {'area': 'Ruta 6', 'desc': 'Manada diaria en la Ruta 6 tras superar la Liga Pokémon (exclusivo de Pokémon Negro 2).'},
    185: {'area': 'Ruta 20', 'desc': 'Manada diaria en la Ruta 20 tras superar la Liga Pokémon (exclusivo de Pokémon Negro 2).'},
    168: {'area': 'Ruta 22', 'desc': 'Manada diaria en la Ruta 22 tras superar la Liga Pokémon (exclusivo de Pokémon Negro 2).'},
    # 15 compartidas (Negro 2 y Blanco 2)
    83:  {'area': 'Ruta 1', 'desc': 'Manada diaria en la Ruta 1 tras superar la Liga Pokémon.'},
    177: {'area': 'Ruta 5', 'desc': 'Manada diaria en la Ruta 5 tras superar la Liga Pokémon.'},
    162: {'area': 'Ruta 7', 'desc': 'Manada diaria en la Ruta 7 tras superar la Liga Pokémon.'},
    195: {'area': 'Ruta 8', 'desc': 'Manada diaria en la Ruta 8 tras superar la Liga Pokémon.'},
    317: {'area': 'Ruta 9', 'desc': 'Manada diaria en la Ruta 9 tras superar la Liga Pokémon.'},
    284: {'area': 'Ruta 11', 'desc': 'Manada diaria en la Ruta 11 tras superar la Liga Pokémon.'},
    84:  {'area': 'Ruta 12', 'desc': 'Manada diaria en la Ruta 12 tras superar la Liga Pokémon.'},
    277: {'area': 'Ruta 13', 'desc': 'Manada diaria en la Ruta 13 tras superar la Liga Pokémon.'},
    22:  {'area': 'Ruta 15', 'desc': 'Manada diaria en la Ruta 15 tras superar la Liga Pokémon.'},
    204: {'area': 'Ruta 16', 'desc': 'Manada diaria en la Ruta 16 tras superar la Liga Pokémon.'},
    187: {'area': 'Ruta 18', 'desc': 'Manada diaria en la Ruta 18 tras superar la Liga Pokémon.'},
    97:  {'area': 'Solar de los Sueños', 'desc': 'Manada diaria en el Solar de los Sueños tras superar la Liga Pokémon.'},
    450: {'area': 'Zona Desierto', 'desc': 'Manada diaria en la Zona Desierto tras superar la Liga Pokémon.'},
    79:  {'area': 'Santuario Abundancia', 'desc': 'Manada diaria en el Santuario Abundancia tras superar la Liga Pokémon.'},
    332: {'area': 'Montaña Reversia', 'desc': 'Manada diaria en la Montaña Reversia tras superar la Liga Pokémon.'},
}

# Claros Ocultos adicionales no incluidos en PokeAPI (ej. Stunky exclusivo de misión Zona Nexo en Negro 2)
EXTRA_HIDDEN_GROTTOS_BLACK2 = {
    434: [
        {
            'area': 'Claros Ocultos (Misión Zona Nexo)',
            'method': 'Claro Oculto (Misión Zona Nexo)',
        }
    ]
}

SPECIAL_OBTAINING_BLACK2 = {
    # Iniciales de Teselia (entregados por Bel en el mirador de Ciudad Engobe)
    495: {
        'type': 'starter',
        'badge_label': 'Inicial',
        'badge_color': 'emerald',
        'summary': 'Elegir como regalo de Bel en el mirador de Ciudad Engobe al comenzar tu aventura (también obtenible mediante crianza).',
        'locations': [
            {'area': 'Ciudad Engobe (Mirador)', 'method': 'Elección de Inicial de Teselia (regalo de Bel)'},
            DAYCARE_LOCATION
        ]
    },
    498: {
        'type': 'starter',
        'badge_label': 'Inicial',
        'badge_color': 'amber',
        'summary': 'Elegir como regalo de Bel en el mirador de Ciudad Engobe al comenzar tu aventura (también obtenible mediante crianza).',
        'locations': [
            {'area': 'Ciudad Engobe (Mirador)', 'method': 'Elección de Inicial de Teselia (regalo de Bel)'},
            DAYCARE_LOCATION
        ]
    },
    501: {
        'type': 'starter',
        'badge_label': 'Inicial',
        'badge_color': 'sky',
        'summary': 'Elegir como regalo de Bel en el mirador de Ciudad Engobe al comenzar tu aventura (también obtenible mediante crianza).',
        'locations': [
            {'area': 'Ciudad Engobe (Mirador)', 'method': 'Elección de Inicial de Teselia (regalo de Bel)'},
            DAYCARE_LOCATION
        ]
    },

    # Regalos del juego y compras especiales
    570: {
        'type': 'gift',
        'badge_label': 'Regalo del juego',
        'badge_color': 'purple',
        'summary': 'Regalo del Sabio Ruga (Ex Equipo Plasma) en Ciudad Fayenza al Nv. 25 (Zorua de N, EO: N; también obtenible mediante crianza).',
        'locations': [
            {'area': 'Ciudad Fayenza (Casa del Ex Equipo Plasma)', 'method': 'Regalo del juego (Sabio Ruga • Zorua de N, Nv. 25)'},
            DAYCARE_LOCATION
        ]
    },
    133: {
        'type': 'gift',
        'badge_label': 'Regalo / Salvaje',
        'badge_color': 'amber',
        'summary': 'Salvaje en el parque de Ciudad Porcelana (accediendo por las Cloacas Porcelana). Además, en el post-Liga, Trufa te regala un Eevee al Nv. 10 con habilidad oculta Anticipación en el P2 de la Calle del Gimnasio de Ciudad Porcelana (y también por crianza).',
        'locations': [
            {'area': 'Ciudad Porcelana (Calle del Gimnasio P2)', 'method': 'Regalo del juego (Trufa, post-Liga • Nv. 10 con Anticipación)'},
            DAYCARE_LOCATION
        ]
    },
    585: {
        'type': 'wild',
        'badge_label': 'Salvaje / Regalo',
        'badge_color': 'emerald',
        'seasons': ['spring', 'summer', 'autumn', 'winter'],
        'summary': 'Salvaje en Ruta 6, Ruta 7 y Torre Duodraco (cambia de pelaje según la estación). Además, un científico del Centro de Estudios Estacionales de la Ruta 6 te regala un Deerling con habilidad oculta Dicha (también obtenible mediante crianza).',
        'locations': [
            {'area': 'Ruta 6 (Centro de Estudios Estacionales)', 'method': 'Regalo del juego (Científico • con habilidad oculta Dicha)'},
            DAYCARE_LOCATION
        ]
    },
    129: {
        'type': 'gift',
        'badge_label': 'Regalo del juego',
        'badge_color': 'sky',
        'summary': 'Comprado por 500 ₽ al vendedor de Magikarp en el Puente Progreso al Nv. 5 (también obtenible mediante crianza).',
        'locations': [
            {'area': 'Puente Progreso', 'method': 'Regalo del juego (compra por 500 ₽ al vendedor, Nv. 5)'},
            DAYCARE_LOCATION
        ]
    },
    443: {
        'type': 'gift',
        'badge_label': 'Variocolor / Regalo',
        'badge_color': 'rose',
        'summary': 'Regalo variocolor garantizado al Nv. 1 del Entrenador Pokémon Guayo en la casa de Mirto en Pueblo Ocre tras superar las 10 áreas del Rascacielos Negro (exclusivo de Pokémon Negro 2; también por crianza).',
        'locations': [
            {'area': 'Pueblo Ocre (Casa de Mirto)', 'method': 'Regalo del juego (Guayo • Gible variocolor Nv. 1 tras superar Rascacielos Negro)'},
            DAYCARE_LOCATION
        ]
    },
    440: {
        'type': 'gift',
        'badge_label': 'Huevo Regalo',
        'badge_color': 'pink',
        'summary': 'Eclosiona del Huevo entregado por un Criapokémon en el acceso oeste de Ciudad Esmalte (hacia el Bosque Azulejo); también obtenible mediante crianza de Chansey o Blissey equipado con Incienso Duplo.',
        'locations': [
            {'area': 'Ciudad Esmalte (Acceso Oeste)', 'method': 'Huevo regalo de Criapokémon'},
            DAYCARE_LOCATION
        ]
    },

    # Estáticos especiales y variocolores
    612: {
        'type': 'wild',
        'badge_label': 'Variocolor / Nivel',
        'badge_color': 'rose',
        'summary': 'Evoluciona de Fraxure al Nv. 48. Además, aparece como encuentro estático variocolor garantizado al Nv. 60 en la Reserva Natural (accesible en avión desde Ciudad Loza tras ver las 300 especies de la Pokédex Regional de Teselia).',
        'locations': [
            {'area': 'Reserva Natural', 'method': 'Encuentro estático variocolor garantizado (Nv. 60)'}
        ]
    },
    630: {
        'type': 'wild',
        'badge_label': 'Estático / Nivel',
        'badge_color': 'purple',
        'summary': 'Evoluciona de Vullaby al Nv. 54. Además, aparece como encuentro estático semanal todos los jueves en la Ruta 4 al Nv. 25 con habilidad oculta Armadura Frágil (exclusivo de Pokémon Negro 2).',
        'locations': [
            {'area': 'Ruta 4', 'method': 'Encuentro estático semanal (Jueves, Nv. 25 con Armadura Frágil)'}
        ]
    },
    637: {
        'type': 'wild',
        'badge_label': 'Estático / Nivel',
        'badge_color': 'amber',
        'summary': 'Evoluciona de Larvesta al Nv. 59. Además, aparece como encuentro estático al Nv. 35 en la planta más profunda del Castillo Ancestral (accesible desde el Pasadizo Ancestral tras obtener la Medalla Temblor; reaparece al Nv. 65 en post-Liga si lo debilitaste).',
        'locations': [
            {'area': 'Castillo Ancestral (Planta más profunda)', 'method': 'Encuentro estático (Nv. 35 historia / Nv. 65 post-Liga)'}
        ]
    },
    593: {
        'type': 'wild',
        'badge_label': 'Estático / Salvaje',
        'badge_color': 'sky',
        'summary': 'Evoluciona de Frillish al Nv. 40 y aparece en sombras del agua en Bahía Arenisca, Ruta 4, Ruta 17, Ruta 18 y Ciudad Hormigón. Además, un Jellicent macho aparece como estático semanal todos los lunes en Bahía Arenisca (Nv. 40, habilidad oculta Humedad).',
        'locations': [
            {'area': 'Bahía Arenisca', 'method': 'Encuentro estático semanal (Lunes, macho Nv. 40 con Humedad)'}
        ]
    },
    558: {
        'type': 'wild',
        'badge_label': 'Estático / Salvaje',
        'badge_color': 'amber',
        'summary': 'Evoluciona de Dwebble al Nv. 34 y aparece salvaje en la Gruta Marina (P1 y S1). Un Crustle bloquea el paso en la Gruta Marina y despierta como encuentro estático al usar la Acromáquina entregada por Acromo.',
        'locations': [
            {'area': 'Gruta Marina (P1)', 'method': 'Encuentro estático (despertar con Acromáquina de Acromo)'}
        ]
    },
    550: {
        'type': 'wild',
        'badge_label': 'Salvaje / Forma',
        'badge_color': 'sky',
        'summary': 'Forma Raya Roja salvaje de forma común haciendo Surf y pescando con Supercaña por toda Teselia (la Forma Raya Azul aparece rara vez al 5% en sombras del agua). También obtenible mediante crianza.',
        'locations': [DAYCARE_LOCATION]
    },

    # Intercambios NPC estándar de Pokémon Negro 2
    548: {
        'type': 'trade_npc',
        'badge_label': 'Intercambio NPC',
        'badge_color': 'emerald',
        'summary': 'En Pokémon Negro 2, una entrenadora en la Ruta 4 cambia su Petilil (Nv. 20, mote «Pettulip», EO: Lilly) por tu Cottonee salvaje (también obtenible mediante crianza).',
        'locations': [
            {'area': 'Ruta 4', 'method': 'Intercambio NPC por Cottonee (mote «Pettulip», Nv. 20)'},
            DAYCARE_LOCATION
        ]
    },
    526: {
        'type': 'trade_npc',
        'badge_label': 'Intercambio NPC',
        'badge_color': 'indigo',
        'summary': 'Evoluciona de Boldore por intercambio. Además, un Montañero en una casa de la Ruta 7 te entrega directamente un Gigalith (Nv. 35) a cambio de un Emolga.',
        'locations': [
            {'area': 'Ruta 7', 'method': 'Intercambio NPC por Emolga (Nv. 35)'}
        ]
    },
    465: {
        'type': 'wild',
        'badge_label': 'Salvaje / Intercambio',
        'badge_color': 'emerald',
        'summary': 'Evoluciona de Tangela al subir de nivel con Poder Pasado y aparece en hierba movediza del Boquete Gigante. Además, un NPC en Ciudad Marga te entrega un Tangrowth (Nv. 45) a cambio de un Mantine.',
        'locations': [
            {'area': 'Ciudad Marga', 'method': 'Intercambio NPC por Mantine (Nv. 45)'}
        ]
    },
    424: {
        'type': 'trade_npc',
        'badge_label': 'Intercambio NPC',
        'badge_color': 'indigo',
        'summary': 'Evoluciona de Aipom al subir de nivel con Doble Golpe. En Pueblo Terracota (post-Liga), la Chica Corina te entrega un Ambipom (Nv. 40) a cambio de un Excadrill.',
        'locations': [
            {'area': 'Pueblo Terracota', 'method': 'Intercambio NPC con Chica Corina por Excadrill (Nv. 40)'}
        ]
    },
    65: {
        'type': 'trade_npc',
        'badge_label': 'Intercambio NPC',
        'badge_color': 'indigo',
        'summary': 'Evoluciona de Kadabra por intercambio. En Pueblo Terracota (post-Liga), la Chica Corina te entrega un Alakazam (Nv. 40) a cambio de un Hippowdon.',
        'locations': [
            {'area': 'Pueblo Terracota', 'method': 'Intercambio NPC con Chica Corina por Hippowdon (Nv. 40)'}
        ]
    },
    479: {
        'type': 'trade_npc',
        'badge_label': 'Intercambio NPC',
        'badge_color': 'amber',
        'summary': 'Una Científica en la autocaravana de la Ruta 15 te entrega un Rotom (Nv. 60) a cambio de un Ditto (también obtenible mediante crianza). Sus formas alternas se activan en las cajas del Centro Comercial R9.',
        'locations': [
            {'area': 'Ruta 15 (Autocaravana)', 'method': 'Intercambio NPC con Científica por Ditto (Nv. 60)'},
            DAYCARE_LOCATION
        ]
    },

    # Intercambios especiales de Belinda (Rizzo) y Julián (Nanci) en Ciudad Mayólica
    202: {
        'type': 'trade_npc',
        'badge_label': 'Intercambio NPC',
        'badge_color': 'indigo',
        'summary': 'Intercambio NPC en Ciudad Mayólica (Nv. 50 con habilidad oculta Telepatía) con la Presentadora Belinda (Rizzo) o el Presentador Julián (Nanci) tras devolver el Videomisor y completar 51 llamadas (también mediante crianza).',
        'locations': [
            {'area': 'Ciudad Mayólica (Noria)', 'method': 'Intercambio NPC con Belinda / Julián (Nv. 50, habilidad oculta)'},
            DAYCARE_LOCATION
        ]
    },
    280: {
        'type': 'trade_npc',
        'badge_label': 'Intercambio NPC',
        'badge_color': 'indigo',
        'summary': 'Intercambio NPC en Ciudad Mayólica (Nv. 50 con habilidad oculta Telepatía) con Belinda (Rizzo) o Julián (Nanci) tras completar las 51 llamadas del Videomisor (también mediante crianza).',
        'locations': [
            {'area': 'Ciudad Mayólica (Noria)', 'method': 'Intercambio NPC con Belinda / Julián (Nv. 50, habilidad oculta)'},
            DAYCARE_LOCATION
        ]
    },
    111: {
        'type': 'trade_npc',
        'badge_label': 'Intercambio NPC',
        'badge_color': 'indigo',
        'summary': 'Intercambio NPC en Ciudad Mayólica (Nv. 50 con habilidad oculta Audaz) con Belinda (Rizzo) o Julián (Nanci) tras completar las 51 llamadas del Videomisor (también mediante crianza).',
        'locations': [
            {'area': 'Ciudad Mayólica (Noria)', 'method': 'Intercambio NPC con Belinda / Julián (Nv. 50, habilidad oculta)'},
            DAYCARE_LOCATION
        ]
    },
    442: {
        'type': 'trade_npc',
        'badge_label': 'Intercambio NPC',
        'badge_color': 'indigo',
        'summary': 'Intercambio NPC en Ciudad Mayólica (Nv. 50 con habilidad oculta Allanamiento) con Belinda (Rizzo) o Julián (Nanci) tras completar las 51 llamadas del Videomisor (también mediante crianza).',
        'locations': [
            {'area': 'Ciudad Mayólica (Noria)', 'method': 'Intercambio NPC con Belinda / Julián (Nv. 50, habilidad oculta)'},
            DAYCARE_LOCATION
        ]
    },
    143: {
        'type': 'trade_npc',
        'badge_label': 'Intercambio NPC',
        'badge_color': 'indigo',
        'summary': 'Intercambio NPC en Ciudad Mayólica (Nv. 50 con habilidad oculta Gula) con Belinda (Rizzo) o Julián (Nanci) tras completar las 51 llamadas del Videomisor (también mediante crianza).',
        'locations': [
            {'area': 'Ciudad Mayólica (Noria)', 'method': 'Intercambio NPC con Belinda / Julián (Nv. 50, habilidad oculta)'},
            DAYCARE_LOCATION
        ]
    },
    327: {
        'type': 'trade_npc',
        'badge_label': 'Intercambio NPC',
        'badge_color': 'indigo',
        'summary': 'Intercambio NPC en Ciudad Mayólica (Nv. 50 con habilidad oculta Respondón) con Belinda (Rizzo) o Julián (Nanci) tras completar las 51 llamadas del Videomisor (también mediante crianza).',
        'locations': [
            {'area': 'Ciudad Mayólica (Noria)', 'method': 'Intercambio NPC con Belinda / Julián (Nv. 50, habilidad oculta)'},
            DAYCARE_LOCATION
        ]
    },
    175: {
        'type': 'trade_npc',
        'badge_label': 'Intercambio NPC',
        'badge_color': 'indigo',
        'summary': 'Intercambio NPC en Ciudad Mayólica (Nv. 50 con habilidad oculta Afortunado) con Belinda (Rizzo) o Julián (Nanci) tras completar las 51 llamadas del Videomisor (también mediante crianza).',
        'locations': [
            {'area': 'Ciudad Mayólica (Noria)', 'method': 'Intercambio NPC con Belinda / Julián (Nv. 50, habilidad oculta)'},
            DAYCARE_LOCATION
        ]
    },
    422: {
        'type': 'trade_npc',
        'badge_label': 'Intercambio NPC',
        'badge_color': 'indigo',
        'summary': 'Intercambio NPC en Ciudad Mayólica (Nv. 50 con habilidad oculta Poder Arena): Shellos Mar Oeste con Belinda (Rizzo) o Shellos Mar Este con Julián (Nanci) tras 51 llamadas del Videomisor (también mediante crianza).',
        'locations': [
            {'area': 'Ciudad Mayólica (Noria)', 'method': 'Intercambio NPC con Belinda (Mar Oeste) / Julián (Mar Este)'},
            DAYCARE_LOCATION
        ]
    },
    52: {
        'type': 'trade_npc',
        'badge_label': 'Intercambio NPC',
        'badge_color': 'indigo',
        'summary': 'Intercambio NPC en Ciudad Mayólica exclusivo de la Presentadora Belinda (protagonista Rizzo, Nv. 50 con habilidad oculta Nerviosismo) tras 51 llamadas del Videomisor (también mediante crianza).',
        'locations': [
            {'area': 'Ciudad Mayólica (Noria)', 'method': 'Intercambio NPC con Belinda (protagonista Rizzo, Nv. 50)'},
            DAYCARE_LOCATION
        ]
    },
    303: {
        'type': 'trade_npc',
        'badge_label': 'Intercambio NPC',
        'badge_color': 'indigo',
        'summary': 'Intercambio NPC en Ciudad Mayólica exclusivo de la Presentadora Belinda (protagonista Rizzo, Nv. 50 con habilidad oculta Potencia Bruta) tras 51 llamadas del Videomisor (también mediante crianza).',
        'locations': [
            {'area': 'Ciudad Mayólica (Noria)', 'method': 'Intercambio NPC con Belinda (protagonista Rizzo, Nv. 50)'},
            DAYCARE_LOCATION
        ]
    },
    216: {
        'type': 'trade_npc',
        'badge_label': 'Intercambio NPC',
        'badge_color': 'indigo',
        'summary': 'Intercambio NPC en Ciudad Mayólica exclusivo de la Presentadora Belinda (protagonista Rizzo, Nv. 50 con habilidad oculta Recogemiel) tras 51 llamadas del Videomisor (también mediante crianza).',
        'locations': [
            {'area': 'Ciudad Mayólica (Noria)', 'method': 'Intercambio NPC con Belinda (protagonista Rizzo, Nv. 50)'},
            DAYCARE_LOCATION
        ]
    },
    56: {
        'type': 'trade_npc',
        'badge_label': 'Intercambio NPC',
        'badge_color': 'indigo',
        'summary': 'Intercambio NPC en Ciudad Mayólica exclusivo del Presentador Julián (protagonista Nanci, Nv. 50 con habilidad oculta Competitivo) tras 51 llamadas del Videomisor (también mediante crianza).',
        'locations': [
            {'area': 'Ciudad Mayólica (Noria)', 'method': 'Intercambio NPC con Julián (protagonista Nanci, Nv. 50)'},
            DAYCARE_LOCATION
        ]
    },
    302: {
        'type': 'trade_npc',
        'badge_label': 'Intercambio NPC',
        'badge_color': 'indigo',
        'summary': 'Intercambio NPC en Ciudad Mayólica exclusivo del Presentador Julián (protagonista Nanci, Nv. 50 con habilidad oculta Bromista) tras 51 llamadas del Videomisor (también mediante crianza).',
        'locations': [
            {'area': 'Ciudad Mayólica (Noria)', 'method': 'Intercambio NPC con Julián (protagonista Nanci, Nv. 50)'},
            DAYCARE_LOCATION
        ]
    },
    231: {
        'type': 'trade_npc',
        'badge_label': 'Intercambio NPC',
        'badge_color': 'indigo',
        'summary': 'Intercambio NPC en Ciudad Mayólica exclusivo del Presentador Julián (protagonista Nanci, Nv. 50 con habilidad oculta Velo Arena) tras 51 llamadas del Videomisor (también mediante crianza).',
        'locations': [
            {'area': 'Ciudad Mayólica (Noria)', 'method': 'Intercambio NPC con Julián (protagonista Nanci, Nv. 50)'},
            DAYCARE_LOCATION
        ]
    },

    # Fósiles de Teselia (Aloe en Museo de Ciudad Esmalte post-Liga — elección mutua)
    564: {
        'type': 'fossil',
        'badge_label': 'Fósil Tapa',
        'badge_color': 'blue',
        'summary': 'Revivir en el Museo de Ciudad Esmalte el Fósil Tapa entregado por Aloe en el post-Liga (elección única frente al Fósil Pluma por partida; también obtenible mediante crianza).',
        'locations': [
            {'area': 'Museo de Ciudad Esmalte', 'method': 'Restauración de Fósil Tapa'},
            DAYCARE_LOCATION
        ]
    },
    566: {
        'type': 'fossil',
        'badge_label': 'Fósil Pluma',
        'badge_color': 'amber',
        'summary': 'Revivir en el Museo de Ciudad Esmalte el Fósil Pluma entregado por Aloe en el post-Liga (elección única frente al Fósil Tapa por partida; también obtenible mediante crianza).',
        'locations': [
            {'area': 'Museo de Ciudad Esmalte', 'method': 'Restauración de Fósil Pluma'},
            DAYCARE_LOCATION
        ]
    },

    # Fósiles clásicos de Gen 1–4 (Monte Tuerca post-Liga + Tienda de Antigüedades Galería Unión -> Museo Ciudad Esmalte)
    138: {
        'type': 'fossil',
        'badge_label': 'Fósil Hélix',
        'badge_color': 'blue',
        'summary': 'Restaurar en el Museo de Ciudad Esmalte el Fósil Hélix obtenido al azar del obrero diario del Monte Tuerca (post-Liga) o en la Tienda de Antigüedades de la Galería Unión (también por crianza).',
        'locations': [
            {'area': 'Museo de Ciudad Esmalte', 'method': 'Restauración de Fósil Hélix'},
            DAYCARE_LOCATION
        ]
    },
    140: {
        'type': 'fossil',
        'badge_label': 'Fósil Domo',
        'badge_color': 'blue',
        'summary': 'Restaurar en el Museo de Ciudad Esmalte el Fósil Domo obtenido al azar del obrero diario del Monte Tuerca (post-Liga) o en la Tienda de Antigüedades de la Galería Unión (también por crianza).',
        'locations': [
            {'area': 'Museo de Ciudad Esmalte', 'method': 'Restauración de Fósil Domo'},
            DAYCARE_LOCATION
        ]
    },
    142: {
        'type': 'fossil',
        'badge_label': 'Ámbar Viejo',
        'badge_color': 'amber',
        'summary': 'Restaurar en el Museo de Ciudad Esmalte el Ámbar Viejo obtenido al azar del obrero diario del Monte Tuerca (post-Liga) o en la Tienda de Antigüedades de la Galería Unión (también por crianza).',
        'locations': [
            {'area': 'Museo de Ciudad Esmalte', 'method': 'Restauración de Ámbar Viejo'},
            DAYCARE_LOCATION
        ]
    },
    345: {
        'type': 'fossil',
        'badge_label': 'Fósil Raíz',
        'badge_color': 'emerald',
        'summary': 'Restaurar en el Museo de Ciudad Esmalte el Fósil Raíz obtenido al azar del obrero diario del Monte Tuerca (post-Liga) o en la Tienda de Antigüedades de la Galería Unión (también por crianza).',
        'locations': [
            {'area': 'Museo de Ciudad Esmalte', 'method': 'Restauración de Fósil Raíz'},
            DAYCARE_LOCATION
        ]
    },
    347: {
        'type': 'fossil',
        'badge_label': 'Fósil Garra',
        'badge_color': 'amber',
        'summary': 'Restaurar en el Museo de Ciudad Esmalte el Fósil Garra obtenido al azar del obrero diario del Monte Tuerca (post-Liga) o en la Tienda de Antigüedades de la Galería Unión (también por crianza).',
        'locations': [
            {'area': 'Museo de Ciudad Esmalte', 'method': 'Restauración de Fósil Garra'},
            DAYCARE_LOCATION
        ]
    },
    408: {
        'type': 'fossil',
        'badge_label': 'Fósil Cráneo',
        'badge_color': 'blue',
        'summary': 'Restaurar en el Museo de Ciudad Esmalte el Fósil Cráneo (obrero diario del Monte Tuerca o Tienda de Antigüedades de la Galería Unión). Además, el Presentador Julián (protagonista Nanci) lo ofrece por intercambio NPC en Ciudad Mayólica (también por crianza).',
        'locations': [
            {'area': 'Museo de Ciudad Esmalte', 'method': 'Restauración de Fósil Cráneo'},
            DAYCARE_LOCATION
        ]
    },
    410: {
        'type': 'fossil',
        'badge_label': 'Fósil Coraza',
        'badge_color': 'zinc',
        'summary': 'Restaurar en el Museo de Ciudad Esmalte el Fósil Coraza (obrero diario del Monte Tuerca o Tienda de Antigüedades de la Galería Unión). Además, la Presentadora Belinda (protagonista Rizzo) lo ofrece por intercambio NPC en Ciudad Mayólica (también por crianza).',
        'locations': [
            {'area': 'Museo de Ciudad Esmalte', 'method': 'Restauración de Fósil Coraza'},
            DAYCARE_LOCATION
        ]
    },

    # Legendarios capturables en Pokémon Negro 2
    377: {
        'type': 'legendary',
        'badge_label': 'Legendario',
        'badge_color': 'amber',
        'summary': 'Encuentro fijo al Nv. 65 en las Ruinas Subterráneas (accediendo desde el Túnel Yakón en el post-Liga) usando la Clave Pico Roca tras resolver el acertijo de los pasos.',
        'locations': [
            {'area': 'Ruinas Subterráneas (Cámara Pico Roca)', 'method': 'Encuentro fijo a Nivel 65 (Clave Pico Roca)'}
        ]
    },
    379: {
        'type': 'legendary',
        'badge_label': 'Exclusivo Negro 2',
        'badge_color': 'slate',
        'summary': 'Encuentro fijo al Nv. 65 en las Ruinas Subterráneas tras capturar a Regirock y activar la Clave Hierro en el Sistema Clave (desbloqueada de forma nativa en Pokémon Negro 2).',
        'locations': [
            {'area': 'Ruinas Subterráneas (Cámara Hierro)', 'method': 'Encuentro fijo a Nivel 65 (Clave Hierro)'}
        ]
    },
    381: {
        'type': 'legendary',
        'badge_label': 'Exclusivo Negro 2',
        'badge_color': 'sky',
        'summary': 'Encuentro fijo al Nv. 68 en el Solar de los Sueños en el post-Liga tras perseguirlo por sus ruinas (exclusivo de Pokémon Negro 2).',
        'locations': [
            {'area': 'Solar de los Sueños', 'method': 'Encuentro fijo a Nivel 68 (post-Liga)'}
        ]
    },
    480: {
        'type': 'legendary',
        'badge_label': 'Legendario',
        'badge_color': 'amber',
        'summary': 'Encuentro fijo al Nv. 65 frente a la entrada del Museo de Ciudad Esmalte tras el evento de la Prof. Encina en la Cueva Psique (Ruta 20).',
        'locations': [
            {'area': 'Museo de Ciudad Esmalte', 'method': 'Encuentro fijo a Nivel 65 (tras evento en Cueva Psique)'}
        ]
    },
    481: {
        'type': 'legendary',
        'badge_label': 'Legendario',
        'badge_color': 'pink',
        'summary': 'Encuentro fijo al Nv. 65 en la azotea de la Torre de los Cielos tras el evento de la Prof. Encina en la Cueva Psique (Ruta 20).',
        'locations': [
            {'area': 'Torre de los Cielos (Cima)', 'method': 'Encuentro fijo a Nivel 65 (tras evento en Cueva Psique)'}
        ]
    },
    482: {
        'type': 'legendary',
        'badge_label': 'Legendario',
        'badge_color': 'sky',
        'summary': 'Encuentro fijo al Nv. 65 en la Ruta 23 tras el evento de la Prof. Encina en la Cueva Psique (Ruta 20).',
        'locations': [
            {'area': 'Ruta 23', 'method': 'Encuentro fijo a Nivel 65 (tras evento en Cueva Psique)'}
        ]
    },
    485: {
        'type': 'legendary',
        'badge_label': 'Legendario',
        'badge_color': 'rose',
        'summary': 'Encuentro fijo al Nv. 68 en la cámara interior de la Montaña Reversia llevando la Piedra Magma recogida previamente en la Ruta 18 (post-Liga).',
        'locations': [
            {'area': 'Montaña Reversia (Interior)', 'method': 'Encuentro fijo a Nivel 68 (llevando Piedra Magma)'}
        ]
    },
    486: {
        'type': 'legendary',
        'badge_label': 'Legendario',
        'badge_color': 'amber',
        'summary': 'Encuentro fijo al Nv. 68 en el sótano S4 del Monte Tuerca (post-Liga) llevando en el equipo a Regirock, Regice y Registeel (requiere recibir la Clave Iceberg o a Regice desde Pokémon Blanco 2).',
        'locations': [
            {'area': 'Monte Tuerca (S4)', 'method': 'Encuentro fijo a Nivel 68 (llevando a Regirock, Regice y Registeel)'}
        ]
    },
    488: {
        'type': 'legendary',
        'badge_label': 'Legendario',
        'badge_color': 'pink',
        'summary': 'Encuentro fijo al Nv. 68 en el Puente Progreso (post-Liga) llevando la Pluma Lunar recogida en Villa Horroris.',
        'locations': [
            {'area': 'Puente Progreso', 'method': 'Encuentro fijo a Nivel 68 (llevando Pluma Lunar de Villa Horroris)'}
        ]
    },
    638: {
        'type': 'legendary',
        'badge_label': 'Legendario',
        'badge_color': 'teal',
        'summary': 'Encuentro fijo en la Ruta 13 al Nv. 45 durante la historia (o al Nv. 65 en el post-Liga si lo derrotaste anteriormente).',
        'locations': [
            {'area': 'Ruta 13', 'method': 'Encuentro fijo (Nv. 45 historia / Nv. 65 post-Liga)'}
        ]
    },
    639: {
        'type': 'legendary',
        'badge_label': 'Legendario',
        'badge_color': 'amber',
        'summary': 'Encuentro fijo en la Ruta 22 al Nv. 45 durante la historia (o al Nv. 65 en el post-Liga si lo derrotaste anteriormente).',
        'locations': [
            {'area': 'Ruta 22', 'method': 'Encuentro fijo (Nv. 45 historia / Nv. 65 post-Liga)'}
        ]
    },
    640: {
        'type': 'legendary',
        'badge_label': 'Legendario',
        'badge_color': 'emerald',
        'summary': 'Encuentro fijo en la Ruta 11 al Nv. 45 durante la historia (o al Nv. 65 en el post-Liga si lo derrotaste anteriormente).',
        'locations': [
            {'area': 'Ruta 11', 'method': 'Encuentro fijo (Nv. 45 historia / Nv. 65 post-Liga)'}
        ]
    },
    644: {
        'type': 'legendary',
        'badge_label': 'Exclusivo Negro 2',
        'badge_color': 'slate',
        'summary': 'Encuentro fijo al Nv. 70 en la cima de la Torre Duodraco (post-Liga) tras derrotar a N en el Palacio de N y recibir el Orbe Oscuro (exclusivo de Pokémon Negro 2; permite fusionar a Kyurem Negro).',
        'locations': [
            {'area': 'Torre Duodraco (Cima)', 'method': 'Encuentro fijo a Nivel 70 (Orbe Oscuro)'}
        ]
    },
    646: {
        'type': 'legendary',
        'badge_label': 'Legendario',
        'badge_color': 'cyan',
        'summary': 'Encuentro fijo al Nv. 70 en la Cueva Central del Boquete Gigante tras capturar a Zekrom en la Torre Duodraco. Al capturarlo o derrotarlo deja caer la Punta ADN para fusionarlo en Kyurem Negro.',
        'locations': [
            {'area': 'Boquete Gigante (Cueva Central)', 'method': 'Encuentro fijo a Nivel 70 (deja caer Punta ADN)'}
        ]
    },

    # Gen 5 no salvajes en B2W2 (RAdar Pokémon / intercambio Negro y Blanco / Eventos)
    494: {
        'type': 'mythical',
        'badge_label': 'Evento Singular',
        'badge_color': 'amber',
        'summary': 'Inaccesible en estado salvaje en Pokémon Negro 2. Se obtiene mediante intercambio desde Pokémon Negro / Blanco (Ticket Libertad / Película 14) o distribuciones oficiales de 5.ª Generación.',
        'locations': [
            {'area': 'Intercambio desde Pokémon Negro / Blanco', 'method': 'Evento oficial de 5.ª Generación'}
        ]
    },
    641: {
        'type': 'event',
        'badge_label': 'RAdar / Gen 5',
        'badge_color': 'emerald',
        'summary': 'No aparece salvaje en Pokémon Negro 2. Se obtiene en su Forma Tótem mediante la aplicación RAdar Pokémon (Nintendo 3DS) o mediante intercambio desde Pokémon Negro. Alterna de forma con el Espejo Veraz.',
        'locations': [
            {'area': 'RAdar Pokémon (Nintendo 3DS)', 'method': 'Transferencia en Forma Tótem (habilidad oculta)'},
            {'area': 'Intercambio desde Pokémon Negro', 'method': 'Intercambio local Gen 5'}
        ]
    },
    642: {
        'type': 'event',
        'badge_label': 'RAdar / Gen 5',
        'badge_color': 'sky',
        'summary': 'No aparece salvaje en Pokémon Negro 2. Se obtiene en su Forma Tótem mediante la aplicación RAdar Pokémon (Nintendo 3DS) o mediante intercambio desde Pokémon Blanco. Alterna de forma con el Espejo Veraz.',
        'locations': [
            {'area': 'RAdar Pokémon (Nintendo 3DS)', 'method': 'Transferencia en Forma Tótem (habilidad oculta)'},
            {'area': 'Intercambio desde Pokémon Blanco', 'method': 'Intercambio local Gen 5'}
        ]
    },
    645: {
        'type': 'event',
        'badge_label': 'RAdar / Gen 5',
        'badge_color': 'amber',
        'summary': 'No aparece salvaje en Pokémon Negro 2. Se obtiene en su Forma Tótem mediante RAdar Pokémon (Nintendo 3DS; llevarlo al Santuario Abundancia desbloquea el Espejo Veraz) o por intercambio desde Negro/Blanco.',
        'locations': [
            {'area': 'RAdar Pokémon (Nintendo 3DS)', 'method': 'Transferencia en Forma Tótem (desbloquea Espejo Veraz)'},
            {'area': 'Intercambio desde Pokémon Negro / Blanco', 'method': 'Intercambio local Gen 5'}
        ]
    },
    647: {
        'type': 'mythical',
        'badge_label': 'Evento Singular',
        'badge_color': 'sky',
        'summary': 'Inaccesible en estado salvaje; obtenible mediante distribuciones oficiales de evento (ej. Wi-Fi Invierno 2013) o intercambio. En la Arboleda Promesa aprende Sable Místico junto a Cobalion, Terrakion y Virizion para adoptar la Forma Brío.',
        'locations': [
            {'area': 'Evento Oficial de Distribución', 'method': 'Regalo Misterioso (ej. INV2013)'},
            {'area': 'Arboleda Promesa', 'method': 'Evento del juego para aprender Sable Místico y cambiar a Forma Brío'}
        ]
    },
    648: {
        'type': 'mythical',
        'badge_label': 'Evento Singular',
        'badge_color': 'pink',
        'summary': 'Inaccesible en estado salvaje; obtenible mediante distribuciones oficiales de evento (ej. Primavera 2013) o intercambio. En la cafetería La melodía del descanso de Ciudad Porcelana aprende Canto Arcaico para cambiar a Forma Danza.',
        'locations': [
            {'area': 'Evento Oficial de Distribución', 'method': 'Regalo Misterioso (ej. PRI2013)'},
            {'area': 'Ciudad Porcelana (La melodía del descanso)', 'method': 'Músico enseña Canto Arcaico'}
        ]
    },
    649: {
        'type': 'mythical',
        'badge_label': 'Evento Singular',
        'badge_color': 'purple',
        'summary': 'Inaccesible en estado salvaje; obtenible mediante distribuciones oficiales de evento (ej. Genesect Plasma, 2012) o intercambio. En el Laboratorio P+P, un Montañero entrega los 4 cartuchos tras combatir llevando a Genesect.',
        'locations': [
            {'area': 'Evento Oficial de Distribución', 'method': 'Regalo Misterioso (ej. Genesect Plasma)'},
            {'area': 'Laboratorio P+P', 'method': 'Entrega de PiroROM, FulgoROM, HidroROM y CrioROM tras combate'}
        ]
    },
}

# Especies obtenibles exclusivamente por crianza en Pokémon Negro 2
BREEDING_PARENTS_BLACK2 = {
    13:  ("Beedrill (Claro Oculto del Bosque Azulejo Interior; exclusivo de Negro 2)", "Beedrill"),
    21:  ("Fearow (manada diaria en la Ruta 15)", "Fearow"),
    63:  ("Alakazam (intercambio NPC con la Chica Corina en Pueblo Terracota)", "Alakazam"),
    96:  ("Hypno (manada diaria en el Solar de los Sueños)", "Hypno"),
    161: ("Furret (manada diaria en la Ruta 7)", "Furret"),
    163: ("Noctowl (salvaje en Santuario Abundancia)", "Noctowl"),
    167: ("Ariados (manada diaria en la Ruta 22; exclusivo de Negro 2)", "Ariados"),
    173: ("Clefairy o Clefable (salvajes en Boquete Gigante)", "Clefairy / Clefable"),
    174: ("Jigglypuff o Wigglytuff (salvajes en Ruta 1 y Ruta 2)", "Jigglypuff / Wigglytuff"),
    190: ("Ambipom (intercambio NPC con la Chica Corina en Pueblo Terracota)", "Ambipom"),
    194: ("Quagsire (manada diaria en la Ruta 8)", "Quagsire"),
    209: ("Granbull (Claro Oculto de la Ruta 2)", "Granbull"),
    220: ("Piloswine o Mamoswine (salvajes en Boquete Gigante)", "Piloswine / Mamoswine"),
    246: ("Pupitar o Tyranitar (salvajes en Ruta 15)", "Pupitar / Tyranitar"),
    270: ("Lombre (Claro Oculto del lago en la Ruta 3)", "Lombre"),
    273: ("Nuzleaf o Shiftry (salvajes en Reserva Natural)", "Nuzleaf / Shiftry"),
    276: ("Swellow (manada diaria en la Ruta 13 o salvaje en Boquete Gigante)", "Swellow"),
    278: ("Pelipper (salvaje en Ruta 13, Ruta 22, Bahía Arenisca y Claro Oculto de Ruta 22)", "Pelipper"),
    283: ("Masquerain (manada diaria en la Ruta 11)", "Masquerain"),
    285: ("Breloom (Claro Oculto del Bosque Azulejo Interior)", "Breloom"),
    287: ("Vigoroth o Slaking (salvajes en Bosque Azulejo)", "Vigoroth / Slaking"),
    296: ("Hariyama (Claro Oculto del Bosque Azulejo Exterior)", "Hariyama"),
    307: ("Medicham (Claro Oculto del Bosque Azulejo Exterior)", "Medicham"),
    309: ("Manectric (Claro Oculto norte de la Ruta 3)", "Manectric"),
    314: ("Volbeat con Ditto (manada diaria en Ruta 3; en 5.ª Gen sus huevos producen Illumise o Volbeat al 50 %)", "Volbeat + Ditto (50 % por huevo)"),
    316: ("Swalot (manada diaria en la Ruta 9)", "Swalot"),
    331: ("Cacturne (manada diaria en la Montaña Reversia)", "Cacturne"),
    353: ("Banette (salvaje en Villa Horroris)", "Banette"),
    360: ("Wobbuffet equipado con Incienso Suave (intercambio NPC con Belinda/Julián en Ciudad Mayólica)", "Wobbuffet (con Incienso Suave)"),
    374: ("Metang o Metagross (salvajes en Boquete Gigante)", "Metang / Metagross"),
    399: ("Bibarel (salvaje en Puente Villa y Claro Oculto de la Ruta 3)", "Bibarel"),
    406: ("Roselia o Roserade equipado con Incienso Floral (salvajes en Ruta 12 y Bosque de los Perdidos)", "Roselia / Roserade (con Incienso Floral)"),
    438: ("Sudowoodo equipado con Incienso Roca (manada diaria en Ruta 20; exclusivo de Negro 2)", "Sudowoodo (con Incienso Roca)"),
    446: ("Snorlax equipado con Incienso Lento (intercambio NPC con Belinda/Julián en Ciudad Mayólica)", "Snorlax (con Incienso Lento)"),
    449: ("Hippowdon (manada diaria en la Zona Desierto)", "Hippowdon"),
    522: ("Zebstrika (salvaje en Ruta 7 y Claro Oculto de la Ruta 3)", "Zebstrika"),
    535: ("Palpitoad o Seismitoad (salvajes en Ciudad Teja, Ruta 8 y Pantano Teja)", "Palpitoad / Seismitoad"),
    582: ("Vanillish o Vanilluxe (salvajes en Boquete Gigante, Monte Tuerca y Torre Duodraco)", "Vanillish / Vanilluxe"),
    622: ("Golurk (salvaje en Torre Duodraco)", "Golurk"),
    633: ("Zweilous (salvaje en Calle Victoria)", "Zweilous"),
    636: ("Volcarona (estático en Castillo Ancestral)", "Volcarona"),
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

_POSTGAME_FOSSIL_B2_TEXT = (
    "En el post-Liga, el obrero del Monte Tuerca entrega aleatoriamente un fósil clásico al día (entre los 7 de Gen 1–4). "
    "Además, pueden obtenerse abriendo rocas y cajas en la Tienda de Antigüedades de la Galería Unión; "
    "todos se restauran en el Museo de Ciudad Esmalte."
)

_BELINDA_ONLY_NOTE = {
    "title": "Exclusivo por Protagonista • Presentadora Belinda",
    "text": (
        "En Ciudad Mayólica, solo aparece si elegiste al protagonista masculino (Rizzo). "
        "Tras devolver el Objeto perdido (Videomisor) y completar 51 llamadas, la Presentadora Belinda lo intercambia "
        "al Nv. 50 con su habilidad oculta junto a la noria del Parque de Atracciones."
    ),
    "tag": "Rizzo / Belinda",
    "icon": "/media/items/linking-cord.png",
}

_JULIAN_ONLY_NOTE = {
    "title": "Exclusivo por Protagonista • Presentador Julián",
    "text": (
        "En Ciudad Mayólica, solo aparece si elegiste a la protagonista femenina (Nanci). "
        "Tras devolver el Objeto perdido (Videomisor) y completar 51 llamadas, el Presentador Julián lo intercambia "
        "al Nv. 50 con su habilidad oculta junto a la noria del Parque de Atracciones."
    ),
    "tag": "Nanci / Julián",
    "icon": "/media/items/linking-cord.png",
}

_DREAM_RADAR_ICON = "/media/items/reveal-glass.png"
DREAM_RADAR_POKEMON_BLACK2 = {
    # Disponibles desde el inicio (5)
    333: {"method": "Transferencia directa (Habilidad Oculta)", "note": "Disponible desde el inicio en RAdar Pokémon (Nintendo 3DS) en nubes de gotas oníricas rosas y verdes. Incluye habilidad oculta Aclimatación."},
    425: {"method": "Transferencia directa (Habilidad Oculta)", "note": "Disponible desde el inicio en RAdar Pokémon (Nintendo 3DS) en nubes de gotas oníricas rosas y verdes. Incluye habilidad oculta Ímpetu Ardiente."},
    447: {"method": "Transferencia directa (Habilidad Oculta)", "note": "Disponible desde el inicio en RAdar Pokémon (Nintendo 3DS) en nubes de gotas oníricas rosas y verdes. Incluye habilidad oculta Bromista."},
    517: {"method": "Transferencia directa (Habilidad Oculta)", "note": "Disponible desde el inicio en RAdar Pokémon (Nintendo 3DS) en nubes de gotas oníricas rosas. Incluye habilidad oculta Telepatía."},
    561: {"method": "Transferencia directa (Habilidad Oculta)", "note": "Disponible desde el inicio en RAdar Pokémon (Nintendo 3DS) en nubes de gotas oníricas rosas y verdes. Incluye habilidad oculta Cromolente."},
    # Desbloqueados tras capturar a Tornadus (2)
    174: {"method": "Transferencia directa (Habilidad Oculta)", "note": "Se desbloquea en RAdar Pokémon (Nintendo 3DS) tras capturar a Tornadus (Forma Tótem), apareciendo en nubes de gotas oníricas verdes y azules. Incluye habilidad oculta Compiescolta."},
    213: {"method": "Transferencia directa (Habilidad Oculta)", "note": "Se desbloquea en RAdar Pokémon (Nintendo 3DS) tras capturar a Tornadus (Forma Tótem), apareciendo en nubes de gotas oníricas rosas y verdes. Incluye habilidad oculta Respondón."},
    # Desbloqueados tras capturar a Thundurus (4)
    120: {"method": "Transferencia directa (Habilidad Oculta)", "note": "Se desbloquea en RAdar Pokémon (Nintendo 3DS) tras capturar a Thundurus (Forma Tótem), apareciendo en nubes de gotas oníricas rosas y naranjas. Incluye habilidad oculta Cálculo Final."},
    137: {"method": "Transferencia directa (Habilidad Oculta)", "note": "Se desbloquea en RAdar Pokémon (Nintendo 3DS) tras capturar a Thundurus (Forma Tótem), apareciendo en nubes de gotas oníricas rosas y naranjas. Incluye habilidad oculta Cálculo Final."},
    280: {"method": "Transferencia directa (Habilidad Oculta)", "note": "Se desbloquea en RAdar Pokémon (Nintendo 3DS) tras capturar a Thundurus (Forma Tótem), apareciendo en nubes de gotas oníricas verdes y naranjas. Incluye habilidad oculta Telepatía."},
    436: {"method": "Transferencia directa (Habilidad Oculta)", "note": "Se desbloquea en RAdar Pokémon (Nintendo 3DS) tras capturar a Thundurus (Forma Tótem), apareciendo en nubes de gotas oníricas rosas y verdes. Incluye habilidad oculta Metal Pesado."},
    # Desbloqueados tras capturar a Landorus (4)
    175: {"method": "Transferencia directa (Habilidad Oculta)", "note": "Se desbloquea en RAdar Pokémon (Nintendo 3DS) tras capturar a Landorus (Forma Tótem), apareciendo en nubes de gotas oníricas rosas, verdes y azules. Incluye habilidad oculta Afortunado."},
    238: {"method": "Transferencia directa (Habilidad Oculta)", "note": "Se desbloquea en RAdar Pokémon (Nintendo 3DS) tras capturar a Landorus (Forma Tótem), apareciendo en nubes de gotas oníricas azules. Incluye habilidad oculta Hidratación."},
    442: {"method": "Transferencia directa (Habilidad Oculta)", "note": "Se desbloquea en RAdar Pokémon (Nintendo 3DS) tras capturar a Landorus (Forma Tótem), apareciendo en nubes de gotas oníricas rosas y azules. Incluye habilidad oculta Allanamiento."},
    479: {"method": "Transferencia directa (Levitación)", "note": "Se desbloquea en RAdar Pokémon (Nintendo 3DS) tras capturar a Landorus (Forma Tótem), apareciendo en nubes de gotas oníricas rosas y naranjas en su forma base con Levitación."},
    # Fuerzas de la Naturaleza (3)
    641: {"method": "Transferencia directa (Habilidad Oculta)", "note": "Jefe inicial de RAdar Pokémon (Nintendo 3DS) mediante la Lente Maravilla α: se captura en su Forma Tótem con habilidad oculta Regeneración tras reunir 400 gotas oníricas."},
    642: {"method": "Transferencia directa (Habilidad Oculta)", "note": "Segundo jefe de RAdar Pokémon (Nintendo 3DS) mediante la Lente Maravilla β: se captura en su Forma Tótem con habilidad oculta Absorbe Elec tras reunir 1.500 gotas oníricas."},
    645: {"method": "Transferencia directa (Habilidad Oculta)", "note": "Tercer jefe de RAdar Pokémon (Nintendo 3DS) mediante la Lente Maravilla γ: se captura en su Forma Tótem con habilidad oculta Intimidación tras reunir 3.000 gotas oníricas. Llevarlo al Santuario Abundancia desbloquea el Espejo Veraz."},
    # Lentes Especiales por código secreto en pantalla de título (3)
    374: {"method": "Transferencia directa (Habilidad Oculta)", "note": "Modo especial Lente Especial A de RAdar Pokémon (Nintendo 3DS): se desbloquea introduciendo el código secreto en la pantalla de título (Arriba, Derecha, Abajo, Izquierda, X, R, L). Incluye habilidad oculta Metal Liviano."},
    79:  {"method": "Transferencia directa (Habilidad Oculta)", "note": "Modo especial Lente Especial B de RAdar Pokémon (Nintendo 3DS): se desbloquea introduciendo el código secreto en la pantalla de título tras capturar a Tornadus (Arriba, Abajo, Derecha, Izquierda, Y, R, L). Incluye habilidad oculta Regeneración."},
    163: {"method": "Transferencia directa (Habilidad Oculta)", "note": "Modo especial Lente Especial C de RAdar Pokémon (Nintendo 3DS): se desbloquea introduciendo el código secreto en la pantalla de título tras capturar a Thundurus (Arriba, Izquierda, Abajo, Derecha, L, R, X, Y). Incluye habilidad oculta Cromolente."},
    # Lentes de 4.ª Generación con cartucho DS insertado en 3DS tras vencer a Landorus (5)
    483: {"method": "Transferencia directa (Habilidad Oculta)", "note": "Modo especial Lente Temporal de RAdar Pokémon (Nintendo 3DS): se desbloquea tras vencer a Landorus jugando con el cartucho de Pokémon Diamante insertado en la consola. Incluye habilidad oculta Telepatía."},
    484: {"method": "Transferencia directa (Habilidad Oculta)", "note": "Modo especial Lente Espacial de RAdar Pokémon (Nintendo 3DS): se desbloquea tras vencer a Landorus jugando con el cartucho de Pokémon Perla insertado en la consola. Incluye habilidad oculta Telepatía."},
    487: {"method": "Transferencia directa (Habilidad Oculta)", "note": "Modo especial Lente Renegada de RAdar Pokémon (Nintendo 3DS): se desbloquea tras vencer a Landorus jugando con el cartucho de Pokémon Platino insertado en la consola. Incluye habilidad oculta Telepatía."},
    250: {"method": "Transferencia directa (Habilidad Oculta)", "note": "Modo especial Lente Arcoíris de RAdar Pokémon (Nintendo 3DS): se desbloquea tras vencer a Landorus jugando con el cartucho de Pokémon Oro HeartGold insertado en la consola. Incluye habilidad oculta Regeneración."},
    249: {"method": "Transferencia directa (Habilidad Oculta)", "note": "Modo especial Lente Buceo de RAdar Pokémon (Nintendo 3DS): se desbloquea tras vencer a Landorus jugando con el cartucho de Pokémon Plata SoulSilver insertado en la consola. Incluye habilidad oculta Compensación."},
}

SPECIAL_NOTES_BLACK2 = {
    138: [{"title": "Fósil Clásico • Monte Tuerca y Galería Unión", "text": _POSTGAME_FOSSIL_B2_TEXT, "tag": "Fósil", "icon": "/media/items/helix-fossil.png"}],
    140: [{"title": "Fósil Clásico • Monte Tuerca y Galería Unión", "text": _POSTGAME_FOSSIL_B2_TEXT, "tag": "Fósil", "icon": "/media/items/dome-fossil.png"}],
    142: [{"title": "Fósil Clásico • Monte Tuerca y Galería Unión", "text": _POSTGAME_FOSSIL_B2_TEXT, "tag": "Fósil", "icon": "/media/items/old-amber.png"}],
    345: [{"title": "Fósil Clásico • Monte Tuerca y Galería Unión", "text": _POSTGAME_FOSSIL_B2_TEXT, "tag": "Fósil", "icon": "/media/items/root-fossil.png"}],
    347: [{"title": "Fósil Clásico • Monte Tuerca y Galería Unión", "text": _POSTGAME_FOSSIL_B2_TEXT, "tag": "Fósil", "icon": "/media/items/claw-fossil.png"}],
    408: [
        {"title": "Fósil Clásico • Monte Tuerca y Galería Unión", "text": _POSTGAME_FOSSIL_B2_TEXT, "tag": "Fósil", "icon": "/media/items/skull-fossil.png"},
        _JULIAN_ONLY_NOTE,
    ],
    410: [
        {"title": "Fósil Clásico • Monte Tuerca y Galería Unión", "text": _POSTGAME_FOSSIL_B2_TEXT, "tag": "Fósil", "icon": "/media/items/armor-fossil.png"},
        _BELINDA_ONLY_NOTE,
    ],
    564: [{
        "title": "Elección Única con Aloe (Post-Liga)",
        "text": "Al visitar el Museo de Ciudad Esmalte tras superar la Liga Pokémon, la Líder Aloe te entrega a elegir entre el Fósil Tapa (Tirtouga) o el Fósil Pluma (Archen). El fósil no elegido requiere intercambio.",
        "tag": "Fósil Tapa",
        "icon": "/media/items/cover-fossil.png",
    }],
    566: [{
        "title": "Elección Única con Aloe (Post-Liga)",
        "text": "Al visitar el Museo de Ciudad Esmalte tras superar la Liga Pokémon, la Líder Aloe te entrega a elegir entre el Fósil Pluma (Archen) o el Fósil Tapa (Tirtouga). El fósil no elegido requiere intercambio.",
        "tag": "Fósil Pluma",
        "icon": "/media/items/plume-fossil.png",
    }],
    52:  [_BELINDA_ONLY_NOTE],
    303: [_BELINDA_ONLY_NOTE],
    216: [_BELINDA_ONLY_NOTE],
    56:  [_JULIAN_ONLY_NOTE],
    302: [_JULIAN_ONLY_NOTE],
    231: [_JULIAN_ONLY_NOTE],
    127: [{
        "title": "Exclusivo Salvaje de Blanco 2",
        "text": "En hierba alta de la Ruta 12 y el Bosque de los Perdidos, Pinsir es exclusivo de Pokémon Blanco 2 frente a Heracross en Pokémon Negro 2 (en el Claro Oculto del Bosque de los Perdidos tiene una aparición ultrarrara).",
        "tag": "Blanco 2",
        "icon": "/media/items/linking-cord.png",
    }],
    378: [{
        "title": "Sistema Clave • Clave Iceberg (Nexo Teselia)",
        "text": "Aunque la Clave Iceberg se desbloquea en Pokémon Blanco 2, si recibes dicha clave en tu partida de Pokémon Negro 2 mediante Nexo Teselia podrás activar la Cámara Iceberg y capturar a Regice al Nv. 65 en las Ruinas Subterráneas.",
        "tag": "Sistema Clave",
        "icon": "/media/items/card-key.png",
    }],
    434: [{
        "title": "Misión de Zona Nexo (Exclusivo Negro 2)",
        "text": "Stunky aparece de forma exclusiva en Pokémon Negro 2 dentro de los Claros Ocultos durante la misión específica de Zona Nexo correspondiente.",
        "tag": "Claro Oculto",
        "icon": "/media/items/growth-mulch.png",
    }],
    443: [{
        "title": "Recompensa del Rascacielos Negro",
        "text": "Tras derrotar a Guayo en el área 10 del Rascacielos Negro de Ciudad Negra, visítalo en la casa de Mirto en Pueblo Ocre para recibir este Gible variocolor garantizado al Nv. 1.",
        "tag": "Variocolor",
        "icon": "/media/items/star-piece.png",
    }],
    487: [{
        "title": "Griseosfera en Torre Duodraco",
        "text": "En Pokémon Negro 2 y Blanco 2, la Griseosfera (junto a la Diamansfera y la Lustresfera) se recoge directamente en la Torre Duodraco para activar la Forma Origen de Giratina.",
        "tag": "Forma Origen",
        "icon": "/media/items/griseous-orb.png",
    }],
    489: [{
        "title": "Crianza de Manaphy en Teselia 2",
        "text": "Si transfieres un Manaphy desde 4.ª Generación, puedes criarlo con Ditto en la Guardería Pokémon de la Ruta 3 para obtener huevos de Phione (#489).",
        "tag": "Crianza",
        "icon": "/media/items/mystery-egg.png",
    }],
    612: [{
        "title": "Permiso de Reserva Natural",
        "text": "Al ver las 300 especies de la Pokédex Regional de Teselia (sin contar singulares), la Profesora Encina te entrega el Permiso para volar desde Ciudad Loza hasta la Reserva Natural, donde aguarda este Haxorus variocolor fijo al Nv. 60.",
        "tag": "Variocolor",
        "icon": "/media/items/star-piece.png",
    }],
    641: [{
        "title": "RAdar Pokémon y Espejo Veraz",
        "text": "En Negro 2 puede recibirse en Forma Tótem mediante RAdar Pokémon (3DS, eShop cerrada en 2023) o intercambiarse desde Pokémon Negro. Cambia entre Forma Avatar y Forma Tótem usando el Espejo Veraz (Santuario Abundancia).",
        "tag": "Forma Tótem",
        "icon": "/media/items/reveal-glass.png",
    }],
    642: [{
        "title": "RAdar Pokémon y Espejo Veraz",
        "text": "En Negro 2 puede recibirse en Forma Tótem mediante RAdar Pokémon (3DS, eShop cerrada en 2023) o intercambiarse desde Pokémon Blanco. Cambia entre Forma Avatar y Forma Tótem usando el Espejo Veraz (Santuario Abundancia).",
        "tag": "Forma Tótem",
        "icon": "/media/items/reveal-glass.png",
    }],
    645: [{
        "title": "Desbloqueo del Espejo Veraz",
        "text": "Llevar a Landorus Forma Tótem procedente del RAdar Pokémon al Santuario Abundancia desbloquea el Espejo Veraz, permitiendo cambiar de forma libremente a Tornadus, Thundurus y Landorus.",
        "tag": "Espejo Veraz",
        "icon": "/media/items/reveal-glass.png",
    }],
    646: [{
        "title": "Punta ADN • Kyurem Negro y Kyurem Blanco",
        "text": "Tras capturar a Zekrom en la Torre Duodraco, Kyurem aparece al Nv. 70 en el Boquete Gigante y deja caer la Punta ADN para fusionarlo en Kyurem Negro (con Zekrom) o Kyurem Blanco (con Reshiram intercambiado).",
        "tag": "Punta ADN",
        "icon": "/media/items/dna-splicers.png",
    }],
    647: [{
        "title": "Arboleda Promesa • Forma Brío",
        "text": "Lleva a Keldeo junto a Cobalion, Terrakion y Virizion a la Arboleda Promesa (al norte de Pueblo Ocre) para que aprenda Sable Místico y adopte su Forma Brío.",
        "tag": "Forma Brío",
        "icon": "/media/items/cherish-ball.png",
    }],
    649: [{
        "title": "Los 4 Cartuchos en el Laboratorio P+P",
        "text": "A diferencia de Negro y Blanco originales, en Pokémon Negro 2 el Montañero del Laboratorio P+P entrega los 4 cartuchos (PiroROM, FulgoROM, HidroROM y CrioROM) tras combatir llevando a Genesect.",
        "tag": "Cartuchos",
        "icon": "/media/items/burn-drive.png",
    }],
}

HIDDEN_GROTTO_NOTE = {
    "title": "Mecánica de Claros Ocultos",
    "text": (
        "Los Claros Ocultos tienen un 5% de probabilidad de regenerarse cada 256 pasos (20% Pokémon con "
        "Habilidad Oculta garantizada, 40% objeto visible y 40% objeto oculto). Algunos claros de Teselia 2 "
        "requieren Surf o Cascada para alcanzar su entrada."
    ),
    "tag": "Claro Oculto",
    "icon": "/media/items/growth-mulch.png",
}


OUTDOOR_GRASS_RAW_AREAS = {
    'giant-chasm-forest',
    'giant-chasm-forest-cave',
    'giant-chasm-outside',
    'reversal-mountain-unknown-area-48',
    'unova-victory-road-2-unknown-area-72',
    'unova-victory-road-2-unknown-area-73',
    'unova-victory-road-2-unknown-area-76',
    'unova-victory-road-2-unknown-area-79',
}


def is_indoor_or_cave(area_clean: str, area_raw: str = '') -> bool:
    if area_raw in OUTDOOR_GRASS_RAW_AREAS:
        return False
    area_lower = area_clean.lower()
    if any(ext in area_lower for ext in (
        'ladera exterior', 'torre duodraco (entrada)', 'torre duodraco (exterior)',
        'boquete gigante (exterior)', 'bosque interior', 'claro oculto',
        'calle victoria (exterior)', 'montaña reversia (exterior)', 'boquete gigante (cráter)'
    )):
        return False
    return any(
        k in area_lower
        for k in (
            'cueva', 'monte tuerca', 'gruta', 'castillo ancestral', 'pasadizo ancestral',
            'cloacas', 'túnel yakón', 'ruinas subterráneas', 'montaña reversia',
            'villa horroris', 'torre de los cielos', 'torre duodraco', 'calle victoria',
            'estancia orientación', 'cámara'
        )
    )


def format_wild_method(method_raw: str, conditions: list, area_clean: str, area_raw: str = '') -> str:
    if 'swarm-yes' in conditions:
        return 'Manada diaria'
    if method_raw == 'hidden-grotto':
        # Nunca incluir "Surf" aquí para no contaminar el filtro de captura por Surf
        return 'Claro Oculto'
    if method_raw == 'npc-trade':
        return 'Intercambio NPC'
    if method_raw == 'gift':
        return 'Regalo del juego'
    if method_raw == 'gift-egg':
        return 'Huevo regalo'
    if method_raw == 'static':
        return 'Encuentro estático'
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
        area_lower = area_clean.lower()
        if area_lower in ('ciudad teja', 'ruta 8', 'pantano teja'):
            return 'Caminando en charcos'
        if area_lower in ('ruta 4', 'zona desierto', 'zona desierto (entrada)'):
            return 'Caminando en la arena'
        if is_indoor_or_cave(area_clean, area_raw):
            return 'Caminando'
        return 'Hierba alta'
    return 'Salvaje'


def main():
    print("Iniciando compilación oficial de catálogos para Pokémon Negro 2...")

    with open(CACHE_DIR / "pokemon_649_species.json", "r", encoding="utf-8") as f:
        species_649 = json.load(f)

    with open(CACHE_DIR / "encounters_black-2.json", "r", encoding="utf-8") as f:
        encounters_b2 = json.load(f)

    with open(CACHE_DIR / "wikidex_black-2_descriptions.json", "r", encoding="utf-8") as f:
        descriptions = json.load(f)

    with open(CACHE_DIR / "unova_updated_pokedex_301.json", "r", encoding="utf-8") as f:
        unova_301 = json.load(f)

    with open(CACHE_DIR / "gen5_evolutions.json", "r", encoding="utf-8") as f:
        gen5_evos = json.load(f)

    with open(BASE_DIR / "tracker" / "data" / "evolution_stones.json", "r", encoding="utf-8") as f:
        evolution_stones = json.load(f)

    from tracker.exclusives import VERSION_TRANSFERS_CATALOG, VERSION_TRANSFERS_META, VERSION_EXCLUSIVES_CATALOG
    b2_transfers = set(VERSION_TRANSFERS_CATALOG.get("black-2", []))
    b2_origins = VERSION_TRANSFERS_META.get("black-2", {}).get("origins", {})
    white2_exclusives = set(VERSION_EXCLUSIVES_CATALOG.get("white-2", []))

    unmapped_areas = set()

    def build_entry(nat_id: int, entry_num: int, is_regional: bool, unique_id: int, display_number_override: str = None):
        sp = species_649[str(nat_id)]
        flavor = descriptions.get(str(nat_id), "")
        sp_name = sp['name'].lower()
        egg_groups = sp.get('egg_groups', [])
        evo_info = gen5_evos.get(str(nat_id))

        is_baby = sp_name in BABY_NAMES
        is_incense_parent = sp_name in INCENSE_PARENTS_THAT_HATCH
        is_evolution = (evo_info is not None) and not is_incense_parent

        # Regla Universal de Crianza (Invariante 4; #489 Phione criable)
        if nat_id == 489:
            is_hatchable = True
        elif sp_name in NON_BREEDABLE_NAMES or nat_id in {494, 638, 639, 640, 641, 642, 643, 644, 645, 646, 647, 648, 649}:
            is_hatchable = False
        elif ('no-eggs' in egg_groups) and not is_baby:
            is_hatchable = False
        elif is_baby or is_incense_parent:
            is_hatchable = True
        elif is_evolution:
            is_hatchable = False
        else:
            is_hatchable = True

        raw_encs = encounters_b2.get(str(nat_id), [])
        extra_hg = EXTRA_HIDDEN_GROTTOS_BLACK2.get(nat_id, [])
        entry_seasons = set()
        if nat_id in SEASONAL_FORM_SPECIES_IDS:
            entry_seasons.update(("spring", "summer", "autumn", "winter"))

        # Manadas diarias pertenecen exclusivamente al post-Liga / Nacional (has_regional_swarms = False)
        include_swarm = (not is_regional) and (nat_id in SWARM_POKEMON_BLACK2)

        def _collect_wild_locations(exclude_non_wild: bool = False):
            area_method_meta = {}
            for e in raw_encs:
                area_key = e.get('area_raw', '')
                m_raw = e.get('method_raw', 'walk')
                if exclude_non_wild and m_raw in ('gift', 'gift-egg', 'npc-trade', 'static'):
                    continue
                if area_key not in UNOVA2_AREA_NAMES:
                    unmapped_areas.add(area_key)
                clean_area = UNOVA2_AREA_NAMES.get(area_key, area_key)
                conds = e.get('conditions', []) or []
                meth_desc = format_wild_method(m_raw, conds, clean_area, area_key)
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

            for hg in extra_hg:
                area_methods.setdefault(hg['area'], set()).add(hg['method'])

            if include_swarm:
                sw_info = SWARM_POKEMON_BLACK2[nat_id]
                area_methods.setdefault(sw_info['area'], set()).add('Manada diaria')

            if nat_id == 550:
                for a_name in list(area_methods.keys()):
                    area_methods[a_name].update({'Surf', 'Surf en sombra del agua', 'Supercaña', 'Supercaña en sombra del agua'})

            loc_list = []
            for a_name, m_set in area_methods.items():
                loc_list.append({
                    'area': a_name,
                    'method': ", ".join(sorted(list(m_set)))
                })
            return area_methods, loc_list

        # 1. Exclusivos de Pokémon Blanco 2 (prioritario frente a encuentros residuales como Pinsir/Regice)
        if nat_id in white2_exclusives:
            if nat_id == 643:
                summary = "Inaccesible en estado salvaje en Pokémon Negro 2. Legendario exclusivo de Pokémon Blanco 2 (Torre Duodraco con Orbe Claro; requiere intercambio para registrarlo y fusionar a Kyurem Blanco)."
            elif nat_id == 378:
                summary = "Exclusivo de Pokémon Blanco 2 mediante la Clave Iceberg. En Pokémon Negro 2 solo puedes capturarlo en las Ruinas Subterráneas (Nv. 65) si recibes la Clave Iceberg desde Blanco 2 vía Nexo Teselia, o mediante intercambio."
            elif nat_id == 380:
                summary = "Inaccesible en Pokémon Negro 2. Legendario exclusivo del Solar de los Sueños en Pokémon Blanco 2 (requiere intercambio)."
            elif nat_id == 127:
                summary = "Exclusivo salvaje de Pokémon Blanco 2 (Ruta 12 y Bosque de los Perdidos) frente a Heracross en Negro 2. Requiere intercambio con Pokémon Blanco 2."
            else:
                summary = "Inaccesible en estado salvaje en Pokémon Negro 2. Exclusivo de Pokémon Blanco 2 (requiere intercambio)."
            loc_list = [{'area': 'Intercambio con Pokémon Blanco 2', 'method': 'Exclusivo de versión'}]
            if is_hatchable:
                loc_list.append(DAYCARE_LOCATION)
            obt_info = {
                'type': 'transfer',
                'badge_label': 'Edición Blanco 2',
                'badge_color': 'rose',
                'summary': summary,
                'locations': loc_list
            }
        # 2. Casos especiales curados (iniciales, regalos, estáticos, fósiles, intercambios NPC, legendarios)
        elif nat_id in SPECIAL_OBTAINING_BLACK2:
            obt_info = json.loads(json.dumps(SPECIAL_OBTAINING_BLACK2[nat_id]))
            if nat_id in (133, 550, 585, 593, 558, 465) and raw_encs:
                _, wild_locs = _collect_wild_locations(exclude_non_wild=True)
                obt_info['locations'] = wild_locs + obt_info.get('locations', [])
                if entry_seasons and 'seasons' not in obt_info:
                    season_order = ["spring", "summer", "autumn", "winter"]
                    obt_info['seasons'] = [s for s in season_order if s in entry_seasons]
        # 3. Encuentros salvajes, Claros Ocultos y Manadas
        elif raw_encs or extra_hg or include_swarm:
            area_methods, loc_list = _collect_wild_locations()

            if is_hatchable:
                loc_list.append(DAYCARE_LOCATION)

            num_zones = len(area_methods)
            zone_names = list(area_methods.keys())
            only_hg = all(
                all("claro oculto" in m.lower() for m in m_set)
                for m_set in area_methods.values()
            )

            if include_swarm and not raw_encs and not extra_hg:
                sw_info = SWARM_POKEMON_BLACK2[nat_id]
                summary = f"{sw_info['desc']} (también obtenible mediante crianza)." if is_hatchable else sw_info['desc']
            elif only_hg:
                if num_zones == 1:
                    summary = f"Obtenible en Claro Oculto en {zone_names[0]} (con Habilidad Oculta garantizada)."
                else:
                    summary = f"Obtenible en Claros Ocultos en {', '.join(zone_names[:-1])} y {zone_names[-1]} (con Habilidad Oculta garantizada)."
                if is_hatchable:
                    summary += " También obtenible mediante crianza en la Guardería de la Ruta 3."
            else:
                if num_zones == 1:
                    summary = f"Salvaje en {zone_names[0]}."
                elif num_zones == 2:
                    summary = f"Salvaje en {zone_names[0]} y {zone_names[1]}."
                elif num_zones <= 4:
                    summary = f"Salvaje en {', '.join(zone_names[:-1])} y {zone_names[-1]}."
                else:
                    summary = f"Salvaje en múltiples zonas de Teselia, incluyendo {zone_names[0]}, {zone_names[1]} y {zone_names[2]}."
                if include_swarm:
                    summary += f" También aparece en manada diaria en {SWARM_POKEMON_BLACK2[nat_id]['area']}."
                if is_hatchable:
                    summary += " También obtenible mediante crianza en la Guardería de la Ruta 3."

            obt_info = {
                'type': 'wild',
                'badge_label': 'Claro Oculto' if only_hg else 'Salvaje',
                'badge_color': 'emerald',
                'summary': summary,
                'locations': loc_list
            }
            if entry_seasons:
                season_order = ["spring", "summer", "autumn", "winter"]
                obt_info['seasons'] = [s for s in season_order if s in entry_seasons]
        # 4. Evoluciones puras (y padres con incienso evolucionables como Chansey desde Happiny)
        elif (is_evolution or (is_incense_parent and nat_id not in white2_exclusives and nat_id not in b2_transfers)) and evo_info:
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
        # 5. Crianza pura
        elif nat_id in BREEDING_PARENTS_BLACK2:
            parent_desc, loc_parents = BREEDING_PARENTS_BLACK2[nat_id]
            summary = f"Inaccesible en estado salvaje; se obtiene mediante crianza de {parent_desc} en la Guardería de la Ruta 3."
            loc_list = [{'area': 'Ruta 3 (Guardería Pokémon)', 'method': f'Crianza de huevo ({loc_parents})'}]
            obt_info = {
                'type': 'other',
                'badge_label': 'Crianza',
                'badge_color': 'zinc',
                'summary': summary,
                'locations': loc_list
            }
        # 6. Transferencias estrictas Gen 1–4
        elif nat_id in b2_transfers:
            origin_desc = b2_origins.get(nat_id, "Pokétransfer (Ruta 15) o intercambio desde Negro/Blanco")
            if nat_id == 489:
                summary = "Inaccesible en estado salvaje en Teselia 2. Se obtiene mediante Pokétransfer (Ruta 15) o criando con Ditto en la Guardería de la Ruta 3 a partir de un Manaphy transferido."
            elif nat_id in (483, 484, 487):
                summary = "Inaccesible en estado salvaje en Teselia 2. Requiere Pokétransfer (Ruta 15) desde 4.ª Generación o RAdar Pokémon (3DS con cartucho de 4.ª Gen insertado); también fue repartido variocolor en 2013."
            elif nat_id in (249, 250):
                summary = "Inaccesible en estado salvaje en Teselia 2. Requiere Pokétransfer (Ruta 15) desde 4.ª Generación o RAdar Pokémon (3DS con HeartGold/SoulSilver insertado)."
            elif nat_id == 137:
                summary = "Inaccesible en estado salvaje en Teselia 2. Requiere Pokétransfer (Ruta 15), intercambio desde Pokémon Blanco (Bosque Blanco) o RAdar Pokémon (Nintendo 3DS)."
            elif nat_id == 238:
                summary = "Inaccesible en estado salvaje en Teselia 2. Requiere Pokétransfer (Ruta 15) o transferencia directa desde RAdar Pokémon (Nintendo 3DS)."
            else:
                summary = f"Inaccesible en estado salvaje en Pokémon Negro 2. Requiere {origin_desc}."
            loc_list = [{'area': 'Laboratorio de Pokétransfer (Ruta 15)', 'method': origin_desc}]
            if is_hatchable:
                loc_list.append(DAYCARE_LOCATION)
            obt_info = {
                'type': 'transfer',
                'badge_label': 'Pokétransfer',
                'badge_color': 'amber',
                'summary': summary,
                'locations': loc_list
            }
        else:
            # Fallback de seguridad (no debe activarse para ninguna especie de #1..#649)
            summary = "Obtención mediante crianza o intercambio en Teselia 2."
            loc_list = [DAYCARE_LOCATION] if is_hatchable else [{'area': 'Teselia', 'method': 'Especial'}]
            obt_info = {
                'type': 'other',
                'badge_label': 'Crianza',
                'badge_color': 'zinc',
                'summary': summary,
                'locations': loc_list
            }

        # Contrato universal de evolution_info en todas las especies evolucionadas
        if evo_info and 'evolution_info' not in obt_info:
            obt_info['evolution_info'] = {
                'from': evo_info.get('from_name'),
                'text': evo_info.get('text', ''),
                'trigger': evo_info.get('trigger', 'level-up'),
                'condition': evo_info.get('condition', ''),
                'item_slug': evo_info.get('item_slug'),
            }

        # Inciensos de crianza (Regional y Nacional, pasando entero nat_id)
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
            evo_stone_obj = resolve_evolution_stone(item_slug=item_slug_to_resolve, game_slug="black-2")
        else:
            evo_stone_obj = None

        # Fidelidad histórica estricta Gen 5: el tipo Hada no existía hasta Gen 6
        p_type = 'normal' if sp['primary_type'] == 'fairy' else sp['primary_type']
        s_type = None if sp['secondary_type'] == 'fairy' else sp['secondary_type']

        disp_num = display_number_override or f"{entry_num:03d}"

        entry_notes = []
        if nat_id in SPECIAL_NOTES_BLACK2:
            entry_notes.extend(json.loads(json.dumps(SPECIAL_NOTES_BLACK2[nat_id])))
        has_hg_loc = any("claro oculto" in loc.get("method", "").lower() for loc in obt_info.get("locations", []))
        if has_hg_loc and not any(n.get("tag") == "Claro Oculto" for n in entry_notes):
            entry_notes.append(json.loads(json.dumps(HIDDEN_GROTTO_NOTE)))
        if nat_id in DREAM_RADAR_POKEMON_BLACK2:
            dr_info = DREAM_RADAR_POKEMON_BLACK2[nat_id]
            has_dr_loc = any(
                "radar pokémon" in loc.get("area", "").lower() or "rádar pokémon" in loc.get("area", "").lower()
                for loc in obt_info.get("locations", [])
            )
            if not has_dr_loc:
                obt_info["locations"].append({
                    "area": "RAdar Pokémon (Nintendo 3DS)",
                    "method": dr_info["method"],
                })
            else:
                for loc in obt_info["locations"]:
                    area_l = loc.get("area", "").lower()
                    if "radar pokémon" in area_l or "rádar pokémon" in area_l:
                        loc["method"] = dr_info["method"]
            entry_notes.append({
                "title": "RAdar Pokémon (Nintendo 3DS)",
                "text": dr_info["note"],
                "tag": "RAdar Pokémon",
                "icon": _DREAM_RADAR_ICON,
            })

        unown_suffix = "-f" if nat_id == 201 else ""
        home_shiny_url = f"/media/pokemon/home/shiny/{nat_id}{unown_suffix}.png"

        entry = {
            "id": unique_id,
            "entry_number": entry_num,
            "display_number": disp_num,
            "game_slug": "black-2",
            "is_hatchable": is_hatchable,
            "pokemon": {
                "national_number": nat_id,
                "name": sp['name'],
                "display_name": sp['display_name'],
                "category": sp.get('category', ''),
                "height": sp.get('height', 0),
                "weight": sp.get('weight', 0),
                "sprite_url": f"/media/pokemon/artwork/{nat_id}.png",
                "sprite_shiny_url": None,
                "artwork_shiny_url": home_shiny_url,
                "primary_type": p_type,
                "secondary_type": s_type
            },
            "primary_type": p_type,
            "primary_type_display": p_type.capitalize(),
            "primary_type_es": TYPE_NAMES_ES.get(p_type, p_type.capitalize()),
            "secondary_type": s_type,
            "secondary_type_display": s_type.capitalize() if s_type else "",
            "secondary_type_es": TYPE_NAMES_ES.get(s_type, s_type.capitalize()) if s_type else "",
            "game_sprite_url": f"/media/pokemon/sprites/black-2/{nat_id}.png",
            "game_sprite_shiny_url": f"/media/pokemon/sprites/black-2_shiny/{nat_id}.png",
            "game_sprite_back_url": f"/media/pokemon/sprites/black-2/back/{nat_id}.png",
            "game_sprite_shiny_back_url": f"/media/pokemon/sprites/black-2_shiny/back/{nat_id}.png",
            "modern_sprite_shiny_url": home_shiny_url,
            "modal_retro_sprite_url": f"/media/pokemon/sprites/black-2_animated/{nat_id}.gif",
            "modal_retro_sprite_shiny_url": f"/media/pokemon/sprites/black-2_animated_shiny/{nat_id}.gif",
            "modal_retro_sprite_back_url": f"/media/pokemon/sprites/black-2_animated/back/{nat_id}.gif",
            "modal_retro_sprite_shiny_back_url": f"/media/pokemon/sprites/black-2_animated_shiny/back/{nat_id}.gif",
            "pc_icon_url": f"/media/pokemon/icons/gen5/{nat_id}.png",
            "cry_url": f"/media/pokemon/cries/legacy/{nat_id}.ogg",
            "flavor_text": flavor,
            "obtaining_info": obt_info,
            "evolution_stone": evo_stone_obj,
            "notes": entry_notes,
            "game_data": {
                "generation": 5,
                "game_slug": "black-2",
                "game_name": "Pokémon Negro 2",
                "is_regional": is_regional
            }
        }
        return entry

    # 1. Pokédex Regional de Teselia 2 (black-2.json — 301 especies, IDs 10000..10300)
    print("Compilando Pokédex Regional de Teselia 2 (301 entradas)...")
    regional_catalog = []
    victini_nat = int(unova_301.get("0", 494))
    regional_catalog.append(build_entry(
        nat_id=victini_nat,
        entry_num=494,
        is_regional=True,
        unique_id=10000,
        display_number_override="000"
    ))
    for reg_num in range(1, 301):
        nat_id = int(unova_301[str(reg_num)])
        regional_catalog.append(build_entry(
            nat_id=nat_id,
            entry_num=reg_num,
            is_regional=True,
            unique_id=10000 + reg_num,
            display_number_override=f"{reg_num:03d}"
        ))

    regional_file = CATALOGS_DIR / "black-2.json"
    with open(regional_file, "w", encoding="utf-8") as f:
        json.dump(regional_catalog, f, ensure_ascii=False, indent=2)
    print(f"[OK] Guardado {regional_file} con {len(regional_catalog)} entradas.")

    # 2. Pokédex Nacional de Pokémon Negro 2 (black-2_national.json — 649 especies, IDs 10401..11049)
    print("Compilando Pokédex Nacional de Pokémon Negro 2 (649 entradas)...")
    national_catalog = []
    for nat_num in range(1, 650):
        national_catalog.append(build_entry(
            nat_id=nat_num,
            entry_num=nat_num,
            is_regional=False,
            unique_id=10400 + nat_num,
            display_number_override=f"{nat_num:03d}"
        ))

    national_file = CATALOGS_DIR / "black-2_national.json"
    with open(national_file, "w", encoding="utf-8") as f:
        json.dump(national_catalog, f, ensure_ascii=False, indent=2)
    print(f"[OK] Guardado {national_file} con {len(national_catalog)} entradas.")

    if unmapped_areas:
        print(f"[WARN] Áreas sin mapear detectadas: {sorted(unmapped_areas)}")
    else:
        print("[OK] 0 áreas sin mapear en encounters_black-2.json.")


if __name__ == "__main__":
    main()
