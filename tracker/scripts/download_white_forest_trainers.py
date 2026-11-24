"""
Descarga idempotente de los 25 sprites Overworld de 5.ª Generación (32×32 px)
correspondientes a los 30 residentes del Bosque Blanco (Pokémon Blanco)
desde Bulbagarden Archives hacia media/entrenadores/gen5/.
"""
import json
import os
import time
import urllib.parse
import urllib.request
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
OUT_DIR = BASE_DIR / "media" / "entrenadores" / "gen5"

# Mapeo slug local -> nombre exacto en Bulbagarden Archives
TRAINER_SPRITES = {
    "school_kid_m": "File:School Kid m OD.png",
    "school_kid_f": "File:School Kid f OD.png",
    "scientist_m": "File:Scientist m OD.png",
    "scientist_f": "File:Scientist f OD.png",
    "veteran_m": "File:Veteran m OD.png",
    "veteran_f": "File:Veteran f OD.png",
    "lady": "File:Lady OD.png",
    "clerk_m": "File:Clerk m OD.png",
    "clerk_f": "File:Clerk f OD.png",
    "black_belt": "File:Black Belt OD.png",
    "roughneck": "File:Roughneck OD.png",
    "backpacker_m": "File:Backpacker m OD.png",
    "backpacker_f": "File:Backpacker f OD.png",
    "lass": "File:Lass OD.png",
    "rich_boy": "File:Rich Boy V OD.png",
    "youngster": "File:Youngster OD.png",
    "ace_trainer_m": "File:Ace Trainer m V OD.png",
    "ace_trainer_f": "File:Ace Trainer f V OD.png",
    "pokemon_ranger_m": "File:Pokemon Ranger m OD.png",
    "pokemon_ranger_f": "File:Pokemon Ranger f OD.png",
    "nursery_aide": "File:Nursery Aide OD.png",
    "battle_girl": "File:Battle Girl OD.png",
    "hiker": "File:Hiker OD.png",
    "socialite": "File:Socialite OD.png",
    "gentleman": "File:Gentleman OD.png",
}


def fetch_image_urls(titles):
    url = (
        "https://archives.bulbagarden.net/w/api.php"
        "?action=query&prop=imageinfo&iiprop=url&format=json&titles="
        + urllib.parse.quote("|".join(titles))
    )
    req = urllib.request.Request(url, headers={"User-Agent": "PokedexGlobalAssetSync/1.0"})
    with urllib.request.urlopen(req, timeout=20) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    by_title = {}
    for page in data["query"]["pages"].values():
        if "imageinfo" in page:
            by_title[page["title"]] = page["imageinfo"][0]["url"]
    return by_title


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    missing = {slug: title for slug, title in TRAINER_SPRITES.items() if not (OUT_DIR / f"{slug}.png").exists()}
    if not missing:
        print(f"[OK] Todos los {len(TRAINER_SPRITES)} sprites ya existen en {OUT_DIR}")
        return

    urls = fetch_image_urls(list(missing.values()))
    downloaded = 0
    for slug, title in missing.items():
        img_url = urls.get(title)
        if not img_url:
            print(f"[WARN] No se encontró URL para {slug} ({title})")
            continue
        dest = OUT_DIR / f"{slug}.png"
        req = urllib.request.Request(img_url, headers={"User-Agent": "PokedexGlobalAssetSync/1.0"})
        with urllib.request.urlopen(req, timeout=20) as resp:
            dest.write_bytes(resp.read())
        downloaded += 1
        print(f"[OK] {slug}.png <- {title}")
        time.sleep(0.1)

    print(f"Descargados {downloaded}/{len(missing)} sprites en {OUT_DIR}")


if __name__ == "__main__":
    main()
