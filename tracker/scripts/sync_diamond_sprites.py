"""
Script para descargar y sincronizar localmente los sprites oficiales de Pokémon Diamante
en media/pokemon/sprites/diamond/ y diamond_shiny/ (1..493 front, front shiny, back, back shiny).
"""
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import time

BASE_DIR = Path(__file__).resolve().parent.parent.parent
MEDIA_DIR = BASE_DIR / "media" / "pokemon" / "sprites"
DIAMOND_DIR = MEDIA_DIR / "diamond"
DIAMOND_SHINY_DIR = MEDIA_DIR / "diamond_shiny"

DIAMOND_DIR.mkdir(parents=True, exist_ok=True)
DIAMOND_SHINY_DIR.mkdir(parents=True, exist_ok=True)
(DIAMOND_DIR / "back").mkdir(parents=True, exist_ok=True)
(DIAMOND_SHINY_DIR / "back").mkdir(parents=True, exist_ok=True)

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
                dest_path.write_bytes(content)
                return True
        except Exception:
            time.sleep(0.5)
    return False


def download_pokemon_sprites(nat_id: int):
    # 1. Front normal
    url_front = f"{BASE_URL}/{nat_id}.png"
    p_front = DIAMOND_DIR / f"{nat_id}.png"
    download_single_sprite(url_front, p_front)

    # 2. Front shiny
    url_front_shiny = f"{BASE_URL}/shiny/{nat_id}.png"
    p_front_shiny = DIAMOND_SHINY_DIR / f"{nat_id}.png"
    download_single_sprite(url_front_shiny, p_front_shiny)

    # 3. Back normal
    url_back = f"{BASE_URL}/back/{nat_id}.png"
    p_back = DIAMOND_DIR / "back" / f"{nat_id}.png"
    download_single_sprite(url_back, p_back)

    # 4. Back shiny
    url_back_shiny = f"{BASE_URL}/back/shiny/{nat_id}.png"
    p_back_shiny = DIAMOND_SHINY_DIR / "back" / f"{nat_id}.png"
    download_single_sprite(url_back_shiny, p_back_shiny)

    return nat_id


def sync_diamond_unown():
    unown_dir = DIAMOND_DIR / "unown"
    unown_shiny_dir = DIAMOND_SHINY_DIR / "unown"
    unown_back_dir = DIAMOND_DIR / "back" / "unown"
    unown_shiny_back_dir = DIAMOND_SHINY_DIR / "back" / "unown"

    for d in [unown_dir, unown_shiny_dir, unown_back_dir, unown_shiny_back_dir]:
        d.mkdir(parents=True, exist_ok=True)

    letters = [chr(c) for c in range(ord('a'), ord('z') + 1)] + ['exclamation', 'question']
    print(f"Sincronizando 28 formas de Unown para Diamante...")

    def download_unown_letter(letter):
        download_single_sprite(f"{BASE_URL}/201-{letter}.png", unown_dir / f"{letter}.png")
        download_single_sprite(f"{BASE_URL}/shiny/201-{letter}.png", unown_shiny_dir / f"{letter}.png")
        download_single_sprite(f"{BASE_URL}/back/201-{letter}.png", unown_back_dir / f"{letter}.png")
        download_single_sprite(f"{BASE_URL}/back/shiny/201-{letter}.png", unown_shiny_back_dir / f"{letter}.png")
        return letter

    with ThreadPoolExecutor(max_workers=8) as executor:
        list(executor.map(download_unown_letter, letters))

    # Forma F como sprite canónico principal de Unown (201.png) en Sinnoh
    if (unown_dir / "f.png").exists():
        (DIAMOND_DIR / "201.png").write_bytes((unown_dir / "f.png").read_bytes())
        (DIAMOND_SHINY_DIR / "201.png").write_bytes((unown_shiny_dir / "f.png").read_bytes())
        (DIAMOND_DIR / "back" / "201.png").write_bytes((unown_back_dir / "f.png").read_bytes())
        (DIAMOND_SHINY_DIR / "back" / "201.png").write_bytes((unown_shiny_back_dir / "f.png").read_bytes())

    # Icono oficial de Gen 4
    gen4_icon_f = BASE_DIR / "media" / "pokemon" / "icons" / "gen4" / "201-f.png"
    gen4_icon_main = BASE_DIR / "media" / "pokemon" / "icons" / "gen4" / "201.png"
    if gen4_icon_f.exists():
        gen4_icon_main.write_bytes(gen4_f_bytes := gen4_icon_f.read_bytes())


def main():
    print("Sincronizando 1..493 sprites oficiales de Pokémon Diamante...")
    with ThreadPoolExecutor(max_workers=16) as executor:
        futures = {executor.submit(download_pokemon_sprites, i): i for i in range(1, 494)}
        for future in as_completed(futures):
            future.result()

    sync_diamond_unown()

    front_count = len(list(DIAMOND_DIR.glob("*.png")))
    shiny_count = len(list(DIAMOND_SHINY_DIR.glob("*.png")))
    print(f"\n[OK] Sprites de Pokémon Diamante listos:")
    print(f"  - {front_count} frontales en media/pokemon/sprites/diamond/")
    print(f"  - {shiny_count} frontales shiny en media/pokemon/sprites/diamond_shiny/")


if __name__ == "__main__":
    main()
