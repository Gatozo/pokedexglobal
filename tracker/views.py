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

    # Obtener IDs de las entradas capturadas por el usuario actual
    catch_filter = {"pokedex_entry__pokedex": pokedex, "is_caught": True}
    if user:
        catch_filter["user"] = user
    else:
        catch_filter["session_key"] = session_key

    caught_entry_ids = set(
        UserPokemonCatch.objects.filter(**catch_filter).values_list("pokedex_entry_id", flat=True)
    )

    # Copias superficiales ultra-rápidas (~1 ms) para anotar estado de captura específico del usuario de forma thread-safe
    entries_list = [copy.copy(e) for e in cached_entries]
    entries_by_num = {}
    for entry in entries_list:
        entry.is_caught = entry.id in caught_entry_ids
        entries_by_num[entry.pokemon.national_number] = entry

    total_pokemon = len(entries_list)
    caught_count = len(caught_entry_ids)
    caught_percent = round((caught_count / total_pokemon * 100), 1) if total_pokemon else 0

    exclusives_info = get_version_exclusives_context(game, pokedex, caught_entry_ids, entries_by_num=entries_by_num)
    transfers_info = get_version_transfers_context(game, pokedex, caught_entry_ids, entries_by_num=entries_by_num)

    context = {
        "game": game,
        "pokedex": pokedex,
        "game_pokedexes": list(game.pokedexes.all().order_by("id")),
        "entries": entries_list,
        "caught_entry_ids": caught_entry_ids,
        "total_pokemon": total_pokemon,
        "caught_count": caught_count,
        "caught_percent": caught_percent,
        "all_games": _get_cached_all_games(),
        "exclusives_info": exclusives_info,
        "transfers_info": transfers_info,
        "evolution_stones_json": _get_cached_evolution_stones_json(),
    }
    return render(request, "tracker/pokedex_detail.html", context)


@require_POST
def toggle_catch(request):
    """Endpoint AJAX para marcar/desmarcar un Pokémon como capturado."""
    try:
        data = json.loads(request.body)
        entry_id = data.get("entry_id")
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
        defaults={"is_caught": False},
        **filter_kwargs
    )

    # Alternar estado
    new_status = not catch_record.is_caught
    catch_record.is_caught = new_status
    catch_record.caught_at = timezone.now() if new_status else None
    catch_record.save(update_fields=["is_caught", "caught_at"])

    # Recalcular totales para la Pokédex actual
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
        "caught_count": caught_count,
        "total_count": total_count,
        "percent": percent,
    })
