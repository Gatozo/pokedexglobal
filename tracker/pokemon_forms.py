"""
Gestión de Pokémon con múltiples formas alternativas canónicas.
Soporte completo y escalable para Generaciones 1 a 4.

- Gen 1 a 3: Castform (#351) y Unown (#201).
- Gen 4 (Diamante y Perla):
  * Unown (#201): 28 formas (manejado de forma dedicada en Bloc Unown).
  * Castform (#351): 4 formas climáticas (sprites Gen 4 nativos).
  * Deoxys (#386): 4 formas (Normal, Ataque, Defensa, Velocidad vía meteoritos de Rocavelo).
  * Burmy (#412): 3 troncos (Planta, Arena, Basura por entorno de combate y crianza).
  * Wormadam (#413): 3 troncos fijos con tipos elementales distintos (Bicho/Planta, Bicho/Tierra, Bicho/Acero).
  * Cherrim (#421): 2 formas (Encapuchada y Soleada vía clima de sol en combate).
  * Shellos (#422): 2 formas geográficas (Mar Oeste / Mar Este delimitadas por el Monte Corona).
  * Gastrodon (#423): 2 formas geográficas (Mar Oeste / Mar Este delimitadas por el Monte Corona).
  * Arceus (#493): 17 formas (Normal + 16 Tablas elementales canónicas de Sinnoh; excluyendo Tipo Hada inexistente en Gen 4).
"""

from typing import List, Dict, Any


def get_castform_forms(game_slug: str = "ruby") -> List[Dict[str, Any]]:
    """
    Retorna las 4 formas climáticas de Castform (#351):
    Forma Normal (Normal), Forma Sol (Fuego), Forma Lluvia (Agua), Forma Nieve (Hielo).
    Soporta sprites de Hoenn (Gen 3) y sprites nativos de Sinnoh (Gen 4 Diamante/Perla).
    """
    is_gen4 = game_slug in ["diamond", "pearl", "platinum"]
    slug = "diamond" if is_gen4 else (game_slug if game_slug in ["ruby", "sapphire", "emerald", "firered", "leafgreen"] else "ruby")
    is_emerald = (slug == "emerald")

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
            "sprite_retro": f"/media/pokemon/sprites/{slug}/351.png",
            "sprite_retro_shiny": f"/media/pokemon/sprites/{slug}_shiny/351.png",
            "modal_retro_sprite_url": "/media/pokemon/sprites/emerald_animated/351.gif" if is_emerald else None,
            "modal_retro_sprite_shiny_url": "/media/pokemon/sprites/emerald_animated_shiny/351.gif" if is_emerald else None,
            "sprite_retro_back": f"/media/pokemon/sprites/{slug}/back/351.png",
            "sprite_retro_shiny_back": f"/media/pokemon/sprites/{slug}_shiny/back/351.png",
            "sprite_modern": "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/351.png",
            "sprite_modern_shiny": "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/shiny/351.png",
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
            "sprite_retro": f"/media/pokemon/sprites/{slug}/castform/sunny.png",
            "sprite_retro_shiny": f"/media/pokemon/sprites/{slug}_shiny/castform/sunny.png",
            "modal_retro_sprite_url": "/media/pokemon/sprites/emerald_animated/castform/sunny.gif" if is_emerald else None,
            "modal_retro_sprite_shiny_url": "/media/pokemon/sprites/emerald_animated_shiny/castform/sunny.gif" if is_emerald else None,
            "sprite_retro_back": f"/media/pokemon/sprites/{slug}/back/castform/sunny.png",
            "sprite_retro_shiny_back": f"/media/pokemon/sprites/{slug}_shiny/back/castform/sunny.png",
            "sprite_modern": "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/10013.png",
            "sprite_modern_shiny": "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/shiny/10013.png",
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
            "sprite_retro": f"/media/pokemon/sprites/{slug}/castform/rainy.png",
            "sprite_retro_shiny": f"/media/pokemon/sprites/{slug}_shiny/castform/rainy.png",
            "modal_retro_sprite_url": "/media/pokemon/sprites/emerald_animated/castform/rainy.gif" if is_emerald else None,
            "modal_retro_sprite_shiny_url": "/media/pokemon/sprites/emerald_animated_shiny/castform/rainy.gif" if is_emerald else None,
            "sprite_retro_back": f"/media/pokemon/sprites/{slug}/back/castform/rainy.png",
            "sprite_retro_shiny_back": f"/media/pokemon/sprites/{slug}_shiny/back/castform/rainy.png",
            "sprite_modern": "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/10014.png",
            "sprite_modern_shiny": "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/shiny/10014.png",
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
            "sprite_retro": f"/media/pokemon/sprites/{slug}/castform/snowy.png",
            "sprite_retro_shiny": f"/media/pokemon/sprites/{slug}_shiny/castform/snowy.png",
            "modal_retro_sprite_url": "/media/pokemon/sprites/emerald_animated/castform/snowy.gif" if is_emerald else None,
            "modal_retro_sprite_shiny_url": "/media/pokemon/sprites/emerald_animated_shiny/castform/snowy.gif" if is_emerald else None,
            "sprite_retro_back": f"/media/pokemon/sprites/{slug}/back/castform/snowy.png",
            "sprite_retro_shiny_back": f"/media/pokemon/sprites/{slug}_shiny/back/castform/snowy.png",
            "sprite_modern": "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/10015.png",
            "sprite_modern_shiny": "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/shiny/10015.png",
            "notes": notes_snowy,
        }
    ]


