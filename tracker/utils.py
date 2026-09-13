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
    'fuchsia-city-area': 'Ciudad Fucsia',
    'saffron-city-area': 'Ciudad Azafrán',
    'cinnabar-island-area': 'Isla Canela',
    'viridian-forest-area': 'Bosque Verde',
    'digletts-cave-area': 'Cueva Diglett',
    'kanto-power-plant-area': 'Central de Energía',
    'power-plant-area': 'Central de Energía',
    'vermilion-city-ss-anne-dock': 'Muelle del S.S. Anne (Ciudad Carmín)',
    'kanto-route-3-pokemon-center': 'Centro Pokémon de Ruta 4',
    'kanto-route-4-pokemon-center': 'Centro Pokémon de Ruta 4',
}

ENCOUNTER_METHODS_ES = {
    'walk': 'Hierba alta / Cuevas',
    'surf': 'Surfeando (Agua)',
    'old-rod': 'Caña Vieja',
    'good-rod': 'Caña Buena',
    'super-rod': 'Supercaña',
    'gift': 'Regalo / Inicial',
    'only-one': 'Encuentro Especial Único',
    'headbutt': 'Golpe Cabeza',
}

EVOLUTION_ITEMS_ES = {
    'water-stone': 'Piedra Agua',
    'thunder-stone': 'Piedra Trueno',
    'fire-stone': 'Piedra Fuego',
    'leaf-stone': 'Piedra Hoja',
    'moon-stone': 'Piedra Lunar',
    'sun-stone': 'Piedra Solar',
}

