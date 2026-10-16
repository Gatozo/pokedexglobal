import copy
import functools
import json
import re
from django.conf import settings
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.db import transaction
from django.core.cache import cache
from django.contrib.auth import login, logout
from django.contrib import messages
from django.urls import reverse
from .models import Game, Pokedex, UserPokemonCatch
from .forms import HybridLoginForm, UserRegisterForm
from .catalog_service import get_compiled_catalog, get_catalog_entry_by_id
from .exclusives import get_version_exclusives_context, get_version_transfers_context
from .game_hub_data import MAIN_SERIES_GAMES, GENERATIONS_METADATA, AVAILABLE_CONSOLES
from .security import check_username_rate_limit



@functools.lru_cache(maxsize=64)
def _get_game_catalog_metadata(g_slug: str):
    """Retorna identificadores compilados y totales del juego cacheados en memoria para acelerar el selector."""
    reg_cat = get_compiled_catalog(g_slug, is_national=False) or []
    nat_cat = get_compiled_catalog(g_slug, is_national=True) or []
    return {
        "reg_ids": set(e.id for e in reg_cat),
        "nat_ids": set(e.id for e in nat_cat),
        "reg_total": len(reg_cat),
        "nat_total": len(nat_cat),
    }


EXTERNAL_KEYWORDS = [
    "cable link", "transferencia", "parque compi", "traslador",
    "cápsula del tiempo", "capsula del tiempo", "exclusivo de versión",
    "exclusivo de version", "intercambio con pokémon", "intercambio con pokemon",
    "edición pokémon", "edicion pokemon", "edición rojo", "edición azul",
    "edición oro", "edición plata", "edición rubí", "edición zafiro",
    "edición diamante", "edición perla", "distribución oficial", "evento presencial",
    "distribución especial", "evento nintendo", "conexión con pokémon ranger", "disco bonus"
]


