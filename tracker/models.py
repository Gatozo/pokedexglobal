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


_EXISTING_ICONS_SET = None
_EXISTING_CRIES_SET = None


def _get_existing_icons():
    global _EXISTING_ICONS_SET
    if _EXISTING_ICONS_SET is None:
        from django.conf import settings
        from pathlib import Path
        icons_dir = Path(settings.MEDIA_ROOT) / "pokemon" / "icons"
        _EXISTING_ICONS_SET = set()
        if icons_dir.exists():
            for p in icons_dir.glob("*/*.png"):
                _EXISTING_ICONS_SET.add((p.parent.name, p.name))
    return _EXISTING_ICONS_SET


def _get_existing_cries():
    global _EXISTING_CRIES_SET
    if _EXISTING_CRIES_SET is None:
        from django.conf import settings
        from pathlib import Path
        cries_dir = Path(settings.MEDIA_ROOT) / "pokemon" / "cries"
        _EXISTING_CRIES_SET = set()
        if cries_dir.exists():
            for p in cries_dir.glob("*/*.*"):
                _EXISTING_CRIES_SET.add((p.parent.name, p.name))
    return _EXISTING_CRIES_SET


class Pokemon(models.Model):
    national_number = models.PositiveIntegerField(unique=True, db_index=True)
    name = models.CharField(max_length=100, db_index=True)
    display_name = models.CharField(max_length=100)
    category = models.CharField(max_length=100, blank=True, null=True)
    sprite_url = models.URLField(max_length=500)
    primary_type = models.CharField(max_length=30)
    secondary_type = models.CharField(max_length=30, blank=True, null=True)
    height = models.PositiveIntegerField(help_text="Altura en decímetros", null=True, blank=True)
    weight = models.PositiveIntegerField(help_text="Peso en hectogramos", null=True, blank=True)
    species_data = models.JSONField(default=dict, blank=True)
    encounters_data = models.JSONField(default=list, blank=True)
    evolution_chain_data = models.JSONField(default=dict, blank=True)
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

    @property
    def cry_legacy_url(self):
        from django.conf import settings
        existing = _get_existing_cries()
        filename = f"{self.national_number}.ogg"
        if ("legacy", filename) in existing:
            return f"{settings.MEDIA_URL}pokemon/cries/legacy/{filename}"
        if '_raw_data' in self.__dict__ and self.raw_data:
            cries = self.raw_data.get('cries', {})
            url = cries.get('legacy') or cries.get('latest')
            if url:
                return url
        return f"https://raw.githubusercontent.com/PokeAPI/cries/main/cries/pokemon/legacy/{self.national_number}.ogg"

    def get_cry_url(self, kind: str = 'legacy', variation_id: int = None) -> str:
        """
        Retorna la URL local (o fallback oficial) del grito del Pokémon según el estilo
        ('legacy' para retro 8-bits, 'latest' para moderno, o ID de variación específica).
        """
        from django.conf import settings
        existing = _get_existing_cries()
        target_id = variation_id or self.national_number
        target_file = f"{target_id}.ogg"

        folder = 'latest' if kind == 'latest' else 'legacy'
        if (folder, target_file) in existing:
            return f"{settings.MEDIA_URL}pokemon/cries/{folder}/{target_file}"

        return f"https://raw.githubusercontent.com/PokeAPI/cries/main/cries/pokemon/{folder}/{target_id}.ogg"

    def get_pc_icon_url(self, generation: int = 1) -> str:
        """
        Retorna la ruta al icono de PC de la generación indicada.
        Busca localmente en media/pokemon/icons/ con fallback en cascada eficiente en memoria.
        """
        from django.conf import settings
        gen_candidates = [f"gen{generation}"] if generation else []
        gen_candidates += ["gen3", "gen4", "gen5", "gen6", "gen7", "gen8"]

        filename = f"{self.national_number}.png"
        existing = _get_existing_icons()
        for g in gen_candidates:
            if (g, filename) in existing:
                return f"{settings.MEDIA_URL}pokemon/icons/{g}/{filename}"

        # Fallback a la CDN oficial de PokeAPI si no estuviese en disco
        return f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/versions/generation-viii/icons/{self.national_number}.png"

    def get_classic_icon_url(self, generation: int = 1) -> str:
        """
        Retorna la ruta al icono clásico original de Game Boy (Gen 1) o Game Boy Color (Gen 2).
        """
        from django.conf import settings
        from pathlib import Path
        folder = "classic_gen1" if generation == 1 else "classic_gen2"
        target = Path(settings.MEDIA_ROOT) / "pokemon" / "icons" / folder / "by_pokemon" / f"{self.national_number}.png"
        if target.exists():
            return f"{settings.MEDIA_URL}pokemon/icons/{folder}/by_pokemon/{self.national_number}.png"
        return self.get_pc_icon_url(generation=generation)

    @property
    def pc_icon_url(self):
        return self.get_pc_icon_url(generation=1)

    @property
    def sprite_shiny_url(self):
        """Retorna la URL oficial del sprite front-shiny estándar de PokeAPI."""
        if self.national_number == 201:
            return "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/shiny/201-f.png"
        return f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/shiny/{self.national_number}.png"

    @property
    def artwork_shiny_url(self):
        """Retorna la URL oficial del artwork shiny si existe, con fallback a sprite_shiny_url."""
        if self.national_number == 201:
            return "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/shiny/201-f.png"
        return f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/shiny/{self.national_number}.png"


