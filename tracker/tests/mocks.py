# tracker/tests/mocks.py
# Clases shim y mocks en memoria para compatibilidad de pruebas pre-catálogo Plan C.

class MockQuerySet(list):
    def select_related(self, *args, **kwargs):
        return self

    def defer(self, *args, **kwargs):
        return self

    def order_by(self, *args, **kwargs):
        return self

    def filter(self, **kwargs):
        res = [item for item in self if all(getattr(item, k, None) == v for k, v in kwargs.items())]
        return MockQuerySet(res)

    def first(self):
        return self[0] if len(self) > 0 else None

    def exists(self):
        return len(self) > 0


class MockObjects:
    def __init__(self, factory):
        self.factory = factory
        self._items = []

    def create(self, **kwargs):
        obj = self.factory(kwargs)
        for k, v in kwargs.items():
            setattr(obj, k, v)
        if not hasattr(obj, "id") or obj.id is None:
            obj.id = len(self._items) + 1
        self._items.append(obj)
        return obj

    def get_or_create(self, **kwargs):
        defaults = kwargs.pop("defaults", {})
        for item in self._items:
            match = True
            for k, v in kwargs.items():
                if getattr(item, k, None) != v:
                    match = False
                    break
            if match:
                return item, False
        all_kwargs = {**kwargs, **defaults}
        return self.create(**all_kwargs), True

    def filter(self, **kwargs):
        res = []
        for item in self._items:
            match = True
            for k, v in kwargs.items():
                if getattr(item, k, None) != v:
                    match = False
                    break
            if match:
                res.append(item)
        return MockQuerySet(res)

    def count(self):
        return len(self._items)

    def all(self):
        return MockQuerySet(list(self._items))

    def first(self):
        return self._items[0] if self._items else None


class Pokemon:
    objects = MockObjects(lambda kw: Pokemon(**kw))

    def __init__(self, *args, **kwargs):
        data = args[0] if args and isinstance(args[0], dict) else {}
        combined = {**data, **kwargs}
        self.id = combined.get("id")
        self.national_number = combined.get("national_number", 0)
        self.name = combined.get("name", "")
        self.display_name = combined.get("display_name", "")
        self.category = combined.get("category", "Pokémon")
        self.height = combined.get("height", 0)
        self.weight = combined.get("weight", 0)
        self.sprite_url = combined.get("sprite_url", "")
        self._sprite_shiny_url = combined.get("sprite_shiny_url", "")
        self._artwork_shiny_url = combined.get("artwork_shiny_url", "")
        self.primary_type = combined.get("primary_type", "")
        self.secondary_type = combined.get("secondary_type")
        self.raw_data = combined.get("raw_data", {})
        self.species_data = combined.get("species_data", {})
        self.encounters_data = combined.get("encounters_data", [])
        self.evolution_chain_data = combined.get("evolution_chain_data", {})
        for k, v in combined.items():
            setattr(self, k, v)

    def save(self, *args, **kwargs):
        pass

    @property
    def sprite_shiny_url(self):
        if self._sprite_shiny_url:
            return self._sprite_shiny_url
        if self.national_number == 201:
            return "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/shiny/201-f.png"
        return f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/shiny/{self.national_number}.png"

    @property
    def artwork_shiny_url(self):
        if self._artwork_shiny_url:
            return self._artwork_shiny_url
        if self.national_number == 201:
            return "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/shiny/201-f.png"
        return f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/shiny/{self.national_number}.png"

    @property
    def cry_legacy_url(self):
        from tracker.catalog_service import get_existing_cries
        existing = get_existing_cries()
        filename = f"{self.national_number}.ogg"
        if ("legacy", filename) in existing:
            return f"/media/pokemon/cries/legacy/{filename}"
        return f"https://raw.githubusercontent.com/PokeAPI/cries/main/cries/pokemon/legacy/{self.national_number}.ogg"

    def get_cry_url(self, kind="legacy", variation_id=None):
        from tracker.catalog_service import get_existing_cries
        existing = get_existing_cries()
        target_id = variation_id or self.national_number
        filename = f"{target_id}.ogg"
        folder = "latest" if kind == "latest" else "legacy"
        if (folder, filename) in existing:
            return f"/media/pokemon/cries/{folder}/{filename}"
        return f"https://raw.githubusercontent.com/PokeAPI/cries/main/cries/pokemon/{folder}/{target_id}.ogg"

    @property
    def primary_type_es(self):
        from tracker.models import TYPE_NAMES_ES
        return TYPE_NAMES_ES.get(self.primary_type.lower(), self.primary_type.capitalize()) if self.primary_type else ""

    @property
    def secondary_type_es(self):
        if self.secondary_type:
            from tracker.models import TYPE_NAMES_ES
            return TYPE_NAMES_ES.get(self.secondary_type.lower(), self.secondary_type.capitalize())
        return None

    def get_pc_icon_url(self, generation=1):
        return f"/media/pokemon/icons/gen{generation}/{self.national_number}.png"

    def get_classic_icon_url(self, generation=1):
        return self.get_pc_icon_url(generation=generation)


