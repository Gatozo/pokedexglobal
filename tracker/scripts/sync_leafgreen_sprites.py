"""
Sincroniza y persiste localmente los sprites estáticos oficiales de Pokémon Verde Hoja
en media/pokemon/sprites/leafgreen/ y leafgreen_shiny/, incluyendo la forma canónica
de Deoxys Defensa (#386) propia de Verde Hoja.
"""
import shutil
import urllib.request
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
MEDIA_DIR = BASE_DIR / "media" / "pokemon" / "sprites"
FR_DIR = MEDIA_DIR / "firered"
FR_SHINY_DIR = MEDIA_DIR / "firered_shiny"
LG_DIR = MEDIA_DIR / "leafgreen"
LG_SHINY_DIR = MEDIA_DIR / "leafgreen_shiny"


def download_file(url: str, dest: Path):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 PokedexGlobal/1.0'})
    with urllib.request.urlopen(req, timeout=15) as resp:
        dest.write_bytes(resp.read())


def sync_sprites():
    print("Sincronizando sprites estáticos de Pokémon Verde Hoja...")
    LG_DIR.mkdir(parents=True, exist_ok=True)
    LG_SHINY_DIR.mkdir(parents=True, exist_ok=True)
    (LG_DIR / "back").mkdir(parents=True, exist_ok=True)
    (LG_SHINY_DIR / "back").mkdir(parents=True, exist_ok=True)

    # 1. Copiar base desde firered (sprites 1..385 idénticos en Gen 3 remakes)
    for src_file in FR_DIR.glob("*.png"):
        shutil.copy2(src_file, LG_DIR / src_file.name)
    for src_file in (FR_DIR / "back").glob("*.png"):
        shutil.copy2(src_file, LG_DIR / "back" / src_file.name)

    for src_file in FR_SHINY_DIR.glob("*.png"):
        shutil.copy2(src_file, LG_SHINY_DIR / src_file.name)
    for src_file in (FR_SHINY_DIR / "back").glob("*.png"):
        shutil.copy2(src_file, LG_SHINY_DIR / "back" / src_file.name)

    # 2. Descargar y asignar la variante canónica de Deoxys Defensa (10002) exclusiva de Verde Hoja
    print("Descargando sprite de Deoxys Forma Defensa (Verde Hoja)...")
    front_def_url = "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/versions/generation-iii/firered-leafgreen/10002.png"
    front_shiny_def_url = "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/versions/generation-iii/firered-leafgreen/shiny/10002.png"
    back_def_url = "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/versions/generation-iii/firered-leafgreen/back/10002.png"
    back_shiny_def_url = "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/versions/generation-iii/firered-leafgreen/back/shiny/10002.png"

    download_file(front_def_url, LG_DIR / "386.png")
    download_file(front_def_url, LG_DIR / "386-defense.png")
    download_file(front_shiny_def_url, LG_SHINY_DIR / "386.png")
    download_file(front_shiny_def_url, LG_SHINY_DIR / "386-defense.png")

    download_file(back_def_url, LG_DIR / "back" / "386.png")
    download_file(back_shiny_def_url, LG_SHINY_DIR / "back" / "386.png")

    print("[OK] Sprites de Verde Hoja sincronizados exitosamente:")
    print(f"  - {len(list(LG_DIR.glob('*.png')))} sprites frontales normales")
    print(f"  - {len(list(LG_SHINY_DIR.glob('*.png')))} sprites frontales shiny")


if __name__ == "__main__":
    sync_sprites()
