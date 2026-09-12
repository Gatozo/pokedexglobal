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
        """Devuelve el nombre oficial en español del juego."""
        if self.slug in GAME_NAMES_ES:
            return GAME_NAMES_ES[self.slug]
        return self.name

    def __str__(self):
        return f"{self.display_name} (Gen {self.generation})"

    @property
    def has_retro_sprites(self):
        """Hasta la Gen 5 (Blanco/Negro 2) los juegos usaban sprites 2D."""
        return self.generation <= 5


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


class Pokemon(models.Model):
    national_number = models.PositiveIntegerField(unique=True, db_index=True)
    name = models.CharField(max_length=100)
    display_name = models.CharField(max_length=100)
    sprite_url = models.URLField(max_length=500)
    sprite_shiny_url = models.URLField(max_length=500, blank=True, null=True)
    primary_type = models.CharField(max_length=30)
    secondary_type = models.CharField(max_length=30, blank=True, null=True)
    height = models.PositiveIntegerField(null=True, blank=True, help_text="Altura en decímetros")
    weight = models.PositiveIntegerField(null=True, blank=True, help_text="Peso en hectogramos")
    raw_data = models.JSONField(default=dict, blank=True)

    class Meta:
        verbose_name = "Pokémon"
        verbose_name_plural = "Pokémon"
        ordering = ['national_number']

    def __str__(self):
        return f"#{self.national_number:03d} {self.display_name}"

    @property
    def primary_type_es(self):
        return TYPE_NAMES_ES.get(self.primary_type.lower(), self.primary_type.capitalize())

    @property
    def secondary_type_es(self):
        if self.secondary_type:
            return TYPE_NAMES_ES.get(self.secondary_type.lower(), self.secondary_type.capitalize())
        return None


class PokedexEntry(models.Model):
    pokedex = models.ForeignKey(Pokedex, on_delete=models.CASCADE, related_name="entries")
    pokemon = models.ForeignKey(Pokemon, on_delete=models.CASCADE, related_name="pokedex_appearances")
    entry_number = models.PositiveIntegerField()
    game_sprite_url = models.URLField(max_length=500, blank=True, null=True, help_text="Sprite específico de la generación/juego")

    class Meta:
        verbose_name = "Entrada de Pokédex"
        verbose_name_plural = "Entradas de Pokédex"
        ordering = ['entry_number']
        unique_together = ('pokedex', 'entry_number')
        indexes = [
            models.Index(fields=['pokedex', 'entry_number']),
        ]

    def __str__(self):
        return f"{self.pokedex.name} #{self.entry_number:03d}: {self.pokemon.display_name}"


class UserPokemonCatch(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name="catches")
    session_key = models.CharField(max_length=50, null=True, blank=True, db_index=True)
    pokedex_entry = models.ForeignKey(PokedexEntry, on_delete=models.CASCADE, related_name="user_catches")
    is_caught = models.BooleanField(default=False)
    is_shiny = models.BooleanField(default=False)
    caught_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Captura de Usuario"
        verbose_name_plural = "Capturas de Usuarios"
        indexes = [
            models.Index(fields=['user', 'pokedex_entry']),
            models.Index(fields=['session_key', 'pokedex_entry']),
        ]

    def __str__(self):
        owner = self.user.username if self.user else f"Anon ({self.session_key[:8]})"
        status = "Capturado" if self.is_caught else "Pendiente"
        return f"{owner} - {self.pokedex_entry} [{status}]"

    def mark_caught(self, caught=True):
        self.is_caught = caught
        self.caught_at = timezone.now() if caught else None
        self.save(update_fields=['is_caught', 'caught_at'])