def get_deoxys_forms(game_slug: str = "diamond") -> List[Dict[str, Any]]:
    """
    Retorna las 4 formas de Deoxys (#386) en Sinnoh:
    Normal, Ataque, Defensa, Velocidad.
    En Diamante y Perla, Deoxys cambia entre sus 4 formas al interactuar con los meteoritos de Ciudad Rocavelo.
    """
    slug = "diamond"
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
            "sprite_retro": f"/media/pokemon/sprites/{slug}/386.png",
            "sprite_retro_shiny": f"/media/pokemon/sprites/{slug}_shiny/386.png",
            "sprite_retro_back": f"/media/pokemon/sprites/{slug}/back/386.png",
            "sprite_retro_shiny_back": f"/media/pokemon/sprites/{slug}_shiny/back/386.png",
            "sprite_modern": "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/386.png",
            "sprite_modern_shiny": "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/shiny/386.png",
            "notes": [
                {
                    "title": "Meteoritos de Ciudad Rocavelo",
                    "text": "En Diamante y Perla, Deoxys cambia libremente entre sus 4 formas interactuando con los 4 meteoritos extraterrestres al sureste de Ciudad Rocavelo. El meteorito superior izquierdo activa la Forma Normal.",
                    "tag": "Meteorito",
                    "icon": "/media/items/meteorite.png",
                }
            ],
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
            "sprite_retro": f"/media/pokemon/sprites/{slug}/deoxys/attack.png",
            "sprite_retro_shiny": f"/media/pokemon/sprites/{slug}_shiny/deoxys/attack.png",
            "sprite_retro_back": f"/media/pokemon/sprites/{slug}/back/deoxys/attack.png",
            "sprite_retro_shiny_back": f"/media/pokemon/sprites/{slug}_shiny/back/deoxys/attack.png",
            "sprite_modern": "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/10001.png",
            "sprite_modern_shiny": "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/shiny/10001.png",
            "notes": [
                {
                    "title": "Meteorito de Ataque (Ciudad Rocavelo)",
                    "text": "Interactúa con el meteorito inferior derecho en Ciudad Rocavelo para transformarlo a su Forma Ataque. Aumenta drásticamente su Ataque y Ataque Especial reduciendo sus Defensas.",
                    "tag": "Meteorito",
                    "icon": "/media/items/meteorite.png",
                }
            ],
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
            "sprite_retro": f"/media/pokemon/sprites/{slug}/deoxys/defense.png",
            "sprite_retro_shiny": f"/media/pokemon/sprites/{slug}_shiny/deoxys/defense.png",
            "sprite_retro_back": f"/media/pokemon/sprites/{slug}/back/deoxys/defense.png",
            "sprite_retro_shiny_back": f"/media/pokemon/sprites/{slug}_shiny/back/deoxys/defense.png",
            "sprite_modern": "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/10002.png",
            "sprite_modern_shiny": "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/shiny/10002.png",
            "notes": [
                {
                    "title": "Meteorito de Defensa (Ciudad Rocavelo)",
                    "text": "Interactúa con el meteorito inferior izquierdo en Ciudad Rocavelo para transformarlo a su Forma Defensa. Maximiza sus estadísticas defensivas a costa de velocidad y poder ofensivo.",
                    "tag": "Meteorito",
                    "icon": "/media/items/meteorite.png",
                }
            ],
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
            "sprite_retro": f"/media/pokemon/sprites/{slug}/deoxys/speed.png",
            "sprite_retro_shiny": f"/media/pokemon/sprites/{slug}_shiny/deoxys/speed.png",
            "sprite_retro_back": f"/media/pokemon/sprites/{slug}/back/deoxys/speed.png",
            "sprite_retro_shiny_back": f"/media/pokemon/sprites/{slug}_shiny/back/deoxys/speed.png",
            "sprite_modern": "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/10003.png",
            "sprite_modern_shiny": "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/shiny/10003.png",
            "notes": [
                {
                    "title": "Meteorito de Velocidad (Ciudad Rocavelo)",
                    "text": "Interactúa con el meteorito superior derecho en Ciudad Rocavelo para transformarlo a su Forma Velocidad. Otorga una de las mayores estadísticas de Velocidad de todo el juego.",
                    "tag": "Meteorito",
                    "icon": "/media/items/meteorite.png",
                }
            ],
        }
    ]


