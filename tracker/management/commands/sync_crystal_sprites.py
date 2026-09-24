import io
import shutil
from pathlib import Path
import concurrent.futures
import requests
from PIL import Image
from django.conf import settings
from django.core.management.base import BaseCommand


def process_image_transparency(im: Image.Image) -> Image.Image:
    """
    Aplica flood-fill BFS desde los bordes para hacer transparente el fondo blanco exterior
    sin alterar los detalles blancos internos del Pokémon (ojos, colmillos, brillos).
    """
    im = im.convert('RGBA')
    w, h = im.size
    pixels = im.load()

    visited = set()
    queue = []

    # Bordes exteriores
    for x in range(w):
        if pixels[x, 0][:3] == (255, 255, 255) and pixels[x, 0][3] > 0:
            queue.append((x, 0))
        if pixels[x, h - 1][:3] == (255, 255, 255) and pixels[x, h - 1][3] > 0:
            queue.append((x, h - 1))

    for y in range(h):
        if pixels[0, y][:3] == (255, 255, 255) and pixels[0, y][3] > 0:
            queue.append((0, y))
        if pixels[w - 1, y][:3] == (255, 255, 255) and pixels[w - 1, y][3] > 0:
            queue.append((w - 1, y))

    while queue:
        x, y = queue.pop(0)
        if (x, y) in visited:
            continue
        visited.add((x, y))
        pixels[x, y] = (255, 255, 255, 0)

        for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if 0 <= nx < w and 0 <= ny < h and (nx, ny) not in visited:
                if pixels[nx, ny][:3] == (255, 255, 255) and pixels[nx, ny][3] > 0:
                    queue.append((nx, ny))

    return im


def ensure_transparency(im: Image.Image) -> Image.Image:
    """
    Solo aplica flood-fill BFS si la imagen no tiene canal alfa transparente en los bordes.
    Si ya tiene transparencia exterior nativa, evita procesamiento redundante.
    """
    im = im.convert('RGBA')
    w, h = im.size
    pixels = im.load()

    # Comprobar esquinas: si ya son transparentes (alpha == 0), ya viene con transparencia nativa
    corners = [(0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1)]
    if all(pixels[cx, cy][3] == 0 for cx, cy in corners):
        return im

    # Si alguna esquina o borde es blanco opaco, solo entonces aplicamos flood-fill BFS
    has_opaque_white_border = any(
        pixels[cx, cy][:3] == (255, 255, 255) and pixels[cx, cy][3] > 0 
        for cx, cy in corners
    )
    if not has_opaque_white_border:
        return im

    return process_image_transparency(im)


