"""
Módulo centralizado para la gestión de versiones emparejadas y Pokémon exclusivos por edición.
Diseñado para ser escalable a todas las generaciones Pokémon presentes y futuras.
"""
from typing import Dict, List, Optional, Any
from .models import Game, Pokedex, PokedexEntry, Pokemon


# Emparejamiento de juegos por slug de versión (Juego -> [Juegos Contraparte])
GAME_COUNTERPARTS: Dict[str, List[str]] = {
    # Gen 1
    'red': ['blue'],
    'blue': ['red'],
    'yellow': [],
    # Gen 2
    'gold': ['silver'],
    'silver': ['gold'],
    'crystal': ['gold', 'silver'],
    # Gen 3
    'ruby': ['sapphire'],
    'sapphire': ['ruby'],
    'emerald': ['ruby', 'sapphire'],
    'firered': ['leafgreen'],
    'leafgreen': ['firered'],
    # Gen 4
    'diamond': ['pearl'],
    'pearl': ['diamond'],
    'platinum': ['diamond', 'pearl'],
    'heartgold': ['soulsilver'],
    'soulsilver': ['heartgold'],
    # Gen 5
    'black': ['white'],
    'white': ['black'],
    'black-2': ['white-2'],
    'white-2': ['black-2'],
    # Gen 6
    'x': ['y'],
    'y': ['x'],
    'omega-ruby': ['alpha-sapphire'],
    'alpha-sapphire': ['omega-ruby'],
    # Gen 7
    'sun': ['moon'],
    'moon': ['sun'],
    'ultra-sun': ['ultra-moon'],
    'ultra-moon': ['ultra-sun'],
    'lets-go-pikachu': ['lets-go-eevee'],
    'lets-go-eevee': ['lets-go-pikachu'],
    # Gen 8
    'sword': ['shield'],
    'shield': ['sword'],
    'brilliant-diamond': ['shining-pearl'],
    'shining-pearl': ['brilliant-diamond'],
    # Gen 9
    'scarlet': ['violet'],
    'violet': ['scarlet'],
}

# Catálogo canónico de números de Pokédex Nacional exclusivos de cada versión
VERSION_EXCLUSIVES_CATALOG: Dict[str, List[int]] = {
    # Gen 1
    'red': [
        23, 24,      # Ekans, Arbok
        43, 44, 45,  # Oddish, Gloom, Vileplume
        56, 57,      # Mankey, Primeape
        58, 59,      # Growlithe, Arcanine
        123,         # Scyther
        125,         # Electabuzz
    ],
    'blue': [
        27, 28,      # Sandshrew, Sandslash
        37, 38,      # Vulpix, Ninetales
        52, 53,      # Meowth, Persian
        69, 70, 71,  # Bellsprout, Weepinbell, Victreebel
        126,         # Magmar
        127,         # Pinsir
    ],
    # Gen 2
    'gold': [167, 168, 207, 216, 217, 226, 231, 232, 58, 59, 56, 57],
    'silver': [165, 166, 225, 227, 228, 229, 37, 38, 52, 53],
    # Gen 3
    'ruby': [273, 274, 275, 303, 335, 338, 383],
    'sapphire': [270, 271, 272, 302, 336, 337, 382],
    'firered': [23, 24, 43, 44, 45, 54, 55, 58, 59, 123, 125, 198, 211, 215, 227, 246, 247, 248],
    'leafgreen': [27, 28, 69, 70, 71, 79, 80, 126, 127, 199, 200, 216, 217, 225, 228, 229, 241],
}

# Nombres cortos amigables para los botones y pestañas (ej: "Exclusivos de Azul")
GAME_SHORT_NAMES: Dict[str, str] = {
    'red': 'Rojo',
    'blue': 'Azul',
    'yellow': 'Amarillo',
    'gold': 'Oro',
    'silver': 'Plata',
    'crystal': 'Cristal',
    'ruby': 'Rubí',
    'sapphire': 'Zafiro',
    'emerald': 'Esmeralda',
    'firered': 'Rojo Fuego',
    'leafgreen': 'Verde Hoja',
    'diamond': 'Diamante',
    'pearl': 'Perla',
    'platinum': 'Platino',
    'heartgold': 'HeartGold',
    'soulsilver': 'SoulSilver',
    'black': 'Negro',
    'white': 'Blanco',
    'black-2': 'Negro 2',
    'white-2': 'Blanco 2',
    'x': 'X',
    'y': 'Y',
    'omega-ruby': 'Rubí Omega',
    'alpha-sapphire': 'Zafiro Alfa',
    'sun': 'Sol',
    'moon': 'Luna',
    'ultra-sun': 'Ultra Sol',
    'ultra-moon': 'Ultra Luna',
    'lets-go-pikachu': 'Pikachu',
    'lets-go-eevee': 'Eevee',
    'sword': 'Espada',
    'shield': 'Escudo',
    'brilliant-diamond': 'Diamante Brillante',
    'shining-pearl': 'Perla Reluciente',
    'scarlet': 'Escarlata',
    'violet': 'Púrpura',
}


