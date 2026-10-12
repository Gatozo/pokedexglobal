"""
Sincronización masiva de Artworks Oficiales Full HD desde el repositorio oficial de PokeAPI.
Descarga y organiza:
- 1..1025.png (Artworks regulares base)
- 1..1025.png (Artworks shiny base) en media/pokemon/artwork/shiny/
- Todas las formas alternativas (>=10001.png y {id}-{forma}.png) regulares y shiny.
- Creación de alias y enlaces legibles ({especie}-{forma}.png) en regular y shiny.
"""
import os
import sys
import json
import time
import shutil
import urllib.request
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE_DIR = Path(__file__).resolve().parent.parent.parent
ARTWORK_DIR = BASE_DIR / "media" / "pokemon" / "artwork"
SHINY_DIR = ARTWORK_DIR / "shiny"

ARTWORK_DIR.mkdir(parents=True, exist_ok=True)
SHINY_DIR.mkdir(parents=True, exist_ok=True)

GITHUB_TREE_URL = "https://api.github.com/repos/PokeAPI/sprites/git/trees/master?recursive=1"
RAW_BASE_URL = "https://raw.githubusercontent.com/PokeAPI/sprites/master"

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) PokedexGlobal/1.0'}


def fetch_github_manifest():
    print("Obteniendo manifiesto de archivos desde PokeAPI GitHub...")
    req = urllib.request.Request(GITHUB_TREE_URL, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode('utf-8'))
    
    tree = data.get('tree', [])
    regular_files = []
    shiny_files = []

    for item in tree:
        if item.get('type') != 'blob':
            continue
        p = item['path']
        if not p.startswith('sprites/pokemon/other/official-artwork/') or not p.endswith('.png'):
            continue
        if 'versions/' in p:
            continue
        
        rel = p[len('sprites/pokemon/other/official-artwork/'):]
        if rel.startswith('shiny/'):
            shiny_filename = rel[len('shiny/'):]
            shiny_files.append((p, shiny_filename))
        else:
            regular_files.append((p, rel))

    print(f"Archivos oficiales encontrados en PokeAPI: Regulares={len(regular_files)}, Shinies={len(shiny_files)}")
    return regular_files, shiny_files


def download_file(args):
    git_path, dest_path = args
    if dest_path.exists() and dest_path.stat().st_size > 0:
        return True, "skipped"
    
    url = f"{RAW_BASE_URL}/{git_path}"
    req = urllib.request.Request(url, headers=HEADERS)
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                content = resp.read()
                if len(content) > 0:
                    dest_path.write_bytes(content)
                    return True, "downloaded"
        except Exception:
            time.sleep(0.5 * (attempt + 1))
    return False, "failed"


def run_download_pool(tasks, desc="archivos", max_workers=25):
    total = len(tasks)
    print(f"\nDescargando {total} {desc} con {max_workers} hilos...")
    downloaded = 0
    skipped = 0
    failed = []

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_map = {executor.submit(download_file, task): task for task in tasks}
        count = 0
        for future in as_completed(future_map):
            count += 1
            ok, status = future.result()
            if ok:
                if status == "downloaded":
                    downloaded += 1
                else:
                    skipped += 1
            else:
                task = future_map[future]
                failed.append(task)
            
            if count % 100 == 0 or count == total:
                print(f"Progreso: {count}/{total} (Nuevos: {downloaded}, Ya existentes: {skipped}, Errores: {len(failed)})")

    return downloaded, skipped, failed


def create_alias(source_path: Path, alias_path: Path):
    if not source_path.exists():
        return False
    if alias_path.exists():
        if alias_path.stat().st_size == source_path.stat().st_size:
            return True
        alias_path.unlink()
    try:
        os.link(str(source_path), str(alias_path))
        return True
    except Exception:
        shutil.copyfile(str(source_path), str(alias_path))
        return True


def setup_semantic_aliases():
    print("\nGenerando alias y enlaces legibles para formas ({especie}-{forma}.png)...")
    alias_configs = [
        # Arceus (#493)
        *[("arceus", f, f"493-{f}.png") for f in [
            'bug', 'dark', 'dragon', 'electric', 'fairy', 'fighting', 'fire',
            'flying', 'ghost', 'grass', 'ground', 'ice', 'poison', 'psychic',
            'rock', 'steel', 'water'
        ]],
        ("arceus", "normal", "493.png"),
        # Burmy (#412)
        ("burmy", "plant", "412.png"),
        ("burmy", "sandy", "412-sandy.png"),
        ("burmy", "trash", "412-trash.png"),
        # Wormadam (#413)
        ("wormadam", "plant", "413.png"),
        ("wormadam", "sandy", "10004.png"),
        ("wormadam", "trash", "10005.png"),
        # Cherrim (#421)
        ("cherrim", "overcast", "421.png"),
        ("cherrim", "sunshine", "421-sunshine.png"),
        # Shellos (#422)
        ("shellos", "west", "422.png"),
        ("shellos", "east", "422-east.png"),
        # Gastrodon (#423)
        ("gastrodon", "west", "423.png"),
        ("gastrodon", "east", "423-east.png"),
        # Deoxys (#386)
        ("deoxys", "normal", "386.png"),
        ("deoxys", "attack", "10001.png"),
        ("deoxys", "defense", "10002.png"),
        ("deoxys", "speed", "10003.png"),
        # Castform (#351)
        ("castform", "normal", "351.png"),
        ("castform", "sunny", "10013.png"),
        ("castform", "rainy", "10014.png"),
        ("castform", "snowy", "10015.png"),
    ]

    count_reg = 0
    count_shiny = 0

    for species, form_name, src_filename in alias_configs:
        alias_name = f"{species}-{form_name}.png"
        
        # Regular
        src_reg = ARTWORK_DIR / src_filename
        dst_reg = ARTWORK_DIR / alias_name
        if create_alias(src_reg, dst_reg):
            count_reg += 1
        
        # Shiny
        src_shiny = SHINY_DIR / src_filename
        dst_shiny = SHINY_DIR / alias_name
        if create_alias(src_shiny, dst_shiny):
            count_shiny += 1

    print(f"Alias generados con éxito: {count_reg} en regular, {count_shiny} en shiny.")


def main():
    reg_list, shiny_list = fetch_github_manifest()

    # Preparamos tareas regulares
    reg_tasks = [(git_path, ARTWORK_DIR / fname) for git_path, fname in reg_list]
    # Preparamos tareas shiny
    shiny_tasks = [(git_path, SHINY_DIR / fname) for git_path, fname in shiny_list]

    # Ejecutar descargas regulares
    reg_new, reg_skip, reg_fail = run_download_pool(reg_tasks, desc="artworks regulares")
    # Ejecutar descargas shiny
    shiny_new, shiny_skip, shiny_fail = run_download_pool(shiny_tasks, desc="artworks shiny")

    # Si hubo fallos, reintentar una ronda final
    if reg_fail or shiny_fail:
        print("\nReintentando archivos pendientes...")
        if reg_fail:
            run_download_pool(reg_fail, desc="reintentos regulares")
        if shiny_fail:
            run_download_pool(shiny_fail, desc="reintentos shiny")

    # Configurar alias semánticos legibles
    setup_semantic_aliases()

    print("\n" + "=" * 50)
    print("¡Sincronización y descarga completadas!")
    print(f"Total en media/pokemon/artwork/: {len(list(ARTWORK_DIR.glob('*.png')))} archivos")
    print(f"Total en media/pokemon/artwork/shiny/: {len(list(SHINY_DIR.glob('*.png')))} archivos")
    print("=" * 50)


if __name__ == "__main__":
    main()
