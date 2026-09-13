from django.contrib import admin
from .models import Game, Pokedex, Pokemon, PokedexEntry, UserPokemonCatch, Move


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


@admin.register(Pokemon)
class PokemonAdmin(admin.ModelAdmin):
    list_display = ('national_number', 'display_name', 'primary_type', 'secondary_type')
    search_fields = ('display_name', 'name', 'national_number')
    list_filter = ('primary_type', 'secondary_type')
    ordering = ('national_number',)


@admin.register(PokedexEntry)
class PokedexEntryAdmin(admin.ModelAdmin):
    list_display = ('pokedex', 'entry_number', 'pokemon', 'primary_type', 'is_custom_override')
    list_filter = ('pokedex__game', 'pokedex', 'is_custom_override', 'primary_type')
    list_editable = ('is_custom_override',)
    search_fields = ('pokemon__display_name', 'pokemon__name', 'entry_number')
    ordering = ('pokedex', 'entry_number')
    readonly_fields = ('pokedex', 'pokemon', 'entry_number')
    fields = ('pokedex', 'pokemon', 'entry_number', 'is_custom_override', 'flavor_text', 'obtaining_info', 'primary_type', 'secondary_type')



@admin.register(UserPokemonCatch)
class UserPokemonCatchAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'session_key', 'pokedex_entry', 'is_caught', 'caught_at')
    list_filter = ('is_caught', 'pokedex_entry__pokedex')
    search_fields = ('user__username', 'session_key', 'pokedex_entry__pokemon__display_name')


@admin.register(Move)
class MoveAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'display_name', 'type', 'power', 'accuracy', 'pp')
    list_filter = ('type', 'generation', 'damage_class')
    search_fields = ('name', 'display_name')
    ordering = ('id',)