def _classify_catalog_for_game(nat_cat):
    """
    Clasifica las entradas del catálogo nacional de un juego determinando con precisión quirúrgica
    si cada Pokémon es capturable/obtenible de forma nativa en dicha edición.
    Resuelve los linajes evolutivos en memoria (si la especie base no es nativa, sus evoluciones no lo son).
    Retorna un diccionario {entry.pokemon.national_number: (is_native: bool, method_badge: str | None)}.
    """
    if not nat_cat:
        return {}

    by_name = {entry.pokemon.name.lower(): entry for entry in nat_cat}
    by_clean_name = {entry.pokemon.name.lower().split('-')[0]: entry for entry in nat_cat}

    native_status = {}
    method_badges = {}

    for entry in nat_cat:
        p_name = entry.pokemon.name.lower()
        obt = getattr(entry, "obtaining_info", {}) or {}
        obt_type = str(obt.get("type", "")).lower().strip()
        locs = obt.get("locations", []) or []
        summary = str(obt.get("summary", "")).lower()

        # Filtrar ubicaciones locales descartando crianza y transferencias/intercambios externos
        local_locs = []
        for l in locs:
            m = l.get("method", "").lower().strip()
            a = l.get("area", "").lower().strip()
            if "crianza" in m:
                continue
            if any(kw in m or kw in a for kw in EXTERNAL_KEYWORDS):
                continue
            local_locs.append(l)

        methods_str = " ".join([l.get("method", "").lower() for l in local_locs])
        areas_str = " ".join([l.get("area", "").lower() for l in local_locs])
        full_str = methods_str + " " + areas_str

        # Exclusivos de versión contraparte: Si está marcado como exclusivo de otra edición
        # y no cuenta con captura salvaje local directa, debe descartarse inequívocamente.
        wild_kw = ["hierba", "pesca", "caña", "surf", "cueva", "buceo", "roca", "pantano", "safari"]
        has_wild = any(kw in full_str for kw in wild_kw)
        badge_label_lower = str(obt.get("badge_label", "")).lower()
        is_version_exclusive = (
            any("exclusivo de versi" in l.get("method", "").lower() for l in locs)
            or any("intercambio con pokémon" in l.get("area", "").lower() for l in locs)
            or any("intercambio con pokemon" in l.get("area", "").lower() for l in locs)
            or ("exclusivo " in badge_label_lower and "fósil" not in badge_label_lower and "fosil" not in badge_label_lower)
        )
        if is_version_exclusive and not has_wild:
            native_status[p_name] = False
            method_badges[p_name] = None
            continue

        # Si tiene ubicaciones salvajes/encuentro local comprobables
        if local_locs:
            if all("inserci" in l.get("method", "").lower() for l in local_locs):
                native_status[p_name] = True
                method_badges[p_name] = "Inserción Dual (GBA)"
                continue
            if "radar" in full_str and not any("hierba" in l.get("method", "").lower() and "radar" not in l.get("method", "").lower() for l in local_locs):
                native_status[p_name] = True
                method_badges[p_name] = "Poké Radar"
                continue
            if "baldosas especiales" in full_str:
                native_status[p_name] = True
                method_badges[p_name] = "Pesca Especial"
                continue
            if "manada" in full_str:
                native_status[p_name] = True
                method_badges[p_name] = "Manada Diaria"
                continue
            if "miel" in full_str:
                native_status[p_name] = True
                method_badges[p_name] = "Árbol de Miel"
                continue
            if "trofeo" in full_str or "fortuny" in full_str:
                native_status[p_name] = True
                method_badges[p_name] = "Jardín Trofeo"
                continue
            if "viernes" in full_str:
                native_status[p_name] = True
                method_badges[p_name] = "Solo los Viernes"
                continue
            if "fósil" in full_str or "fosil" in full_str or obt_type == "fossil":
                native_status[p_name] = True
                method_badges[p_name] = "Fósil Restaurado"
                continue

            # Salvaje prioritario (rutas, hierba, pesca, surf, cueva, buceo, pantano, safari, etc.)
            # Se evalúa antes de NPC trade para que especies como Seedot o Horsea en Esmeralda
            # (que tienen rutas salvajes y un intercambio NPC secundario) se clasifiquen como Salvaje.
            if obt_type == "wild" or has_wild:
                native_status[p_name] = True
                method_badges[p_name] = "Salvaje"
                continue

            # Intercambio con NPC in-game (ej. Meowth en Esmeralda, Farfetch'd en Rojo)
            if obt_type == "trade_npc" or "intercambio con npc" in full_str or "intercambio npc" in full_str:
                native_status[p_name] = True
                method_badges[p_name] = "Intercambio NPC"
                continue

            native_status[p_name] = True
            method_badges[p_name] = "Salvaje"
            continue

        # Si no tiene local_locs:
        if obt_type in ["gift", "starter"]:
            native_status[p_name] = True
            method_badges[p_name] = "Regalo / Inicial"
            continue

        if obt_type in ["static", "legendary"]:
            if not any(kw in summary for kw in ["evento presencial", "distribución oficial", "exclusivo de", "transferir", "ranger"]):
                native_status[p_name] = True
                method_badges[p_name] = "Encuentro Especial"
                continue

        if obt_type in ["transfer", "trade", "exclusive", "mythical", "event"]:
            native_status[p_name] = False
            method_badges[p_name] = None
            continue

        # Si es evolución o cría, se resolverá en la segunda pasada
        native_status[p_name] = None

    # Segunda pasada: Resolver linaje evolutivo recursivamente
    def resolve_line(p_name, visited=None):
        if visited is None:
            visited = set()
        if p_name in visited:
            return False
        visited.add(p_name)

        if native_status.get(p_name) is not None:
            return native_status[p_name]

        entry = by_name.get(p_name) or by_clean_name.get(p_name)
        if not entry:
            return False

        obt = getattr(entry, "obtaining_info", {}) or {}
        evo_from = obt.get("evolution_info", {}).get("from", "")
        if evo_from:
            res = resolve_line(evo_from.lower(), visited)
            native_status[p_name] = res
            if res:
                method_badges[p_name] = "Evolución / Cría"
            return res

        summary = str(obt.get("summary", "")).lower()
        if "evoluciona de " in summary:
            match = re.search(r"evoluciona de ([a-záéíóúñ\-]+)", summary)
            if match:
                parent = match.group(1).strip()
                res = resolve_line(parent, visited)
                native_status[p_name] = res
                if res:
                    method_badges[p_name] = "Evolución / Cría"
                return res

        if "eclosiona al criar a " in summary or "criar a " in summary:
            match = re.search(r"criar a ([a-záéíóúñ\-]+)", summary)
            if match:
                parent = match.group(1).strip()
                res = resolve_line(parent, visited)
                native_status[p_name] = res
                if res:
                    method_badges[p_name] = "Evolución / Cría"
                return res

        native_status[p_name] = False
        return False

    for entry in nat_cat:
        p_name = entry.pokemon.name.lower()
        if native_status.get(p_name) is None:
            resolve_line(p_name)

    result = {}
    for entry in nat_cat:
        p_name = entry.pokemon.name.lower()
        p_num = entry.pokemon.national_number
        is_native = bool(native_status.get(p_name, False))
        badge = method_badges.get(p_name) if is_native else None
        result[p_num] = (is_native, badge)

    return result


def _classify_obtaining_method(entry):
    """
    Función de compatibilidad para clasificar una sola entrada sin contexto del catálogo completo.
    """
    obt = getattr(entry, "obtaining_info", {}) or {}
    obt_type = str(obt.get("type", "")).lower().strip()
    locs = obt.get("locations", []) or []

    local_locs = []
    for l in locs:
        m = l.get("method", "").lower().strip()
        a = l.get("area", "").lower().strip()
        if "crianza" in m:
            continue
        if any(kw in m or kw in a for kw in EXTERNAL_KEYWORDS):
            continue
        local_locs.append(l)

    if local_locs:
        methods_str = " ".join([l.get("method", "").lower() for l in local_locs])
        if all("inserci" in l.get("method", "").lower() for l in local_locs):
            return True, "Inserción Dual (GBA)"
        if "radar" in methods_str:
            return True, "Poké Radar"
        if "baldosas especiales" in methods_str:
            return True, "Pesca Especial"
        if "manada" in methods_str:
            return True, "Manada Diaria"
        if "miel" in methods_str:
            return True, "Árbol de Miel"
        if "fósil" in methods_str or "fosil" in methods_str or obt_type == "fossil":
            return True, "Fósil Restaurado"
        wild_kw = ["hierba", "pesca", "caña", "surf", "cueva", "buceo", "roca", "pantano", "safari"]
        if obt_type == "wild" or any(kw in methods_str for kw in wild_kw):
            return True, "Salvaje"
        if obt_type == "trade_npc" or "intercambio con npc" in methods_str or "intercambio npc" in methods_str:
            return True, "Intercambio NPC"
        return True, "Salvaje"

    if obt_type in ["gift", "starter"]:
        return True, "Regalo / Inicial"
    if obt_type in ["static", "legendary"]:
        return True, "Encuentro Especial"
    if obt_type in ["evolution", "breeding"]:
        return True, "Evolución / Cría"
    return False, None


