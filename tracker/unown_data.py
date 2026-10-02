"""
Metadatos oficiales y estructura de las cámaras de Unown para Johto (Ruinas Alfa) y Archi7 (Ruinas Sete).
"""

JOHTO_UNOWN_CHAMBERS = {
    "kabuto": {
        "key": "kabuto",
        "name": "Cámara de Kabuto (Ruinas Alfa)",
        "chamber_title": "Kabuto",
        "access": "Entrada principal",
        "letters": ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k"],
        "secret_requirement": "Usar Cuerda Huida (Escape Rope) frente a la inscripción trasera.",
        "secret_rewards": ["Baya Meloc", "Baya Milagro", "Polvoenergía", "Raíz Energía"],
        "badge_class": "bg-amber-100 text-amber-900 border-amber-950",
    },
    "omanyte": {
        "key": "omanyte",
        "name": "Cámara de Omanyte (Ruinas Alfa)",
        "chamber_title": "Omanyte",
        "access": "Noreste (Requiere Surf)",
        "letters": ["l", "m", "n", "o", "p", "q", "r"],
        "secret_requirement": "Usar Piedra Agua (Water Stone) frente a la inscripción trasera.",
        "secret_rewards": ["Polvoestelar", "Fragmento Estrella", "Agua Mística", "Baya Misterio"],
        "badge_class": "bg-sky-100 text-sky-900 border-sky-950",
    },
    "aerodactyl": {
        "key": "aerodactyl",
        "name": "Cámara de Aerodactyl (Ruinas Alfa)",
        "chamber_title": "Aerodactyl",
        "access": "Suroeste (Vía Cueva Unión)",
        "letters": ["s", "t", "u", "v", "w"],
        "secret_requirement": "Usar Destello (Flash) frente a la inscripción trasera.",
        "secret_rewards": ["Polvoenergía", "Raíz Energía", "Polvocoraje", "Hierba Revivir"],
        "badge_class": "bg-violet-100 text-violet-900 border-violet-950",
    },
    "ho_oh": {
        "key": "ho_oh",
        "name": "Cámara de Ho-Oh (Ruinas Alfa)",
        "chamber_title": "Ho-Oh",
        "access": "Noroeste (Cueva Unión con Surf + Fuerza)",
        "letters": ["x", "y", "z"],
        "secret_requirement": "Llevar a Ho-Oh en la 1.ª posición de tu equipo frente a la pared.",
        "secret_rewards": ["Baya Milagro", "Carbón", "Baya Misterio", "Ceniza Sagrada"],
        "badge_class": "bg-rose-100 text-rose-900 border-rose-950",
    }
}

TANOBY_UNOWN_CHAMBERS = {
    "anemuna": {
        "key": "anemuna",
        "name": "Cámara Anémuna (Ruinas Sete)",
        "chamber_title": "Anémuna",
        "access": "Islote 1 (Sureste de Isla Sétima)",
        "letters": ["a", "question"],
        "secret_requirement": "Resolver el acertijo de la Llave Sete con Fuerza en Cañón Sétano para desbloquear las cámaras.",
        "badge_class": "bg-amber-100 text-amber-900 border-amber-950",
        "rates": {"a": "99%", "question": "1%"},
    },
    "tulipdos": {
        "key": "tulipdos",
        "name": "Cámara Tulipdos (Ruinas Sete)",
        "chamber_title": "Tulipdos",
        "access": "Islote 2 (Al sur de Isla Sétima)",
        "letters": ["c", "d", "h", "u", "o"],
        "secret_requirement": "Resolver el acertijo de la Llave Sete con Fuerza en Cañón Sétano para desbloquear las cámaras.",
        "badge_class": "bg-emerald-100 text-emerald-900 border-emerald-950",
        "rates": {"c": "50%", "d": "30%", "h": "14%", "u": "5%", "o": "1%"},
    },
    "trisante": {
        "key": "trisante",
        "name": "Cámara Trisante (Ruinas Sete)",
        "chamber_title": "Trisante",
        "access": "Islote 3 (Al sur de Isla Sétima)",
        "letters": ["n", "s", "i", "e"],
        "secret_requirement": "Resolver el acertijo de la Llave Sete con Fuerza en Cañón Sétano para desbloquear las cámaras.",
        "badge_class": "bg-sky-100 text-sky-900 border-sky-950",
        "rates": {"n": "60%", "s": "30%", "i": "8%", "e": "2%"},
    },
    "quarciso": {
        "key": "quarciso",
        "name": "Cámara Quarciso (Ruinas Sete)",
        "chamber_title": "Quarciso",
        "access": "Islote 4 (Al sur de Isla Sétima)",
        "letters": ["p", "j", "l", "r", "q"],
        "secret_requirement": "Resolver el acertijo de la Llave Sete con Fuerza en Cañón Sétano para desbloquear las cámaras.",
        "badge_class": "bg-purple-100 text-purple-900 border-purple-950",
        "rates": {"p": "40%", "j": "20%", "l": "20%", "r": "14%", "q": "6%"},
    },
    "hibinca": {
        "key": "hibinca",
        "name": "Cámara Hibinca (Ruinas Sete)",
        "chamber_title": "Hibinca",
        "access": "Islote 5 (Al sur de Isla Sétima)",
        "letters": ["y", "g", "t", "f", "k"],
        "secret_requirement": "Resolver el acertijo de la Llave Sete con Fuerza en Cañón Sétano para desbloquear las cámaras.",
        "badge_class": "bg-rose-100 text-rose-900 border-rose-950",
        "rates": {"y": "40%", "g": "25%", "t": "20%", "f": "13%", "k": "2%"},
    },
    "seiris": {
        "key": "seiris",
        "name": "Cámara Seiris (Ruinas Sete)",
        "chamber_title": "Seiris",
        "access": "Islote 6 (Al sur de Isla Sétima)",
        "letters": ["v", "w", "x", "m", "b"],
        "secret_requirement": "Resolver el acertijo de la Llave Sete con Fuerza en Cañón Sétano para desbloquear las cámaras.",
        "badge_class": "bg-indigo-100 text-indigo-900 border-indigo-950",
        "rates": {"v": "50%", "w": "30%", "x": "10%", "m": "8%", "b": "2%"},
    },
    "pasiete": {
        "key": "pasiete",
        "name": "Cámara Pasiete (Ruinas Sete)",
        "chamber_title": "Pasiete",
        "access": "Islote 7 (Al norte de Seiris)",
        "letters": ["z", "exclamation"],
        "secret_requirement": "Resolver el acertijo de la Llave Sete con Fuerza en Cañón Sétano para desbloquear las cámaras.",
        "badge_class": "bg-teal-100 text-teal-900 border-teal-950",
        "rates": {"z": "99%", "exclamation": "1%"},
    },
}

