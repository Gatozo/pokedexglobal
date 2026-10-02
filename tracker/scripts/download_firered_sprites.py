"""
Descarga offline-first de los 386 sprites estáticos oficiales (normales y shiny)
de Pokémon Rojo Fuego / Verde Hoja en media/pokemon/sprites/firered/ y media/pokemon/sprites/firered_shiny/.
"""
import os
import urllib.request
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

BASE_DIR = Path(__file__).resolve().parent.parent.parent
MEDIA_DIR = BASE_DIR / "media" / "pokemon" / "sprites"
DIR_NORMAL = MEDIA_DIR / "firered"
DIR_SHINY = MEDIA_DIR / "firered_shiny"

DIR_NORMAL.mkdir(parents=True, exist_ok=True)
DIR_SHINY.mkdir(parents=True, exist_ok=True)

URL_BASE_NORMAL = "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/versions/generation-iii/firered-leafgreen/{nat_id}.png"
URL_BASE_SHINY = "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/versions/generation-iii/firered-leafgreen/shiny/{nat_id}.png"


def download_sprite(nat_id: int):
    # 1. Normal
    path_normal = DIR_NORMAL / f"{nat_id}.png"
    if not path_normal.exists() or path_normal.stat().st_size == 0:
        url_norm = URL_BASE_NORMAL.format(nat_id=nat_id)
        req = urllib.request.Request(url_norm, headers={"User-Agent": "Mozilla/5.0"})
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                content = resp.read()
                if resp.status == 200 and len(content) > 0:
                    with open(path_normal, "wb") as f:
                        f.write(content)
        except Exception as e:
            print(f"Error descargando normal #{nat_id}: {e}")

    # 2. Shiny
    path_shiny = DIR_SHINY / f"{nat_id}.png"
    if not path_shiny.exists() or path_shiny.stat().st_size == 0:
        url_shi = URL_BASE_SHINY.format(nat_id=nat_id)
        req = urllib.request.Request(url_shi, headers={"User-Agent": "Mozilla/5.0"})
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                content = resp.read()
                if resp.status == 200 and len(content) > 0:
                    with open(path_shiny, "wb") as f:
                        f.write(content)
        except Exception as e:
            print(f"Error descargando shiny #{nat_id}: {e}")


def main():
    print(f"Iniciando descarga de sprites oficiales de Pokémon Rojo Fuego (1..386)...")
    with ThreadPoolExecutor(max_workers=12) as executor:
        list(executor.map(download_sprite, range(1, 387)))

    # Verificación
    normal_count = len(list(DIR_NORMAL.glob("*.png")))
    shiny_count = len(list(DIR_SHINY.glob("*.png")))
    print(f"[OK] Normales descargados: {normal_count}/386 en {DIR_NORMAL}")
    print(f"[OK] Shinies descargados: {shiny_count}/386 en {DIR_SHINY}")


if __name__ == "__main__":
    main()