def get_burmy_forms(game_slug: str = "diamond") -> List[Dict[str, Any]]:
    """
    Retorna los 3 troncos de Burmy (#412) en Sinnoh:
    Tronco Planta, Tronco Arena, Tronco Basura.
    """
    slug = "diamond"
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
            "sprite_retro": f"/media/pokemon/sprites/{slug}/burmy/plant.png",
            "sprite_retro_shiny": f"/media/pokemon/sprites/{slug}_shiny/burmy/plant.png",
            "sprite_retro_back": f"/media/pokemon/sprites/{slug}/back/burmy/plant.png",
            "sprite_retro_shiny_back": f"/media/pokemon/sprites/{slug}_shiny/back/burmy/plant.png",
            "sprite_modern": "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/412.png",
            "sprite_modern_shiny": "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/shiny/412.png",
            "summary": "Salvaje en árboles de miel en exteriores y rutas abiertas.",
            "locations": [
                {"area": "Árboles de Miel (Exteriores)", "method": "Untar Miel (Hierba/Rutas abiertas)"}
            ],
            "notes": [
                {
                    "title": "Camuflaje por Terreno",
                    "text": "Adopta el Tronco Planta tras combatir en exteriores, rutas de hierba alta o bosques.",
                    "tag": "Entorno",
                    "icon": "/media/items/miracle-seed.png",
                },
                {
                    "title": "Crianza y Eclosión",
                    "text": "Al eclosionar de un huevo, Burmy nace con la forma del lugar geográfico donde se abrió el huevo (eclosionar en exteriores da Tronco Planta).",
                    "tag": "Crianza",
                    "icon": "/media/items/mystery-egg.png",
                },
                {
                    "title": "Evolución por Género",
                    "text": "Las hembras evolucionan a Wormadam a Nivel 20 conservando permanentemente este tronco. Los machos siempre evolucionan a Mothim perdiendo el camuflaje.",
                    "tag": "Evolución",
                    "icon": "/media/items/rule-book.png",
                }
            ],
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
            "sprite_retro": f"/media/pokemon/sprites/{slug}/burmy/sandy.png",
            "sprite_retro_shiny": f"/media/pokemon/sprites/{slug}_shiny/burmy/sandy.png",
            "sprite_retro_back": f"/media/pokemon/sprites/{slug}/back/burmy/sandy.png",
            "sprite_retro_shiny_back": f"/media/pokemon/sprites/{slug}_shiny/back/burmy/sandy.png",
            "sprite_modern": "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/412.png",
            "sprite_modern_shiny": "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/shiny/412.png",
            "summary": "Adopta este camuflaje tras combatir en cuevas o playas arenosas.",
            "locations": [
                {"area": "Cuevas y Playas de Sinnoh", "method": "Combatir en cueva/playa o Árboles de Miel de la zona"}
            ],
            "notes": [
                {
                    "title": "Camuflaje por Terreno",
                    "text": "Adopta el Tronco Arena tras combatir en el interior de cuevas o en terrenos arenosos de playas.",
                    "tag": "Entorno",
                    "icon": "/media/items/soft-sand.png",
                },
                {
                    "title": "Crianza y Eclosión",
                    "text": "Si el huevo eclosiona mientras el jugador se encuentra dentro de una cueva o en una playa, el Burmy recién nacido tendrá Tronco Arena.",
                    "tag": "Crianza",
                    "icon": "/media/items/mystery-egg.png",
                },
                {
                    "title": "Evolución por Género",
                    "text": "Las hembras evolucionan a Wormadam (Tronco Arena) a Nivel 20 fijando este tronco y ganando el tipo Tierra. Los machos siempre evolucionan a Mothim.",
                    "tag": "Evolución",
                    "icon": "/media/items/rule-book.png",
                }
            ],
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
            "sprite_retro": f"/media/pokemon/sprites/{slug}/burmy/trash.png",
            "sprite_retro_shiny": f"/media/pokemon/sprites/{slug}_shiny/burmy/trash.png",
            "sprite_retro_back": f"/media/pokemon/sprites/{slug}/back/burmy/trash.png",
            "sprite_retro_shiny_back": f"/media/pokemon/sprites/{slug}_shiny/back/burmy/trash.png",
            "sprite_modern": "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/412.png",
            "sprite_modern_shiny": "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/shiny/412.png",
            "summary": "Adopta este camuflaje tras combatir dentro de edificios o estancias cerradas.",
            "locations": [
                {"area": "Edificios e Interiores", "method": "Combatir en cualquier edificio cerrado"}
            ],
            "notes": [
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
            ],
        }
    ]