class PokedexEntry(models.Model):
    pokedex = models.ForeignKey(Pokedex, on_delete=models.CASCADE, related_name="entries")
    pokemon = models.ForeignKey(Pokemon, on_delete=models.CASCADE, related_name="pokedex_appearances")
    entry_number = models.PositiveIntegerField()
    game_sprite_url = models.URLField(max_length=500, blank=True, null=True, help_text="Sprite específico de la generación/juego")
    primary_type = models.CharField(max_length=30, blank=True, null=True, help_text="Tipo primario en la generación de este juego")
    secondary_type = models.CharField(max_length=30, blank=True, null=True, help_text="Tipo secundario en la generación de este juego")
    flavor_text = models.TextField(blank=True, help_text="Descripción de la Pokédex específica de este juego")
    obtaining_info = models.JSONField(default=dict, blank=True, help_text="Información detallada de cómo obtenerlo en este juego")
    game_data = models.JSONField(default=dict, blank=True, help_text="Datos completos y enriquecidos de este juego (stats Gen 1, movimientos, ratio de captura, etc.)")
    is_custom_override = models.BooleanField(default=False, help_text="Si está activo, las sincronizaciones automáticas no sobreescribirán esta entrada")

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

    @property
    def primary_type_display(self):
        return self.primary_type or self.pokemon.primary_type

    @property
    def secondary_type_display(self):
        if self.primary_type:
            return self.secondary_type
        return self.pokemon.secondary_type

    @property
    def primary_type_es(self):
        t = self.primary_type_display
        return TYPE_NAMES_ES.get(t.lower(), t.capitalize()) if t else ""

    @property
    def secondary_type_es(self):
        t = self.secondary_type_display
        return TYPE_NAMES_ES.get(t.lower(), t.capitalize()) if t else None

    @property
    def cry_url(self):
        """Retorna el grito del Pokémon. Para juegos retro (Gen <= 5), usa el sonido clásico en 8-bits."""
        from django.conf import settings
        existing = _get_existing_cries()
        game_slug = self.pokedex.game.slug if (self.pokedex and self.pokedex.game) else ""
        num = self.pokemon.national_number

        # Caso especial: Pokémon Amarillo tiene el grito con la voz anime original de Pikachu
        if game_slug == 'yellow' and num == 25:
            if ("yellow", "25.wav") in existing:
                return f"{settings.MEDIA_URL}pokemon/cries/yellow/25.wav"

        is_retro = self.pokedex.game.generation <= 5 if (self.pokedex and self.pokedex.game) else True
        kind = 'legacy' if is_retro else 'latest'
        filename = f"{num}.ogg"

        if (kind, filename) in existing:
            return f"{settings.MEDIA_URL}pokemon/cries/{kind}/{filename}"

        if '_raw_data' in self.pokemon.__dict__ and self.pokemon.raw_data:
            cries = self.pokemon.raw_data.get('cries', {})
            if is_retro:
                return cries.get('legacy') or cries.get('latest') or ""
            return cries.get('latest') or cries.get('legacy') or ""

        return f"https://raw.githubusercontent.com/PokeAPI/cries/main/cries/pokemon/{kind}/{num}.ogg"

    @property
    def pc_icon_url(self):
        return self.pokemon.get_pc_icon_url(generation=self.pokedex.game.generation)

    @property
    def evolution_stone(self):
        """Retorna información de la piedra evolutiva si este Pokémon se obtiene evolucionando con piedra."""
        obt = self.obtaining_info or {}
        evo = obt.get('evolution_info') or {}
        item_slug = evo.get('item_slug')
        text_hint = evo.get('condition') or evo.get('text') or obt.get('summary') or ''
        game_slug = self.pokedex.game.slug if (self.pokedex and self.pokedex.game) else None

        from .utils import resolve_evolution_stone
        return resolve_evolution_stone(item_slug=item_slug, text_hint=text_hint, game_slug=game_slug)

    @property
    def game_sprite_shiny_url(self):
        """
        Retorna el sprite retro shiny específico del juego/generación si aplica (Gen 2-5).
        Para Gen 2 (Oro/Plata/Cristal), busca la variante específica de la edición.
        Para Gen 1 (o fallback), retorna el sprite shiny estándar.
        """
        from django.conf import settings
        from pathlib import Path

        gen = self.pokedex.game.generation if (self.pokedex and self.pokedex.game) else 1
        slug = self.pokedex.game.slug if (self.pokedex and self.pokedex.game) else ""
        num = self.pokemon.national_number

        # 1. Comprobar existencia local en media/pokemon/sprites/{slug}_shiny/{num}.png (100% offline)
        local_rel = f"pokemon/sprites/{slug}_shiny/{num}.png"
        if (Path(settings.MEDIA_ROOT) / local_rel).exists():
            return f"{settings.MEDIA_URL}{local_rel}"

        if gen == 2:
            return f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/versions/generation-ii/gold/shiny/{num}.png"
        elif gen == 3:
            return f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/versions/generation-iii/emerald/shiny/{num}.png"
        elif gen == 4:
            return f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/versions/generation-iv/platinum/shiny/{num}.png"
        elif gen == 5:
            return f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/versions/generation-v/black-white/shiny/{num}.png"
        return self.pokemon.sprite_shiny_url

    @property
    def modern_sprite_shiny_url(self):
        return self.pokemon.artwork_shiny_url

    @property
    def modal_data_json(self):
        """Serializa de forma segura y válida todos los datos del Pokémon para el modal estilo cómic."""
        import json
        return json.dumps({
            "id": self.id,
            "number": f"{self.entry_number:03d}",
            "name": self.pokemon.display_name,
            "category": self.pokemon.category or "Pokémon",
            "primary_type": self.primary_type_display,
            "primary_type_es": self.primary_type_es,
            "secondary_type": self.secondary_type_display or "",
            "secondary_type_es": self.secondary_type_es or "",
            "sprite_retro": self.game_sprite_url or self.pokemon.sprite_url,
            "sprite_modern": self.pokemon.sprite_url,
            "sprite_retro_shiny": self.game_sprite_shiny_url,
            "sprite_modern_shiny": self.modern_sprite_shiny_url,
            "pc_icon_url": self.pc_icon_url,
            "height": self.pokemon.height or 0,
            "weight": self.pokemon.weight or 0,
            "flavor_text": self.flavor_text or "",
            "obtaining": self.obtaining_info or {},
            "evolution_stone": self.evolution_stone,
            "is_caught": getattr(self, "is_caught", False),
            "is_shiny_caught": getattr(self, "is_shiny_caught", False),
            "cry_url": self.cry_url,
        }, ensure_ascii=False)



