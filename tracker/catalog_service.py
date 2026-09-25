"""
Servicio centralizado de catálogos compilados inmutables (Plan B).
Permite servir las entradas de la Pokédex desde archivos JSON compilados en memoria
en 0 ms de consultas SQL, manteniendo la interfaz compatible con PokedexEntry.
"""
import copy
import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Any
from django.conf import settings

CATALOGS_DIR = Path(__file__).resolve().parent / "data" / "catalogs"

_CATALOG_CACHE: Dict[str, List["CatalogEntry"]] = {}
_ENTRY_BY_ID_CACHE: Dict[int, "CatalogEntry"] = {}
_POKEMON_BY_NATIONAL_CACHE: Dict[int, "CatalogPokemon"] = {}
_EXISTING_ICONS_SET = None
_EXISTING_CRIES_SET = None

# Familias evolutivas completas de iniciales (Gen 1 a Gen 9)
STARTER_NATIONAL_NUMBERS = {
    # Gen 1: Bulbasaur, Charmander, Squirtle, Pikachu (Yellow)
    1, 2, 3, 4, 5, 6, 7, 8, 9, 25, 26,
    # Gen 2: Chikorita, Cyndaquil, Totodile
    152, 153, 154, 155, 156, 157, 158, 159, 160,
    # Gen 3: Treecko, Torchic, Mudkip
    252, 253, 254, 255, 256, 257, 258, 259, 260,
    # Gen 4: Turtwig, Chimchar, Piplup
    387, 388, 389, 390, 391, 392, 393, 394, 395,
    # Gen 5: Snivy, Tepig, Oshawott
    495, 496, 497, 498, 499, 500, 501, 502, 503,
    # Gen 6: Chespin, Fennekin, Froakie
    650, 651, 652, 653, 654, 655, 656, 657, 658,
    # Gen 7: Rowlet, Litten, Popplio
    722, 723, 724, 725, 726, 727, 728, 729, 730,
    # Gen 8: Grookey, Scorbunny, Sobble
    810, 811, 812, 813, 814, 815, 816, 817, 818,
    # Gen 9: Sprigatito, Fuecoco, Quaxly
    906, 907, 908, 909, 910, 911, 912, 913, 914
}



def get_existing_icons():
    global _EXISTING_ICONS_SET
    if _EXISTING_ICONS_SET is None:
        icons_dir = Path(settings.MEDIA_ROOT) / "pokemon" / "icons"
        _EXISTING_ICONS_SET = set()
        if icons_dir.exists():
            for p in icons_dir.glob("*/*.png"):
                _EXISTING_ICONS_SET.add((p.parent.name, p.name))
    return _EXISTING_ICONS_SET


def get_existing_cries():
    global _EXISTING_CRIES_SET
    if _EXISTING_CRIES_SET is None:
        cries_dir = Path(settings.MEDIA_ROOT) / "pokemon" / "cries"
        _EXISTING_CRIES_SET = set()
        if cries_dir.exists():
            for p in cries_dir.glob("*/*.*"):
                _EXISTING_CRIES_SET.add((p.parent.name, p.name))
    return _EXISTING_CRIES_SET


class CatalogPokemon:
    """Representación ligera de un Pokémon para una entrada de catálogo."""

    def __init__(self, data: Dict[str, Any]):
        self.national_number = data.get("national_number", 0)
        self.name = data.get("name", "")
        self.display_name = data.get("display_name", "")
        self.category = data.get("category", "Pokémon")
        self.height = data.get("height", 0)
        self.weight = data.get("weight", 0)
        self.sprite_url = data.get("sprite_url", "")
        self._sprite_shiny_url = data.get("sprite_shiny_url", "")
        self._artwork_shiny_url = data.get("artwork_shiny_url", "")
        self.primary_type = data.get("primary_type", "")
        self.secondary_type = data.get("secondary_type")

    @property
    def sprite_shiny_url(self) -> str:
        if self._sprite_shiny_url:
            return self._sprite_shiny_url
        if self.national_number == 201:
            return "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/shiny/201-f.png"
        return f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/shiny/{self.national_number}.png"

    @property
    def artwork_shiny_url(self) -> str:
        if self._artwork_shiny_url:
            return self._artwork_shiny_url
        if self.national_number == 201:
            return "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/shiny/201-f.png"
        return f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/shiny/{self.national_number}.png"

    @property
    def cry_legacy_url(self) -> str:
        return f"/media/pokemon/cries/legacy/{self.national_number}.ogg"

    def get_cry_url(self, kind: str = "legacy", variation_id: int = None) -> str:
        target_id = variation_id or self.national_number
        folder = "latest" if kind == "latest" else "legacy"
        return f"/media/pokemon/cries/{folder}/{target_id}.ogg"

    @property
    def primary_type_es(self) -> str:
        from tracker.models import TYPE_NAMES_ES
        return TYPE_NAMES_ES.get(self.primary_type.lower(), self.primary_type.capitalize()) if self.primary_type else ""

    @property
    def secondary_type_es(self) -> Optional[str]:
        if self.secondary_type:
            from tracker.models import TYPE_NAMES_ES
            return TYPE_NAMES_ES.get(self.secondary_type.lower(), self.secondary_type.capitalize())
        return None

    def get_pc_icon_url(self, generation: int = 1) -> str:
        gen_candidates = [f"gen{generation}"] if generation else []
        gen_candidates += ["gen3", "gen4", "gen5", "gen6", "gen7", "gen8"]

        filename = f"{self.national_number}.png"
        existing = get_existing_icons()
        for g in gen_candidates:
            if (g, filename) in existing:
                return f"{settings.MEDIA_URL}pokemon/icons/{g}/{filename}"

        return f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/versions/generation-viii/icons/{self.national_number}.png"

    def get_classic_icon_url(self, generation: int = 1) -> str:
        folder = "classic_gen1" if generation == 1 else "classic_gen2"
        target = Path(settings.MEDIA_ROOT) / "pokemon" / "icons" / folder / "by_pokemon" / f"{self.national_number}.png"
        if target.exists():
            return f"{settings.MEDIA_URL}pokemon/icons/{folder}/by_pokemon/{self.national_number}.png"
        return self.get_pc_icon_url(generation=generation)

    @property
    def pc_icon_url(self):
        return self.get_pc_icon_url(generation=1)

    def __str__(self):
        return self.display_name