def get_wormadam_forms(game_slug: str = "diamond") -> List[Dict[str, Any]]:
    """
    Retorna los 3 troncos de Wormadam (#413) en Sinnoh:
    Tronco Planta (Bicho/Planta), Tronco Arena (Bicho/Tierra), Tronco Basura (Bicho/Acero).
    Cada forma tiene tipos elementales, estadísticas y evoluciones exclusivas.
    """
    slug = "diamond"
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
            "sprite_retro": f"/media/pokemon/sprites/{slug}/wormadam/plant.png",
            "sprite_retro_shiny": f"/media/pokemon/sprites/{slug}_shiny/wormadam/plant.png",
            "sprite_retro_back": f"/media/pokemon/sprites/{slug}/back/wormadam/plant.png",
            "sprite_retro_shiny_back": f"/media/pokemon/sprites/{slug}_shiny/back/wormadam/plant.png",
            "sprite_modern": "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/413.png",
            "sprite_modern_shiny": "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/shiny/413.png",
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
            "sprite_retro": f"/media/pokemon/sprites/{slug}/wormadam/sandy.png",
            "sprite_retro_shiny": f"/media/pokemon/sprites/{slug}_shiny/wormadam/sandy.png",
            "sprite_retro_back": f"/media/pokemon/sprites/{slug}/back/wormadam/sandy.png",
            "sprite_retro_shiny_back": f"/media/pokemon/sprites/{slug}_shiny/back/wormadam/sandy.png",
            "sprite_modern": "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/10004.png",
            "sprite_modern_shiny": "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/shiny/10004.png",
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
            "sprite_retro": f"/media/pokemon/sprites/{slug}/wormadam/trash.png",
            "sprite_retro_shiny": f"/media/pokemon/sprites/{slug}_shiny/wormadam/trash.png",
            "sprite_retro_back": f"/media/pokemon/sprites/{slug}/back/wormadam/trash.png",
            "sprite_retro_shiny_back": f"/media/pokemon/sprites/{slug}_shiny/back/wormadam/trash.png",
            "sprite_modern": "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/10005.png",
            "sprite_modern_shiny": "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/shiny/10005.png",
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
        }
    ]


