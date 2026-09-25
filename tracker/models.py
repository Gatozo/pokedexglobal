from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


GAME_NAMES_ES = {
    # Gen 1
    'red': 'Pokémon Rojo',
    'blue': 'Pokémon Azul',
    'yellow': 'Pokémon Amarillo',
    # Gen 2
    'gold': 'Pokémon Oro',
    'silver': 'Pokémon Plata',
    'crystal': 'Pokémon Cristal',
    # Gen 3
    'ruby': 'Pokémon Rubí',
    'sapphire': 'Pokémon Zafiro',
    'emerald': 'Pokémon Esmeralda',
    'firered': 'Pokémon Rojo Fuego',
    'leafgreen': 'Pokémon Verde Hoja',
    # Gen 4
    'diamond': 'Pokémon Diamante',
    'pearl': 'Pokémon Perla',
    'platinum': 'Pokémon Platino',
    'heartgold': 'Pokémon Oro HeartGold',
    'soulsilver': 'Pokémon Plata SoulSilver',
    # Gen 5
    'black': 'Pokémon Negro',
    'white': 'Pokémon Blanco',
    'black-2': 'Pokémon Negro 2',
    'white-2': 'Pokémon Blanco 2',
    # Gen 6
    'x': 'Pokémon X',
    'y': 'Pokémon Y',
    'omega-ruby': 'Pokémon Rubí Omega',
    'alpha-sapphire': 'Pokémon Zafiro Alfa',
    # Gen 7
    'sun': 'Pokémon Sol',
    'moon': 'Pokémon Luna',
    'ultra-sun': 'Pokémon Ultra Sol',
    'ultra-moon': 'Pokémon Ultra Luna',
    'lets-go-pikachu': "Pokémon: Let's Go, Pikachu!",
    'lets-go-eevee': "Pokémon: Let's Go, Eevee!",
    # Gen 8
    'sword': 'Pokémon Espada',
    'shield': 'Pokémon Escudo',
    'brilliant-diamond': 'Pokémon Diamante Brillante',
    'shining-pearl': 'Pokémon Perla Reluciente',
    'legends-arceus': 'Leyendas Pokémon: Arceus',
    # Gen 9
    'scarlet': 'Pokémon Escarlata',
    'violet': 'Pokémon Púrpura',
}

TYPE_NAMES_ES = {
    'normal': 'Normal',
    'fire': 'Fuego',
    'water': 'Agua',
    'grass': 'Planta',
    'electric': 'Eléctrico',
    'ice': 'Hielo',
    'fighting': 'Lucha',
    'poison': 'Veneno',
    'ground': 'Tierra',
    'flying': 'Volador',
    'psychic': 'Psíquico',
    'bug': 'Bicho',
    'rock': 'Roca',
    'ghost': 'Fantasma',
    'dragon': 'Dragón',
    'steel': 'Acero',
    'fairy': 'Hada',
    'dark': 'Siniestro',
}


from .utils import resolve_game_display_name


class Game(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    generation = models.PositiveSmallIntegerField(default=1)
    cover_image = models.URLField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Juego"
        verbose_name_plural = "Juegos"
        ordering = ['generation', 'name']

    @property
    def display_name(self):
        """Devuelve el nombre oficial del juego con fallback idiomático (es -> custom/en -> slug)."""
        return resolve_game_display_name(
            game_slug=self.slug,
            custom_name=self.name,
            game_translations_map=GAME_NAMES_ES
        )

    def __str__(self):
        return f"{self.display_name} (Gen {self.generation})"

    @property
    def has_retro_sprites(self):
        """Hasta la Gen 5 (Blanco/Negro 2) los juegos usaban sprites 2D."""
        return self.generation <= 5

    @property
    def has_safari_zone(self):
        """Determina si este juego cuenta con Zona Safari activa."""
        return self.slug in [
            "red", "blue", "yellow",
            "firered", "leafgreen",
            "ruby", "sapphire", "emerald",
            "diamond", "pearl", "platinum",
            "heartgold", "soulsilver"
        ]


class Pokedex(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name="pokedexes")
    name = models.CharField(max_length=100)
    slug = models.SlugField()
    is_national = models.BooleanField(default=False)
    pokeapi_name = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Pokédex"
        verbose_name_plural = "Pokédexes"
        unique_together = ('game', 'slug')
        ordering = ['game', 'id']

    def __str__(self):
        return f"{self.name} - {self.game.name}"


def _get_existing_icons():
    from .catalog_service import get_existing_icons
    return get_existing_icons()


def _get_existing_cries():
    from .catalog_service import get_existing_cries
    return get_existing_cries()


class UserPokemonCatch(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name="catches")
    session_key = models.CharField(max_length=50, null=True, blank=True, db_index=True)
    game_slug = models.CharField(max_length=30, default="", db_index=True)
    entry_number = models.PositiveIntegerField(default=0, db_index=True)
    entry_id = models.PositiveIntegerField(default=0, db_index=True)
    is_caught = models.BooleanField(default=False)
    is_shiny = models.BooleanField(default=False)
    unown_forms_caught = models.JSONField(default=dict, blank=True, help_text="Formas capturadas de Unown: {'normal': [...], 'shiny': [...]}")
    caught_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Captura de Usuario"
        verbose_name_plural = "Capturas de Usuarios"
        indexes = [
            models.Index(fields=['user', 'game_slug']),
            models.Index(fields=['session_key', 'game_slug']),
            models.Index(fields=['game_slug', 'entry_id']),
            models.Index(fields=['game_slug', 'entry_number']),
        ]

    def __str__(self):
        owner = self.user.username if self.user else f"Anon ({self.session_key[:8]})"
        status = "Capturado" if self.is_caught else "Pendiente"
        return f"{owner} - [{self.game_slug}] #{self.entry_number} [{status}]"

    def mark_caught(self, caught=True):
        self.is_caught = caught
        self.caught_at = timezone.now() if caught else None
        self.save(update_fields=['is_caught', 'caught_at'])


from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache


@receiver([post_save, post_delete], sender=Game)
def _invalidate_games_cache(sender, **kwargs):
    cache.delete("all_games_catalog")


# Clases shim no-modelo para retrocompatibilidad con scripts legacy (cero impacto en base de datos)
class MockCatalogManager:
    def __init__(self):
        self._items = []
    def get(self, *args, **kwargs):
        raise NotImplementedError("Las tablas del catálogo fueron migradas a JSON estáticos en Plan C. Usa catalog_service.")
    def filter(self, *args, **kwargs):
        return self
    def select_related(self, *args, **kwargs):
        return self
    def order_by(self, *args, **kwargs):
        return self
    def defer(self, *args, **kwargs):
        return self
    def all(self):
        return self
    def count(self):
        return 0
    def exists(self):
        return False
    def first(self):
        return None
    def __iter__(self):
        return iter(self._items)
    def __len__(self):
        return 0


class Pokemon:
    objects = MockCatalogManager()


class PokedexEntry:
    objects = MockCatalogManager()


class Move:
    objects = MockCatalogManager()




