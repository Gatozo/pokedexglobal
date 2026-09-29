"""
Script para descargar, asegurar transparencia desde los bordes y centrar
todos los sprites de espalda (back sprites) desde la 1ª Generación (Rojo/Azul/Amarillo)
hasta la 3ª Generación (Rubí y Rubí Shiny), incluyendo formas alternas (Castform y Unown).
"""
import os
import io
import urllib.request
from collections import deque
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from PIL import Image

BASE_DIR = Path(__file__).resolve().parent.parent.parent
MEDIA_SPRITES = BASE_DIR / "media" / "pokemon" / "sprites"
POKEAPI_BASE = "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon"

def make_border_transparent(im: Image.Image) -> Image.Image:
    """Aplica flood-fill desde los bordes exteriores si el fondo es blanco o cuasi-blanco."""
    im = im.convert("RGBA")
    w, h = im.size
    pixels = im.load()
    visited = set()
    queue = deque()

    # Comprobar los 4 bordes exteriores
    for x in range(w):
        for y in [0, h - 1]:
            r, g, b, a = pixels[x, y]
            if a > 0 and r > 235 and g > 235 and b > 235 and (x, y) not in visited:
                queue.append((x, y))
                visited.add((x, y))

    for y in range(h):
        for x in [0, w - 1]:
            r, g, b, a = pixels[x, y]
            if a > 0 and r > 235 and g > 235 and b > 235 and (x, y) not in visited:
                queue.append((x, y))
                visited.add((x, y))

    while queue:
        cx, cy = queue.popleft()
        pixels[cx, cy] = (0, 0, 0, 0)
        for nx, ny in [(cx + 1, cy), (cx - 1, cy), (cx, cy + 1), (cx, cy - 1)]:
            if 0 <= nx < w and 0 <= ny < h and (nx, ny) not in visited:
                nr, ng, nb, na = pixels[nx, ny]
                if na > 0 and nr > 235 and ng > 235 and nb > 235:
                    visited.add((nx, ny))
                    queue.append((nx, ny))
    return im

def center_sprite(im: Image.Image) -> Image.Image:
    """Centra el dibujo visible dentro de su lienzo respetando el tamaño original."""
    bbox = im.getbbox()
    if not bbox:
        return im
    top = bbox[1]
    bot = im.size[1] - bbox[3]
    left = bbox[0]
    right = im.size[0] - bbox[2]
    # Si está desalineado por más de 2px
    if abs(top - bot) > 2 or abs(left - right) > 2:
        crop = im.crop(bbox)
        cw, ch = crop.size
        w, h = im.size
        tx = (w - cw) // 2
        ty = (h - ch) // 2
        new_im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        new_im.paste(crop, (tx, ty))
        return new_im
    return im

def download_and_process(task):
    url, dest_path = task
    dest_path = Path(dest_path)
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = resp.read()
            im = Image.open(io.BytesIO(data))
            im = make_border_transparent(im)
            im = center_sprite(im)
            im.save(dest_path, format="PNG")
            return dest_path.name, True, None
    except Exception as e:
        return dest_path.name, False, str(e)

