from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from django.conf import settings
from django.core.management.base import BaseCommand
from tracker.management.commands.sync_white_sprites import _mirror_sprite_tree
from tracker.management.commands.sync_black2_sprites import (
    B2W2_NEW_FORMS,
    POKEAPI_GEN5_BASE,
    _download_file,
)


class Command(BaseCommand):
    help = (
        "Espeja localmente de forma idempotente los sprites animados (.gif) de Pokémon Negro a Pokémon Negro 2 "
        "y descarga únicamente los 24 archivos nuevos de las 6 formas introducidas en B2W2."
    )

    def add_arguments(self, parser):
        parser.add_argument("--force", action="store_true", help="Sobrescribe archivos existentes.")
        parser.add_argument("--workers", type=int, default=8, help="Número de hilos para descargas HTTP.")

    def handle(self, *args, **options):
        force = options["force"]
        workers = max(1, int(options["workers"]))
        sprites_root = Path(settings.MEDIA_ROOT) / "pokemon" / "sprites"

        # Paso 1: Espejado local idempotente desde black_animated y black_animated_shiny
        pairs = [
            (sprites_root / "black_animated", sprites_root / "black-2_animated"),
            (sprites_root / "black_animated_shiny", sprites_root / "black-2_animated_shiny"),
        ]
        for src_dir, dest_dir in pairs:
            if not src_dir.exists():
                self.stderr.write(self.style.ERROR(f"Directorio origen no encontrado: {src_dir}"))
                return
            copied, skipped = _mirror_sprite_tree(src_dir, dest_dir, force=force)
            self.stdout.write(
                self.style.SUCCESS(f"[OK] {dest_dir.name} (espejo): {copied} copiados, {skipped} omitidos.")
            )

        # Paso 2: Descarga selectiva de los 24 GIFs nuevos de las 6 formas de B2W2
        tasks = []
        for form_id, rel_stem in B2W2_NEW_FORMS:
            tasks.append((
                f"{POKEAPI_GEN5_BASE}/animated/{form_id}.gif",
                sprites_root / "black-2_animated" / f"{rel_stem}.gif",
            ))
            tasks.append((
                f"{POKEAPI_GEN5_BASE}/animated/back/{form_id}.gif",
                sprites_root / "black-2_animated" / "back" / f"{rel_stem}.gif",
            ))
            tasks.append((
                f"{POKEAPI_GEN5_BASE}/animated/shiny/{form_id}.gif",
                sprites_root / "black-2_animated_shiny" / f"{rel_stem}.gif",
            ))
            tasks.append((
                f"{POKEAPI_GEN5_BASE}/animated/back/shiny/{form_id}.gif",
                sprites_root / "black-2_animated_shiny" / "back" / f"{rel_stem}.gif",
            ))

        stats = {"downloaded": 0, "skipped": 0, "failed": 0}
        with ThreadPoolExecutor(max_workers=workers) as ex:
            futs = {ex.submit(_download_file, url, dest, force): (url, dest) for url, dest in tasks}
            for fut in as_completed(futs):
                res = fut.result()
                stats[res] += 1
                if res == "failed":
                    url, dest = futs[fut]
                    self.stderr.write(self.style.ERROR(f"[FAIL] {url} -> {dest}"))

        self.stdout.write(
            self.style.SUCCESS(
                f"[OK] Formas nuevas B2W2 (.gif): {stats['downloaded']} descargados, "
                f"{stats['skipped']} omitidos, {stats['failed']} fallidos."
            )
        )