RED_SPECIAL_CASES = {
    # Exclusivos de Pokémon Azul (no aparecen salvajes en Rojo)
    27: {"type": "trade", "badge_label": "Intercambio", "badge_color": "sky", "summary": "Exclusivo de Pokémon Azul (obtenible mediante intercambio)"},
    28: {"type": "trade", "badge_label": "Intercambio", "badge_color": "sky", "summary": "Evoluciona de Sandshrew (Exclusivo de Pokémon Azul)"},
    37: {"type": "trade", "badge_label": "Intercambio", "badge_color": "sky", "summary": "Exclusivo de Pokémon Azul (obtenible mediante intercambio)"},
    38: {"type": "trade", "badge_label": "Intercambio", "badge_color": "sky", "summary": "Evoluciona de Vulpix (Exclusivo de Pokémon Azul)"},
    52: {"type": "trade", "badge_label": "Intercambio", "badge_color": "sky", "summary": "Exclusivo de Pokémon Azul (obtenible mediante intercambio)"},
    53: {"type": "trade", "badge_label": "Intercambio", "badge_color": "sky", "summary": "Evoluciona de Meowth (Exclusivo de Pokémon Azul)"},
    69: {"type": "trade", "badge_label": "Intercambio", "badge_color": "sky", "summary": "Exclusivo de Pokémon Azul (obtenible mediante intercambio)"},
    70: {"type": "trade", "badge_label": "Intercambio", "badge_color": "sky", "summary": "Evoluciona de Bellsprout (Exclusivo de Pokémon Azul)"},
    71: {"type": "trade", "badge_label": "Intercambio", "badge_color": "sky", "summary": "Evoluciona de Weepinbell (Exclusivo de Pokémon Azul)"},
    126: {"type": "trade", "badge_label": "Intercambio", "badge_color": "sky", "summary": "Exclusivo de Pokémon Azul (obtenible mediante intercambio)"},
    127: {"type": "trade", "badge_label": "Intercambio", "badge_color": "sky", "summary": "Exclusivo de Pokémon Azul (obtenible mediante intercambio)"},
    # Intercambios dentro del juego (In-game trades)
    83: {"type": "trade", "badge_label": "Intercambio NPC", "badge_color": "violet", "summary": "Intercambio en Ciudad Carmín (dar un Spearow a cambio de Dux)"},
    122: {"type": "trade", "badge_label": "Intercambio NPC", "badge_color": "violet", "summary": "Intercambio en la caseta de Ruta 2 (dar un Abra a cambio de Marcel)"},
    124: {"type": "trade", "badge_label": "Intercambio NPC", "badge_color": "violet", "summary": "Intercambio en Ciudad Celeste (dar un Poliwhirl a cambio de Lola)"},
    108: {"type": "trade", "badge_label": "Intercambio NPC", "badge_color": "violet", "summary": "Intercambio en la caseta de Ruta 18 (dar un Slowbro a cambio de Marc)"},
    # Casino Ciudad Azulona
    137: {"type": "casino", "badge_label": "Premio Casino", "badge_color": "amber", "summary": "Premio en el Casino Rocket de Ciudad Azulona (9.999 fichas)"},
    # Fósiles
    138: {"type": "fossil", "badge_label": "Fósil", "badge_color": "amber", "summary": "Revivir el Fósil Hélix en el Laboratorio de Isla Canela"},
    139: {"type": "evolution", "badge_label": "Evolución", "badge_color": "indigo", "summary": "Evoluciona de Omanyte al nivel 40"},
    140: {"type": "fossil", "badge_label": "Fósil", "badge_color": "amber", "summary": "Revivir el Fósil Domo en el Laboratorio de Isla Canela"},
    141: {"type": "evolution", "badge_label": "Evolución", "badge_color": "indigo", "summary": "Evoluciona de Kabuto al nivel 40"},
    142: {"type": "fossil", "badge_label": "Fósil", "badge_color": "amber", "summary": "Revivir el Ámbar Viejo en el Laboratorio de Isla Canela"},
    # Regalos especiales
    106: {"type": "gift", "badge_label": "Regalo / Elección", "badge_color": "emerald", "summary": "Elegir como premio al vencer al Maestro del Dojo Kárate de Ciudad Azafrán"},
    107: {"type": "gift", "badge_label": "Regalo / Elección", "badge_color": "emerald", "summary": "Elegir como premio al vencer al Maestro del Dojo Kárate de Ciudad Azafrán"},
    131: {"type": "gift", "badge_label": "Regalo", "badge_color": "emerald", "summary": "Regalo de un empleado en el piso 7 del edificio Silph S.A. (Ciudad Azafrán)"},
    133: {"type": "gift", "badge_label": "Regalo", "badge_color": "emerald", "summary": "Encuentro en la azotea de la Mansión Azulona (Ciudad Azulona)"},
    # Estáticos / Legendarios
    143: {"type": "special", "badge_label": "Encuentro Único", "badge_color": "rose", "summary": "Ruta 12 o Ruta 16 (despertar usando la Poké Flauta)"},
    144: {"type": "special", "badge_label": "Legendario", "badge_color": "rose", "summary": "En lo profundo de las Islas Espuma (Sótano B4F)"},
    145: {"type": "special", "badge_label": "Legendario", "badge_color": "rose", "summary": "Al final de la Central de Energía"},
    146: {"type": "special", "badge_label": "Legendario", "badge_color": "rose", "summary": "En la Calle Victoria (cerca del Alto Mando)"},
    150: {"type": "special", "badge_label": "Legendario", "badge_color": "rose", "summary": "En lo profundo de la Cueva Celeste (tras vencer la Liga Pokémon)"},
    151: {"type": "special", "badge_label": "Mítico / Evento", "badge_color": "rose", "summary": "Distribución oficial de Nintendo mediante evento especial"},
}

def clean_location_name(area_slug: str) -> str:
    """Convierte el slug de un área a un nombre amigable en español."""
    if area_slug in KANTO_LOCATION_NAMES_ES:
        return KANTO_LOCATION_NAMES_ES[area_slug]

    m_sea = re.match(r"(?:kanto-)?sea-route-(\d+)", area_slug)
    if m_sea:
        return f"Ruta marítima {m_sea.group(1)}"

    m_route = re.match(r"(?:kanto-)?route-(\d+)", area_slug)
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

    clean = area_slug.replace("kanto-", "").replace("-area", "").replace("-", " ")
    return clean.title()