# Alias retrocompatible
UNOWN_CHAMBERS = JOHTO_UNOWN_CHAMBERS

GEN2_LEGIT_SHINY_LETTERS = {"i", "v"}


def get_game_unown_chambers(game_slug: str = "gold"):
    """Retorna el diccionario de cámaras correspondiente al juego actual."""
    if game_slug in ["firered", "leafgreen"]:
        return TANOBY_UNOWN_CHAMBERS
    if game_slug in ["ruby", "sapphire", "emerald"]:
        return {}
    return JOHTO_UNOWN_CHAMBERS


def get_unown_catalog(game_slug: str = "gold"):
    """
    Retorna la lista de las 26 formas de Unown (Gen 2) o 28 formas (Gen 3+) con información de cámara,
    sprites locales de 56x56, iconos y particularidad shiny de Gen 2.
    """
    is_tanoby = game_slug in ["firered", "leafgreen"]
    is_hoenn = game_slug in ["ruby", "sapphire", "emerald"]
    is_gen3_plus = game_slug in ["ruby", "sapphire", "emerald", "firered", "leafgreen"]
    slug = game_slug if game_slug in ["gold", "silver", "crystal", "ruby", "sapphire", "emerald", "firered", "leafgreen"] else "gold"
    sprite_slug = slug
    if is_gen3_plus and slug not in ["ruby"]:
        sprite_slug = "ruby"

    chambers = TANOBY_UNOWN_CHAMBERS if is_tanoby else ({} if is_hoenn else JOHTO_UNOWN_CHAMBERS)

    catalog = []
    chamber_by_letter = {}
    for ch_key, ch_data in chambers.items():
        for l in ch_data["letters"]:
            chamber_by_letter[l] = ch_data

    letters = [chr(code) for code in range(ord('a'), ord('z') + 1)]
    if is_gen3_plus:
        letters.extend(["exclamation", "question"])

    fallback_chamber = list(chambers.values())[0] if chambers else None

    for letter in letters:
        ch = chamber_by_letter.get(letter, fallback_chamber)
        if letter == "exclamation":
            display = "Unown [!]"
        elif letter == "question":
            display = "Unown [?]"
        else:
            display = f"Unown [{letter.upper()}]"

        if is_hoenn:
            chamber_key = ""
            chamber_title = ""
            chamber_name = "No disponible en Hoenn"
            chamber_badge = "hidden"
            hint = "No aparece en estado salvaje en Hoenn. Se obtiene mediante transferencia externa."
            rate_val = ""
        else:
            chamber_key = ch["key"] if ch else ""
            chamber_title = ch.get("chamber_title", ch["name"]) if ch else ""
            chamber_name = ch["name"] if ch else ""
            chamber_badge = ch["badge_class"] if ch else ""
            hint = ch["secret_requirement"] if ch else ""
            rate_val = ch.get("rates", {}).get(letter, "") if ch else ""

        icon_gen = "gen3" if is_gen3_plus else "gen2"

        catalog.append({
            "letter": letter,
            "display": display,
            "chamber": chamber_key,
            "chamber_key": chamber_key,
            "chamber_title": chamber_title,
            "chamber_name": chamber_name,
            "chamber_badge_class": chamber_badge,
            "secret_hint": hint,
            "is_legit_shiny_gen2": letter in GEN2_LEGIT_SHINY_LETTERS,
            "sprite_normal": f"/media/pokemon/sprites/{sprite_slug}/unown/{letter}.png",
            "sprite_shiny": f"/media/pokemon/sprites/{sprite_slug}_shiny/unown/{letter}.png",
            "sprite_normal_back": f"/media/pokemon/sprites/{sprite_slug}/back/unown/{letter}.png",
            "sprite_shiny_back": f"/media/pokemon/sprites/{sprite_slug}_shiny/back/unown/{letter}.png",
            "icon_url": f"/media/pokemon/icons/{icon_gen}/201-{letter}.png",
            "rate": rate_val,
        })
    return catalog


UNOWN_LETTERS_DATA = {item["letter"]: item for item in get_unown_catalog()}


