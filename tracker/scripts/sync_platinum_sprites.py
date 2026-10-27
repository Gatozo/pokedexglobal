"""
Script para sincronizar y descargar localmente los sprites estáticos oficiales de Pokémon Platino
en media/pokemon/sprites/platinum/ y platinum_shiny/ (1..493 front, front shiny, back, back shiny,
hembras, Unown y formas nativas de Platino: Giratina Origen, Shaymin Cielo, Rotom electrodomésticos,
Burmy, Wormadam, Shellos, Gastrodon, Deoxys, Arceus).
Descarga directa desde PokeAPI GitHub Raw con verificación e idempotencia.
"""
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import time
from tracker.gender_differences import GENDER_DIFFERENCES_GEN4

BASE_DIR = Path(__file__).resolve().parent.parent.parent
MEDIA_DIR = BASE_DIR / "media" / "pokemon" / "sprites"
PLATINUM_DIR = MEDIA_DIR / "platinum"
PLATINUM_SHINY_DIR = MEDIA_DIR / "platinum_shiny"

PLATINUM_DIR.mkdir(parents=True, exist_ok=True)
PLATINUM_SHINY_DIR.mkdir(parents=True, exist_ok=True)

BASE_URL = "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/versions/generation-iv/platinum"

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


def download_single_sprite(url: str, dest_path: Path):
    if dest_path.exists() and dest_path.stat().st_size > 0:
        return True
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) PokedexGlobal/1.0'}
    req = urllib.request.Request(url, headers=headers)
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=12) as resp:
                content = resp.read()
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                dest_path.write_bytes(content)
                return True
        except Exception:
            time.sleep(0.4 * (attempt + 1))
    return False