def find_evolution_details(chain_node: Dict[str, Any], target_species_name: str, parent_name: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Recorre recursivamente un árbol de evolución de PokeAPI buscando al Pokémon objetivo."""
    current_species = chain_node.get("species", {}).get("name", "")
    if current_species == target_species_name:
        evo_details_list = chain_node.get("evolution_details", [])
        return {
            "parent_name": parent_name,
            "details": evo_details_list[0] if evo_details_list else {}
        }

    for child in chain_node.get("evolves_to", []):
        res = find_evolution_details(child, target_species_name, parent_name=current_species)
        if res:
            return res

    return None


def resolve_obtaining_info(
    national_number: int,
    pokemon_name: str,
    game_slug: str,
    encounters_data: Optional[List[Dict[str, Any]]] = None,
    evolution_chain_data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Determina de forma estructurada cómo se obtiene el Pokémon en la versión especificada.
    Retorna un diccionario estructurado listo para ser consumido por el frontend y la base de datos:
    {
        "type": "wild" | "gift" | "evolution" | "trade" | "casino" | "fossil" | "special" | "unknown",
        "badge_label": "Salvaje" | "Regalo" | "Evolución" | ... ,
        "badge_color": "emerald" | "amber" | "indigo" | "sky" | "rose" | "slate",
        "summary": "Texto resumen explicativo",
        "locations": [{"area": "Ruta 1", "method": "Hierba alta / Cuevas"}],
        "evolution_info": {"from": "Bulbasaur", "trigger": "level-up", "condition": "Nivel 16"}
    }
    """
    # 1. Casos especiales curados por juego (ej. Pokémon Rojo)
    if game_slug == 'red' and national_number in RED_SPECIAL_CASES:
        return RED_SPECIAL_CASES[national_number]

    # 2. Encuentros salvajes / directos registrados en PokeAPI para este juego
    game_locations = []
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
                    method_labels = [ENCOUNTER_METHODS_ES.get(m, m.title()) for m in sorted(list(methods))]
                    game_locations.append({
                        "area": clean_area,
                        "method": ", ".join(method_labels) if method_labels else "Encuentro salvaje"
                    })

    if game_locations:
        if has_gift_encounter and len(game_locations) == 1:
            loc = game_locations[0]
            return {
                "type": "gift",
                "badge_label": "Regalo / Inicial",
                "badge_color": "emerald",
                "summary": f"Entregado como regalo o Pokémon inicial en {loc['area']}",
                "locations": game_locations
            }
        else:
            # Agrupar áreas únicas
            unique_areas = list(dict.fromkeys([l["area"] for l in game_locations]))
            if len(unique_areas) <= 3:
                summary_text = f"Salvaje en: {', '.join(unique_areas)}"
            else:
                summary_text = f"Salvaje en {len(unique_areas)} zonas (ej: {', '.join(unique_areas[:3])}...)"

            return {
                "type": "wild",
                "badge_label": "Salvaje",
                "badge_color": "emerald",
                "summary": summary_text,
                "locations": game_locations[:10]
            }

    # 3. Si no tiene encuentros salvajes, comprobar si es por evolución
    if evolution_chain_data:
        chain_root = evolution_chain_data.get("chain", {})
        evo_res = find_evolution_details(chain_root, pokemon_name.lower())

        if evo_res and evo_res.get("parent_name"):
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

            summary = f"Evoluciona de {parent}"
            if condition:
                if condition.startswith("Nivel") or condition.startswith("usando") or condition.startswith("Intercambio"):
                    summary += f" ({condition})" if not condition.startswith("usando") else f" {condition}"
                else:
                    summary += f" ({condition})"

            return {
                "type": "evolution",
                "badge_label": "Evolución",
                "badge_color": "indigo",
                "summary": summary,
                "evolution_info": {
                    "from": parent,
                    "trigger": trigger,
                    "condition": condition
                }
            }

    # 4. Desconocido o evento
    return {
        "type": "unknown",
        "badge_label": "Especial",
        "badge_color": "slate",
        "summary": "Método no disponible en estado salvaje en este juego"
    }