def align_on_56x56(im: Image.Image, ref_im: Image.Image = None) -> Image.Image:
    """
    Garantiza que la imagen esté en un lienzo transparente de 56x56 y alineada
    con respecto a la imagen de referencia (normal).
    """
    im = ensure_transparency(im)
    s_bbox = im.split()[3].getbbox()

    canvas = Image.new('RGBA', (56, 56), (0, 0, 0, 0))
    if not s_bbox:
        return canvas

    if ref_im is not None:
        ref_im = ref_im.convert('RGBA')
        r_bbox = ref_im.split()[3].getbbox()
        if r_bbox and ref_im.size == (56, 56):
            s_crop = im.crop(s_bbox)
            canvas.paste(s_crop, (r_bbox[0], r_bbox[1]))
            return canvas

    if im.size == (56, 56):
        return im

    # Si no tiene referencia, centrar el crop en el lienzo de 56x56
    s_crop = im.crop(s_bbox)
    cw, ch = s_crop.size
    offset_x = max(0, (56 - cw) // 2)
    offset_y = max(0, 56 - ch)  # Alinear al suelo de la caja de batalla
    canvas.paste(s_crop, (offset_x, offset_y))
    return canvas


class Command(BaseCommand):
    help = "Descarga, comprueba transparencia y alinea a 56x56 los sprites normales y shiny de Pokémon Cristal (incluyendo Unown)."

    def add_arguments(self, parser):
        parser.add_argument('--force', action='store_true', help='Fuerza la descarga y reprocesamiento')
        parser.add_argument('--workers', type=int, default=8, help='Número de hilos concurrentes')

    def handle(self, *args, **options):
        force = options['force']
        workers = options['workers']

        normal_dir = Path(settings.MEDIA_ROOT) / "pokemon" / "sprites" / "crystal"
        shiny_dir = Path(settings.MEDIA_ROOT) / "pokemon" / "sprites" / "crystal_shiny"
        normal_unown_dir = normal_dir / "unown"
        shiny_unown_dir = shiny_dir / "unown"

        normal_dir.mkdir(parents=True, exist_ok=True)
        shiny_dir.mkdir(parents=True, exist_ok=True)
        normal_unown_dir.mkdir(parents=True, exist_ok=True)
        shiny_unown_dir.mkdir(parents=True, exist_ok=True)

        pokemon_numbers = list(range(1, 252))
        self.stdout.write(f"Iniciando descarga y sincronización de {len(pokemon_numbers)} sprites de Pokémon Cristal...")

        def fetch_and_save_normal(num):
            norm_file = normal_dir / f"{num}.png"
            if norm_file.exists() and norm_file.stat().st_size > 0 and not force:
                return num, True

            urls = [
                f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/versions/generation-ii/crystal/transparent/{num}.png",
                f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/versions/generation-ii/crystal/{num}.png"
            ]
            for u in urls:
                try:
                    r = requests.get(u, timeout=12)
                    if r.status_code == 200 and len(r.content) > 0:
                        im = Image.open(io.BytesIO(r.content))
                        im_aligned = align_on_56x56(im)
                        im_aligned.save(norm_file, format='PNG')
                        return num, True
                except Exception:
                    pass
            return num, False

        def fetch_and_save_shiny(num):
            shiny_file = shiny_dir / f"{num}.png"
            norm_file = normal_dir / f"{num}.png"
            if shiny_file.exists() and shiny_file.stat().st_size > 0 and not force:
                return num, True

            norm_im = None
            if norm_file.exists():
                try:
                    norm_im = Image.open(norm_file)
                except Exception:
                    pass

            urls = [
                f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/versions/generation-ii/crystal/transparent/shiny/{num}.png",
                f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/versions/generation-ii/crystal/shiny/{num}.png"
            ]
            for u in urls:
                try:
                    r = requests.get(u, timeout=12)
                    if r.status_code == 200 and len(r.content) > 0:
                        im = Image.open(io.BytesIO(r.content))
                        im_aligned = align_on_56x56(im, ref_im=norm_im)
                        im_aligned.save(shiny_file, format='PNG')
                        return num, True
                except Exception:
                    pass
            return num, False

        # 1. Descargar normales
        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
            norm_results = list(executor.map(fetch_and_save_normal, pokemon_numbers))
        norm_ok = sum(1 for _, ok in norm_results if ok)
        self.stdout.write(f"Normales: {norm_ok}/{len(pokemon_numbers)} guardados en {normal_dir}")

        # 2. Descargar shiny alineados
        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
            shiny_results = list(executor.map(fetch_and_save_shiny, pokemon_numbers))
        shiny_ok = sum(1 for _, ok in shiny_results if ok)
        self.stdout.write(f"Shiny: {shiny_ok}/{len(pokemon_numbers)} guardados en {shiny_dir}")

        # 3. Procesar Unown A-Z
        letters = [chr(c) for c in range(ord('a'), ord('z') + 1)]
        self.stdout.write(f"Procesando 26 variantes de Unown (normales y shiny)...")

        def fetch_unown_normal(letter):
            target = normal_unown_dir / f"{letter}.png"
            if target.exists() and target.stat().st_size > 0 and not force:
                return letter, True
            urls = [
                f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/versions/generation-ii/crystal/transparent/201-{letter}.png",
                f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/versions/generation-ii/crystal/201-{letter}.png"
            ]
            for u in urls:
                try:
                    r = requests.get(u, timeout=12)
                    if r.status_code == 200 and len(r.content) > 0:
                        im = Image.open(io.BytesIO(r.content))
                        im_aligned = align_on_56x56(im)
                        im_aligned.save(target, format='PNG')
                        return letter, True
                except Exception:
                    pass
            return letter, False

        def fetch_unown_shiny(letter):
            target = shiny_unown_dir / f"{letter}.png"
            ref_path = normal_unown_dir / f"{letter}.png"
            if target.exists() and target.stat().st_size > 0 and not force:
                return letter, True
            ref_im = None
            if ref_path.exists():
                try:
                    ref_im = Image.open(ref_path)
                except Exception:
                    pass
            urls = [
                f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/versions/generation-ii/crystal/transparent/shiny/201-{letter}.png",
                f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/versions/generation-ii/crystal/shiny/201-{letter}.png"
            ]
            for u in urls:
                try:
                    r = requests.get(u, timeout=12)
                    if r.status_code == 200 and len(r.content) > 0:
                        im = Image.open(io.BytesIO(r.content))
                        im_aligned = align_on_56x56(im, ref_im=ref_im)
                        im_aligned.save(target, format='PNG')
                        return letter, True
                except Exception:
                    pass
            return letter, False

        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
            unown_norm_res = list(executor.map(fetch_unown_normal, letters))
            unown_shiny_res = list(executor.map(fetch_unown_shiny, letters))

        u_norm_ok = sum(1 for _, ok in unown_norm_res if ok)
        u_shiny_ok = sum(1 for _, ok in unown_shiny_res if ok)
        self.stdout.write(f"Unown normales: {u_norm_ok}/26 guardados.")
        self.stdout.write(f"Unown shiny: {u_shiny_ok}/26 guardados.")

        # 4. Asegurar que Unown #201 representativo sea la forma 'F'
        unown_f_norm = normal_unown_dir / "f.png"
        unown_f_shiny = shiny_unown_dir / "f.png"
        if unown_f_norm.exists():
            shutil.copyfile(unown_f_norm, normal_dir / "201.png")
            self.stdout.write("  -> Unown #201 representativo fijado a forma [F] (normal).")
        if unown_f_shiny.exists():
            shutil.copyfile(unown_f_shiny, shiny_dir / "201.png")
            self.stdout.write("  -> Unown #201 representativo fijado a forma [F] (shiny).")

        self.stdout.write(self.style.SUCCESS("¡Sincronización de sprites de Pokémon Cristal completada con éxito!"))
