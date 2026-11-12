import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from django.conf import settings
from django.core.management.base import BaseCommand
from tracker.gender_differences import GENDER_DIFFERENCES_GEN4, GENDER_DIFFERENCES_GEN5

USER_AGENT = "PokedexGlobal/1.0 (Educational/Collector Tool; https://github.com/Gatozo/pokedexglobal)"
BASE_ANIMATED_URL = "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/versions/generation-v/black-white/animated"
BASE_STATIC_URL = "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/versions/generation-v/black-white"

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


def download_single_gif(url: str, dest_path: Path, max_retries: int = 3, force: bool = False) -> bool:
    """Descarga y valida un archivo GIF asegurando integridad de encabezado GIF87a/GIF89a."""
    if not force and dest_path.exists() and dest_path.stat().st_size > 0:
        return True

    for attempt in range(max_retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=15) as resp:
                if resp.status == 200:
                    data = resp.read()
                    if len(data) > 0 and data.startswith(b"GIF8"):
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


def download_fallback_png(url: str, dest_path: Path, max_retries: int = 2) -> bool:
    """Fallback si no existe versión animada en PokeAPI pero existe PNG estático."""
    if dest_path.exists() and dest_path.stat().st_size > 0:
        return True
    try:
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=10) as resp:
            if resp.status == 200:
                data = resp.read()
                if len(data) > 0 and (data.startswith(b"\x89PNG") or data.startswith(b"GIF8")):
                    dest_path.parent.mkdir(parents=True, exist_ok=True)
                    with open(dest_path, "wb") as f:
                        f.write(data)
                    return True
    except Exception:
        pass
    return False


