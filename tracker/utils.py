import os
import re
import json
import time
import random
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
import requests

DEFAULT_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36'
}


def safe_api_get(
    url: str,
    session: Optional[requests.Session] = None,
    headers: Optional[Dict[str, str]] = None,
    max_retries: int = 3,
    base_delay: float = 1.0,
    timeout: float = 12.0,
    pacing_delay: float = 0.05
) -> Optional[requests.Response]:
    """
    Realiza una petición GET HTTP segura con protección contra bloqueos por IP:
    - Retardo de cortesía voluntario (pacing_delay).
    - Soporte de cabecera 'Retry-After' ante respuestas HTTP 429.
    - Backoff exponencial con jitter aleatorio para evitar efecto avalancha.
    - Manejo de timeouts y excepciones de conexión.
    """
    req_headers = {**DEFAULT_HEADERS, **(headers or {})}
    client = session or requests

    if pacing_delay > 0:
        time.sleep(pacing_delay)

    for attempt in range(max_retries):
        try:
            response = client.get(url, headers=req_headers, timeout=timeout)
            if response.status_code == 200:
                return response
            elif response.status_code == 429:
                # El servidor indica Rate Limiting
                retry_after = response.headers.get("Retry-After")
                if retry_after:
                    try:
                        sleep_seconds = float(retry_after) + 0.5
                    except ValueError:
                        sleep_seconds = base_delay * (2 ** attempt) + random.uniform(0.1, 0.5)
                else:
                    sleep_seconds = base_delay * (2 ** attempt) + random.uniform(0.1, 0.5)
                time.sleep(sleep_seconds)
            elif 500 <= response.status_code < 600:
                # Error de servidor temporal de PokeAPI / Cloudflare
                sleep_seconds = base_delay * (2 ** attempt) + random.uniform(0.1, 0.5)
                time.sleep(sleep_seconds)
            else:
                # 404 u otros códigos de cliente no se resuelven reintentando
                return response
        except (requests.RequestException, Exception):
            sleep_seconds = base_delay * (2 ** attempt) + random.uniform(0.1, 0.4)
            time.sleep(sleep_seconds)

    return None


def get_localized_text(
    entries: Optional[List[Dict[str, Any]]],
    text_key: str = "name",
    primary_lang: str = "es",
    fallback_lang: str = "en",
    default: str = ""
) -> str:
    """
    Extrae el texto de una lista de entradas localizadas de PokeAPI aplicando el patrón de cascada:
    1. Busca la traducción en el idioma primario (por defecto español 'es').
    2. Si no existe o está vacía, busca en el idioma de respaldo (por defecto inglés 'en').
    3. Si tampoco existe, devuelve el valor por defecto provisto.
    """
    if not entries:
        return default

    fallback_val = None

    for entry in entries:
        if not isinstance(entry, dict):
            continue
        lang_info = entry.get("language")
        lang_name = lang_info.get("name") if isinstance(lang_info, dict) else lang_info
        text_val = entry.get(text_key, "")

        if lang_name == primary_lang and text_val:
            return text_val
        elif lang_name == fallback_lang and text_val and fallback_val is None:
            fallback_val = text_val

    if fallback_val is not None:
        return fallback_val

    return default


def resolve_game_display_name(
    game_slug: str,
    custom_name: str = "",
    version_names_data: Optional[List[Dict[str, Any]]] = None,
    game_translations_map: Optional[Dict[str, str]] = None
) -> str:
    """
    Resuelve el nombre de un juego con la cascada de fallback idiomático:
    1. Si game_slug está en el diccionario oficial español, usa ese nombre (ej. 'Pokémon Rojo').
    2. Si custom_name está definido y no es vacío, usa custom_name.
    3. Si se provee version_names_data de PokeAPI, usa get_localized_text buscando 'es', luego 'en'.
    4. Fallback final: 'Pokémon ' + slug formateado.
    """
    if game_translations_map and game_slug in game_translations_map:
        return game_translations_map[game_slug]

    if custom_name and custom_name.strip():
        return custom_name.strip()

    if version_names_data:
        localized_name = get_localized_text(
            version_names_data,
            text_key="name",
            primary_lang="es",
            fallback_lang="en",
            default=""
        )
        if localized_name:
            if not localized_name.lower().startswith("pokémon") and not localized_name.lower().startswith("pokemon"):
                return f"Pokémon {localized_name}"
            return localized_name

    clean_slug = game_slug.replace("-", " ").title()
    return f"Pokémon {clean_slug}"


GENERATION_ROMAN_TO_INT = {
    'generation-i': 1,
    'generation-ii': 2,
    'generation-iii': 3,
    'generation-iv': 4,
    'generation-v': 5,
    'generation-vi': 6,
    'generation-vii': 7,
    'generation-viii': 8,
    'generation-ix': 9,
}


def resolve_types_for_generation(
    raw_data: Optional[Dict[str, Any]],
    fallback_primary: str,
    fallback_secondary: Optional[str],
    generation: int
) -> tuple[str, Optional[str]]:
    """
    Determina los tipos primario y secundario correspondientes a una generación de juego específica.
    Utiliza el campo 'past_types' de PokeAPI. Si la generación del juego es anterior o igual
    a la generación indicada en 'past_types', retorna la tipología histórica de esa época.
    De lo contrario, retorna la tipología moderna (fallback).
    """
    if not raw_data:
        return fallback_primary, fallback_secondary

    past_types = raw_data.get('past_types', [])
    if not past_types:
        return fallback_primary, fallback_secondary

    # Parsear cada entrada histórica con su número entero de generación
    parsed_past = []
    for entry in past_types:
        gen_info = entry.get('generation', {})
        gen_str = gen_info.get('name', '') if isinstance(gen_info, dict) else str(gen_info)
        gen_num = GENERATION_ROMAN_TO_INT.get(gen_str)
        if gen_num is not None:
            types_list = entry.get('types', [])
            # PokeAPI organiza types con slot o lista de objetos
            type_names = [
                t['type']['name'] for t in types_list
                if isinstance(t, dict) and 'type' in t and 'name' in t['type']
            ]
            if type_names:
                parsed_past.append((gen_num, type_names))

    if not parsed_past:
        return fallback_primary, fallback_secondary

    # Ordenar por generación ascendente
    parsed_past.sort(key=lambda x: x[0])

    # En PokeAPI, un past_type indica la tipología vigente HASTA esa generación (inclusive)
    for past_gen, type_names in parsed_past:
        if generation <= past_gen:
            p_type = type_names[0]
            s_type = type_names[1] if len(type_names) > 1 else None
            return p_type, s_type

    return fallback_primary, fallback_secondary


ITEMS_DATA_PATH = Path(__file__).resolve().parent / "data" / "items.json"
_ITEMS_CACHE: Optional[Dict[str, Any]] = None

EVOLUTION_STONES_PATH = Path(__file__).resolve().parent / "data" / "evolution_stones.json"
_STONES_CACHE: Optional[Dict[str, Any]] = None


def get_evolution_stones_catalog() -> Dict[str, Any]:
    """Carga y cachea en memoria el catálogo canónico de piedras evolutivas si existe."""
    global _STONES_CACHE
    if _STONES_CACHE is None:
        if EVOLUTION_STONES_PATH.exists():
            try:
                with open(EVOLUTION_STONES_PATH, "r", encoding="utf-8") as f:
                    _STONES_CACHE = json.load(f)
            except Exception:
                _STONES_CACHE = {}
        else:
            _STONES_CACHE = {}
    return _STONES_CACHE


def get_items_catalog() -> Dict[str, Any]:
    """Carga y cachea en memoria el catálogo canónico de objetos (items.json) si existe."""
    global _ITEMS_CACHE
    if _ITEMS_CACHE is None:
        if ITEMS_DATA_PATH.exists():
            try:
                with open(ITEMS_DATA_PATH, "r", encoding="utf-8") as f:
                    _ITEMS_CACHE = json.load(f)
            except Exception:
                _ITEMS_CACHE = {"meta": {}, "items": {}, "by_id": {}}
        else:
            _ITEMS_CACHE = {"meta": {}, "items": {}, "by_id": {}}
    return _ITEMS_CACHE


def get_item(slug_or_id: Union[str, int]) -> Optional[Dict[str, Any]]:
    """Obtiene la información estructurada de un objeto por slug o por ID numérico."""
    catalog = get_items_catalog()
    items = catalog.get("items", {})

    if isinstance(slug_or_id, int) or (isinstance(slug_or_id, str) and slug_or_id.isdigit()):
        slug = catalog.get("by_id", {}).get(str(slug_or_id))
        return items.get(slug) if slug else None

    return items.get(str(slug_or_id).lower())


FLAVOR_TEXTS_DIR = Path(__file__).resolve().parent / "data" / "flavor_texts"
_FLAVOR_CACHE: Dict[str, Dict[str, Any]] = {}

def get_cached_flavor_texts(game_slug: str) -> Dict[str, Any]:
    """Carga y cachea en memoria los textos oficiales en español del archivo local si existe."""
    if game_slug not in _FLAVOR_CACHE:
        file_path = FLAVOR_TEXTS_DIR / f"{game_slug}_es.json"
        if file_path.exists():
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    _FLAVOR_CACHE[game_slug] = json.load(f)
            except Exception:
                _FLAVOR_CACHE[game_slug] = {}
        else:
            _FLAVOR_CACHE[game_slug] = {}
    return _FLAVOR_CACHE[game_slug]


def resolve_flavor_text(
    national_number: int,
    game_slug: str,
    species_data: Optional[Dict[str, Any]] = None
) -> str:
    """
    Resuelve la descripción de la Pokédex oficial en español:
    1. Si existe archivo de datos curado oficial (ej: red_es.json), retorna esa descripción canónica.
    2. Si no, busca en species_data['flavor_text_entries'] para version == game_slug y language == 'es'.
    3. Si no hay 'es' para ese juego pero sí para remakes o ediciones afines (lets-go, x, etc.), usa esa versión oficial en español.
    4. Fallback final: texto oficial en inglés ('en') para version == game_slug.
    """
    cached = get_cached_flavor_texts(game_slug)
    entry = cached.get(str(national_number))
    if entry and entry.get("flavor_text_es"):
        return entry["flavor_text_es"].strip()

    if not species_data:
        return ""

    flavor_entries = species_data.get("flavor_text_entries", [])

    # 2. Español en la versión exacta
    for fe in flavor_entries:
        if fe.get("language", {}).get("name") == "es" and fe.get("version", {}).get("name") == game_slug:
            txt = fe.get("flavor_text", "").replace("\n", " ").replace("\x0c", " ")
            return " ".join(txt.split()).strip()

    # 3. Español en versiones afines/canónicas según la edición
    if game_slug == 'silver':
        related_versions = ["silver", "soulsilver", "y", "alpha-sapphire", "shield", "lets-go-eevee"]
    elif game_slug == 'gold':
        related_versions = ["gold", "heartgold", "x", "omega-ruby", "sword", "lets-go-pikachu"]
    elif game_slug == 'crystal':
        related_versions = ["crystal", "heartgold", "soulsilver", "x", "y"]
    elif game_slug in ['blue', 'leafgreen']:
        related_versions = ["blue", "leafgreen", "lets-go-eevee", "y", "alpha-sapphire"]
    elif game_slug in ['yellow']:
        related_versions = ["yellow", "lets-go-pikachu", "lets-go-eevee", "x", "y"]
    else:
        related_versions = ["lets-go-pikachu", "lets-go-eevee", "x", "y", "omega-ruby", "alpha-sapphire", "sword", "shield"]
    for v in related_versions:
        for fe in flavor_entries:
            if fe.get("language", {}).get("name") == "es" and fe.get("version", {}).get("name") == v:
                txt = fe.get("flavor_text", "").replace("\n", " ").replace("\x0c", " ")
                return " ".join(txt.split()).strip()

    # 4. Fallback inglés de la versión exacta
    for fe in flavor_entries:
        if fe.get("language", {}).get("name") == "en" and fe.get("version", {}).get("name") == game_slug:
            txt = fe.get("flavor_text", "").replace("\n", " ").replace("\x0c", " ")
            return " ".join(txt.split()).strip()

    return ""


KANTO_LOCATION_NAMES_ES = {
    'pallet-town-area': 'Pueblo Paleta',
    'viridian-city-area': 'Ciudad Verde',
    'pewter-city-area': 'Ciudad Plateada',
    'cerulean-city-area': 'Ciudad Celeste',
    'vermilion-city-area': 'Ciudad Carmín',
    'lavender-town-area': 'Pueblo Lavanda',
    'celadon-city-area': 'Ciudad Azulona',
    'celadon-city-prize-corner': 'Ciudad Azulona (Casino)',
    'fuchsia-city-area': 'Ciudad Fucsia',
    'saffron-city-area': 'Ciudad Azafrán',
    'cinnabar-island-area': 'Isla Canela',
    'cinnabar-island-cinnabar-lab': 'Isla Canela (Laboratorio)',
    'viridian-forest-area': 'Bosque Verde',
    'digletts-cave-area': 'Cueva Diglett',
    'kanto-power-plant-area': 'Central de Energía',
    'power-plant-area': 'Central de Energía',
    'vermilion-city-ss-anne-dock': 'Muelle del S.S. Anne (Ciudad Carmín)',
    'kanto-route-3-pokemon-center': 'Centro Pokémon de la Ruta 4',
    'kanto-route-4-pokemon-center': 'Centro Pokémon de la Ruta 4',
    'underground-path': 'Vía Subterránea',
    'kanto-underground-path': 'Vía Subterránea',
    'kanto-victory-road-1-1f': 'Calle Victoria (1P)',
    'kanto-victory-road-1-2f': 'Calle Victoria (2P)',
    'kanto-victory-road-1-3f': 'Calle Victoria (3P)',
    'kanto-route-2-south-towards-viridian-city': 'Ruta 2 (Sur)',
    'mt-moon-1f': 'Monte Moon (1P)',
    'rock-tunnel-1f': 'Túnel Roca (1P)',
    'rock-tunnel-b1f': 'Túnel Roca (Sótano)',
}

