import os
import re
import json
import time
import random
from pathlib import Path
from typing import List, Dict, Any, Optional
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

    # 3. Español en versiones afines/canónicas (Let's Go, X, Y, etc.)
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
    'kanto-route-3-pokemon-center': 'Centro Pokémon de Ruta 4',
    'kanto-route-4-pokemon-center': 'Centro Pokémon de Ruta 4',
    'underground-path': 'Vía Subterránea',
    'kanto-underground-path': 'Vía Subterránea',
}

ENCOUNTER_METHODS_ES = {
    'walk': 'Hierba alta',
    'surf': 'Surfeando (Agua)',
    'old-rod': 'Caña Vieja',
    'good-rod': 'Caña Buena',
    'super-rod': 'Supercaña',
    'gift': 'Regalo',
    'only-one': 'Encuentro Especial Único',
    'headbutt': 'Golpe Cabeza',
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

# Catálogo canónico de Pokémon Iniciales aislados por juego
STARTERS_BY_GAME: Dict[str, Dict[int, Dict[str, Any]]] = {
    'red': {
        1: {
            "type": "starter",
            "badge_label": "Inicial",
            "badge_color": "emerald",
            "summary": "Pokémon inicial a elegir en el Laboratorio del Profesor Oak en Pueblo Paleta.",
            "locations": [{"area": "Pueblo Paleta (Laboratorio de Oak)", "method": "Elección inicial"}]
        },
        4: {
            "type": "starter",
            "badge_label": "Inicial",
            "badge_color": "emerald",
            "summary": "Pokémon inicial a elegir en el Laboratorio del Profesor Oak en Pueblo Paleta.",
            "locations": [{"area": "Pueblo Paleta (Laboratorio de Oak)", "method": "Elección inicial"}]
        },
        7: {
            "type": "starter",
            "badge_label": "Inicial",
            "badge_color": "emerald",
            "summary": "Pokémon inicial a elegir en el Laboratorio del Profesor Oak en Pueblo Paleta.",
            "locations": [{"area": "Pueblo Paleta (Laboratorio de Oak)", "method": "Elección inicial"}]
        },
    },
    'blue': {
        1: {
            "type": "starter",
            "badge_label": "Inicial",
            "badge_color": "emerald",
            "summary": "Pokémon inicial a elegir en el Laboratorio del Profesor Oak en Pueblo Paleta.",
            "locations": [{"area": "Pueblo Paleta (Laboratorio de Oak)", "method": "Elección inicial"}]
        },
        4: {
            "type": "starter",
            "badge_label": "Inicial",
            "badge_color": "emerald",
            "summary": "Pokémon inicial a elegir en el Laboratorio del Profesor Oak en Pueblo Paleta.",
            "locations": [{"area": "Pueblo Paleta (Laboratorio de Oak)", "method": "Elección inicial"}]
        },
        7: {
            "type": "starter",
            "badge_label": "Inicial",
            "badge_color": "emerald",
            "summary": "Pokémon inicial a elegir en el Laboratorio del Profesor Oak en Pueblo Paleta.",
            "locations": [{"area": "Pueblo Paleta (Laboratorio de Oak)", "method": "Elección inicial"}]
        },
    },
    'yellow': {
        25: {
            "type": "starter",
            "badge_label": "Inicial",
            "badge_color": "emerald",
            "summary": "Pokémon inicial entregado por el Profesor Oak en Pueblo Paleta.",
            "locations": [{"area": "Pueblo Paleta (Laboratorio de Oak)", "method": "Elección inicial"}]
        },
    },
}

RED_SPECIAL_CASES: Dict[int, Dict[str, Any]] = {
    # Exclusivos de Pokémon Azul (no aparecen salvajes en Rojo)
    27: {"type": "trade", "badge_label": "Intercambio", "badge_color": "sky", "summary": "Exclusivo de Pokémon Azul (obtenible mediante intercambio)", "locations": [{"area": "Edición Pokémon Azul", "method": "Intercambio con cable link"}]},
    28: {"type": "trade", "badge_label": "Intercambio", "badge_color": "sky", "summary": "Evoluciona de Sandshrew (Exclusivo de Pokémon Azul)", "locations": [{"area": "Edición Pokémon Azul", "method": "Intercambio con cable link"}]},
    37: {"type": "trade", "badge_label": "Intercambio", "badge_color": "sky", "summary": "Exclusivo de Pokémon Azul (obtenible mediante intercambio)", "locations": [{"area": "Edición Pokémon Azul", "method": "Intercambio con cable link"}]},
    38: {"type": "trade", "badge_label": "Intercambio", "badge_color": "sky", "summary": "Evoluciona de Vulpix (Exclusivo de Pokémon Azul)", "locations": [{"area": "Edición Pokémon Azul", "method": "Intercambio con cable link"}]},
    52: {"type": "trade", "badge_label": "Intercambio", "badge_color": "sky", "summary": "Exclusivo de Pokémon Azul (obtenible mediante intercambio)", "locations": [{"area": "Edición Pokémon Azul", "method": "Intercambio con cable link"}]},
    53: {"type": "trade", "badge_label": "Intercambio", "badge_color": "sky", "summary": "Evoluciona de Meowth (Exclusivo de Pokémon Azul)", "locations": [{"area": "Edición Pokémon Azul", "method": "Intercambio con cable link"}]},
    69: {"type": "trade", "badge_label": "Intercambio", "badge_color": "sky", "summary": "Exclusivo de Pokémon Azul (obtenible mediante intercambio)", "locations": [{"area": "Edición Pokémon Azul", "method": "Intercambio con cable link"}]},
    70: {"type": "trade", "badge_label": "Intercambio", "badge_color": "sky", "summary": "Evoluciona de Bellsprout (Exclusivo de Pokémon Azul)", "locations": [{"area": "Edición Pokémon Azul", "method": "Intercambio con cable link"}]},
    71: {"type": "trade", "badge_label": "Intercambio", "badge_color": "sky", "summary": "Evoluciona de Weepinbell (Exclusivo de Pokémon Azul)", "locations": [{"area": "Edición Pokémon Azul", "method": "Intercambio con cable link"}]},
    126: {"type": "trade", "badge_label": "Intercambio", "badge_color": "sky", "summary": "Exclusivo de Pokémon Azul (obtenible mediante intercambio)", "locations": [{"area": "Edición Pokémon Azul", "method": "Intercambio con cable link"}]},
    127: {"type": "trade", "badge_label": "Intercambio", "badge_color": "sky", "summary": "Exclusivo de Pokémon Azul (obtenible mediante intercambio)", "locations": [{"area": "Edición Pokémon Azul", "method": "Intercambio con cable link"}]},
    # Intercambios dentro del juego (In-game trades)
    83: {"type": "trade_npc", "badge_label": "Intercambio NPC", "badge_color": "violet", "summary": "Intercambio en Ciudad Carmín (dar un Spearow a cambio de Dux)", "locations": [{"area": "Ciudad Carmín", "method": "Intercambio por Spearow"}]},
    122: {"type": "trade_npc", "badge_label": "Intercambio NPC", "badge_color": "violet", "summary": "Intercambio en la caseta de Ruta 2 (dar un Abra a cambio de Marcel)", "locations": [{"area": "Ruta 2 (Caseta)", "method": "Intercambio por Abra"}]},
    124: {"type": "trade_npc", "badge_label": "Intercambio NPC", "badge_color": "violet", "summary": "Intercambio en Ciudad Celeste (dar un Poliwhirl a cambio de Lola)", "locations": [{"area": "Ciudad Celeste", "method": "Intercambio por Poliwhirl"}]},
    108: {"type": "trade_npc", "badge_label": "Intercambio NPC", "badge_color": "violet", "summary": "Intercambio en la caseta de Ruta 18 (dar un Slowbro a cambio de Marc)", "locations": [{"area": "Ruta 18 (Caseta)", "method": "Intercambio por Slowbro"}]},
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
    150: {"type": "legendary", "badge_label": "Legendario", "badge_color": "rose", "is_unique": True, "summary": "En lo profundo de la Cueva Celeste (tras vencer la Liga Pokémon)", "locations": [{"area": "Cueva Celeste", "method": "Encuentro Legendario"}]},
    151: {"type": "mythical", "badge_label": "Mítico / Evento", "badge_color": "violet", "is_unique": True, "summary": "Distribución oficial de Nintendo mediante evento especial", "locations": [{"area": "Evento Nintendo", "method": "Distribución especial"}]},
}

# Registro modular de casos especiales indexado por versión de juego
GAME_SPECIAL_CASES: Dict[str, Dict[int, Dict[str, Any]]] = {
    'red': RED_SPECIAL_CASES,
    'blue': RED_SPECIAL_CASES,
}

def clean_location_name(area_slug: str) -> str:
    """Convierte el slug de un área a un nombre amigable en español."""
    if area_slug in KANTO_LOCATION_NAMES_ES:
        return KANTO_LOCATION_NAMES_ES[area_slug]

    m_route = re.match(r"(?:kanto-)?(?:sea-)?route-(\d+)", area_slug)
    if m_route:
        return f"Ruta {m_route.group(1)}"

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
    if "prize-corner" in area_slug or "game-corner" in area_slug:
        return "Ciudad Azulona (Casino)"
    if "cinnabar-lab" in area_slug:
        return "Isla Canela (Laboratorio)"
    if "underground-path" in area_slug:
        return "Vía Subterránea"

    clean = area_slug.replace("kanto-", "").replace("-area", "").replace("-", " ")
    return clean.title()


# Identificadores de biomas y entornos de Kanto
KANTO_CAVE_SLUGS = {
    'mt-moon', 'rock-tunnel', 'seafoam-islands',
    'cerulean-cave', 'digletts-cave', 'victory-road'
}

KANTO_INTERIOR_SLUGS = {
    'pokemon-tower', 'pokemon-mansion', 'power-plant'
}


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
        32: 1200,    # Nidorino
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
        # Cuevas de Kanto (suelo de roca/gruta sin hierba)
        if any(c in area_slug for c in KANTO_CAVE_SLUGS):
            return "Cueva"
        # Interiores de edificios / estructuras de Kanto
        if any(b in area_slug for b in KANTO_INTERIOR_SLUGS):
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
                if trigger == "level-up":
                    min_lvl = details.get("min_level")
                    min_happ = details.get("min_happiness")
                    if min_lvl:
                        condition = f"Nivel {min_lvl}"
                    elif min_happ:
                        condition = "Felicidad alta"
                    else:
                        condition = "Subir de nivel"
                elif trigger == "use-item":
                    item_slug = details.get("item", {}).get("name", "")
                    condition = f"usando {EVOLUTION_ITEMS_ES.get(item_slug, item_slug.title())}"
                elif trigger == "trade":
                    held_item = details.get("held_item")
                    if held_item:
                        condition = f"Intercambio con {held_item.get('name', '').title()}"
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
                    "text": evo_summary
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
            if "Casino" in loc['area']:
                coins = GAME_CASINO_PRIZES.get(game_slug, {}).get(national_number)
                coins_str = f" por {coins:,} fichas".replace(",", ".") if coins else ""
                return {
                    "type": "casino",
                    "badge_label": "Premio Casino",
                    "badge_color": "amber",
                    "summary": f"Canjeable{coins_str} en el Casino Rocket de Ciudad Azulona",
                    "locations": game_locations,
                    "evolution_info": evolution_info
                }
            return {
                "type": "gift",
                "badge_label": "Regalo",
                "badge_color": "emerald",
                "summary": f"Entregado como regalo en {loc['area']}",
                "locations": game_locations,
                "evolution_info": evolution_info
            }
        else:
            wild_areas = [l["area"] for l in game_locations if "Casino" not in l["area"] and "Intercambio" not in l["method"]]
            has_casino = any("Casino" in l["area"] for l in game_locations)
            has_trade = any("Intercambio" in l["method"] for l in game_locations)

            if wild_areas:
                if len(wild_areas) <= 3:
                    summary_text = f"Salvaje en: {', '.join(wild_areas)}"
                else:
                    summary_text = f"Salvaje en {len(wild_areas)} zonas (ej: {', '.join(wild_areas[:3])}...)"

                if has_casino:
                    coins = GAME_CASINO_PRIZES.get(game_slug, {}).get(national_number)
                    coins_str = f" por {coins:,} fichas".replace(",", ".") if coins else ""
                    summary_text += f" y canjeable{coins_str} en el Casino de Ciudad Azulona"
                if has_trade:
                    summary_text += " (también por intercambio NPC)"
            elif has_casino:
                coins = GAME_CASINO_PRIZES.get(game_slug, {}).get(national_number)
                coins_str = f" por {coins:,} fichas".replace(",", ".") if coins else ""
                summary_text = f"Canjeable{coins_str} en el Casino Rocket de Ciudad Azulona"
            else:
                unique_areas = [l["area"] for l in game_locations]
                summary_text = f"Disponible en: {', '.join(unique_areas[:3])}"

            badge_label = "Salvaje / Evolución" if evolution_info else "Salvaje"

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

    # 6. Desconocido o evento
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


