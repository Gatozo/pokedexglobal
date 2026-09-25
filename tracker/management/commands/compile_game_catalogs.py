import json
import os
from pathlib import Path
from django.conf import settings
from django.core.management.base import BaseCommand
from django.core.cache import cache
from tracker.models import Game, Pokedex, PokedexEntry
from tracker.catalog_service import clear_catalog_memory_cache

CATALOGS_DIR = Path(settings.BASE_DIR) / "tracker" / "data" / "catalogs"


class Command(BaseCommand):
    help = "Compila las entradas de Pokédex de cada juego en archivos JSON estáticos inmutables (Plan B)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--game",
            type=str,
            help="Slug del juego específico a compilar (ej: crystal, gold, red). Si se omite, compila todos.",
        )

    def handle(self, *args, **options):
        CATALOGS_DIR.mkdir(parents=True, exist_ok=True)
        game_slug = options.get("game")

        if game_slug:
            games = Game.objects.filter(slug=game_slug)
            if not games.exists():
                self.stdout.write(self.style.ERROR(f"No se encontró el juego con slug '{game_slug}'."))
                return
        else:
            games = Game.objects.all().order_by("generation", "id")

        self.stdout.write(self.style.NOTICE(f"Iniciando compilación de catálogos JSON estáticos para {games.count()} juego(s)..."))

        total_compiled = 0

        for game in games:
            # Seleccionar Pokédex principal (regional / no nacional si existe, o primera)
            pokedex = game.pokedexes.filter(is_national=False).first() or game.pokedexes.first()
            if not pokedex:
                self.stdout.write(self.style.WARNING(f"Juego '{game.slug}' no tiene Pokédex asociada. Omitiendo."))
                continue

            entries = (
                PokedexEntry.objects.filter(pokedex=pokedex)
                .select_related("pokemon", "pokedex__game")
                .order_by("entry_number")
            )

            compiled_entries = []
            for entry in entries:
                poke = entry.pokemon
                compiled_data = {
                    "id": entry.id,
                    "entry_number": entry.entry_number,
                    "game_slug": game.slug,
                    "pokemon": {
                        "national_number": poke.national_number,
                        "name": poke.name,
                        "display_name": poke.display_name,
                        "category": poke.category or "Pokémon",
                        "height": poke.height or 0,
                        "weight": poke.weight or 0,
                        "sprite_url": poke.sprite_url,
                        "sprite_shiny_url": poke.sprite_shiny_url,
                        "artwork_shiny_url": poke.artwork_shiny_url,
                        "primary_type": poke.primary_type,
                        "secondary_type": poke.secondary_type,
                    },
                    "primary_type": entry.primary_type,
                    "primary_type_display": entry.primary_type_display,
                    "primary_type_es": entry.primary_type_es,
                    "secondary_type": entry.secondary_type,
                    "secondary_type_display": entry.secondary_type_display,
                    "secondary_type_es": entry.secondary_type_es,
                    "game_sprite_url": entry.game_sprite_url,
                    "game_sprite_shiny_url": entry.game_sprite_shiny_url,
                    "modern_sprite_shiny_url": entry.modern_sprite_shiny_url,
                    "modal_retro_sprite_url": entry.modal_retro_sprite_url,
                    "modal_retro_sprite_shiny_url": entry.modal_retro_sprite_shiny_url,
                    "pc_icon_url": entry.pc_icon_url,
                    "cry_url": entry.cry_url,
                    "flavor_text": entry.flavor_text or "",
                    "obtaining_info": entry.obtaining_info or {},
                    "evolution_stone": entry.evolution_stone,
                    "game_data": entry.game_data or {},
                }
                compiled_entries.append(compiled_data)

            output_file = CATALOGS_DIR / f"{game.slug}.json"
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(compiled_entries, f, ensure_ascii=False, indent=2)

            file_size_kb = output_file.stat().st_size / 1024
            total_compiled += len(compiled_entries)
            self.stdout.write(
                self.style.SUCCESS(
                    f"[OK] Catálogo compilado para '{game.display_name}' ({game.slug}): "
                    f"{len(compiled_entries)} entradas -> {output_file.name} ({file_size_kb:.1f} KB)"
                )
            )

        clear_catalog_memory_cache()
        cache.clear()
        self.stdout.write(self.style.SUCCESS(f"¡Compilación finalizada con éxito! Total entradas compiladas: {total_compiled}"))
