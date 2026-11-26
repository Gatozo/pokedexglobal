"""
Gestión de Pokémon con múltiples formas alternativas canónicas.
Soporte completo y escalable para Generaciones 1 a 5.

- Gen 1 a 3: Castform (#351) y Unown (#201).
- Gen 4 (Diamante, Perla, Platino, HeartGold, SoulSilver):
  * Pichu (#172): Estándar y Picoreja (exclusiva HGSS).
  * Unown (#201): 28 formas (manejado de forma dedicada en Bloc Unown).
  * Castform (#351): 4 formas climáticas (sprites Gen 4 nativos).
  * Deoxys (#386): 4 formas (Normal, Ataque, Defensa, Velocidad).
  * Burmy (#412): 3 troncos (Planta, Arena, Basura por entorno de combate y crianza).
  * Wormadam (#413): 3 troncos fijos con tipos elementales distintos (Bicho/Planta, Bicho/Tierra, Bicho/Acero).
  * Cherrim (#421): 2 formas (Encapuchada y Soleada vía clima de sol en combate).
  * Shellos (#422): 2 formas geográficas (Mar Oeste / Mar Este).
  * Gastrodon (#423): 2 formas geográficas (Mar Oeste / Mar Este).
  * Rotom (#479), Giratina (#487), Shaymin (#492): formas desde Platino.
  * Arceus (#493): 17 formas (Normal + 16 Tablas elementales; excluyendo Tipo Hada de Gen 6).
- Gen 5 (Pokémon Negro):
  * Todas las formas anteriores con sprites animados .gif (frente y espalda, normal y variocolor),
    más Basculin (#550), Darmanitan (#555), Deerling (#585), Sawsbuck (#586), Meloetta (#648) y Genesect (#649).
"""

from typing import List, Dict, Any

GAME_SPRITE_CONFIG: Dict[str, Dict[str, Any]] = {
    # Gen 1
    "red":        {"gen": 1, "static_dir": "red",        "anim_dir": None,                  "anim_ext": None,   "has_animated_back": False, "back_modal_mode": None},
    "blue":       {"gen": 1, "static_dir": "blue",       "anim_dir": None,                  "anim_ext": None,   "has_animated_back": False, "back_modal_mode": None},
    "yellow":     {"gen": 1, "static_dir": "yellow",     "anim_dir": None,                  "anim_ext": None,   "has_animated_back": False, "back_modal_mode": None},
    # Gen 2
    "gold":       {"gen": 2, "static_dir": "gold",       "anim_dir": None,                  "anim_ext": None,   "has_animated_back": False, "back_modal_mode": None},
    "silver":     {"gen": 2, "static_dir": "silver",     "anim_dir": None,                  "anim_ext": None,   "has_animated_back": False, "back_modal_mode": None},
    "crystal":    {"gen": 2, "static_dir": "crystal",    "anim_dir": "crystal_animated",    "anim_ext": ".gif", "has_animated_back": False, "back_modal_mode": None},
    # Gen 3
    "ruby":       {"gen": 3, "static_dir": "ruby",       "anim_dir": None,                  "anim_ext": None,   "has_animated_back": False, "back_modal_mode": None},
    "sapphire":   {"gen": 3, "static_dir": "sapphire",   "anim_dir": None,                  "anim_ext": None,   "has_animated_back": False, "back_modal_mode": None},
    "emerald":    {"gen": 3, "static_dir": "emerald",    "anim_dir": "emerald_animated",    "anim_ext": ".gif", "has_animated_back": False, "back_modal_mode": None},
    "firered":    {"gen": 3, "static_dir": "firered",    "anim_dir": None,                  "anim_ext": None,   "has_animated_back": False, "back_modal_mode": None, "shared_hoenn_form_dir": "ruby"},
    "leafgreen":  {"gen": 3, "static_dir": "leafgreen",  "anim_dir": None,                  "anim_ext": None,   "has_animated_back": False, "back_modal_mode": None, "shared_hoenn_form_dir": "ruby"},
    # Gen 4
    "diamond":    {"gen": 4, "static_dir": "diamond",    "anim_dir": "diamond_animated",    "anim_ext": ".png", "has_animated_back": False, "back_modal_mode": "static"},
    "pearl":      {"gen": 4, "static_dir": "pearl",      "anim_dir": "pearl_animated",      "anim_ext": ".png", "has_animated_back": False, "back_modal_mode": "static"},
    "platinum":   {"gen": 4, "static_dir": "platinum",   "anim_dir": "platinum_animated",   "anim_ext": ".png", "has_animated_back": False, "back_modal_mode": "static"},
    "heartgold":  {"gen": 4, "static_dir": "heartgold",  "anim_dir": "heartgold_animated",  "anim_ext": ".png", "has_animated_back": False, "back_modal_mode": "static"},
    "soulsilver": {"gen": 4, "static_dir": "soulsilver", "anim_dir": "soulsilver_animated", "anim_ext": ".png", "has_animated_back": False, "back_modal_mode": "static"},
    # Gen 5
    "black":      {"gen": 5, "static_dir": "black",      "anim_dir": "black_animated",      "anim_ext": ".gif", "has_animated_back": True,  "back_modal_mode": "animated"},
    "white":      {"gen": 5, "static_dir": "white",      "anim_dir": "white_animated",      "anim_ext": ".gif", "has_animated_back": True,  "back_modal_mode": "animated"},
    "black-2":    {"gen": 5, "static_dir": "black-2",    "anim_dir": "black-2_animated",    "anim_ext": ".gif", "has_animated_back": True,  "back_modal_mode": "animated"},
}

GEN2_FORM_GAMES = {s for s, cfg in GAME_SPRITE_CONFIG.items() if cfg["gen"] == 2}
GEN3_FORM_GAMES = {s for s, cfg in GAME_SPRITE_CONFIG.items() if cfg["gen"] == 3}
GEN4_FORM_GAMES = {s for s, cfg in GAME_SPRITE_CONFIG.items() if cfg["gen"] == 4}
GEN5_FORM_GAMES = {s for s, cfg in GAME_SPRITE_CONFIG.items() if cfg["gen"] == 5}
B2W2_FORM_GAMES = {"black-2", "white-2"}

TRANSFER_TEMPLATES_BY_GEN: Dict[int, Dict[str, Any]] = {
    5: {
        "area": "Laboratorio de Pokétransfer (Ruta 15)",
        "method": "Pokétransfer (transferencia desde 4.ª generación)",
        "badge_label": "Pokétransfer",
        "badge_color": "amber",
        "type": "transfer",
    },
}


def get_game_sprite_config(game_slug: str) -> Dict[str, Any]:
    """Retorna la configuración de sprites de una edición registrada; falla explícitamente si falta."""
    clean = (game_slug or "").replace("_national", "")
    if clean not in GAME_SPRITE_CONFIG:
        raise ValueError(
            f"Edición '{game_slug}' no registrada en GAME_SPRITE_CONFIG. "
            "Regístrala en tracker/pokemon_forms.py antes de resolver formas o sprites."
        )
    return GAME_SPRITE_CONFIG[clean]


def _get_transfer_obt_meta(generation: int, badge_color: str = None) -> Dict[str, Any]:
    """Retorna los metadatos de badge y tipo de obtención por transferencia para una generación."""
    tpl = TRANSFER_TEMPLATES_BY_GEN.get(generation)
    if not tpl:
        return {}
    return {
        "type": tpl["type"],
        "badge_label": tpl["badge_label"],
        "badge_color": badge_color or tpl["badge_color"],
    }


def _build_retro_form_sprites(
    slug: str,
    rel_static: str,
    rel_anim: str = None,
    include_back_modal: bool = True,
    rel_back_static: str = None,
    rel_back_anim: str = None,
    back_slug: str = None,
) -> Dict[str, Any]:
    """
    Genera de manera centralizada todas las URLs de sprites retro (estáticos y animados,
    frente y espalda, normal y variocolor) desde GAME_SPRITE_CONFIG.
    Falla explícitamente ante juegos no configurados para evitar caídas silenciosas.
    """
    cfg = get_game_sprite_config(slug)
    static_dir = cfg["static_dir"]
    anim_dir = cfg["anim_dir"]
    anim_ext = cfg["anim_ext"]

    back_cfg = get_game_sprite_config(back_slug) if back_slug else cfg
    back_static_dir = back_cfg["static_dir"]
    back_anim_dir = back_cfg["anim_dir"]
    back_anim_ext = back_cfg["anim_ext"]
    back_modal_mode = back_cfg["back_modal_mode"]

    anim_stem = rel_anim or rel_static
    static_back_stem = rel_back_static or rel_static
    anim_back_stem = rel_back_anim or rel_back_static or anim_stem

    modal_front = f"/media/pokemon/sprites/{anim_dir}/{anim_stem}{anim_ext}" if anim_dir else None
    modal_front_shiny = f"/media/pokemon/sprites/{anim_dir}_shiny/{anim_stem}{anim_ext}" if anim_dir else None

    modal_back = None
    modal_back_shiny = None
    if include_back_modal:
        if back_modal_mode == "animated" and back_anim_dir:
            modal_back = f"/media/pokemon/sprites/{back_anim_dir}/back/{anim_back_stem}{back_anim_ext}"
            modal_back_shiny = f"/media/pokemon/sprites/{back_anim_dir}_shiny/back/{anim_back_stem}{back_anim_ext}"
        elif back_modal_mode == "static":
            modal_back = f"/media/pokemon/sprites/{back_static_dir}/back/{static_back_stem}.png"
            modal_back_shiny = f"/media/pokemon/sprites/{back_static_dir}_shiny/back/{static_back_stem}.png"

    sprites: Dict[str, Any] = {
        "sprite_retro": f"/media/pokemon/sprites/{static_dir}/{rel_static}.png",
        "sprite_retro_shiny": f"/media/pokemon/sprites/{static_dir}_shiny/{rel_static}.png",
        "modal_retro_sprite_url": modal_front,
        "modal_retro_sprite_shiny_url": modal_front_shiny,
        "sprite_retro_back": f"/media/pokemon/sprites/{back_static_dir}/back/{static_back_stem}.png",
        "sprite_retro_shiny_back": f"/media/pokemon/sprites/{back_static_dir}_shiny/back/{static_back_stem}.png",
    }
    if modal_back is not None:
        sprites["modal_retro_sprite_back_url"] = modal_back
        sprites["modal_retro_sprite_shiny_back_url"] = modal_back_shiny
    return sprites


def get_castform_forms(game_slug: str = "ruby") -> List[Dict[str, Any]]:
    """
    Retorna las 4 formas climáticas de Castform (#351):
    Forma Normal (Normal), Forma Sol (Fuego), Forma Lluvia (Agua), Forma Nieve (Hielo).
    Soporta sprites de Hoenn (Gen 3), Sinnoh/Johto (Gen 4) y Teselia (Gen 5 animados .gif).
    """
    clean_slug = (game_slug or "ruby").replace("_national", "")
    cfg = get_game_sprite_config(clean_slug)
    # Kanto (FRLG) solo contiene el sprite base 351.png; sus variantes climáticas provienen de Hoenn (ruby).
    weather_slug = cfg.get("shared_hoenn_form_dir", clean_slug)

    notes_normal = [
        {
            "title": "Mecánica de Predicción",
            "text": "Cambio de forma temporal y exclusivo en combate mediante su habilidad Predicción según el clima activo (Sol intenso, Lluvia o Granizo). Fuera de combate siempre permanece en Forma Normal.",
            "tag": "Clima",
            "icon": "/media/items/rule-book.png",
        }
    ]
    notes_sunny = [
        {
            "title": "Forma Sol (Día Soleado)",
            "text": "Se transforma durante el combate cuando hay luz solar intensa. Su tipo elemental cambia a Fuego puro.",
            "tag": "Clima",
            "icon": "/media/items/sun-stone.png",
        }
    ]
    notes_rainy = [
        {
            "title": "Forma Lluvia (Danza Lluvia)",
            "text": "Se transforma durante el combate cuando cae lluvia. Su tipo elemental cambia a Agua puro.",
            "tag": "Clima",
            "icon": "/media/items/water-stone.png",
        }
    ]
    notes_snowy = [
        {
            "title": "Forma Nieve (Granizo)",
            "text": "Se transforma durante el combate bajo una tormenta de granizo. Su tipo elemental cambia a Hielo puro.",
            "tag": "Clima",
            "icon": "/media/items/never-melt-ice.png",
        }
    ]

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
            **_build_retro_form_sprites(clean_slug, "351"),
            "sprite_modern": "/media/pokemon/home/351.png",
            "sprite_modern_shiny": "/media/pokemon/home/shiny/351.png",
            "notes": notes_normal,
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
            **_build_retro_form_sprites(weather_slug, "castform/sunny"),
            "sprite_modern": "/media/pokemon/home/10013.png",
            "sprite_modern_shiny": "/media/pokemon/home/shiny/10013.png",
            "notes": notes_sunny,
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
            **_build_retro_form_sprites(weather_slug, "castform/rainy"),
            "sprite_modern": "/media/pokemon/home/10014.png",
            "sprite_modern_shiny": "/media/pokemon/home/shiny/10014.png",
            "notes": notes_rainy,
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
            **_build_retro_form_sprites(weather_slug, "castform/snowy"),
            "sprite_modern": "/media/pokemon/home/10015.png",
            "sprite_modern_shiny": "/media/pokemon/home/shiny/10015.png",
            "notes": notes_snowy,
        }
    ]


