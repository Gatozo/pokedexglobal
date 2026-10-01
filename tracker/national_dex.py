"""
Módulo centralizado para la gestión de navegación por regiones/generaciones
en el modo Pokédex Nacional (Gen 3 a Gen 9 y Desconocido).
"""
from typing import Dict, List, Optional, Any, Tuple

NATIONAL_REGIONS_CATALOG: List[Dict[str, Any]] = [
    {
        "slug": "kanto",
        "name": "Kanto",
        "generation": 1,
        "range": (1, 151),
    },
    {
        "slug": "johto",
        "name": "Johto",
        "generation": 2,
        "range": (152, 251),
    },
    {
        "slug": "hoenn",
        "name": "Hoenn",
        "generation": 3,
        "range": (252, 386),
    },
    {
        "slug": "sinnoh",
        "name": "Sinnoh",
        "generation": 4,
        "range": (387, 493),
    },
    {
        "slug": "unova",
        "name": "Teselia",
        "generation": 5,
        "range": (494, 649),
    },
    {
        "slug": "kalos",
        "name": "Kalos",
        "generation": 6,
        "range": (650, 721),
    },
    {
        "slug": "alola",
        "name": "Alola",
        "generation": 7,
        "range": (722, 807),
    },
    {
        "slug": "unknown",
        "name": "Desconocido",
        "generation": 7.5,
        "range": (808, 809),  # Meltan y Melmetal
    },
    {
        "slug": "galar_hisui",
        "name": "Galar / Hisui",
        "generation": 8,
        "range": (810, 905),
    },
    {
        "slug": "paldea",
        "name": "Paldea",
        "generation": 9,
        "range": (906, 1025),
    },
]


def get_national_regions_context(
    game,
    pokedex,
    entries_by_num: Dict[int, Any],
    caught_entry_ids: set,
    shiny_caught_entry_ids: set,
    requested_slug: Optional[str] = None,
    is_shinydex: bool = False,
) -> Optional[Dict[str, Any]]:
    """
    Computa el contexto de regiones para la barra de Pokédex Nacional.
    Regla estricta:
    - Únicamente activa para Pokédex Nacional en juegos de Generación >= 3.
    - Gen 1 (sin Pokédex Nacional) y Gen 2 (los 251 se presentan sin partición) retornan None.
    - La región por defecto es siempre 'kanto'.
    """
    is_national = bool(getattr(pokedex, "is_national", False) or pokedex.slug == "national")
    if not is_national or game.generation < 3:
        return None

    # Determinar el número máximo nacional presente en este juego
    max_nat = max(entries_by_num.keys()) if entries_by_num else 0
    if max_nat == 0:
        return None

    # Filtrar solo las regiones que correspondan a especies presentes en este juego
    available_regions = []
    for reg in NATIONAL_REGIONS_CATALOG:
        start_id, end_id = reg["range"]
        # Incluir si el rango de la región se superpone con los Pokémon del cartucho
        if start_id <= max_nat:
            available_regions.append(reg)

    if not available_regions:
        return None

    valid_slugs = {r["slug"] for r in available_regions}

    # Resolver región activa: solicitada -> por defecto 'kanto'
    active_slug = requested_slug if (requested_slug and requested_slug in valid_slugs) else "kanto"
    if active_slug not in valid_slugs:
        active_slug = available_regions[0]["slug"]

    regions_data = []
    active_region_meta = None

    for reg in available_regions:
        start_id, end_id = reg["range"]
        reg_entries = [e for num, e in entries_by_num.items() if start_id <= num <= end_id]
        total_in_reg = len(reg_entries)
        
        # Conteo de capturas
        caught_count = sum(1 for e in reg_entries if e.id in caught_entry_ids)
        shiny_caught_count = sum(1 for e in reg_entries if e.id in shiny_caught_entry_ids)
        display_caught = shiny_caught_count if is_shinydex else caught_count

        is_active = (reg["slug"] == active_slug)
        reg_item = {
            "slug": reg["slug"],
            "name": reg["name"],
            "generation": reg["generation"],
            "start_id": start_id,
            "end_id": end_id,
            "total": total_in_reg,
            "caught": caught_count,
            "shiny_caught": shiny_caught_count,
            "display_caught": display_caught,
            "is_active": is_active,
            "url": f"?gen={reg['slug']}",
        }
        regions_data.append(reg_item)
        if is_active:
            active_region_meta = reg_item

    return {
        "regions": regions_data,
        "active_slug": active_slug,
        "active_region": active_region_meta,
        "active_range": (active_region_meta["start_id"], active_region_meta["end_id"]) if active_region_meta else None,
    }