def get_cherrim_forms(game_slug: str = "diamond") -> List[Dict[str, Any]]:
    """
    Retorna las 2 formas de Cherrim (#421) en Sinnoh:
    Forma Encapuchada (Overcast), Forma Soleada (Sunshine).
    """
    slug = "diamond"
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
            "sprite_retro": f"/media/pokemon/sprites/{slug}/cherrim/overcast.png",
            "sprite_retro_shiny": f"/media/pokemon/sprites/{slug}_shiny/cherrim/overcast.png",
            "sprite_retro_back": f"/media/pokemon/sprites/{slug}/back/cherrim/overcast.png",
            "sprite_retro_shiny_back": f"/media/pokemon/sprites/{slug}_shiny/back/cherrim/overcast.png",
            "sprite_modern": "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/421.png",
            "sprite_modern_shiny": "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/shiny/421.png",
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
            "sprite_retro": f"/media/pokemon/sprites/{slug}/cherrim/sunshine.png",
            "sprite_retro_shiny": f"/media/pokemon/sprites/{slug}_shiny/cherrim/sunshine.png",
            "sprite_retro_back": f"/media/pokemon/sprites/{slug}/back/cherrim/sunshine.png",
            "sprite_retro_shiny_back": f"/media/pokemon/sprites/{slug}_shiny/back/cherrim/sunshine.png",
            "sprite_modern": "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/10008.png",
            "sprite_modern_shiny": "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/shiny/10008.png",
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
    Retorna las 2 formas geográficas de Shellos (#422) en Sinnoh:
    Mar Oeste (Rosa), Mar Este (Azul).
    Rutas de obtención exclusivas a ambos lados del Monte Corona.
    """
    slug = "diamond"
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
            "sprite_retro": f"/media/pokemon/sprites/{slug}/shellos/west.png",
            "sprite_retro_shiny": f"/media/pokemon/sprites/{slug}_shiny/shellos/west.png",
            "sprite_retro_back": f"/media/pokemon/sprites/{slug}/back/shellos/west.png",
            "sprite_retro_shiny_back": f"/media/pokemon/sprites/{slug}_shiny/back/shellos/west.png",
            "sprite_modern": "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/422.png",
            "sprite_modern_shiny": "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/shiny/422.png",
            "summary": "Exclusivo de la vertiente occidental de Sinnoh (al oeste del Monte Corona).",
            "locations": [
                {"area": "Ruta 205", "method": "Salvaje (Hierba)"},
                {"area": "Ruta 218", "method": "Salvaje (Surfing / Pesca)"},
                {"area": "Parque Eólico", "method": "Salvaje (Hierba)"},
                {"area": "Forja Fuego", "method": "Salvaje (Hierba)"},
            ],
            "notes": [
                {
                    "title": "Variación Geográfica Sinnoh",
                    "text": "La cordillera del Monte Corona divide geográficamente las poblaciones de esta especie. La variante rosa habita exclusivamente en la zona occidental de la región.",
                    "tag": "Geografía",
                    "icon": "/media/items/town-map.png",
                }
            ],
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
            "sprite_retro": f"/media/pokemon/sprites/{slug}/shellos/east.png",
            "sprite_retro_shiny": f"/media/pokemon/sprites/{slug}_shiny/shellos/east.png",
            "sprite_retro_back": f"/media/pokemon/sprites/{slug}/back/shellos/east.png",
            "sprite_retro_shiny_back": f"/media/pokemon/sprites/{slug}_shiny/back/shellos/east.png",
            "sprite_modern": "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/10009.png",
            "sprite_modern_shiny": "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/shiny/10009.png",
            "summary": "Exclusivo de la vertiente oriental de Sinnoh (al este del Monte Corona).",
            "locations": [
                {"area": "Ruta 213", "method": "Salvaje (Hierba / Surfing)"},
                {"area": "Ruta 221", "method": "Salvaje (Hierba)"},
                {"area": "Ruta 222", "method": "Salvaje (Hierba / Surfing)"},
                {"area": "Ruta 224", "method": "Salvaje (Hierba / Surfing)"},
                {"area": "Orilla Valor", "method": "Salvaje (Hierba)"},
            ],
            "notes": [
                {
                    "title": "Variación Geográfica Sinnoh",
                    "text": "La cordillera del Monte Corona divide geográficamente las poblaciones de esta especie. La variante azul habita exclusivamente en la zona oriental de la región.",
                    "tag": "Geografía",
                    "icon": "/media/items/town-map.png",
                }
            ],
        }
    ]


def get_gastrodon_forms(game_slug: str = "diamond") -> List[Dict[str, Any]]:
    """
    Retorna las 2 formas geográficas de Gastrodon (#423) en Sinnoh:
    Mar Oeste (Rosa), Mar Este (Azul).
    Rutas de obtención exclusivas a ambos lados del Monte Corona.
    """
    slug = "diamond"
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
            "sprite_retro": f"/media/pokemon/sprites/{slug}/gastrodon/west.png",
            "sprite_retro_shiny": f"/media/pokemon/sprites/{slug}_shiny/gastrodon/west.png",
            "sprite_retro_back": f"/media/pokemon/sprites/{slug}/back/gastrodon/west.png",
            "sprite_retro_shiny_back": f"/media/pokemon/sprites/{slug}_shiny/back/gastrodon/west.png",
            "sprite_modern": "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/423.png",
            "sprite_modern_shiny": "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/shiny/423.png",
            "summary": "Exclusivo de la vertiente occidental de Sinnoh (al oeste del Monte Corona).",
            "locations": [
                {"area": "Ruta 205", "method": "Salvaje (Hierba)"},
                {"area": "Ruta 218", "method": "Salvaje (Surfing / Pesca)"},
                {"area": "Parque Eólico", "method": "Salvaje (Hierba)"},
                {"area": "Forja Fuego", "method": "Salvaje (Hierba / Surfing)"},
                {"area": "Canal de Pastoria", "method": "Salvaje (Surfing)"},
            ],
            "notes": [
                {
                    "title": "Variación Geográfica Sinnoh",
                    "text": "La cordillera del Monte Corona divide geográficamente las poblaciones de esta especie. La variante rosa habita exclusivamente en la zona occidental de la región.",
                    "tag": "Geografía",
                    "icon": "/media/items/town-map.png",
                }
            ],
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
            "sprite_retro": f"/media/pokemon/sprites/{slug}/gastrodon/east.png",
            "sprite_retro_shiny": f"/media/pokemon/sprites/{slug}_shiny/gastrodon/east.png",
            "sprite_retro_back": f"/media/pokemon/sprites/{slug}/back/gastrodon/east.png",
            "sprite_retro_shiny_back": f"/media/pokemon/sprites/{slug}_shiny/back/gastrodon/east.png",
            "sprite_modern": "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/10010.png",
            "sprite_modern_shiny": "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/shiny/10010.png",
            "summary": "Exclusivo de la vertiente oriental de Sinnoh (al este del Monte Corona).",
            "locations": [
                {"area": "Ruta 213", "method": "Salvaje (Hierba / Surfing)"},
                {"area": "Ruta 221", "method": "Salvaje (Hierba)"},
                {"area": "Ruta 222", "method": "Salvaje (Hierba / Surfing)"},
                {"area": "Ruta 224", "method": "Salvaje (Hierba / Surfing)"},
                {"area": "Ruta 230", "method": "Salvaje (Surfing)"},
            ],
            "notes": [
                {
                    "title": "Variación Geográfica Sinnoh",
                    "text": "La cordillera del Monte Corona divide geográficamente las poblaciones de esta especie. La variante azul habita exclusivamente en la zona oriental de la región.",
                    "tag": "Geografía",
                    "icon": "/media/items/town-map.png",
                }
            ],
        }
    ]


def get_arceus_forms(game_slug: str = "diamond") -> List[Dict[str, Any]]:
    """
    Retorna las 17 formas canónicas de Arceus (#493) en Generación 4:
    Forma Normal + 16 Tablas elementales repartidas por Sinnoh.
    (La Tabla Duende y el Tipo Hada quedan estrictamente excluidos por pertenecer a Gen 6).
    """
    slug = "diamond"
    plates_def = [
        ("normal", "Forma Normal", "Normal", "normal", "Normal", "", "", "Sin Tabla", "/media/items/rule-book.png", "Permanece en su Forma Normal cuando no lleva ninguna tabla elemental equipada."),
        ("fire", "Tabla Llama", "Fuego", "fire", "Fuego", "", "", "Tabla Llama", "/media/items/flame-plate.png", "Al equipar la Tabla Llama, su habilidad Multitipo cambia su tipo elemental a Fuego puro."),
        ("water", "Tabla Linfa", "Agua", "water", "Agua", "", "", "Tabla Linfa", "/media/items/splash-plate.png", "Al equipar la Tabla Linfa, su habilidad Multitipo cambia su tipo elemental a Agua puro."),
        ("grass", "Tabla Pradal", "Planta", "grass", "Planta", "", "", "Tabla Pradal", "/media/items/meadow-plate.png", "Al equipar la Tabla Pradal, su habilidad Multitipo cambia su tipo elemental a Planta puro."),
        ("electric", "Tabla Trueno", "Eléctrico", "electric", "Eléctrico", "", "", "Tabla Trueno", "/media/items/zap-plate.png", "Al equipar la Tabla Trueno, su habilidad Multitipo cambia su tipo elemental a Eléctrico puro."),
        ("ice", "Tabla Helada", "Hielo", "ice", "Hielo", "", "", "Tabla Helada", "/media/items/icicle-plate.png", "Al equipar la Tabla Helada, su habilidad Multitipo cambia su tipo elemental a Hielo puro."),
        ("fighting", "Tabla Fuerte", "Lucha", "fighting", "Lucha", "", "", "Tabla Fuerte", "/media/items/fist-plate.png", "Al equipar la Tabla Fuerte, su habilidad Multitipo cambia su tipo elemental a Lucha puro."),
        ("poison", "Tabla Tóxica", "Veneno", "poison", "Veneno", "", "", "Tabla Tóxica", "/media/items/toxic-plate.png", "Al equipar la Tabla Tóxica, su habilidad Multitipo cambia su tipo elemental a Veneno puro."),
        ("ground", "Tabla Terraja", "Tierra", "ground", "Tierra", "", "", "Tabla Terraja", "/media/items/earth-plate.png", "Al equipar la Tabla Terraja, su habilidad Multitipo cambia su tipo elemental a Tierra puro."),
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
            "sprite_retro": f"/media/pokemon/sprites/{slug}/arceus/{f_key}.png",
            "sprite_retro_shiny": f"/media/pokemon/sprites/{slug}_shiny/arceus/{f_key}.png",
            "sprite_retro_back": f"/media/pokemon/sprites/{slug}/back/arceus/{f_key}.png",
            "sprite_retro_shiny_back": f"/media/pokemon/sprites/{slug}_shiny/back/arceus/{f_key}.png",
            "sprite_modern": "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/493.png",
            "sprite_modern_shiny": "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/shiny/493.png",
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
        elif game_slug in ["diamond", "pearl", "platinum"]:
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
            "chamber_key": item.get("chamber_key", ""),
            "chamber_name": ch_name,
            "summary": summary,
            "locations": locations,
            "badge_color": badge_color,
            "badge_label": badge_label,
            "type": obt_type,
        })

    if clean_slug in ["firered", "leafgreen", "diamond", "pearl", "platinum"]:
        # En Rojo Fuego / Verde Hoja y Diamante / Perla / Platino, la forma canónica predeterminada en la Pokédex es la F
        forms = [f for f in forms if f["form_key"] == "f"] + [f for f in forms if f["form_key"] != "f"]

    return forms


def get_pokemon_forms(national_number: int, game_slug: str = "ruby") -> List[Dict[str, Any]]:
    """
    Punto de entrada unificado y escalable para obtener las formas alternas de un Pokémon.
    Retorna una lista vacía para especies sin formas alternativas en la edición activa.
    """
    clean_slug = (game_slug or "ruby").replace("_national", "")
    is_gen4 = clean_slug in ["diamond", "pearl", "platinum"]

    # 1. Unown (#201) disponible en Gen 2+
    if national_number == 201:
        return get_unown_forms(clean_slug)

    # 2. Castform (#351) disponible en Gen 3+
    elif national_number == 351:
        return get_castform_forms(clean_slug)

    # 3. Formas activas a partir de Gen 4 (Sinnoh)
    elif is_gen4:
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
        elif national_number == 493:
            return get_arceus_forms(clean_slug)

    return []