def get_deoxys_forms(game_slug: str = "diamond") -> List[Dict[str, Any]]:
    """
    Retorna las 4 formas de Deoxys (#386):
    Normal, Ataque, Defensa, Velocidad.
    En Sinnoh: Meteoritos de Ciudad Rocavelo.
    En HeartGold/SoulSilver: Meteoritos de la Ruta 3 (Kanto).
    En Teselia: Meteorito del Museo de Ciudad Esmalte.
    """
    clean_slug = (game_slug or "diamond").replace("_national", "")
    is_hgss = clean_slug in ["heartgold", "soulsilver"]
    is_gen5 = clean_slug in GEN5_FORM_GAMES
    slug = clean_slug

    if is_gen5:
        note_base = "Al examinar el meteorito expuesto en el Museo de Ciudad Esmalte, Deoxys cambia sucesivamente de forma entre Normal, Ataque, Defensa y Velocidad."
        note_normal = {
            "title": "Meteorito del Museo de Ciudad Esmalte",
            "text": f"{note_base} El primer examen activa la Forma Normal.",
            "tag": "Meteorito",
            "icon": "/media/items/meteorite.png",
        }
        note_attack = {
            "title": "Meteorito de Ciudad Esmalte (Ataque)",
            "text": f"{note_base} Aumenta drásticamente su Ataque y Ataque Especial reduciendo sus Defensas.",
            "tag": "Meteorito",
            "icon": "/media/items/meteorite.png",
        }
        note_defense = {
            "title": "Meteorito de Ciudad Esmalte (Defensa)",
            "text": f"{note_base} Maximiza sus estadísticas defensivas a costa de velocidad y poder ofensivo.",
            "tag": "Meteorito",
            "icon": "/media/items/meteorite.png",
        }
        note_speed = {
            "title": "Meteorito de Ciudad Esmalte (Velocidad)",
            "text": f"{note_base} Otorga una de las mayores estadísticas de Velocidad de todo el juego.",
            "tag": "Meteorito",
            "icon": "/media/items/meteorite.png",
        }
    elif is_hgss:
        note_normal = {
            "title": "Meteoritos de la Ruta 3 (Kanto)",
            "text": "En HeartGold y SoulSilver, Deoxys cambia entre sus 4 formas interactuando con los meteoritos situados en la Ruta 3 (Kanto). El meteorito superior activa la Forma Normal.",
            "tag": "Meteorito",
            "icon": "/media/items/meteorite.png",
        }
        note_attack = {
            "title": "Meteorito de Ataque (Ruta 3)",
            "text": "Interactúa con el meteorito inferior en la Ruta 3 (Kanto) para transformarlo a su Forma Ataque. Aumenta drásticamente su Ataque y Ataque Especial reduciendo sus Defensas.",
            "tag": "Meteorito",
            "icon": "/media/items/meteorite.png",
        }
        note_defense = {
            "title": "Meteorito de Defensa (Ruta 3)",
            "text": "Interactúa con el meteorito central izquierdo en la Ruta 3 (Kanto) para transformarlo a su Forma Defensa. Maximiza sus estadísticas defensivas a costa de velocidad y poder ofensivo.",
            "tag": "Meteorito",
            "icon": "/media/items/meteorite.png",
        }
        note_speed = {
            "title": "Meteorito de Velocidad (Ruta 3)",
            "text": "Interactúa con el meteorito central derecho en la Ruta 3 (Kanto) para transformarlo a su Forma Velocidad. Otorga una de las mayores estadísticas de Velocidad de todo el juego.",
            "tag": "Meteorito",
            "icon": "/media/items/meteorite.png",
        }
    else:
        note_normal = {
            "title": "Meteoritos de Ciudad Rocavelo",
            "text": "En Diamante y Perla, Deoxys cambia libremente entre sus 4 formas interactuando con los 4 meteoritos extraterrestres al sureste de Ciudad Rocavelo. El meteorito superior izquierdo activa la Forma Normal.",
            "tag": "Meteorito",
            "icon": "/media/items/meteorite.png",
        }
        note_attack = {
            "title": "Meteorito de Ataque (Ciudad Rocavelo)",
            "text": "Interactúa con el meteorito inferior derecho en Ciudad Rocavelo para transformarlo a su Forma Ataque. Aumenta drásticamente su Ataque y Ataque Especial reduciendo sus Defensas.",
            "tag": "Meteorito",
            "icon": "/media/items/meteorite.png",
        }
        note_defense = {
            "title": "Meteorito de Defensa (Ciudad Rocavelo)",
            "text": "Interactúa con el meteorito inferior izquierdo en Ciudad Rocavelo para transformarlo a su Forma Defensa. Maximiza sus estadísticas defensivas a costa de velocidad y poder ofensivo.",
            "tag": "Meteorito",
            "icon": "/media/items/meteorite.png",
        }
        note_speed = {
            "title": "Meteorito de Velocidad (Ciudad Rocavelo)",
            "text": "Interactúa con el meteorito superior derecho en Ciudad Rocavelo para transformarlo a su Forma Velocidad. Otorga una de las mayores estadísticas de Velocidad de todo el juego.",
            "tag": "Meteorito",
            "icon": "/media/items/meteorite.png",
        }

    return [
        {
            "form_key": "normal",
            "name": "Forma Normal",
            "display_name": "Deoxys",
            "category": "Pokémon ADN",
            "primary_type": "psychic",
            "primary_type_es": "Psíquico",
            "secondary_type": "",
            "secondary_type_es": "",
            **_build_retro_form_sprites(slug, "386", rel_anim="deoxys/normal"),
            "sprite_modern": "/media/pokemon/home/386.png",
            "sprite_modern_shiny": "/media/pokemon/home/shiny/386.png",
            "notes": [note_normal],
        },
        {
            "form_key": "attack",
            "name": "Forma Ataque",
            "display_name": "Deoxys (Ataque)",
            "category": "Pokémon ADN",
            "primary_type": "psychic",
            "primary_type_es": "Psíquico",
            "secondary_type": "",
            "secondary_type_es": "",
            **_build_retro_form_sprites(slug, "deoxys/attack"),
            "sprite_modern": "/media/pokemon/home/10001.png",
            "sprite_modern_shiny": "/media/pokemon/home/shiny/10001.png",
            "notes": [note_attack],
        },
        {
            "form_key": "defense",
            "name": "Forma Defensa",
            "display_name": "Deoxys (Defensa)",
            "category": "Pokémon ADN",
            "primary_type": "psychic",
            "primary_type_es": "Psíquico",
            "secondary_type": "",
            "secondary_type_es": "",
            **_build_retro_form_sprites(slug, "deoxys/defense"),
            "sprite_modern": "/media/pokemon/home/10002.png",
            "sprite_modern_shiny": "/media/pokemon/home/shiny/10002.png",
            "notes": [note_defense],
        },
        {
            "form_key": "speed",
            "name": "Forma Velocidad",
            "display_name": "Deoxys (Velocidad)",
            "category": "Pokémon ADN",
            "primary_type": "psychic",
            "primary_type_es": "Psíquico",
            "secondary_type": "",
            "secondary_type_es": "",
            **_build_retro_form_sprites(slug, "deoxys/speed"),
            "sprite_modern": "/media/pokemon/home/10003.png",
            "sprite_modern_shiny": "/media/pokemon/home/shiny/10003.png",
            "notes": [note_speed],
        }
    ]


def get_burmy_forms(game_slug: str = "diamond") -> List[Dict[str, Any]]:
    """
    Retorna los 3 troncos de Burmy (#412):
    Tronco Planta, Tronco Arena, Tronco Basura.
    En Sinnoh: Árboles de miel y combates en exterior/cueva/edificio.
    En HeartGold/SoulSilver: Salvaje con Golpe Cabeza en Ruta 38 (Tronco Planta); camuflajes combatiendo en Johto/Kanto.
    En Teselia (Gen 5): Obtenible por Pokétransfer (Ruta 15) o crianza en Ruta 3; camuflajes combatiendo o eclosionando en Teselia.
    """
    clean_slug = (game_slug or "diamond").replace("_national", "")
    is_hgss = clean_slug in ["heartgold", "soulsilver"]
    is_gen5 = clean_slug in GEN5_FORM_GAMES
    slug = clean_slug

    gen5_obt_meta = _get_transfer_obt_meta(5) if is_gen5 else {}

    if is_gen5:
        plant_summary = "Inaccesible en estado salvaje en Teselia. Se obtiene mediante Pokétransfer (Ruta 15) desde 4.ª generación o por crianza; adopta este tronco al combatir o eclosionar en exteriores."
        plant_locations = [
            {"area": "Laboratorio de Pokétransfer (Ruta 15)", "method": "Pokétransfer (transferencia desde 4.ª generación)"},
            {"area": "Ruta 3 (Guardería Pokémon)", "method": "Crianza de huevo (eclosión en exteriores / rutas)"}
        ]
        plant_notes = [
            {
                "title": "Camuflaje por Terreno (Teselia)",
                "text": "Adopta el Tronco Planta tras combatir en exteriores con hierba, bosques o rutas abiertas de Teselia (ej: Ruta 3, Bosque Azulejo).",
                "tag": "Entorno",
                "icon": "/media/items/miracle-seed.png",
            },
            {
                "title": "Crianza y Eclosión",
                "text": "Si el huevo eclosiona mientras el jugador se encuentra en una ruta exterior con hierba, el Burmy recién nacido tendrá Tronco Planta.",
                "tag": "Crianza",
                "icon": "/media/items/mystery-egg.png",
            },
            {
                "title": "Evolución por Género",
                "text": "Las hembras evolucionan a Wormadam (Tronco Planta) a Nivel 20 fijando este tronco. Los machos siempre evolucionan a Mothim.",
                "tag": "Evolución",
                "icon": "/media/items/rule-book.png",
            }
        ]

        sandy_summary = "Inaccesible en estado salvaje en Teselia. Obtenido por Pokétransfer (Ruta 15) o crianza, adopta este camuflaje tras combatir o eclosionar en cuevas, desiertos o playas."
        sandy_locations = [
            {"area": "Laboratorio de Pokétransfer (Ruta 15)", "method": "Pokétransfer (transferencia desde 4.ª generación)"},
            {"area": "Ruta 3 (Guardería Pokémon)", "method": "Crianza de huevo (eclosión en cueva, desierto o playa)"}
        ]
        sandy_notes = [
            {
                "title": "Camuflaje por Terreno (Teselia)",
                "text": "Adopta el Tronco Arena tras combatir dentro de cuevas, desiertos o playas de Teselia (ej: Zona Desierto, Cueva Electrorroca, Monte Tuerca, Bahía Arenisca).",
                "tag": "Entorno",
                "icon": "/media/items/soft-sand.png",
            },
            {
                "title": "Crianza y Eclosión",
                "text": "Si el huevo eclosiona en una cueva, desierto o playa arenosa, el Burmy recién nacido tendrá Tronco Arena.",
                "tag": "Crianza",
                "icon": "/media/items/mystery-egg.png",
            },
            {
                "title": "Evolución por Género",
                "text": "Las hembras evolucionan a Wormadam (Tronco Arena) a Nivel 20 fijando este tronco y ganando el tipo Tierra. Los machos siempre evolucionan a Mothim.",
                "tag": "Evolución",
                "icon": "/media/items/rule-book.png",
            }
        ]

        trash_summary = "Inaccesible en estado salvaje en Teselia. Obtenido por Pokétransfer (Ruta 15) o crianza, adopta este camuflaje tras combatir o eclosionar dentro de edificios."
        trash_locations = [
            {"area": "Laboratorio de Pokétransfer (Ruta 15)", "method": "Pokétransfer (transferencia desde 4.ª generación)"},
            {"area": "Ruta 3 (Guardería Pokémon)", "method": "Crianza de huevo (eclosión dentro de un edificio)"}
        ]
        trash_notes = [
            {
                "title": "Camuflaje por Terreno (Teselia)",
                "text": "Adopta el Tronco Basura tras combatir dentro de cualquier edificio, gimnasio o estructura cerrada de Teselia (ej: Ciudad Porcelana, Liga Pokémon).",
                "tag": "Entorno",
                "icon": "/media/items/metal-coat.png",
            },
            {
                "title": "Crianza y Eclosión",
                "text": "Si el huevo eclosiona mientras el jugador se encuentra dentro de un edificio o estancia interior, el Burmy recién nacido tendrá Tronco Basura.",
                "tag": "Crianza",
                "icon": "/media/items/mystery-egg.png",
            },
            {
                "title": "Evolución por Género",
                "text": "Las hembras evolucionan a Wormadam (Tronco Basura) a Nivel 20 fijando este tronco y ganando el tipo Acero. Los machos siempre evolucionan a Mothim.",
                "tag": "Evolución",
                "icon": "/media/items/rule-book.png",
            }
        ]
    elif is_hgss:
        plant_summary = "Salvaje en árboles especiales de la Ruta 38 usando Golpe Cabeza (o combatiendo en hierba y exteriores)."
        plant_locations = [
            {"area": "Ruta 38", "method": "Golpe Cabeza (Árboles especiales)"},
            {"area": "Ruta 34 (Guardería Pokémon)", "method": "Crianza de huevo"}
        ]
        plant_notes = [
            {
                "title": "Camuflaje por Terreno",
                "text": "En Johto, Burmy salvaje aparece exclusivamente con Tronco Planta en la Ruta 38 al usar Golpe Cabeza en árboles especiales.",
                "tag": "Entorno",
                "icon": "/media/items/miracle-seed.png",
            },
            {
                "title": "Evolución por Género",
                "text": "Las hembras evolucionan a Wormadam (Tronco Planta) a Nivel 20 fijando este tronco. Los machos siempre evolucionan a Mothim.",
                "tag": "Evolución",
                "icon": "/media/items/rule-book.png",
            }
        ]

        sandy_summary = "Adopta este camuflaje tras combatir en cuevas o playas de Johto y Kanto (ej: Cueva Unión, Cueva Oscura, Islas Remolino)."
        sandy_locations = [
            {"area": "Cuevas y Playas de Johto / Kanto", "method": "Combatir en cueva o playa"}
        ]
        sandy_notes = [
            {
                "title": "Camuflaje por Terreno",
                "text": "Adopta el Tronco Arena tras combatir en cualquier cueva, superficie rocosa o playa arenosa de Johto o Kanto.",
                "tag": "Entorno",
                "icon": "/media/items/soft-sand.png",
            },
            {
                "title": "Evolución por Género",
                "text": "Las hembras evolucionan a Wormadam (Tronco Arena) a Nivel 20 fijando este tronco y ganando el tipo Tierra. Los machos siempre evolucionan a Mothim.",
                "tag": "Evolución",
                "icon": "/media/items/rule-book.png",
            }
        ]

        trash_summary = "Adopta este camuflaje tras combatir dentro de edificios e interiores cerrados de Johto y Kanto (ej: Gimnasios, Torres, Silph S.A.)."
        trash_locations = [
            {"area": "Edificios e Interiores de Johto / Kanto", "method": "Combatir en cualquier edificio cerrado"}
        ]
        trash_notes = [
            {
                "title": "Camuflaje por Terreno",
                "text": "Adopta el Tronco Basura tras combatir dentro de cualquier edificio, gimnasio o estructura cerrada.",
                "tag": "Entorno",
                "icon": "/media/items/metal-coat.png",
            },
            {
                "title": "Evolución por Género",
                "text": "Las hembras evolucionan a Wormadam (Tronco Basura) a Nivel 20 fijando este tronco y ganando el tipo Acero. Los machos siempre evolucionan a Mothim.",
                "tag": "Evolución",
                "icon": "/media/items/rule-book.png",
            }
        ]
    else:
        plant_summary = "Salvaje en árboles de miel en exteriores y rutas abiertas."
        plant_locations = [
            {"area": "Árboles de Miel (Exteriores)", "method": "Untar Miel (Hierba/Rutas abiertas)"}
        ]
        plant_notes = [
            {
                "title": "Camuflaje por Terreno",
                "text": "Adopta el Tronco Planta tras combatir en exteriores con hierba, flores o rutas abiertas.",
                "tag": "Entorno",
                "icon": "/media/items/miracle-seed.png",
            },
            {
                "title": "Crianza y Eclosión",
                "text": "Si el huevo eclosiona mientras el jugador se encuentra en una ruta exterior con hierba, el Burmy recién nacido tendrá Tronco Planta.",
                "tag": "Crianza",
                "icon": "/media/items/mystery-egg.png",
            },
            {
                "title": "Evolución por Género",
                "text": "Las hembras evolucionan a Wormadam (Tronco Planta) a Nivel 20 fijando este tronco. Los machos siempre evolucionan a Mothim.",
                "tag": "Evolución",
                "icon": "/media/items/rule-book.png",
            }
        ]

        sandy_summary = "Adopta este camuflaje tras combatir en cuevas o playas arenosas."
        sandy_locations = [
            {"area": "Cuevas y Playas de Sinnoh", "method": "Combatir en cueva/playa o Árboles de Miel de la zona"}
        ]
        sandy_notes = [
            {
                "title": "Camuflaje por Terreno",
                "text": "Adopta el Tronco Arena tras combatir dentro de cuevas, zonas rocosas, playas o montañas (ej: Monte Corona, Cueva Extravío).",
                "tag": "Entorno",
                "icon": "/media/items/soft-sand.png",
            },
            {
                "title": "Crianza y Eclosión",
                "text": "Si el huevo eclosiona mientras el jugador se encuentra en una cueva o playa, el Burmy recién nacido tendrá Tronco Arena.",
                "tag": "Crianza",
                "icon": "/media/items/mystery-egg.png",
            },
            {
                "title": "Evolución por Género",
                "text": "Las hembras evolucionan a Wormadam (Tronco Arena) a Nivel 20 fijando este tronco y ganando el tipo Tierra. Los machos siempre evolucionan a Mothim.",
                "tag": "Evolución",
                "icon": "/media/items/rule-book.png",
            }
        ]

        trash_summary = "Adopta este camuflaje tras combatir dentro de edificios o estancias cerradas."
        trash_locations = [
            {"area": "Edificios e Interiores", "method": "Combatir en cualquier edificio cerrado"}
        ]
        trash_notes = [
            {
                "title": "Camuflaje por Terreno",
                "text": "Adopta el Tronco Basura tras combatir dentro de edificios, gimnasios o estructuras cerradas.",
                "tag": "Entorno",
                "icon": "/media/items/metal-coat.png",
            },
            {
                "title": "Crianza y Eclosión",
                "text": "Si el huevo eclosiona mientras el jugador se encuentra dentro de un edificio o estancia interior, el Burmy recién nacido tendrá Tronco Basura.",
                "tag": "Crianza",
                "icon": "/media/items/mystery-egg.png",
            },
            {
                "title": "Evolución por Género",
                "text": "Las hembras evolucionan a Wormadam (Tronco Basura) a Nivel 20 fijando este tronco y ganando el tipo Acero. Los machos siempre evolucionan a Mothim.",
                "tag": "Evolución",
                "icon": "/media/items/rule-book.png",
            }
        ]

    return [
        {
            "form_key": "plant",
            "name": "Tronco Planta",
            "display_name": "Burmy (Tronco Planta)",
            "category": "Pokémon Larva",
            "primary_type": "bug",
            "primary_type_es": "Bicho",
            "secondary_type": "",
            "secondary_type_es": "",
            **_build_retro_form_sprites(slug, "burmy/plant"),
            "sprite_modern": "/media/pokemon/home/412.png",
            "sprite_modern_shiny": "/media/pokemon/home/shiny/412.png",
            "summary": plant_summary,
            "locations": plant_locations,
            "notes": plant_notes,
            **gen5_obt_meta,
        },
        {
            "form_key": "sandy",
            "name": "Tronco Arena",
            "display_name": "Burmy (Tronco Arena)",
            "category": "Pokémon Larva",
            "primary_type": "bug",
            "primary_type_es": "Bicho",
            "secondary_type": "",
            "secondary_type_es": "",
            **_build_retro_form_sprites(slug, "burmy/sandy"),
            "sprite_modern": "/media/pokemon/home/412-sandy.png",
            "sprite_modern_shiny": "/media/pokemon/home/shiny/412-sandy.png",
            "summary": sandy_summary,
            "locations": sandy_locations,
            "notes": sandy_notes,
            **gen5_obt_meta,
        },
        {
            "form_key": "trash",
            "name": "Tronco Basura",
            "display_name": "Burmy (Tronco Basura)",
            "category": "Pokémon Larva",
            "primary_type": "bug",
            "primary_type_es": "Bicho",
            "secondary_type": "",
            "secondary_type_es": "",
            **_build_retro_form_sprites(slug, "burmy/trash"),
            "sprite_modern": "/media/pokemon/home/412-trash.png",
            "sprite_modern_shiny": "/media/pokemon/home/shiny/412-trash.png",
            "summary": trash_summary,
            "locations": trash_locations,
            "notes": trash_notes,
            **gen5_obt_meta,
        }
    ]


