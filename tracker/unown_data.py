"""
Metadatos oficiales y estructura de las Ruinas Alfa para la Unowndex en 2ª Generación.
"""

UNOWN_CHAMBERS = {
    "kabuto": {
        "key": "kabuto",
        "name": "Cámara de Kabuto",
        "access": "Entrada principal",
        "letters": ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k"],
        "secret_requirement": "Usar Cuerda Huida (Escape Rope) frente a la inscripción trasera.",
        "secret_rewards": ["Baya Meloc", "Baya Milagro", "Polvoenergía", "Raíz Energía"],
        "badge_class": "bg-amber-100 text-amber-900 border-amber-950",
    },
    "omanyte": {
        "key": "omanyte",
        "name": "Cámara de Omanyte",
        "access": "Noreste (Requiere Surf)",
        "letters": ["l", "m", "n", "o", "p", "q", "r"],
        "secret_requirement": "Usar Piedra Agua (Water Stone) frente a la inscripción trasera.",
        "secret_rewards": ["Polvoestelar", "Fragmento Estrella", "Agua Mística", "Baya Misterio"],
        "badge_class": "bg-sky-100 text-sky-900 border-sky-950",
    },
    "aerodactyl": {
        "key": "aerodactyl",
        "name": "Cámara de Aerodactyl",
        "access": "Suroeste (Vía Cueva Unión)",
        "letters": ["s", "t", "u", "v", "w"],
        "secret_requirement": "Usar Destello (Flash) frente a la inscripción trasera.",
        "secret_rewards": ["Polvoenergía", "Raíz Energía", "Polvocoraje", "Hierba Revivir"],
        "badge_class": "bg-violet-100 text-violet-900 border-violet-950",
    },
    "ho_oh": {
        "key": "ho_oh",
        "name": "Cámara de Ho-Oh",
        "access": "Noroeste (Cueva Unión con Surf + Fuerza)",
        "letters": ["x", "y", "z"],
        "secret_requirement": "Llevar a Ho-Oh en la 1.ª posición de tu equipo frente a la pared.",
        "secret_rewards": ["Baya Milagro", "Carbón", "Baya Misterio", "Ceniza Sagrada"],
        "badge_class": "bg-rose-100 text-rose-900 border-rose-950",
    }
}

GEN2_LEGIT_SHINY_LETTERS = {"i", "v"}


def get_unown_catalog():
    """
    Retorna la lista de las 26 formas de Unown con información de cámara,
    sprites locales de 56x56, iconos y particularidad shiny de Gen 2.
    """
    catalog = []
    chamber_by_letter = {}
    for ch_key, ch_data in UNOWN_CHAMBERS.items():
        for l in ch_data["letters"]:
            chamber_by_letter[l] = ch_data

    for code in range(ord('a'), ord('z') + 1):
        letter = chr(code)
        ch = chamber_by_letter.get(letter, UNOWN_CHAMBERS["kabuto"])
        catalog.append({
            "letter": letter,
            "display": f"Unown [{letter.upper()}]",
            "chamber": ch["key"],
            "chamber_key": ch["key"],
            "chamber_name": ch["name"],
            "chamber_badge_class": ch["badge_class"],
            "secret_hint": ch["secret_requirement"],
            "is_legit_shiny_gen2": letter in GEN2_LEGIT_SHINY_LETTERS,
            "sprite_normal": f"/media/pokemon/sprites/gold/unown/{letter}.png",
            "sprite_shiny": f"/media/pokemon/sprites/gold_shiny/unown/{letter}.png",
            "icon_url": f"/media/pokemon/icons/gen2/201-{letter}.png",
        })
    return catalog


UNOWN_LETTERS_DATA = {item["letter"]: item for item in get_unown_catalog()}

