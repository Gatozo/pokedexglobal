import shutil
from pathlib import Path
from django.conf import settings
from django.core.management.base import BaseCommand


def _mirror_sprite_tree(src_dir: Path, dest_dir: Path, force: bool = False) -> tuple[int, int]:
    """Copia localmente archivos de sprite de src_dir a dest_dir de forma idempotente."""
    copied = 0
    skipped = 0
    for src_file in src_dir.rglob("*"):
        if not src_file.is_file():
            continue
        rel = src_file.relative_to(src_dir)
        dest_file = dest_dir / rel
        if not force and dest_file.exists() and dest_file.stat().st_size > 0:
            skipped += 1
            continue
        dest_file.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src_file, dest_file)
        copied += 1
    return copied, skipped


class Command(BaseCommand):
    help = "Espeja localmente de forma idempotente los sprites estáticos (.png) de Pokémon Negro a Pokémon Blanco."

    def add_arguments(self, parser):
        parser.add_argument("--force", action="store_true", help="Sobrescribe archivos existentes.")

    def handle(self, *args, **options):
        force = options["force"]
        sprites_root = Path(settings.MEDIA_ROOT) / "pokemon" / "sprites"
        pairs = [
            (sprites_root / "black", sprites_root / "white"),
            (sprites_root / "black_shiny", sprites_root / "white_shiny"),
        ]

        for src_dir, dest_dir in pairs:
            if not src_dir.exists():
                self.stderr.write(self.style.ERROR(f"Directorio origen no encontrado: {src_dir}"))
                return
            copied, skipped = _mirror_sprite_tree(src_dir, dest_dir, force=force)
            self.stdout.write(
                self.style.SUCCESS(f"[OK] {dest_dir.name}: {copied} copiados, {skipped} omitidos (ya existentes).")
            )