class Command(BaseCommand):
    help = "Descarga y almacena localmente los sprites animados (.gif) de Pokémon Negro (1..649, espaldas, hembras y formas)."

    def add_arguments(self, parser):
        parser.add_argument("--force", action="store_true", help="Fuerza la descarga incluso si el archivo ya existe.")
        parser.add_argument("--workers", type=int, default=16, help="Hilos concurrentes para la descarga (defecto: 16)")

    def handle(self, *args, **options):
        force = options["force"]
        workers = options["workers"]

        base_normal_dir = Path(settings.MEDIA_ROOT) / "pokemon" / "sprites" / "black_animated"
        base_shiny_dir = Path(settings.MEDIA_ROOT) / "pokemon" / "sprites" / "black_animated_shiny"

        tasks = []

        # 1. Especies 1 a 649 (frente normal, frente shiny, espalda normal, espalda shiny)
        for nat_id in range(1, 650):
            tasks.append((f"{BASE_ANIMATED_URL}/{nat_id}.gif", base_normal_dir / f"{nat_id}.gif", False))
            tasks.append((f"{BASE_ANIMATED_URL}/shiny/{nat_id}.gif", base_shiny_dir / f"{nat_id}.gif", False))
            tasks.append((f"{BASE_ANIMATED_URL}/back/{nat_id}.gif", base_normal_dir / "back" / f"{nat_id}.gif", False))
            tasks.append((f"{BASE_ANIMATED_URL}/back/shiny/{nat_id}.gif", base_shiny_dir / "back" / f"{nat_id}.gif", False))

        # 2. Variantes femeninas (97 especies)
        female_species = set(GENDER_DIFFERENCES_GEN4) | set(GENDER_DIFFERENCES_GEN5)
        for nat_id in female_species:
            tasks.append((f"{BASE_ANIMATED_URL}/female/{nat_id}.gif", base_normal_dir / "female" / f"{nat_id}.gif", False))
            tasks.append((f"{BASE_ANIMATED_URL}/shiny/female/{nat_id}.gif", base_shiny_dir / "female" / f"{nat_id}.gif", False))
            tasks.append((f"{BASE_ANIMATED_URL}/back/female/{nat_id}.gif", base_normal_dir / "back" / "female" / f"{nat_id}.gif", False))
            tasks.append((f"{BASE_ANIMATED_URL}/back/shiny/female/{nat_id}.gif", base_shiny_dir / "back" / "female" / f"{nat_id}.gif", False))

        # 3. Formas alternas animadas (Tabla 4.4)
        def add_animated_form(subfolder: str, form_key: str, src_stem: str, has_back_gif: bool = True):
            # Frente
            tasks.append((f"{BASE_ANIMATED_URL}/{src_stem}.gif", base_normal_dir / subfolder / f"{form_key}.gif", False))
            tasks.append((f"{BASE_ANIMATED_URL}/shiny/{src_stem}.gif", base_shiny_dir / subfolder / f"{form_key}.gif", False))
            # Espalda
            if has_back_gif:
                tasks.append((f"{BASE_ANIMATED_URL}/back/{src_stem}.gif", base_normal_dir / "back" / subfolder / f"{form_key}.gif", False))
                tasks.append((f"{BASE_ANIMATED_URL}/back/shiny/{src_stem}.gif", base_shiny_dir / "back" / subfolder / f"{form_key}.gif", False))
            else:
                # Si PokeAPI no provee gif de espalda para la subforma, intentar gif y caer a estático si falla
                tasks.append((f"{BASE_ANIMATED_URL}/back/{src_stem}.gif", base_normal_dir / "back" / subfolder / f"{form_key}.gif", True))
                tasks.append((f"{BASE_ANIMATED_URL}/back/shiny/{src_stem}.gif", base_shiny_dir / "back" / subfolder / f"{form_key}.gif", True))

        # Unown (201)
        for letter in UNOWN_LETTERS:
            stem = "201-a" if letter == "a" else f"201-{letter}"
            add_animated_form("unown", letter, stem)

        # Castform (351)
        add_animated_form("castform", "normal", "351")
        add_animated_form("castform", "sunny", "10013")
        add_animated_form("castform", "rainy", "10014")
        add_animated_form("castform", "snowy", "10015")

        # Deoxys (386)
        add_animated_form("deoxys", "normal", "386")
        add_animated_form("deoxys", "attack", "10001")
        add_animated_form("deoxys", "defense", "10002")
        add_animated_form("deoxys", "speed", "10003")

        # Burmy (412)
        add_animated_form("burmy", "plant", "412")
        add_animated_form("burmy", "sandy", "412-sandy", has_back_gif=False)
        add_animated_form("burmy", "trash", "412-trash", has_back_gif=False)

        # Wormadam (413)
        add_animated_form("wormadam", "plant", "413")
        add_animated_form("wormadam", "sandy", "10004")
        add_animated_form("wormadam", "trash", "10005")

        # Cherrim (421)
        add_animated_form("cherrim", "overcast", "421")
        add_animated_form("cherrim", "sunshine", "421-sunshine", has_back_gif=False)

        # Shellos (422)
        add_animated_form("shellos", "west", "422")
        add_animated_form("shellos", "east", "422-east", has_back_gif=False)

        # Gastrodon (423)
        add_animated_form("gastrodon", "west", "423")
        add_animated_form("gastrodon", "east", "423-east", has_back_gif=False)

        # Rotom (479)
        add_animated_form("rotom", "normal", "479")
        add_animated_form("rotom", "heat", "10008")
        add_animated_form("rotom", "wash", "10009")
        add_animated_form("rotom", "frost", "10010")
        add_animated_form("rotom", "fan", "10011")
        add_animated_form("rotom", "mow", "10012")

        # Giratina (487)
        add_animated_form("giratina", "altered", "487")
        add_animated_form("giratina", "origin", "10007")

        # Shaymin (492)
        add_animated_form("shaymin", "land", "492")
        add_animated_form("shaymin", "sky", "10006")

        # Arceus (493)
        add_animated_form("arceus", "normal", "493")
        for arc_type in ARCEUS_TYPES:
            add_animated_form("arceus", arc_type, f"493-{arc_type}", has_back_gif=False)

        # Basculin (550)
        add_animated_form("basculin", "red", "550")
        add_animated_form("basculin", "blue", "10016")

        # Darmanitan (555)
        add_animated_form("darmanitan", "standard", "555")
        add_animated_form("darmanitan", "zen", "10017")

        # Deerling (585)
        add_animated_form("deerling", "spring", "585-spring")
        add_animated_form("deerling", "summer", "585-summer")
        add_animated_form("deerling", "autumn", "585-autumn", has_back_gif=False)
        add_animated_form("deerling", "winter", "585-winter", has_back_gif=False)

        # Sawsbuck (586)
        add_animated_form("sawsbuck", "spring", "586-spring")
        add_animated_form("sawsbuck", "summer", "586-summer")
        add_animated_form("sawsbuck", "autumn", "586-autumn", has_back_gif=False)
        add_animated_form("sawsbuck", "winter", "586-winter", has_back_gif=False)

        # Meloetta (648)
        add_animated_form("meloetta", "aria", "648")
        add_animated_form("meloetta", "pirouette", "10018")

        # Genesect (649)
        add_animated_form("genesect", "normal", "649")
        add_animated_form("genesect", "douse", "649-douse")
        add_animated_form("genesect", "shock", "649-shock", has_back_gif=False)
        add_animated_form("genesect", "burn", "649-burn", has_back_gif=False)
        add_animated_form("genesect", "chill", "649-chill", has_back_gif=False)

        self.stdout.write(f"Iniciando descarga de {len(tasks)} sprites animados (.gif) de Pokémon Negro con {workers} hilos...")

        downloaded = 0
        failed = 0

        def process_task(item):
            url, dest, allow_fallback = item
            res = download_single_gif(url, dest, 3, force)
            if not res and allow_fallback:
                # Intentar fallback a estático png
                png_url = url.replace("/animated", "").replace(".gif", ".png")
                png_dest = dest.with_suffix(".png")
                res = download_fallback_png(png_url, png_dest)
            return res

        with ThreadPoolExecutor(max_workers=workers) as executor:
            future_to_item = {executor.submit(process_task, item): item for item in tasks}
            for future in as_completed(future_to_item):
                try:
                    res = future.result()
                    if res:
                        downloaded += 1
                    else:
                        failed += 1
                except Exception:
                    failed += 1

        self.stdout.write(self.style.SUCCESS(
            f"Sincronización animada finalizada:\n"
            f"  - Procesados con éxito: {downloaded}\n"
            f"  - No disponibles / Fallos opcionales: {failed}"
        ))
