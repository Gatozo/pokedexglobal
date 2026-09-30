"""
Gestión de Pokémon con múltiples formas alternativas en Generaciones 1 a 3.
En las primeras 3 generaciones, los únicos Pokémon con formas alternas intercambiables
o visualizables en el mismo cartucho son Castform (#351) y Unown (#201).
(Deoxys cuenta con formas ligadas a juegos específicos: Rubí/Zafiro, Rojo Fuego, Verde Hoja y Esmeralda).
"""

from typing import List, Dict, Any


def get_castform_forms(game_slug: str = "ruby") -> List[Dict[str, Any]]:
    """
    Retorna las 4 formas climáticas de Castform (#351) en Hoenn:
    Forma Normal (Normal), Forma Sol (Fuego), Forma Lluvia (Agua), Forma Nieve (Hielo).
    En Pokémon Esmeralda, incluye las URLs de los sprites animados oficiales (.gif) para el modal individual.
    """
    slug = game_slug if game_slug in ["ruby", "sapphire", "emerald", "firered", "leafgreen"] else "ruby"
    is_emerald = (slug == "emerald")

    return [
        {
            "form_key": "normal",
            "name": "Forma Normal",
            "display_name": "Castform",
            "category": "Pokémon Clima",
            "primary_type": "normal",
            "primary_type_es": "Normal",
            "secondary_type": "",
            "secondary_type_es": "",
            "sprite_retro": f"/media/pokemon/sprites/{slug}/351.png",
            "sprite_retro_shiny": f"/media/pokemon/sprites/{slug}_shiny/351.png",
            "modal_retro_sprite_url": "/media/pokemon/sprites/emerald_animated/351.gif" if is_emerald else None,
            "modal_retro_sprite_shiny_url": "/media/pokemon/sprites/emerald_animated_shiny/351.gif" if is_emerald else None,
            "sprite_retro_back": f"/media/pokemon/sprites/{slug}/back/351.png",
            "sprite_retro_shiny_back": f"/media/pokemon/sprites/{slug}_shiny/back/351.png",
            "sprite_modern": "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/351.png",
            "sprite_modern_shiny": "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/shiny/351.png",
        },
        {
            "form_key": "sunny",
            "name": "Forma Sol",
            "display_name": "Castform (Sol)",
            "category": "Pokémon Clima",
            "primary_type": "fire",
            "primary_type_es": "Fuego",
            "secondary_type": "",
            "secondary_type_es": "",
            "sprite_retro": f"/media/pokemon/sprites/{slug}/castform/sunny.png",
            "sprite_retro_shiny": f"/media/pokemon/sprites/{slug}_shiny/castform/sunny.png",
            "modal_retro_sprite_url": "/media/pokemon/sprites/emerald_animated/castform/sunny.gif" if is_emerald else None,
            "modal_retro_sprite_shiny_url": "/media/pokemon/sprites/emerald_animated_shiny/castform/sunny.gif" if is_emerald else None,
            "sprite_retro_back": f"/media/pokemon/sprites/{slug}/back/castform/sunny.png",
            "sprite_retro_shiny_back": f"/media/pokemon/sprites/{slug}_shiny/back/castform/sunny.png",
            "sprite_modern": "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/10013.png",
            "sprite_modern_shiny": "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/shiny/10013.png",
        },
        {
            "form_key": "rainy",
            "name": "Forma Lluvia",
            "display_name": "Castform (Lluvia)",
            "category": "Pokémon Clima",
            "primary_type": "water",
            "primary_type_es": "Agua",
            "secondary_type": "",
            "secondary_type_es": "",
            "sprite_retro": f"/media/pokemon/sprites/{slug}/castform/rainy.png",
            "sprite_retro_shiny": f"/media/pokemon/sprites/{slug}_shiny/castform/rainy.png",
            "modal_retro_sprite_url": "/media/pokemon/sprites/emerald_animated/castform/rainy.gif" if is_emerald else None,
            "modal_retro_sprite_shiny_url": "/media/pokemon/sprites/emerald_animated_shiny/castform/rainy.gif" if is_emerald else None,
            "sprite_retro_back": f"/media/pokemon/sprites/{slug}/back/castform/rainy.png",
            "sprite_retro_shiny_back": f"/media/pokemon/sprites/{slug}_shiny/back/castform/rainy.png",
            "sprite_modern": "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/10014.png",
            "sprite_modern_shiny": "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/shiny/10014.png",
        },
        {
            "form_key": "snowy",
            "name": "Forma Nieve",
            "display_name": "Castform (Nieve)",
            "category": "Pokémon Clima",
            "primary_type": "ice",
            "primary_type_es": "Hielo",
            "secondary_type": "",
            "secondary_type_es": "",
            "sprite_retro": f"/media/pokemon/sprites/{slug}/castform/snowy.png",
            "sprite_retro_shiny": f"/media/pokemon/sprites/{slug}_shiny/castform/snowy.png",
            "modal_retro_sprite_url": "/media/pokemon/sprites/emerald_animated/castform/snowy.gif" if is_emerald else None,
            "modal_retro_sprite_shiny_url": "/media/pokemon/sprites/emerald_animated_shiny/castform/snowy.gif" if is_emerald else None,
            "sprite_retro_back": f"/media/pokemon/sprites/{slug}/back/castform/snowy.png",
            "sprite_retro_shiny_back": f"/media/pokemon/sprites/{slug}_shiny/back/castform/snowy.png",
            "sprite_modern": "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/10015.png",
            "sprite_modern_shiny": "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/shiny/10015.png",
        }
    ]


def get_unown_forms(game_slug: str = "gold") -> List[Dict[str, Any]]:
    """
    Retorna las 26 (Gen 2) o 28 (Gen 3+) formas alfabéticas de Unown (#201).
    """
    from .unown_data import get_unown_catalog
    raw_unown = get_unown_catalog(game_slug)
    forms = []
    for item in raw_unown:
        letter = item["letter"]
        forms.append({
            "form_key": letter,
            "name": item["display"],
            "display_name": item["display"],
            "category": "Pokémon Símbolo",
            "primary_type": "psychic",
            "primary_type_es": "Psíquico",
            "secondary_type": "",
            "secondary_type_es": "",
            "sprite_retro": item["sprite_normal"],
            "sprite_retro_shiny": item["sprite_shiny"],
            "sprite_retro_back": item.get("sprite_normal_back") or item["sprite_normal"].replace(f"/{item['sprite_normal'].split('/')[4]}/", f"/{item['sprite_normal'].split('/')[4]}/back/"),
            "sprite_retro_shiny_back": item.get("sprite_shiny_back") or item["sprite_shiny"].replace(f"/{item['sprite_shiny'].split('/')[4]}/", f"/{item['sprite_shiny'].split('/')[4]}/back/"),
            "sprite_modern": "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/201.png",
            "sprite_modern_shiny": "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/shiny/201.png",
        })
    return forms


def get_pokemon_forms(national_number: int, game_slug: str = "ruby") -> List[Dict[str, Any]]:
    """
    Punto de entrada unificado para obtener las formas alternas de un Pokémon.
    Retorna una lista vacía para especies sin formas alternativas.
    """
    if national_number == 351:
        return get_castform_forms(game_slug)
    elif national_number == 201:
        return get_unown_forms(game_slug)
    return []
