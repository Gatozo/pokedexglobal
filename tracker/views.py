import copy
import json
from django.conf import settings
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.core.cache import cache
from django.contrib.auth import login, logout
from django.contrib import messages
from .models import Game, Pokedex, UserPokemonCatch
from .forms import HybridLoginForm, UserRegisterForm
from .catalog_service import get_compiled_catalog, get_catalog_entry_by_id
from .exclusives import get_version_exclusives_context, get_version_transfers_context



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


def get_cached_pokedex_entries(pokedex_id=None, force_refresh=False, game_slug="", is_national=False):
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
    if not session_key:
        return 0

    anon_catches = list(UserPokemonCatch.objects.filter(session_key=session_key, user__isnull=True))
    if not anon_catches:
        return 0

    transferred_count = 0
    for anon in anon_catches:
        user_catch, created = UserPokemonCatch.objects.get_or_create(
            user=user,
            game_slug=anon.game_slug,
            entry_number=anon.entry_number,
            defaults={
                "entry_id": anon.entry_id,
                "is_caught": anon.is_caught,
                "is_shiny": anon.is_shiny,
                "unown_forms_caught": anon.unown_forms_caught,
                "caught_at": anon.caught_at,
            }
        )
        if not created:
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
    Determina la URL de destino adecuada:
    1. Si hay un parámetro 'next' seguro, lo usa.
    2. Si hay un último juego visitado en sesión ('last_game_slug'), va a ese juego.
    3. Por defecto, va a 'red' (/red/).
    """
    next_url = request.GET.get("next") or request.POST.get("next")
    if next_url and next_url.startswith("/") and not next_url.startswith("//") and not next_url.startswith("/login"):
        return next_url

    last_game = request.session.get("last_game_slug")
    if last_game:
        games = _get_cached_all_games()
        if any(g.slug == last_game for g in games):
            return f"/{last_game}/"

    return "/red/"


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
                    messages.success(request, f"¡Bienvenido de vuelta, {user.username}! Se transfirieron {migrated} capturas realizadas en esta sesión a tu cuenta.")
                else:
                    messages.success(request, f"¡Bienvenido, Entrenador {user.username}!")
                return redirect(target_url)
        elif action == "register":
            active_tab = "register"
            register_form = UserRegisterForm(request.POST)
            if register_form.is_valid():
                user = register_form.save()
                login(request, user, backend="tracker.backends.EmailOrUsernameModelBackend")
                migrated = merge_session_catches_to_user(prev_session_key, user)
                if migrated > 0:
                    messages.success(request, f"¡Cuenta de Entrenador creada con éxito! Se guardaron {migrated} capturas previas en tu nueva cuenta.")
                else:
                    messages.success(request, f"¡Bienvenido a Pokédex Global, Entrenador {user.username}! Tu progreso se guardará de forma personal e independiente.")
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


def logout_view(request):
    """Cierra la sesión del usuario y lo redirige al portal de entrada."""
    username = request.user.username if request.user.is_authenticated else None
    logout(request)
    if username:
        messages.info(request, f"Sesión de {username} cerrada correctamente. ¡Hasta la próxima aventura!")
    return redirect("tracker:home")


def check_username(request):
    """
    Endpoint AJAX liviano para comprobar en tiempo real si un nombre de usuario
    está disponible o ya existe en la base de datos.
    """
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
        pokedex.id,
        force_refresh=force_refresh,
        game_slug=game.slug,
        is_national=is_national,
    )

    user, session_key = _get_user_or_session(request)

    # Base filter for current user/session
    user_filter = {"game_slug": game.slug}
    if user:
        user_filter["user"] = user
    else:
        user_filter["session_key"] = session_key

    # Obtener IDs de las entradas capturadas normales y shiny por el usuario actual
    caught_entry_ids = set(
        UserPokemonCatch.objects.filter(**user_filter, is_caught=True).values_list("entry_id", flat=True)
    )
    shiny_caught_entry_ids = set(
        UserPokemonCatch.objects.filter(**user_filter, is_shiny=True).values_list("entry_id", flat=True)
    )

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

    # Catálogo de Unown para Gen >= 2
    unown_entry = None
    unown_catalog = []
    unown_chambers = {}
    unown_normal_caught = set()
    unown_shiny_caught = set()
    if game.generation >= 2:
        from .unown_data import get_unown_catalog, UNOWN_CHAMBERS
        unown_chambers = UNOWN_CHAMBERS
        unown_entry = entries_by_num.get(201)
        if unown_entry:
            unown_catch = UserPokemonCatch.objects.filter(**user_filter, entry_id=unown_entry.id).first()
            if not unown_catch:
                reg_num = getattr(unown_entry, 'regional_number', unown_entry.entry_number)
                unown_catch = UserPokemonCatch.objects.filter(**user_filter, entry_number=reg_num).first()
            if not unown_catch:
                unown_catch = UserPokemonCatch.objects.filter(**user_filter, entry_number=unown_entry.entry_number).first()
            if unown_catch and unown_catch.unown_forms_caught:
                unown_normal_caught = set(unown_catch.unown_forms_caught.get("normal", []))
                unown_shiny_caught = set(unown_catch.unown_forms_caught.get("shiny", []))

            raw_cat = get_unown_catalog(game_slug=game.slug)
            for item in raw_cat:
                l = item["letter"]
                item_copy = dict(item)
                item_copy["is_caught"] = l in unown_normal_caught
                item_copy["is_shiny_caught"] = l in unown_shiny_caught
                unown_catalog.append(item_copy)

    context = {
        "game": game,
        "pokedex": pokedex,
        "game_pokedexes": list(game.pokedexes.all().order_by("id")),
        "entries": entries_list,
        "caught_entry_ids": caught_entry_ids,
        "shiny_caught_entry_ids": shiny_caught_entry_ids,
        "total_pokemon": total_pokemon,
        "caught_count": caught_count,
        "caught_percent": caught_percent,
        "shiny_caught_count": shiny_caught_count,
        "shiny_caught_percent": shiny_caught_percent,
        "is_shinydex_active": is_shinydex_active,
        "all_games": _get_cached_all_games(),
        "exclusives_info": exclusives_info,
        "transfers_info": transfers_info,
        "evolution_stones_json": _get_cached_evolution_stones_json(),
        "is_johto": (game.generation == 2 or game.slug in ["gold", "silver", "crystal"]),
        "unown_entry": unown_entry,
        "unown_catalog": unown_catalog,
        "unown_chambers": unown_chambers,
        "unown_total_forms": len(unown_catalog) if unown_catalog else (28 if game.generation >= 3 else 26),
        "unown_normal_count": len(unown_normal_caught),
        "unown_normal_percent": round((len(unown_normal_caught) / (len(unown_catalog) if unown_catalog else 26) * 100), 1) if unown_catalog else 0,
        "unown_shiny_count": len(unown_shiny_caught),
        "unown_shiny_percent": round((len(unown_shiny_caught) / (len(unown_catalog) if unown_catalog else 26) * 100), 1) if unown_catalog else 0,
    }
    return render(request, "tracker/pokedex_detail.html", context)


@require_POST
def toggle_catch(request):
    """Endpoint AJAX para marcar/desmarcar un Pokémon como capturado (normal o shiny)."""
    try:
        data = json.loads(request.body)
        entry_id = data.get("entry_id")
        is_shiny = bool(data.get("is_shiny", False))
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

    catch_record, _ = UserPokemonCatch.objects.get_or_create(
        defaults={"is_caught": False, "is_shiny": False, "entry_id": entry.id},
        **filter_kwargs
    )
    if catch_record.entry_id != entry.id:
        catch_record.entry_id = entry.id

    # Alternar estado según la modalidad (normal vs shiny)
    if is_shiny:
        new_status = not catch_record.is_shiny
        catch_record.is_shiny = new_status
        catch_record.save(update_fields=["is_shiny", "entry_id"])
        stats_filter = {"game_slug": entry.game_slug, "is_shiny": True}
    else:
        new_status = not catch_record.is_caught
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

    catch_record, _ = UserPokemonCatch.objects.get_or_create(
        defaults={"is_caught": False, "is_shiny": False, "entry_id": entry.id, "unown_forms_caught": {}},
        **filter_kwargs
    )
    if catch_record.entry_id != entry.id:
        catch_record.entry_id = entry.id

    forms_data = dict(catch_record.unown_forms_caught or {})
    key = "shiny" if is_shiny else "normal"
    form_set = set(forms_data.get(key, []))

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
    total_unown_forms = 28 if entry.game_slug in ["ruby", "sapphire", "emerald", "firered", "leafgreen"] else 26

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
