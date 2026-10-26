"""
Script para compilar y generar los catálogos oficiales JSON de Pokémon Platino
para PokedexGlobal a 0 ms SQL:
1. Pokédex Regional de Sinnoh Expandida: tracker/data/catalogs/platinum.json (210 especies canónicas)
2. Pokédex Nacional: tracker/data/catalogs/platinum_national.json (493 especies canónicas)
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
from tracker.utils import get_incense_for_baby, resolve_evolution_stone

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

SINNOH_AREA_NAMES = {
    'twinleaf-town': 'Pueblo Hojaverde',
    'sandgem-town': 'Pueblo Arena',
    'jubilife-city': 'Ciudad Jubileo',
    'oreburgh-city': 'Ciudad Pirita',
    'oreburgh-mine': 'Mina Pirita',
    'oreburgh-gate': 'Puerta Pirita',
    'floaroma-town': 'Pueblo Aromaflor',
    'floaroma-meadow': 'Prado Aromaflor',
    'valley-windworks': 'Valle Eólico',
    'eterna-city': 'Ciudad Vetusta',
    'eterna-forest': 'Bosque Vetusto',
    'old-chateau': 'Vieja Mansión',
    'wayward-cave': 'Cueva Extravío',
    'mt-coronet': 'Monte Corona',
    'hearthome-city': 'Ciudad Corazón',
    'amity-square': 'Plaza Amistad',
    'solaceon-town': 'Pueblo Sosiego',
    'solaceon-ruins': 'Ruinas Sosiego',
    'lost-tower': 'Torre Perdida',
    'veilstone-city': 'Ciudad Rocavelo',
    'pastoria-city': 'Ciudad Pradera',
    'great-marsh': 'Gran Pantano',
    'celestic-town': 'Pueblo Caelestis',
    'canalave-city': 'Ciudad Canal',
    'iron-island': 'Isla Hierro',
    'snowpoint-city': 'Ciudad Puntaneva',
    'snowpoint-temple': 'Templo Puntaneva',
    'sunyshore-city': 'Ciudad Marina',
    'pokemon-league': 'Liga Pokémon',
    'victory-road': 'Calle Victoria',
    'ravaged-path': 'Senda Desolada',
    'fuego-ironworks': 'Forja Fuego',
    'lake-verity': 'Lago Veraz',
    'lake-valor': 'Lago Valor',
    'lake-acuity': 'Lago Agudeza',
    'spear-pillar': 'Columna Lanza',
    'hall-of-origin': 'Sala del Origen',
    'distortion-world': 'Mundo Distorsión',
    'turnback-cave': 'Cueva Retorno',
    'spring-path': 'Senda Manantial',
    'sendoff-spring': 'Fuente Despedida',
    'fullmoon-island': 'Isla Plenilunio',
    'newmoon-island': 'Isla Lunanueva',
    'flower-paradise': 'Paraíso Floral',
    'fight-area': 'Zona de Combate',
    'battle-frontier': 'Frente de Batalla',
    'survival-area': 'Zona Sobrevivir',
    'resort-area': 'Zona Descanso',
    'stark-mountain': 'Montaña Dura',
    'trophy-garden': 'Jardín Trofeo (Mansión Pokémon)',
    'pal-park': 'Parque Compi (Ruta 221)',
    'underground': 'Subsuelo de Sinnoh',
    'maniac-tunnel': 'Túnel Ruinamaníaco',
    'ruin-maniac-cave': 'Cueva Ruinamaníaco',
    'iron-ruins': 'Ruinas Hierro',
    'iceberg-ruins': 'Ruinas Iceberg',
    'rock-peak-ruins': 'Ruinas Pico',
}
for r in range(201, 231):
    SINNOH_AREA_NAMES[f'route-{r}'] = f'Ruta {r}'
    SINNOH_AREA_NAMES[f'sinnoh-route-{r}'] = f'Ruta {r}'

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
    'area': 'Pueblo Sosiego (Guardería Pokémon)',
    'method': 'Crianza de huevo'
}

SPECIAL_OBTAINING = {
    # Iniciales de Sinnoh (Elección en Ruta 201)
    387: {
        'type': 'starter',
        'badge_label': 'Inicial',
        'badge_color': 'emerald',
        'summary': 'Elegir en el maletín del Profesor Serbal en la Ruta 201 durante el ataque de los Starly salvajes (también obtenible mediante crianza).',
        'locations': [
            {'area': 'Ruta 201 (Maletín de Serbal)', 'method': 'Elección de Inicial de Sinnoh'},
            DAYCARE_LOCATION
        ]
    },
    390: {
        'type': 'starter',
        'badge_label': 'Inicial',
        'badge_color': 'amber',
        'summary': 'Elegir en el maletín del Profesor Serbal en la Ruta 201 durante el ataque de los Starly salvajes (también obtenible mediante crianza).',
        'locations': [
            {'area': 'Ruta 201 (Maletín de Serbal)', 'method': 'Elección de Inicial de Sinnoh'},
            DAYCARE_LOCATION
        ]
    },
    393: {
        'type': 'starter',
        'badge_label': 'Inicial',
        'badge_color': 'sky',
        'summary': 'Elegir en el maletín del Profesor Serbal en la Ruta 201 durante el ataque de los Starly salvajes (también obtenible mediante crianza).',
        'locations': [
            {'area': 'Ruta 201 (Maletín de Serbal)', 'method': 'Elección de Inicial de Sinnoh'},
            DAYCARE_LOCATION
        ]
    },

    # Huevos y Regalos en Sinnoh
    175: {
        'type': 'gift',
        'badge_label': 'Huevo Regalo',
        'badge_color': 'sky',
        'summary': 'Huevo entregado por Cintia en el acceso oeste de Ciudad Vetusta tras derrotar a Júpiter en el Edificio Galaxia (también obtenible mediante crianza).',
        'locations': [
            {'area': 'Ciudad Vetusta (Acceso Oeste)', 'method': 'Huevo entregado por Cintia'},
            DAYCARE_LOCATION
        ]
    },
    133: {
        'type': 'gift',
        'badge_label': 'Regalo',
        'badge_color': 'amber',
        'summary': 'Entregado por Tecla en su casa de Ciudad Corazón al nivel 20 antes de la Liga Pokémon (también obtenible mediante crianza o en el Jardín Trofeo).',
        'locations': [
            {'area': 'Ciudad Corazón (Casa de Tecla)', 'method': 'Regalo de Tecla al Nivel 20'},
            {'area': 'Jardín Trofeo', 'method': 'Hierba alta (Mención del Sr. Fortuny)'},
            DAYCARE_LOCATION
        ]
    },
    137: {
        'type': 'gift',
        'badge_label': 'Regalo',
        'badge_color': 'indigo',
        'summary': 'Regalo de un habitante en una casa de Ciudad Rocavelo al nivel 25.',
        'locations': [
            {'area': 'Ciudad Rocavelo (Casa)', 'method': 'Regalo al Nivel 25'}
        ]
    },
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

    # Fósiles del Subsuelo según paridad de TID (Modelo C de Platino)
    408: {
        'type': 'fossil',
        'badge_label': 'Fósil (TID Impar)',
        'badge_color': 'blue',
        'summary': 'Revivir del Fósil Cráneo en el Museo Minero de Ciudad Pirita. Excavar en el Subsuelo de Sinnoh si el último dígito del TID del entrenador es impar (o aleatoriamente tras la Pokédex Nacional; también por crianza).',
        'locations': [
            {'area': 'Subsuelo de Sinnoh', 'method': 'Excavación de Fósil Cráneo (TID impar / Post-Nacional)'},
            {'area': 'Ciudad Pirita (Museo Minero)', 'method': 'Restauración de Fósil Cráneo'},
            DAYCARE_LOCATION
        ]
    },
    410: {
        'type': 'fossil',
        'badge_label': 'Fósil (TID Par)',
        'badge_color': 'pink',
        'summary': 'Revivir del Fósil Coraza en el Museo Minero de Ciudad Pirita. Excavar en el Subsuelo de Sinnoh si el último dígito del TID del entrenador es par (o aleatoriamente tras la Pokédex Nacional; también por crianza).',
        'locations': [
            {'area': 'Subsuelo de Sinnoh', 'method': 'Excavación de Fósil Coraza (TID par / Post-Nacional)'},
            {'area': 'Ciudad Pirita (Museo Minero)', 'method': 'Restauración de Fósil Coraza'},
            DAYCARE_LOCATION
        ]
    },

    # Fósiles de Kanto y Hoenn en el Subsuelo de Sinnoh post-Nacional
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
        'summary': 'Revivir del Fósil Domo en el Museo Minero de Ciudad Pirita. Excavar en el Subsuelo de Sinnoh tras obtener la Pokédex Nacional (también obtenible mediante crianza).',
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
            {'area': 'Ciudad Pirita (Museo Minero)', 'method': 'Restauración de Fósil Ámbar Viejo'},
            DAYCARE_LOCATION
        ]
    },
    345: {
        'type': 'fossil',
        'badge_label': 'Fósil',
        'badge_color': 'emerald',
        'summary': 'Revivir del Fósil Raíz en el Museo Minero de Ciudad Pirita. Excavar en el Subsuelo de Sinnoh tras obtener la Pokédex Nacional (también obtenible mediante crianza).',
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

    # Legendarios de Sinnoh
    479: {
        'type': 'wild',
        'badge_label': 'Vieja Mansión',
        'badge_color': 'indigo',
        'summary': 'Interactuar con el televisor encendido en la Habitación Televisión de la Vieja Mansión (Bosque Vetusto) entre las 20:00 y las 03:59 al nivel 20 (accesible antes de la Liga Pokémon, Sinnoh #152).',
        'locations': [{'area': 'Vieja Mansión (Televisor)', 'method': 'Encuentro nocturno al Nivel 20'}]
    },
    480: {
        'type': 'legendary',
        'badge_label': 'Legendario',
        'badge_color': 'amber',
        'summary': 'Encuentro estático en la Caverna Agudeza en el centro del Lago Agudeza al Nivel 50 tras resolver los eventos del Mundo Distorsión.',
        'locations': [{'area': 'Caverna Agudeza (Lago Agudeza)', 'method': 'Encuentro estático al Nivel 50'}]
    },
    481: {
        'type': 'legendary',
        'badge_label': 'Errante',
        'badge_color': 'rose',
        'summary': 'Interaccionar en la Caverna Veraz para registrar su avistamiento; a partir de ese momento recorre libremente las rutas de Sinnoh al Nivel 50 (rastreable con la función Marcamapa del Poké-reloj).',
        'locations': [{'area': 'Rutas de Sinnoh (Errante)', 'method': 'Pokémon errante al Nivel 50 tras Caverna Veraz'}]
    },
    482: {
        'type': 'legendary',
        'badge_label': 'Legendario',
        'badge_color': 'sky',
        'summary': 'Encuentro estático en la Caverna Valor en el centro del Lago Valor al Nivel 50 tras resolver los eventos del Mundo Distorsión.',
        'locations': [{'area': 'Caverna Valor (Lago Valor)', 'method': 'Encuentro estático al Nivel 50'}]
    },
    483: {
        'type': 'legendary',
        'badge_label': 'Columna Lanza',
        'badge_color': 'blue',
        'summary': 'Encuentro estático en la Columna Lanza al Nivel 70 en el postgame tras hablar con la anciana de Pueblo Caelestis y llevar la Diamansfera encontrada en el Monte Corona.',
        'locations': [{'area': 'Columna Lanza (Monte Corona)', 'method': 'Encuentro estático postgame al Nivel 70 con Diamansfera'}]
    },
    484: {
        'type': 'legendary',
        'badge_label': 'Columna Lanza',
        'badge_color': 'pink',
        'summary': 'Encuentro estático en la Columna Lanza al Nivel 70 en el postgame tras hablar con la anciana de Pueblo Caelestis y llevar la Lustresfera encontrada en el Monte Corona.',
        'locations': [{'area': 'Columna Lanza (Monte Corona)', 'method': 'Encuentro estático postgame al Nivel 70 con Lustresfera'}]
    },
    485: {
        'type': 'legendary',
        'badge_label': 'Legendario',
        'badge_color': 'rose',
        'summary': 'Encuentro estático en la cámara más profunda de la Montaña Dura al Nivel 50 tras devolver la Piedra Magma junto a Bulgur.',
        'locations': [{'area': 'Montaña Dura (Cámara de Heatran)', 'method': 'Encuentro estático al Nivel 50'}]
    },
    486: {
        'type': 'legendary',
        'badge_label': 'Legendario',
        'badge_color': 'slate',
        'summary': 'Encuentro estático en el piso B5F del Templo Puntaneva al Nivel 1 llevando en el equipo a Regirock, Regice y Registeel.',
        'locations': [{'area': 'Templo Puntaneva (Sótano B5)', 'method': 'Encuentro estático al Nivel 1 (Requiere trío Regi)'}]
    },
    487: {
        'type': 'legendary',
        'badge_label': 'Mascota Oficial',
        'badge_color': 'purple',
        'summary': 'Encuentro estático obligatorio de historia en el Mundo Distorsión al Nivel 47 en su Forma Origen. Si se debilita o huye, reaparece en la Cueva Retorno al Nivel 65 en Forma Modificada.',
        'locations': [
            {'area': 'Mundo Distorsión', 'method': 'Encuentro obligatorio de historia al Nivel 47 (Forma Origen)'},
            {'area': 'Cueva Retorno', 'method': 'Reaparición postgame al Nivel 65 si huyó'}
        ]
    },
    488: {
        'type': 'legendary',
        'badge_label': 'Errante',
        'badge_color': 'indigo',
        'summary': 'Interaccionar en la Isla Plenilunio tras curar la pesadilla del hijo de Marinero en Ciudad Canal; recorre las rutas de Sinnoh al Nivel 50.',
        'locations': [{'area': 'Rutas de Sinnoh (Errante)', 'method': 'Pokémon errante al Nivel 50 tras visitar Isla Plenilunio'}]
    },

    # Aves Legendarias errantes por Sinnoh tras hablar con Oak
    144: {
        'type': 'legendary',
        'badge_label': 'Errante',
        'badge_color': 'sky',
        'summary': 'Hablar con el Profesor Oak en su casa de Ciudad Vetusta tras obtener la Pokédex Nacional; a partir de ese momento recorre libremente las rutas de Sinnoh al Nivel 60.',
        'locations': [{'area': 'Rutas de Sinnoh (Errante)', 'method': 'Pokémon errante al Nivel 60 tras hablar con Oak en Vetusta'}]
    },
    145: {
        'type': 'legendary',
        'badge_label': 'Errante',
        'badge_color': 'amber',
        'summary': 'Hablar con el Profesor Oak en su casa de Ciudad Vetusta tras obtener la Pokédex Nacional; a partir de ese momento recorre libremente las rutas de Sinnoh al Nivel 60.',
        'locations': [{'area': 'Rutas de Sinnoh (Errante)', 'method': 'Pokémon errante al Nivel 60 tras hablar con Oak en Vetusta'}]
    },
    146: {
        'type': 'legendary',
        'badge_label': 'Errante',
        'badge_color': 'rose',
        'summary': 'Hablar con el Profesor Oak en su casa de Ciudad Vetusta tras obtener la Pokédex Nacional; a partir de ese momento recorre libremente las rutas de Sinnoh al Nivel 60.',
        'locations': [{'area': 'Rutas de Sinnoh (Errante)', 'method': 'Pokémon errante al Nivel 60 tras hablar con Oak en Vetusta'}]
    },

    # Regis en Ruinas de Sinnoh
    377: {
        'type': 'legendary',
        'badge_label': 'Ruinas Pico',
        'badge_color': 'amber',
        'summary': 'Encuentro estático en las Ruinas Pico (Ruta 228) al Nivel 30 al portar el Regigigas de evento en el equipo.',
        'locations': [{'area': 'Ruinas Pico (Ruta 228)', 'method': 'Encuentro estático al Nivel 30 (Evento Regigigas)'}]
    },
    378: {
        'type': 'legendary',
        'badge_label': 'Ruinas Iceberg',
        'badge_color': 'sky',
        'summary': 'Encuentro estático en las Ruinas Iceberg (Monte Corona) al Nivel 30 al portar el Regigigas de evento en el equipo.',
        'locations': [{'area': 'Ruinas Iceberg (Monte Corona)', 'method': 'Encuentro estático al Nivel 30 (Evento Regigigas)'}]
    },
    379: {
        'type': 'legendary',
        'badge_label': 'Ruinas Hierro',
        'badge_color': 'slate',
        'summary': 'Encuentro estático en las Ruinas Hierro (Isla Hierro) al Nivel 30 al portar el Regigigas de evento en el equipo.',
        'locations': [{'area': 'Ruinas Hierro (Isla Hierro)', 'method': 'Encuentro estático al Nivel 30 (Evento Regigigas)'}]
    },

    # Singulares y Eventos Oficiales de Sinnoh
    489: {
        'type': 'gift',
        'badge_label': 'Crianza',
        'badge_color': 'sky',
        'summary': 'Eclosiona del huevo resultante al criar a Manaphy con Ditto en la Guardería Pokémon de Pueblo Sosiego.',
        'locations': [DAYCARE_LOCATION]
    },
    490: {
        'type': 'event',
        'badge_label': 'Huevo Ranger',
        'badge_color': 'sky',
        'summary': 'Transferir el Huevo de Manaphy desde un juego de Pokémon Ranger a través de la conexión inalámbrica de Nintendo DS.',
        'locations': [{'area': 'Tienda Pokémon', 'method': 'Entrega por repartidor tras transferir Huevo Ranger'}]
    },
    491: {
        'type': 'event',
        'badge_label': 'Evento Oficial',
        'badge_color': 'slate',
        'summary': 'Encuentro estático en Isla Lunanueva al Nivel 50 (requiere Tarjeta Miembro de evento y pesadilla en Posada del Recodo de Ciudad Canal).',
        'locations': [{'area': 'Isla Lunanueva', 'method': 'Evento oficial con Tarjeta Miembro al Nivel 50'}]
    },
    492: {
        'type': 'event',
        'badge_label': 'Evento Oficial',
        'badge_color': 'emerald',
        'summary': 'Encuentro estático en el Paraíso Floral al Nivel 30 (requiere Carta de Oak de evento a través de la Vía Costera de la Ruta 224).',
        'locations': [{'area': 'Paraíso Floral (Ruta 224)', 'method': 'Evento oficial con Carta de Oak al Nivel 30'}]
    },
    493: {
        'type': 'event',
        'badge_label': 'Evento Oficial',
        'badge_color': 'amber',
        'summary': 'Encuentro estático en la Sala del Origen sobre la Columna Lanza al Nivel 80 (requiere Flauta Azur de evento).',
        'locations': [{'area': 'Sala del Origen (Columna Lanza)', 'method': 'Evento oficial con Flauta Azur al Nivel 80'}]
    }
}


def format_wild_method(method_raw: str, conditions: list) -> str:
    cond_names = set(conditions)
    if 'radar-on' in cond_names:
        return 'Poké Radar'
    if 'swarm-yes' in cond_names:
        return 'Manada diaria'
    if 'slot2-firered' in cond_names:
        return 'Inserción Dual (GBA: Pokémon Rojo Fuego)'
    if 'slot2-leafgreen' in cond_names:
        return 'Inserción Dual (GBA: Pokémon Verde Hoja)'
    if 'slot2-ruby' in cond_names:
        return 'Inserción Dual (GBA: Pokémon Rubí)'
    if 'slot2-sapphire' in cond_names:
        return 'Inserción Dual (GBA: Pokémon Zafiro)'
    if 'slot2-emerald' in cond_names:
        return 'Inserción Dual (GBA: Pokémon Esmeralda)'
    if method_raw == 'surf':
        return 'Surf'
    if method_raw == 'super-rod':
        return 'Supercaña'
    if method_raw == 'good-rod':
        return 'Caña Buena'
    if method_raw == 'old-rod':
        return 'Caña Vieja'
    if method_raw == 'rock-smash':
        return 'Golpe Roca'
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
    print("Iniciando compilación oficial de catálogos para Pokémon Platino...")

    with open(CACHE_DIR / "pokemon_493_species.json", "r", encoding="utf-8") as f:
        species_493 = json.load(f)

    with open(CACHE_DIR / "encounters_platinum.json", "r", encoding="utf-8") as f:
        encounters_platinum = json.load(f)

    with open(CACHE_DIR / "wikidex_platinum_descriptions.json", "r", encoding="utf-8") as f:
        descriptions = json.load(f)

    with open(CACHE_DIR / "sinnoh_pokedex_210.json", "r", encoding="utf-8") as f:
        sinnoh_210 = json.load(f)

    with open(CACHE_DIR / "gen4_evolutions.json", "r", encoding="utf-8") as f:
        gen4_evos = json.load(f)

    with open(BASE_DIR / "tracker" / "data" / "evolution_stones.json", "r", encoding="utf-8") as f:
        evolution_stones = json.load(f)

    # Cargar transferencias desde exclusives.py
    from tracker.exclusives import VERSION_TRANSFERS_CATALOG, VERSION_TRANSFERS_META
    platinum_transfers = set(VERSION_TRANSFERS_CATALOG.get("platinum", []))
    platinum_origins = VERSION_TRANSFERS_META.get("platinum", {}).get("origins", {})

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

        raw_encs = encounters_platinum.get(str(nat_id), [])
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

        elif nat_id in platinum_transfers:
            origin = platinum_origins.get(nat_id, 'Cartuchos de GBA (RSE/FRLG)')
            summary = f"Inaccesible en estado salvaje en Pokémon Platino. Requiere transferir desde {origin} mediante el Parque Compi (Ruta 221) o mediante intercambio con otras ediciones"
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
            evo_stone_obj = resolve_evolution_stone(item_slug=item_slug_to_resolve, game_slug="platinum")
        else:
            evo_stone_obj = None

        p_type = sp['primary_type']
        s_type = sp['secondary_type']

        entry = {
            "id": unique_id,
            "entry_number": entry_num,
            "game_slug": "platinum",
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
            "game_sprite_url": f"/media/pokemon/sprites/platinum/{nat_id}.png",
            "game_sprite_shiny_url": f"/media/pokemon/sprites/platinum_shiny/{nat_id}.png",
            "game_sprite_back_url": f"/media/pokemon/sprites/platinum/back/{nat_id}.png",
            "game_sprite_shiny_back_url": f"/media/pokemon/sprites/platinum_shiny/back/{nat_id}.png",
            "modern_sprite_shiny_url": f"/media/pokemon/artwork/shiny/{nat_id}.png",
            "modal_retro_sprite_url": f"/media/pokemon/sprites/platinum_animated/{nat_id}.png",
            "modal_retro_sprite_shiny_url": f"/media/pokemon/sprites/platinum_animated_shiny/{nat_id}.png",
            "modal_retro_sprite_back_url": f"/media/pokemon/sprites/platinum/back/{nat_id}.png",
            "modal_retro_sprite_shiny_back_url": f"/media/pokemon/sprites/platinum_shiny/back/{nat_id}.png",
            "pc_icon_url": f"/media/pokemon/icons/gen4/{nat_id}.png",
            "cry_url": f"/media/pokemon/cries/legacy/{nat_id}.ogg",
            "flavor_text": flavor,
            "obtaining_info": obt_info,
            "evolution_stone": evo_stone_obj,
            "game_data": {
                "generation": 4,
                "game_slug": "platinum",
                "game_name": "Pokémon Platino",
                "is_regional": is_regional
            }
        }
        return entry

    # 1. Compilar Pokédex Regional (platinum.json - 210 Pokémon)
    print("Compilando Pokédex Regional de Sinnoh Expandida en Platino (210 entradas)...")
    platinum_regional_catalog = []
    for reg_num in range(1, 211):
        nat_id = int(sinnoh_210[str(reg_num)])
        unique_id = 5000 + reg_num
        platinum_regional_catalog.append(build_entry(nat_id, reg_num, is_regional=True, unique_id=unique_id))

    regional_file = CATALOGS_DIR / "platinum.json"
    with open(regional_file, "w", encoding="utf-8") as f:
        json.dump(platinum_regional_catalog, f, ensure_ascii=False, indent=2)
    print(f"[OK] Guardado {regional_file} con {len(platinum_regional_catalog)} entradas.")

    # 2. Compilar Pokédex Nacional (platinum_national.json - 493 Pokémon)
    print("Compilando Pokédex Nacional de Platino (493 entradas)...")
    platinum_national_catalog = []
    for nat_num in range(1, 494):
        unique_id = 5300 + nat_num
        platinum_national_catalog.append(build_entry(nat_num, nat_num, is_regional=False, unique_id=unique_id))

    national_file = CATALOGS_DIR / "platinum_national.json"
    with open(national_file, "w", encoding="utf-8") as f:
        json.dump(platinum_national_catalog, f, ensure_ascii=False, indent=2)
    print(f"[OK] Guardado {national_file} con {len(platinum_national_catalog)} entradas.")


if __name__ == "__main__":
    main()