def get_wormadam_forms(game_slug: str = "diamond") -> List[Dict[str, Any]]:
    """
    Retorna los 3 troncos de Wormadam (#413):
    Tronco Planta (Bicho/Planta), Tronco Arena (Bicho/Tierra), Tronco Basura (Bicho/Acero).
    Cada forma tiene tipos elementales y estadísticas exclusivas.
    """
    slug = (game_slug or "diamond").replace("_national", "")
    is_gen5 = slug in GEN5_FORM_GAMES
    gen5_obt_meta = {
        "type": "evolution",
        "badge_label": "Evolución",
        "badge_color": "purple",
    } if is_gen5 else {}

    return [
        {
            "form_key": "plant",
            "name": "Tronco Planta",
            "display_name": "Wormadam (Tronco Planta)",
            "category": "Pokémon Larva",
            "primary_type": "bug",
            "primary_type_es": "Bicho",
            "secondary_type": "grass",
            "secondary_type_es": "Planta",
            **_build_retro_form_sprites(slug, "wormadam/plant"),
            "sprite_modern": "/media/pokemon/home/413.png",
            "sprite_modern_shiny": "/media/pokemon/home/shiny/413.png",
            "summary": "Evolución permanente de Burmy hembra con Tronco Planta al nivel 20.",
            "locations": [
                {"area": "Evolución de Burmy Hembra", "method": "Nivel 20 (Burmy Tronco Planta)"}
            ],
            "notes": [
                {
                    "title": "Evolución Fija Permanente",
                    "text": "Wormadam no puede cambiar de forma. Su tronco queda fijado para siempre al evolucionar según el tronco que poseía Burmy, adquiriendo el tipo secundario Planta.",
                    "tag": "Evolución",
                    "icon": "/media/items/miracle-seed.png",
                }
            ],
            **gen5_obt_meta,
        },
        {
            "form_key": "sandy",
            "name": "Tronco Arena",
            "display_name": "Wormadam (Tronco Arena)",
            "category": "Pokémon Larva",
            "primary_type": "bug",
            "primary_type_es": "Bicho",
            "secondary_type": "ground",
            "secondary_type_es": "Tierra",
            **_build_retro_form_sprites(slug, "wormadam/sandy"),
            "sprite_modern": "/media/pokemon/home/10004.png",
            "sprite_modern_shiny": "/media/pokemon/home/shiny/10004.png",
            "summary": "Evolución permanente de Burmy hembra con Tronco Arena al nivel 20.",
            "locations": [
                {"area": "Evolución de Burmy Hembra", "method": "Nivel 20 (Burmy Tronco Arena)"}
            ],
            "notes": [
                {
                    "title": "Evolución Fija Permanente",
                    "text": "Wormadam no puede cambiar de forma. Su tronco queda fijado para siempre al evolucionar según el tronco que poseía Burmy, adquiriendo el tipo secundario Tierra.",
                    "tag": "Evolución",
                    "icon": "/media/items/soft-sand.png",
                }
            ],
            **gen5_obt_meta,
        },
        {
            "form_key": "trash",
            "name": "Tronco Basura",
            "display_name": "Wormadam (Tronco Basura)",
            "category": "Pokémon Larva",
            "primary_type": "bug",
            "primary_type_es": "Bicho",
            "secondary_type": "steel",
            "secondary_type_es": "Acero",
            **_build_retro_form_sprites(slug, "wormadam/trash"),
            "sprite_modern": "/media/pokemon/home/10005.png",
            "sprite_modern_shiny": "/media/pokemon/home/shiny/10005.png",
            "summary": "Evolución permanente de Burmy hembra con Tronco Basura al nivel 20.",
            "locations": [
                {"area": "Evolución de Burmy Hembra", "method": "Nivel 20 (Burmy Tronco Basura)"}
            ],
            "notes": [
                {
                    "title": "Evolución Fija Permanente",
                    "text": "Wormadam no puede cambiar de forma. Su tronco queda fijado para siempre al evolucionar según el tronco que poseía Burmy, adquiriendo el tipo secundario Acero.",
                    "tag": "Evolución",
                    "icon": "/media/items/metal-coat.png",
                }
            ],
            **gen5_obt_meta,
        }
    ]


def get_cherrim_forms(game_slug: str = "diamond") -> List[Dict[str, Any]]:
    """
    Retorna las 2 formas de Cherrim (#421):
    Forma Encapuchada (Overcast), Forma Soleada (Sunshine).
    """
    slug = (game_slug or "diamond").replace("_national", "")
    is_hgss = slug in ["heartgold", "soulsilver"]
    # HGSS no incluye carpeta back/cherrim/: Overcast usa su dorsal base 421.png y Sunshine comparte el de Platino.
    overcast_back = {"rel_back_static": "421"} if is_hgss else {}
    sunshine_back = {"back_slug": "platinum"} if is_hgss else {}
    return [
        {
            "form_key": "overcast",
            "name": "Forma Encapuchada",
            "display_name": "Cherrim",
            "category": "Pokémon Flor",
            "primary_type": "grass",
            "primary_type_es": "Planta",
            "secondary_type": "",
            "secondary_type_es": "",
            **_build_retro_form_sprites(slug, "cherrim/overcast", **overcast_back),
            "sprite_modern": "/media/pokemon/home/421.png",
            "sprite_modern_shiny": "/media/pokemon/home/shiny/421.png",
            "notes": [
                {
                    "title": "Forma Base de Cherrim",
                    "text": "Cherrim permanece en su Forma Encapuchada fuera de combate y durante el combate mientras no haya luz solar intensa activa.",
                    "tag": "Don Floral",
                    "icon": "/media/items/rule-book.png",
                }
            ],
        },
        {
            "form_key": "sunshine",
            "name": "Forma Soleada",
            "display_name": "Cherrim (Soleada)",
            "category": "Pokémon Flor",
            "primary_type": "grass",
            "primary_type_es": "Planta",
            "secondary_type": "",
            "secondary_type_es": "",
            **_build_retro_form_sprites(slug, "cherrim/sunshine", **sunshine_back),
            "sprite_modern": "/media/pokemon/home/421-sunshine.png",
            "sprite_modern_shiny": "/media/pokemon/home/shiny/421-sunshine.png",
            "notes": [
                {
                    "title": "Transformación por Sol Intenso",
                    "text": "Cambio exclusivo durante el combate mediante su habilidad Don Floral. Con luz solar intensa (Día Soleado) se abre en su Forma Soleada, aumentando en un 50% el Ataque y la Defensa Especial de todo el equipo.",
                    "tag": "Don Floral",
                    "icon": "/media/items/sun-stone.png",
                }
            ],
        }
    ]