JOHTO_LOCATION_NAMES_ES = {
    # Ciudades y pueblos de Johto
    'new-bark-town-area': 'Pueblo Primavera',
    'cherrygrove-city-area': 'Ciudad Cerezo',
    'violet-city-area': 'Ciudad Malva',
    'violet-city-southwest-house': 'Ciudad Malva (Casa Suroeste)',
    'azalea-town-area': 'Pueblo Azalea',
    'goldenrod-city-area': 'Ciudad Trigal',
    'goldenrod-city-bills-house': 'Ciudad Trigal (Casa de Bill)',
    'goldenrod-city-department-store-5f': 'Ciudad Trigal (Centro Comercial 5P)',
    'goldenrod-city-game-corner': 'Ciudad Trigal (Casino)',
    'goldenrod-city-north-gate': 'Ciudad Trigal (Caseta Norte)',
    'ecruteak-city-area': 'Ciudad Iris',
    'olivine-city-area': 'Ciudad Olivo',
    'cianwood-city-area': 'Ciudad Orquídea',
    'cianwood-city-manias-house': 'Ciudad Orquídea (Casa de Manía)',
    'mahogany-town-area': 'Pueblo Caoba',
    'blackthorn-city-area': 'Ciudad Endrino',

    # Mazmorras, cuevas, torres e interiores de Johto
    'sprout-tower-2f': 'Torre Bellsprout (2P)',
    'sprout-tower-3f': 'Torre Bellsprout (3P)',
    'ruins-of-alph-outside': 'Ruinas Alfa (Exterior)',
    'ruins-of-alph-interior-a': 'Ruinas Alfa (Cámara A)',
    'ruins-of-alph-interior-b': 'Ruinas Alfa (Cámara B)',
    'ruins-of-alph-interior-c': 'Ruinas Alfa (Cámara C)',
    'ruins-of-alph-interior-d': 'Ruinas Alfa (Cámara D)',
    'union-cave-1f': 'Cueva Unión (1P)',
    'union-cave-b1f': 'Cueva Unión (Sótano 1)',
    'union-cave-b2f': 'Cueva Unión (Sótano 2)',
    'slowpoke-well-1f': 'Pozo Slowpoke (1P)',
    'slowpoke-well-b1f': 'Pozo Slowpoke (Sótano)',
    'ilex-forest-area': 'Encinar',
    'national-park-area': 'Parque Nacional',
    'burned-tower-1f': 'Torre Quemada (1P)',
    'burned-tower-b1f': 'Torre Quemada (Sótano)',
    'bell-tower-2f': 'Torre Hojalata (2P)',
    'bell-tower-3f': 'Torre Hojalata (3P)',
    'bell-tower-4f': 'Torre Hojalata (4P)',
    'bell-tower-5f': 'Torre Hojalata (5P)',
    'bell-tower-6f': 'Torre Hojalata (6P)',
    'bell-tower-7f': 'Torre Hojalata (7P)',
    'bell-tower-8f': 'Torre Hojalata (8P)',
    'bell-tower-9f': 'Torre Hojalata (9P)',
    'bell-tower-roof': 'Torre Hojalata (Tejado)',
    'tin-tower-roof': 'Torre Hojalata (Tejado)',
    'whirl-islands-1f': 'Islas Remolino (1P)',
    'whirl-islands-b1f': 'Islas Remolino (Sótano 1)',
    'whirl-islands-b2f': 'Islas Remolino (Sótano 2)',
    'whirl-islands-b3f': 'Islas Remolino (Sótano 3)',
    'mt-mortar-1f': 'Monte Mortero (1P)',
    'mt-mortar-b1f': 'Monte Mortero (Sótano)',
    'mt-mortar-lower-cave': 'Monte Mortero (Cueva Baja)',
    'mt-mortar-upper-cave': 'Monte Mortero (Cueva Alta)',
    'lake-of-rage-area': 'Lago de la Furia',
    'team-rocket-hq-area': 'Guarida del Team Rocket',
    'ice-path-1f': 'Ruta Helada (1P)',
    'ice-path-b1f': 'Ruta Helada (Sótano 1)',
    'ice-path-b2f': 'Ruta Helada (Sótano 2)',
    'ice-path-b3f': 'Ruta Helada (Sótano 3)',
    'dragons-den-area': 'Guarida Dragón',
    'dark-cave-violet-city-entrance': 'Cueva Oscura (Entrada Ciudad Malva)',
    'dark-cave-blackthorn-city-entrance': 'Cueva Oscura (Entrada Ciudad Endrino)',
    'tohjo-falls-area': 'Cataratas Tohjo',
    'mt-silver-outside': 'Monte Plateado (Exterior)',
    'mt-silver-1f': 'Monte Plateado (1P)',
    'mt-silver-2f': 'Monte Plateado (2P)',
    'mt-silver-top': 'Monte Plateado (Cima)',
    'roaming-johto-area': 'En movimiento por Johto',
}

# Diccionario maestro de ubicaciones canónicas en español
ALL_LOCATION_NAMES_ES = {
    **KANTO_LOCATION_NAMES_ES,
    **JOHTO_LOCATION_NAMES_ES,
}

ENCOUNTER_METHODS_ES = {
    'walk': 'Hierba alta',
    'surf': 'Surfeando (Agua)',
    'old-rod': 'Caña Vieja',
    'good-rod': 'Caña Buena',
    'super-rod': 'Supercaña',
    'gift': 'Regalo',
    'gift-egg': 'Huevo regalo',
    'only-one': 'Encuentro Especial Único',
    'headbutt': 'Golpe Cabeza',
    'headbutt-high': 'Golpe Cabeza',
    'headbutt-low': 'Golpe Cabeza',
    'headbutt-normal': 'Golpe Cabeza',
    'rock-smash': 'Golpe Roca',
    'squirt-bottle': 'Regadera',
    'roaming-grass': 'Pokémon errante',
    'pokeflute': 'Despertar con Poké Flauta',
    'npc-trade': 'Intercambio NPC',
    'static': 'Estático',
}

EVOLUTION_ITEMS_ES = {
    'water-stone': 'Piedra Agua',
    'thunder-stone': 'Piedra Trueno',
    'fire-stone': 'Piedra Fuego',
    'leaf-stone': 'Piedra Hoja',
    'moon-stone': 'Piedra Lunar',
    'sun-stone': 'Piedra Solar',
    'shiny-stone': 'Piedra Día',
    'dusk-stone': 'Piedra Noche',
    'dawn-stone': 'Piedra Alba',
    'ice-stone': 'Piedra Hielo',
    'oval-stone': 'Piedra Oval',
    'kings-rock': 'Roca del Rey',
    'metal-coat': 'Revestimiento Metálico',
    'dragon-scale': 'Escama Dragón',
    'up-grade': 'Mejora',
}

STONE_NAME_TO_SLUG = {
    'piedra agua': 'water-stone',
    'piedra trueno': 'thunder-stone',
    'piedra fuego': 'fire-stone',
    'piedra hoja': 'leaf-stone',
    'piedra lunar': 'moon-stone',
    'piedra solar': 'sun-stone',
    'piedra día': 'shiny-stone',
    'piedra dia': 'shiny-stone',
    'piedra noche': 'dusk-stone',
    'piedra alba': 'dawn-stone',
    'piedra hielo': 'ice-stone',
    'piedra oval': 'oval-stone',
    'roca del rey': 'kings-rock',
    'revestimiento metálico': 'metal-coat',
    'revestimiento metalico': 'metal-coat',
    'revest. metálico': 'metal-coat',
    'revest. metalico': 'metal-coat',
    'escama dragón': 'dragon-scale',
    'escama dragon': 'dragon-scale',
    'mejora': 'up-grade',
}


