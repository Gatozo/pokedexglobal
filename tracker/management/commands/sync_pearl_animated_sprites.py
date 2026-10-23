import os
import shutil
import time
import urllib.request
import concurrent.futures
from pathlib import Path
from django.conf import settings
from django.core.management.base import BaseCommand
from django.core.cache import cache
from tracker.gender_differences import GENDER_DIFFERENCES_GEN4

USER_AGENT = "PokedexGlobal/1.0 (Educational/Collector Tool; https://github.com/Gatozo/pokedexglobal)"

BASE_NORMAL_URL = "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/versions/generation-iv/diamond-pearl/animated"
BASE_SHINY_URL = "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/versions/generation-iv/diamond-pearl/animated/shiny"

BASE_PLATINUM_NORMAL_URL = "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/versions/generation-iv/platinum/animated"
BASE_PLATINUM_SHINY_URL = "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/versions/generation-iv/platinum/animated/shiny"

UNOWN_LETTERS = [
    "a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m",
    "n", "o", "p", "q", "r", "s", "t", "u", "v", "w", "x", "y", "z",
    "exclamation", "question"
]

ARCEUS_TYPES = [
    "normal", "bug", "dark", "dragon", "electric", "fighting", "fire",
    "flying", "ghost", "grass", "ground", "ice", "poison", "psychic",
    "rock", "steel", "water"
]


def download_single_apng(url: str, dest_path: Path, max_retries: int = 3, force: bool = False) -> bool:
    """Descarga y valida un archivo APNG (.png) asegurando integridad del encabezado PNG."""
    if not force and dest_path.exists() and dest_path.stat().st_size > 0:
        return True

    for attempt in range(max_retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=15) as resp:
                if resp.status == 200:
                    data = resp.read()
                    if len(data) > 0 and data.startswith(b"\x89PNG\r\n\x1a\n"):
                        dest_path.parent.mkdir(parents=True, exist_ok=True)
                        temp_path = dest_path.with_suffix(".tmp")
                        with open(temp_path, "wb") as f:
                            f.write(data)
                        temp_path.replace(dest_path)
                        return True
        except Exception:
            if attempt < max_retries - 1:
                time.sleep(0.4 * (2 ** attempt))

    return False


def copy_local_sprites(src_dir: Path, dst_dir: Path):
    dst_dir.mkdir(parents=True, exist_ok=True)
    if src_dir.exists():
        for src_file in src_dir.rglob("*.png"):
            rel_path = src_file.relative_to(src_dir)
            target = dst_dir / rel_path
            if not target.exists() or target.stat().st_size == 0:
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src_file, target)


