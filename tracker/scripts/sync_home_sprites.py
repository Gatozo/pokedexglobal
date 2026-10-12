"""
Script de sincronización masiva para descargar el catálogo completo de
sprites oficiales de Pokémon HOME (ultra alta definición) desde PokéAPI:
- Especies 1 a 1025 (normal y shiny)
- Formas alternas 10001 a 10275 (normal y shiny)
- Formas de Unown (201-a a 201-z, 201-exclamation, 201-question)
- Formas de Arceus por tipo (493-fire, 493-water, etc.)
- Diferencias de género (103 hembras normales y shiny)
- Creación de alias/hardlinks NTFS legibles para formas.
"""

import sys
import os
import urllib.request
import urllib.error
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR))
HOME_DIR = BASE_DIR / "media" / "pokemon" / "home"
HOME_SHINY_DIR = HOME_DIR / "shiny"
HOME_FEMALE_DIR = HOME_DIR / "female"
HOME_SHINY_FEMALE_DIR = HOME_SHINY_DIR / "female"

BASE_URL = "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/home"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}


def download_file(url: str, dest_path: Path, max_retries: int = 3) -> bool:
    if dest_path.exists() and dest_path.stat().st_size > 0:
        return True

    temp_path = dest_path.with_suffix(".tmp")
    for attempt in range(max_retries):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = resp.read()
                if len(data) > 0:
                    dest_path.parent.mkdir(parents=True, exist_ok=True)
                    temp_path.write_bytes(data)
                    temp_path.replace(dest_path)
                    return True
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return False
            time.sleep(1.0)
        except Exception:
            time.sleep(1.0)
        finally:
            if temp_path.exists():
                try:
                    temp_path.unlink()
                except Exception:
                    pass
    return False


def create_alias(target_path: Path, alias_path: Path):
    if not target_path.exists():
        return
    if alias_path.exists():
        return
    try:
        os.link(str(target_path), str(alias_path))
    except Exception:
        try:
            alias_path.write_bytes(target_path.read_bytes())
        except Exception:
            pass


def sync_home_catalog():
    for d in [HOME_DIR, HOME_SHINY_DIR, HOME_FEMALE_DIR, HOME_SHINY_FEMALE_DIR]:
        d.mkdir(parents=True, exist_ok=True)

    tasks = []

    # 1. Base 1..1025 normales y shiny
    for nat_id in range(1, 1026):
        tasks.append((f"{BASE_URL}/{nat_id}.png", HOME_DIR / f"{nat_id}.png"))
        tasks.append((f"{BASE_URL}/shiny/{nat_id}.png", HOME_SHINY_DIR / f"{nat_id}.png"))

    # 2. Formas 10001..10275 normales y shiny
    for form_id in range(10001, 10276):
        tasks.append((f"{BASE_URL}/{form_id}.png", HOME_DIR / f"{form_id}.png"))
        tasks.append((f"{BASE_URL}/shiny/{form_id}.png", HOME_SHINY_DIR / f"{form_id}.png"))

    # 3. Formas de Unown
    letters = [chr(c) for c in range(ord('a'), ord('z') + 1)] + ['exclamation', 'question']
    for l in letters:
        tasks.append((f"{BASE_URL}/201-{l}.png", HOME_DIR / f"201-{l}.png"))
        tasks.append((f"{BASE_URL}/shiny/201-{l}.png", HOME_SHINY_DIR / f"201-{l}.png"))

    # 4. Formas de Arceus por tipo
    arceus_types = [
        "bug", "dark", "dragon", "electric", "fairy", "fighting", "fire",
        "flying", "ghost", "grass", "ground", "ice", "poison", "psychic",
        "rock", "steel", "unknown", "water"
    ]
    for t in arceus_types:
        tasks.append((f"{BASE_URL}/493-{t}.png", HOME_DIR / f"493-{t}.png"))
        tasks.append((f"{BASE_URL}/shiny/493-{t}.png", HOME_SHINY_DIR / f"493-{t}.png"))

    # 5. Especies con diferencias de género (103 hembras registradas en PokéAPI)
    from tracker.gender_differences import GENDER_DIFFERENCES_GEN4
    for nat_id in range(1, 1026):
        if nat_id in GENDER_DIFFERENCES_GEN4:
            tasks.append((f"{BASE_URL}/female/{nat_id}.png", HOME_FEMALE_DIR / f"{nat_id}.png"))
            tasks.append((f"{BASE_URL}/shiny/female/{nat_id}.png", HOME_SHINY_FEMALE_DIR / f"{nat_id}.png"))

    print(f"Iniciando descarga de {len(tasks)} imágenes de Pokémon HOME...")
    downloaded = 0
    with ThreadPoolExecutor(max_workers=16) as executor:
        futures = {executor.submit(download_file, url, path): (url, path) for url, path in tasks}
        for future in as_completed(futures):
            res = future.result()
            if res:
                downloaded += 1

    print(f"[OK] Descargas finalizadas. {downloaded} imágenes listas en {HOME_DIR}")
    print("[OK] Sincronización oficial de Pokémon HOME completada.")


if __name__ == "__main__":
    sync_home_catalog()