class CatalogEntry:
    """
    Adaptador inmutable de entrada de Pokédex.
    Expone la misma interfaz que el modelo PokedexEntry para plantillas y vistas.
    """

    def __init__(self, data: Dict[str, Any], game_slug: str = ""):
        self.id = data.get("id")
        self.entry_number = data.get("entry_number", 0)
        self.game_slug = game_slug or data.get("game_slug", "")
        self.pokemon = CatalogPokemon(data.get("pokemon", {}))

        self.primary_type = data.get("primary_type")
        self.primary_type_display = data.get("primary_type_display") or self.pokemon.primary_type
        self.primary_type_es = data.get("primary_type_es", "")

        self.secondary_type = data.get("secondary_type")
        self.secondary_type_display = data.get("secondary_type_display")
        self.secondary_type_es = data.get("secondary_type_es")

        self.game_sprite_url = data.get("game_sprite_url") or self.pokemon.sprite_url
        self.game_sprite_shiny_url = data.get("game_sprite_shiny_url") or self.pokemon.sprite_shiny_url
        self.modern_sprite_shiny_url = data.get("modern_sprite_shiny_url") or self.pokemon.artwork_shiny_url

        self.modal_retro_sprite_url = data.get("modal_retro_sprite_url") or self.game_sprite_url
        self.modal_retro_sprite_shiny_url = data.get("modal_retro_sprite_shiny_url") or self.game_sprite_shiny_url

        self._pc_icon_url = data.get("pc_icon_url", "")
        self._cry_url = data.get("cry_url", "")
        self.flavor_text = data.get("flavor_text", "")
        self.obtaining_info = data.get("obtaining_info") or {}
        self._evolution_stone = data.get("evolution_stone")
        self.game_data = data.get("game_data") or {}

        # Estado mutable específico del usuario anotado en memoria en tiempo de petición
        self.is_caught = False
        self.is_shiny_caught = False

        self._cached_modal_json = data.get("modal_data_json")

    @property
    def cry_url(self) -> str:
        if self._cry_url:
            return self._cry_url
        if self.pokemon:
            return getattr(self.pokemon, "cry_legacy_url", "")
        return ""

    @property
    def pc_icon_url(self) -> str:
        if self._pc_icon_url:
            return self._pc_icon_url
        gen = 2 if self.game_slug in ["gold", "silver", "crystal"] else 1
        return self.pokemon.get_pc_icon_url(generation=gen)

    @property
    def evolution_stone(self):
        if self._evolution_stone is not None:
            return self._evolution_stone
        obt = self.obtaining_info or {}
        evo = obt.get("evolution_info") or {}
        item_slug = evo.get("item_slug")
        text_hint = evo.get("condition") or evo.get("text") or obt.get("summary") or ""
        from .utils import resolve_evolution_stone
        return resolve_evolution_stone(item_slug=item_slug, text_hint=text_hint, game_slug=self.game_slug)

    @property
    def filter_locations(self) -> str:
        """Cadena concatenada de todas las áreas y descripciones para búsqueda de texto libre."""
        obt = self.obtaining_info or {}
        areas = [loc.get("area", "") for loc in obt.get("locations", []) if loc.get("area")]
        summary = obt.get("summary") or ""
        all_text = " | ".join(areas + ([summary] if summary else []))
        return all_text

    @property
    def filter_tags(self) -> str:
        """Conjunto de etiquetas para filtros avanzados (cañas, surf, golpe cabeza, inicial, legendario, regalo)."""
        tags = set()
        obt = self.obtaining_info or {}
        nat_num = getattr(self.pokemon, "national_number", 0)

        # Iniciales y evoluciones
        if obt.get("type") == "starter" or nat_num in STARTER_NATIONAL_NUMBERS:
            tags.add("starter")

        # Legendarios y míticos
        if obt.get("type") in ["legendary", "mythical"]:
            tags.add("legendary")

        # Métodos de obtención en texto
        methods_lower = " ".join([loc.get("method", "").lower() for loc in obt.get("locations", [])])
        summary_lower = (obt.get("summary") or "").lower()
        full_obt_text = f"{methods_lower} {summary_lower}"

        # Regalos
        if obt.get("type") == "gift" or "regalo" in full_obt_text:
            tags.add("gift")

        # Surf
        if "surf" in full_obt_text:
            tags.add("surf")

        # Golpe Cabeza
        if "golpe cabeza" in full_obt_text:
            tags.add("headbutt")

        # Cañas de pescar
        has_old = "vieja" in full_obt_text
        has_good = "buena" in full_obt_text
        has_super = "super" in full_obt_text or "súper" in full_obt_text

        if has_old:
            tags.add("rod_old")
        if has_good:
            tags.add("rod_good")
        if has_super:
            tags.add("rod_super")
        if has_old or has_good or has_super:
            tags.add("rod_any")

        return " ".join(sorted(tags))

    def __copy__(self):
        new_copy = CatalogEntry.__new__(CatalogEntry)
        new_copy.__dict__.update(self.__dict__)
        return new_copy


    @property
    def modal_data_json(self) -> str:
        """Retorna el JSON serializado para el modal estilo cómic con el estado de captura actual."""
        return json.dumps({
            "id": self.id,
            "number": f"{self.entry_number:03d}",
            "name": self.pokemon.display_name,
            "category": self.pokemon.category or "Pokémon",
            "primary_type": self.primary_type_display,
            "primary_type_es": self.primary_type_es,
            "secondary_type": self.secondary_type_display or "",
            "secondary_type_es": self.secondary_type_es or "",
            "sprite_retro": self.modal_retro_sprite_url,
            "sprite_modern": self.pokemon.sprite_url,
            "sprite_retro_shiny": self.modal_retro_sprite_shiny_url,
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

    def __str__(self):
        return f"#{self.entry_number:03d}: {self.pokemon.display_name} ({self.game_slug})"


def clear_catalog_memory_cache():
    """Limpia la caché en memoria de los catálogos compilados."""
    global _CATALOG_CACHE, _ENTRY_BY_ID_CACHE, _POKEMON_BY_NATIONAL_CACHE
    _CATALOG_CACHE.clear()
    _ENTRY_BY_ID_CACHE.clear()
    _POKEMON_BY_NATIONAL_CACHE.clear()


def get_compiled_catalog(game_slug: str, force_reload: bool = False) -> Optional[List[CatalogEntry]]:
    """
    Retorna la lista de CatalogEntry compiladas desde el archivo JSON local.
    Carga en memoria una sola vez por proceso servidor (~150 KB de RAM).
    """
    global _CATALOG_CACHE, _ENTRY_BY_ID_CACHE, _POKEMON_BY_NATIONAL_CACHE

    if not force_reload and game_slug in _CATALOG_CACHE:
        return _CATALOG_CACHE[game_slug]

    catalog_file = CATALOGS_DIR / f"{game_slug}.json"
    if not catalog_file.exists():
        return None

    try:
        with open(catalog_file, "r", encoding="utf-8") as f:
            raw_entries = json.load(f)

        entries = [CatalogEntry(d, game_slug=game_slug) for d in raw_entries]
        _CATALOG_CACHE[game_slug] = entries
        for entry in entries:
            if entry.id is not None:
                _ENTRY_BY_ID_CACHE[entry.id] = entry
            if entry.pokemon and entry.pokemon.national_number:
                _POKEMON_BY_NATIONAL_CACHE[entry.pokemon.national_number] = entry.pokemon
        return entries
    except Exception as e:
        print(f"Error cargando catálogo compilado para {game_slug}: {e}")
        return None


def ensure_all_catalogs_loaded():
    """Precarga todos los catálogos disponibles para indexación O(1)."""
    global _CATALOG_CACHE
    all_slugs = ["red", "blue", "yellow", "gold", "silver", "crystal"]
    for slug in all_slugs:
        if slug not in _CATALOG_CACHE:
            get_compiled_catalog(slug)


def get_catalog_entry_by_id(entry_id: int) -> Optional[CatalogEntry]:
    """Retorna una CatalogEntry por su ID único en O(1) desde memoria."""
    global _ENTRY_BY_ID_CACHE
    if entry_id in _ENTRY_BY_ID_CACHE:
        return _ENTRY_BY_ID_CACHE[entry_id]

    ensure_all_catalogs_loaded()
    return _ENTRY_BY_ID_CACHE.get(entry_id)


def get_pokemon_by_national_number(national_num: int) -> Optional[CatalogPokemon]:
    """Retorna un CatalogPokemon por su número nacional (1..251) en O(1) desde memoria."""
    global _POKEMON_BY_NATIONAL_CACHE
    if national_num in _POKEMON_BY_NATIONAL_CACHE:
        return _POKEMON_BY_NATIONAL_CACHE[national_num]

    ensure_all_catalogs_loaded()
    return _POKEMON_BY_NATIONAL_CACHE.get(national_num)
