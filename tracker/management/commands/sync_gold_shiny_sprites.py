import io
from pathlib import Path
import concurrent.futures
import requests
from PIL import Image
from django.conf import settings
from django.core.management.base import BaseCommand
from tracker.models import Pokemon


def process_gold_shiny_transparency_and_alignment(image_bytes: bytes, normal_sprite_path: Path = None) -> bytes:
    """
    Toma los bytes de un sprite de Pokémon Oro y:
    1. Aplica flood-fill BFS desde los bordes para hacer transparente el fondo blanco exterior
       sin alterar los detalles blancos internos del Pokémon (ojos, brillos, vientre).
    2. Si existe el sprite normal correspondiente (56x56), monta el sprite shiny en un lienzo
       transparente de 56x56 respetando exactamente las mismas coordenadas de píxel (bounding box).
       Esto garantiza que al alternar entre la Pokédex normal y la Shinydex, el Pokémon no cambie
       de tamaño ni de posición en pantalla.
    """
    im = Image.open(io.BytesIO(image_bytes)).convert('RGBA')
    w, h = im.size
    pixels = im.load()

    visited = set()
    queue = []

    # Iniciar búsqueda en los 4 bordes exteriores
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

    # BFS flood-fill
    while queue:
        x, y = queue.pop(0)
        if (x, y) in visited:
            continue
        visited.add((x, y))
        pixels[x, y] = (255, 255, 255, 0)  # Totalmente transparente

        for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if 0 <= nx < w and 0 <= ny < h and (nx, ny) not in visited:
                if pixels[nx, ny][:3] == (255, 255, 255):
                    queue.append((nx, ny))

    # Alineación con el sprite normal en lienzo 56x56
    if normal_sprite_path and normal_sprite_path.exists():
        try:
            norm_im = Image.open(normal_sprite_path).convert('RGBA')
            g_bbox = norm_im.split()[3].getbbox()
            s_bbox = im.split()[3].getbbox()

            if g_bbox and s_bbox and norm_im.size == (56, 56):
                s_crop = im.crop(s_bbox)
                canvas = Image.new('RGBA', (56, 56), (0, 0, 0, 0))
                canvas.paste(s_crop, (g_bbox[0], g_bbox[1]))
                im = canvas
        except Exception:
            pass

    out_buf = io.BytesIO()
    im.save(out_buf, format='PNG')
    return out_buf.getvalue()


class Command(BaseCommand):
    help = "Descarga, procesa con transparencia y alinea a 56x56 los sprites shiny auténticos de Pokémon Oro en media/pokemon/sprites/gold_shiny/"

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Fuerza la descarga y reprocesamiento aunque el archivo ya exista'
        )
        parser.add_argument(
            '--align-only',
            action='store_true',
            help='Reprocesa y alinea los sprites locales existentes sin volver a descargar'
        )
        parser.add_argument(
            '--workers',
            type=int,
            default=8,
            help='Número de hilos concurrentes'
        )

    def handle(self, *args, **options):
        force = options['force']
        align_only = options['align_only']
        workers = options['workers']

        target_dir = Path(settings.MEDIA_ROOT) / "pokemon" / "sprites" / "gold_shiny"
        normal_dir = Path(settings.MEDIA_ROOT) / "pokemon" / "sprites" / "gold"
        target_dir.mkdir(parents=True, exist_ok=True)

        pokemon_numbers = list(Pokemon.objects.values_list('national_number', flat=True).order_by('national_number'))
        if not pokemon_numbers:
            pokemon_numbers = list(range(1, 252))

        self.stdout.write(f"Iniciando sincronización y alineación de {len(pokemon_numbers)} sprites shiny auténticos de Pokémon Oro...")

        def process_pokemon(num):
            file_path = target_dir / f"{num}.png"
            norm_path = normal_dir / f"{num}.png"

            if file_path.exists() and file_path.stat().st_size > 0:
                if align_only:
                    try:
                        content = file_path.read_bytes()
                        processed_bytes = process_gold_shiny_transparency_and_alignment(content, norm_path)
                        with open(file_path, 'wb') as f:
                            f.write(processed_bytes)
                        return num, True, "alineado localmente"
                    except Exception as e:
                        return num, False, f"error alinear: {e}"
                elif not force:
                    return num, True, "existente"

            url = f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/versions/generation-ii/gold/shiny/{num}.png"
            try:
                resp = requests.get(url, timeout=12)
                if resp.status_code == 200 and len(resp.content) > 0:
                    processed_bytes = process_gold_shiny_transparency_and_alignment(resp.content, norm_path)
                    with open(file_path, 'wb') as f:
                        f.write(processed_bytes)
                    return num, True, "descargado, procesado y alineado"
                else:
                    return num, False, f"HTTP {resp.status_code}"
            except Exception as e:
                return num, False, str(e)

        success_count = 0
        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
            results = executor.map(process_pokemon, pokemon_numbers)
            for num, success, msg in results:
                if success:
                    success_count += 1
                else:
                    self.stdout.write(self.style.WARNING(f"  [!] #{num:03d} falló: {msg}"))

        self.stdout.write(self.style.SUCCESS(f"Sincronización finalizada: {success_count}/{len(pokemon_numbers)} sprites guardados en {target_dir}"))
