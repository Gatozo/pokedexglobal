import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from django.conf import settings
from django.core.management.base import BaseCommand
from tracker.management.commands.sync_white_sprites import _mirror_sprite_tree

POKEAPI_GEN5_BASE = (
    "https://raw.githubusercontent.com/PokeAPI/sprites/master/"
    "sprites/pokemon/versions/generation-v/black-white"
)

B2W2_NEW_FORMS = [
    (10019, "tornadus/therian"),
    (10020, "thundurus/therian"),
    (10021, "landorus/therian"),
    (10022, "kyurem/black"),
    (10023, "kyurem/white"),
    (10024, "keldeo/resolute"),
]

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) PokedexGlobal/1.0"


def _download_file(url: str, dest: Path, force: bool = False) -> str:
    if not force and dest.exists() and dest.stat().st_size > 0:
        return "skipped"
    dest.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                data = resp.read()
            if data:
                dest.write_bytes(data)
                return "downloaded"
        except Exception:
            if attempt < 2:
                time.sleep(1)
    return "failed"


class Command(BaseCommand):
    help = (
        "Espeja localmente de forma idempotente los sprites estáticos (.png) de Pokémon Negro a Pokémon Negro 2 "
        "y descarga únicamente los 24 archivos nuevos de las 6 formas introducidas en B2W2."
    )

    def add_arguments(self, parser):
        parser.add_argument("--force", action="store_true", help="Sobrescribe archivos existentes.")
        parser.add_argument("--workers", type=int, default=8, help="Número de hilos para descargas HTTP.")

    def handle(self, *args, **options):
        force = options["force"]
        workers = max(1, int(options["workers"]))
        sprites_root = Path(settings.MEDIA_ROOT) / "pokemon" / "sprites"

        # Paso 1: Espejado local idempotente desde black y black_shiny (0 peticiones HTTP)
        pairs = [
            (sprites_root / "black", sprites_root / "black-2"),
            (sprites_root / "black_shiny", sprites_root / "black-2_shiny"),
        ]
        for src_dir, dest_dir in pairs:
            if not src_dir.exists():
                self.stderr.write(self.style.ERROR(f"Directorio origen no encontrado: {src_dir}"))
                return
            copied, skipped = _mirror_sprite_tree(src_dir, dest_dir, force=force)
            self.stdout.write(
                self.style.SUCCESS(f"[OK] {dest_dir.name} (espejo): {copied} copiados, {skipped} omitidos.")
            )

        # Paso 2: Descarga selectiva de los 24 PNGs nuevos de las 6 formas de B2W2
        tasks = []
        for form_id, rel_stem in B2W2_NEW_FORMS:
            tasks.append((
                f"{POKEAPI_GEN5_BASE}/{form_id}.png",
                sprites_root / "black-2" / f"{rel_stem}.png",
            ))
            tasks.append((
                f"{POKEAPI_GEN5_BASE}/back/{form_id}.png",
                sprites_root / "black-2" / "back" / f"{rel_stem}.png",
            ))
            tasks.append((
                f"{POKEAPI_GEN5_BASE}/shiny/{form_id}.png",
                sprites_root / "black-2_shiny" / f"{rel_stem}.png",
            ))
            tasks.append((
                f"{POKEAPI_GEN5_BASE}/back/shiny/{form_id}.png",
                sprites_root / "black-2_shiny" / "back" / f"{rel_stem}.png",
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
                f"[OK] Formas nuevas B2W2 (.png): {stats['downloaded']} descargados, "
                f"{stats['skipped']} omitidos, {stats['failed']} fallidos."
            )
        )