def resolve_evolution_stone(
    item_slug: Optional[str] = None,
    text_hint: Optional[str] = None,
    game_slug: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Identifica si un Pokémon evoluciona mediante piedra u objeto evolutivo y retorna
    su información estructurada (slug, nombre, icono y ubicaciones exclusivas por juego).
    """
    catalog = get_evolution_stones_catalog()
    slug = item_slug.lower() if item_slug else None

    if not slug and text_hint:
        hint_lower = text_hint.lower()
        for name_key, s in STONE_NAME_TO_SLUG.items():
            if name_key in hint_lower:
                slug = s
                break

    if not slug or (slug not in catalog and slug not in EVOLUTION_ITEMS_ES):
        return None

    stone_data = catalog.get(slug, {})
    name_es = stone_data.get("name_es") or EVOLUTION_ITEMS_ES.get(slug, slug.replace("-", " ").title())
    icon_url = stone_data.get("icon_url") or f"/media/items/{slug}.png"

    # Resolución estricta por versión de juego sin mezclar regiones
    locations = []
    if game_slug and "games" in stone_data:
        locations = stone_data["games"].get(game_slug, [])
    elif not game_slug and "games" in stone_data:
        locations = next(iter(stone_data["games"].values()), [])

    is_purchasable = stone_data.get("is_purchasable", False)
    price = stone_data.get("price")
    availability_note = stone_data.get("availability_note", "")

    # En 2ª Generación (Oro, Plata, Cristal), las piedras y objetos evolutivos NO se compran en centros comerciales
    if game_slug in ['gold', 'silver', 'crystal']:
        is_purchasable = False
        price = None
        if not availability_note or "2.100" in availability_note:
            availability_note = "Objeto limitado. No se encuentra a la venta en tiendas."

    return {
        "slug": slug,
        "name": name_es,
        "icon_url": icon_url,
        "description": stone_data.get("description_es", ""),
        "is_purchasable": is_purchasable,
        "price": price,
        "availability_note": availability_note,
        "locations": locations
    }


# Límite superior de número nacional de Pokédex introducido en cada generación
MAX_NATIONAL_NUMBER_BY_GEN = {
    1: 151,
    2: 251,
    3: 386,
    4: 493,
    5: 649,
    6: 721,
    7: 809,
    8: 905,
    9: 1025,
}

# Ubicación principal de la Guardería / Cuidados Pokémon por edición
DAYCARE_LOCATIONS_BY_GAME: Dict[str, str] = {
    # Gen 2
    'gold': 'Ruta 34 (Guardería Pokémon)',
    'silver': 'Ruta 34 (Guardería Pokémon)',
    'crystal': 'Ruta 34 (Guardería Pokémon)',
    # Gen 3
    'ruby': 'Ruta 117 (Guardería Pokémon)',
    'sapphire': 'Ruta 117 (Guardería Pokémon)',
    'emerald': 'Ruta 117 (Guardería Pokémon)',
    'firered': 'Isla Cuatro (Guardería Pokémon)',
    'leafgreen': 'Isla Cuatro (Guardería Pokémon)',
    # Gen 4
    'diamond': 'Pueblo Sosiego (Guardería Pokémon)',
    'pearl': 'Pueblo Sosiego (Guardería Pokémon)',
    'platinum': 'Pueblo Sosiego (Guardería Pokémon)',
    'heartgold': 'Ruta 34 (Guardería Pokémon)',
    'soulsilver': 'Ruta 34 (Guardería Pokémon)',
    # Gen 5
    'black': 'Ruta 3 (Guardería Pokémon)',
    'white': 'Ruta 3 (Guardería Pokémon)',
    'black-2': 'Ruta 3 (Guardería Pokémon)',
    'white-2': 'Ruta 3 (Guardería Pokémon)',
    # Gen 6
    'x': 'Ruta 7 (Guardería Pokémon)',
    'y': 'Ruta 7 (Guardería Pokémon)',
    'omega-ruby': 'Ruta 117 (Guardería Pokémon)',
    'alpha-sapphire': 'Ruta 117 (Guardería Pokémon)',
    # Gen 7
    'sun': 'Rancho Ohana (Cuidados Pokémon)',
    'moon': 'Rancho Ohana (Cuidados Pokémon)',
    'ultra-sun': 'Rancho Ohana (Cuidados Pokémon)',
    'ultra-moon': 'Rancho Ohana (Cuidados Pokémon)',
    # Gen 8
    'sword': 'Ruta 5 (Cuidados Pokémon)',
    'shield': 'Ruta 5 (Cuidados Pokémon)',
    'brilliant-diamond': 'Pueblo Sosiego (Guardería Pokémon)',
    'shining-pearl': 'Pueblo Sosiego (Guardería Pokémon)',
    # Gen 9
    'scarlet': 'Pícnic Pokémon',
    'violet': 'Pícnic Pokémon',
}

# Especies que no pueden nacer de un huevo bajo ninguna circunstancia (grupo no-eggs o Ditto)
NON_HATCHABLE_SPECIES = {
    # Nidorina y Nidoqueen
    30, 31,
    # Ditto (no existen huevos de Ditto)
    132,
    # Unown
    201,
    # Legendarios y Míticos Gen 1
    144, 145, 146, 150, 151,
    # Legendarios y Míticos Gen 2
    243, 244, 245, 249, 250, 251,
    # Legendarios y Míticos Gen 3
    377, 378, 379, 380, 381, 382, 383, 384, 385, 386,
    # Legendarios y Míticos Gen 4
    480, 481, 482, 483, 484, 485, 486, 487, 488, 490, 491, 492, 493,
}

# Pokémon bebé reconocidos en la franquicia
BABY_SPECIES = {
    # Gen 2
    172, 173, 174, 175, 236, 238, 239, 240,
    # Gen 3
    298, 360,
    # Gen 4
    406, 433, 438, 439, 440, 446, 447, 458,
    # Gen 8
    848,
}

# Pokémon bebé que pueden eclosionar del Huevo Extraño regalado en la Guardería de Johto (con mayor probabilidad de variocolor)
GEN2_ODD_EGG_SPECIES = {172, 173, 174, 236, 238, 239, 240}

def _make_starter_entry(
    summary: str,
    area: str,
    method: str = "Elección inicial",
    extra_locations: Optional[List[Dict[str, str]]] = None
) -> Dict[str, Any]:
    locs = [{"area": area, "method": method}]
    if extra_locations:
        locs.extend(extra_locations)
    return {
        "type": "starter",
        "badge_label": "Inicial",
        "badge_color": "emerald",
        "summary": summary,
        "locations": locs
    }

GEN1_KANTO_STARTERS: Dict[int, Dict[str, Any]] = {
    1: _make_starter_entry("Pokémon inicial a elegir en el Laboratorio del Profesor Oak en Pueblo Paleta.", "Pueblo Paleta (Laboratorio de Oak)"),
    4: _make_starter_entry("Pokémon inicial a elegir en el Laboratorio del Profesor Oak en Pueblo Paleta.", "Pueblo Paleta (Laboratorio de Oak)"),
    7: _make_starter_entry("Pokémon inicial a elegir en el Laboratorio del Profesor Oak en Pueblo Paleta.", "Pueblo Paleta (Laboratorio de Oak)"),
}

GEN2_JOHTO_STARTERS: Dict[int, Dict[str, Any]] = {
    152: _make_starter_entry(
        "Pokémon inicial a elegir en el Laboratorio del Profesor Elm en Pueblo Primavera (también obtenible mediante crianza).",
        "Pueblo Primavera (Laboratorio de Elm)",
        extra_locations=[{"area": "Ruta 34 (Guardería Pokémon)", "method": "Crianza de huevo"}]
    ),
    155: _make_starter_entry(
        "Pokémon inicial a elegir en el Laboratorio del Profesor Elm en Pueblo Primavera (también obtenible mediante crianza).",
        "Pueblo Primavera (Laboratorio de Elm)",
        extra_locations=[{"area": "Ruta 34 (Guardería Pokémon)", "method": "Crianza de huevo"}]
    ),
    158: _make_starter_entry(
        "Pokémon inicial a elegir en el Laboratorio del Profesor Elm en Pueblo Primavera (también obtenible mediante crianza).",
        "Pueblo Primavera (Laboratorio de Elm)",
        extra_locations=[{"area": "Ruta 34 (Guardería Pokémon)", "method": "Crianza de huevo"}]
    ),
}

GEN3_HOENN_STARTERS: Dict[int, Dict[str, Any]] = {
    252: _make_starter_entry("Pokémon inicial a elegir en la Ruta 101 (maletín del Profesor Abedul).", "Ruta 101 (Maletín de Abedul)"),
    255: _make_starter_entry("Pokémon inicial a elegir en la Ruta 101 (maletín del Profesor Abedul).", "Ruta 101 (Maletín de Abedul)"),
    258: _make_starter_entry("Pokémon inicial a elegir en la Ruta 101 (maletín del Profesor Abedul).", "Ruta 101 (Maletín de Abedul)"),
}

GEN4_SINNOH_STARTERS: Dict[int, Dict[str, Any]] = {
    387: _make_starter_entry("Pokémon inicial a elegir en el Lago Veraz (maletín del Profesor Serbal).", "Lago Veraz (Maletín de Serbal)"),
    390: _make_starter_entry("Pokémon inicial a elegir en el Lago Veraz (maletín del Profesor Serbal).", "Lago Veraz (Maletín de Serbal)"),
    393: _make_starter_entry("Pokémon inicial a elegir en el Lago Veraz (maletín del Profesor Serbal).", "Lago Veraz (Maletín de Serbal)"),
}

GEN5_UNOVA_STARTERS: Dict[int, Dict[str, Any]] = {
    495: _make_starter_entry("Pokémon inicial a elegir en Pueblo Arcilla (regalo de la Profesora Encina).", "Pueblo Arcilla"),
    498: _make_starter_entry("Pokémon inicial a elegir en Pueblo Arcilla (regalo de la Profesora Encina).", "Pueblo Arcilla"),
    501: _make_starter_entry("Pokémon inicial a elegir en Pueblo Arcilla (regalo de la Profesora Encina).", "Pueblo Arcilla"),
}

# Catálogo canónico de Pokémon Iniciales modular por juego
STARTERS_BY_GAME: Dict[str, Dict[int, Dict[str, Any]]] = {
    # Gen 1
    'red': GEN1_KANTO_STARTERS,
    'blue': GEN1_KANTO_STARTERS,
    'yellow': {
        25: _make_starter_entry("Pokémon inicial entregado por el Profesor Oak en Pueblo Paleta.", "Pueblo Paleta (Laboratorio de Oak)"),
    },
    # Gen 2
    'gold': GEN2_JOHTO_STARTERS,
    'silver': GEN2_JOHTO_STARTERS,
    'crystal': GEN2_JOHTO_STARTERS,
    # Gen 3
    'ruby': GEN3_HOENN_STARTERS,
    'sapphire': GEN3_HOENN_STARTERS,
    'emerald': GEN3_HOENN_STARTERS,
    'firered': GEN1_KANTO_STARTERS,
    'leafgreen': GEN1_KANTO_STARTERS,
    # Gen 4
    'diamond': GEN4_SINNOH_STARTERS,
    'pearl': GEN4_SINNOH_STARTERS,
    'platinum': GEN4_SINNOH_STARTERS,
    'heartgold': GEN2_JOHTO_STARTERS,
    'soulsilver': GEN2_JOHTO_STARTERS,
    # Gen 5
    'black': GEN5_UNOVA_STARTERS,
    'white': GEN5_UNOVA_STARTERS,
    'black-2': GEN5_UNOVA_STARTERS,
    'white-2': GEN5_UNOVA_STARTERS,
}

RED_SPECIAL_CASES: Dict[int, Dict[str, Any]] = {
    # Exclusivos de Pokémon Azul (no aparecen salvajes en Rojo)
    27: {"type": "trade", "badge_label": "Intercambio", "badge_color": "sky", "summary": "Exclusivo de Pokémon Azul (obtenible mediante intercambio)", "locations": [{"area": "Edición Pokémon Azul", "method": "Intercambio con cable link"}]},
    28: {"type": "trade", "badge_label": "Intercambio", "badge_color": "sky", "summary": "Evoluciona de Sandshrew (Exclusivo de Pokémon Azul, obtenible mediante intercambio)", "locations": [{"area": "Edición Pokémon Azul", "method": "Intercambio con cable link"}]},
    37: {"type": "trade", "badge_label": "Intercambio", "badge_color": "sky", "summary": "Exclusivo de Pokémon Azul (obtenible mediante intercambio)", "locations": [{"area": "Edición Pokémon Azul", "method": "Intercambio con cable link"}]},
    38: {"type": "trade", "badge_label": "Intercambio", "badge_color": "sky", "summary": "Evoluciona de Vulpix (Exclusivo de Pokémon Azul, obtenible mediante intercambio)", "locations": [{"area": "Edición Pokémon Azul", "method": "Intercambio con cable link"}]},
    52: {"type": "trade", "badge_label": "Intercambio", "badge_color": "sky", "summary": "Exclusivo de Pokémon Azul (obtenible mediante intercambio)", "locations": [{"area": "Edición Pokémon Azul", "method": "Intercambio con cable link"}]},
    53: {"type": "trade", "badge_label": "Intercambio", "badge_color": "sky", "summary": "Evoluciona de Meowth (Exclusivo de Pokémon Azul, obtenible mediante intercambio)", "locations": [{"area": "Edición Pokémon Azul", "method": "Intercambio con cable link"}]},
    69: {"type": "trade", "badge_label": "Intercambio", "badge_color": "sky", "summary": "Exclusivo de Pokémon Azul (obtenible mediante intercambio)", "locations": [{"area": "Edición Pokémon Azul", "method": "Intercambio con cable link"}]},
    70: {"type": "trade", "badge_label": "Intercambio", "badge_color": "sky", "summary": "Evoluciona de Bellsprout (Exclusivo de Pokémon Azul, obtenible mediante intercambio)", "locations": [{"area": "Edición Pokémon Azul", "method": "Intercambio con cable link"}]},
    71: {"type": "trade", "badge_label": "Intercambio", "badge_color": "sky", "summary": "Evoluciona de Weepinbell (Exclusivo de Pokémon Azul, obtenible mediante intercambio)", "locations": [{"area": "Edición Pokémon Azul", "method": "Intercambio con cable link"}]},
    126: {"type": "trade", "badge_label": "Intercambio", "badge_color": "sky", "summary": "Exclusivo de Pokémon Azul (obtenible mediante intercambio)", "locations": [{"area": "Edición Pokémon Azul", "method": "Intercambio con cable link"}]},
    127: {"type": "trade", "badge_label": "Intercambio", "badge_color": "sky", "summary": "Exclusivo de Pokémon Azul (obtenible mediante intercambio)", "locations": [{"area": "Edición Pokémon Azul", "method": "Intercambio con cable link"}]},
    # Intercambios dentro del juego (In-game trades)
    83: {"type": "trade_npc", "badge_label": "Intercambio NPC", "badge_color": "violet", "summary": "Intercambio en Ciudad Carmín: entrega un Spearow a cambio de Farfetch'd (con el mote «Dux»)", "locations": [{"area": "Ciudad Carmín", "method": "Intercambio por Spearow"}]},
    122: {"type": "trade_npc", "badge_label": "Intercambio NPC", "badge_color": "violet", "summary": "Intercambio en la caseta de la Ruta 2: entrega un Abra a cambio de Mr. Mime (con el mote «Marcel»)", "locations": [{"area": "Ruta 2 (Caseta)", "method": "Intercambio por Abra"}]},
    124: {"type": "trade_npc", "badge_label": "Intercambio NPC", "badge_color": "violet", "summary": "Intercambio en Ciudad Celeste: entrega un Poliwhirl a cambio de Jynx (con el mote «Lola»)", "locations": [{"area": "Ciudad Celeste", "method": "Intercambio por Poliwhirl"}]},
    108: {"type": "trade_npc", "badge_label": "Intercambio NPC", "badge_color": "violet", "summary": "Intercambio en la caseta de la Ruta 18: entrega un Slowbro a cambio de Lickitung (con el mote «Marc»)", "locations": [{"area": "Ruta 18 (Caseta)", "method": "Intercambio por Slowbro"}]},
    # Casino Ciudad Azulona
    137: {"type": "casino", "badge_label": "Premio Casino", "badge_color": "amber", "summary": "Canjeable en el Casino Rocket de Ciudad Azulona por 9.999 fichas", "locations": [{"area": "Ciudad Azulona (Casino)", "method": "Canje de fichas (9.999)"}]},
    # Fósiles
    138: {"type": "fossil", "badge_label": "Fósil", "badge_color": "amber", "is_unique": True, "summary": "Revivir el Fósil Hélix en el Laboratorio de Isla Canela", "locations": [{"area": "Isla Canela (Laboratorio)", "method": "Revivir Fósil Hélix"}]},
    139: {"type": "evolution", "badge_label": "Evolución", "badge_color": "indigo", "summary": "Evoluciona de Omanyte al nivel 40"},
    140: {"type": "fossil", "badge_label": "Fósil", "badge_color": "amber", "is_unique": True, "summary": "Revivir el Fósil Domo en el Laboratorio de Isla Canela", "locations": [{"area": "Isla Canela (Laboratorio)", "method": "Revivir Fósil Domo"}]},
    141: {"type": "evolution", "badge_label": "Evolución", "badge_color": "indigo", "summary": "Evoluciona de Kabuto al nivel 40"},
    142: {"type": "fossil", "badge_label": "Fósil", "badge_color": "amber", "is_unique": True, "summary": "Revivir el Ámbar Viejo en el Laboratorio de Isla Canela", "locations": [{"area": "Isla Canela (Laboratorio)", "method": "Revivir Ámbar Viejo"}]},
    # Premios por victoria / Elección
    106: {"type": "prize", "badge_label": "Premio Dojo", "badge_color": "emerald", "is_unique": True, "summary": "Elegir entre Hitmonlee o Hitmonchan tras vencer al Maestro del Dojo Kárate en Ciudad Azafrán", "locations": [{"area": "Ciudad Azafrán (Dojo Kárate)", "method": "Premio por victoria"}]},
    107: {"type": "prize", "badge_label": "Premio Dojo", "badge_color": "emerald", "is_unique": True, "summary": "Elegir entre Hitmonlee o Hitmonchan tras vencer al Maestro del Dojo Kárate en Ciudad Azafrán", "locations": [{"area": "Ciudad Azafrán (Dojo Kárate)", "method": "Premio por victoria"}]},
    # Regalos de NPCs
    131: {"type": "gift", "badge_label": "Regalo", "badge_color": "emerald", "is_unique": True, "summary": "Regalo de un empleado en el piso 7 del edificio Silph S.A. (Ciudad Azafrán)", "locations": [{"area": "Ciudad Azafrán (Silph S.A.)", "method": "Regalo de empleado"}]},
    133: {"type": "gift", "badge_label": "Regalo", "badge_color": "emerald", "is_unique": True, "summary": "Pokéball sobre la mesa del ático en la Mansión Azulona (Ciudad Azulona)", "locations": [{"area": "Ciudad Azulona (Mansión Azulona)", "method": "Pokéball en el ático"}]},
    # Estáticos / Legendarios
    143: {"type": "special", "badge_label": "Estático", "badge_color": "rose", "is_unique": True, "summary": "Pokémon único que se encuentra durmiendo y bloqueando el camino entre las rutas 12 y 16. Se debe despertar usando la Poké Flauta para poder capturarlo.", "locations": [{"area": "Bloqueando el camino entre las rutas 12 y 16", "method": "Despertar con Poké Flauta"}]},
    144: {"type": "legendary", "badge_label": "Legendario", "badge_color": "rose", "is_unique": True, "summary": "En lo profundo de las Islas Espuma (Sótano B4F)", "locations": [{"area": "Islas Espuma (Sótano B4F)", "method": "Encuentro Legendario"}]},
    145: {"type": "legendary", "badge_label": "Legendario", "badge_color": "rose", "is_unique": True, "summary": "Al final de la Central de Energía", "locations": [{"area": "Central de Energía", "method": "Encuentro Legendario"}]},
    146: {"type": "legendary", "badge_label": "Legendario", "badge_color": "rose", "summary": "En la Calle Victoria (cerca del Alto Mando)", "is_unique": True, "locations": [{"area": "Calle Victoria", "method": "Encuentro Legendario"}]},
    150: {"type": "legendary", "badge_label": "Legendario", "badge_color": "rose", "is_unique": True, "summary": "En lo profundo de la Cueva Celeste (tras vencer en la Liga Pokémon)", "locations": [{"area": "Cueva Celeste", "method": "Encuentro Legendario"}]},
    151: {"type": "mythical", "badge_label": "Mítico / Evento", "badge_color": "violet", "is_unique": True, "summary": "Distribución oficial de Nintendo mediante evento especial", "locations": [{"area": "Evento Nintendo", "method": "Distribución especial"}]},
}

BLUE_SPECIAL_CASES: Dict[int, Dict[str, Any]] = {
    # Exclusivos de Pokémon Rojo (no aparecen salvajes en Azul)
    23: {"type": "trade", "badge_label": "Intercambio", "badge_color": "sky", "summary": "Exclusivo de Pokémon Rojo (obtenible mediante intercambio)", "locations": [{"area": "Edición Pokémon Rojo", "method": "Intercambio con cable link"}]},
    24: {"type": "trade", "badge_label": "Intercambio", "badge_color": "sky", "summary": "Evoluciona de Ekans (Exclusivo de Pokémon Rojo, obtenible mediante intercambio)", "locations": [{"area": "Edición Pokémon Rojo", "method": "Intercambio con cable link"}]},
    43: {"type": "trade", "badge_label": "Intercambio", "badge_color": "sky", "summary": "Exclusivo de Pokémon Rojo (obtenible mediante intercambio)", "locations": [{"area": "Edición Pokémon Rojo", "method": "Intercambio con cable link"}]},
    44: {"type": "trade", "badge_label": "Intercambio", "badge_color": "sky", "summary": "Evoluciona de Oddish (Exclusivo de Pokémon Rojo, obtenible mediante intercambio)", "locations": [{"area": "Edición Pokémon Rojo", "method": "Intercambio con cable link"}]},
    45: {"type": "trade", "badge_label": "Intercambio", "badge_color": "sky", "summary": "Evoluciona de Gloom (Exclusivo de Pokémon Rojo, obtenible mediante intercambio)", "locations": [{"area": "Edición Pokémon Rojo", "method": "Intercambio con cable link"}]},
    56: {"type": "trade", "badge_label": "Intercambio", "badge_color": "sky", "summary": "Exclusivo de Pokémon Rojo (obtenible mediante intercambio)", "locations": [{"area": "Edición Pokémon Rojo", "method": "Intercambio con cable link"}]},
    57: {"type": "trade", "badge_label": "Intercambio", "badge_color": "sky", "summary": "Evoluciona de Mankey (Exclusivo de Pokémon Rojo, obtenible mediante intercambio)", "locations": [{"area": "Edición Pokémon Rojo", "method": "Intercambio con cable link"}]},
    58: {"type": "trade", "badge_label": "Intercambio", "badge_color": "sky", "summary": "Exclusivo de Pokémon Rojo (obtenible mediante intercambio)", "locations": [{"area": "Edición Pokémon Rojo", "method": "Intercambio con cable link"}]},
    59: {"type": "trade", "badge_label": "Intercambio", "badge_color": "sky", "summary": "Evoluciona de Growlithe (Exclusivo de Pokémon Rojo, obtenible mediante intercambio)", "locations": [{"area": "Edición Pokémon Rojo", "method": "Intercambio con cable link"}]},
    123: {"type": "trade", "badge_label": "Intercambio", "badge_color": "sky", "summary": "Exclusivo de Pokémon Rojo (obtenible mediante intercambio)", "locations": [{"area": "Edición Pokémon Rojo", "method": "Intercambio con cable link"}]},
    125: {"type": "trade", "badge_label": "Intercambio", "badge_color": "sky", "summary": "Exclusivo de Pokémon Rojo (obtenible mediante intercambio)", "locations": [{"area": "Edición Pokémon Rojo", "method": "Intercambio con cable link"}]},
    # Intercambios dentro del juego (In-game trades)
    83: {"type": "trade_npc", "badge_label": "Intercambio NPC", "badge_color": "violet", "summary": "Intercambio en Ciudad Carmín: entrega un Spearow a cambio de Farfetch'd (con el mote «Dux»)", "locations": [{"area": "Ciudad Carmín", "method": "Intercambio por Spearow"}]},
    122: {"type": "trade_npc", "badge_label": "Intercambio NPC", "badge_color": "violet", "summary": "Intercambio en la caseta de la Ruta 2: entrega un Abra a cambio de Mr. Mime (con el mote «Marcel»)", "locations": [{"area": "Ruta 2 (Caseta)", "method": "Intercambio por Abra"}]},
    124: {"type": "trade_npc", "badge_label": "Intercambio NPC", "badge_color": "violet", "summary": "Intercambio en Ciudad Celeste: entrega un Poliwhirl a cambio de Jynx (con el mote «Lola»)", "locations": [{"area": "Ciudad Celeste", "method": "Intercambio por Poliwhirl"}]},
    108: {"type": "trade_npc", "badge_label": "Intercambio NPC", "badge_color": "violet", "summary": "Intercambio en la caseta de la Ruta 18: entrega un Slowbro a cambio de Lickitung (con el mote «Marc»)", "locations": [{"area": "Ruta 18 (Caseta)", "method": "Intercambio por Slowbro"}]},
    # Casino Ciudad Azulona (Premios específicos de Azul)
    137: {"type": "casino", "badge_label": "Premio Casino", "badge_color": "amber", "summary": "Canjeable en el Casino Rocket de Ciudad Azulona por 6.500 fichas", "locations": [{"area": "Ciudad Azulona (Casino)", "method": "Canje de fichas (6.500)"}]},
    # Fósiles
    138: {"type": "fossil", "badge_label": "Fósil", "badge_color": "amber", "is_unique": True, "summary": "Revivir el Fósil Hélix en el Laboratorio de Isla Canela", "locations": [{"area": "Isla Canela (Laboratorio)", "method": "Revivir Fósil Hélix"}]},
    139: {"type": "evolution", "badge_label": "Evolución", "badge_color": "indigo", "summary": "Evoluciona de Omanyte al nivel 40"},
    140: {"type": "fossil", "badge_label": "Fósil", "badge_color": "amber", "is_unique": True, "summary": "Revivir el Fósil Domo en el Laboratorio de Isla Canela", "locations": [{"area": "Isla Canela (Laboratorio)", "method": "Revivir Fósil Domo"}]},
    141: {"type": "evolution", "badge_label": "Evolución", "badge_color": "indigo", "summary": "Evoluciona de Kabuto al nivel 40"},
    142: {"type": "fossil", "badge_label": "Fósil", "badge_color": "amber", "is_unique": True, "summary": "Revivir el Ámbar Viejo en el Laboratorio de Isla Canela", "locations": [{"area": "Isla Canela (Laboratorio)", "method": "Revivir Ámbar Viejo"}]},
    # Premios por victoria / Elección
    106: {"type": "prize", "badge_label": "Premio Dojo", "badge_color": "emerald", "is_unique": True, "summary": "Elegir entre Hitmonlee o Hitmonchan tras vencer al Maestro del Dojo Kárate en Ciudad Azafrán", "locations": [{"area": "Ciudad Azafrán (Dojo Kárate)", "method": "Premio por victoria"}]},
    107: {"type": "prize", "badge_label": "Premio Dojo", "badge_color": "emerald", "is_unique": True, "summary": "Elegir entre Hitmonlee o Hitmonchan tras vencer al Maestro del Dojo Kárate en Ciudad Azafrán", "locations": [{"area": "Ciudad Azafrán (Dojo Kárate)", "method": "Premio por victoria"}]},
    # Regalos de NPCs
    131: {"type": "gift", "badge_label": "Regalo", "badge_color": "emerald", "is_unique": True, "summary": "Regalo de un empleado en el piso 7 del edificio Silph S.A. (Ciudad Azafrán)", "locations": [{"area": "Ciudad Azafrán (Silph S.A.)", "method": "Regalo de empleado"}]},
    133: {"type": "gift", "badge_label": "Regalo", "badge_color": "emerald", "is_unique": True, "summary": "Pokéball sobre la mesa del ático en la Mansión Azulona (Ciudad Azulona)", "locations": [{"area": "Ciudad Azulona (Mansión Azulona)", "method": "Pokéball en el ático"}]},
    # Estáticos / Legendarios
    143: {"type": "special", "badge_label": "Estático", "badge_color": "rose", "is_unique": True, "summary": "Pokémon único que se encuentra durmiendo y bloqueando el camino entre las rutas 12 y 16. Se debe despertar usando la Poké Flauta para poder capturarlo.", "locations": [{"area": "Bloqueando el camino entre las rutas 12 y 16", "method": "Despertar con Poké Flauta"}]},
    144: {"type": "legendary", "badge_label": "Legendario", "badge_color": "rose", "is_unique": True, "summary": "En lo profundo de las Islas Espuma (Sótano B4F)", "locations": [{"area": "Islas Espuma (Sótano B4F)", "method": "Encuentro Legendario"}]},
    145: {"type": "legendary", "badge_label": "Legendario", "badge_color": "rose", "is_unique": True, "summary": "Al final de la Central de Energía", "locations": [{"area": "Central de Energía", "method": "Encuentro Legendario"}]},
    146: {"type": "legendary", "badge_label": "Legendario", "badge_color": "rose", "summary": "En la Calle Victoria (cerca del Alto Mando)", "is_unique": True, "locations": [{"area": "Calle Victoria", "method": "Encuentro Legendario"}]},
    150: {"type": "legendary", "badge_label": "Legendario", "badge_color": "rose", "is_unique": True, "summary": "En lo profundo de la Cueva Celeste (tras vencer en la Liga Pokémon)", "locations": [{"area": "Cueva Celeste", "method": "Encuentro Legendario"}]},
    151: {"type": "mythical", "badge_label": "Mítico / Evento", "badge_color": "violet", "is_unique": True, "summary": "Distribución oficial de Nintendo mediante evento especial", "locations": [{"area": "Evento Nintendo", "method": "Distribución especial"}]},
}

YELLOW_SPECIAL_CASES: Dict[int, Dict[str, Any]] = {
    # 1. Los 13 Pokémon faltantes en Pokémon Amarillo (no aparecen salvajes ni pueden evolucionar)
    13: {"type": "trade", "badge_label": "Intercambio", "badge_color": "amber", "summary": "No disponible en Amarillo. Conseguir mediante intercambio desde Pokémon Rojo o Pokémon Azul", "locations": [{"area": "Edición Rojo / Azul", "method": "Intercambio con cable link"}]},
    14: {"type": "trade", "badge_label": "Intercambio", "badge_color": "amber", "summary": "Evoluciona de Weedle (No disponible en Amarillo. Intercambio desde Pokémon Rojo o Pokémon Azul)", "locations": [{"area": "Edición Rojo / Azul", "method": "Intercambio con cable link"}]},
    15: {"type": "trade", "badge_label": "Intercambio", "badge_color": "amber", "summary": "Evoluciona de Kakuna (No disponible en Amarillo. Intercambio desde Pokémon Rojo o Pokémon Azul)", "locations": [{"area": "Edición Rojo / Azul", "method": "Intercambio con cable link"}]},
    23: {"type": "trade", "badge_label": "Intercambio", "badge_color": "rose", "summary": "Exclusivo de Pokémon Rojo (no disponible en Amarillo). Conseguir mediante intercambio", "locations": [{"area": "Edición Pokémon Rojo", "method": "Intercambio con cable link"}]},
    24: {"type": "trade", "badge_label": "Intercambio", "badge_color": "rose", "summary": "Evoluciona de Ekans (Exclusivo de Pokémon Rojo. Conseguir mediante intercambio)", "locations": [{"area": "Edición Pokémon Rojo", "method": "Intercambio con cable link"}]},
    26: {"type": "trade", "badge_label": "Intercambio", "badge_color": "amber", "summary": "Tu Pikachu inicial se niega a evolucionar con la Piedra Trueno. Debes transferir un Raichu o un Pikachu desde Pokémon Rojo o Azul", "locations": [{"area": "Edición Rojo / Azul", "method": "Intercambio con cable link"}]},
    52: {"type": "trade", "badge_label": "Intercambio", "badge_color": "sky", "summary": "Exclusivo de Pokémon Azul (no disponible en Amarillo). Conseguir mediante intercambio", "locations": [{"area": "Edición Pokémon Azul", "method": "Intercambio con cable link"}]},
    53: {"type": "trade", "badge_label": "Intercambio", "badge_color": "sky", "summary": "Evoluciona de Meowth (Exclusivo de Pokémon Azul. Conseguir mediante intercambio)", "locations": [{"area": "Edición Pokémon Azul", "method": "Intercambio con cable link"}]},
    109: {"type": "trade", "badge_label": "Intercambio", "badge_color": "amber", "summary": "No disponible en Amarillo. Conseguir mediante intercambio desde Pokémon Rojo o Pokémon Azul", "locations": [{"area": "Edición Rojo / Azul", "method": "Intercambio con cable link"}]},
    110: {"type": "trade", "badge_label": "Intercambio", "badge_color": "amber", "summary": "Evoluciona de Koffing (No disponible en Amarillo. Intercambio desde Pokémon Rojo o Pokémon Azul)", "locations": [{"area": "Edición Rojo / Azul", "method": "Intercambio con cable link"}]},
    124: {"type": "trade", "badge_label": "Intercambio", "badge_color": "amber", "summary": "No disponible en Amarillo. Conseguir mediante intercambio desde Pokémon Rojo o Pokémon Azul", "locations": [{"area": "Edición Rojo / Azul", "method": "Intercambio con cable link"}]},
    125: {"type": "trade", "badge_label": "Intercambio", "badge_color": "rose", "summary": "Exclusivo de Pokémon Rojo (no disponible en Amarillo). Conseguir mediante intercambio", "locations": [{"area": "Edición Pokémon Rojo", "method": "Intercambio con cable link"}]},
    126: {"type": "trade", "badge_label": "Intercambio", "badge_color": "sky", "summary": "Exclusivo de Pokémon Azul (no disponible en Amarillo). Conseguir mediante intercambio", "locations": [{"area": "Edición Pokémon Azul", "method": "Intercambio con cable link"}]},

    # 2. Iniciales clásicos entregados como regalo en Amarillo
    1: {"type": "gift", "badge_label": "Regalo", "badge_color": "emerald", "is_unique": True, "summary": "Regalado por una chica en una casa de Ciudad Celeste si Pikachu tiene un alto nivel de amistad", "locations": [{"area": "Ciudad Celeste", "method": "Regalo si Pikachu es feliz"}]},
    4: {"type": "gift", "badge_label": "Regalo", "badge_color": "emerald", "is_unique": True, "summary": "Entregado por un entrenador en la Ruta 24 (al norte del Puente Pepita)", "locations": [{"area": "Ruta 24", "method": "Regalo de entrenador"}]},
    7: {"type": "gift", "badge_label": "Regalo", "badge_color": "emerald", "is_unique": True, "summary": "Entregado por la Agente Mara en Ciudad Carmín tras derrotar al Líder Lt. Surge", "locations": [{"area": "Ciudad Carmín", "method": "Regalo de la Agente Mara"}]},

    # 3. Intercambios dentro del juego en Amarillo (In-game NPC trades)
    68: {"type": "trade_npc", "badge_label": "Intercambio NPC", "badge_color": "violet", "summary": "Intercambio en la Vía Subterránea de la Ruta 5: entrega un Cubone a cambio de Machoke (con el mote «Ricky»), que evoluciona inmediatamente a Machamp tras el intercambio", "locations": [{"area": "Ruta 5 (Vía Subterránea)", "method": "Intercambio por Cubone"}]},
    122: {"type": "trade_npc", "badge_label": "Intercambio NPC", "badge_color": "violet", "summary": "Intercambio en la caseta de la Ruta 2: entrega un Clefairy a cambio de Mr. Mime (con el mote «Miles»)", "locations": [{"area": "Ruta 2 (Caseta)", "method": "Intercambio por Clefairy"}]},

    # 4. Fósiles
    138: {"type": "fossil", "badge_label": "Fósil", "badge_color": "amber", "is_unique": True, "summary": "Revivir el Fósil Hélix en el Laboratorio de Isla Canela", "locations": [{"area": "Isla Canela (Laboratorio)", "method": "Revivir Fósil Hélix"}]},
    139: {"type": "evolution", "badge_label": "Evolución", "badge_color": "indigo", "summary": "Evoluciona de Omanyte al nivel 40"},
    140: {"type": "fossil", "badge_label": "Fósil", "badge_color": "amber", "is_unique": True, "summary": "Revivir el Fósil Domo en el Laboratorio de Isla Canela", "locations": [{"area": "Isla Canela (Laboratorio)", "method": "Revivir Fósil Domo"}]},
    141: {"type": "evolution", "badge_label": "Evolución", "badge_color": "indigo", "summary": "Evoluciona de Kabuto al nivel 40"},
    142: {"type": "fossil", "badge_label": "Fósil", "badge_color": "amber", "is_unique": True, "summary": "Revivir el Ámbar Viejo en el Laboratorio de Isla Canela", "locations": [{"area": "Isla Canela (Laboratorio)", "method": "Revivir Ámbar Viejo"}]},

    # 5. Premios Dojo Kárate
    106: {"type": "prize", "badge_label": "Premio Dojo", "badge_color": "emerald", "is_unique": True, "summary": "Elegir entre Hitmonlee o Hitmonchan tras vencer al Maestro del Dojo Kárate en Ciudad Azafrán", "locations": [{"area": "Ciudad Azafrán (Dojo Kárate)", "method": "Premio por victoria"}]},
    107: {"type": "prize", "badge_label": "Premio Dojo", "badge_color": "emerald", "is_unique": True, "summary": "Elegir entre Hitmonlee o Hitmonchan tras vencer al Maestro del Dojo Kárate en Ciudad Azafrán", "locations": [{"area": "Ciudad Azafrán (Dojo Kárate)", "method": "Premio por victoria"}]},

    # 6. Regalos de NPCs
    131: {"type": "gift", "badge_label": "Regalo", "badge_color": "emerald", "is_unique": True, "summary": "Regalo de un empleado en el piso 7 del edificio Silph S.A. (Ciudad Azafrán)", "locations": [{"area": "Ciudad Azafrán (Silph S.A.)", "method": "Regalo de empleado"}]},
    133: {"type": "gift", "badge_label": "Regalo", "badge_color": "emerald", "is_unique": True, "summary": "Pokéball sobre la mesa del ático en la Mansión Azulona (Ciudad Azulona)", "locations": [{"area": "Ciudad Azulona (Mansión Azulona)", "method": "Pokéball en el ático"}]},

    # 7. Estáticos / Legendarios
    143: {"type": "special", "badge_label": "Estático", "badge_color": "rose", "is_unique": True, "summary": "Pokémon único que se encuentra durmiendo y bloqueando el camino entre las rutas 12 y 16. Se debe despertar usando la Poké Flauta para poder capturarlo.", "locations": [{"area": "Bloqueando el camino entre las rutas 12 y 16", "method": "Despertar con Poké Flauta"}]},
    144: {"type": "legendary", "badge_label": "Legendario", "badge_color": "rose", "is_unique": True, "summary": "En lo profundo de las Islas Espuma (Sótano B4F)", "locations": [{"area": "Islas Espuma (Sótano B4F)", "method": "Encuentro Legendario"}]},
    145: {"type": "legendary", "badge_label": "Legendario", "badge_color": "rose", "is_unique": True, "summary": "Al final de la Central de Energía", "locations": [{"area": "Central de Energía", "method": "Encuentro Legendario"}]},
    146: {"type": "legendary", "badge_label": "Legendario", "badge_color": "rose", "is_unique": True, "summary": "En la Calle Victoria (cerca del Alto Mando)", "locations": [{"area": "Calle Victoria", "method": "Encuentro Legendario"}]},
    150: {"type": "legendary", "badge_label": "Legendario", "badge_color": "rose", "is_unique": True, "summary": "En lo profundo de la Cueva Celeste (tras vencer en la Liga Pokémon)", "locations": [{"area": "Cueva Celeste", "method": "Encuentro Legendario"}]},
    151: {"type": "mythical", "badge_label": "Mítico / Evento", "badge_color": "violet", "is_unique": True, "summary": "Distribución oficial de Nintendo mediante evento especial", "locations": [{"area": "Evento Nintendo", "method": "Distribución especial"}]},
}

GOLD_SPECIAL_CASES: Dict[int, Dict[str, Any]] = {
    # 1. Iniciales de Kanto (no disponibles de forma salvaje en Johto; Cápsula del Tiempo)
    1: {"type": "trade", "badge_label": "Intercambio", "badge_color": "sky", "summary": "No disponible en estado salvaje en Johto. Conseguir mediante intercambio desde Pokémon Rojo, Azul o Amarillo (Cápsula del Tiempo, también obtenible mediante crianza)", "locations": [{"area": "Cápsula del Tiempo (Rojo/Azul/Amarillo)", "method": "Intercambio con cable link"}, {"area": "Ruta 34 (Guardería Pokémon)", "method": "Crianza de huevo"}]},
    2: {"type": "trade", "badge_label": "Intercambio", "badge_color": "sky", "summary": "Evoluciona de Bulbasaur al nivel 16 (Transferir mediante Cápsula del Tiempo)", "locations": [{"area": "Cápsula del Tiempo (Rojo/Azul/Amarillo)", "method": "Intercambio con cable link"}]},
    3: {"type": "trade", "badge_label": "Intercambio", "badge_color": "sky", "summary": "Evoluciona de Ivysaur al nivel 32 (Transferir mediante Cápsula del Tiempo)", "locations": [{"area": "Cápsula del Tiempo (Rojo/Azul/Amarillo)", "method": "Intercambio con cable link"}]},
    4: {"type": "trade", "badge_label": "Intercambio", "badge_color": "sky", "summary": "No disponible en estado salvaje en Johto. Conseguir mediante intercambio desde Pokémon Rojo, Azul o Amarillo (Cápsula del Tiempo, también obtenible mediante crianza)", "locations": [{"area": "Cápsula del Tiempo (Rojo/Azul/Amarillo)", "method": "Intercambio con cable link"}, {"area": "Ruta 34 (Guardería Pokémon)", "method": "Crianza de huevo"}]},
    5: {"type": "trade", "badge_label": "Intercambio", "badge_color": "sky", "summary": "Evoluciona de Charmander al nivel 16 (Transferir mediante Cápsula del Tiempo)", "locations": [{"area": "Cápsula del Tiempo (Rojo/Azul/Amarillo)", "method": "Intercambio con cable link"}]},
    6: {"type": "trade", "badge_label": "Intercambio", "badge_color": "sky", "summary": "Evoluciona de Charmeleon al nivel 36 (Transferir mediante Cápsula del Tiempo)", "locations": [{"area": "Cápsula del Tiempo (Rojo/Azul/Amarillo)", "method": "Intercambio con cable link"}]},
    7: {"type": "trade", "badge_label": "Intercambio", "badge_color": "sky", "summary": "No disponible en estado salvaje en Johto. Conseguir mediante intercambio desde Pokémon Rojo, Azul o Amarillo (Cápsula del Tiempo, también obtenible mediante crianza)", "locations": [{"area": "Cápsula del Tiempo (Rojo/Azul/Amarillo)", "method": "Intercambio con cable link"}, {"area": "Ruta 34 (Guardería Pokémon)", "method": "Crianza de huevo"}]},
    8: {"type": "trade", "badge_label": "Intercambio", "badge_color": "sky", "summary": "Evoluciona de Squirtle al nivel 16 (Transferir mediante Cápsula del Tiempo)", "locations": [{"area": "Cápsula del Tiempo (Rojo/Azul/Amarillo)", "method": "Intercambio con cable link"}]},
    9: {"type": "trade", "badge_label": "Intercambio", "badge_color": "sky", "summary": "Evoluciona de Wartortle al nivel 36 (Transferir mediante Cápsula del Tiempo)", "locations": [{"area": "Cápsula del Tiempo (Rojo/Azul/Amarillo)", "method": "Intercambio con cable link"}]},

    # 2. Concurso de Captura de Bichos (Parque Nacional)
    13: {"type": "contest", "badge_label": "Parque Nacional", "badge_color": "emerald", "summary": "Capturable en el Concurso de Captura de Bichos del Parque Nacional (Martes, Jueves y Sábado). También obtenible mediante crianza", "locations": [{"area": "Parque Nacional", "method": "Concurso de Captura de Bichos"}, {"area": "Ruta 34 (Guardería Pokémon)", "method": "Crianza de huevo"}]},
    123: {"type": "contest", "badge_label": "Parque Nacional", "badge_color": "emerald", "summary": "Capturable en el Concurso de Captura de Bichos del Parque Nacional (Martes, Jueves y Sábado). También obtenible mediante crianza", "locations": [{"area": "Parque Nacional", "method": "Concurso de Captura de Bichos"}, {"area": "Ruta 34 (Guardería Pokémon)", "method": "Crianza de huevo"}]},
    127: {"type": "contest", "badge_label": "Parque Nacional", "badge_color": "emerald", "summary": "Capturable en el Concurso de Captura de Bichos del Parque Nacional (Martes, Jueves y Sábado). También obtenible mediante crianza", "locations": [{"area": "Parque Nacional", "method": "Concurso de Captura de Bichos"}, {"area": "Ruta 34 (Guardería Pokémon)", "method": "Crianza de huevo"}]},

    # 3. Exclusivos de Pokémon Plata (no disponibles en Oro; requieren intercambio)
    37: {"type": "trade", "badge_label": "Intercambio", "badge_color": "sky", "summary": "Exclusivo de Pokémon Plata (obtenible mediante intercambio o crianza)", "locations": [{"area": "Edición Pokémon Plata", "method": "Intercambio con cable link"}, {"area": "Ruta 34 (Guardería Pokémon)", "method": "Crianza de huevo"}]},
    38: {"type": "trade", "badge_label": "Intercambio", "badge_color": "sky", "summary": "Evoluciona de Vulpix (Exclusivo de Pokémon Plata, obtenible mediante intercambio)", "locations": [{"area": "Edición Pokémon Plata", "method": "Intercambio con cable link"}]},
    52: {"type": "trade", "badge_label": "Intercambio", "badge_color": "sky", "summary": "Exclusivo de Pokémon Plata (obtenible mediante intercambio o crianza)", "locations": [{"area": "Edición Pokémon Plata", "method": "Intercambio con cable link"}, {"area": "Ruta 34 (Guardería Pokémon)", "method": "Crianza de huevo"}]},
    53: {"type": "trade", "badge_label": "Intercambio", "badge_color": "sky", "summary": "Evoluciona de Meowth (Exclusivo de Pokémon Plata, obtenible mediante intercambio)", "locations": [{"area": "Edición Pokémon Plata", "method": "Intercambio con cable link"}]},
    165: {"type": "trade", "badge_label": "Intercambio", "badge_color": "sky", "summary": "Exclusivo de Pokémon Plata (obtenible mediante intercambio o crianza)", "locations": [{"area": "Edición Pokémon Plata", "method": "Intercambio con cable link"}, {"area": "Ruta 34 (Guardería Pokémon)", "method": "Crianza de huevo"}]},
    166: {"type": "trade", "badge_label": "Intercambio", "badge_color": "sky", "summary": "Evoluciona de Ledyba (Exclusivo de Pokémon Plata, obtenible mediante intercambio)", "locations": [{"area": "Edición Pokémon Plata", "method": "Intercambio con cable link"}]},
    225: {"type": "trade", "badge_label": "Intercambio", "badge_color": "sky", "summary": "Exclusivo de Pokémon Plata (obtenible mediante intercambio o crianza)", "locations": [{"area": "Edición Pokémon Plata", "method": "Intercambio con cable link"}, {"area": "Ruta 34 (Guardería Pokémon)", "method": "Crianza de huevo"}]},
    227: {"type": "trade", "badge_label": "Intercambio", "badge_color": "sky", "summary": "Exclusivo de Pokémon Plata (obtenible mediante intercambio o crianza)", "locations": [{"area": "Edición Pokémon Plata", "method": "Intercambio con cable link"}, {"area": "Ruta 34 (Guardería Pokémon)", "method": "Crianza de huevo"}]},
    231: {"type": "trade", "badge_label": "Intercambio", "badge_color": "sky", "summary": "Exclusivo de Pokémon Plata (obtenible mediante intercambio o crianza)", "locations": [{"area": "Edición Pokémon Plata", "method": "Intercambio con cable link"}, {"area": "Ruta 34 (Guardería Pokémon)", "method": "Crianza de huevo"}]},
    232: {"type": "trade", "badge_label": "Intercambio", "badge_color": "sky", "summary": "Evoluciona de Phanpy (Exclusivo de Pokémon Plata, obtenible mediante intercambio)", "locations": [{"area": "Edición Pokémon Plata", "method": "Intercambio con cable link"}]},

    # 4. Intercambios dentro del juego (In-game trades)
    95: {"type": "trade_npc", "badge_label": "Intercambio NPC", "badge_color": "violet", "summary": "Intercambio en Ciudad Malva: entrega un Bellsprout a cambio de Onix (con el mote «Rocky»). También obtenible mediante crianza", "locations": [{"area": "Ciudad Malva (Casa Suroeste)", "method": "Intercambio por Bellsprout"}, {"area": "Ruta 34 (Guardería Pokémon)", "method": "Crianza de huevo"}]},
    66: {"type": "trade_npc", "badge_label": "Intercambio NPC", "badge_color": "violet", "summary": "Intercambio en el Centro Comercial de Ciudad Trigal (5P): entrega un Drowzee a cambio de Machop (con el mote «Musculín»). También obtenible mediante crianza", "locations": [{"area": "Ciudad Trigal (Centro Comercial 5P)", "method": "Intercambio por Drowzee"}, {"area": "Ruta 34 (Guardería Pokémon)", "method": "Crianza de huevo"}]},
    100: {"type": "trade_npc", "badge_label": "Intercambio NPC", "badge_color": "violet", "summary": "Intercambio en Ciudad Olivo: entrega un Krabby a cambio de Voltorb (con el mote «Volty»). También obtenible mediante crianza", "locations": [{"area": "Ciudad Olivo", "method": "Intercambio por Krabby"}, {"area": "Ruta 34 (Guardería Pokémon)", "method": "Crianza de huevo"}]},
    112: {"type": "trade_npc", "badge_label": "Intercambio NPC", "badge_color": "violet", "summary": "Intercambio en Ciudad Endrino: entrega un Dragonair hembra a cambio de Rhydon (con el mote «Don»)", "locations": [{"area": "Ciudad Endrino", "method": "Intercambio por Dragonair hembra"}]},
    142: {"type": "trade_npc", "badge_label": "Intercambio NPC", "badge_color": "violet", "summary": "Intercambio en la caseta de la Ruta 14: entrega una Chansey a cambio de Aerodactyl (con el mote «Aeris»). También obtenible mediante crianza", "locations": [{"area": "Ruta 14", "method": "Intercambio por Chansey"}, {"area": "Ruta 34 (Guardería Pokémon)", "method": "Crianza de huevo"}]},
    78: {"type": "trade_npc", "badge_label": "Intercambio NPC", "badge_color": "violet", "summary": "Intercambio en el Centro Pokémon de Ciudad Plateada: entrega un Gloom a cambio de Rapidash (con el mote «Galope»)", "locations": [{"area": "Ciudad Plateada", "method": "Intercambio por Gloom"}]},

    # 5. Regalos especiales de NPCs y eventos clave
    175: {"type": "gift", "badge_label": "Huevo Regalo", "badge_color": "emerald", "summary": "Eclosiona del Huevo Misterioso entregado por el ayudante del Profesor Elm en el Centro Pokémon de Ciudad Malva (también obtenible mediante crianza)", "locations": [{"area": "Ciudad Malva", "method": "Huevo del ayudante de Elm"}, {"area": "Ruta 34 (Guardería Pokémon)", "method": "Crianza de huevo"}]},
    21: {"type": "gift", "badge_label": "Regalo", "badge_color": "emerald", "summary": "Entregado por el guardia de la Caseta Norte de Ciudad Trigal con una carta para la Ruta 31 (con el mote «Kenya»). También obtenible salvaje o mediante crianza", "locations": [{"area": "Ciudad Trigal (Caseta Norte)", "method": "Regalo de guardia"}, {"area": "Ruta 34 (Guardería Pokémon)", "method": "Crianza de huevo"}]},
    213: {"type": "gift", "badge_label": "Regalo", "badge_color": "emerald", "summary": "Entregado como regalo temporal por Manía en Ciudad Orquídea (con el mote «Shuckie»). También obtenible mediante crianza", "locations": [{"area": "Ciudad Orquídea (Casa de Manía)", "method": "Regalo de Manía"}, {"area": "Ruta 34 (Guardería Pokémon)", "method": "Crianza de huevo"}]},
    236: {"type": "gift", "badge_label": "Premio Kárate", "badge_color": "emerald", "summary": "Entregado por el Rey Kárate (Kiyo) en lo profundo del Monte Mortero (B1F) tras vencerle en combate. También obtenible mediante crianza o del Huevo Extraño en la Guardería Pokémon", "locations": [{"area": "Monte Mortero (Sótano)", "method": "Premio tras vencer al Rey Kárate"}, {"area": "Ruta 34 (Guardería Pokémon)", "method": "Crianza de huevo"}, {"area": "Ruta 34 (Guardería Pokémon)", "method": "Huevo Extraño (Regalo con alta probabilidad de variocolor)"}]},

    # 6. Fósiles de Kanto no disponibles en Gen 2 (Cápsula del Tiempo)
    138: {"type": "trade", "badge_label": "Intercambio", "badge_color": "sky", "summary": "No disponible en estado salvaje ni fósil en Johto. Conseguir mediante intercambio desde Gen 1 (también obtenible mediante crianza)", "locations": [{"area": "Cápsula del Tiempo (Rojo/Azul/Amarillo)", "method": "Intercambio con cable link"}, {"area": "Ruta 34 (Guardería Pokémon)", "method": "Crianza de huevo"}]},
    139: {"type": "evolution", "badge_label": "Evolución", "badge_color": "indigo", "summary": "Evoluciona de Omanyte al nivel 40"},
    140: {"type": "trade", "badge_label": "Intercambio", "badge_color": "sky", "summary": "No disponible en estado salvaje ni fósil en Johto. Conseguir mediante intercambio desde Gen 1 (también obtenible mediante crianza)", "locations": [{"area": "Cápsula del Tiempo (Rojo/Azul/Amarillo)", "method": "Intercambio con cable link"}, {"area": "Ruta 34 (Guardería Pokémon)", "method": "Crianza de huevo"}]},
    141: {"type": "evolution", "badge_label": "Evolución", "badge_color": "indigo", "summary": "Evoluciona de Kabuto al nivel 40"},

    # 7. Legendarios de Kanto (Cápsula del Tiempo)
    144: {"type": "trade", "badge_label": "Intercambio", "badge_color": "sky", "is_unique": True, "summary": "No disponible en Johto. Conseguir mediante intercambio desde Pokémon Rojo, Azul o Amarillo (Cápsula del Tiempo)", "locations": [{"area": "Cápsula del Tiempo (Rojo/Azul/Amarillo)", "method": "Intercambio con cable link"}]},
    145: {"type": "trade", "badge_label": "Intercambio", "badge_color": "sky", "is_unique": True, "summary": "No disponible en Johto. Conseguir mediante intercambio desde Pokémon Rojo, Azul o Amarillo (Cápsula del Tiempo)", "locations": [{"area": "Cápsula del Tiempo (Rojo/Azul/Amarillo)", "method": "Intercambio con cable link"}]},
    146: {"type": "trade", "badge_label": "Intercambio", "badge_color": "sky", "is_unique": True, "summary": "No disponible en Johto. Conseguir mediante intercambio desde Pokémon Rojo, Azul o Amarillo (Cápsula del Tiempo)", "locations": [{"area": "Cápsula del Tiempo (Rojo/Azul/Amarillo)", "method": "Intercambio con cable link"}]},
    150: {"type": "trade", "badge_label": "Intercambio", "badge_color": "sky", "is_unique": True, "summary": "No disponible en Johto. Conseguir mediante intercambio desde Pokémon Rojo, Azul o Amarillo (Cápsula del Tiempo)", "locations": [{"area": "Cápsula del Tiempo (Rojo/Azul/Amarillo)", "method": "Intercambio con cable link"}]},
    151: {"type": "mythical", "badge_label": "Mítico / Evento", "badge_color": "violet", "is_unique": True, "summary": "Distribución oficial de Nintendo mediante evento especial (o transferir desde Gen 1)", "locations": [{"area": "Evento Nintendo", "method": "Distribución especial"}]},

    # 8. Encuentros estáticos únicos y legendarios de Johto
    130: {"type": "special", "badge_label": "Encuentro Variocolor", "badge_color": "rose", "is_unique": False, "summary": "Encuentro variocolor garantizado en el centro del Lago de la Furia (Gyarados Rojo a nivel 30). También disponible salvaje (pesca y surf) y mediante evolución de Magikarp", "locations": [{"area": "Lago de la Furia", "method": "Encuentro Especial (Gyarados Rojo variocolor garantizado)"}, {"area": "Lago de la Furia", "method": "Caña Buena, Súper Caña, Surf"}, {"area": "Ciudad Fucsia", "method": "Caña Buena, Súper Caña"}]},
    131: {"type": "special", "badge_label": "Estático", "badge_color": "emerald", "summary": "Aparece cada viernes en el nivel inferior de la Cueva Unión (Sótano 2). También obtenible mediante crianza", "locations": [{"area": "Cueva Unión (Sótano 2)", "method": "Aparición fija los viernes"}, {"area": "Ruta 34 (Guardería Pokémon)", "method": "Crianza de huevo"}]},
    143: {"type": "special", "badge_label": "Estático", "badge_color": "rose", "summary": "Durmiendo en Ciudad Carmín bloqueando la Cueva Diglett. Sintonizar la Poké Flauta en el PokéGear para despertarlo (también obtenible mediante crianza)", "locations": [{"area": "Ciudad Carmín (Cueva Diglett)", "method": "Sintonizar Poké Flauta en PokéGear"}, {"area": "Ruta 34 (Guardería Pokémon)", "method": "Crianza de huevo"}]},
    185: {"type": "special", "badge_label": "Estático", "badge_color": "rose", "summary": "Pokémon que bloquea la intersección de la Ruta 36 con forma de árbol. Usar la Regadera para combatir (también obtenible mediante crianza)", "locations": [{"area": "Ruta 36", "method": "Usar Regadera"}, {"area": "Ruta 34 (Guardería Pokémon)", "method": "Crianza de huevo"}]},
    243: {"type": "legendary", "badge_label": "Legendario Errante", "badge_color": "rose", "is_unique": True, "summary": "Bestia legendaria que recorre las rutas de Johto de forma aleatoria tras ser liberada en la Torre Quemada", "locations": [{"area": "En movimiento por Johto", "method": "Legendario errante en hierba"}]},
    244: {"type": "legendary", "badge_label": "Legendario Errante", "badge_color": "rose", "is_unique": True, "summary": "Bestia legendaria que recorre las rutas de Johto de forma aleatoria tras ser liberada en la Torre Quemada", "locations": [{"area": "En movimiento por Johto", "method": "Legendario errante en hierba"}]},
    245: {"type": "legendary", "badge_label": "Legendario Errante", "badge_color": "rose", "is_unique": True, "summary": "Bestia legendaria que recorre las rutas de Johto de forma aleatoria tras ser liberada en la Torre Quemada", "locations": [{"area": "En movimiento por Johto", "method": "Legendario errante en hierba"}]},
    249: {"type": "legendary", "badge_label": "Legendario", "badge_color": "rose", "is_unique": True, "summary": "En lo profundo de las Islas Remolino (Sótano 2) a nivel 70 tras obtener el Ala Plateada", "locations": [{"area": "Islas Remolino (Sótano 2)", "method": "Encuentro Legendario (Ala Plateada)"}]},
    250: {"type": "legendary", "badge_label": "Legendario", "badge_color": "rose", "is_unique": True, "summary": "En el tejado de la Torre Hojalata a nivel 40 tras obtener el Ala Arcoíris", "locations": [{"area": "Torre Hojalata (Tejado)", "method": "Encuentro Legendario (Ala Arcoíris)"}]},
    251: {"type": "mythical", "badge_label": "Mítico / Evento", "badge_color": "violet", "is_unique": True, "summary": "Guardián del bosque obtenible mediante evento especial oficial (GS Ball en el altar del Encinar)", "locations": [{"area": "Encinar (Altar del Bosque)", "method": "Evento GS Ball"}]},
}

SILVER_SPECIAL_CASES: Dict[int, Dict[str, Any]] = {
    **{k: v for k, v in GOLD_SPECIAL_CASES.items() if k not in [13, 37, 38, 52, 53, 165, 166, 225, 227, 231, 232, 249, 250]},
    # Parque Nacional en Plata (Caterpie es exclusivo del concurso, mientras Weedle es salvaje)
    10: {"type": "contest", "badge_label": "Parque Nacional", "badge_color": "emerald", "summary": "Capturable en el Concurso de Captura de Bichos del Parque Nacional (Martes, Jueves y Sábado). También obtenible mediante crianza", "locations": [{"area": "Parque Nacional", "method": "Concurso de Captura de Bichos"}, {"area": "Ruta 34 (Guardería Pokémon)", "method": "Crianza de huevo"}]},
    # Exclusivos de Pokémon Oro (obtenibles mediante intercambio o crianza en Plata)
    56: {"type": "trade", "badge_label": "Intercambio", "badge_color": "sky", "summary": "Exclusivo de Pokémon Oro (obtenible mediante intercambio o crianza)", "locations": [{"area": "Edición Pokémon Oro", "method": "Intercambio con cable link"}, {"area": "Ruta 34 (Guardería Pokémon)", "method": "Crianza de huevo"}]},
    57: {"type": "trade", "badge_label": "Intercambio", "badge_color": "sky", "summary": "Evoluciona de Mankey (Exclusivo de Pokémon Oro, obtenible mediante intercambio)", "locations": [{"area": "Edición Pokémon Oro", "method": "Intercambio con cable link"}]},
    58: {"type": "trade", "badge_label": "Intercambio", "badge_color": "sky", "summary": "Exclusivo de Pokémon Oro (obtenible mediante intercambio o crianza)", "locations": [{"area": "Edición Pokémon Oro", "method": "Intercambio con cable link"}, {"area": "Ruta 34 (Guardería Pokémon)", "method": "Crianza de huevo"}]},
    59: {"type": "trade", "badge_label": "Intercambio", "badge_color": "sky", "summary": "Evoluciona de Growlithe (Exclusivo de Pokémon Oro, obtenible mediante intercambio)", "locations": [{"area": "Edición Pokémon Oro", "method": "Intercambio con cable link"}]},
    167: {"type": "trade", "badge_label": "Intercambio", "badge_color": "sky", "summary": "Exclusivo de Pokémon Oro (obtenible mediante intercambio o crianza)", "locations": [{"area": "Edición Pokémon Oro", "method": "Intercambio con cable link"}, {"area": "Ruta 34 (Guardería Pokémon)", "method": "Crianza de huevo"}]},
    168: {"type": "trade", "badge_label": "Intercambio", "badge_color": "sky", "summary": "Evoluciona de Spinarak (Exclusivo de Pokémon Oro, obtenible mediante intercambio)", "locations": [{"area": "Edición Pokémon Oro", "method": "Intercambio con cable link"}]},
    207: {"type": "trade", "badge_label": "Intercambio", "badge_color": "sky", "summary": "Exclusivo de Pokémon Oro (obtenible mediante intercambio o crianza)", "locations": [{"area": "Edición Pokémon Oro", "method": "Intercambio con cable link"}, {"area": "Ruta 34 (Guardería Pokémon)", "method": "Crianza de huevo"}]},
    216: {"type": "trade", "badge_label": "Intercambio", "badge_color": "sky", "summary": "Exclusivo de Pokémon Oro (obtenible mediante intercambio o crianza)", "locations": [{"area": "Edición Pokémon Oro", "method": "Intercambio con cable link"}, {"area": "Ruta 34 (Guardería Pokémon)", "method": "Crianza de huevo"}]},
    217: {"type": "trade", "badge_label": "Intercambio", "badge_color": "sky", "summary": "Evoluciona de Teddiursa (Exclusivo de Pokémon Oro, obtenible mediante intercambio)", "locations": [{"area": "Edición Pokémon Oro", "method": "Intercambio con cable link"}]},
    226: {"type": "trade", "badge_label": "Intercambio", "badge_color": "sky", "summary": "Exclusivo de Pokémon Oro (obtenible mediante intercambio o crianza)", "locations": [{"area": "Edición Pokémon Oro", "method": "Intercambio con cable link"}, {"area": "Ruta 34 (Guardería Pokémon)", "method": "Crianza de huevo"}]},
    # Inversión de niveles para legendarios en Plata
    249: {"type": "legendary", "badge_label": "Legendario", "badge_color": "rose", "is_unique": True, "summary": "En lo profundo de las Islas Remolino (Sótano 2) a nivel 40 tras obtener el Ala Plateada", "locations": [{"area": "Islas Remolino (Sótano 2)", "method": "Encuentro Legendario (Ala Plateada)"}]},
    250: {"type": "legendary", "badge_label": "Legendario", "badge_color": "rose", "is_unique": True, "summary": "En el tejado de la Torre Hojalata a nivel 70 tras obtener el Ala Arcoíris", "locations": [{"area": "Torre Hojalata (Tejado)", "method": "Encuentro Legendario (Ala Arcoíris)"}]},
}

# Esqueletos preparados para siguientes juegos de la franquicia
CRYSTAL_SPECIAL_CASES: Dict[int, Dict[str, Any]] = {
    # Encuentro variocolor garantizado en el Lago de la Furia
    130: {
        "type": "special",
        "badge_label": "Encuentro Variocolor",
        "badge_color": "rose",
        "is_unique": False,
        "summary": "Encuentro variocolor garantizado en el centro del Lago de la Furia (Gyarados Rojo a nivel 30). También disponible salvaje (pesca y surf) y mediante evolución de Magikarp",
        "locations": [
            {"area": "Lago de la Furia", "method": "Encuentro Especial (Gyarados Rojo variocolor garantizado)"},
            {"area": "Lago de la Furia", "method": "Caña Buena, Súper Caña, Surf"},
            {"area": "Ciudad Fucsia", "method": "Caña Buena, Súper Caña"},
        ]
    },
}
RUBY_SPECIAL_CASES: Dict[int, Dict[str, Any]] = {}
SAPPHIRE_SPECIAL_CASES: Dict[int, Dict[str, Any]] = {}
EMERALD_SPECIAL_CASES: Dict[int, Dict[str, Any]] = {}
FIRERED_SPECIAL_CASES: Dict[int, Dict[str, Any]] = {}
LEAFGREEN_SPECIAL_CASES: Dict[int, Dict[str, Any]] = {}
DIAMOND_SPECIAL_CASES: Dict[int, Dict[str, Any]] = {}
PEARL_SPECIAL_CASES: Dict[int, Dict[str, Any]] = {}
PLATINUM_SPECIAL_CASES: Dict[int, Dict[str, Any]] = {}
HEARTGOLD_SPECIAL_CASES: Dict[int, Dict[str, Any]] = {}
SOULSILVER_SPECIAL_CASES: Dict[int, Dict[str, Any]] = {}
BLACK_SPECIAL_CASES: Dict[int, Dict[str, Any]] = {}
WHITE_SPECIAL_CASES: Dict[int, Dict[str, Any]] = {}
BLACK_2_SPECIAL_CASES: Dict[int, Dict[str, Any]] = {}
WHITE_2_SPECIAL_CASES: Dict[int, Dict[str, Any]] = {}
X_SPECIAL_CASES: Dict[int, Dict[str, Any]] = {}
Y_SPECIAL_CASES: Dict[int, Dict[str, Any]] = {}
OMEGA_RUBY_SPECIAL_CASES: Dict[int, Dict[str, Any]] = {}
ALPHA_SAPPHIRE_SPECIAL_CASES: Dict[int, Dict[str, Any]] = {}
SUN_SPECIAL_CASES: Dict[int, Dict[str, Any]] = {}
MOON_SPECIAL_CASES: Dict[int, Dict[str, Any]] = {}
ULTRA_SUN_SPECIAL_CASES: Dict[int, Dict[str, Any]] = {}
ULTRA_MOON_SPECIAL_CASES: Dict[int, Dict[str, Any]] = {}
LETS_GO_PIKACHU_SPECIAL_CASES: Dict[int, Dict[str, Any]] = {}
LETS_GO_EEVEE_SPECIAL_CASES: Dict[int, Dict[str, Any]] = {}
SWORD_SPECIAL_CASES: Dict[int, Dict[str, Any]] = {}
SHIELD_SPECIAL_CASES: Dict[int, Dict[str, Any]] = {}
BRILLIANT_DIAMOND_SPECIAL_CASES: Dict[int, Dict[str, Any]] = {}
SHINING_PEARL_SPECIAL_CASES: Dict[int, Dict[str, Any]] = {}
LEGENDS_ARCEUS_SPECIAL_CASES: Dict[int, Dict[str, Any]] = {}
SCARLET_SPECIAL_CASES: Dict[int, Dict[str, Any]] = {}
VIOLET_SPECIAL_CASES: Dict[int, Dict[str, Any]] = {}

# Registro modular de casos especiales indexado por versión de juego
GAME_SPECIAL_CASES: Dict[str, Dict[int, Dict[str, Any]]] = {
    # Gen 1
    'red': RED_SPECIAL_CASES,
    'blue': BLUE_SPECIAL_CASES,
    'yellow': YELLOW_SPECIAL_CASES,
    # Gen 2
    'gold': GOLD_SPECIAL_CASES,
    'silver': SILVER_SPECIAL_CASES,
    'crystal': CRYSTAL_SPECIAL_CASES,
    # Gen 3
    'ruby': RUBY_SPECIAL_CASES,
    'sapphire': SAPPHIRE_SPECIAL_CASES,
    'emerald': EMERALD_SPECIAL_CASES,
    'firered': FIRERED_SPECIAL_CASES,
    'leafgreen': LEAFGREEN_SPECIAL_CASES,
    # Gen 4
    'diamond': DIAMOND_SPECIAL_CASES,
    'pearl': PEARL_SPECIAL_CASES,
    'platinum': PLATINUM_SPECIAL_CASES,
    'heartgold': HEARTGOLD_SPECIAL_CASES,
    'soulsilver': SOULSILVER_SPECIAL_CASES,
    # Gen 5
    'black': BLACK_SPECIAL_CASES,
    'white': WHITE_SPECIAL_CASES,
    'black-2': BLACK_2_SPECIAL_CASES,
    'white-2': WHITE_2_SPECIAL_CASES,
    # Gen 6
    'x': X_SPECIAL_CASES,
    'y': Y_SPECIAL_CASES,
    'omega-ruby': OMEGA_RUBY_SPECIAL_CASES,
    'alpha-sapphire': ALPHA_SAPPHIRE_SPECIAL_CASES,
    # Gen 7
    'sun': SUN_SPECIAL_CASES,
    'moon': MOON_SPECIAL_CASES,
    'ultra-sun': ULTRA_SUN_SPECIAL_CASES,
    'ultra-moon': ULTRA_MOON_SPECIAL_CASES,
    'lets-go-pikachu': LETS_GO_PIKACHU_SPECIAL_CASES,
    'lets-go-eevee': LETS_GO_EEVEE_SPECIAL_CASES,
    # Gen 8
    'sword': SWORD_SPECIAL_CASES,
    'shield': SHIELD_SPECIAL_CASES,
    'brilliant-diamond': BRILLIANT_DIAMOND_SPECIAL_CASES,
    'shining-pearl': SHINING_PEARL_SPECIAL_CASES,
    'legends-arceus': LEGENDS_ARCEUS_SPECIAL_CASES,
    # Gen 9
    'scarlet': SCARLET_SPECIAL_CASES,
    'violet': VIOLET_SPECIAL_CASES,
}

def clean_location_name(area_slug: str) -> str:
    """Convierte el slug de un área a un nombre amigable en español."""
    if area_slug in ALL_LOCATION_NAMES_ES:
        return ALL_LOCATION_NAMES_ES[area_slug]
    if area_slug in KANTO_LOCATION_NAMES_ES:
        return KANTO_LOCATION_NAMES_ES[area_slug]
    if area_slug in JOHTO_LOCATION_NAMES_ES:
        return JOHTO_LOCATION_NAMES_ES[area_slug]

    m_route = re.match(r"(?:johto-|kanto-|hoenn-|sinnoh-|unova-|kalos-|alola-|galar-|paldea-)?(?:sea-)?route-(\d+)", area_slug)
    if m_route:
        return f"Ruta {m_route.group(1)}"

    # Monumentos y cuevas de Kanto y Johto
    if "mt-moon" in area_slug:
        return "Monte Moon"
    if "rock-tunnel" in area_slug:
        return "Túnel Roca"
    if "seafoam-islands" in area_slug:
        return "Islas Espuma"
    if "safari-zone" in area_slug:
        return "Zona Safari"
    if "cerulean-cave" in area_slug:
        return "Cueva Celeste"
    if "victory-road" in area_slug:
        return "Calle Victoria"
    if "pokemon-tower" in area_slug:
        return "Torre Pokémon"
    if "pokemon-mansion" in area_slug:
        return "Mansión Pokémon"
    if "sprout-tower" in area_slug:
        return "Torre Bellsprout"
    if "burned-tower" in area_slug:
        return "Torre Quemada"
    if "bell-tower" in area_slug or "tin-tower" in area_slug:
        return "Torre Hojalata"
    if "whirl-islands" in area_slug:
        return "Islas Remolino"
    if "mt-mortar" in area_slug:
        return "Monte Mortero"
    if "mt-silver" in area_slug:
        return "Monte Plateado"
    if "slowpoke-well" in area_slug:
        return "Pozo Slowpoke"
    if "union-cave" in area_slug:
        return "Cueva Unión"
    if "dark-cave" in area_slug:
        return "Cueva Oscura"
    if "ice-path" in area_slug:
        return "Ruta Helada"
    if "dragons-den" in area_slug:
        return "Guarida Dragón"
    if "ruins-of-alph" in area_slug:
        return "Ruinas Alfa"
    if "national-park" in area_slug:
        return "Parque Nacional"
    if "ilex-forest" in area_slug:
        return "Encinar"
    if "lake-of-rage" in area_slug:
        return "Lago de la Furia"
    if "tohjo-falls" in area_slug:
        return "Cataratas Tohjo"
    if "team-rocket-hq" in area_slug:
        return "Guarida del Team Rocket"
    if "prize-corner" in area_slug or "game-corner" in area_slug:
        if "goldenrod" in area_slug or "trigal" in area_slug:
            return "Ciudad Trigal (Casino)"
        if "mauville" in area_slug or "malvalona" in area_slug:
            return "Ciudad Malvalona (Casino)"
        return "Ciudad Azulona (Casino)"
    if "cinnabar-lab" in area_slug:
        return "Isla Canela (Laboratorio)"
    if "underground-path" in area_slug:
        return "Vía Subterránea"

    clean = area_slug.replace("kanto-", "").replace("johto-", "").replace("-area", "").replace("-", " ")
    return clean.title()


# Identificadores de biomas y entornos de cuevas e interiores (Kanto, Johto y regiones futuras)
CAVE_SLUGS = {
    # Kanto
    'mt-moon', 'rock-tunnel', 'seafoam-islands', 'cerulean-cave', 'digletts-cave', 'victory-road',
    # Johto
    'dark-cave', 'union-cave', 'slowpoke-well', 'ice-path', 'dragons-den',
    'mt-mortar', 'mt-silver', 'whirl-islands', 'tohjo-falls', 'ruins-of-alph',
    # Genéricas
    'cave', 'tunnel', 'falls', 'grotto'
}

INTERIOR_SLUGS = {
    # Kanto
    'pokemon-tower', 'pokemon-mansion', 'power-plant',
    # Johto
    'sprout-tower', 'bell-tower', 'tin-tower', 'burned-tower', 'team-rocket-hq', 'radio-tower', 'department-store'
}

KANTO_CAVE_SLUGS = CAVE_SLUGS
KANTO_INTERIOR_SLUGS = INTERIOR_SLUGS


def get_casino_name(area_str: str, game_slug: str = "", is_wild_combined: bool = False) -> str:
    """Retorna el nombre oficial del Casino contextualizado según localidad y versión."""
    area_lower = area_str.lower()
    if "trigal" in area_lower or "goldenrod" in area_lower:
        return "Casino de Ciudad Trigal"
    if "azulona" in area_lower or "celadon" in area_lower:
        if game_slug in ['red', 'blue', 'yellow'] and not is_wild_combined:
            return "Casino Rocket de Ciudad Azulona"
        return "Casino de Ciudad Azulona"
    if "malvalona" in area_lower or "mauville" in area_lower:
        return "Casino de Ciudad Malvalona"
    if "rocavelo" in area_lower or "veilstone" in area_lower:
        return "Casino de Ciudad Rocavelo"
    return "Casino"


# Catálogo oficial de precios de fichas del Casino por juego
GAME_CASINO_PRIZES: Dict[str, Dict[int, int]] = {
    'red': {
        63: 180,     # Abra
        35: 500,     # Clefairy
        30: 1200,    # Nidorina
        147: 2800,   # Dratini
        123: 5500,   # Scyther
        137: 9999,   # Porygon
    },
    'blue': {
        63: 120,     # Abra
        35: 750,     # Clefairy
        32: 1200,    # Nidoran ♂
        33: 1200,    # Nidorino
        127: 2500,   # Pinsir
        147: 4600,   # Dratini
        137: 6500,   # Porygon
    },
    'yellow': {
        63: 230,     # Abra
        37: 1000,    # Vulpix
        40: 2680,    # Wigglytuff
        123: 6500,   # Scyther
        127: 6500,   # Pinsir
        137: 9999,   # Porygon
    },
    'gold': {
        63: 200,     # Abra (Casino Ciudad Trigal)
        23: 700,     # Ekans (Casino Ciudad Trigal)
        147: 2100,   # Dratini (Casino Ciudad Trigal)
        122: 3333,   # Mr. Mime (Casino Ciudad Azulona)
        133: 6666,   # Eevee (Casino Ciudad Azulona)
        137: 9999,   # Porygon (Casino Ciudad Azulona)
    },
    'silver': {
        63: 200,     # Abra (Casino Ciudad Trigal)
        27: 700,     # Sandshrew (Casino Ciudad Trigal)
        147: 2100,   # Dratini (Casino Ciudad Trigal)
        122: 3333,   # Mr. Mime (Casino Ciudad Azulona)
        133: 6666,   # Eevee (Casino Ciudad Azulona)
        137: 9999,   # Porygon (Casino Ciudad Azulona)
    },
    'crystal': {
        63: 100,     # Abra
        220: 700,    # Swinub
        147: 2100,   # Dratini
        25: 2222,    # Pikachu
        137: 5555,   # Porygon
        246: 8888,   # Larvitar
    },
    'ruby': {},
    'sapphire': {},
    'emerald': {},
    'firered': {
        63: 180,
        35: 500,
        147: 2800,
        123: 5500,
        137: 9999,
    },
    'leafgreen': {
        63: 120,
        35: 750,
        127: 2500,
        147: 4600,
        137: 6500,
    },
    'diamond': {},
    'pearl': {},
    'platinum': {},
    'heartgold': {
        63: 200, 23: 700, 147: 2100, 122: 3333, 133: 6666, 137: 9999,
    },
    'soulsilver': {
        63: 200, 27: 700, 147: 2100, 122: 3333, 133: 6666, 137: 9999,
    },
}


def resolve_encounter_method_label(
    method_slug: str,
    area_slug: str,
    game_slug: str = 'red',
    national_number: Optional[int] = None
) -> str:
    """
    Traduce el método de encuentro al español contextualizado según el bioma del área y la versión del juego.
    """
    m_clean = method_slug.lower()
    if 'prize-corner' in area_slug or 'game-corner' in area_slug:
        if national_number:
            coins = GAME_CASINO_PRIZES.get(game_slug, {}).get(national_number)
            if coins:
                formatted = f"{coins:,}".replace(",", ".")
                return f"Canje de fichas ({formatted})"
        return "Premio del Casino"

    if m_clean == 'walk':
        # Cuevas de Kanto/Johto (suelo de roca/gruta sin hierba)
        if any(c in area_slug for c in CAVE_SLUGS):
            return "Cueva"
        # Interiores de edificios / estructuras
        if any(b in area_slug for b in INTERIOR_SLUGS):
            return "Interior"
        # Rutas y exteriores naturales
        return "Hierba alta"

    if m_clean == 'npc-trade':
        return "Intercambio NPC"
    if m_clean == 'static':
        return "Estático"

    return ENCOUNTER_METHODS_ES.get(m_clean, method_slug.title())



def find_evolution_details(
    chain_node: Dict[str, Any],
    target_species_name: str,
    parent_name: Optional[str] = None,
    parent_id: Optional[int] = None
) -> Optional[Dict[str, Any]]:
    """Recorre recursivamente un árbol de evolución de PokeAPI buscando al Pokémon objetivo."""
    current_species = chain_node.get("species", {}).get("name", "")
    current_url = chain_node.get("species", {}).get("url", "")
    current_id = None
    if current_url:
        try:
            current_id = int(current_url.rstrip("/").split("/")[-1])
        except (ValueError, IndexError):
            pass

    if current_species == target_species_name:
        evo_details_list = chain_node.get("evolution_details", [])
        return {
            "parent_name": parent_name,
            "parent_id": parent_id,
            "details": evo_details_list[0] if evo_details_list else {}
        }

    for child in chain_node.get("evolves_to", []):
        res = find_evolution_details(child, target_species_name, parent_name=current_species, parent_id=current_id)
        if res:
            return res

    return None


def resolve_obtaining_info(
    national_number: int,
    pokemon_name: str,
    game_slug: str,
    encounters_data: Optional[List[Dict[str, Any]]] = None,
    evolution_chain_data: Optional[Dict[str, Any]] = None,
    generation: int = 1
) -> Dict[str, Any]:
    """
    Determina de forma estructurada cómo se obtiene el Pokémon en la versión especificada.
    Deduplica áreas, verifica iniciales aislados por juego, casos especiales curados,
    y filtra pre-evoluciones anacrónicas según la generación del juego.
    """
    # 1. Comprobar si el Pokémon proviene de una evolución previa en el árbol evolutivo
    evolution_info = None
    if evolution_chain_data:
        chain_root = evolution_chain_data.get("chain", {})
        evo_res = find_evolution_details(chain_root, pokemon_name.lower())

        if evo_res and evo_res.get("parent_name"):
            parent_id = evo_res.get("parent_id")
            max_gen_id = MAX_NATIONAL_NUMBER_BY_GEN.get(generation, 9999)

            # Si la pre-evolución pertenece a una generación posterior al juego actual (ej. Tyrogue en Gen 1),
            # no se considera una evolución válida para esta edición histórica.
            if not (parent_id and parent_id > max_gen_id):
                parent = evo_res["parent_name"].replace("-", " ").title()
                details = evo_res.get("details", {})
                trigger = details.get("trigger", {}).get("name", "")

                condition = ""
                item_slug = None
                item_name = None
                item_icon = None

                if trigger == "level-up":
                    min_lvl = details.get("min_level")
                    min_happ = details.get("min_happiness")
                    rel_stats = details.get("relative_physical_stats")

                    stat_cond = ""
                    if rel_stats == 1 or (parent == "Tyrogue" and national_number == 106):
                        stat_cond = " si Ataque > Defensa"
                    elif rel_stats == -1 or (parent == "Tyrogue" and national_number == 107):
                        stat_cond = " si Defensa > Ataque"
                    elif rel_stats == 0 or (parent == "Tyrogue" and national_number == 237):
                        stat_cond = " si Ataque = Defensa"

                    if min_lvl:
                        condition = f"Nivel {min_lvl}{stat_cond}"
                    elif min_happ:
                        condition = f"Felicidad alta{stat_cond}"
                    elif stat_cond:
                        condition = f"Subir de nivel{stat_cond}"
                    else:
                        condition = "Subir de nivel"
                elif trigger == "use-item":
                    item_slug = details.get("item", {}).get("name", "")
                    item_name = EVOLUTION_ITEMS_ES.get(item_slug, item_slug.title())
                    condition = f"usando {item_name}"
                    item_icon = f"/media/items/{item_slug}.png" if item_slug else None
                elif trigger == "trade":
                    held_item = details.get("held_item")
                    if held_item:
                        item_slug = held_item.get("name", "")
                        item_name = EVOLUTION_ITEMS_ES.get(item_slug, item_slug.title())
                        item_icon = f"/media/items/{item_slug}.png" if item_slug else None
                        condition = f"Intercambio equipado con {item_name}"
                    else:
                        condition = "Intercambio con otro entrenador"
                else:
                    condition = "Evolución especial"

                evo_summary = f"Evoluciona de {parent}"
                if condition:
                    if condition.startswith("Nivel") or condition.startswith("usando") or condition.startswith("Intercambio"):
                        evo_summary += f" ({condition})" if not condition.startswith("usando") else f" {condition}"
                    else:
                        evo_summary += f" ({condition})"

                evolution_info = {
                    "from": parent,
                    "trigger": trigger,
                    "condition": condition,
                    "text": evo_summary,
                    "item_slug": item_slug,
                    "item_name": item_name,
                    "item_icon": item_icon,
                }

    # 2. Comprobar si es un Pokémon inicial oficial para este juego específico
    starters_game = STARTERS_BY_GAME.get(game_slug, {})
    if national_number in starters_game:
        starter_data = dict(starters_game[national_number])
        starter_data["evolution_info"] = evolution_info
        return starter_data

    # 3. Casos especiales curados por juego (ej. Pokémon Rojo)
    special_cases_game = GAME_SPECIAL_CASES.get(game_slug, {})
    if national_number in special_cases_game:
        special_data = dict(special_cases_game[national_number])
        if evolution_info:
            special_data["evolution_info"] = evolution_info
        return special_data

    # 4. Encuentros salvajes / directos registrados en PokeAPI para este juego (agrupados por área limpia)
    locations_by_area: Dict[str, set] = {}
    has_gift_encounter = False

    if encounters_data:
        for area_item in encounters_data:
            area_slug = area_item.get("location_area", {}).get("name", "")
            version_details = area_item.get("version_details", [])

            for vd in version_details:
                if vd.get("version", {}).get("name") == game_slug:
                    enc_details = vd.get("encounter_details", [])
                    methods = set()
                    for ed in enc_details:
                        m_name = ed.get("method", {}).get("name", "")
                        methods.add(m_name)
                        if m_name == "gift":
                            has_gift_encounter = True

                    clean_area = clean_location_name(area_slug)
                    method_labels = {resolve_encounter_method_label(m, area_slug, game_slug, national_number) for m in methods}
                    if clean_area not in locations_by_area:
                        locations_by_area[clean_area] = set()
                    locations_by_area[clean_area].update(method_labels)

    # Convertir a lista deduplicada
    game_locations = []
    for area, methods_set in locations_by_area.items():
        sorted_methods = sorted(list(methods_set))
        game_locations.append({
            "area": area,
            "method": ", ".join(sorted_methods) if sorted_methods else "Encuentro salvaje"
        })

    if game_locations:
        if has_gift_encounter and len(game_locations) == 1:
            loc = game_locations[0]
            can_breed = (
                generation >= 2
                and evolution_info is None
                and national_number not in NON_HATCHABLE_SPECIES
            )
            daycare_area = DAYCARE_LOCATIONS_BY_GAME.get(game_slug)
            locs = [loc]
            summary_breed = ""
            if can_breed and daycare_area:
                locs.append({
                    "area": daycare_area,
                    "method": "Crianza de huevo"
                })
                summary_breed = " (también obtenible mediante crianza)"

            if "Casino" in loc['area']:
                coins = GAME_CASINO_PRIZES.get(game_slug, {}).get(national_number)
                coins_str = f" por {coins:,} fichas".replace(",", ".") if coins else ""
                casino_name = get_casino_name(loc['area'], game_slug)
                return {
                    "type": "casino",
                    "badge_label": "Premio Casino",
                    "badge_color": "amber",
                    "summary": f"Canjeable{coins_str} en el {casino_name}{summary_breed}",
                    "locations": locs,
                    "evolution_info": evolution_info
                }
            return {
                "type": "gift",
                "badge_label": "Regalo",
                "badge_color": "emerald",
                "summary": f"Entregado como regalo en {loc['area']}{summary_breed}",
                "locations": locs,
                "evolution_info": evolution_info
            }
        else:
            can_breed = (
                generation >= 2
                and evolution_info is None
                and national_number not in NON_HATCHABLE_SPECIES
            )
            daycare_area = DAYCARE_LOCATIONS_BY_GAME.get(game_slug)
            if can_breed and daycare_area:
                if not any(daycare_area in loc["area"] for loc in game_locations):
                    game_locations.append({
                        "area": daycare_area,
                        "method": "Crianza de huevo"
                    })

            wild_areas = [l["area"] for l in game_locations if "Casino" not in l["area"] and "Intercambio" not in l["method"] and "Guardería" not in l["area"] and "Cuidados" not in l["area"] and "Pícnic" not in l["area"]]
            has_casino = any("Casino" in l["area"] for l in game_locations)
            has_trade = any("Intercambio" in l["method"] for l in game_locations)
            has_daycare = any(daycare_area in l["area"] for l in game_locations) if daycare_area else False

            if wild_areas:
                if len(wild_areas) <= 3:
                    summary_text = f"Salvaje en: {', '.join(wild_areas)}"
                else:
                    summary_text = f"Salvaje en {len(wild_areas)} zonas (ej: {', '.join(wild_areas[:3])}...)"

                if has_casino:
                    coins = GAME_CASINO_PRIZES.get(game_slug, {}).get(national_number)
                    coins_str = f" por {coins:,} fichas".replace(",", ".") if coins else ""
                    casino_loc = next((l["area"] for l in game_locations if "Casino" in l["area"]), "Casino")
                    casino_name = get_casino_name(casino_loc, game_slug, is_wild_combined=True)
                    summary_text += f" y canjeable{coins_str} en el {casino_name}"
                if has_trade:
                    summary_text += " (también por intercambio NPC)"
                if has_daycare and can_breed:
                    summary_text += " (también obtenible como cría en la Guardería Pokémon)"
            elif has_casino:
                coins = GAME_CASINO_PRIZES.get(game_slug, {}).get(national_number)
                coins_str = f" por {coins:,} fichas".replace(",", ".") if coins else ""
                casino_loc = next((l["area"] for l in game_locations if "Casino" in l["area"]), "Casino")
                casino_name = get_casino_name(casino_loc, game_slug)
                summary_text = f"Canjeable{coins_str} en el {casino_name}"
            else:
                unique_areas = [l["area"] for l in game_locations]
                summary_text = f"Disponible en: {', '.join(unique_areas[:3])}"

            if can_breed and has_daycare and wild_areas:
                badge_label = "Salvaje / Crianza"
            elif evolution_info:
                badge_label = "Salvaje / Evolución"
            else:
                badge_label = "Salvaje"

            return {
                "type": "wild",
                "badge_label": badge_label,
                "badge_color": "emerald",
                "summary": summary_text,
                "locations": game_locations,
                "evolution_info": evolution_info
            }

    # 5. Si no tiene encuentros salvajes pero sí evoluciona
    if evolution_info:
        return {
            "type": "evolution",
            "badge_label": "Evolución",
            "badge_color": "indigo",
            "summary": evolution_info["text"],
            "evolution_info": evolution_info,
            "locations": []
        }

    # 6. Crianza / Pokémon bebé (a partir de Gen 2)
    is_baby = False
    if evolution_chain_data:
        chain_root = evolution_chain_data.get("chain", {})
        if chain_root.get("is_baby") and chain_root.get("species", {}).get("name") == pokemon_name.lower():
            is_baby = True

    if generation >= 2 and (is_baby or national_number in BABY_SPECIES) and national_number not in NON_HATCHABLE_SPECIES:
        daycare_area = DAYCARE_LOCATIONS_BY_GAME.get(game_slug, "Guardería Pokémon")
        locs = [{"area": daycare_area, "method": "Crianza de huevo"}]
        if national_number in GEN2_ODD_EGG_SPECIES:
            locs.append({"area": daycare_area, "method": "Huevo Extraño (Regalo con alta probabilidad de variocolor)"})
            summary_text = f"Obtenible mediante eclosión de huevo por crianza en la {daycare_area} o aleatoriamente mediante el Huevo Extraño regalado en la Guardería."
        else:
            summary_text = f"Obtenible mediante eclosión de huevo por crianza en la {daycare_area}."

        return {
            "type": "breeding",
            "badge_label": "Crianza",
            "badge_color": "pink",
            "summary": summary_text,
            "locations": locs,
            "evolution_info": None
        }

    # 7. Desconocido o evento
    return {
        "type": "unknown",
        "badge_label": "Especial",
        "badge_color": "slate",
        "summary": "Método no disponible en estado salvaje en este juego",
        "evolution_info": None,
        "locations": []
    }


GAME_TO_VERSION_GROUP: Dict[str, str] = {
    'red': 'red-blue',
    'blue': 'red-blue',
    'yellow': 'yellow',
    'gold': 'gold-silver',
    'silver': 'gold-silver',
    'crystal': 'crystal',
    'ruby': 'ruby-sapphire',
    'sapphire': 'ruby-sapphire',
    'emerald': 'emerald',
    'firered': 'firered-leafgreen',
    'leafgreen': 'firered-leafgreen',
}


def extract_game_specific_data(
    raw_pokemon_data: Dict[str, Any],
    species_data: Dict[str, Any],
    game_slug: str,
    generation: int = 1,
    moves_map: Optional[Dict[str, Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """
    Extrae y estructura todos los datos específicos del juego:
    - Movimientos por nivel y MT en la versión del juego.
    - Estadísticas base históricas de la generación.
    - Métricas biológicas y de captura (catch rate, gender rate, base happiness, etc.).
    """
    version_group = GAME_TO_VERSION_GROUP.get(game_slug, game_slug)
    
    # 1. Movimientos en este version_group
    raw_moves = raw_pokemon_data.get("moves", [])
    level_up_moves = []
    machine_moves = []
    
    for m in raw_moves:
        move_name = m.get("move", {}).get("name", "")
        m_info = (moves_map.get(move_name) if moves_map else {}) or {}
        
        for vgd in m.get("version_group_details", []):
            if vgd.get("version_group", {}).get("name") == version_group:
                method = vgd.get("move_learn_method", {}).get("name")
                level = vgd.get("level_learned_at", 0)
                
                move_payload = {
                    "name": move_name,
                    "display_name": m_info.get("display_name", move_name.replace("-", " ").title()),
                    "type": m_info.get("type", "normal"),
                    "power": m_info.get("power"),
                    "accuracy": m_info.get("accuracy"),
                    "pp": m_info.get("pp"),
                    "damage_class": m_info.get("damage_class", ""),
                    "effect": m_info.get("effect_description", "")
                }
                
                if method == "level-up":
                    move_payload["level"] = level
                    level_up_moves.append(move_payload)
                elif method == "machine":
                    machine_moves.append(move_payload)

    level_up_moves.sort(key=lambda x: (x.get("level", 0), x.get("display_name", "")))
    machine_moves.sort(key=lambda x: x.get("display_name", ""))
    
    # 2. Estadísticas de la generación
    stats_dict = {s.get("stat", {}).get("name"): s.get("base_stat") for s in raw_pokemon_data.get("stats", [])}
    if generation == 1:
        special = None
        for ps in raw_pokemon_data.get("past_stats", []):
            if ps.get("generation", {}).get("name") == "generation-i":
                for s in ps.get("stats", []):
                    if s.get("stat", {}).get("name") == "special":
                        special = s.get("base_stat")
        if special is None:
            special = stats_dict.get("special-attack", 0)
            
        gen_stats = {
            "hp": stats_dict.get("hp", 0),
            "attack": stats_dict.get("attack", 0),
            "defense": stats_dict.get("defense", 0),
            "special": special,
            "speed": stats_dict.get("speed", 0),
            "total": stats_dict.get("hp", 0) + stats_dict.get("attack", 0) + stats_dict.get("defense", 0) + special + stats_dict.get("speed", 0)
        }
    else:
        gen_stats = {
            "hp": stats_dict.get("hp", 0),
            "attack": stats_dict.get("attack", 0),
            "defense": stats_dict.get("defense", 0),
            "special_attack": stats_dict.get("special-attack", 0),
            "special_defense": stats_dict.get("special-defense", 0),
            "speed": stats_dict.get("speed", 0),
            "total": sum(stats_dict.values())
        }

    # 3. Métricas biológicas y de especie
    species_metrics = {
        "capture_rate": species_data.get("capture_rate"),
        "base_happiness": species_data.get("base_happiness"),
        "gender_rate": species_data.get("gender_rate"),
        "growth_rate": species_data.get("growth_rate", {}).get("name") if isinstance(species_data.get("growth_rate"), dict) else species_data.get("growth_rate"),
        "egg_groups": [eg.get("name") for eg in species_data.get("egg_groups", []) if isinstance(eg, dict)],
        "habitat": species_data.get("habitat", {}).get("name") if isinstance(species_data.get("habitat"), dict) else species_data.get("habitat"),
    }

    return {
        "version_group": version_group,
        "generation": generation,
        "stats": gen_stats,
        "species_metrics": species_metrics,
        "moves": {
            "level_up": level_up_moves,
            "machine": machine_moves
        }
    }