@functools.lru_cache(maxsize=1)
def _get_base_pokemon_search_index():
    """Construye en memoria una sola vez la estructura base estática de búsqueda nacional de los 38 juegos."""
    index = {}
    for item in MAIN_SERIES_GAMES:
        g_slug = item["slug"]
        nat_cat = get_compiled_catalog(g_slug, is_national=True) or []
        game_classification = _classify_catalog_for_game(nat_cat)

        for entry in nat_cat:
            p_num = entry.pokemon.national_number
            p_name = entry.pokemon.name
            is_native, method_badge = game_classification.get(p_num, (False, None))
            if not is_native:
                continue

            if p_num not in index:
                index[p_num] = {
                    "id": p_num,
                    "name": p_name,
                    "games": {},
                }
            index[p_num]["games"][g_slug] = {
                "entry_id": entry.id,
                "method_badge": method_badge or "Salvaje",
            }
    return index



def _get_user_or_session(request):
    """Devuelve una tupla (user, session_key) según el estado de autenticación."""
    if request.user.is_authenticated:
        return request.user, None
    if not request.session.session_key:
        request.session.save()
    return None, request.session.session_key


def _get_cached_all_games():
    """Retorna el catálogo de juegos desde la caché en memoria."""
    games = cache.get("all_games_catalog")
    if games is None:
        games = list(Game.objects.all())
        timeout = 60 if getattr(settings, "DEBUG", False) else 86400
        cache.set("all_games_catalog", games, timeout=timeout)
    return games


def get_cached_pokedex_entries(game_slug="", is_national=False, force_refresh=False):
    """
    Retorna la lista base de entradas de la Pokédex desde los catálogos compilados inmutables (0 ms SQL).
    Soporta modo regional (Johto, Kanto, etc.) y modo nacional según is_national.
    """
    if game_slug:
        catalog = get_compiled_catalog(game_slug, force_reload=force_refresh, is_national=is_national)
        if catalog is not None and len(catalog) > 0:
            return catalog
    return []


_STONES_JSON_CACHE = None
_STONES_JSON_MTIME = 0.0


def _get_cached_evolution_stones_json():
    global _STONES_JSON_CACHE, _STONES_JSON_MTIME
    from .utils import EVOLUTION_STONES_PATH, get_evolution_stones_catalog
    mtime = EVOLUTION_STONES_PATH.stat().st_mtime if EVOLUTION_STONES_PATH.exists() else 0.0
    if _STONES_JSON_CACHE is None or mtime != _STONES_JSON_MTIME:
        _STONES_JSON_CACHE = json.dumps(get_evolution_stones_catalog(force_reload=True), ensure_ascii=False)
        _STONES_JSON_MTIME = mtime
    return _STONES_JSON_CACHE


def merge_session_catches_to_user(session_key, user):
    """
    Si el usuario estuvo interactuando con la Pokédex como invitado (usando session_key),
    transfiere de forma inteligente y segura todas sus capturas registradas a su cuenta de usuario.
    Si ya existía un registro para ese Pokémon en su cuenta, fusiona los estados (is_caught, is_shiny, unown forms).
    """
    if not session_key or not user:
        return 0

    anon_catches = list(UserPokemonCatch.objects.filter(session_key=session_key, user__isnull=True))
    if not anon_catches:
        return 0

    transferred_count = 0
    with transaction.atomic():
        for anon in anon_catches:
            # Descartar registros huérfanos o con datos inválidos
            if not anon.game_slug or anon.entry_number <= 0:
                anon.delete()
                continue

            user_catch = UserPokemonCatch.objects.filter(
                user=user,
                game_slug=anon.game_slug,
                entry_number=anon.entry_number,
            ).first()

            if not user_catch:
                user_catch = UserPokemonCatch.objects.create(
                    user=user,
                    game_slug=anon.game_slug,
                    entry_number=anon.entry_number,
                    entry_id=anon.entry_id,
                    is_caught=anon.is_caught,
                    is_shiny=anon.is_shiny,
                    unown_forms_caught=anon.unown_forms_caught,
                    caught_at=anon.caught_at,
                )
            else:
                changed = False
                if anon.is_caught and not user_catch.is_caught:
                    user_catch.is_caught = True
                    user_catch.caught_at = user_catch.caught_at or anon.caught_at or timezone.now()
                    changed = True
                if anon.is_shiny and not user_catch.is_shiny:
                    user_catch.is_shiny = True
                    changed = True
                if anon.unown_forms_caught:
                    existing_unown = dict(user_catch.unown_forms_caught or {})
                    anon_unown = dict(anon.unown_forms_caught or {})
                    for k in ["normal", "shiny"]:
                        merged_set = set(existing_unown.get(k, [])) | set(anon_unown.get(k, []))
                        if merged_set:
                            existing_unown[k] = sorted(list(merged_set))
                    user_catch.unown_forms_caught = existing_unown
                    changed = True
                if changed:
                    user_catch.save()

            anon.delete()
            transferred_count += 1

    return transferred_count