def get_shellos_forms(game_slug: str = "diamond") -> List[Dict[str, Any]]:
    """
    Retorna las 2 formas geográficas de Shellos (#422):
    Mar Oeste (Rosa), Mar Este (Azul).
    En Sinnoh: Delimitadas a ambos lados del Monte Corona.
    En HeartGold/SoulSilver: Mar Oeste obtenible en Pokéwalker (Playa Tormenta); Mar Este solo por transferencia desde D/P/Pt.
    En Teselia (Gen 5): Obtenibles mediante Pokétransfer (Ruta 15) desde 4.ª generación o crianza en Ruta 3.
    """
    clean_slug = (game_slug or "diamond").replace("_national", "")
    is_hgss = clean_slug in ["heartgold", "soulsilver"]
    is_b2w2 = clean_slug in B2W2_FORM_GAMES
    is_gen5 = clean_slug in GEN5_FORM_GAMES
    slug = clean_slug

    gen5_obt_meta = (
        {"type": "trade_npc", "badge_label": "Intercambio NPC", "badge_color": "indigo"}
        if is_b2w2 else (_get_transfer_obt_meta(5) if is_gen5 else {})
    )

    if is_b2w2:
        west_summary = "Obtenible en Ciudad Mayólica mediante intercambio con la Presentadora Belinda (si el protagonista es Rizzo, tras devolver el Videomisor y completar 51 llamadas), por crianza en la Ruta 3 o vía Pokétransfer (Ruta 15)."
        west_locations = [
            {"area": "Ciudad Mayólica (Noria)", "method": "Intercambio NPC con Belinda (protagonista Rizzo • Nv. 50 con habilidad oculta)"},
            {"area": "Ruta 3 (Guardería Pokémon)", "method": "Crianza de huevo (conserva variante Mar Oeste)"},
            {"area": "Laboratorio de Pokétransfer (Ruta 15)", "method": "Pokétransfer (desde 4.ª generación • Mar Oeste)"}
        ]
        west_notes = [
            {
                "title": "Intercambio con Belinda (Rizzo)",
                "text": "Si juegas como Rizzo, la Presentadora Belinda ofrece a Shellos Mar Oeste (rosa) al Nv. 50 con habilidad oculta Poder Arena en Ciudad Mayólica tras completar la cadena de llamadas del Videomisor. Al criarlo con Ditto en la Ruta 3, sus crías conservan la variante Mar Oeste.",
                "tag": "Ciudad Mayólica",
                "icon": "/media/items/linking-cord.png",
            }
        ]

        east_summary = "Obtenible en Ciudad Mayólica mediante intercambio con el Presentador Julián (si la protagonista es Nanci, tras devolver el Videomisor y completar 51 llamadas), por crianza en la Ruta 3 o vía Pokétransfer (Ruta 15)."
        east_locations = [
            {"area": "Ciudad Mayólica (Noria)", "method": "Intercambio NPC con Julián (protagonista Nanci • Nv. 50 con habilidad oculta)"},
            {"area": "Ruta 3 (Guardería Pokémon)", "method": "Crianza de huevo (conserva variante Mar Este)"},
            {"area": "Laboratorio de Pokétransfer (Ruta 15)", "method": "Pokétransfer (desde 4.ª generación • Mar Este)"}
        ]
        east_notes = [
            {
                "title": "Intercambio con Julián (Nanci)",
                "text": "Si juegas como Nanci, el Presentador Julián ofrece a Shellos Mar Este (azul) al Nv. 50 con habilidad oculta Poder Arena en Ciudad Mayólica tras completar la cadena de llamadas del Videomisor. Al criarlo con Ditto en la Ruta 3, sus crías conservan la variante Mar Este.",
                "tag": "Ciudad Mayólica",
                "icon": "/media/items/linking-cord.png",
            }
        ]
    elif is_gen5:
        west_summary = "Inaccesible en estado salvaje en Teselia. Se obtiene mediante Pokétransfer (Ruta 15) desde juegos de 4.ª generación o por crianza en la Guardería Pokémon."
        west_locations = [
            {"area": "Laboratorio de Pokétransfer (Ruta 15)", "method": "Pokétransfer (desde 4.ª generación • Mar Oeste)"},
            {"area": "Ruta 3 (Guardería Pokémon)", "method": "Crianza de huevo (conserva variante Mar Oeste)"}
        ]
        west_notes = [
            {
                "title": "Variación Geográfica (Pokétransfer)",
                "text": "Shellos no aparece en estado salvaje en Teselia. Debes transferir la variante Mar Oeste (rosa) desde 4.ª generación en el Laboratorio de Pokétransfer (Ruta 15); al criarla con Ditto en la Ruta 3, las crías heredan su forma.",
                "tag": "Pokétransfer",
                "icon": "/media/items/linking-cord.png",
            }
        ]

        east_summary = "Inaccesible en estado salvaje en Teselia. Se obtiene mediante Pokétransfer (Ruta 15) desde juegos de 4.ª generación o por crianza en la Guardería Pokémon."
        east_locations = [
            {"area": "Laboratorio de Pokétransfer (Ruta 15)", "method": "Pokétransfer (desde 4.ª generación • Mar Este)"},
            {"area": "Ruta 3 (Guardería Pokémon)", "method": "Crianza de huevo (conserva variante Mar Este)"}
        ]
        east_notes = [
            {
                "title": "Variación Geográfica (Pokétransfer)",
                "text": "Shellos no aparece en estado salvaje en Teselia. Debes transferir la variante Mar Este (azul) desde 4.ª generación en el Laboratorio de Pokétransfer (Ruta 15); al criarla con Ditto en la Ruta 3, las crías heredan su forma.",
                "tag": "Pokétransfer",
                "icon": "/media/items/linking-cord.png",
            }
        ]
    elif is_hgss:
        west_summary = "Obtenible en el Pokéwalker (Playa Tormenta tras 5.000 pasos) o mediante transferencia desde Pokémon Diamante, Perla o Platino."
        west_locations = [
            {"area": "Pokéwalker (Playa Tormenta)", "method": "Paseo en el Pokéwalker (5.000+ pasos)"},
            {"area": "Intercambio con D/P/Pt", "method": "Transferencia desde Sinnoh"},
            {"area": "Ruta 34 (Guardería Pokémon)", "method": "Crianza de huevo"}
        ]
        west_notes = [
            {
                "title": "Variación Geográfica en Johto",
                "text": "Shellos Mar Oeste es la única variante que puede conseguirse directamente en HeartGold y SoulSilver a través de la ruta Playa Tormenta del Pokéwalker.",
                "tag": "Pokéwalker",
                "icon": "/media/items/poke-radar.png",
            }
        ]

        east_summary = "Inaccesible en estado salvaje y en el Pokéwalker en HGSS. Requiere transferencia desde Pokémon Diamante, Perla o Platino."
        east_locations = [
            {"area": "Intercambio con D/P/Pt", "method": "Transferencia desde Sinnoh (Vertiente oriental)"},
            {"area": "Ruta 34 (Guardería Pokémon)", "method": "Crianza de huevo de Shellos Este transferido"}
        ]
        east_notes = [
            {
                "title": "Forma Exclusiva de Sinnoh Este",
                "text": "La variante azul no aparece en ninguna ruta del Pokéwalker ni en Johto o Kanto. La única vía para registrarla es transferirla desde la vertiente oriental de Diamante, Perla o Platino.",
                "tag": "Transferencia",
                "icon": "/media/items/linking-cord.png",
            }
        ]
    else:
        west_summary = "Exclusivo de la vertiente occidental de Sinnoh (al oeste del Monte Corona)."
        west_locations = [
            {"area": "Ruta 205", "method": "Salvaje (Hierba)"},
            {"area": "Ruta 218", "method": "Salvaje (Surf / Pesca)"},
            {"area": "Parque Eólico", "method": "Salvaje (Hierba)"},
            {"area": "Forja Fuego", "method": "Salvaje (Hierba)"},
        ]
        west_notes = [
            {
                "title": "Variación Geográfica Sinnoh",
                "text": "La cordillera del Monte Corona divide geográficamente las poblaciones de esta especie. La variante rosa habita exclusivamente en la zona occidental de la región.",
                "tag": "Geografía",
                "icon": "/media/items/town-map.png",
            }
        ]

        east_summary = "Exclusivo de la vertiente oriental de Sinnoh (al este del Monte Corona)."
        east_locations = [
            {"area": "Ruta 213", "method": "Salvaje (Hierba / Surf)"},
            {"area": "Ruta 221", "method": "Salvaje (Hierba)"},
            {"area": "Ruta 222", "method": "Salvaje (Hierba / Surf)"},
            {"area": "Ruta 224", "method": "Salvaje (Hierba / Surf)"},
            {"area": "Orilla Valor", "method": "Salvaje (Hierba)"},
        ]
        east_notes = [
            {
                "title": "Variación Geográfica Sinnoh",
                "text": "La cordillera del Monte Corona divide geográficamente las poblaciones de esta especie. La variante azul habita exclusivamente en la zona oriental de la región.",
                "tag": "Geografía",
                "icon": "/media/items/town-map.png",
            }
        ]

    return [
        {
            "form_key": "west",
            "name": "Mar Oeste",
            "display_name": "Shellos (Mar Oeste)",
            "category": "Pokémon Babosa Marina",
            "primary_type": "water",
            "primary_type_es": "Agua",
            "secondary_type": "",
            "secondary_type_es": "",
            **_build_retro_form_sprites(slug, "shellos/west"),
            "sprite_modern": "/media/pokemon/home/422.png",
            "sprite_modern_shiny": "/media/pokemon/home/shiny/422.png",
            "summary": west_summary,
            "locations": west_locations,
            "notes": west_notes,
            **gen5_obt_meta,
        },
        {
            "form_key": "east",
            "name": "Mar Este",
            "display_name": "Shellos (Mar Este)",
            "category": "Pokémon Babosa Marina",
            "primary_type": "water",
            "primary_type_es": "Agua",
            "secondary_type": "",
            "secondary_type_es": "",
            **_build_retro_form_sprites(slug, "shellos/east"),
            "sprite_modern": "/media/pokemon/home/422-east.png",
            "sprite_modern_shiny": "/media/pokemon/home/shiny/422-east.png",
            "summary": east_summary,
            "locations": east_locations,
            "notes": east_notes,
            **gen5_obt_meta,
        }
    ]


def get_gastrodon_forms(game_slug: str = "diamond") -> List[Dict[str, Any]]:
    """
    Retorna las 2 formas geográficas de Gastrodon (#423):
    Mar Oeste (Rosa), Mar Este (Azul).
    En Sinnoh: Salvaje a ambos lados del Monte Corona.
    En HeartGold/SoulSilver: Inaccesible en estado salvaje; evoluciona de Shellos al Nivel 30 o transferencia desde D/P/Pt.
    En Teselia (Gen 5): Inaccesible en estado salvaje; evoluciona de Shellos al Nivel 30 o transferencia vía Pokétransfer (Ruta 15).
    """
    clean_slug = (game_slug or "diamond").replace("_national", "")
    is_hgss = clean_slug in ["heartgold", "soulsilver"]
    is_b2w2 = clean_slug in B2W2_FORM_GAMES
    is_gen5 = clean_slug in GEN5_FORM_GAMES
    slug = clean_slug

    gen5_obt_meta = {
        "type": "evolution",
        "badge_label": "Evolución",
        "badge_color": "purple",
    } if is_gen5 else {}

    if is_b2w2:
        west_summary = "Evoluciona de Shellos Mar Oeste al Nivel 30 (obtenible con Belinda en Ciudad Mayólica si juegas como Rizzo, por crianza o vía Pokétransfer en la Ruta 15)."
        west_locations = [
            {"area": "Evolución de Shellos", "method": "Evolución al Nivel 30 (Shellos Mar Oeste)"},
            {"area": "Laboratorio de Pokétransfer (Ruta 15)", "method": "Pokétransfer (transferencia desde 4.ª generación)"}
        ]
        west_notes = [
            {
                "title": "Evolución en Teselia 2",
                "text": "Evoluciona al Nivel 30 a partir de un Shellos Mar Oeste obtenido por intercambio con Belinda en Ciudad Mayólica, por crianza en la Ruta 3 o vía Pokétransfer, conservando su coloración rosa.",
                "tag": "Evolución",
                "icon": "/media/items/rule-book.png",
            }
        ]

        east_summary = "Evoluciona de Shellos Mar Este al Nivel 30 (obtenible con Julián en Ciudad Mayólica si juegas como Nanci, por crianza o vía Pokétransfer en la Ruta 15)."
        east_locations = [
            {"area": "Evolución de Shellos", "method": "Evolución al Nivel 30 (Shellos Mar Este)"},
            {"area": "Laboratorio de Pokétransfer (Ruta 15)", "method": "Pokétransfer (transferencia desde 4.ª generación)"}
        ]
        east_notes = [
            {
                "title": "Evolución en Teselia 2",
                "text": "Evoluciona al Nivel 30 a partir de un Shellos Mar Este obtenido por intercambio con Julián en Ciudad Mayólica, por crianza en la Ruta 3 o vía Pokétransfer, conservando su coloración azul.",
                "tag": "Evolución",
                "icon": "/media/items/rule-book.png",
            }
        ]
    elif is_gen5:
        west_summary = "Inaccesible en estado salvaje en Teselia. Evoluciona de Shellos Mar Oeste al Nivel 30 o mediante Pokétransfer (Ruta 15) desde juegos de 4.ª generación."
        west_locations = [
            {"area": "Evolución de Shellos", "method": "Evolución al Nivel 30 (Shellos Mar Oeste)"},
            {"area": "Laboratorio de Pokétransfer (Ruta 15)", "method": "Pokétransfer (transferencia desde 4.ª generación)"}
        ]
        west_notes = [
            {
                "title": "Evolución en Teselia",
                "text": "Evoluciona al Nivel 30 a partir de un Shellos Mar Oeste transferido vía Pokétransfer (Ruta 15) o nacido por crianza en la Ruta 3, conservando su coloración rosa.",
                "tag": "Evolución",
                "icon": "/media/items/rule-book.png",
            }
        ]

        east_summary = "Inaccesible en estado salvaje en Teselia. Evoluciona de Shellos Mar Este al Nivel 30 o mediante Pokétransfer (Ruta 15) desde juegos de 4.ª generación."
        east_locations = [
            {"area": "Evolución de Shellos", "method": "Evolución al Nivel 30 (Shellos Mar Este)"},
            {"area": "Laboratorio de Pokétransfer (Ruta 15)", "method": "Pokétransfer (transferencia desde 4.ª generación)"}
        ]
        east_notes = [
            {
                "title": "Evolución en Teselia",
                "text": "Evoluciona al Nivel 30 a partir de un Shellos Mar Este transferido vía Pokétransfer (Ruta 15) o nacido por crianza en la Ruta 3, conservando su coloración azul.",
                "tag": "Evolución",
                "icon": "/media/items/rule-book.png",
            }
        ]
    elif is_hgss:
        west_summary = "Inaccesible en estado salvaje en Johto y Kanto. Evoluciona de Shellos Mar Oeste al Nivel 30 o transferencia desde D/P/Pt."
        west_locations = [
            {"area": "Evolución de Shellos Mar Oeste", "method": "Evolución al Nivel 30"},
            {"area": "Intercambio con D/P/Pt", "method": "Transferencia desde Sinnoh"}
        ]
        west_notes = [
            {
                "title": "Evolución en HGSS",
                "text": "Evoluciona a partir de Shellos Mar Oeste capturado en el Pokéwalker (Playa Tormenta) o transferido desde Sinnoh.",
                "tag": "Evolución",
                "icon": "/media/items/rule-book.png",
            }
        ]

        east_summary = "Inaccesible en estado salvaje en Johto y Kanto. Evoluciona de Shellos Mar Este al Nivel 30 o transferencia desde D/P/Pt."
        east_locations = [
            {"area": "Evolución de Shellos Mar Este", "method": "Evolución al Nivel 30 (Shellos Este transferido)"},
            {"area": "Intercambio con D/P/Pt", "method": "Transferencia desde Sinnoh"}
        ]
        east_notes = [
            {
                "title": "Evolución en HGSS",
                "text": "Evoluciona a partir de Shellos Mar Este transferido desde la vertiente oriental de Sinnoh.",
                "tag": "Evolución",
                "icon": "/media/items/rule-book.png",
            }
        ]
    else:
        west_summary = "Exclusivo de la vertiente occidental de Sinnoh (al oeste del Monte Corona)."
        west_locations = [
            {"area": "Ruta 205", "method": "Salvaje (Hierba)"},
            {"area": "Ruta 218", "method": "Salvaje (Surf / Pesca)"},
            {"area": "Parque Eólico", "method": "Salvaje (Hierba)"},
            {"area": "Forja Fuego", "method": "Salvaje (Hierba / Surf)"},
            {"area": "Canal de Pastoria", "method": "Salvaje (Surf)"},
        ]
        west_notes = [
            {
                "title": "Variación Geográfica Sinnoh",
                "text": "La cordillera del Monte Corona divide geográficamente las poblaciones de esta especie. La variante rosa habita exclusivamente en la zona occidental de la región.",
                "tag": "Geografía",
                "icon": "/media/items/town-map.png",
            }
        ]

        east_summary = "Exclusivo de la vertiente oriental de Sinnoh (al este del Monte Corona)."
        east_locations = [
            {"area": "Ruta 213", "method": "Salvaje (Hierba / Surf)"},
            {"area": "Ruta 222", "method": "Salvaje (Hierba / Surf)"},
            {"area": "Ruta 224", "method": "Salvaje (Hierba / Surf)"},
            {"area": "Ruta 230", "method": "Salvaje (Surf)"},
        ]
        east_notes = [
            {
                "title": "Variación Geográfica Sinnoh",
                "text": "La cordillera del Monte Corona divide geográficamente las poblaciones de esta especie. La variante azul habita exclusivamente en la zona oriental de la región.",
                "tag": "Geografía",
                "icon": "/media/items/town-map.png",
            }
        ]

    return [
        {
            "form_key": "west",
            "name": "Mar Oeste",
            "display_name": "Gastrodon (Mar Oeste)",
            "category": "Pokémon Babosa Marina",
            "primary_type": "water",
            "primary_type_es": "Agua",
            "secondary_type": "ground",
            "secondary_type_es": "Tierra",
            **_build_retro_form_sprites(slug, "gastrodon/west"),
            "sprite_modern": "/media/pokemon/home/423.png",
            "sprite_modern_shiny": "/media/pokemon/home/shiny/423.png",
            "summary": west_summary,
            "locations": west_locations,
            "notes": west_notes,
            **gen5_obt_meta,
        },
        {
            "form_key": "east",
            "name": "Mar Este",
            "display_name": "Gastrodon (Mar Este)",
            "category": "Pokémon Babosa Marina",
            "primary_type": "water",
            "primary_type_es": "Agua",
            "secondary_type": "ground",
            "secondary_type_es": "Tierra",
            **_build_retro_form_sprites(slug, "gastrodon/east"),
            "sprite_modern": "/media/pokemon/home/423-east.png",
            "sprite_modern_shiny": "/media/pokemon/home/shiny/423-east.png",
            "summary": east_summary,
            "locations": east_locations,
            "notes": east_notes,
            **gen5_obt_meta,
        }
    ]