class Command(BaseCommand):
    help = "Descarga y almacena localmente los sprites animados (APNG) de Pokémon Perla para el modal cómic."

    def add_arguments(self, parser):
        parser.add_argument("--force", action="store_true", help="Fuerza la descarga incluso si el archivo ya existe.")
        parser.add_argument("--workers", type=int, default=16, help="Hilos concurrentes para la descarga (defecto: 16)")

    def handle(self, *args, **options):
        force = options["force"]
        workers = options["workers"]

        base_normal_dir = Path(settings.MEDIA_ROOT) / "pokemon" / "sprites" / "pearl_animated"
        base_shiny_dir = Path(settings.MEDIA_ROOT) / "pokemon" / "sprites" / "pearl_animated_shiny"

        base_normal_dir.mkdir(parents=True, exist_ok=True)
        base_shiny_dir.mkdir(parents=True, exist_ok=True)

        # 1. Sincronización offline-first desde el paquete consolidado D/P
        dia_norm = Path(settings.MEDIA_ROOT) / "pokemon" / "sprites" / "diamond_animated"
        dia_shiny = Path(settings.MEDIA_ROOT) / "pokemon" / "sprites" / "diamond_animated_shiny"
        if dia_norm.exists() and not force:
            copy_local_sprites(dia_norm, base_normal_dir)
        if dia_shiny.exists() and not force:
            copy_local_sprites(dia_shiny, base_shiny_dir)

        tasks = []

        # 1. Especies Base (1 a 493)
        for num in range(1, 494):
            if num == 421:
                url_norm = f"{BASE_PLATINUM_NORMAL_URL}/421.png"
                url_shiny = f"{BASE_PLATINUM_SHINY_URL}/421.png"
            else:
                url_norm = f"{BASE_NORMAL_URL}/{num}.png"
                url_shiny = f"{BASE_SHINY_URL}/{num}.png"

            dest_norm = base_normal_dir / f"{num}.png"
            if not dest_norm.exists() or force:
                tasks.append((url_norm, dest_norm, f"#{num} normal"))

            dest_shiny = base_shiny_dir / f"{num}.png"
            if not dest_shiny.exists() or force:
                tasks.append((url_shiny, dest_shiny, f"#{num} shiny"))

        # 2. Variantes Femeninas (93 especies de Gen 4)
        for num in GENDER_DIFFERENCES_GEN4.keys():
            dest_norm = base_normal_dir / "female" / f"{num}.png"
            if not dest_norm.exists() or force:
                tasks.append((f"{BASE_NORMAL_URL}/female/{num}.png", dest_norm, f"#{num} hembra normal"))

            dest_shiny = base_shiny_dir / "female" / f"{num}.png"
            if not dest_shiny.exists() or force:
                tasks.append((f"{BASE_SHINY_URL}/female/{num}.png", dest_shiny, f"#{num} hembra shiny"))

        # 3. Formas de Unown (#201)
        for letter in UNOWN_LETTERS:
            dest_norm = base_normal_dir / "unown" / f"{letter}.png"
            if not dest_norm.exists() or force:
                tasks.append((f"{BASE_NORMAL_URL}/201-{letter}.png", dest_norm, f"Unown {letter} normal"))

            dest_shiny = base_shiny_dir / "unown" / f"{letter}.png"
            if not dest_shiny.exists() or force:
                tasks.append((f"{BASE_SHINY_URL}/201-{letter}.png", dest_shiny, f"Unown {letter} shiny"))

        # 4. Burmy (#412) y Wormadam (#413)
        burmy_wormadam_map = {
            "plant": "{num}.png",
            "sandy": "{num}-trash.png",
            "trash": "{num}-sandy.png",
        }
        for num, key in [(412, "burmy"), (413, "wormadam")]:
            for form, file_tmpl in burmy_wormadam_map.items():
                src_name = file_tmpl.format(num=num)
                dest_norm = base_normal_dir / key / f"{form}.png"
                if not dest_norm.exists() or force:
                    tasks.append((f"{BASE_NORMAL_URL}/{src_name}", dest_norm, f"{key} {form} normal"))
                dest_shiny = base_shiny_dir / key / f"{form}.png"
                if not dest_shiny.exists() or force:
                    tasks.append((f"{BASE_SHINY_URL}/{src_name}", dest_shiny, f"{key} {form} shiny"))

        # 5. Shellos (#422) y Gastrodon (#423)
        for num, key, form in [(422, "shellos", "west"), (422, "shellos", "east"),
                               (423, "gastrodon", "west"), (423, "gastrodon", "east")]:
            src_name = f"{num}.png" if form == "west" else f"{num}-{form}.png"
            dest_norm = base_normal_dir / key / f"{form}.png"
            if not dest_norm.exists() or force:
                tasks.append((f"{BASE_NORMAL_URL}/{src_name}", dest_norm, f"{key} {form} normal"))
            dest_shiny = base_shiny_dir / key / f"{form}.png"
            if not dest_shiny.exists() or force:
                tasks.append((f"{BASE_SHINY_URL}/{src_name}", dest_shiny, f"{key} {form} shiny"))

        # 6. Cherrim (#421)
        if not (base_normal_dir / "cherrim" / "overcast.png").exists() or force:
            tasks.append((f"{BASE_PLATINUM_NORMAL_URL}/421.png", base_normal_dir / "cherrim" / "overcast.png", "Cherrim overcast normal"))
        if not (base_shiny_dir / "cherrim" / "overcast.png").exists() or force:
            tasks.append((f"{BASE_PLATINUM_SHINY_URL}/421.png", base_shiny_dir / "cherrim" / "overcast.png", "Cherrim overcast shiny"))
        if not (base_normal_dir / "cherrim" / "sunshine.png").exists() or force:
            tasks.append((f"{BASE_NORMAL_URL}/421-sunshine.png", base_normal_dir / "cherrim" / "sunshine.png", "Cherrim sunshine normal"))
        if not (base_shiny_dir / "cherrim" / "sunshine.png").exists() or force:
            tasks.append((f"{BASE_SHINY_URL}/421-sunshine.png", base_shiny_dir / "cherrim" / "sunshine.png", "Cherrim sunshine shiny"))

        # 7. Deoxys (#386)
        for form, src_name in [("normal", "386.png"), ("attack", "10001.png"), ("defense", "10002.png"), ("speed", "10003.png")]:
            dest_norm = base_normal_dir / "deoxys" / f"{form}.png"
            if not dest_norm.exists() or force:
                tasks.append((f"{BASE_NORMAL_URL}/{src_name}", dest_norm, f"Deoxys {form} normal"))
            dest_shiny = base_shiny_dir / "deoxys" / f"{form}.png"
            if not dest_shiny.exists() or force:
                tasks.append((f"{BASE_SHINY_URL}/{src_name}", dest_shiny, f"Deoxys {form} shiny"))

        # 8. Arceus (#493)
        for t in ARCEUS_TYPES:
            src_name = "493.png" if t == "normal" else f"493-{t}.png"
            dest_norm = base_normal_dir / "arceus" / f"{t}.png"
            if not dest_norm.exists() or force:
                tasks.append((f"{BASE_NORMAL_URL}/{src_name}", dest_norm, f"Arceus {t} normal"))
            dest_shiny = base_shiny_dir / "arceus" / f"{t}.png"
            if not dest_shiny.exists() or force:
                tasks.append((f"{BASE_SHINY_URL}/{src_name}", dest_shiny, f"Arceus {t} shiny"))

        # 9. Castform (#351)
        if not (base_normal_dir / "castform" / "normal.png").exists() or force:
            tasks.append((f"{BASE_NORMAL_URL}/351.png", base_normal_dir / "castform" / "normal.png", "Castform normal"))
        if not (base_shiny_dir / "castform" / "normal.png").exists() or force:
            tasks.append((f"{BASE_SHINY_URL}/351.png", base_shiny_dir / "castform" / "normal.png", "Castform shiny"))

        total_tasks = len(tasks)
        if total_tasks > 0:
            self.stdout.write(f"Descargando {total_tasks} sprites animados faltantes de Pokémon Perla...")
            with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
                future_to_desc = {
                    executor.submit(download_single_apng, url, dest, 3, force): desc
                    for url, dest, desc in tasks
                }
                for future in concurrent.futures.as_completed(future_to_desc):
                    desc = future_to_desc[future]
                    try:
                        future.result()
                    except Exception as exc:
                        self.stderr.write(f"[ERROR] Excepción al procesar {desc}: {exc}")

        cache.clear()
        norm_count = len(list(base_normal_dir.rglob("*.png")))
        shiny_count = len(list(base_shiny_dir.rglob("*.png")))
        self.stdout.write(self.style.SUCCESS(
            f"¡Completado! {norm_count} animados normales y {shiny_count} shinies en media/pokemon/sprites/pearl_animated*/."
        ))
