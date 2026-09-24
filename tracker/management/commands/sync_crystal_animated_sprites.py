import os
import time
import urllib.request
import concurrent.futures
from pathlib import Path
from django.conf import settings
from django.core.management.base import BaseCommand
from django.core.cache import cache

USER_AGENT = "PokedexGlobal/1.0 (Educational/Collector Tool; https://github.com/Gatozo/pokedexglobal)"

BASE_NORMAL_URL = "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/versions/generation-ii/crystal/animated/{num}.gif"
BASE_SHINY_URL = "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/versions/generation-ii/crystal/animated/shiny/{num}.gif"


def download_single_gif(url: str, dest_path: Path, max_retries: int = 3) -> bool:
    """Descarga y valida un archivo GIF asegurando integridad de encabezado."""
    if dest_path.exists() and dest_path.stat().st_size > 0:
        return True

    for attempt in range(max_retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=15) as resp:
                if resp.status == 200:
                    data = resp.read()
                    if len(data) > 0 and (data.startswith(b"GIF87a") or data.startswith(b"GIF89a")):
                        temp_path = dest_path.with_suffix(".tmp")
                        with open(temp_path, "wb") as f:
                            f.write(data)
                        temp_path.replace(dest_path)
                        return True
        except Exception:
            if attempt < max_retries - 1:
                time.sleep(0.5 * (2 ** attempt))

    return False


class Command(BaseCommand):
    help = "Descarga y almacena localmente los sprites animados (normales y shiny) exclusivos de Pokémon Cristal."

    def add_arguments(self, parser):
        parser.add_argument("--start", type=int, default=1, help="Número nacional inicial (defecto: 1)")
        parser.add_argument("--end", type=int, default=251, help="Número nacional final (defecto: 251)")
        parser.add_argument("--force", action="store_true", help="Fuerza la descarga incluso si el archivo ya existe.")

    def handle(self, *args, **options):
        start_num = options["start"]
        end_num = options["end"]
        force = options["force"]

        normal_dir = Path(settings.MEDIA_ROOT) / "pokemon" / "sprites" / "crystal_animated"
        shiny_dir = Path(settings.MEDIA_ROOT) / "pokemon" / "sprites" / "crystal_animated_shiny"

        normal_dir.mkdir(parents=True, exist_ok=True)
        shiny_dir.mkdir(parents=True, exist_ok=True)

        if force:
            for d in [normal_dir, shiny_dir]:
                for f in d.glob("*.gif"):
                    f.unlink(missing_ok=True)

        tasks = []
        for num in range(start_num, end_num + 1):
            sprite_id = "201-f" if num == 201 else num
            tasks.append((BASE_NORMAL_URL.format(num=sprite_id), normal_dir / f"{num}.gif", f"#{num} normal"))
            tasks.append((BASE_SHINY_URL.format(num=sprite_id), shiny_dir / f"{num}.gif", f"#{num} shiny"))

        total_tasks = len(tasks)
        self.stdout.write(self.style.NOTICE(f"Iniciando descarga local de {total_tasks} sprites animados para Pokémon Cristal (#{start_num} a #{end_num})..."))

        success_count = 0
        failed_count = 0

        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
            future_to_label = {
                executor.submit(download_single_gif, url, path): label
                for url, path, label in tasks
            }

            completed = 0
            for future in concurrent.futures.as_completed(future_to_label):
                label = future_to_label[future]
                completed += 1
                try:
                    ok = future.result()
                    if ok:
                        success_count += 1
                    else:
                        failed_count += 1
                        self.stdout.write(self.style.WARNING(f"Fallo al descargar {label}"))
                except Exception as e:
                    failed_count += 1
                    self.stdout.write(self.style.ERROR(f"Error procesando {label}: {e}"))

                if completed % 50 == 0 or completed == total_tasks:
                    self.stdout.write(f"Progreso: {completed}/{total_tasks} descargas completadas...")

        cache.clear()

        self.stdout.write(self.style.SUCCESS(
            f"¡Completado! {success_count}/{total_tasks} sprites animados guardados en media/pokemon/sprites/crystal_animated/"
        ))
        if failed_count > 0:
            self.stdout.write(self.style.WARNING(f"Atención: {failed_count} descargas fallaron."))
