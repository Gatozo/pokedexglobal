from django.contrib import admin
from django.contrib import messages
from django.shortcuts import redirect
from django.urls import path
from .models import Game, Pokedex, UserPokemonCatch
from .fixtures_util import export_tracker_fixtures, get_fixture_info


@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'generation', 'created_at')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)
    list_filter = ('generation',)


@admin.register(Pokedex)
class PokedexAdmin(admin.ModelAdmin):
    list_display = ('name', 'game', 'slug', 'is_national', 'pokeapi_name')
    list_filter = ('game', 'is_national')
    search_fields = ('name', 'game__name')


@admin.register(UserPokemonCatch)
class UserPokemonCatchAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'session_key', 'game_slug', 'entry_number', 'entry_id', 'is_caught', 'is_shiny', 'caught_at')
    list_filter = ('is_caught', 'is_shiny', 'game_slug')
    search_fields = ('user__username', 'session_key', 'game_slug', 'entry_number')


def export_fixtures_admin_view(request):
    """
    Vista administrativa protegida para generar o actualizar el fixture de la Pokédex.
    Solo accesible para superusuarios mediante petición POST.
    """
    if not request.user.is_superuser:
        messages.error(request, "Solo los superadministradores pueden exportar los respaldos.")
        return redirect('admin:index')

    if request.method == 'POST':
        try:
            info = export_tracker_fixtures()
            messages.success(
                request,
                f"Respaldo actualizado con éxito: {info['records_count']} registros exportados en '{info['relative_path']}' ({info['size_human']}). Listo para hacer git commit."
            )
        except Exception as e:
            messages.error(request, f"Error al exportar el respaldo: {str(e)}")

    return redirect('admin:index')


# Personalizar admin.site para inyectar la URL del respaldo y el estado del fixture en el contexto
_original_admin_get_urls = admin.site.get_urls
_original_admin_each_context = admin.site.each_context


def _custom_admin_get_urls():
    custom_urls = [
        path(
            'tracker/export-fixtures/',
            admin.site.admin_view(export_fixtures_admin_view),
            name='export_fixtures',
        ),
    ]
    return custom_urls + _original_admin_get_urls()


def _custom_admin_each_context(request):
    context = _original_admin_each_context(request)
    context['fixture_info'] = get_fixture_info()
    return context


admin.site.get_urls = _custom_admin_get_urls
admin.site.each_context = _custom_admin_each_context

