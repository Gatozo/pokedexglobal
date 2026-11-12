import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from django.conf import settings
from django.core.management.base import BaseCommand
from tracker.gender_differences import GENDER_DIFFERENCES_GEN4, GENDER_DIFFERENCES_GEN5

USER_AGENT = "PokedexGlobal/1.0 (Educational/Collector Tool; https://github.com/Gatozo/pokedexglobal)"
BASE_URL = "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/versions/generation-v/black-white"

UNOWN_LETTERS = [
    "a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m",
    "n", "o", "p", "q", "r", "s", "t", "u", "v", "w", "x", "y", "z",
    "exclamation", "question"
]

ARCEUS_TYPES = [
    "bug", "dark", "dragon", "electric", "fighting", "fire",
    "flying", "ghost", "grass", "ground", "ice", "poison", "psychic",
    "rock", "steel", "water"
]


def download_single_png(url: str, dest_path: Path, max_retries: int = 3, force: bool = False) -> bool:
    """Descarga y valida un archivo PNG asegurando integridad de encabezado PNG."""
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
                time.sleep(0.3 * (2 ** attempt))

    return False


class Command(BaseCommand):
    help = "Descarga y almacena localmente los sprites estáticos (.png) de Pokémon Negro (1..649, hembras y formas)."

    def add_arguments(self, parser):
        parser.add_argument("--force", action="store_true", help="Fuerza la descarga incluso si el archivo ya existe.")
        parser.add_argument("--workers", type=int, default=16, help="Hilos concurrentes para la descarga (defecto: 16)")

    def handle(self, *args, **options):
        force = options["force"]
        workers = options["workers"]

        base_normal_dir = Path(settings.MEDIA_ROOT) / "pokemon" / "sprites" / "black"
        base_shiny_dir = Path(settings.MEDIA_ROOT) / "pokemon" / "sprites" / "black_shiny"

        tasks = []

        # 1. Especies 1 a 649 (frente normal, frente shiny, espalda normal, espalda shiny)
        for nat_id in range(1, 650):
            tasks.append((f"{BASE_URL}/{nat_id}.png", base_normal_dir / f"{nat_id}.png"))
            tasks.append((f"{BASE_URL}/shiny/{nat_id}.png", base_shiny_dir / f"{nat_id}.png"))
            tasks.append((f"{BASE_URL}/back/{nat_id}.png", base_normal_dir / "back" / f"{nat_id}.png"))
            tasks.append((f"{BASE_URL}/back/shiny/{nat_id}.png", base_shiny_dir / "back" / f"{nat_id}.png"))

        # 2. Variantes femeninas (97 especies: 94 Gen 1-4 + 3 Gen 5: 521, 592, 593)
        female_species = set(GENDER_DIFFERENCES_GEN4) | set(GENDER_DIFFERENCES_GEN5)
        for nat_id in female_species:
            tasks.append((f"{BASE_URL}/female/{nat_id}.png", base_normal_dir / "female" / f"{nat_id}.png"))
            tasks.append((f"{BASE_URL}/shiny/female/{nat_id}.png", base_shiny_dir / "female" / f"{nat_id}.png"))
            tasks.append((f"{BASE_URL}/back/female/{nat_id}.png", base_normal_dir / "back" / "female" / f"{nat_id}.png"))
            tasks.append((f"{BASE_URL}/back/shiny/female/{nat_id}.png", base_shiny_dir / "back" / "female" / f"{nat_id}.png"))

        # 3. Formas alternas (Tabla 4.4)
        def add_form_task(subfolder: str, form_key: str, src_stem: str):
            # Normal frente
            tasks.append((f"{BASE_URL}/{src_stem}.png", base_normal_dir / subfolder / f"{form_key}.png"))
            # Shiny frente
            tasks.append((f"{BASE_URL}/shiny/{src_stem}.png", base_shiny_dir / subfolder / f"{form_key}.png"))
            # Normal espalda
            tasks.append((f"{BASE_URL}/back/{src_stem}.png", base_normal_dir / "back" / subfolder / f"{form_key}.png"))
            # Shiny espalda
            tasks.append((f"{BASE_URL}/back/shiny/{src_stem}.png", base_shiny_dir / "back" / subfolder / f"{form_key}.png"))

        # Unown (201)
        for letter in UNOWN_LETTERS:
            stem = "201" if letter == "a" else f"201-{letter}"
            add_form_task("unown", letter, stem)

        # Castform (351)
        add_form_task("castform", "normal", "351")
        add_form_task("castform", "sunny", "10013")
        add_form_task("castform", "rainy", "10014")
        add_form_task("castform", "snowy", "10015")

        # Deoxys (386)
        add_form_task("deoxys", "normal", "386")
        add_form_task("deoxys", "attack", "10001")
        add_form_task("deoxys", "defense", "10002")
        add_form_task("deoxys", "speed", "10003")

        # Burmy (412)
        add_form_task("burmy", "plant", "412")
        add_form_task("burmy", "sandy", "412-sandy")
        add_form_task("burmy", "trash", "412-trash")

        # Wormadam (413)
        add_form_task("wormadam", "plant", "413")
        add_form_task("wormadam", "sandy", "10004")
        add_form_task("wormadam", "trash", "10005")

        # Cherrim (421)
        add_form_task("cherrim", "overcast", "421")
        add_form_task("cherrim", "sunshine", "421-sunshine")

        # Shellos (422)
        add_form_task("shellos", "west", "422")
        add_form_task("shellos", "east", "422-east")

        # Gastrodon (423)
        add_form_task("gastrodon", "west", "423")
        add_form_task("gastrodon", "east", "423-east")

        # Rotom (479)
        add_form_task("rotom", "normal", "479")
        add_form_task("rotom", "heat", "10008")
        add_form_task("rotom", "wash", "10009")
        add_form_task("rotom", "frost", "10010")
        add_form_task("rotom", "fan", "10011")
        add_form_task("rotom", "mow", "10012")

        # Giratina (487)
        add_form_task("giratina", "altered", "487")
        add_form_task("giratina", "origin", "10007")

        # Shaymin (492)
        add_form_task("shaymin", "land", "492")
        add_form_task("shaymin", "sky", "10006")

        # Arceus (493)
        add_form_task("arceus", "normal", "493")
        for arc_type in ARCEUS_TYPES:
            add_form_task("arceus", arc_type, f"493-{arc_type}")

        # Basculin (550)
        add_form_task("basculin", "red", "550")
        add_form_task("basculin", "blue", "10016")

        # Darmanitan (555)
        add_form_task("darmanitan", "standard", "555")
        add_form_task("darmanitan", "zen", "10017")

        # Deerling (585)
        add_form_task("deerling", "spring", "585")
        add_form_task("deerling", "summer", "585-summer")
        add_form_task("deerling", "autumn", "585-autumn")
        add_form_task("deerling", "winter", "585-winter")

        # Sawsbuck (586)
        add_form_task("sawsbuck", "spring", "586")
        add_form_task("sawsbuck", "summer", "586-summer")
        add_form_task("sawsbuck", "autumn", "586-autumn")
        add_form_task("sawsbuck", "winter", "586-winter")

        # Meloetta (648)
        add_form_task("meloetta", "aria", "648")
        add_form_task("meloetta", "pirouette", "10018")

        # Genesect (649)
        add_form_task("genesect", "normal", "649")
        add_form_task("genesect", "douse", "649-douse")
        add_form_task("genesect", "shock", "649-shock")
        add_form_task("genesect", "burn", "649-burn")
        add_form_task("genesect", "chill", "649-chill")

        self.stdout.write(f"Iniciando descarga de {len(tasks)} sprites estáticos de Pokémon Negro con {workers} hilos...")

        downloaded = 0
        skipped = 0
        failed = 0

        with ThreadPoolExecutor(max_workers=workers) as executor:
            future_to_url = {executor.submit(download_single_png, url, path, 3, force): (url, path) for url, path in tasks}
            for future in as_completed(future_to_url):
                url, path = future_to_url[future]
                try:
                    res = future.result()
                    if res:
                        downloaded += 1
                    else:
                        failed += 1
                except Exception:
                    failed += 1

        self.stdout.write(self.style.SUCCESS(
            f"Sincronización finalizada:\n"
            f"  - Procesados con éxito: {downloaded}\n"
            f"  - No disponibles / Fallos opcionales: {failed}"
        ))
