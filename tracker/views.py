import copy
import json
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.core.cache import cache
from .models import Game, Pokedex, PokedexEntry, UserPokemonCatch
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
        cache.set("all_games_catalog", games, timeout=86400)
    return games


def get_cached_pokedex_entries(pokedex_id):
    """
    Retorna la lista base de entradas de la Pokédex desde la caché en memoria.
    Evita consultas SQL y deserialización en cada cambio de juego.
    """
    cache_key = f"pokedex_entries_base_{pokedex_id}"
    entries = cache.get(cache_key)
    if entries is None:
        entries = list(
            PokedexEntry.objects.filter(pokedex_id=pokedex_id)
            .select_related("pokemon", "pokedex__game")
            .defer(
                "pokemon__raw_data",
                "pokemon__species_data",
                "pokemon__encounters_data",
                "pokemon__evolution_chain_data",
                "game_data",
            )
            .order_by("entry_number")
        )
        cache.set(cache_key, entries, timeout=86400)
    return entries


_STONES_JSON_CACHE = None


def _get_cached_evolution_stones_json():
    global _STONES_JSON_CACHE
    if _STONES_JSON_CACHE is None:
        from .utils import get_evolution_stones_catalog
        _STONES_JSON_CACHE = json.dumps(get_evolution_stones_catalog())
    return _STONES_JSON_CACHE


def pokedex_view(request, game_slug="red", pokedex_slug=None):
    """Vista principal que lista los Pokémon de la Pokédex de un juego."""
    game = get_object_or_404(Game, slug=game_slug)
    if pokedex_slug:
        pokedex = get_object_or_404(Pokedex, game=game, slug=pokedex_slug)
    else:
        pokedex = game.pokedexes.first()
        if not pokedex:
            pokedex = get_object_or_404(Pokedex, game=game)

    # Entradas de la Pokédex obtenidas de la caché en memoria (0 ms DB)
    cached_entries = get_cached_pokedex_entries(pokedex.id)

    user, session_key = _get_user_or_session(request)

    # Base filter for current user/session
    user_filter = {"pokedex_entry__pokedex": pokedex}
    if user:
        user_filter["user"] = user
    else:
        user_filter["session_key"] = session_key

    # Obtener IDs de las entradas capturadas normales y shiny por el usuario actual
    caught_entry_ids = set(
        UserPokemonCatch.objects.filter(**user_filter, is_caught=True).values_list("pokedex_entry_id", flat=True)
    )
    shiny_caught_entry_ids = set(
        UserPokemonCatch.objects.filter(**user_filter, is_shiny=True).values_list("pokedex_entry_id", flat=True)
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
            unown_catch = UserPokemonCatch.objects.filter(**user_filter, pokedex_entry=unown_entry).first()
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
        "unown_entry": unown_entry,
        "unown_catalog": unown_catalog,
        "unown_chambers": unown_chambers,
        "unown_normal_count": len(unown_normal_caught),
        "unown_normal_percent": round((len(unown_normal_caught) / 26 * 100), 1) if unown_catalog else 0,
        "unown_shiny_count": len(unown_shiny_caught),
        "unown_shiny_percent": round((len(unown_shiny_caught) / 26 * 100), 1) if unown_catalog else 0,
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

    entry = get_object_or_404(PokedexEntry, id=entry_id)
    user, session_key = _get_user_or_session(request)

    filter_kwargs = {"pokedex_entry": entry}
    if user:
        filter_kwargs["user"] = user
    else:
        filter_kwargs["session_key"] = session_key

    catch_record, _ = UserPokemonCatch.objects.get_or_create(
        defaults={"is_caught": False, "is_shiny": False},
        **filter_kwargs
    )

    # Alternar estado según la modalidad (normal vs shiny)
    if is_shiny:
        new_status = not catch_record.is_shiny
        catch_record.is_shiny = new_status
        catch_record.save(update_fields=["is_shiny"])
        stats_filter = {"pokedex_entry__pokedex": entry.pokedex, "is_shiny": True}
    else:
        new_status = not catch_record.is_caught
        catch_record.is_caught = new_status
        catch_record.caught_at = timezone.now() if new_status else None
        catch_record.save(update_fields=["is_caught", "caught_at"])
        stats_filter = {"pokedex_entry__pokedex": entry.pokedex, "is_caught": True}

    if user:
        stats_filter["user"] = user
    else:
        stats_filter["session_key"] = session_key

    caught_count = UserPokemonCatch.objects.filter(**stats_filter).count()
    total_count = entry.pokedex.entries.count()
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

    if not entry_id or not letter or len(letter) != 1 or not ('a' <= letter <= 'z'):
        return JsonResponse({"error": "Parámetros incompletos o letra inválida"}, status=400)

    entry = get_object_or_404(PokedexEntry, id=entry_id)
    user, session_key = _get_user_or_session(request)

    filter_kwargs = {"pokedex_entry": entry}
    if user:
        filter_kwargs["user"] = user
    else:
        filter_kwargs["session_key"] = session_key

    catch_record, _ = UserPokemonCatch.objects.get_or_create(
        defaults={"is_caught": False, "is_shiny": False, "unown_forms_caught": {}},
        **filter_kwargs
    )

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
    user_filter = {"pokedex_entry__pokedex": entry.pokedex}
    if user:
        user_filter["user"] = user
    else:
        user_filter["session_key"] = session_key

    total_pokemon = entry.pokedex.entries.count()
    global_caught_count = UserPokemonCatch.objects.filter(**user_filter, is_caught=True).count()
    global_caught_percent = round((global_caught_count / total_pokemon * 100), 1) if total_pokemon else 0

    global_shiny_count = UserPokemonCatch.objects.filter(**user_filter, is_shiny=True).count()
    global_shiny_percent = round((global_shiny_count / total_pokemon * 100), 1) if total_pokemon else 0

    normal_unown_count = len(forms_data.get("normal", []))
    shiny_unown_count = len(forms_data.get("shiny", []))

    return JsonResponse({
        "success": True,
        "entry_id": entry.id,
        "letter": letter,
        "is_shiny": is_shiny,
        "is_caught": is_now_caught,
        "unown_normal_count": normal_unown_count,
        "unown_normal_percent": round(normal_unown_count / 26 * 100, 1),
        "unown_shiny_count": shiny_unown_count,
        "unown_shiny_percent": round(shiny_unown_count / 26 * 100, 1),
        "entry_is_caught": catch_record.is_caught,
        "entry_is_shiny": catch_record.is_shiny,
        "global_normal_caught": global_caught_count,
        "global_normal_percent": global_caught_percent,
        "global_shiny_caught": global_shiny_count,
        "global_shiny_percent": global_shiny_percent,
    })
