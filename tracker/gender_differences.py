"""
Registro canónico de diferencias de género y sprites de 4ª Generación (Gen 4+).
Define qué especies presentan diferencias visuales entre macho y hembra,
cuáles son exclusivamente macho o hembra, cuáles carecen de género,
y genera las rutas relativas de sprites femeninos descargados.
"""

from typing import Dict, Any, Optional

# Especies de Gen 1-4 que carecen de género (genderless / género desconocido)
GENDERLESS_SPECIES = {
    81, 82, 100, 101, 120, 121, 132, 137, 144, 145, 146, 150, 151,
    201, 233, 243, 244, 245, 249, 250, 251, 292, 337, 338, 343, 344,
    374, 375, 376, 377, 378, 379, 382, 383, 384, 385, 386, 436, 437,
    462, 474, 479, 480, 481, 482, 483, 484, 486, 487, 489, 490, 491,
    492, 493
}

# Especies exclusivamente hembra (100% hembra)
FEMALE_ONLY_SPECIES = {
    29, 30, 31, 113, 115, 124, 238, 241, 242, 314, 380, 413, 416, 440, 478, 488
}

# Especies exclusivamente macho (100% macho)
MALE_ONLY_SPECIES = {
    32, 33, 34, 106, 107, 128, 236, 237, 313, 381, 414, 475
}

# Las 94 especies canónicas de 4ª Generación con diferencias visuales físicas entre macho y hembra
GENDER_DIFFERENCES_GEN4: Dict[int, str] = {
    3: "La flor del lomo de la hembra tiene una semilla en el centro.",
    12: "Las alas inferiores de la hembra tienen manchas oscuras.",
    19: "Los bigotes de la hembra son más cortos que los del macho.",
    20: "Los bigotes de la hembra son más cortos que los del macho.",
    25: "La hembra tiene la punta de la cola en forma de corazón.",
    26: "La punta de la cola de la hembra es más corta y roma.",
    41: "Los colmillos de la hembra son más pequeños.",
    42: "Los colmillos de la hembra son más pequeños.",
    44: "La hembra tiene un único punto grande en cada pétalo en vez de varios pequeños.",
    45: "Las manchas blancas de los pétalos de la hembra son más grandes.",
    64: "El bigote de la hembra es notablemente más corto.",
    65: "El bigote de la hembra es notablemente más corto.",
    84: "El macho tiene el cuello negro; la hembra tiene el cuello beige claro.",
    85: "El macho tiene los cuellos negros; la hembra tiene los cuellos beige claro.",
    97: "El collar de pelo blanco de la hembra es más frondoso y largo.",
    118: "El cuerno de la hembra es más pequeño.",
    119: "El cuerno de la hembra es más pequeño.",
    123: "El abdomen de la hembra es más grande.",
    129: "El macho tiene los bigotes amarillos; la hembra tiene los bigotes blancos.",
    130: "El macho tiene los bigotes azules; la hembra tiene los bigotes blancos.",
    154: "Las antenas de la hembra son más cortas.",
    165: "Las antenas de la hembra son más cortas.",
    166: "Las antenas de la hembra son más cortas.",
    178: "El macho tiene tres rayas amarillas en el pecho; la hembra tiene dos.",
    185: "La rama de la cabeza de la hembra es más pequeña.",
    186: "Las manchas rosas de las mejillas son más pequeñas en la hembra.",
    190: "El mechón de pelo de la cabeza de la hembra es más largo.",
    194: "Las branquias de la hembra tienen una sola punta en lugar de dos.",
    195: "La aleta dorsal de la hembra es más pequeña.",
    198: "Las plumas de la cabeza de la hembra son más cortas.",
    202: "La hembra tiene los labios pintados de carmín rojo.",
    203: "La sección trasera marrón oscuro del cuerpo es más corta en la hembra.",
    207: "El aguijón de la cola de la hembra es más pequeño.",
    208: "El macho tiene un colmillo/cresta adicional en la mandíbula inferior.",
    212: "El abdomen de la hembra es más grande.",
    214: "El cuerno de la hembra termina en forma de corazón; el del macho en cruz.",
    215: "La pluma roja de la oreja de la hembra es más corta.",
    217: "El pelaje de los hombros de la hembra es más largo.",
    221: "Los colmillos de la hembra son más cortos.",
    224: "Las ventosas de los tentáculos de la hembra son más pequeñas.",
    229: "Los cuernos de la hembra son más cortos.",
    232: "Los colmillos de la hembra son más cortos.",
    255: "El macho tiene una diminuta mancha negra en la parte trasera del cuerpo.",
    256: "Las plumas de la cabeza y garras son más cortas en la hembra.",
    257: "Las plumas traseras de la cabeza son más cortas en la hembra.",
    267: "Las manchas rojas de las alas superiores son más pequeñas en la hembra.",
    269: "Las antenas de la hembra son más cortas.",
    272: "Las rayas marrones del poncho de la hembra son más estrechas.",
    274: "La hoja de la cabeza de la hembra es más pequeña.",
    275: "Las hojas de las manos de la hembra son más pequeñas.",
    277: "Las dos plumas de la cola son más cortas en la hembra.",
    278: "Las dos plumas de la cola son más cortas en la hembra.",
    307: "Las orejas de la hembra están situadas más abajo.",
    308: "El moño de pelo de la cabeza de la hembra es más pequeño.",
    315: "La hoja que cubre el torso es más larga en la hembra.",
    316: "La pluma amarilla de la cabeza de la hembra es más corta.",
    317: "Los bigotes de la hembra son más cortos.",
    322: "La joroba del lomo de la hembra es más pequeña.",
    323: "Las dos jorobas del lomo de la hembra son más pequeñas.",
    332: "El rombo amarillo del pecho de la hembra es más grande.",
    350: "Los filamentos de las antenas son más largos en la hembra.",
    369: "Los bigotes de la mandíbula inferior de la hembra son más cortos.",
    396: "La mancha blanca de la frente de la hembra es más pequeña.",
    397: "La mancha blanca de la frente de la hembra es más pequeña.",
    398: "La mancha blanca de la cresta de la hembra es más pequeña.",
    399: "La cola de la hembra tiene menos curvas/lóbulos.",
    400: "La máscara beige de la cara de la hembra tiene menos curvas.",
    401: "El collar rojo del cuello tiene una raya más fina en la hembra.",
    402: "El bigote de la hembra es notablemente más corto.",
    403: "El mechón de la cabeza es más corto en la hembra y sus patas traseras son azules.",
    404: "La melena de la hembra es más corta y sus patas traseras son azules.",
    405: "La melena de la hembra es más corta.",
    407: "La capa de hojas del torso es más larga en la hembra.",
    415: "La hembra tiene una marca roja en la frente y es la única que puede evolucionar a Vespiquen.",
    417: "La franja azul de la cabeza de la hembra es más corta.",
    418: "El macho tiene dos manchas en la espalda; la hembra tiene solo una.",
    419: "El macho tiene dos manchas en la espalda; la hembra tiene solo una.",
    424: "Los mechones de pelo de la cabeza de la hembra son más largos.",
    443: "El macho tiene una muesca en su aleta dorsal; la hembra no.",
    444: "El macho tiene una muesca en su aleta dorsal; la hembra no.",
    445: "El macho tiene una muesca en su aleta dorsal; la hembra no.",
    449: "El macho es de color arena claro; la hembra es de color marrón oscuro / negro.",
    450: "El macho es de color amarillo arena; la hembra es de color gris oscuro / negro.",
    453: "La raya blanca del pecho de la hembra está situada más arriba.",
    454: "El saco vocal de la garganta de la hembra es más pequeño.",
    456: "Las dos aletas de la cola son más grandes en la hembra.",
    457: "Las aletas pectorales inferiores son más grandes en la hembra.",
    459: "El torso medio es blanco en el macho y marrón en la hembra.",
    460: "El pelaje blanco del pecho de la hembra es más largo.",
    461: "Las plumas rojas de las orejas de la hembra son más cortas.",
    464: "El cuerno superior de la hembra es más pequeño.",
    465: "Las puntas rojas de los dedos son más cortas en la hembra.",
    473: "Los colmillos de hielo de la hembra son más pequeños.",
}