def get_target_pokedex_url(request):
    """
    Determina la URL de destino adecuada tras autenticación o acceso de invitado:
    1. Si hay un parámetro 'next' seguro (que no sea login o portal), lo usa.
    2. Por defecto, redirige al selector de juegos central (/games/).
    """
    next_url = request.GET.get("next") or request.POST.get("next")
    if next_url:
        next_url = next_url.strip()
        # Rechazar URLs con barras invertidas o que inicien con doble barra para evitar redirección abierta
        if "\\" not in next_url and not next_url.startswith("//"):
            allowed_hosts = {request.get_host()}
            if url_has_allowed_host_and_scheme(url=next_url, allowed_hosts=allowed_hosts, require_https=request.is_secure()):
                if not next_url.startswith("/login") and next_url != "/":
                    return next_url

    return reverse("tracker:game_selector")


def auth_portal_view(request):
    """
    Portal de bienvenida, login y registro inicial en '/'.
    Permite iniciar sesión con usuario o correo, registrarse o continuar como invitado.
    """
    target_url = get_target_pokedex_url(request)
    active_tab = request.GET.get("tab", "login")

    login_form = HybridLoginForm(request=request)
    register_form = UserRegisterForm()

    if request.method == "POST":
        action = request.POST.get("action", "login")
        prev_session_key = request.session.session_key
        if action == "login":
            active_tab = "login"
            login_form = HybridLoginForm(request.POST, request=request)
            if login_form.is_valid():
                user = login_form.get_user()
                login(request, user)
                migrated = merge_session_catches_to_user(prev_session_key, user)
                if migrated > 0:
                    messages.success(request, f"¡Bienvenido de vuelta, {user.username}! Se transfirieron {migrated} capturas realizadas en esta sesión a tu cuenta.", extra_tags="notification catch_transfer")
                else:
                    messages.success(request, f"¡Bienvenido, Entrenador {user.username}!", extra_tags="notification welcome")
                return redirect(target_url)
        elif action == "register":
            active_tab = "register"
            register_form = UserRegisterForm(request.POST)
            if register_form.is_valid():
                user = register_form.save()
                login(request, user, backend="tracker.backends.EmailOrUsernameModelBackend")
                migrated = merge_session_catches_to_user(prev_session_key, user)
                if migrated > 0:
                    messages.success(request, f"¡Cuenta de Entrenador creada con éxito! Se guardaron {migrated} capturas previas en tu nueva cuenta.", extra_tags="notification catch_transfer")
                else:
                    messages.success(request, f"¡Bienvenido a Pokédex Global, Entrenador {user.username}! Tu progreso se guardará de forma personal e independiente.", extra_tags="notification welcome")
                return redirect(target_url)

    last_game_slug = request.session.get("last_game_slug", "red")
    context = {
        "login_form": login_form,
        "register_form": register_form,
        "active_tab": active_tab,
        "target_url": target_url,
        "last_game_slug": last_game_slug,
        "all_games": _get_cached_all_games(),
    }
    return render(request, "tracker/auth.html", context)


def register_view(request):
    """Acceso directo o alias a la pestaña de registro del portal."""
    if request.method == "POST":
        return auth_portal_view(request)
    next_param = request.GET.get("next")
    url = "/?tab=register"
    if next_param:
        url += f"&next={next_param}"
    return redirect(url)


def guest_continue_view(request):
    """Permite al usuario continuar a la Pokédex sin iniciar sesión (Modo Invitado)."""
    target_url = get_target_pokedex_url(request)
    return redirect(target_url)


@require_POST
def logout_view(request):
    """Cierra la sesión del usuario mediante método POST y lo redirige al portal de entrada."""
    username = request.user.username if request.user.is_authenticated else None
    logout(request)
    if username:
        messages.info(request, f"Sesión de {username} cerrada correctamente. ¡Hasta la próxima aventura!", extra_tags="portal")
    return redirect("tracker:home")