def get_arceus_forms(game_slug: str = "diamond") -> List[Dict[str, Any]]:
    """
    Retorna las 17 formas canónicas de Arceus (#493) en Generaciones 4 y 5:
    Forma Normal + 16 Tablas elementales.
    (La Tabla Duende y el Tipo Hada quedan estrictamente excluidos por pertenecer a Gen 6).
    """
    slug = (game_slug or "diamond").replace("_national", "")
    plates_def = [
        ("normal", "Forma Normal", "Normal", "normal", "Normal", "", "", "Sin Tabla", "/media/items/rule-book.png", "Permanece en su Forma Normal cuando no lleva ninguna tabla elemental equipada."),
        ("fire", "Tabla Llama", "Fuego", "fire", "Fuego", "", "", "Tabla Llama", "/media/items/flame-plate.png", "Al equipar la Tabla Llama, su habilidad Multitipo cambia su tipo elemental a Fuego puro."),
        ("water", "Tabla Linfa", "Agua", "water", "Agua", "", "", "Tabla Linfa", "/media/items/splash-plate.png", "Al equipar la Tabla Linfa, su habilidad Multitipo cambia su tipo elemental a Agua puro."),
        ("grass", "Tabla Pradal", "Planta", "grass", "Planta", "", "", "Tabla Pradal", "/media/items/meadow-plate.png", "Al equipar la Tabla Pradal, su habilidad Multitipo cambia su tipo elemental a Planta puro."),
        ("electric", "Tabla Trueno", "Eléctrico", "electric", "Eléctrico", "", "", "Tabla Trueno", "/media/items/zap-plate.png", "Al equipar la Tabla Trueno, su habilidad Multitipo cambia su tipo elemental a Eléctrico puro."),
        ("ice", "Tabla Helada", "Hielo", "ice", "Hielo", "", "", "Tabla Helada", "/media/items/icicle-plate.png", "Al equipar la Tabla Helada, su habilidad Multitipo cambia su tipo elemental a Hielo puro."),
        ("fighting", "Tabla Fuerte", "Lucha", "fighting", "Lucha", "", "", "Tabla Fuerte", "/media/items/fist-plate.png", "Al equipar la Tabla Fuerte, su habilidad Multitipo cambia su tipo elemental a Lucha puro."),
        ("poison", "Tabla Tóxica", "Veneno", "poison", "Veneno", "", "", "Tabla Tóxica", "/media/items/toxic-plate.png", "Al equipar la Tabla Tóxica, su habilidad Multitipo cambia su tipo elemental a Veneno puro."),
        ("ground", "Tabla Terrax", "Tierra", "ground", "Tierra", "", "", "Tabla Terrax", "/media/items/earth-plate.png", "Al equipar la Tabla Terrax, su habilidad Multitipo cambia su tipo elemental a Tierra puro."),
        ("flying", "Tabla Cielo", "Volador", "flying", "Volador", "", "", "Tabla Cielo", "/media/items/sky-plate.png", "Al equipar la Tabla Cielo, su habilidad Multitipo cambia su tipo elemental a Volador puro."),
        ("psychic", "Tabla Mental", "Psíquico", "psychic", "Psíquico", "", "", "Tabla Mental", "/media/items/mind-plate.png", "Al equipar la Tabla Mental, su habilidad Multitipo cambia su tipo elemental a Psíquico puro."),
        ("bug", "Tabla Bicho", "Bicho", "bug", "Bicho", "", "", "Tabla Bicho", "/media/items/insect-plate.png", "Al equipar la Tabla Bicho, su habilidad Multitipo cambia su tipo elemental a Bicho puro."),
        ("rock", "Tabla Pétrea", "Roca", "rock", "Roca", "", "", "Tabla Pétrea", "/media/items/stone-plate.png", "Al equipar la Tabla Pétrea, su habilidad Multitipo cambia su tipo elemental a Roca puro."),
        ("ghost", "Tabla Terror", "Fantasma", "ghost", "Fantasma", "", "", "Tabla Terror", "/media/items/spooky-plate.png", "Al equipar la Tabla Terror, su habilidad Multitipo cambia su tipo elemental a Fantasma puro."),
        ("dragon", "Tabla Draco", "Dragón", "dragon", "Dragón", "", "", "Tabla Draco", "/media/items/draco-plate.png", "Al equipar la Tabla Draco, su habilidad Multitipo cambia su tipo elemental a Dragón puro."),
        ("steel", "Tabla Acero", "Acero", "steel", "Acero", "", "", "Tabla Acero", "/media/items/iron-plate.png", "Al equipar la Tabla Acero, su habilidad Multitipo cambia su tipo elemental a Acero puro."),
        ("dark", "Tabla Oscura", "Siniestro", "dark", "Siniestro", "", "", "Tabla Oscura", "/media/items/dread-plate.png", "Al equipar la Tabla Oscura, su habilidad Multitipo cambia su tipo elemental a Siniestro puro."),
    ]

    forms = []
    for f_key, f_name, d_name, p_type, p_type_es, s_type, s_type_es, plate_name, plate_icon, note_desc in plates_def:
        forms.append({
            "form_key": f_key,
            "name": f_name,
            "display_name": f"Arceus ({d_name})" if f_key != "normal" else "Arceus",
            "category": "Pokémon Alfa",
            "primary_type": p_type,
            "primary_type_es": p_type_es,
            "secondary_type": s_type,
            "secondary_type_es": s_type_es,
            **_build_retro_form_sprites(slug, f"arceus/{f_key}"),
            "sprite_modern": "/media/pokemon/home/493.png" if f_key == "normal" else f"/media/pokemon/home/493-{f_key}.png",
            "sprite_modern_shiny": "/media/pokemon/home/shiny/493.png" if f_key == "normal" else f"/media/pokemon/home/shiny/493-{f_key}.png",
            "notes": [
                {
                    "title": f"Mecánica Multitipo ({plate_name})",
                    "text": note_desc,
                    "tag": "Multitipo",
                    "icon": plate_icon,
                }
            ],
        })

    return forms


def get_unown_forms(game_slug: str = "gold") -> List[Dict[str, Any]]:
    """
    Retorna las 26 (Gen 2) o 28 (Gen 3+) formas alfabéticas de Unown (#201).
    Cada forma incluye su método de obtención y ubicación según el juego:
    - Kanto / Archi7 (Rojo Fuego / Verde Hoja): Ruinas Sete (7 cámaras con tasas oficiales).
    - Johto (Oro / Plata / Cristal): Ruinas Alfa (4 cámaras).
    - Hoenn (Rubí / Zafiro / Esmeralda): No salvaje. Transferencia externa (GBA / GameCube).
    - Sinnoh (Diamante / Perla / Platino): Ruinas Sosiego (Ruta central FRIEND, cámaras sin salida y cámara secreta ! ?).
    """
    from .unown_data import get_unown_catalog
    clean_slug = (game_slug or "gold").replace("_national", "")
    cfg = get_game_sprite_config(clean_slug)
    raw_unown = get_unown_catalog(clean_slug)
    is_hoenn = clean_slug in ["ruby", "sapphire", "emerald"]

    forms = []
    for item in raw_unown:
        letter = item["letter"]
        if is_hoenn:
            summary = "No disponible en Hoenn. Requiere Pokémon Rojo Fuego / Verde Hoja o Pokémon Colosseum. No es posible transferir desde Gen 1 o Gen 2."
            locations = [
                {
                    "area": "Transferencia externa (GBA / GameCube)",
                    "method": "Pokémon Rojo Fuego / Verde Hoja o Pokémon Colosseum"
                }
            ]
            badge_color = "slate"
            badge_label = "Transferencia"
            obt_type = "transfer"
            ch_name = ""
        elif clean_slug in ["diamond", "pearl", "platinum"]:
            rate_val = item.get("rate", "")
            rate_str = f" (Tasa: {rate_val})" if rate_val else ""
            if letter in ["exclamation", "question"]:
                summary = "Exclusivo de la Cámara Superior Secreta de Ruinas Sosiego (Tasa: 50%). Solo accesible a través del Túnel Ruinamaniaco tras registrar las 26 formas alfabéticas (A-Z)."
                locations = [
                    {
                        "area": "Ruinas Sosiego (Cámara Superior Secreta)",
                        "method": "Salvaje (Tasa: 50%) • Conexión vía Túnel Ruinamaniaco (Ruta 214)"
                    }
                ]
            elif letter in ["f", "r", "i", "e", "n", "d"]:
                summary = f"Exclusivo de la sala '{letter.upper()}' en la ruta central de descenso FRIEND de Ruinas Sosiego (Tasa: 100%)."
                locations = [
                    {
                        "area": f"Ruinas Sosiego (Ruta Central - Sala {letter.upper()})",
                        "method": "Salvaje (Tasa: 100%)"
                    }
                ]
            else:
                summary = f"Salvaje en las salas sin salida al tomar desvíos de la ruta principal en Ruinas Sosiego{rate_str}."
                locations = [
                    {
                        "area": "Ruinas Sosiego (Salas Sin Salida)",
                        "method": f"Salvaje{rate_str}"
                    }
                ]
            badge_color = "emerald"
            badge_label = "Salvaje"
            obt_type = "wild"
            ch_name = item.get("chamber_name", "Ruinas Sosiego")
        elif clean_slug in ["heartgold", "soulsilver"]:
            ch_name = item.get("chamber_name", "Ruinas Alfa")
            ch_title = item.get("chamber_title", ch_name)
            if letter in ["exclamation", "question"]:
                summary = "Exclusivo de la Sala Secreta de Entrada en Ruinas Alfa (Tasa: 50%). Requiere haber capturado las 26 formas alfabéticas (A-Z) y haber resuelto las 4 salas secretas tras los rompecabezas para desbloquear el acceso."
                locations = [
                    {
                        "area": "Ruinas Alfa (Sala Secreta de Entrada)",
                        "method": "Salvaje (Tasa: 50%) • Requiere registrar las 26 formas (A-Z) y resolver las 4 salas secretas"
                    }
                ]
            else:
                summary = f"Salvaje en la sala principal de Ruinas Alfa tras resolver el puzzle de la {ch_name}."
                locations = [
                    {
                        "area": ch_name,
                        "method": f"Salvaje • Desbloqueado al resolver el rompecabezas de {ch_title}"
                    }
                ]
            badge_color = "emerald"
            badge_label = "Salvaje"
            obt_type = "wild"
        elif clean_slug in GEN5_FORM_GAMES:
            summary = "No disponible en estado salvaje en Teselia. Se obtiene mediante transferencia externa con el Pokétransfer en el Laboratorio de Pokétransfer (Ruta 15), desde juegos de 4.ª generación (Pokémon Diamante, Perla, Platino, Oro HeartGold o Plata SoulSilver)."
            locations = [
                {
                    "area": "Laboratorio de Pokétransfer (Ruta 15)",
                    "method": "Pokétransfer (transferencia desde 4.ª generación)"
                }
            ]
            badge_color = "slate"
            badge_label = "Pokétransfer"
            obt_type = "transfer"
            ch_name = "Teselia (Pokétransfer)"
        elif clean_slug in ["gold", "silver", "crystal"]:
            ch_name = item.get("chamber_name", "Ruinas Alfa")
            ch_title = item.get("chamber_title", ch_name)
            summary = f"Salvaje en la sala principal de Ruinas Alfa tras resolver el puzzle de la {ch_name}."
            locations = [
                {
                    "area": ch_name,
                    "method": f"Salvaje • Desbloqueado al resolver el rompecabezas de {ch_title}"
                }
            ]
            badge_color = "emerald"
            badge_label = "Salvaje"
            obt_type = "wild"
        else:
            ch_name = item.get("chamber_name", "Ruinas")
            rate_val = item.get("rate", "")
            rate_str = f" (Tasa: {rate_val})" if rate_val else ""
            summary = f"Exclusivo de {ch_name}{rate_str}."
            locations = [
                {
                    "area": ch_name,
                    "method": f"Salvaje{rate_str}"
                }
            ]
            badge_color = "emerald"
            badge_label = "Salvaje"
            obt_type = "wild"

        anim_dir = cfg["anim_dir"]
        anim_ext = cfg["anim_ext"]
        modal_retro_url = f"/media/pokemon/sprites/{anim_dir}/unown/{letter}{anim_ext}" if anim_dir else None
        modal_retro_shiny_url = f"/media/pokemon/sprites/{anim_dir}_shiny/unown/{letter}{anim_ext}" if anim_dir else None
        modal_retro_back_url = None
        modal_retro_shiny_back_url = None
        if cfg["has_animated_back"] and anim_dir:
            modal_retro_back_url = f"/media/pokemon/sprites/{anim_dir}/back/unown/{letter}{anim_ext}"
            modal_retro_shiny_back_url = f"/media/pokemon/sprites/{anim_dir}_shiny/back/unown/{letter}{anim_ext}"

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
            "modal_retro_sprite_url": modal_retro_url,
            "modal_retro_sprite_shiny_url": modal_retro_shiny_url,
            "modal_retro_sprite_back_url": modal_retro_back_url,
            "modal_retro_sprite_shiny_back_url": modal_retro_shiny_back_url,
            "sprite_retro_back": item.get("sprite_normal_back") or item["sprite_normal"].replace(f"/{item['sprite_normal'].split('/')[4]}/", f"/{item['sprite_normal'].split('/')[4]}/back/"),
            "sprite_retro_shiny_back": item.get("sprite_shiny_back") or item["sprite_shiny"].replace(f"/{item['sprite_shiny'].split('/')[4]}/", f"/{item['sprite_shiny'].split('/')[4]}/back/"),
            "sprite_modern": f"/media/pokemon/home/201-{letter}.png",
            "sprite_modern_shiny": f"/media/pokemon/home/shiny/201-{letter}.png",
            "chamber_key": item.get("chamber_key", ""),
            "chamber_name": ch_name,
            "summary": summary,
            "locations": locations,
            "badge_color": badge_color,
            "badge_label": badge_label,
            "type": obt_type,
        })

    return forms




