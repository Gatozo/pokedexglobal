import json
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone
from .models import Game, Pokedex, PokedexEntry, UserPokemonCatch
from .exclusives import get_version_exclusives_context


def _get_user_or_session(request):
    """Devuelve una tupla (user, session_key) según el estado de autenticación."""
    if request.user.is_authenticated:
        return request.user, None
    if not request.session.session_key:
        request.session.save()
    return None, request.session.session_key


def pokedex_view(request, game_slug="red", pokedex_slug="kanto"):
    """Vista principal que lista los Pokémon de la Pokédex de un juego."""
    game = get_object_or_404(Game, slug=game_slug)
    pokedex = get_object_or_404(Pokedex, game=game, slug=pokedex_slug)

    # Entradas de la Pokédex optimizadas con su respectivo Pokémon
    entries = pokedex.entries.select_related("pokemon").order_by("entry_number")

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

    # Anotar cada entrada con su estado para la plantilla
    entries_list = list(entries)
    for entry in entries_list:
        entry.is_caught = entry.id in caught_entry_ids

    total_pokemon = len(entries_list)
    caught_count = len(caught_entry_ids)
    caught_percent = round((caught_count / total_pokemon * 100), 1) if total_pokemon else 0

    exclusives_info = get_version_exclusives_context(game, pokedex, caught_entry_ids)

    from .utils import get_evolution_stones_catalog
    evolution_stones_json = json.dumps(get_evolution_stones_catalog())

    context = {
        "game": game,
        "pokedex": pokedex,
        "entries": entries_list,
        "caught_entry_ids": caught_entry_ids,
        "total_pokemon": total_pokemon,
        "caught_count": caught_count,
        "caught_percent": caught_percent,
        "all_games": Game.objects.all(),
        "exclusives_info": exclusives_info,
        "evolution_stones_json": evolution_stones_json,
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
