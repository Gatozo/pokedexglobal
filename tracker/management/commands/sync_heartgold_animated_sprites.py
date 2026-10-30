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

BASE_NORMAL_URL = "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/versions/generation-iv/heartgold-soulsilver/animated"
BASE_SHINY_URL = "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/versions/generation-iv/heartgold-soulsilver/animated/shiny"

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
    help = "Descarga y almacena localmente los sprites animados (APNG) de Pokémon Oro HeartGold para el modal cómic."

    def add_arguments(self, parser):
        parser.add_argument("--force", action="store_true", help="Fuerza la descarga incluso si el archivo ya existe.")
        parser.add_argument("--workers", type=int, default=16, help="Hilos concurrentes para la descarga (defecto: 16)")

    def handle(self, *args, **options):
        force = options["force"]
        workers = options["workers"]

        base_normal_dir = Path(settings.MEDIA_ROOT) / "pokemon" / "sprites" / "heartgold_animated"
        base_shiny_dir = Path(settings.MEDIA_ROOT) / "pokemon" / "sprites" / "heartgold_animated_shiny"

        base_normal_dir.mkdir(parents=True, exist_ok=True)
        base_shiny_dir.mkdir(parents=True, exist_ok=True)

        tasks = []

        # 1. Especies Estándar (1 a 493)
        for num in range(1, 494):
            url_norm = f"{BASE_NORMAL_URL}/{num}.png"
            url_shiny = f"{BASE_SHINY_URL}/{num}.png"

            dest_norm = base_normal_dir / f"{num}.png"
            if not dest_norm.exists() or force:
                tasks.append((url_norm, dest_norm, f"#{num} normal"))

            dest_shiny = base_shiny_dir / f"{num}.png"
            if not dest_shiny.exists() or force:
                tasks.append((url_shiny, dest_shiny, f"#{num} shiny"))

        # 2. Variantes Femeninas (Gen 4)
        for num in GENDER_DIFFERENCES_GEN4.keys():
            dest_norm = base_normal_dir / "female" / f"{num}.png"
            if not dest_norm.exists() or force:
                tasks.append((f"{BASE_NORMAL_URL}/female/{num}.png", dest_norm, f"#{num} hembra normal"))

            dest_shiny = base_shiny_dir / "female" / f"{num}.png"
            if not dest_shiny.exists() or force:
                tasks.append((f"{BASE_SHINY_URL}/female/{num}.png", dest_shiny, f"#{num} hembra shiny"))

        # 3. Pichu Picorejita (#172)
        dest_pichu_norm = base_normal_dir / "172-spiky-eared.png"
        if not dest_pichu_norm.exists() or force:
            tasks.append((f"{BASE_NORMAL_URL}/172-spiky-eared.png", dest_pichu_norm, "Pichu picorejita normal"))

        dest_pichu_shiny = base_shiny_dir / "172-spiky-eared.png"
        if not dest_pichu_shiny.exists() or force:
            tasks.append((f"{BASE_SHINY_URL}/172-spiky-eared.png", dest_pichu_shiny, "Pichu picorejita shiny"))

        # 4. Formas de Unown (#201)
        for letter in UNOWN_LETTERS:
            dest_norm = base_normal_dir / "unown" / f"{letter}.png"
            src_name = "201.png" if letter == "a" else f"201-{letter}.png"
            if not dest_norm.exists() or force:
                tasks.append((f"{BASE_NORMAL_URL}/{src_name}", dest_norm, f"Unown {letter} normal"))

            dest_shiny = base_shiny_dir / "unown" / f"{letter}.png"
            if not dest_shiny.exists() or force:
                tasks.append((f"{BASE_SHINY_URL}/{src_name}", dest_shiny, f"Unown {letter} shiny"))

        # 5. Burmy (#412) y Wormadam (#413)
        burmy_map = {"plant": "412.png", "sandy": "412-trash.png", "trash": "412-sandy.png"}
        wormadam_map = {"plant": "413.png", "sandy": "10004.png", "trash": "10005.png"}

        for key, mapping in [("burmy", burmy_map), ("wormadam", wormadam_map)]:
            for form, src_name in mapping.items():
                dest_norm = base_normal_dir / key / f"{form}.png"
                if not dest_norm.exists() or force:
                    tasks.append((f"{BASE_NORMAL_URL}/{src_name}", dest_norm, f"{key} {form} normal"))
                dest_shiny = base_shiny_dir / key / f"{form}.png"
                if not dest_shiny.exists() or force:
                    tasks.append((f"{BASE_SHINY_URL}/{src_name}", dest_shiny, f"{key} {form} shiny"))

        # 6. Shellos (#422) y Gastrodon (#423)
        sg_map = {"west": "422.png", "east": "10002.png"}
        gastro_map = {"west": "423.png", "east": "10003.png"}

        for key, mapping in [("shellos", sg_map), ("gastrodon", gastro_map)]:
            for form, src_name in mapping.items():
                dest_norm = base_normal_dir / key / f"{form}.png"
                if not dest_norm.exists() or force:
                    tasks.append((f"{BASE_NORMAL_URL}/{src_name}", dest_norm, f"{key} {form} normal"))
                dest_shiny = base_shiny_dir / key / f"{form}.png"
                if not dest_shiny.exists() or force:
                    tasks.append((f"{BASE_SHINY_URL}/{src_name}", dest_shiny, f"{key} {form} shiny"))

        # 7. Cherrim (#421)
        if not (base_normal_dir / "cherrim" / "overcast.png").exists() or force:
            tasks.append((f"{BASE_NORMAL_URL}/421.png", base_normal_dir / "cherrim" / "overcast.png", "Cherrim overcast normal"))
        if not (base_shiny_dir / "cherrim" / "overcast.png").exists() or force:
            tasks.append((f"{BASE_SHINY_URL}/421.png", base_shiny_dir / "cherrim" / "overcast.png", "Cherrim overcast shiny"))
        if not (base_normal_dir / "cherrim" / "sunshine.png").exists() or force:
            tasks.append((f"{BASE_NORMAL_URL}/421-sunshine.png", base_normal_dir / "cherrim" / "sunshine.png", "Cherrim sunshine normal"))
        if not (base_shiny_dir / "cherrim" / "sunshine.png").exists() or force:
            tasks.append((f"{BASE_SHINY_URL}/421-sunshine.png", base_shiny_dir / "cherrim" / "sunshine.png", "Cherrim sunshine shiny"))

        # 8. Deoxys (#386)
        deoxys_map = {"normal": "386.png", "attack": "10001.png", "defense": "10002.png", "speed": "10003.png"}
        for form, src_name in deoxys_map.items():
            dest_norm = base_normal_dir / "deoxys" / f"{form}.png"
            if not dest_norm.exists() or force:
                tasks.append((f"{BASE_NORMAL_URL}/{src_name}", dest_norm, f"Deoxys {form} normal"))
            dest_shiny = base_shiny_dir / "deoxys" / f"{form}.png"
            if not dest_shiny.exists() or force:
                tasks.append((f"{BASE_SHINY_URL}/{src_name}", dest_shiny, f"Deoxys {form} shiny"))

        # 9. Arceus (#493)
        arceus_id_map = {
            "normal": "493.png", "bug": "10013.png", "dark": "10014.png", "dragon": "10015.png",
            "electric": "10016.png", "fighting": "10017.png", "fire": "10018.png", "flying": "10019.png",
            "ghost": "10020.png", "grass": "10021.png", "ground": "10022.png", "ice": "10023.png",
            "poison": "10024.png", "psychic": "10025.png", "rock": "10026.png", "steel": "10027.png",
            "water": "10028.png",
        }
        for t, src_name in arceus_id_map.items():
            dest_norm = base_normal_dir / "arceus" / f"{t}.png"
            if not dest_norm.exists() or force:
                tasks.append((f"{BASE_NORMAL_URL}/{src_name}", dest_norm, f"Arceus {t} normal"))
            dest_shiny = base_shiny_dir / "arceus" / f"{t}.png"
            if not dest_shiny.exists() or force:
                tasks.append((f"{BASE_SHINY_URL}/{src_name}", dest_shiny, f"Arceus {t} shiny"))

        # 10. Castform (#351)
        castform_map = {"normal": "351.png", "sunny": "10013.png", "rainy": "10014.png", "snowy": "10015.png"}
        for form_key, src_name in castform_map.items():
            dest_norm = base_normal_dir / "castform" / f"{form_key}.png"
            if not dest_norm.exists() or force:
                tasks.append((f"{BASE_NORMAL_URL}/{src_name}", dest_norm, f"Castform {form_key} normal"))
            dest_shiny = base_shiny_dir / "castform" / f"{form_key}.png"
            if not dest_shiny.exists() or force:
                tasks.append((f"{BASE_SHINY_URL}/{src_name}", dest_shiny, f"Castform {form_key} shiny"))

        # 11. Giratina Forma Origen (#487, ID 10007)
        dest_norm = base_normal_dir / "giratina" / "origin.png"
        if not dest_norm.exists() or force:
            tasks.append((f"{BASE_NORMAL_URL}/10007.png", dest_norm, "Giratina origin normal"))
        dest_shiny = base_shiny_dir / "giratina" / "origin.png"
        if not dest_shiny.exists() or force:
            tasks.append((f"{BASE_SHINY_URL}/10007.png", dest_shiny, "Giratina origin shiny"))

        # 12. Shaymin Forma Cielo (#492, ID 10006)
        dest_norm = base_normal_dir / "shaymin" / "sky.png"
        if not dest_norm.exists() or force:
            tasks.append((f"{BASE_NORMAL_URL}/10006.png", dest_norm, "Shaymin sky normal"))
        dest_shiny = base_shiny_dir / "shaymin" / "sky.png"
        if not dest_shiny.exists() or force:
            tasks.append((f"{BASE_SHINY_URL}/10006.png", dest_shiny, "Shaymin sky shiny"))

        # 13. Rotom Electrodomésticos (#479)
        for f_name, f_id in ROTOM_FORMS:
            dest_norm = base_normal_dir / "rotom" / f"{f_name}.png"
            if not dest_norm.exists() or force:
                tasks.append((f"{BASE_NORMAL_URL}/{f_id}.png", dest_norm, f"Rotom {f_name} normal"))
            dest_shiny = base_shiny_dir / "rotom" / f"{f_name}.png"
            if not dest_shiny.exists() or force:
                tasks.append((f"{BASE_SHINY_URL}/{f_id}.png", dest_shiny, f"Rotom {f_name} shiny"))

        total_tasks = len(tasks)
        self.stdout.write(self.style.NOTICE(f"Total de tareas de descarga animada pendientes: {total_tasks}"))

        if total_tasks == 0:
            self.stdout.write(self.style.SUCCESS("Todos los sprites animados ya existen en disco."))
            return

        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
            future_to_task = {
                executor.submit(download_single_apng, url, dest, 3, force): desc
                for url, dest, desc in tasks
            }
            success_count = 0
            for i, future in enumerate(concurrent.futures.as_completed(future_to_task)):
                desc = future_to_task[future]
                try:
                    if future.result():
                        success_count += 1
                except Exception as exc:
                    self.stdout.write(self.style.ERROR(f"Excepción en {desc}: {exc}"))

        self.stdout.write(self.style.SUCCESS(
            f"Descarga finalizada: {success_count}/{total_tasks} archivos sincronizados con éxito."
        ))