def build_tasks():
    tasks = []

    # 1. Especies Estándar 1 a 493 (Frontal, Frontal Shiny, Dorsal, Dorsal Shiny)
    for nat_id in range(1, 494):
        # Frontal normal
        tasks.append((f"{BASE_URL}/{nat_id}.png", PLATINUM_DIR / f"{nat_id}.png"))
        # Frontal shiny
        tasks.append((f"{BASE_URL}/shiny/{nat_id}.png", PLATINUM_SHINY_DIR / f"{nat_id}.png"))
        # Dorsal normal
        tasks.append((f"{BASE_URL}/back/{nat_id}.png", PLATINUM_DIR / "back" / f"{nat_id}.png"))
        # Dorsal shiny
        tasks.append((f"{BASE_URL}/back/shiny/{nat_id}.png", PLATINUM_SHINY_DIR / "back" / f"{nat_id}.png"))

    # 2. Diferencias de Género (Hembras normales y shinies, frontales y dorsales)
    for nat_id in GENDER_DIFFERENCES_GEN4.keys():
        tasks.append((f"{BASE_URL}/female/{nat_id}.png", PLATINUM_DIR / "female" / f"{nat_id}.png"))
        tasks.append((f"{BASE_URL}/shiny/female/{nat_id}.png", PLATINUM_SHINY_DIR / "female" / f"{nat_id}.png"))
        tasks.append((f"{BASE_URL}/back/female/{nat_id}.png", PLATINUM_DIR / "back" / "female" / f"{nat_id}.png"))
        tasks.append((f"{BASE_URL}/back/shiny/female/{nat_id}.png", PLATINUM_SHINY_DIR / "back" / "female" / f"{nat_id}.png"))

    # 3. Giratina Forma Origen (#487, ID 10007)
    tasks.append((f"{BASE_URL}/10007.png", PLATINUM_DIR / "giratina" / "origin.png"))
    tasks.append((f"{BASE_URL}/shiny/10007.png", PLATINUM_SHINY_DIR / "giratina" / "origin.png"))
    tasks.append((f"{BASE_URL}/back/10007.png", PLATINUM_DIR / "back" / "giratina" / "origin.png"))
    tasks.append((f"{BASE_URL}/back/shiny/10007.png", PLATINUM_SHINY_DIR / "back" / "giratina" / "origin.png"))

    # 4. Shaymin Forma Cielo (#492, ID 10006)
    tasks.append((f"{BASE_URL}/10006.png", PLATINUM_DIR / "shaymin" / "sky.png"))
    tasks.append((f"{BASE_URL}/shiny/10006.png", PLATINUM_SHINY_DIR / "shaymin" / "sky.png"))
    tasks.append((f"{BASE_URL}/back/10006.png", PLATINUM_DIR / "back" / "shaymin" / "sky.png"))
    tasks.append((f"{BASE_URL}/back/shiny/10006.png", PLATINUM_SHINY_DIR / "back" / "shaymin" / "sky.png"))

    # 5. Rotom Electrodomésticos (#479)
    for f_name, f_id in ROTOM_FORMS:
        tasks.append((f"{BASE_URL}/{f_id}.png", PLATINUM_DIR / "rotom" / f"{f_name}.png"))
        tasks.append((f"{BASE_URL}/shiny/{f_id}.png", PLATINUM_SHINY_DIR / "rotom" / f"{f_name}.png"))
        tasks.append((f"{BASE_URL}/back/{f_id}.png", PLATINUM_DIR / "back" / "rotom" / f"{f_name}.png"))
        tasks.append((f"{BASE_URL}/back/shiny/{f_id}.png", PLATINUM_SHINY_DIR / "back" / "rotom" / f"{f_name}.png"))

    # 6. Burmy (#412) y Wormadam (#413) (plant, sandy, trash)
    # PokeAPI invierte sandy y trash en sus nombres de archivo para Burmy (412)
    burmy_map = {
        "plant": "412.png",
        "sandy": "412-trash.png",
        "trash": "412-sandy.png",
    }
    for form, src_name in burmy_map.items():
        tasks.append((f"{BASE_URL}/{src_name}", PLATINUM_DIR / "burmy" / f"{form}.png"))
        tasks.append((f"{BASE_URL}/shiny/{src_name}", PLATINUM_SHINY_DIR / "burmy" / f"{form}.png"))
        tasks.append((f"{BASE_URL}/back/{src_name}", PLATINUM_DIR / "back" / "burmy" / f"{form}.png"))
        tasks.append((f"{BASE_URL}/back/shiny/{src_name}", PLATINUM_SHINY_DIR / "back" / "burmy" / f"{form}.png"))

    # Wormadam (#413): En PokeAPI Platino estático, las formas usan IDs de PokeAPI 10004 (sandy) y 10005 (trash)
    wormadam_map = {
        "plant": "413.png",
        "sandy": "10004.png",
        "trash": "10005.png",
    }
    for form, src_name in wormadam_map.items():
        tasks.append((f"{BASE_URL}/{src_name}", PLATINUM_DIR / "wormadam" / f"{form}.png"))
        tasks.append((f"{BASE_URL}/shiny/{src_name}", PLATINUM_SHINY_DIR / "wormadam" / f"{form}.png"))
        tasks.append((f"{BASE_URL}/back/{src_name}", PLATINUM_DIR / "back" / "wormadam" / f"{form}.png"))
        tasks.append((f"{BASE_URL}/back/shiny/{src_name}", PLATINUM_SHINY_DIR / "back" / "wormadam" / f"{form}.png"))

    # 7. Shellos (#422) y Gastrodon (#423)
    for num, key, form in [(422, "shellos", "west"), (422, "shellos", "east"),
                           (423, "gastrodon", "west"), (423, "gastrodon", "east")]:
        src_name = f"{num}.png" if form == "west" else f"{num}-{form}.png"
        tasks.append((f"{BASE_URL}/{src_name}", PLATINUM_DIR / key / f"{form}.png"))
        tasks.append((f"{BASE_URL}/shiny/{src_name}", PLATINUM_SHINY_DIR / key / f"{form}.png"))
        tasks.append((f"{BASE_URL}/back/{src_name}", PLATINUM_DIR / "back" / key / f"{form}.png"))
        tasks.append((f"{BASE_URL}/back/shiny/{src_name}", PLATINUM_SHINY_DIR / "back" / key / f"{form}.png"))

    # 8. Deoxys (#386)
    for form, src_name in [("normal", "386.png"), ("attack", "10001.png"), ("defense", "10002.png"), ("speed", "10003.png")]:
        tasks.append((f"{BASE_URL}/{src_name}", PLATINUM_DIR / "deoxys" / f"{form}.png"))
        tasks.append((f"{BASE_URL}/shiny/{src_name}", PLATINUM_SHINY_DIR / "deoxys" / f"{form}.png"))
        tasks.append((f"{BASE_URL}/back/{src_name}", PLATINUM_DIR / "back" / "deoxys" / f"{form}.png"))
        tasks.append((f"{BASE_URL}/back/shiny/{src_name}", PLATINUM_SHINY_DIR / "back" / "deoxys" / f"{form}.png"))

    # 9. Arceus (#493)
    for t in ARCEUS_TYPES:
        src_name = "493.png" if t == "normal" else f"493-{t}.png"
        tasks.append((f"{BASE_URL}/{src_name}", PLATINUM_DIR / "arceus" / f"{t}.png"))
        tasks.append((f"{BASE_URL}/shiny/{src_name}", PLATINUM_SHINY_DIR / "arceus" / f"{t}.png"))
        tasks.append((f"{BASE_URL}/back/{src_name}", PLATINUM_DIR / "back" / "arceus" / f"{t}.png"))
        tasks.append((f"{BASE_URL}/back/shiny/{src_name}", PLATINUM_SHINY_DIR / "back" / "arceus" / f"{t}.png"))

    # 10. Unown (#201)
    for letter in UNOWN_LETTERS:
        src_name = f"201-{letter}.png"
        tasks.append((f"{BASE_URL}/{src_name}", PLATINUM_DIR / "unown" / f"{letter}.png"))
        tasks.append((f"{BASE_URL}/shiny/{src_name}", PLATINUM_SHINY_DIR / "unown" / f"{letter}.png"))
        tasks.append((f"{BASE_URL}/back/{src_name}", PLATINUM_DIR / "back" / "unown" / f"{letter}.png"))
        tasks.append((f"{BASE_URL}/back/shiny/{src_name}", PLATINUM_SHINY_DIR / "back" / "unown" / f"{letter}.png"))

    # 11. Cherrim (#421)
    tasks.append((f"{BASE_URL}/421.png", PLATINUM_DIR / "cherrim" / "overcast.png"))
    tasks.append((f"{BASE_URL}/shiny/421.png", PLATINUM_SHINY_DIR / "cherrim" / "overcast.png"))
    tasks.append((f"{BASE_URL}/421-sunshine.png", PLATINUM_DIR / "cherrim" / "sunshine.png"))
    tasks.append((f"{BASE_URL}/shiny/421-sunshine.png", PLATINUM_SHINY_DIR / "cherrim" / "sunshine.png"))
    tasks.append((f"{BASE_URL}/back/421.png", PLATINUM_DIR / "back" / "cherrim" / "overcast.png"))
    tasks.append((f"{BASE_URL}/back/shiny/421.png", PLATINUM_SHINY_DIR / "back" / "cherrim" / "overcast.png"))
    tasks.append((f"{BASE_URL}/back/421-sunshine.png", PLATINUM_DIR / "back" / "cherrim" / "sunshine.png"))
    tasks.append((f"{BASE_URL}/back/shiny/421-sunshine.png", PLATINUM_SHINY_DIR / "back" / "cherrim" / "sunshine.png"))

    # 12. Castform (#351) formas climáticas para Platino Nacional (10013=sunny, 10014=rainy, 10015=snowy)
    castform_map = {
        "sunny": "10013.png",
        "rainy": "10014.png",
        "snowy": "10015.png",
    }
    for form, src_name in castform_map.items():
        tasks.append((f"{BASE_URL}/{src_name}", PLATINUM_DIR / "castform" / f"{form}.png"))
        tasks.append((f"{BASE_URL}/shiny/{src_name}", PLATINUM_SHINY_DIR / "castform" / f"{form}.png"))
        tasks.append((f"{BASE_URL}/back/{src_name}", PLATINUM_DIR / "back" / "castform" / f"{form}.png"))
        tasks.append((f"{BASE_URL}/back/shiny/{src_name}", PLATINUM_SHINY_DIR / "back" / "castform" / f"{form}.png"))

    return tasks


def main():
    print("Sincronizando paquete de sprites estáticos oficiales de Pokémon Platino...")
    tasks = build_tasks()

    # Filtrar solo las tareas que realmente falten por descargar
    pending = [(url, path) for url, path in tasks if not path.exists() or path.stat().st_size == 0]
    print(f"Total sprites a auditar: {len(tasks)} (Pendientes de descarga: {len(pending)})")

    if pending:
        with ThreadPoolExecutor(max_workers=16) as executor:
            futures = [executor.submit(download_single_sprite, url, path) for url, path in pending]
            for f in as_completed(futures):
                f.result()

    platinum_count = len(list(PLATINUM_DIR.rglob("*.png")))
    platinum_shiny_count = len(list(PLATINUM_SHINY_DIR.rglob("*.png")))
    print(f"\n[OK] Sprites de Pokémon Platino sincronizados:")
    print(f"  - {platinum_count} sprites en media/pokemon/sprites/platinum/")
    print(f"  - {platinum_shiny_count} sprites en media/pokemon/sprites/platinum_shiny/")


if __name__ == "__main__":
    main()
