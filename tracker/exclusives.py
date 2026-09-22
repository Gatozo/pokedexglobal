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
    'yellow': ['red', 'blue'],
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
    'yellow': [],    # Amarillo no tiene exclusivos propios bloqueados hacia Rojo/Azul
    # Gen 2
    'gold': [56, 57, 58, 59, 167, 168, 207, 216, 217, 226],
    'silver': [37, 38, 52, 53, 165, 166, 225, 227, 228, 229, 231, 232],
    # Gen 3
    'ruby': [273, 274, 275, 303, 335, 338, 383],
    'sapphire': [270, 271, 272, 302, 336, 337, 382],
    'firered': [23, 24, 43, 44, 45, 54, 55, 58, 59, 123, 125, 198, 211, 215, 227, 246, 247, 248],
    'leafgreen': [27, 28, 69, 70, 71, 79, 80, 126, 127, 199, 200, 216, 217, 225, 228, 229, 241],
}

# Pokémon faltantes en Pokémon Amarillo que no se pueden capturar ni evolucionar de forma nativa
# y deben transferirse obligatoriamente desde Pokémon Rojo y/o Pokémon Azul para completar la Pokédex
YELLOW_MISSING_POKEMON: List[int] = [
    13, 14, 15,  # Weedle, Kakuna, Beedrill (Rojo / Azul)
    23, 24,      # Ekans, Arbok (Rojo)
    26,          # Raichu (El Pikachu inicial rehúsa evolucionar; requiere intercambio)
    52, 53,      # Meowth, Persian (Azul)
    109, 110,    # Koffing, Weezing (Rojo / Azul)
    124,         # Jynx (Rojo / Azul mediante intercambio NPC en Celeste)
    125,         # Electabuzz (Rojo)
    126,         # Magmar (Azul)
]

YELLOW_ORIGIN_MAP: Dict[int, str] = {
    13: "Rojo / Azul",
    14: "Rojo / Azul",
    15: "Rojo / Azul",
    23: "Rojo",
    24: "Rojo",
    26: "Rojo / Azul",
    52: "Azul",
    53: "Azul",
    109: "Rojo / Azul",
    110: "Rojo / Azul",
    124: "Rojo / Azul",
    125: "Rojo",
    126: "Azul",
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
    is_counterpart: bool,
    origin_badge: Optional[str] = None,
    entries_by_num: Optional[Dict[int, PokedexEntry]] = None
) -> Optional[Dict[str, Any]]:
    """Construye los datos estructurados de un Pokémon exclusivo o faltante para la plantilla."""
    # Buscar si existe en la Pokédex actual (en memoria si está disponible, o query diferida)
    if entries_by_num and national_num in entries_by_num:
        entry = entries_by_num[national_num]
    else:
        entry = current_pokedex.entries.select_related('pokemon').defer(
            'pokemon__raw_data',
            'pokemon__species_data',
            'pokemon__encounters_data',
            'pokemon__evolution_chain_data',
            'game_data'
        ).filter(pokemon__national_number=national_num).first()

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
        evolution_stone = entry.evolution_stone
    else:
        # Fallback a modelo Pokemon global diferido
        pokemon = Pokemon.objects.defer(
            'raw_data', 'species_data', 'encounters_data', 'evolution_chain_data'
        ).filter(national_number=national_num).first()
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
        evolution_stone = None

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
        'origin_badge': origin_badge,
        'evolution_stone': evolution_stone,
    }


