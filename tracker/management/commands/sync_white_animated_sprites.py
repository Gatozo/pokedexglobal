import shutil
from pathlib import Path
from django.conf import settings
from django.core.management.base import BaseCommand
from tracker.management.commands.sync_white_sprites import _mirror_sprite_tree


class Command(BaseCommand):
    help = "Espeja localmente de forma idempotente los sprites animados (.gif) de Pokémon Negro a Pokémon Blanco."

    def add_arguments(self, parser):
        parser.add_argument("--force", action="store_true", help="Sobrescribe archivos existentes.")

    def handle(self, *args, **options):
        force = options["force"]
        sprites_root = Path(settings.MEDIA_ROOT) / "pokemon" / "sprites"
        pairs = [
            (sprites_root / "black_animated", sprites_root / "white_animated"),
            (sprites_root / "black_animated_shiny", sprites_root / "white_animated_shiny"),
        ]

        for src_dir, dest_dir in pairs:
            if not src_dir.exists():
                self.stderr.write(self.style.ERROR(f"Directorio origen no encontrado: {src_dir}"))
                return
            copied, skipped = _mirror_sprite_tree(src_dir, dest_dir, force=force)
            self.stdout.write(
                self.style.SUCCESS(f"[OK] {dest_dir.name}: {copied} copiados, {skipped} omitidos (ya existentes).")
            )