def get_pokemon_gender_info(national_number: int, game_slug: str) -> Optional[Dict[str, Any]]:
    """
    Retorna la configuración de género para el Pokémon especificado en el contexto de 4ª Generación en adelante.
    Si el juego es anterior a 4ª generación, retorna None.
    Si la especie no tiene género, retorna estructura con can_toggle=False.
    Si tiene diferencias visuales, incluye las URLs de los sprites femeninos oficiales descargados.
    """
    from .catalog_service import get_game_generation
    if get_game_generation(game_slug) < 4:
        return None

    if national_number in GENDERLESS_SPECIES:
        return {
            "gender_type": "genderless",
            "can_toggle": False,
            "default_gender": "none",
            "has_visual_differences": False,
            "female_sprite_available": False,
            "difference_note": None,
            "female_sprites": None,
        }

    if national_number in FEMALE_ONLY_SPECIES:
        return {
            "gender_type": "female_only",
            "can_toggle": False,
            "default_gender": "female",
            "has_visual_differences": False,
            "female_sprite_available": False,
            "difference_note": "Especie exclusivamente hembra.",
            "female_sprites": None,
        }

    if national_number in MALE_ONLY_SPECIES:
        return {
            "gender_type": "male_only",
            "can_toggle": False,
            "default_gender": "male",
            "has_visual_differences": False,
            "female_sprite_available": False,
            "difference_note": "Especie exclusivamente macho.",
            "female_sprites": None,
        }

    has_diff = national_number in GENDER_DIFFERENCES_GEN4
    diff_note = GENDER_DIFFERENCES_GEN4.get(national_number)

    # Determinar si existen sprites descargados
    base_slug = game_slug if game_slug in ["diamond", "pearl", "platinum", "heartgold", "soulsilver"] else "diamond"
    female_sprites = None
    if has_diff:
        female_sprites = {
            "retro": f"/media/pokemon/sprites/{base_slug}/female/{national_number}.png",
            "retro_back": f"/media/pokemon/sprites/{base_slug}/back/female/{national_number}.png",
            "retro_shiny": f"/media/pokemon/sprites/{base_slug}_shiny/female/{national_number}.png",
            "retro_shiny_back": f"/media/pokemon/sprites/{base_slug}_shiny/back/female/{national_number}.png",
            "modern": f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/female/{national_number}.png",
            "modern_shiny": f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/shiny/female/{national_number}.png",
        }

    return {
        "gender_type": "both_with_diff" if has_diff else "both_no_diff",
        "can_toggle": True,
        "default_gender": "male",
        "has_visual_differences": has_diff,
        "female_sprite_available": female_sprites is not None,
        "difference_note": diff_note or "Sin cambios visuales entre géneros",
        "female_sprites": female_sprites,
    }