def game_selector_view(request):
    """
    Selector principal de juegos (Game Hub) en '/games/'.
    Presenta un banner central neutro con buscador en vivo de Pokémon y filtro por generación,
    así como una cuadrícula continua de 3 columnas de juegos de la saga principal con sus
    respectivas barras de progreso y mascotas oficiales.
    Optimizado con índices y totales en memoria LRU (0 ms I/O repetido).
    """
    user, session_key = _get_user_or_session(request)
    if user:
        user_filter = {"user": user}
    else:
        user_filter = {"session_key": session_key}

    # Obtener todas las capturas del usuario en una sola consulta
    user_catches = UserPokemonCatch.objects.filter(**user_filter, is_caught=True).values("game_slug", "entry_id")
    catches_by_game = {}
    for c in user_catches:
        g_slug = c["game_slug"]
        if g_slug not in catches_by_game:
            catches_by_game[g_slug] = set()
        catches_by_game[g_slug].add(c["entry_id"])

    # Juegos instalados y disponibles en la base de datos
    available_games = {g.slug: g for g in _get_cached_all_games()}

    games_cards = []

    for item in MAIN_SERIES_GAMES:
        g_slug = item["slug"]
        is_available = g_slug in available_games
        game_catches = catches_by_game.get(g_slug, set())
        has_started = len(game_catches) > 0

        card_data = dict(item)
        card_data["is_available"] = is_available
        card_data["has_started"] = has_started
        card_data["mascot_icon"] = f"/media/pokemon/icons/gen8/{item['mascot_num']}.png"
        card_data["mascot_artwork"] = f"/media/pokemon/artwork/{item['mascot_num']}.png"
        card_data["mascot_home_sprite"] = item.get("mascot_home_sprite", f"/media/pokemon/home/{item['mascot_num']}.png")
        card_data["platforms_str"] = ",".join(item.get("platforms", [item["platform"]]))

        if is_available:
            meta = _get_game_catalog_metadata(g_slug)
            reg_ids = meta["reg_ids"]
            nat_ids = meta["nat_ids"]
            reg_total = meta["reg_total"]
            nat_total = meta["nat_total"]

            reg_caught = len(game_catches.intersection(reg_ids))
            reg_percent = round((reg_caught / reg_total * 100), 1) if reg_total else 0.0

            has_national_dex = (item["generation"] >= 3)
            nat_total_dex = nat_total if has_national_dex else 0
            nat_caught = len(game_catches.intersection(nat_ids)) if has_national_dex else 0
            nat_percent = round((nat_caught / nat_total_dex * 100), 1) if nat_total_dex else 0.0

            card_data["has_national_dex"] = has_national_dex
            card_data["reg_total"] = reg_total
            card_data["reg_caught"] = reg_caught
            card_data["reg_percent"] = reg_percent
            card_data["nat_total"] = nat_total_dex
            card_data["nat_caught"] = nat_caught
            card_data["nat_percent"] = nat_percent
            card_data["button_label"] = "Continuar" if has_started else "Empezar"
            card_data["url"] = f"/{g_slug}/"
        else:
            card_data["header_bg"] = "bg-slate-500"
            card_data["header_text"] = "text-white font-black"
            card_data["card_bg"] = "#f8fafc"
            card_data["badge_bg"] = "bg-slate-600 text-white"
            card_data["border_color"] = "border-slate-500"
            card_data["progress_color"] = "bg-slate-500"
            card_data["has_national_dex"] = (item["generation"] >= 3)
            card_data["reg_total"] = 0
            card_data["reg_caught"] = 0
            card_data["reg_percent"] = 0.0
            card_data["nat_total"] = 0
            card_data["nat_caught"] = 0
            card_data["nat_percent"] = 0.0
            card_data["button_label"] = "No disponible"
            card_data["url"] = "#"

        games_cards.append(card_data)

    # Construir lista para buscador a partir de la estructura estática precalculada
    base_search_index = _get_base_pokemon_search_index()
    pokemon_search_list = []
    for p_num, base_item in base_search_index.items():
        entry_games = {}
        for g_slug, g_info in base_item["games"].items():
            if g_slug in available_games:
                eid = g_info["entry_id"]
                entry_games[g_slug] = {
                    "is_caught": eid in catches_by_game.get(g_slug, set()),
                    "method_badge": g_info.get("method_badge", "Salvaje"),
                }
        pokemon_search_list.append({
            "id": p_num,
            "name": base_item["name"],
            "games": entry_games,
        })
    pokemon_search_list.sort(key=lambda x: x["id"])

    # Agrupar tarjetas por generación y subgrupos cronológicos (Tríos, Dúos y Solitarios)
    cards_by_slug = {c["slug"]: c for c in games_cards}
    generation_groups = []
    for gen_meta in GENERATIONS_METADATA:
        gen_data = {
            "generation": gen_meta["generation"],
            "region_name": gen_meta["region_name"],
            "platform": gen_meta["platform"],
            "subgroups": [],
        }
        for sub in gen_meta["subgroups"]:
            subgroup_games = [cards_by_slug[s] for s in sub["slugs"] if s in cards_by_slug]
            if subgroup_games:
                gen_data["subgroups"].append({
                    "title": sub["title"],
                    "games": subgroup_games,
                    "count": len(subgroup_games),
                })
        generation_groups.append(gen_data)

    context = {
        "games_cards": games_cards,
        "generation_groups": generation_groups,
        "generations_list": [1, 2, 3, 4, 5, 6, 7, 8, 9],
        "available_consoles": AVAILABLE_CONSOLES,
        "pokemon_search_json": json.dumps(pokemon_search_list),
        "total_active_games": len(available_games),
        "total_main_games": len(MAIN_SERIES_GAMES),
    }
    return render(request, "tracker/game_selector.html", context)


def check_username(request):
    """
    Endpoint AJAX liviano para comprobar en tiempo real si un nombre de usuario
    está disponible o ya existe en la base de datos.
    Protegido contra enumeración mediante limitador de tasa (20 req/min por IP).
    """
    if not check_username_rate_limit(request):
        return JsonResponse({
            "available": False,
            "valid_format": False,
            "message": "Demasiadas consultas de disponibilidad. Por favor espera un momento."
        }, status=429)

    import re
    from django.contrib.auth import get_user_model
    User = get_user_model()

    raw_username = request.GET.get("username", "").strip()
    if not raw_username:
        return JsonResponse({"available": False, "valid_format": False, "message": "El nombre no puede estar vacío."})

    if len(raw_username) < 3:
        return JsonResponse({
            "available": False,
            "valid_format": False,
            "message": "El nombre debe tener al menos 3 caracteres."
        })

    if len(raw_username) > 25:
        return JsonResponse({
            "available": False,
            "valid_format": False,
            "message": "Máximo 25 caracteres permitidos."
        })

    if not re.match(r'^[a-zA-Z0-9_]+$', raw_username):
        return JsonResponse({
            "available": False,
            "valid_format": False,
            "message": "Solo se permiten letras, números y guiones bajos (_)."
        })

    exists = User.objects.filter(username__iexact=raw_username).exists()
    if exists:
        return JsonResponse({
            "available": False,
            "valid_format": True,
            "message": "Este nombre de entrenador ya no está disponible."
        })

    return JsonResponse({
        "available": True,
        "valid_format": True,
        "message": "¡Nombre de entrenador disponible!"
    })