def get_giratina_forms(game_slug: str = "platinum"):
    """
    Retorna las 2 formas de Giratina (#487):
    Forma Modificada (terrestre) y Forma Origen (serpenteante del Mundo Distorsión / Griseosfera).
    """
    clean_slug = (game_slug or "platinum").replace("_national", "")
    is_b2w2 = clean_slug in B2W2_FORM_GAMES
    is_gen5 = get_game_sprite_config(clean_slug)["gen"] >= 5

    if is_b2w2:
        origin_note_text = (
            "Forma serpenteante original de Giratina. En Teselia 2 se manifiesta llevando equipada la Griseosfera, "
            "recogida en la Torre Duodraco. Adquiere la habilidad Levitación y orienta sus estadísticas al ataque."
        )
    elif is_gen5:
        origin_note_text = (
            "Forma serpenteante original de Giratina. En Teselia se manifiesta llevando equipada la Griseosfera, "
            "entregada por el Trío Sombrío en el Puente Progreso. Adquiere la habilidad Levitación y orienta sus estadísticas al ataque."
        )
    else:
        origin_note_text = (
            "Forma serpenteante original de Giratina. Se manifiesta dentro del Mundo Distorsión o llevando equipada la "
            "Griseosfera en el mundo real. Adquiere la habilidad Levitación y orienta sus estadísticas al ataque."
        )

    return [
        {
            "form_key": "altered",
            "name": "Forma Modificada",
            "display_name": "Giratina (Forma Modificada)",
            "category": "Pokémon Renegado",
            "primary_type": "ghost",
            "primary_type_es": "Fantasma",
            "secondary_type": "dragon",
            "secondary_type_es": "Dragón",
            **_build_retro_form_sprites(clean_slug, "487"),
            "sprite_modern": "/media/pokemon/home/487.png",
            "sprite_modern_shiny": "/media/pokemon/home/shiny/487.png",
            "notes": [
                {
                    "title": "Mundo Real",
                    "text": "Forma con patas adoptada fuera del Mundo Distorsión cuando no lleva equipada la Griseosfera. Posee la habilidad Presión y mayores defensas.",
                    "tag": "Presión",
                    "icon": "/media/items/griseous-orb.png",
                }
            ],
        },
        {
            "form_key": "origin",
            "name": "Forma Origen",
            "display_name": "Giratina (Forma Origen)",
            "category": "Pokémon Renegado",
            "primary_type": "ghost",
            "primary_type_es": "Fantasma",
            "secondary_type": "dragon",
            "secondary_type_es": "Dragón",
            **_build_retro_form_sprites(clean_slug, "giratina/origin"),
            "sprite_modern": "/media/pokemon/home/10007.png",
            "sprite_modern_shiny": "/media/pokemon/home/shiny/10007.png",
            "notes": [
                {
                    "title": "Griseosfera",
                    "text": origin_note_text,
                    "tag": "Levitación",
                    "icon": "/media/items/griseous-orb.png",
                }
            ],
        },
    ]


def get_shaymin_forms(game_slug: str = "platinum"):
    """
    Retorna las 2 formas de Shaymin (#492):
    Forma Tierra (Erizo) y Forma Cielo (Gracídea de día).
    """
    clean_slug = (game_slug or "platinum").replace("_national", "")
    is_gen5 = get_game_sprite_config(clean_slug)["gen"] >= 5

    sky_note_text = (
        "Forma alada adoptada al usar la Flor Gracídea entre las 05:00 y las 19:59 (entregada en el Centro Pokémon de Pueblo Ladrillo al llevar a Shaymin). Adquiere el tipo secundario Volador, la habilidad Dicha y altas estadísticas de Velocidad (127) y Ataque Especial (120). Revierte de noche o al congelarse."
        if is_gen5 else
        "Forma alada adoptada al usar la Flor Gracídea entre las 05:00 y las 19:59. Adquiere el tipo secundario Volador, la habilidad Dicha y estadísticas altas de Velocidad (127) y Ataque Especial (120). Revierte de noche o al congelarse."
    )

    return [
        {
            "form_key": "land",
            "name": "Forma Tierra",
            "display_name": "Shaymin (Forma Tierra)",
            "category": "Pokémon Gratitud",
            "primary_type": "grass",
            "primary_type_es": "Planta",
            "secondary_type": "",
            "secondary_type_es": "",
            **_build_retro_form_sprites(clean_slug, "492"),
            "sprite_modern": "/media/pokemon/home/492.png",
            "sprite_modern_shiny": "/media/pokemon/home/shiny/492.png",
            "notes": [
                {
                    "title": "Forma Base",
                    "text": "Forma terrestre original de Shaymin. Posee la habilidad Cura Natural y estadísticas homogéneas de 100 en todos sus atributos.",
                    "tag": "Cura Natural",
                    "icon": "/media/items/gracidea.png",
                }
            ],
        },
        {
            "form_key": "sky",
            "name": "Forma Cielo",
            "display_name": "Shaymin (Forma Cielo)",
            "category": "Pokémon Gratitud",
            "primary_type": "grass",
            "primary_type_es": "Planta",
            "secondary_type": "flying",
            "secondary_type_es": "Volador",
            **_build_retro_form_sprites(clean_slug, "shaymin/sky"),
            "sprite_modern": "/media/pokemon/home/10006.png",
            "sprite_modern_shiny": "/media/pokemon/home/shiny/10006.png",
            "notes": [
                {
                    "title": "Flor Gracídea",
                    "text": sky_note_text,
                    "tag": "Dicha",
                    "icon": "/media/items/gracidea.png",
                }
            ],
        },
    ]


def get_rotom_forms(game_slug: str = "platinum"):
    """
    Retorna las 6 formas de Rotom (#479):
    Normal y los 5 electrodomésticos (Calor, Lavado, Frío, Ventilador y Corte).
    Canónico Gen 4: Todas las formas conservan estrictamente el tipo Eléctrico / Fantasma.
    Canónico Gen 5: Las 5 formas adquieren su tipo elemental secundario (Fuego, Agua, Hielo, Volador, Planta).
    En Sinnoh: Edificio Galaxia de Ciudad Vetusta con Llave Secreta.
    En HeartGold/SoulSilver: Edificio Silph S.A. en Ciudad Azafrán llevando a Rotom de acompañante.
    En Teselia: Almacén de cajas en la planta baja del Centro Comercial R9 (Ruta 9).
    """
    clean_slug = (game_slug or "platinum").replace("_national", "")
    is_hgss = clean_slug in ["heartgold", "soulsilver"]
    is_gen5 = get_game_sprite_config(clean_slug)["gen"] >= 5

    if is_gen5:
        appliances = [
            ("normal", "Forma Normal", "Rotom", "479", 479, "Forma original de plasma de Rotom.", "Rayo", "ghost", "Fantasma"),
            ("heat", "Rotom Calor", "Rotom Calor (Microondas)", "rotom/heat", 10008, "Posee un microondas. En 5.ª Generación adquiere el tipo Eléctrico/Fuego y aprende Sofoco.", "Sofoco", "fire", "Fuego"),
            ("wash", "Rotom Lavado", "Rotom Lavado (Lavadora)", "rotom/wash", 10009, "Posee una lavadora. En 5.ª Generación adquiere el tipo Eléctrico/Agua y aprende Hidrobomba.", "Hidrobomba", "water", "Agua"),
            ("frost", "Rotom Frío", "Rotom Frío (Frigorífico)", "rotom/frost", 10010, "Posee un frigorífico. En 5.ª Generación adquiere el tipo Eléctrico/Hielo y aprende Ventisca.", "Ventisca", "ice", "Hielo"),
            ("fan", "Rotom Ventilador", "Rotom Ventilador (Ventilador)", "rotom/fan", 10011, "Posee un ventilador. En 5.ª Generación adquiere el tipo Eléctrico/Volador y aprende Tajo Aéreo.", "Tajo Aéreo", "flying", "Volador"),
            ("mow", "Rotom Corte", "Rotom Corte (Cortacésped)", "rotom/mow", 10012, "Posee un cortacésped. En 5.ª Generación adquiere el tipo Eléctrico/Planta y aprende Lluevehojas.", "Lluevehojas", "grass", "Planta"),
        ]
    else:
        appliances = [
            ("normal", "Forma Normal", "Rotom", "479", 479, "Forma original de plasma de Rotom.", "Rayo", "ghost", "Fantasma"),
            ("heat", "Rotom Calor", "Rotom Calor (Microondas)", "rotom/heat", 10008, "Posee un microondas. En 4ª Generación mantiene el tipo Eléctrico/Fantasma y aprende Sofoco.", "Sofoco", "ghost", "Fantasma"),
            ("wash", "Rotom Lavado", "Rotom Lavado (Lavadora)", "rotom/wash", 10009, "Posee una lavadora. En 4ª Generación mantiene el tipo Eléctrico/Fantasma y aprende Hidrobomba.", "Hidrobomba", "ghost", "Fantasma"),
            ("frost", "Rotom Frío", "Rotom Frío (Frigorífico)", "rotom/frost", 10010, "Posee un frigorífico. En 4ª Generación mantiene el tipo Eléctrico/Fantasma y aprende Ventisca.", "Ventisca", "ghost", "Fantasma"),
            ("fan", "Rotom Ventilador", "Rotom Ventilador (Ventilador)", "rotom/fan", 10011, "Posee un ventilador. En 4ª Generación mantiene el tipo Eléctrico/Fantasma y aprende Tajo Aéreo.", "Tajo Aéreo", "ghost", "Fantasma"),
            ("mow", "Rotom Corte", "Rotom Corte (Cortacésped)", "rotom/mow", 10012, "Posee un cortacésped. En 4ª Generación mantiene el tipo Eléctrico/Fantasma y aprende Lluevehojas.", "Lluevehojas", "ghost", "Fantasma"),
        ]

    forms = []
    for f_key, f_name, d_name, rel_stem, home_id, desc, special_move, sec_type, sec_type_es in appliances:
        if is_gen5:
            title_text = f"Centro Comercial R9 ({special_move})"
            body_text = f"{desc} En el almacén de cajas de la planta baja del Centro Comercial R9 (Ruta 9), Rotom puede poseer los electrodomésticos para cambiar de forma y de tipo secundario."
            icon_path = "/media/items/card-key.png"
        elif is_hgss:
            title_text = f"Silph S.A. ({special_move})"
            body_text = f"{desc} Requiere llevar a Rotom en primer lugar del equipo para activar el ascensor a la Sala de Electrodomésticos en el Edificio Silph S.A. de Ciudad Azafrán."
            icon_path = "/media/items/card-key.png"
        else:
            title_text = f"Edificio Galaxia ({special_move})"
            body_text = f"{desc} Requiere la Llave Secreta en la Sala Secreta del Edificio Galaxia de Ciudad Vetusta."
            icon_path = "/media/items/secret-key.png"

        forms.append({
            "form_key": f_key,
            "name": f_name,
            "display_name": d_name,
            "category": "Pokémon Plasma",
            "primary_type": "electric",
            "primary_type_es": "Eléctrico",
            "secondary_type": sec_type,
            "secondary_type_es": sec_type_es,
            **_build_retro_form_sprites(clean_slug, rel_stem),
            "sprite_modern": f"/media/pokemon/home/{home_id}.png",
            "sprite_modern_shiny": f"/media/pokemon/home/shiny/{home_id}.png",
            "notes": [
                {
                    "title": title_text,
                    "text": body_text,
                    "tag": special_move,
                    "icon": icon_path,
                }
            ],
        })
    return forms


def get_pichu_forms(game_slug: str = "heartgold") -> List[Dict[str, Any]]:
    """
    Retorna las formas canónicas de Pichu (#172):
    Forma Estándar y Pichu Picoreja (exclusiva de HeartGold y SoulSilver).
    """
    slug = (game_slug or "heartgold").replace("_national", "")
    forms = [
        {
            "form_key": "standard",
            "name": "Forma Estándar",
            "display_name": "Pichu",
            "category": "Pokémon Ratón",
            "primary_type": "electric",
            "primary_type_es": "Eléctrico",
            "secondary_type": "",
            "secondary_type_es": "",
            **_build_retro_form_sprites(slug, "172"),
            "sprite_modern": "/media/pokemon/home/172.png",
            "sprite_modern_shiny": "/media/pokemon/home/shiny/172.png",
            "notes": [
                {
                    "title": "Crianza en Guardería",
                    "text": "Cría de Pikachu obtenida mediante crianza en la Guardería Pokémon de la Ruta 34.",
                    "tag": "Bebé",
                    "icon": "/media/items/rule-book.png",
                }
            ],
        }
    ]
    if slug in ["heartgold", "soulsilver"]:
        forms.append({
            "form_key": "spiky_eared",
            "name": "Pichu Picoreja",
            "display_name": "Pichu Picoreja",
            "category": "Pokémon Ratón",
            "primary_type": "electric",
            "primary_type_es": "Eléctrico",
            "secondary_type": "",
            "secondary_type_es": "",
            **_build_retro_form_sprites(slug, "172-spiky-eared"),
            "sprite_modern": "/media/pokemon/home/172.png",
            "sprite_modern_shiny": "/media/pokemon/home/shiny/172.png",
            "notes": [
                {
                    "title": "Exclusividad Absoluta de Cartucho",
                    "text": "Esta variante hembra única de oreja izquierda con tres puntas no puede evolucionar ni transferirse fuera de Pokémon Oro HeartGold y Plata SoulSilver.",
                    "tag": "Intransferible",
                    "icon": "/media/items/rule-book.png",
                },
                {
                    "title": "Santuario del Encinar",
                    "text": "Se une a tu equipo al interactuar con el santuario llevando al 'Pichu Color Pikachu' de evento como acompañante.",
                    "tag": "Evento",
                    "icon": "/media/items/everstone.png",
                }
            ],
        })
    return forms


