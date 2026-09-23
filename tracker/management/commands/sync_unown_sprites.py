import io
from pathlib import Path
import concurrent.futures
import requests
from PIL import Image
from django.conf import settings
from django.core.management.base import BaseCommand


def process_unown_transparency_and_canvas(image_bytes: bytes) -> bytes:
    """
    Toma los bytes de un sprite de Unown (40x40) y:
    1. Aplica flood-fill BFS desde los bordes para hacer transparente el fondo blanco exterior
       preservando el blanco interior del ojo de Unown.
    2. Lo coloca en un lienzo estándar de Game Boy Color de 56x56 en el offset (8, 16),
       garantizando escala y alineación idéntica al resto de la Pokédex.
    """
    im = Image.open(io.BytesIO(image_bytes)).convert('RGBA')
    w, h = im.size
    pixels = im.load()

    visited = set()
    queue = []

    # Iniciar BFS en los bordes exteriores
    for x in range(w):
        if pixels[x, 0][:3] == (255, 255, 255):
            queue.append((x, 0))
        if pixels[x, h - 1][:3] == (255, 255, 255):
            queue.append((x, h - 1))

    for y in range(h):
        if pixels[0, y][:3] == (255, 255, 255):
            queue.append((0, y))
        if pixels[w - 1, y][:3] == (255, 255, 255):
            queue.append((w - 1, y))

    while queue:
        x, y = queue.pop(0)
        if (x, y) in visited:
            continue
        visited.add((x, y))
        pixels[x, y] = (255, 255, 255, 0)

        for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if 0 <= nx < w and 0 <= ny < h and (nx, ny) not in visited:
                if pixels[nx, ny][:3] == (255, 255, 255):
                    queue.append((nx, ny))

    # Lienzo estándar de 56x56
    canvas = Image.new('RGBA', (56, 56), (0, 0, 0, 0))
    # Offset estándar de Game Boy: centrado horizontalmente (8px), fondo alineado abajo (16px)
    offset_x = (56 - w) // 2
    offset_y = 56 - h
    canvas.paste(im, (offset_x, offset_y), im)

    out_buf = io.BytesIO()
    canvas.save(out_buf, format='PNG')
    return out_buf.getvalue()


class Command(BaseCommand):
    help = "Descarga, procesa transparencia y alinea a 56x56 las 26 formas de Unown (normales y shiny) de Pokémon Oro"

    def add_arguments(self, parser):
        parser.add_argument('--force', action='store_true', help='Fuerza la descarga y reprocesamiento')
        parser.add_argument('--workers', type=int, default=6, help='Hilos concurrentes')

    def handle(self, *args, **options):
        force = options['force']
        workers = options['workers']

        base_media = Path(settings.MEDIA_ROOT) / "pokemon" / "sprites"
        gold_unown_dir = base_media / "gold" / "unown"
        gold_shiny_unown_dir = base_media / "gold_shiny" / "unown"

        gold_unown_dir.mkdir(parents=True, exist_ok=True)
        gold_shiny_unown_dir.mkdir(parents=True, exist_ok=True)

        letters = [chr(c) for c in range(ord('a'), ord('z') + 1)]
        self.stdout.write(f"Iniciando descarga y procesamiento de las 26 formas de Unown...")

        def process_letter(letter):
            norm_file = gold_unown_dir / f"{letter}.png"
            shiny_file = gold_shiny_unown_dir / f"{letter}.png"

            # 1. Normal
            if not norm_file.exists() or force:
                url_norm = f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/versions/generation-ii/gold/201-{letter}.png"
                r = requests.get(url_norm, timeout=12)
                if r.status_code == 200:
                    data = process_unown_transparency_and_canvas(r.content)
                    norm_file.write_bytes(data)

            # 2. Shiny
            if not shiny_file.exists() or force:
                url_shiny = f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/versions/generation-ii/gold/shiny/201-{letter}.png"
                r = requests.get(url_shiny, timeout=12)
                if r.status_code == 200:
                    data = process_unown_transparency_and_canvas(r.content)
                    shiny_file.write_bytes(data)

            # 3. Si es la letra 'f', actualizar también 201.png principal
            if letter == 'f':
                main_norm = base_media / "gold" / "201.png"
                main_shiny = base_media / "gold_shiny" / "201.png"
                if norm_file.exists():
                    main_norm.write_bytes(norm_file.read_bytes())
                if shiny_file.exists():
                    main_shiny.write_bytes(shiny_file.read_bytes())

            return letter

        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
            list(executor.map(process_letter, letters))

        self.stdout.write(self.style.SUCCESS(f"¡26 formas de Unown procesadas con éxito en {gold_unown_dir} y {gold_shiny_unown_dir}!"))
        self.stdout.write(self.style.SUCCESS(f"Sprite principal de Unown (201.png) actualizado a la forma F."))
