"""
Script para sincronizar y descargar localmente los sprites estáticos oficiales de Pokémon Oro HeartGold
en media/pokemon/sprites/heartgold/ y heartgold_shiny/ (1..493 front, front shiny, back, back shiny,
hembras, Pichu Picorejita, Unown y formas nativas: Rotom, Giratina Origen, Shaymin Cielo,
Burmy, Wormadam, Shellos, Gastrodon, Deoxys, Arceus, Castform, Cherrim).
Descarga directa desde PokeAPI GitHub Raw con verificación e idempotencia.
"""
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import time
from tracker.gender_differences import GENDER_DIFFERENCES_GEN4

BASE_DIR = Path(__file__).resolve().parent.parent.parent
MEDIA_DIR = BASE_DIR / "media" / "pokemon" / "sprites"
HG_DIR = MEDIA_DIR / "heartgold"
HG_SHINY_DIR = MEDIA_DIR / "heartgold_shiny"

HG_DIR.mkdir(parents=True, exist_ok=True)
HG_SHINY_DIR.mkdir(parents=True, exist_ok=True)

BASE_URL = "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/versions/generation-iv/heartgold-soulsilver"

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
        tasks.append((f"{BASE_URL}/{nat_id}.png", HG_DIR / f"{nat_id}.png"))
        tasks.append((f"{BASE_URL}/shiny/{nat_id}.png", HG_SHINY_DIR / f"{nat_id}.png"))
        tasks.append((f"{BASE_URL}/back/{nat_id}.png", HG_DIR / "back" / f"{nat_id}.png"))
        tasks.append((f"{BASE_URL}/back/shiny/{nat_id}.png", HG_SHINY_DIR / "back" / f"{nat_id}.png"))

    # 2. Diferencias de Género (Hembras normales y shinies, frontales y dorsales)
    for nat_id in GENDER_DIFFERENCES_GEN4.keys():
        tasks.append((f"{BASE_URL}/female/{nat_id}.png", HG_DIR / "female" / f"{nat_id}.png"))
        tasks.append((f"{BASE_URL}/shiny/female/{nat_id}.png", HG_SHINY_DIR / "female" / f"{nat_id}.png"))
        tasks.append((f"{BASE_URL}/back/female/{nat_id}.png", HG_DIR / "back" / "female" / f"{nat_id}.png"))
        tasks.append((f"{BASE_URL}/back/shiny/female/{nat_id}.png", HG_SHINY_DIR / "back" / "female" / f"{nat_id}.png"))

    # 3. Pichu Picorejita (#172, Spiky-Eared Pichu)
    tasks.append((f"{BASE_URL}/172-spiky-eared.png", HG_DIR / "172-spiky-eared.png"))
    tasks.append((f"{BASE_URL}/shiny/172-spiky-eared.png", HG_SHINY_DIR / "172-spiky-eared.png"))
    tasks.append((f"{BASE_URL}/back/172-spiky-eared.png", HG_DIR / "back" / "172-spiky-eared.png"))
    tasks.append((f"{BASE_URL}/back/shiny/172-spiky-eared.png", HG_SHINY_DIR / "back" / "172-spiky-eared.png"))

    # 4. Giratina Forma Origen (#487, ID 10007)
    tasks.append((f"{BASE_URL}/10007.png", HG_DIR / "giratina" / "origin.png"))
    tasks.append((f"{BASE_URL}/shiny/10007.png", HG_SHINY_DIR / "giratina" / "origin.png"))
    tasks.append((f"{BASE_URL}/back/10007.png", HG_DIR / "back" / "giratina" / "origin.png"))
    tasks.append((f"{BASE_URL}/back/shiny/10007.png", HG_SHINY_DIR / "back" / "giratina" / "origin.png"))

    # 5. Shaymin Forma Cielo (#492, ID 10006)
    tasks.append((f"{BASE_URL}/10006.png", HG_DIR / "shaymin" / "sky.png"))
    tasks.append((f"{BASE_URL}/shiny/10006.png", HG_SHINY_DIR / "shaymin" / "sky.png"))
    tasks.append((f"{BASE_URL}/back/10006.png", HG_DIR / "back" / "shaymin" / "sky.png"))
    tasks.append((f"{BASE_URL}/back/shiny/10006.png", HG_SHINY_DIR / "back" / "shaymin" / "sky.png"))

    # 6. Rotom Electrodomésticos (#479)
    for f_name, f_id in ROTOM_FORMS:
        tasks.append((f"{BASE_URL}/{f_id}.png", HG_DIR / "rotom" / f"{f_name}.png"))
        tasks.append((f"{BASE_URL}/shiny/{f_id}.png", HG_SHINY_DIR / "rotom" / f"{f_name}.png"))
        tasks.append((f"{BASE_URL}/back/{f_id}.png", HG_DIR / "back" / "rotom" / f"{f_name}.png"))
        tasks.append((f"{BASE_URL}/back/shiny/{f_id}.png", HG_SHINY_DIR / "back" / "rotom" / f"{f_name}.png"))

    # 7. Burmy (#412) y Wormadam (#413)
    burmy_map = {
        "plant": "412.png",
        "sandy": "412-trash.png",
        "trash": "412-sandy.png",
    }
    for form, src_name in burmy_map.items():
        tasks.append((f"{BASE_URL}/{src_name}", HG_DIR / "burmy" / f"{form}.png"))
        tasks.append((f"{BASE_URL}/shiny/{src_name}", HG_SHINY_DIR / "burmy" / f"{form}.png"))
        tasks.append((f"{BASE_URL}/back/{src_name}", HG_DIR / "back" / "burmy" / f"{form}.png"))
        tasks.append((f"{BASE_URL}/back/shiny/{src_name}", HG_SHINY_DIR / "back" / "burmy" / f"{form}.png"))

    wormadam_map = {
        "plant": "413.png",
        "sandy": "10004.png",
        "trash": "10005.png",
    }
    for form, src_name in wormadam_map.items():
        tasks.append((f"{BASE_URL}/{src_name}", HG_DIR / "wormadam" / f"{form}.png"))
        tasks.append((f"{BASE_URL}/shiny/{src_name}", HG_SHINY_DIR / "wormadam" / f"{form}.png"))
        tasks.append((f"{BASE_URL}/back/{src_name}", HG_DIR / "back" / "wormadam" / f"{form}.png"))
        tasks.append((f"{BASE_URL}/back/shiny/{src_name}", HG_SHINY_DIR / "back" / "wormadam" / f"{form}.png"))

    # 8. Shellos (#422) y Gastrodon (#423)
    sg_map = {
        "west": "422.png",
        "east": "10002.png"
    }
    for form, src_name in sg_map.items():
        tasks.append((f"{BASE_URL}/{src_name}", HG_DIR / "shellos" / f"{form}.png"))
        tasks.append((f"{BASE_URL}/shiny/{src_name}", HG_SHINY_DIR / "shellos" / f"{form}.png"))
        tasks.append((f"{BASE_URL}/back/{src_name}", HG_DIR / "back" / "shellos" / f"{form}.png"))
        tasks.append((f"{BASE_URL}/back/shiny/{src_name}", HG_SHINY_DIR / "back" / "shellos" / f"{form}.png"))

    gastro_map = {
        "west": "423.png",
        "east": "10003.png"
    }
    for form, src_name in gastro_map.items():
        tasks.append((f"{BASE_URL}/{src_name}", HG_DIR / "gastrodon" / f"{form}.png"))
        tasks.append((f"{BASE_URL}/shiny/{src_name}", HG_SHINY_DIR / "gastrodon" / f"{form}.png"))
        tasks.append((f"{BASE_URL}/back/{src_name}", HG_DIR / "back" / "gastrodon" / f"{form}.png"))
        tasks.append((f"{BASE_URL}/back/shiny/{src_name}", HG_SHINY_DIR / "back" / "gastrodon" / f"{form}.png"))

    # 9. Cherrim (#421)
    tasks.append((f"{BASE_URL}/421.png", HG_DIR / "cherrim" / "overcast.png"))
    tasks.append((f"{BASE_URL}/shiny/421.png", HG_SHINY_DIR / "cherrim" / "overcast.png"))
    tasks.append((f"{BASE_URL}/421-sunshine.png", HG_DIR / "cherrim" / "sunshine.png"))
    tasks.append((f"{BASE_URL}/shiny/421-sunshine.png", HG_SHINY_DIR / "cherrim" / "sunshine.png"))

    # 10. Deoxys (#386)
    deoxys_map = {
        "normal": "386.png",
        "attack": "10001.png",
        "defense": "10002.png",
        "speed": "10003.png"
    }
    for form, src_name in deoxys_map.items():
        tasks.append((f"{BASE_URL}/{src_name}", HG_DIR / "deoxys" / f"{form}.png"))
        tasks.append((f"{BASE_URL}/shiny/{src_name}", HG_SHINY_DIR / "deoxys" / f"{form}.png"))
        tasks.append((f"{BASE_URL}/back/{src_name}", HG_DIR / "back" / "deoxys" / f"{form}.png"))
        tasks.append((f"{BASE_URL}/back/shiny/{src_name}", HG_SHINY_DIR / "back" / "deoxys" / f"{form}.png"))

    # 11. Arceus (#493)
    arceus_id_map = {
        "normal": "493.png",
        "bug": "10013.png",
        "dark": "10014.png",
        "dragon": "10015.png",
        "electric": "10016.png",
        "fighting": "10017.png",
        "fire": "10018.png",
        "flying": "10019.png",
        "ghost": "10020.png",
        "grass": "10021.png",
        "ground": "10022.png",
        "ice": "10023.png",
        "poison": "10024.png",
        "psychic": "10025.png",
        "rock": "10026.png",
        "steel": "10027.png",
        "water": "10028.png",
    }
    for form, src_name in arceus_id_map.items():
        tasks.append((f"{BASE_URL}/{src_name}", HG_DIR / "arceus" / f"{form}.png"))
        tasks.append((f"{BASE_URL}/shiny/{src_name}", HG_SHINY_DIR / "arceus" / f"{form}.png"))
        tasks.append((f"{BASE_URL}/back/{src_name}", HG_DIR / "back" / "arceus" / f"{form}.png"))
        tasks.append((f"{BASE_URL}/back/shiny/{src_name}", HG_SHINY_DIR / "back" / "arceus" / f"{form}.png"))

    # 12. Castform (#351)
    castform_map = {
        "normal": "351.png",
        "sunny": "10013.png",
        "rainy": "10014.png",
        "snowy": "10015.png"
    }
    for form, src_name in castform_map.items():
        tasks.append((f"{BASE_URL}/{src_name}", HG_DIR / "castform" / f"{form}.png"))
        tasks.append((f"{BASE_URL}/shiny/{src_name}", HG_SHINY_DIR / "castform" / f"{form}.png"))
        tasks.append((f"{BASE_URL}/back/{src_name}", HG_DIR / "back" / "castform" / f"{form}.png"))
        tasks.append((f"{BASE_URL}/back/shiny/{src_name}", HG_SHINY_DIR / "back" / "castform" / f"{form}.png"))

    # 13. Unown (#201) (28 formas)
    for letter in UNOWN_LETTERS:
        src_name = "201.png" if letter == "a" else f"201-{letter}.png"
        tasks.append((f"{BASE_URL}/{src_name}", HG_DIR / "unown" / f"{letter}.png"))
        tasks.append((f"{BASE_URL}/shiny/{src_name}", HG_SHINY_DIR / "unown" / f"{letter}.png"))
        tasks.append((f"{BASE_URL}/back/{src_name}", HG_DIR / "back" / "unown" / f"{letter}.png"))
        tasks.append((f"{BASE_URL}/back/shiny/{src_name}", HG_SHINY_DIR / "back" / "unown" / f"{letter}.png"))

    return tasks


def main():
    print("Iniciando sincronización oficial de sprites estáticos de Pokémon Oro HeartGold...")
    tasks = build_tasks()
    print(f"Total de tareas de descarga calculadas: {len(tasks)}")

    pending = [(url, path) for url, path in tasks if not path.exists() or path.stat().st_size == 0]
    print(f"Sprites pendientes de descarga: {len(pending)} (los ya existentes se preservan)")

    if not pending:
        print("Todos los sprites estáticos de HeartGold ya se encuentran en disco.")
        return

    success_count = 0
    with ThreadPoolExecutor(max_workers=16) as executor:
        future_to_task = {executor.submit(download_single_sprite, url, path): (url, path) for url, path in pending}
        for future in as_completed(future_to_task):
            if future.result():
                success_count += 1

    print(f"Sincronización finalizada. Descargados con éxito: {success_count}/{len(pending)}")


if __name__ == "__main__":
    main()