def get_basculin_forms(game_slug: str = "black") -> List[Dict[str, Any]]:
    clean_slug = (game_slug or "black").replace("_national", "")
    is_white = (clean_slug == "white")
    is_black2 = (clean_slug == "black-2")
    is_white2 = (clean_slug == "white-2")
    if is_black2:
        red_text = (
            "Es la forma predominante y muy común en Pokémon Negro 2. Aparece haciendo Surf y pescando con Supercaña "
            "por toda Teselia (y también en sombras del agua)."
        )
        blue_text = (
            "En Pokémon Negro 2 es rara en estado salvaje: solo aparece ocasionalmente (5%) en sombras del agua "
            "al hacer Surf o pescar con Supercaña."
        )
    elif is_white2:
        red_text = (
            "En Pokémon Blanco 2 es rara en estado salvaje: solo aparece ocasionalmente (5%) en sombras del agua "
            "al hacer Surf o pescar con Supercaña."
        )
        blue_text = (
            "Es la forma predominante y muy común en Pokémon Blanco 2. Aparece haciendo Surf y pescando con Supercaña "
            "por toda Teselia (y también en sombras del agua)."
        )
    else:
        red_text = (
            "En Pokémon Blanco es muy rara en estado salvaje y no se obtiene por intercambio interno: "
            "solo aparece ocasionalmente (5%) en sombras del agua al hacer Surf o pescar con Supercaña."
            if is_white
            else
            "Es la forma predominante y muy común en Pokémon Negro. Aparece haciendo Surf y pescando con Supercaña "
            "por toda Teselia; además, puedes recibir uno (mote: Mordiscos) mediante intercambio NPC en Ciudad Fayenza "
            "a cambio de un Minccino."
        )
        blue_text = (
            "Es la forma predominante y muy común en Pokémon Blanco. Aparece haciendo Surf y pescando con Supercaña "
            "por toda Teselia; además, puedes recibir uno (mote: Mordiscos, habilidad Cabeza Roca) mediante intercambio NPC "
            "en Ciudad Fayenza a cambio de un Minccino."
            if is_white
            else
            "En Pokémon Negro es muy rara en estado salvaje y no se obtiene por intercambio interno: "
            "solo aparece ocasionalmente (5%) en sombras del agua al hacer Surf o pescar con Supercaña."
        )
    return [
        {
            "form_key": "red_striped",
            "name": "Forma Raya Roja",
            "display_name": "Basculin (Raya Roja)",
            "category": "Pokémon Hostil",
            "primary_type": "water",
            "primary_type_es": "Agua",
            "secondary_type": "",
            "secondary_type_es": "",
            **_build_retro_form_sprites(clean_slug, "550"),
            "sprite_modern": "/media/pokemon/home/550.png",
            "sprite_modern_shiny": "/media/pokemon/home/shiny/550.png",
            "notes": [
                {
                    "title": "Forma Raya Roja",
                    "text": red_text,
                    "tag": "Raya Roja",
                    "icon": "/media/items/rule-book.png",
                }
            ],
        },
        {
            "form_key": "blue_striped",
            "name": "Forma Raya Azul",
            "display_name": "Basculin (Raya Azul)",
            "category": "Pokémon Hostil",
            "primary_type": "water",
            "primary_type_es": "Agua",
            "secondary_type": "",
            "secondary_type_es": "",
            **_build_retro_form_sprites(clean_slug, "basculin/blue"),
            "sprite_modern": "/media/pokemon/home/10016.png",
            "sprite_modern_shiny": "/media/pokemon/home/shiny/10016.png",
            "notes": [
                {
                    "title": "Forma Raya Azul",
                    "text": blue_text,
                    "tag": "Raya Azul",
                    "icon": "/media/items/rule-book.png",
                }
            ],
        },
    ]


def get_darmanitan_forms(game_slug: str = "black") -> List[Dict[str, Any]]:
    clean_slug = (game_slug or "black").replace("_national", "")
    is_b2w2 = clean_slug in B2W2_FORM_GAMES
    zen_text = (
        "Adquiere el tipo Fuego/Psíquico y altas defensas y Ataque Especial al caer sus PS por debajo del 50%. "
        "En Pokémon Negro 2 y Blanco 2 ya no aparecen las estatuas del Castillo Ancestral de BW1; se obtiene "
        "intercambiando o criando a partir de un Darmanitan con Modo Daruma de Pokémon Negro/Blanco."
        if is_b2w2 else
        "Adquiere el tipo Fuego/Psíquico y altas defensas y Ataque Especial al caer sus PS por debajo del 50%. "
        "En el exterior del Castillo Ancestral hay 5 estatuas de Darmanitan que despiertan con esta habilidad al entregarles un Caramelo Furia."
    )
    return [
        {
            "form_key": "standard",
            "name": "Forma Normal",
            "display_name": "Darmanitan",
            "category": "Pokémon Candente",
            "primary_type": "fire",
            "primary_type_es": "Fuego",
            "secondary_type": "",
            "secondary_type_es": "",
            **_build_retro_form_sprites(clean_slug, "555"),
            "sprite_modern": "/media/pokemon/home/555.png",
            "sprite_modern_shiny": "/media/pokemon/home/shiny/555.png",
            "notes": [
                {
                    "title": "Forma Normal",
                    "text": "Forma habitual de tipo Fuego. Destaca por su descomunal Ataque físico (140) y la habilidad Potencia Bruta.",
                    "tag": "Fuego",
                    "icon": "/media/items/rule-book.png",
                }
            ],
        },
        {
            "form_key": "zen",
            "name": "Modo Daruma",
            "display_name": "Darmanitan (Modo Daruma)",
            "category": "Pokémon Candente",
            "primary_type": "fire",
            "primary_type_es": "Fuego",
            "secondary_type": "psychic",
            "secondary_type_es": "Psíquico",
            **_build_retro_form_sprites(clean_slug, "darmanitan/zen"),
            "sprite_modern": "/media/pokemon/home/10017.png",
            "sprite_modern_shiny": "/media/pokemon/home/shiny/10017.png",
            "notes": [
                {
                    "title": "Modo Daruma (Habilidad Oculta)",
                    "text": zen_text,
                    "tag": "Modo Daruma",
                    "icon": "/media/items/rage-candy-bar.png",
                }
            ],
        },
    ]


def get_deerling_forms(game_slug: str = "black") -> List[Dict[str, Any]]:
    clean_slug = (game_slug or "black").replace("_national", "")
    seasons = [
        ("spring", "Forma Primavera", "Primavera (Ene / May / Sep)", "deerling/spring", "585"),
        ("summer", "Forma Verano", "Verano (Feb / Jun / Oct)", "deerling/summer", None),
        ("autumn", "Forma Otoño", "Otoño (Mar / Jul / Nov)", "deerling/autumn", None),
        ("winter", "Forma Invierno", "Invierno (Abr / Ago / Dic)", "deerling/winter", None),
    ]
    forms = []
    for f_key, f_name, season_text, rel_stem, rel_back_anim in seasons:
        forms.append({
            "form_key": f_key,
            "name": f_name,
            "display_name": f"Deerling ({f_name.replace('Forma ', '')})",
            "category": "Pokémon Estacional",
            "primary_type": "normal",
            "primary_type_es": "Normal",
            "secondary_type": "grass",
            "secondary_type_es": "Planta",
            **_build_retro_form_sprites(clean_slug, rel_stem, rel_back_anim=rel_back_anim),
            "sprite_modern": f"/media/pokemon/home/585-{f_key}.png",
            "sprite_modern_shiny": f"/media/pokemon/home/shiny/585-{f_key}.png",
            "notes": [
                {
                    "title": season_text,
                    "text": "Cambia su pelaje automáticamente según la estación del año activa en Teselia cuando está en el equipo o en la caja del PC.",
                    "tag": "Estación",
                    "icon": "/media/items/rule-book.png",
                }
            ],
        })
    return forms


def get_sawsbuck_forms(game_slug: str = "black") -> List[Dict[str, Any]]:
    clean_slug = (game_slug or "black").replace("_national", "")
    seasons = [
        ("spring", "Forma Primavera", "Primavera (Ene / May / Sep)", "sawsbuck/spring", "586"),
        ("summer", "Forma Verano", "Verano (Feb / Jun / Oct)", "sawsbuck/summer", None),
        ("autumn", "Forma Otoño", "Otoño (Mar / Jul / Nov)", "sawsbuck/autumn", None),
        ("winter", "Forma Invierno", "Invierno (Abr / Ago / Dic)", "sawsbuck/winter", None),
    ]
    forms = []
    for f_key, f_name, season_text, rel_stem, rel_back_anim in seasons:
        forms.append({
            "form_key": f_key,
            "name": f_name,
            "display_name": f"Sawsbuck ({f_name.replace('Forma ', '')})",
            "category": "Pokémon Estacional",
            "primary_type": "normal",
            "primary_type_es": "Normal",
            "secondary_type": "grass",
            "secondary_type_es": "Planta",
            **_build_retro_form_sprites(clean_slug, rel_stem, rel_back_anim=rel_back_anim),
            "sprite_modern": f"/media/pokemon/home/586-{f_key}.png",
            "sprite_modern_shiny": f"/media/pokemon/home/shiny/586-{f_key}.png",
            "notes": [
                {
                    "title": season_text,
                    "text": "Modifica su cornamenta y follaje automáticamente según la estación del año activa en Teselia.",
                    "tag": "Estación",
                    "icon": "/media/items/rule-book.png",
                }
            ],
        })
    return forms


def get_meloetta_forms(game_slug: str = "black") -> List[Dict[str, Any]]:
    clean_slug = (game_slug or "black").replace("_national", "")
    return [
        {
            "form_key": "aria",
            "name": "Forma Lírica",
            "display_name": "Meloetta (Forma Lírica)",
            "category": "Pokémon Melodía",
            "primary_type": "normal",
            "primary_type_es": "Normal",
            "secondary_type": "psychic",
            "secondary_type_es": "Psíquico",
            **_build_retro_form_sprites(clean_slug, "648"),
            "sprite_modern": "/media/pokemon/home/648.png",
            "sprite_modern_shiny": "/media/pokemon/home/shiny/648.png",
            "notes": [
                {
                    "title": "Forma Lírica",
                    "text": "Forma base de tipo Normal/Psíquico orientada al Ataque Especial y la Defensa Especial. Habilidad Dicha.",
                    "tag": "Psíquico",
                    "icon": "/media/items/rule-book.png",
                }
            ],
        },
        {
            "form_key": "pirouette",
            "name": "Forma Danza",
            "display_name": "Meloetta (Forma Danza)",
            "category": "Pokémon Melodía",
            "primary_type": "normal",
            "primary_type_es": "Normal",
            "secondary_type": "fighting",
            "secondary_type_es": "Lucha",
            **_build_retro_form_sprites(clean_slug, "meloetta/pirouette"),
            "sprite_modern": "/media/pokemon/home/10018.png",
            "sprite_modern_shiny": "/media/pokemon/home/shiny/10018.png",
            "notes": [
                {
                    "title": "Canto Arcaico (La melodía del descanso)",
                    "text": "Meloetta adopta esta forma de tipo Normal/Lucha al usar en combate el movimiento Canto Arcaico, enseñado por un músico en la cafetería La melodía del descanso de Ciudad Porcelana.",
                    "tag": "Lucha",
                    "icon": "/media/items/rule-book.png",
                }
            ],
        },
    ]


def get_genesect_forms(game_slug: str = "black") -> List[Dict[str, Any]]:
    clean_slug = (game_slug or "black").replace("_national", "")
    is_white = (clean_slug == "white")
    is_b2w2 = clean_slug in B2W2_FORM_GAMES
    b2w2_note = "Entregado junto a los otros 3 cartuchos por el Montañero del Laboratorio P+P tras combatir llevando a Genesect."
    drives = [
        ("normal", "Forma Normal", "Normal", "649", "Sin cartucho equipado. Su movimiento característico Tecnochoque es de tipo Normal.", None),
        (
            "shock", "FulgoROM", "Eléctrico", "genesect/shock",
            "Equipado con el cartucho FulgoROM. Su movimiento Tecnochoque pasa a ser de tipo Eléctrico. " + (
                b2w2_note if is_b2w2 else (
                    "Exclusivo de Pokémon Negro (requiere intercambio equipado desde Negro)."
                    if is_white else
                    "Entregado por el científico del Laboratorio P+P en Pokémon Negro tras derrotarlo."
                )
            ),
            "/media/items/shock-drive.png",
        ),
        (
            "burn", "PiroROM", "Fuego", "genesect/burn",
            "Equipado con el cartucho PiroROM. Su movimiento Tecnochoque pasa a ser de tipo Fuego. " + (
                b2w2_note if is_b2w2 else (
                    "Exclusivo de Pokémon Negro (requiere intercambio equipado desde Negro)."
                    if is_white else
                    "Entregado por el científico del Laboratorio P+P en Pokémon Negro tras derrotarlo."
                )
            ),
            "/media/items/burn-drive.png",
        ),
        (
            "douse", "HidroROM", "Agua", "genesect/douse",
            "Equipado con el cartucho HidroROM. Su movimiento Tecnochoque pasa a ser de tipo Agua. " + (
                b2w2_note if is_b2w2 else (
                    "Entregado por el científico del Laboratorio P+P en Pokémon Blanco tras derrotarlo."
                    if is_white else
                    "Exclusivo de Pokémon Blanco (requiere intercambio equipado desde Blanco)."
                )
            ),
            "/media/items/douse-drive.png",
        ),
        (
            "chill", "CrioROM", "Hielo", "genesect/chill",
            "Equipado con el cartucho CrioROM. Su movimiento Tecnochoque pasa a ser de tipo Hielo. " + (
                b2w2_note if is_b2w2 else (
                    "Entregado por el científico del Laboratorio P+P en Pokémon Blanco tras derrotarlo."
                    if is_white else
                    "Exclusivo de Pokémon Blanco (requiere intercambio equipado desde Blanco)."
                )
            ),
            "/media/items/chill-drive.png",
        ),
    ]
    forms = []
    for f_key, f_name, type_label, rel_stem, desc, icon_path in drives:
        home_stem = "649" if f_key == "normal" else f"649-{f_key}"
        forms.append({
            "form_key": f_key,
            "name": f_name,
            "display_name": f"Genesect ({f_name.replace('Forma ', '')})",
            "category": "Pokémon Paleozoico",
            "primary_type": "bug",
            "primary_type_es": "Bicho",
            "secondary_type": "steel",
            "secondary_type_es": "Acero",
            **_build_retro_form_sprites(clean_slug, rel_stem),
            "sprite_modern": f"/media/pokemon/home/{home_stem}.png",
            "sprite_modern_shiny": f"/media/pokemon/home/shiny/{home_stem}.png",
            "notes": [
                {
                    "title": f"Cartucho {f_name} ({type_label})" if f_key != "normal" else "Forma Normal (Sin Cartucho)",
                    "text": desc,
                    "tag": type_label,
                    "icon": icon_path or "/media/items/rule-book.png",
                }
            ],
        })
    return forms


