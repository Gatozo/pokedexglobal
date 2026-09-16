import os
import concurrent.futures
from pathlib import Path
from typing import Dict, List, Tuple
import requests
from django.conf import settings
from django.core.management.base import BaseCommand

# URL base para los archivos crudos de PokeAPI
RAW_BASE_URL = "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/versions"
TREE_API_URL = "https://api.github.com/repos/PokeAPI/sprites/git/trees/5be89d86cd86f3c68cde016aa36eefcfebf33ca9?recursive=1"

# Mapeo de generaciones canónicas a carpetas amigables
GEN_FOLDER_MAP = {
    "generation-iii": "gen3",
    "generation-iv": "gen4",
    "generation-v": "gen5",
    "generation-vi": "gen6",
    "generation-vii": "gen7",
    "generation-viii": "gen8",
}


class Command(BaseCommand):
    help = "Descarga y organiza localmente en media/pokemon/icons/ todos los iconos de PC de todas las generaciones de Pokémon."

    def add_arguments(self, parser):
        parser.add_argument(
            '--workers',
            type=int,
            default=24,
            help='Número de hilos concurrentes para descarga (por defecto: 24)'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Fuerza la re-descarga de archivos incluso si ya existen localmente'
        )

    def download_file(self, session: requests.Session, url: str, target_path: Path, force: bool = False) -> bool:
        if target_path.exists() and not force and target_path.stat().st_size > 0:
            return False  # Ya existe

        try:
            resp = session.get(url, timeout=15)
            if resp.status_code == 200 and len(resp.content) > 0:
                target_path.parent.mkdir(parents=True, exist_ok=True)
                with open(target_path, "wb") as f:
                    f.write(resp.content)
                return True
        except Exception:
            pass
        return False

    def handle(self, *args, **options):
        workers = options['workers']
        force = options['force']

        icons_base_dir = Path(settings.MEDIA_ROOT) / "pokemon" / "icons"
        icons_base_dir.mkdir(parents=True, exist_ok=True)

        self.stdout.write("Consultando catálogo de iconos en PokeAPI...")
        try:
            tree_resp = requests.get(TREE_API_URL, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
            if tree_resp.status_code != 200:
                self.stderr.write(f"Error al obtener árbol de archivos: HTTP {tree_resp.status_code}")
                return
            tree_data = tree_resp.json()
        except Exception as e:
            self.stderr.write(f"Excepción al conectar con GitHub API: {e}")
            return

        icon_paths = [
            t['path'] for t in tree_data.get('tree', [])
            if 'icons' in t['path'] and t['path'].endswith('.png')
        ]

        self.stdout.write(f"Se encontraron {len(icon_paths)} iconos disponibles en total.")

        # Preparar cola de descargas
        tasks = []
        for rel_path in icon_paths:
            # rel_path tiene la forma: generation-iii/icons/1.png o generation-vii/icons/female/1.png
            parts = rel_path.split('/')
            gen_raw = parts[0]
            subpath = "/".join(parts[2:])  # elimina 'generation-xxx' y 'icons' -> ej '1.png' o 'female/1.png'
            friendly_gen = GEN_FOLDER_MAP.get(gen_raw, gen_raw)

            # Destino organizado en friendly_gen: media/pokemon/icons/gen3/1.png
            target_file = icons_base_dir / friendly_gen / subpath
            url = f"{RAW_BASE_URL}/{rel_path}"
            tasks.append((url, target_file))

        total_tasks = len(tasks)
        self.stdout.write(f"Iniciando descarga de {total_tasks} iconos con {workers} hilos...")

        downloaded_count = 0
        skipped_count = 0
        failed_count = 0

        with requests.Session() as session:
            adapter = requests.adapters.HTTPAdapter(pool_connections=workers, pool_maxsize=workers, max_retries=3)
            session.mount("https://", adapter)

            with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
                future_to_url = {
                    executor.submit(self.download_file, session, url, target_path, force): (url, target_path)
                    for url, target_path in tasks
                }

                done = 0
                for future in concurrent.futures.as_completed(future_to_url):
                    done += 1
                    if done % 500 == 0 or done == total_tasks:
                        self.stdout.write(f"Progreso: {done}/{total_tasks} procesados ({(done/total_tasks*100):.1f}%)...")

                    try:
                        result = future.result()
                        if result:
                            downloaded_count += 1
                        else:
                            skipped_count += 1
                    except Exception:
                        failed_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Descarga finalizada: {downloaded_count} descargados, {skipped_count} ya existentes, {failed_count} errores."
            )
        )

        # Generar carpetas de conveniencia gen1 y gen2 enlazadas/duplicadas de gen3 para compatibilidad retro total
        gen3_dir = icons_base_dir / "gen3"
        if gen3_dir.exists():
            for alias in ["gen1", "gen2"]:
                alias_dir = icons_base_dir / alias
                alias_dir.mkdir(parents=True, exist_ok=True)
                for f in gen3_dir.glob("*.png"):
                    alias_file = alias_dir / f.name
                    if not alias_file.exists():
                        try:
                            alias_file.write_bytes(f.read_bytes())
                        except Exception:
                            pass
            self.stdout.write(self.style.SUCCESS("Carpetas de conveniencia retro 'gen1' y 'gen2' sincronizadas con éxito."))