class PokedexEntry:
    objects = MockObjects(lambda kw: PokedexEntry(**kw))

    def __init__(self, *args, **kwargs):
        data = args[0] if args and isinstance(args[0], dict) else {}
        combined = {**data, **kwargs}
        self.id = combined.get("id")
        self.pokedex = combined.get("pokedex")
        self.entry_number = combined.get("entry_number", 0)
        poke = combined.get("pokemon")
        if isinstance(poke, dict):
            self.pokemon = Pokemon(poke)
        elif poke:
            self.pokemon = poke
        else:
            self.pokemon = Pokemon()

        self.primary_type = combined.get("primary_type")
        self.primary_type_display = combined.get("primary_type_display") or self.primary_type or self.pokemon.primary_type
        from tracker.models import TYPE_NAMES_ES
        self.primary_type_es = combined.get("primary_type_es") or (TYPE_NAMES_ES.get(self.primary_type_display.lower(), self.primary_type_display.capitalize()) if self.primary_type_display else "")
        self.secondary_type = combined.get("secondary_type")
        self.secondary_type_display = combined.get("secondary_type_display") or (self.secondary_type if self.primary_type else self.pokemon.secondary_type)
        self.secondary_type_es = combined.get("secondary_type_es") or (TYPE_NAMES_ES.get(self.secondary_type_display.lower(), self.secondary_type_display.capitalize()) if self.secondary_type_display else None)

        self.game_sprite_url = combined.get("game_sprite_url") or self.pokemon.sprite_url
        self._game_sprite_shiny_url = combined.get("game_sprite_shiny_url")
        self.modern_sprite_shiny_url = combined.get("modern_sprite_shiny_url") or self.pokemon.artwork_shiny_url
        self._modal_retro_sprite_url = combined.get("modal_retro_sprite_url")
        self._modal_retro_sprite_shiny_url = combined.get("modal_retro_sprite_shiny_url")
        self._pc_icon_url = combined.get("pc_icon_url")
        self._cry_url = combined.get("cry_url", "")
        self.flavor_text = combined.get("flavor_text", "")
        self.obtaining_info = combined.get("obtaining_info") or {}
        self._evolution_stone = combined.get("evolution_stone")
        self.game_data = combined.get("game_data") or {}
        self.is_custom_override = combined.get("is_custom_override", False)
        self.is_caught = False
        self.is_shiny_caught = False

        for k, v in combined.items():
            setattr(self, k, v)

    def save(self, *args, **kwargs):
        pass

    @property
    def cry_url(self):
        if self._cry_url:
            return self._cry_url
        if self.pokemon:
            return getattr(self.pokemon, "cry_legacy_url", "")
        return ""

    @property
    def game_sprite_shiny_url(self):
        if self._game_sprite_shiny_url:
            return self._game_sprite_shiny_url
        slug = self.pokedex.game.slug if (self.pokedex and hasattr(self.pokedex, "game") and self.pokedex.game) else ""
        num = self.pokemon.national_number
        if slug in ["gold", "silver", "crystal"]:
            from django.conf import settings
            from pathlib import Path
            local_rel = f"pokemon/sprites/{slug}_shiny/{num}.png"
            if (Path(settings.MEDIA_ROOT) / local_rel).exists() or True:
                return f"{settings.MEDIA_URL}{local_rel}"
        return self.pokemon.sprite_shiny_url

    @property
    def modal_retro_sprite_url(self):
        slug = self.pokedex.game.slug if (self.pokedex and hasattr(self.pokedex, "game") and self.pokedex.game) else ""
        num = self.pokemon.national_number
        if slug == "crystal":
            from pathlib import Path
            from django.conf import settings
            anim_rel = f"pokemon/sprites/crystal_animated/{num}.gif"
            if (Path(settings.MEDIA_ROOT) / anim_rel).exists():
                return f"{settings.MEDIA_URL}{anim_rel}"
        return self._modal_retro_sprite_url or self.game_sprite_url or self.pokemon.sprite_url

    @property
    def modal_retro_sprite_shiny_url(self):
        slug = self.pokedex.game.slug if (self.pokedex and hasattr(self.pokedex, "game") and self.pokedex.game) else ""
        num = self.pokemon.national_number
        if slug == "crystal":
            from pathlib import Path
            from django.conf import settings
            anim_rel = f"pokemon/sprites/crystal_animated_shiny/{num}.gif"
            if (Path(settings.MEDIA_ROOT) / anim_rel).exists():
                return f"{settings.MEDIA_URL}{anim_rel}"
        return self._modal_retro_sprite_shiny_url or self.game_sprite_shiny_url

    @property
    def pc_icon_url(self):
        if self._pc_icon_url:
            return self._pc_icon_url
        gen = self.pokedex.game.generation if (self.pokedex and hasattr(self.pokedex, "game") and self.pokedex.game) else 1
        return self.pokemon.get_pc_icon_url(generation=gen)

    @property
    def evolution_stone(self):
        if self._evolution_stone is not None:
            return self._evolution_stone
        obt = self.obtaining_info or {}
        evo = obt.get("evolution_info") or {}
        item_slug = evo.get("item_slug")
        text_hint = evo.get("condition") or evo.get("text") or obt.get("summary") or ""
        game_slug = self.pokedex.game.slug if (self.pokedex and hasattr(self.pokedex, "game") and self.pokedex.game) else None
        from tracker.utils import resolve_evolution_stone
        return resolve_evolution_stone(item_slug=item_slug, text_hint=text_hint, game_slug=game_slug)

    @property
    def modal_data_json(self):
        import json
        return json.dumps({
            "id": self.id,
            "number": f"{self.entry_number:03d}",
            "name": self.pokemon.display_name,
            "category": self.pokemon.category,
            "primary_type": self.primary_type_display,
            "primary_type_es": self.primary_type_es,
            "secondary_type": self.secondary_type_display or "",
            "secondary_type_es": self.secondary_type_es or "",
            "sprite_retro": self.modal_retro_sprite_url,
            "sprite_modern": self.pokemon.sprite_url,
            "sprite_retro_shiny": self.modal_retro_sprite_shiny_url,
            "sprite_modern_shiny": self.modern_sprite_shiny_url,
            "pc_icon_url": self.pc_icon_url,
            "height": self.pokemon.height,
            "weight": self.pokemon.weight,
            "flavor_text": self.flavor_text,
            "obtaining": self.obtaining_info,
            "evolution_stone": self.evolution_stone,
            "is_caught": self.is_caught,
            "is_shiny_caught": self.is_shiny_caught,
            "cry_url": self.cry_url,
            "forms": getattr(self, "forms", []),
        }, ensure_ascii=False)


class Move:
    objects = MockObjects(lambda kw: Move(**kw))

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

    def save(self, *args, **kwargs):
        pass