def pokedex_view(request, game_slug="red", pokedex_slug=None):
    """Vista principal que lista los Pokémon de la Pokédex de un juego."""
    game = get_object_or_404(Game, slug=game_slug)
    request.session["last_game_slug"] = game.slug

    if pokedex_slug:
        pokedex = get_object_or_404(Pokedex, game=game, slug=pokedex_slug)
    else:
        pokedex = game.pokedexes.filter(is_national=False).first() or game.pokedexes.first()
        if not pokedex:
            pokedex = get_object_or_404(Pokedex, game=game)

    is_national = bool(pokedex.is_national or pokedex.slug == "national")

    # Entradas de la Pokédex obtenidas del catálogo compilado o caché en memoria (0 ms DB)
    force_refresh = request.GET.get("refresh") == "1" or request.GET.get("nocache") == "1"
    cached_entries = get_cached_pokedex_entries(
        game_slug=game.slug,
        is_national=is_national,
        force_refresh=force_refresh,
    )

    user, session_key = _get_user_or_session(request)

    # Base filter for current user/session
    user_filter = {"game_slug": game.slug}
    if user:
        user_filter["user"] = user
    else:
        user_filter["session_key"] = session_key

    # Consolidar capturas normales, shiny y formas de Unown en una sola consulta optimizada
    user_catches = list(
        UserPokemonCatch.objects.filter(**user_filter).values(
            "entry_id", "entry_number", "is_caught", "is_shiny", "unown_forms_caught"
        )
    )
    caught_entry_ids = {c["entry_id"] for c in user_catches if c["is_caught"]}
    shiny_caught_entry_ids = {c["entry_id"] for c in user_catches if c["is_shiny"]}
    catches_by_id = {c["entry_id"]: c for c in user_catches}
    catches_by_num = {c["entry_number"]: c for c in user_catches}

    # Copias superficiales ultra-rápidas (~1 ms) para anotar estado de captura específico del usuario de forma thread-safe
    entries_list = [copy.copy(e) for e in cached_entries]
    entries_by_num = {}
    for entry in entries_list:
        entry.is_caught = entry.id in caught_entry_ids
        entry.is_shiny_caught = entry.id in shiny_caught_entry_ids
        entries_by_num[entry.pokemon.national_number] = entry

    total_pokemon = len(entries_list)
    caught_count = len(caught_entry_ids)
    caught_percent = round((caught_count / total_pokemon * 100), 1) if total_pokemon else 0

    shiny_caught_count = len(shiny_caught_entry_ids)
    shiny_caught_percent = round((shiny_caught_count / total_pokemon * 100), 1) if total_pokemon else 0

    exclusives_info = get_version_exclusives_context(
        game, pokedex, caught_entry_ids, entries_by_num=entries_by_num, shiny_caught_entry_ids=shiny_caught_entry_ids
    )
    transfers_info = get_version_transfers_context(game, pokedex, caught_entry_ids, entries_by_num=entries_by_num)

    is_shinydex_active = False
    if game.generation >= 2:
        is_shinydex_active = request.COOKIES.get(f"pokedex_shinydex_{game.slug}") == "1"

    sprite_style = request.COOKIES.get("pokedex_sprite_style", "retro")
    is_modern_active = (sprite_style == "modern")

    # Catálogo de Unown para Gen >= 2
    unown_entry = None
    unown_catalog = []
    unown_chambers = {}
    unown_normal_caught = set()
    unown_shiny_caught = set()
    if game.generation >= 2:
        from .unown_data import get_unown_catalog, UNOWN_CHAMBERS, get_game_unown_chambers
        unown_chambers = get_game_unown_chambers(game.slug)
        unown_entry = entries_by_num.get(201)
        if unown_entry:
            reg_num = getattr(unown_entry, 'regional_number', unown_entry.entry_number)
            unown_data = (
                catches_by_id.get(unown_entry.id)
                or catches_by_num.get(reg_num)
                or catches_by_num.get(unown_entry.entry_number)
            )
            if unown_data and unown_data.get("unown_forms_caught"):
                forms_map = unown_data["unown_forms_caught"]
                unown_normal_caught = set(forms_map.get("normal", []))
                unown_shiny_caught = set(forms_map.get("shiny", []))

            raw_cat = get_unown_catalog(game_slug=game.slug)
            for item in raw_cat:
                l = item["letter"]
                item_copy = dict(item)
                item_copy["is_caught"] = l in unown_normal_caught
                item_copy["is_shiny_caught"] = l in unown_shiny_caught
                unown_catalog.append(item_copy)

    # Barra de Generaciones/Regiones para Pokédex Nacional (Gen >= 3)
    from .national_dex import get_national_regions_context
    requested_gen = request.GET.get("gen")
    session_gen_key = f"national_gen_{game.slug}"
    if not requested_gen:
        requested_gen = request.session.get(session_gen_key)

    national_regions_ctx = get_national_regions_context(
        game=game,
        pokedex=pokedex,
        entries_by_num=entries_by_num,
        caught_entry_ids=caught_entry_ids,
        shiny_caught_entry_ids=shiny_caught_entry_ids,
        requested_slug=requested_gen,
        is_shinydex=is_shinydex_active,
    )

    rendered_entries = entries_list
    if national_regions_ctx:
        active_slug = national_regions_ctx["active_slug"]
        if active_slug != "all":
            request.session[session_gen_key] = active_slug
        start_id, end_id = national_regions_ctx["active_range"]
        rendered_entries = [
            e for e in entries_list if start_id <= e.pokemon.national_number <= end_id
        ]

    context = {
        "game": game,
        "pokedex": pokedex,
        "game_pokedexes": list(game.pokedexes.all().order_by("id")),
        "entries": rendered_entries,
        "national_regions_ctx": national_regions_ctx,
        "caught_entry_ids": caught_entry_ids,
        "shiny_caught_entry_ids": shiny_caught_entry_ids,
        "total_pokemon": total_pokemon,
        "caught_count": caught_count,
        "caught_percent": caught_percent,
        "shiny_caught_count": shiny_caught_count,
        "shiny_caught_percent": shiny_caught_percent,
        "is_shinydex_active": is_shinydex_active,
        "is_modern_active": is_modern_active,
        "sprite_style": sprite_style,
        "all_games": _get_cached_all_games(),
        "exclusives_info": exclusives_info,
        "transfers_info": transfers_info,
        "evolution_stones_json": _get_cached_evolution_stones_json(),
        "is_johto": (game.generation == 2 or game.slug in ["gold", "silver", "crystal"]),
        "is_tanoby": (game.slug in ["firered", "leafgreen"]),
        "is_sinnoh": (game.generation == 4 or game.slug in ["diamond", "pearl", "platinum"]),
        "unown_entry": unown_entry,
        "unown_catalog": unown_catalog,
        "unown_chambers": unown_chambers,
        "unown_total_forms": len(unown_catalog) if unown_catalog else (28 if game.generation >= 3 else 26),
        "unown_normal_count": len(unown_normal_caught),
        "unown_normal_percent": round((len(unown_normal_caught) / (len(unown_catalog) if unown_catalog else 26) * 100), 1) if unown_catalog else 0,
        "unown_shiny_count": len(unown_shiny_caught),
        "unown_shiny_percent": round((len(unown_shiny_caught) / (len(unown_catalog) if unown_catalog else 26) * 100), 1) if unown_catalog else 0,
    }
    if request.headers.get("x-requested-with") == "XMLHttpRequest" or request.GET.get("partial") == "grid":
        response = render(request, "tracker/components/_pokemon_grid_partial.html", context)
        if national_regions_ctx:
            response["X-Active-Slug"] = national_regions_ctx["active_slug"]
        return response

    return render(request, "tracker/pokedex_detail.html", context)