def _build_exclusive_item(
    national_num: int,
    current_pokedex: Pokedex,
    current_generation: int,
    caught_entry_ids: set,
    is_counterpart: bool
) -> Optional[Dict[str, Any]]:
    """Construye los datos estructurados de un Pokémon exclusivo para la plantilla."""
    # Buscar si existe en la Pokédex actual
    entry = current_pokedex.entries.select_related('pokemon').filter(pokemon__national_number=national_num).first()
    
    if entry:
        pokemon = entry.pokemon
        entry_id = entry.id
        number = entry.entry_number
        is_caught = entry.id in caught_entry_ids
        primary_type = entry.primary_type_display
        primary_type_es = entry.primary_type_es
        secondary_type = entry.secondary_type_display
        secondary_type_es = entry.secondary_type_es
        sprite_retro = entry.game_sprite_url or pokemon.sprite_url
        sprite_modern = pokemon.sprite_url
        obtaining_summary = entry.obtaining_info.get('summary', '') if entry.obtaining_info else ''
    else:
        # Fallback a modelo Pokemon global
        pokemon = Pokemon.objects.filter(national_number=national_num).first()
        if not pokemon:
            return None
        entry_id = None
        number = pokemon.national_number
        is_caught = False
        primary_type = pokemon.primary_type
        primary_type_es = pokemon.primary_type_es
        secondary_type = pokemon.secondary_type
        secondary_type_es = pokemon.secondary_type_es
        sprite_retro = pokemon.sprite_url
        sprite_modern = pokemon.sprite_url
        obtaining_summary = ''

    pc_icon_url = pokemon.get_pc_icon_url(generation=current_generation)

    return {
        'entry_id': entry_id,
        'national_number': national_num,
        'number': f"{number:03d}",
        'name': pokemon.display_name,
        'primary_type': primary_type,
        'primary_type_es': primary_type_es,
        'secondary_type': secondary_type or '',
        'secondary_type_es': secondary_type_es or '',
        'sprite_retro': sprite_retro,
        'sprite_modern': sprite_modern,
        'pc_icon_url': pc_icon_url,
        'is_caught': is_caught,
        'summary': obtaining_summary,
        'is_counterpart': is_counterpart,
    }


def get_version_exclusives_context(
    current_game: Game,
    current_pokedex: Pokedex,
    caught_entry_ids: set
) -> Optional[Dict[str, Any]]:
    """
    Retorna el contexto completo para el botón y el modal de exclusivos de versión.
    Si el juego no tiene contraparte o no tiene exclusivos registrados, devuelve None.
    """
    counterparts = GAME_COUNTERPARTS.get(current_game.slug, [])
    if not counterparts:
        return None

    counterpart_slug = counterparts[0]
    counterpart_short_name = GAME_SHORT_NAMES.get(counterpart_slug, counterpart_slug.title())
    current_short_name = GAME_SHORT_NAMES.get(current_game.slug, current_game.slug.title())

    counterpart_exclusive_nums = VERSION_EXCLUSIVES_CATALOG.get(counterpart_slug, [])
    own_exclusive_nums = VERSION_EXCLUSIVES_CATALOG.get(current_game.slug, [])

    if not counterpart_exclusive_nums and not own_exclusive_nums:
        return None

    current_gen = current_game.generation

    # 1. Construir lista de exclusivos de la contraparte
    counterpart_list = []
    for num in counterpart_exclusive_nums:
        item = _build_exclusive_item(
            num, current_pokedex, current_gen, caught_entry_ids, is_counterpart=True
        )
        if item:
            counterpart_list.append(item)

    # 2. Construir lista de exclusivos de la propia versión
    own_list = []
    for num in own_exclusive_nums:
        item = _build_exclusive_item(
            num, current_pokedex, current_gen, caught_entry_ids, is_counterpart=False
        )
        if item:
            own_list.append(item)

    # Estadísticas de exclusivos de contraparte
    counterpart_total = len(counterpart_list)
    counterpart_caught = sum(1 for p in counterpart_list if p['is_caught'])
    counterpart_percent = round((counterpart_caught / counterpart_total * 100), 1) if counterpart_total else 0

    own_total = len(own_list)
    own_caught = sum(1 for p in own_list if p['is_caught'])

    # Tema de color para la contraparte y la propia versión
    counterpart_theme = 'blue' if counterpart_slug in ['blue', 'sapphire', 'pearl', 'white', 'moon', 'shield', 'violet'] else 'red'
    own_theme = 'blue' if current_game.slug in ['blue', 'sapphire', 'pearl', 'white', 'moon', 'shield', 'violet'] else 'red'

    counterpart_game = Game.objects.filter(slug=counterpart_slug).first()
    counterpart_name = counterpart_game.display_name if counterpart_game else f"Pokémon {counterpart_short_name}"

    return {
        'has_exclusives': True,
        'button_label': f"Exclusivos de {counterpart_short_name}",
        'counterpart_slug': counterpart_slug,
        'counterpart_short_name': counterpart_short_name,
        'current_short_name': current_short_name,
        'counterpart_name': counterpart_name,
        'counterpart_theme': counterpart_theme,
        'own_theme': own_theme,
        'counterpart_list': counterpart_list,
        'own_list': own_list,
        'counterpart_total': counterpart_total,
        'counterpart_caught': counterpart_caught,
        'counterpart_percent': counterpart_percent,
        'own_total': own_total,
        'own_caught': own_caught,
    }