def get_tornadus_forms(game_slug: str = "black-2") -> List[Dict[str, Any]]:
    clean_slug = (game_slug or "black-2").replace("_national", "")
    return [
        {
            "form_key": "incarnate",
            "name": "Forma Avatar",
            "display_name": "Tornadus (Forma Avatar)",
            "category": "Pokémon Torbellino",
            "primary_type": "flying",
            "primary_type_es": "Volador",
            "secondary_type": "",
            "secondary_type_es": "",
            **_build_retro_form_sprites(clean_slug, "641"),
            "sprite_modern": "/media/pokemon/home/641.png",
            "sprite_modern_shiny": "/media/pokemon/home/shiny/641.png",
            "notes": [
                {
                    "title": "Forma Avatar • Espejo Veraz",
                    "text": "Forma original de tipo Volador puro con habilidad Bromista. Puedes alternar entre Forma Avatar y Forma Tótem usando el Espejo Veraz, entregado en el Santuario Abundancia tras llevar a Landorus Forma Tótem procedente del RAdar Pokémon.",
                    "tag": "Espejo Veraz",
                    "icon": "/media/items/reveal-glass.png",
                }
            ],
        },
        {
            "form_key": "therian",
            "name": "Forma Tótem",
            "display_name": "Tornadus (Forma Tótem)",
            "category": "Pokémon Torbellino",
            "primary_type": "flying",
            "primary_type_es": "Volador",
            "secondary_type": "",
            "secondary_type_es": "",
            **_build_retro_form_sprites(clean_slug, "tornadus/therian"),
            "sprite_modern": "/media/pokemon/home/10019.png",
            "sprite_modern_shiny": "/media/pokemon/home/shiny/10019.png",
            "notes": [
                {
                    "title": "Forma Tótem (Teselia 2)",
                    "text": "Introducida en Pokémon Negro 2 y Blanco 2. Obtenible mediante RAdar Pokémon o transformando a Tornadus con el Espejo Veraz (Santuario Abundancia). Adquiere la habilidad Regeneración y aumenta notablemente su Velocidad y defensas.",
                    "tag": "Regeneración",
                    "icon": "/media/items/reveal-glass.png",
                }
            ],
        },
    ]


def get_thundurus_forms(game_slug: str = "black-2") -> List[Dict[str, Any]]:
    clean_slug = (game_slug or "black-2").replace("_national", "")
    return [
        {
            "form_key": "incarnate",
            "name": "Forma Avatar",
            "display_name": "Thundurus (Forma Avatar)",
            "category": "Pokémon Centella",
            "primary_type": "electric",
            "primary_type_es": "Eléctrico",
            "secondary_type": "flying",
            "secondary_type_es": "Volador",
            **_build_retro_form_sprites(clean_slug, "642"),
            "sprite_modern": "/media/pokemon/home/642.png",
            "sprite_modern_shiny": "/media/pokemon/home/shiny/642.png",
            "notes": [
                {
                    "title": "Forma Avatar • Espejo Veraz",
                    "text": "Forma original Eléctrico/Volador con habilidad Bromista. Alterna a Forma Tótem usando el Espejo Veraz, entregado en el Santuario Abundancia al llevar a Landorus Forma Tótem del RAdar Pokémon.",
                    "tag": "Espejo Veraz",
                    "icon": "/media/items/reveal-glass.png",
                }
            ],
        },
        {
            "form_key": "therian",
            "name": "Forma Tótem",
            "display_name": "Thundurus (Forma Tótem)",
            "category": "Pokémon Centella",
            "primary_type": "electric",
            "primary_type_es": "Eléctrico",
            "secondary_type": "flying",
            "secondary_type_es": "Volador",
            **_build_retro_form_sprites(clean_slug, "thundurus/therian"),
            "sprite_modern": "/media/pokemon/home/10020.png",
            "sprite_modern_shiny": "/media/pokemon/home/shiny/10020.png",
            "notes": [
                {
                    "title": "Forma Tótem (Teselia 2)",
                    "text": "Introducida en Pokémon Negro 2 y Blanco 2. Obtenible mediante RAdar Pokémon o transformando a Thundurus con el Espejo Veraz (Santuario Abundancia). Posee la habilidad Absorbe Electricidad y un Ataque Especial extraordinario (145).",
                    "tag": "Absorbe Elec.",
                    "icon": "/media/items/reveal-glass.png",
                }
            ],
        },
    ]


def get_landorus_forms(game_slug: str = "black-2") -> List[Dict[str, Any]]:
    clean_slug = (game_slug or "black-2").replace("_national", "")
    return [
        {
            "form_key": "incarnate",
            "name": "Forma Avatar",
            "display_name": "Landorus (Forma Avatar)",
            "category": "Pokémon Fertilidad",
            "primary_type": "ground",
            "primary_type_es": "Tierra",
            "secondary_type": "flying",
            "secondary_type_es": "Volador",
            **_build_retro_form_sprites(clean_slug, "645"),
            "sprite_modern": "/media/pokemon/home/645.png",
            "sprite_modern_shiny": "/media/pokemon/home/shiny/645.png",
            "notes": [
                {
                    "title": "Forma Avatar • Espejo Veraz",
                    "text": "Forma original Tierra/Volador con habilidad Poder Arena. Alterna libremente con su Forma Tótem usando el Espejo Veraz obtenido en el Santuario Abundancia.",
                    "tag": "Espejo Veraz",
                    "icon": "/media/items/reveal-glass.png",
                }
            ],
        },
        {
            "form_key": "therian",
            "name": "Forma Tótem",
            "display_name": "Landorus (Forma Tótem)",
            "category": "Pokémon Fertilidad",
            "primary_type": "ground",
            "primary_type_es": "Tierra",
            "secondary_type": "flying",
            "secondary_type_es": "Volador",
            **_build_retro_form_sprites(clean_slug, "landorus/therian"),
            "sprite_modern": "/media/pokemon/home/10021.png",
            "sprite_modern_shiny": "/media/pokemon/home/shiny/10021.png",
            "notes": [
                {
                    "title": "Forma Tótem (Teselia 2)",
                    "text": "Introducida en Pokémon Negro 2 y Blanco 2. Llevar a Landorus Forma Tótem del RAdar Pokémon al Santuario Abundancia desbloquea el Espejo Veraz. Cuenta con la habilidad Intimidación y un altísimo Ataque físico (145).",
                    "tag": "Intimidación",
                    "icon": "/media/items/reveal-glass.png",
                }
            ],
        },
    ]


def get_kyurem_forms(game_slug: str = "black-2") -> List[Dict[str, Any]]:
    clean_slug = (game_slug or "black-2").replace("_national", "")
    is_black2 = (clean_slug == "black-2")
    return [
        {
            "form_key": "normal",
            "name": "Forma Normal",
            "display_name": "Kyurem",
            "category": "Pokémon Frontera",
            "primary_type": "dragon",
            "primary_type_es": "Dragón",
            "secondary_type": "ice",
            "secondary_type_es": "Hielo",
            **_build_retro_form_sprites(clean_slug, "646"),
            "sprite_modern": "/media/pokemon/home/646.png",
            "sprite_modern_shiny": "/media/pokemon/home/shiny/646.png",
            "notes": [
                {
                    "title": "Boquete Gigante (Post-Liga)",
                    "text": "Capturable al Nv. 70 en la cueva central del Boquete Gigante tras atrapar a Zekrom en la Torre Duodraco. Al capturarlo o derrotarlo deja caer la Punta ADN.",
                    "tag": "Punta ADN",
                    "icon": "/media/items/dna-splicers.png",
                }
            ],
        },
        {
            "form_key": "black",
            "name": "Kyurem Negro",
            "display_name": "Kyurem Negro",
            "category": "Pokémon Frontera",
            "primary_type": "dragon",
            "primary_type_es": "Dragón",
            "secondary_type": "ice",
            "secondary_type_es": "Hielo",
            **_build_retro_form_sprites(clean_slug, "kyurem/black"),
            "sprite_modern": "/media/pokemon/home/10022.png",
            "sprite_modern_shiny": "/media/pokemon/home/shiny/10022.png",
            "notes": [
                {
                    "title": "Fusión con Zekrom (Punta ADN)",
                    "text": (
                        "Fusión de Kyurem y Zekrom mediante la Punta ADN (nativa en Pokémon Negro 2 tras capturar a Zekrom en la Torre Duodraco). "
                        "Posee la habilidad Terravoltaje, un colosal Ataque físico (170) y el movimiento Rayo Gélido."
                        if is_black2 else
                        "Fusión de Kyurem y Zekrom mediante la Punta ADN (requiere intercambiar un Zekrom desde Pokémon Negro 2 o Pokémon Blanco). "
                        "Posee la habilidad Terravoltaje, un colosal Ataque físico (170) y el movimiento Rayo Gélido."
                    ),
                    "tag": "Punta ADN",
                    "icon": "/media/items/dna-splicers.png",
                }
            ],
        },
        {
            "form_key": "white",
            "name": "Kyurem Blanco",
            "display_name": "Kyurem Blanco",
            "category": "Pokémon Frontera",
            "primary_type": "dragon",
            "primary_type_es": "Dragón",
            "secondary_type": "ice",
            "secondary_type_es": "Hielo",
            **_build_retro_form_sprites(clean_slug, "kyurem/white"),
            "sprite_modern": "/media/pokemon/home/10023.png",
            "sprite_modern_shiny": "/media/pokemon/home/shiny/10023.png",
            "notes": [
                {
                    "title": "Fusión con Reshiram (Punta ADN)",
                    "text": (
                        "Fusión de Kyurem y Reshiram mediante la Punta ADN (requiere intercambiar un Reshiram desde Pokémon Blanco 2 o Pokémon Negro). "
                        "Posee la habilidad Turbollama, un colosal Ataque Especial (170) y el movimiento Llama Gélida."
                        if is_black2 else
                        "Fusión de Kyurem y Reshiram mediante la Punta ADN (nativa en Pokémon Blanco 2 tras capturar a Reshiram en la Torre Duodraco). "
                        "Posee la habilidad Turbollama, un colosal Ataque Especial (170) y el movimiento Llama Gélida."
                    ),
                    "tag": "Punta ADN",
                    "icon": "/media/items/dna-splicers.png",
                }
            ],
        },
    ]


def get_keldeo_forms(game_slug: str = "black-2") -> List[Dict[str, Any]]:
    clean_slug = (game_slug or "black-2").replace("_national", "")
    return [
        {
            "form_key": "ordinary",
            "name": "Forma Habitual",
            "display_name": "Keldeo (Forma Habitual)",
            "category": "Pokémon Potro",
            "primary_type": "water",
            "primary_type_es": "Agua",
            "secondary_type": "fighting",
            "secondary_type_es": "Lucha",
            **_build_retro_form_sprites(clean_slug, "647"),
            "sprite_modern": "/media/pokemon/home/647.png",
            "sprite_modern_shiny": "/media/pokemon/home/shiny/647.png",
            "notes": [
                {
                    "title": "Forma Habitual",
                    "text": "Forma base de Keldeo antes de conocer el movimiento Sable Místico (o si olvida dicho movimiento).",
                    "tag": "Agua / Lucha",
                    "icon": "/media/items/rule-book.png",
                }
            ],
        },
        {
            "form_key": "resolute",
            "name": "Forma Brío",
            "display_name": "Keldeo (Forma Brío)",
            "category": "Pokémon Potro",
            "primary_type": "water",
            "primary_type_es": "Agua",
            "secondary_type": "fighting",
            "secondary_type_es": "Lucha",
            **_build_retro_form_sprites(clean_slug, "keldeo/resolute"),
            "sprite_modern": "/media/pokemon/home/10024.png",
            "sprite_modern_shiny": "/media/pokemon/home/shiny/10024.png",
            "notes": [
                {
                    "title": "Arboleda Promesa • Sable Místico",
                    "text": "Introducida en Pokémon Negro 2 y Blanco 2. Al llevar a Keldeo a la Arboleda Promesa (al norte de Pueblo Ocre) junto a Cobalion, Terrakion y Virizion en el equipo, examinar la roca marcada le enseña Sable Místico y adopta la Forma Brío.",
                    "tag": "Arboleda Promesa",
                    "icon": "/media/items/rule-book.png",
                }
            ],
        },
    ]


def get_pokemon_forms(national_number: int, game_slug: str = "ruby") -> List[Dict[str, Any]]:
    """
    Punto de entrada unificado y escalable para obtener las formas alternas de un Pokémon.
    Retorna una lista vacía para especies sin formas alternativas en la edición activa.
    """
    clean_slug = (game_slug or "ruby").replace("_national", "")
    cfg = get_game_sprite_config(clean_slug)
    gen = cfg["gen"]
    is_gen4 = (gen == 4)
    is_gen5 = (gen == 5)

    # 1. Pichu Picoreja (#172) disponible en HeartGold y SoulSilver
    if national_number == 172 and clean_slug in ["heartgold", "soulsilver"]:
        return get_pichu_forms(clean_slug)

    # 2. Unown (#201) disponible en Gen 2+
    elif national_number == 201 and gen >= 2:
        return get_unown_forms(clean_slug)

    # 3. Castform (#351) disponible en Gen 3+
    elif national_number == 351 and gen >= 3:
        return get_castform_forms(clean_slug)

    # 4. Formas activas en Gen 4 y Gen 5
    elif is_gen4 or is_gen5:
        if national_number == 386:
            return get_deoxys_forms(clean_slug)
        elif national_number == 412:
            return get_burmy_forms(clean_slug)
        elif national_number == 413:
            return get_wormadam_forms(clean_slug)
        elif national_number == 421:
            return get_cherrim_forms(clean_slug)
        elif national_number == 422:
            return get_shellos_forms(clean_slug)
        elif national_number == 423:
            return get_gastrodon_forms(clean_slug)
        elif national_number == 479 and (clean_slug in ["platinum", "heartgold", "soulsilver"] or is_gen5):
            return get_rotom_forms(clean_slug)
        elif national_number == 487 and (clean_slug in ["platinum", "heartgold", "soulsilver"] or is_gen5):
            return get_giratina_forms(clean_slug)
        elif national_number == 492 and (clean_slug in ["platinum", "heartgold", "soulsilver"] or is_gen5):
            return get_shaymin_forms(clean_slug)
        elif national_number == 493:
            return get_arceus_forms(clean_slug)

    # 5. Formas exclusivas de 5.ª Generación (Teselia)
    if is_gen5:
        if national_number == 550:
            return get_basculin_forms(clean_slug)
        elif national_number == 555:
            return get_darmanitan_forms(clean_slug)
        elif national_number == 585:
            return get_deerling_forms(clean_slug)
        elif national_number == 586:
            return get_sawsbuck_forms(clean_slug)
        elif national_number == 648:
            return get_meloetta_forms(clean_slug)
        elif national_number == 649:
            return get_genesect_forms(clean_slug)

    # 6. Formas introducidas exclusivamente en Pokémon Negro 2 y Blanco 2 (Teselia 2)
    if clean_slug in B2W2_FORM_GAMES:
        if national_number == 641:
            return get_tornadus_forms(clean_slug)
        elif national_number == 642:
            return get_thundurus_forms(clean_slug)
        elif national_number == 645:
            return get_landorus_forms(clean_slug)
        elif national_number == 646:
            return get_kyurem_forms(clean_slug)
        elif national_number == 647:
            return get_keldeo_forms(clean_slug)

    return []
