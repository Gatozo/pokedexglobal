from pathlib import Path
from PIL import Image
from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Normaliza los sprites frontales de 1ª generación (Rojo, Azul, Amarillo) a 56x56 píxeles eliminando el marco transparente de PokeAPI.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--games',
            nargs='+',
            default=['red', 'blue', 'yellow'],
            help='Ediciones a procesar (por defecto: red, blue, yellow)'
        )

    def handle(self, *args, **options):
        media_root = Path(settings.MEDIA_ROOT)
        games = options['games']
        total_processed = 0

        for game in games:
            sprite_dir = media_root / 'pokemon' / 'sprites' / game
            if not sprite_dir.exists():
                self.stdout.write(self.style.WARNING(f"Directorio no encontrado: {sprite_dir}"))
                continue

            count = 0
            for file_path in sorted(sprite_dir.glob('*.png')):
                try:
                    with Image.open(file_path) as img:
                        if img.size == (96, 96):
                            rgba = img.convert('RGBA')
                            cropped = rgba.crop((20, 20, 76, 76))
                            cropped.save(file_path, 'PNG', optimize=True)
                            count += 1
                except Exception as e:
                    self.stderr.write(f"Error procesando {file_path.name}: {e}")

            self.stdout.write(self.style.SUCCESS(f"{game}: {count} sprites normalizados a 56x56 px."))
            total_processed += count

        self.stdout.write(self.style.SUCCESS(f"Total procesados: {total_processed} sprites."))