def get_version_exclusives_context(
    current_game: Game,
    current_pokedex: Pokedex,
    caught_entry_ids: set,
    entries_by_num: Optional[Dict[int, PokedexEntry]] = None
) -> Optional[Dict[str, Any]]:
    """
    Retorna el contexto completo para el botón y el modal de exclusivos de versión / Pokémon a transferir.
    Si el juego no tiene contrapartes o no tiene exclusivos/faltantes registrados, devuelve None.
    """
    counterparts = GAME_COUNTERPARTS.get(current_game.slug, [])
    if not counterparts:
        return None

    current_gen = current_game.generation
    current_short_name = GAME_SHORT_NAMES.get(current_game.slug, current_game.slug.title())

    # Caso especial: Pokémon Amarillo
    # (Sus contrapartes son Rojo y Azul; no tiene exclusivos propios bloqueados hacia ellos,
    # pero carece de 13 especies salvajes que deben transferirse desde Rojo y/o Azul).
    if current_game.slug == 'yellow':
        is_yellow = True
        counterpart_slug = 'red-blue'
        counterpart_short_name = "Rojo y Azul"
        counterpart_name = "Pokémon Rojo y Pokémon Azul"
        counterpart_theme = 'amber'
        own_theme = 'amber'
        counterpart_exclusive_nums = YELLOW_MISSING_POKEMON
        own_exclusive_nums = []
        button_label = f"Pokémon a Transferir ({len(counterpart_exclusive_nums)})"
    else:
        is_yellow = False
        counterpart_slug = counterparts[0]
        counterpart_short_name = GAME_SHORT_NAMES.get(counterpart_slug, counterpart_slug.title())
        counterpart_exclusive_nums = VERSION_EXCLUSIVES_CATALOG.get(counterpart_slug, [])
        own_exclusive_nums = VERSION_EXCLUSIVES_CATALOG.get(current_game.slug, [])

        if not counterpart_exclusive_nums and not own_exclusive_nums:
            return None

        def _resolve_theme(slug: str) -> str:
            if slug in ['blue', 'sapphire', 'pearl', 'white', 'moon', 'shield', 'violet']:
                return 'blue'
            elif slug in ['gold', 'heartgold']:
                return 'gold'
            elif slug in ['silver', 'soulsilver']:
                return 'silver'
            elif slug in ['yellow']:
                return 'amber'
            return 'red'

        counterpart_theme = _resolve_theme(counterpart_slug)
        own_theme = _resolve_theme(current_game.slug)

        counterpart_game = Game.objects.filter(slug=counterpart_slug).first()
        counterpart_name = counterpart_game.display_name if counterpart_game else f"Pokémon {counterpart_short_name}"
        button_label = f"Exclusivos de {counterpart_short_name}"

    # 1. Construir lista de exclusivos / faltantes de la contraparte
    counterpart_list = []
    for num in counterpart_exclusive_nums:
        origin = YELLOW_ORIGIN_MAP.get(num) if is_yellow else None
        item = _build_exclusive_item(
            num, current_pokedex, current_gen, caught_entry_ids, is_counterpart=True, origin_badge=origin, entries_by_num=entries_by_num
        )
        if item:
            counterpart_list.append(item)

    # 2. Construir lista de exclusivos de la propia versión
    own_list = []
    for num in own_exclusive_nums:
        item = _build_exclusive_item(
            num, current_pokedex, current_gen, caught_entry_ids, is_counterpart=False, entries_by_num=entries_by_num
        )
        if item:
            own_list.append(item)

    # Estadísticas de exclusivos/faltantes
    counterpart_total = len(counterpart_list)
    counterpart_caught = sum(1 for p in counterpart_list if p['is_caught'])
    counterpart_percent = round((counterpart_caught / counterpart_total * 100), 1) if counterpart_total else 0

    own_total = len(own_list)
    own_caught = sum(1 for p in own_list if p['is_caught'])

    return {
        'has_exclusives': True,
        'button_label': button_label,
        'counterpart_slug': counterpart_slug,
        'counterpart_short_name': counterpart_short_name,
        'current_short_name': current_short_name,
        'counterpart_name': counterpart_name,
        'counterpart_theme': counterpart_theme,
        'own_theme': own_theme,
        'is_yellow': is_yellow,
        'counterpart_list': counterpart_list,
        'own_list': own_list,
        'counterpart_total': counterpart_total,
        'counterpart_caught': counterpart_caught,
        'counterpart_percent': counterpart_percent,
        'own_total': own_total,
        'own_caught': own_caught,
    }
