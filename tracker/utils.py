import time
import random
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

