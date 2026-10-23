"""
Script para sincronizar y descargar localmente los sprites oficiales de Pokémon Perla
en media/pokemon/sprites/pearl/ y pearl_shiny/ (1..493 front, front shiny, back, back shiny,
hembras, Unown y formas de Sinnoh).
Aplica la política Offline-First de PokedexGlobal reutilizando los assets consolidados de D/P.
"""
import shutil
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import time

BASE_DIR = Path(__file__).resolve().parent.parent.parent
MEDIA_DIR = BASE_DIR / "media" / "pokemon" / "sprites"
DIAMOND_DIR = MEDIA_DIR / "diamond"
DIAMOND_SHINY_DIR = MEDIA_DIR / "diamond_shiny"
PEARL_DIR = MEDIA_DIR / "pearl"
PEARL_SHINY_DIR = MEDIA_DIR / "pearl_shiny"

BASE_URL = "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/versions/generation-iv/diamond-pearl"


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
            time.sleep(0.5)
    return False


def copy_or_sync_sprites(src_dir: Path, dst_dir: Path):
    dst_dir.mkdir(parents=True, exist_ok=True)
    if src_dir.exists():
        for src_file in src_dir.rglob("*.png"):
            rel_path = src_file.relative_to(src_dir)
            target = dst_dir / rel_path
            if not target.exists() or target.stat().st_size == 0:
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src_file, target)


def main():
    print("Sincronizando paquete de sprites oficiales de Pokémon Perla...")

    # 1. Copia local offline-first desde el paquete consolidado de D/P
    if DIAMOND_DIR.exists():
        print("Sincronizando sprites normales desde la base canónica D/P...")
        copy_or_sync_sprites(DIAMOND_DIR, PEARL_DIR)
    if DIAMOND_SHINY_DIR.exists():
        print("Sincronizando sprites shinies desde la base canónica D/P...")
        copy_or_sync_sprites(DIAMOND_SHINY_DIR, PEARL_SHINY_DIR)

    # 2. Descarga de seguridad en caso de archivos faltantes (1..493)
    missing_tasks = []
    for nat_id in range(1, 494):
        p_front = PEARL_DIR / f"{nat_id}.png"
        if not p_front.exists() or p_front.stat().st_size == 0:
            missing_tasks.append((f"{BASE_URL}/{nat_id}.png", p_front))

        p_front_shiny = PEARL_SHINY_DIR / f"{nat_id}.png"
        if not p_front_shiny.exists() or p_front_shiny.stat().st_size == 0:
            missing_tasks.append((f"{BASE_URL}/shiny/{nat_id}.png", p_front_shiny))

        p_back = PEARL_DIR / "back" / f"{nat_id}.png"
        if not p_back.exists() or p_back.stat().st_size == 0:
            missing_tasks.append((f"{BASE_URL}/back/{nat_id}.png", p_back))

        p_back_shiny = PEARL_SHINY_DIR / "back" / f"{nat_id}.png"
        if not p_back_shiny.exists() or p_back_shiny.stat().st_size == 0:
            missing_tasks.append((f"{BASE_URL}/back/shiny/{nat_id}.png", p_back_shiny))

    if missing_tasks:
        print(f"Descargando {len(missing_tasks)} sprites faltantes desde PokeAPI...")
        with ThreadPoolExecutor(max_workers=12) as executor:
            futures = [executor.submit(download_single_sprite, url, path) for url, path in missing_tasks]
            for f in as_completed(futures):
                f.result()

    pearl_count = len(list(PEARL_DIR.rglob("*.png")))
    pearl_shiny_count = len(list(PEARL_SHINY_DIR.rglob("*.png")))
    print(f"\n[OK] Sprites de Pokémon Perla listos:")
    print(f"  - {pearl_count} sprites totales en media/pokemon/sprites/pearl/")
    print(f"  - {pearl_shiny_count} sprites totales en media/pokemon/sprites/pearl_shiny/")


if __name__ == "__main__":
    main()
