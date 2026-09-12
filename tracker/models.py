from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


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

    def __str__(self):
        return f"{self.name} (Gen {self.generation})"


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


class PokedexEntry(models.Model):
    pokedex = models.ForeignKey(Pokedex, on_delete=models.CASCADE, related_name="entries")
    pokemon = models.ForeignKey(Pokemon, on_delete=models.CASCADE, related_name="pokedex_appearances")
    entry_number = models.PositiveIntegerField()

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