@require_POST
def toggle_catch(request):
    """Endpoint AJAX para marcar/desmarcar un Pokémon como capturado (normal o shiny)."""
    try:
        data = json.loads(request.body)
        entry_id = data.get("entry_id")
        is_shiny = bool(data.get("is_shiny", False))
        target_status = data.get("target_status")
    except (ValueError, KeyError):
        return JsonResponse({"error": "Payload JSON inválido"}, status=400)

    entry = get_catalog_entry_by_id(entry_id)
    if not entry:
        return JsonResponse({"error": "Entrada de catálogo no encontrada"}, status=404)

    user, session_key = _get_user_or_session(request)

    filter_kwargs = {
        "game_slug": entry.game_slug,
        "entry_number": entry.entry_number,
    }
    if user:
        filter_kwargs["user"] = user
    else:
        filter_kwargs["session_key"] = session_key

    with transaction.atomic():
        catch_record, _ = UserPokemonCatch.objects.get_or_create(
            defaults={"is_caught": False, "is_shiny": False, "entry_id": entry.id},
            **filter_kwargs
        )
        if catch_record.entry_id != entry.id:
            catch_record.entry_id = entry.id

        # Alternar estado según la modalidad (normal vs shiny) o asignar estado explícito idempotente
        if is_shiny:
            new_status = bool(target_status) if target_status is not None else not catch_record.is_shiny
            catch_record.is_shiny = new_status
            catch_record.save(update_fields=["is_shiny", "entry_id"])
            stats_filter = {"game_slug": entry.game_slug, "is_shiny": True}
        else:
            new_status = bool(target_status) if target_status is not None else not catch_record.is_caught
            catch_record.is_caught = new_status
            catch_record.caught_at = timezone.now() if new_status else None
            catch_record.save(update_fields=["is_caught", "caught_at", "entry_id"])
            stats_filter = {"game_slug": entry.game_slug, "is_caught": True}

        if user:
            stats_filter["user"] = user
        else:
            stats_filter["session_key"] = session_key

        caught_count = UserPokemonCatch.objects.filter(**stats_filter).count()

    catalog = get_compiled_catalog(entry.game_slug) or []
    total_count = len(catalog)
    percent = round((caught_count / total_count * 100), 1) if total_count else 0

    return JsonResponse({
        "success": True,
        "entry_id": entry.id,
        "is_caught": new_status,
        "is_shiny": is_shiny,
        "caught_count": caught_count,
        "total_count": total_count,
        "percent": percent,
    })