def build_download_tasks():
    tasks = []

    # 1. Gen 1: Red (1..151), Blue (1..151), Yellow (1..151)
    for i in range(1, 152):
        tasks.append((
            f"{POKEAPI_BASE}/versions/generation-i/red-blue/back/{i}.png",
            MEDIA_SPRITES / "red" / "back" / f"{i}.png"
        ))
        tasks.append((
            f"{POKEAPI_BASE}/versions/generation-i/red-blue/back/{i}.png",
            MEDIA_SPRITES / "blue" / "back" / f"{i}.png"
        ))
        tasks.append((
            f"{POKEAPI_BASE}/versions/generation-i/yellow/back/{i}.png",
            MEDIA_SPRITES / "yellow" / "back" / f"{i}.png"
        ))

    # 2. Gen 2: Gold, Silver, Crystal (1..251) normal & shiny
    gen2_games = [
        ("gold", "generation-ii/gold/transparent"),
        ("silver", "generation-ii/silver/transparent"),
        ("crystal", "generation-ii/crystal/transparent"),
    ]
    for game_slug, pokeapi_folder in gen2_games:
        for i in range(1, 252):
            tasks.append((
                f"{POKEAPI_BASE}/versions/{pokeapi_folder}/back/{i}.png",
                MEDIA_SPRITES / game_slug / "back" / f"{i}.png"
            ))
            tasks.append((
                f"{POKEAPI_BASE}/versions/{pokeapi_folder}/back/shiny/{i}.png",
                MEDIA_SPRITES / f"{game_slug}_shiny" / "back" / f"{i}.png"
            ))

    # 3. Gen 3: Ruby (1..386) normal & shiny
    for i in range(1, 387):
        tasks.append((
            f"{POKEAPI_BASE}/versions/generation-iii/ruby-sapphire/back/{i}.png",
            MEDIA_SPRITES / "ruby" / "back" / f"{i}.png"
        ))
        tasks.append((
            f"{POKEAPI_BASE}/versions/generation-iii/ruby-sapphire/back/shiny/{i}.png",
            MEDIA_SPRITES / "ruby_shiny" / "back" / f"{i}.png"
        ))

    # 4. Formas: Castform (Rubí)
    castform_forms = {
        "sunny": 10013,
        "rainy": 10014,
        "snowy": 10015,
    }
    for form_key, form_id in castform_forms.items():
        tasks.append((
            f"{POKEAPI_BASE}/versions/generation-iii/ruby-sapphire/back/{form_id}.png",
            MEDIA_SPRITES / "ruby" / "back" / "castform" / f"{form_key}.png"
        ))
        tasks.append((
            f"{POKEAPI_BASE}/versions/generation-iii/ruby-sapphire/back/shiny/{form_id}.png",
            MEDIA_SPRITES / "ruby_shiny" / "back" / "castform" / f"{form_key}.png"
        ))

    # 5. Formas: Unown (Gen 2 y Gen 3)
    letters = [chr(c) for c in range(ord('a'), ord('z') + 1)]
    for game_slug, pokeapi_folder in gen2_games:
        for l in letters:
            poke_file = f"201-{l}.png" if l != 'a' else "201.png"
            tasks.append((
                f"{POKEAPI_BASE}/versions/{pokeapi_folder}/back/{poke_file}",
                MEDIA_SPRITES / game_slug / "back" / "unown" / f"{l}.png"
            ))
            tasks.append((
                f"{POKEAPI_BASE}/versions/{pokeapi_folder}/back/shiny/{poke_file}",
                MEDIA_SPRITES / f"{game_slug}_shiny" / "back" / "unown" / f"{l}.png"
            ))

    # Gen 3 Unown (a..z, exclamation, question)
    ruby_unown_keys = letters + ["exclamation", "question"]
    for k in ruby_unown_keys:
        poke_file = f"201-{k}.png" if k != 'a' else "201.png"
        tasks.append((
            f"{POKEAPI_BASE}/versions/generation-iii/ruby-sapphire/back/{poke_file}",
            MEDIA_SPRITES / "ruby" / "back" / "unown" / f"{k}.png"
        ))
        tasks.append((
            f"{POKEAPI_BASE}/versions/generation-iii/ruby-sapphire/back/shiny/{poke_file}",
            MEDIA_SPRITES / "ruby_shiny" / "back" / "unown" / f"{k}.png"
        ))

    return tasks

def main():
    tasks = build_download_tasks()
    print(f"Total de tareas de descarga preparadas: {len(tasks)}")
    
    success_count = 0
    errors = []
    
    with ThreadPoolExecutor(max_workers=25) as executor:
        for name, ok, err in executor.map(download_and_process, tasks):
            if ok:
                success_count += 1
            else:
                errors.append((name, err))

    print(f"Descargas exitosas: {success_count}/{len(tasks)}")
    if errors:
        print(f"Errores encontrados ({len(errors)}):")
        for name, err in errors[:10]:
            print(f"  {name}: {err}")

if __name__ == "__main__":
    main()
