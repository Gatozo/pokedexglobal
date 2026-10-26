import os
import shutil
import time
import urllib.request
import concurrent.futures
from pathlib import Path
from django.conf import settings
from django.core.management.base import BaseCommand
from tracker.gender_differences import GENDER_DIFFERENCES_GEN4

USER_AGENT = "PokedexGlobal/1.0 (Educational/Collector Tool; https://github.com/Gatozo/pokedexglobal)"

BASE_NORMAL_URL = "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/versions/generation-iv/platinum/animated"
BASE_SHINY_URL = "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/versions/generation-iv/platinum/animated/shiny"

ROTOM_FORMS = [
    ("heat", 10008),
    ("wash", 10009),
    ("frost", 10010),
    ("fan", 10011),
    ("mow", 10012),
]

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


class Command(BaseCommand):
    help = "Descarga y almacena localmente los sprites animados (APNG) de Pokémon Platino para el modal cómic."

    def add_arguments(self, parser):
        parser.add_argument("--force", action="store_true", help="Fuerza la descarga incluso si el archivo ya existe.")
        parser.add_argument("--workers", type=int, default=16, help="Hilos concurrentes para la descarga (defecto: 16)")

    def handle(self, *args, **options):
        force = options["force"]
        workers = options["workers"]

        base_normal_dir = Path(settings.MEDIA_ROOT) / "pokemon" / "sprites" / "platinum_animated"
        base_shiny_dir = Path(settings.MEDIA_ROOT) / "pokemon" / "sprites" / "platinum_animated_shiny"

        base_normal_dir.mkdir(parents=True, exist_ok=True)
        base_shiny_dir.mkdir(parents=True, exist_ok=True)

        tasks = []

        # 1. Especies Base (1 a 493)
        for num in range(1, 494):
            url_norm = f"{BASE_NORMAL_URL}/{num}.png"
            url_shiny = f"{BASE_SHINY_URL}/{num}.png"

            dest_norm = base_normal_dir / f"{num}.png"
            if not dest_norm.exists() or force:
                tasks.append((url_norm, dest_norm, f"#{num} normal"))

            dest_shiny = base_shiny_dir / f"{num}.png"
            if not dest_shiny.exists() or force:
                tasks.append((url_shiny, dest_shiny, f"#{num} shiny"))

        # 2. Variantes Femeninas (93 especies de Gen 4, excluyendo Taillow y Swellow sin diff de sprite)
        for num in GENDER_DIFFERENCES_GEN4.keys():
            if num in {277, 278}:
                continue
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
        # PokeAPI invierte sandy y trash en sus nombres de archivo
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
            tasks.append((f"{BASE_NORMAL_URL}/421.png", base_normal_dir / "cherrim" / "overcast.png", "Cherrim overcast normal"))
        if not (base_shiny_dir / "cherrim" / "overcast.png").exists() or force:
            tasks.append((f"{BASE_SHINY_URL}/421.png", base_shiny_dir / "cherrim" / "overcast.png", "Cherrim overcast shiny"))
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
        castform_forms = [
            ("normal", "351.png"),
            ("sunny", "10013.png"),
            ("rainy", "10014.png"),
            ("snowy", "10015.png"),
        ]
        for form_key, src_name in castform_forms:
            dest_norm = base_normal_dir / "castform" / f"{form_key}.png"
            if not dest_norm.exists() or force:
                tasks.append((f"{BASE_NORMAL_URL}/{src_name}", dest_norm, f"Castform {form_key} normal"))
            dest_shiny = base_shiny_dir / "castform" / f"{form_key}.png"
            if not dest_shiny.exists() or force:
                tasks.append((f"{BASE_SHINY_URL}/{src_name}", dest_shiny, f"Castform {form_key} shiny"))

        # 10. Giratina Forma Origen (#487, ID 10007)
        dest_norm = base_normal_dir / "giratina" / "origin.png"
        if not dest_norm.exists() or force:
            tasks.append((f"{BASE_NORMAL_URL}/10007.png", dest_norm, "Giratina origin normal"))
        dest_shiny = base_shiny_dir / "giratina" / "origin.png"
        if not dest_shiny.exists() or force:
            tasks.append((f"{BASE_SHINY_URL}/10007.png", dest_shiny, "Giratina origin shiny"))

        # 11. Shaymin Forma Cielo (#492, ID 10006)
        dest_norm = base_normal_dir / "shaymin" / "sky.png"
        if not dest_norm.exists() or force:
            tasks.append((f"{BASE_NORMAL_URL}/10006.png", dest_norm, "Shaymin sky normal"))
        dest_shiny = base_shiny_dir / "shaymin" / "sky.png"
        if not dest_shiny.exists() or force:
            tasks.append((f"{BASE_SHINY_URL}/10006.png", dest_shiny, "Shaymin sky shiny"))

        # 12. Rotom Electrodomésticos (#479)
        for f_name, f_id in ROTOM_FORMS:
            dest_norm = base_normal_dir / "rotom" / f"{f_name}.png"
            if not dest_norm.exists() or force:
                tasks.append((f"{BASE_NORMAL_URL}/{f_id}.png", dest_norm, f"Rotom {f_name} normal"))
            dest_shiny = base_shiny_dir / "rotom" / f"{f_name}.png"
            if not dest_shiny.exists() or force:
                tasks.append((f"{BASE_SHINY_URL}/{f_id}.png", dest_shiny, f"Rotom {f_name} shiny"))

        total_tasks = len(tasks)
        if total_tasks > 0:
            self.stdout.write(f"Descargando {total_tasks} sprites animados de Pokémon Platino...")
            with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
                future_to_desc = {
                    executor.submit(download_single_apng, url, dest, 3, force): desc
                    for url, dest, desc in tasks
                }
                success_count = 0
                for future in concurrent.futures.as_completed(future_to_desc):
                    desc = future_to_desc[future]
                    try:
                        if future.result():
                            success_count += 1
                        else:
                            self.stderr.write(f"Fallo al descargar {desc}")
                    except Exception as exc:
                        self.stderr.write(f"Excepción en {desc}: {exc}")

            self.stdout.write(self.style.SUCCESS(f"Sincronizados {success_count}/{total_tasks} sprites animados de Platino."))
        else:
            self.stdout.write(self.style.SUCCESS("Todos los sprites animados de Platino ya están en disco."))