@require_POST
def toggle_unown_catch(request):
    """Endpoint AJAX para marcar/desmarcar una forma específica de Unown (normal o shiny)."""
    try:
        data = json.loads(request.body)
        entry_id = data.get("entry_id")
        letter = str(data.get("letter", "")).lower().strip()
        is_shiny = bool(data.get("is_shiny", False))
        target_status = data.get("target_status")
    except (ValueError, KeyError, AttributeError):
        return JsonResponse({"error": "JSON inválido"}, status=400)

    valid_unown_letters = set([chr(c) for c in range(ord('a'), ord('z') + 1)] + ['exclamation', 'question'])
    if not entry_id or not letter or letter not in valid_unown_letters:
        return JsonResponse({"error": "Parámetros incompletos o letra inválida"}, status=400)

    entry = get_catalog_entry_by_id(entry_id)
    if not entry:
        return JsonResponse({"error": "Entrada de catálogo no encontrada"}, status=404)

    user, session_key = _get_user_or_session(request)

    filter_kwargs = {
        "game_slug": entry.game_slug,
        "entry_number": entry.entry_number,
    }
    if user:
        filter_kwargs["user"] = user
    else:
        filter_kwargs["session_key"] = session_key

    with transaction.atomic():
        catch_record, _ = UserPokemonCatch.objects.get_or_create(
            defaults={"is_caught": False, "is_shiny": False, "entry_id": entry.id, "unown_forms_caught": {}},
            **filter_kwargs
        )
        if catch_record.entry_id != entry.id:
            catch_record.entry_id = entry.id

        forms_data = dict(catch_record.unown_forms_caught or {})
        key = "shiny" if is_shiny else "normal"
        form_set = set(forms_data.get(key, []))

        if target_status is not None:
            if target_status:
                form_set.add(letter)
                is_now_caught = True
            else:
                form_set.discard(letter)
                is_now_caught = False
        else:
            if letter in form_set:
                form_set.remove(letter)
                is_now_caught = False
            else:
                form_set.add(letter)
                is_now_caught = True

        forms_data[key] = sorted(list(form_set))
        catch_record.unown_forms_caught = forms_data

        # Sincronizar captura general del Pokémon:
        catch_record.is_caught = len(forms_data.get("normal", [])) > 0
        catch_record.is_shiny = len(forms_data.get("shiny", [])) > 0
        if not is_shiny and is_now_caught and not catch_record.caught_at:
            catch_record.caught_at = timezone.now()
        catch_record.save()

    # Recalcular métricas generales de la Pokédex
    user_filter = {"game_slug": entry.game_slug}
    if user:
        user_filter["user"] = user
    else:
        user_filter["session_key"] = session_key

    catalog = get_compiled_catalog(entry.game_slug) or []
    total_pokemon = len(catalog)
    global_caught_count = UserPokemonCatch.objects.filter(**user_filter, is_caught=True).count()
    global_caught_percent = round((global_caught_count / total_pokemon * 100), 1) if total_pokemon else 0

    global_shiny_count = UserPokemonCatch.objects.filter(**user_filter, is_shiny=True).count()
    global_shiny_percent = round((global_shiny_count / total_pokemon * 100), 1) if total_pokemon else 0

    normal_unown_count = len(forms_data.get("normal", []))
    shiny_unown_count = len(forms_data.get("shiny", []))
    total_unown_forms = 28 if entry.game_slug in ["ruby", "sapphire", "emerald", "firered", "leafgreen", "diamond", "pearl", "platinum"] else 26

    return JsonResponse({
        "success": True,
        "entry_id": entry.id,
        "letter": letter,
        "is_shiny": is_shiny,
        "is_caught": is_now_caught,
        "unown_normal_count": normal_unown_count,
        "unown_normal_percent": round(normal_unown_count / total_unown_forms * 100, 1),
        "unown_shiny_count": shiny_unown_count,
        "unown_shiny_percent": round(shiny_unown_count / total_unown_forms * 100, 1),
        "unown_total_forms": total_unown_forms,
        "entry_is_caught": catch_record.is_caught,
        "entry_is_shiny": catch_record.is_shiny,
        "global_normal_caught": global_caught_count,
        "global_normal_percent": global_caught_percent,
        "global_shiny_caught": global_shiny_count,
        "global_shiny_percent": global_shiny_percent,
    })


def catalog_entry_modal(request, entry_id):
    """
    Retorna los datos del modal en formato JSON para carga bajo demanda (0 ms SQL).
    Soporta anotación dinámica del estado de captura del usuario o sesión actual.
    """
    entry = get_catalog_entry_by_id(entry_id)
    if not entry:
        return JsonResponse({"error": "Entrada de catálogo no encontrada"}, status=404)

    user, session_key = _get_user_or_session(request)
    user_filter = {"game_slug": entry.game_slug, "entry_number": entry.entry_number}
    if user:
        user_filter["user"] = user
    else:
        user_filter["session_key"] = session_key

    catch_rec = UserPokemonCatch.objects.filter(**user_filter).first()
    data = json.loads(entry.modal_data_json)
    data["is_caught"] = catch_rec.is_caught if catch_rec else False
    data["is_shiny_caught"] = catch_rec.is_shiny if catch_rec else False

    return JsonResponse(data, safe=False)
