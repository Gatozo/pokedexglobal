import os
import time
import urllib.request
import concurrent.futures
from pathlib import Path
from django.conf import settings
from django.core.management.base import BaseCommand
from django.core.cache import cache

USER_AGENT = "PokedexGlobal/1.0 (Educational/Collector Tool; https://github.com/Gatozo/pokedexglobal)"

BASE_NORMAL_URL = "https://veekun.com/dex/media/pokemon/main-sprites/emerald/animated/{slug}.gif"
BASE_SHINY_URL = "https://veekun.com/dex/media/pokemon/main-sprites/emerald/animated/shiny/{slug}.gif"


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
    help = "Descarga y almacena localmente los sprites animados (normales y shiny) de Pokémon Esmeralda (1-386)."

    def add_arguments(self, parser):
        parser.add_argument("--start", type=int, default=1, help="Número nacional inicial (defecto: 1)")
        parser.add_argument("--end", type=int, default=386, help="Número nacional final (defecto: 386)")
        parser.add_argument("--force", action="store_true", help="Fuerza la descarga incluso si el archivo ya existe.")

    def handle(self, *args, **options):
        start_num = options["start"]
        end_num = options["end"]
        force = options["force"]

        normal_dir = Path(settings.MEDIA_ROOT) / "pokemon" / "sprites" / "emerald_animated"
        shiny_dir = Path(settings.MEDIA_ROOT) / "pokemon" / "sprites" / "emerald_animated_shiny"

        normal_dir.mkdir(parents=True, exist_ok=True)
        shiny_dir.mkdir(parents=True, exist_ok=True)

        if force:
            for d in [normal_dir, shiny_dir]:
                for f in d.glob("*.gif"):
                    f.unlink(missing_ok=True)

        tasks = []
        for num in range(start_num, end_num + 1):
            if num == 201:
                sprite_slug = "201-f"  # Forma F canónica de Esmeralda o 201-a
            elif num == 386:
                sprite_slug = "386-speed"  # Forma Velocidad canónica de Esmeralda
            else:
                sprite_slug = str(num)

            tasks.append((BASE_NORMAL_URL.format(slug=sprite_slug), normal_dir / f"{num}.gif", f"#{num} normal"))
            tasks.append((BASE_SHINY_URL.format(slug=sprite_slug), shiny_dir / f"{num}.gif", f"#{num} shiny"))

        total_tasks = len(tasks)
        self.stdout.write(self.style.NOTICE(f"Iniciando descarga local de {total_tasks} sprites animados para Pokémon Esmeralda (#{start_num} a #{end_num})..."))

        success_count = 0
        failed_count = 0

        with concurrent.futures.ThreadPoolExecutor(max_workers=16) as executor:
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
            f"¡Completado! {success_count}/{total_tasks} sprites animados guardados en media/pokemon/sprites/emerald_animated/"
        ))