class UserPokemonCatch(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name="catches")
    session_key = models.CharField(max_length=50, null=True, blank=True, db_index=True)
    pokedex_entry = models.ForeignKey(PokedexEntry, on_delete=models.CASCADE, related_name="user_catches")
    is_caught = models.BooleanField(default=False)
    is_shiny = models.BooleanField(default=False)
    unown_forms_caught = models.JSONField(default=dict, blank=True, help_text="Formas capturadas de Unown: {'normal': [...], 'shiny': [...]}")
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


class Move(models.Model):
    name = models.CharField(max_length=100, unique=True, db_index=True)
    display_name = models.CharField(max_length=100, help_text="Nombre oficial en español")
    generation = models.PositiveSmallIntegerField(default=1)
    type = models.CharField(max_length=30)
    power = models.PositiveIntegerField(null=True, blank=True)
    accuracy = models.PositiveIntegerField(null=True, blank=True)
    pp = models.PositiveIntegerField(null=True, blank=True)
    damage_class = models.CharField(max_length=30, blank=True)
    effect_description = models.TextField(blank=True, help_text="Descripción del efecto en español")
    raw_data = models.JSONField(default=dict, blank=True)

    class Meta:
        verbose_name = "Movimiento"
        verbose_name_plural = "Movimientos"
        ordering = ['id']

    def __str__(self):
        return f"{self.display_name} ({self.type_es})"

    @property
    def type_es(self):
        return TYPE_NAMES_ES.get(self.type.lower(), self.type.capitalize())


from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache


@receiver([post_save, post_delete], sender=PokedexEntry)
def _invalidate_pokedex_entries_cache(sender, instance, **kwargs):
    cache.delete(f"pokedex_entries_base_{instance.pokedex_id}")


@receiver([post_save, post_delete], sender=Game)
def _invalidate_games_cache(sender, **kwargs):
    cache.delete("all_games_catalog")


