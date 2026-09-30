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


def generate_castform_animated_forms(normal_dir: Path, shiny_dir: Path, force: bool = False):
    """Genera y sincroniza los sprites animados (.gif) para las formas climáticas de Castform (#351)."""
    from PIL import Image

    coords = [
        (0, 0), (0, 0), (1, 0), (2, 0), (3, 0), (4, 0), (5, 0), (6, 0), (6, 0),
        (7, 0), (7, 0), (7, 0), (7, 0), (7, 1), (7, 1), (7, 1), (7, 2), (6, 2),
        (6, 2), (5, 2), (4, 2), (3, 2), (3, 1), (2, 1), (1, 1), (0, 0), (-1, 0),
        (-2, 0), (-3, 0), (-4, 0), (-5, 0), (-6, 0), (-7, 0), (-7, 0), (-8, 0),
        (-8, 0), (-8, 0), (-8, 0), (-8, 1), (-8, 1), (-8, 1), (-8, 2), (-7, 2),
        (-7, 2), (-6, 2), (-5, 2), (-4, 2), (-4, 1), (-3, 1), (-2, 1), (0, 0)
    ]
    durations = [80] + [20] * 49 + [2250]

    media_sprites = Path(settings.MEDIA_ROOT) / "pokemon" / "sprites"
    tasks = [
        (media_sprites / "emerald" / "castform" / "sunny.png", normal_dir / "castform" / "sunny.gif"),
        (media_sprites / "emerald" / "castform" / "rainy.png", normal_dir / "castform" / "rainy.gif"),
        (media_sprites / "emerald" / "castform" / "snowy.png", normal_dir / "castform" / "snowy.gif"),
        (media_sprites / "emerald_shiny" / "castform" / "sunny.png", shiny_dir / "castform" / "sunny.gif"),
        (media_sprites / "emerald_shiny" / "castform" / "rainy.png", shiny_dir / "castform" / "rainy.gif"),
        (media_sprites / "emerald_shiny" / "castform" / "snowy.png", shiny_dir / "castform" / "snowy.gif"),
    ]

    for src_png, dest_gif in tasks:
        if not force and dest_gif.exists() and dest_gif.stat().st_size > 0:
            continue
        if not src_png.exists():
            continue

        src = Image.open(src_png).convert("RGBA")
        colors = set()
        for pixel in list(src.getdata()):
            if pixel[3] > 0:
                colors.add(pixel[:3])

        palette = [0, 0, 0]
        color_to_idx = {}
        for i, c in enumerate(sorted(colors), start=1):
            palette.extend(c)
            color_to_idx[c] = i
        palette += [0] * (768 - len(palette))

        gif_frames = []
        for f_idx, (dx, dy) in enumerate(coords):
            canvas = Image.new("RGBA", (96, 96), (0, 0, 0, 0))
            canvas.paste(src, (16 + dx, 16 + dy), src)
            p_img = Image.new("P", (96, 96), 0)
            p_img.putpalette(palette)
            raw_pixels = list(canvas.getdata())
            p_data = bytearray(96 * 96)
            for idx, px in enumerate(raw_pixels):
                p_data[idx] = color_to_idx.get(px[:3], 1) if px[3] > 0 else 0
            p_img.frombytes(bytes(p_data))
            p_img.info["transparency"] = 0
            p_img.info["duration"] = durations[f_idx]
            gif_frames.append(p_img)

        dest_gif.parent.mkdir(parents=True, exist_ok=True)
        gif_frames[0].save(
            dest_gif,
            save_all=True,
            append_images=gif_frames[1:],
            duration=durations,
            loop=0,
            transparency=0,
            disposal=2
        )


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

        generate_castform_animated_forms(normal_dir, shiny_dir, force=force)

        cache.clear()
        self.stdout.write(self.style.SUCCESS(
            f"¡Completado! {success_count}/{total_tasks} sprites animados guardados en media/pokemon/sprites/emerald_animated/"
        ))
