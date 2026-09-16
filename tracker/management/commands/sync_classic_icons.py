import os
import requests
from io import BytesIO
from pathlib import Path
from PIL import Image
from django.conf import settings
from django.core.management.base import BaseCommand


def make_transparent_gb(img: Image.Image) -> Image.Image:
    """Convierte una imagen de Game Boy en escala de grises a RGBA haciendo el fondo blanco transparente."""
    img = img.convert('L')
    rgba = Image.new('RGBA', img.size)
    for x in range(img.width):
        for y in range(img.height):
            val = img.getpixel((x, y))
            # En Game Boy: 255 suele ser el fondo blanco
            if val >= 240:
                rgba.putpixel((x, y), (255, 255, 255, 0))
            elif val <= 30:
                rgba.putpixel((x, y), (15, 23, 42, 255))      # Negro / azul oscuro
            elif val <= 100:
                rgba.putpixel((x, y), (51, 65, 85, 255))     # Gris oscuro
            else:
                rgba.putpixel((x, y), (148, 163, 184, 255))  # Gris claro
    return rgba


def make_transparent_gbc(img: Image.Image) -> Image.Image:
    """Convierte una imagen de GBC a RGBA haciendo el color más claro transparente."""
    img = img.convert('L')
    rgba = Image.new('RGBA', img.size)
    for x in range(img.width):
        for y in range(img.height):
            val = img.getpixel((x, y))
            if val >= 230:
                rgba.putpixel((x, y), (255, 255, 255, 0))
            elif val <= 40:
                rgba.putpixel((x, y), (15, 23, 42, 255))
            elif val <= 110:
                rgba.putpixel((x, y), (71, 85, 105, 255))
            else:
                rgba.putpixel((x, y), (148, 163, 184, 255))
    return rgba


class Command(BaseCommand):
    help = "Descarga y procesa los iconos clásicos de menú originales de Game Boy (Gen 1) y Game Boy Color (Gen 2)."

    def handle(self, *args, **options):
        base_icons_dir = Path(settings.MEDIA_ROOT) / "pokemon" / "icons"
        gen1_dir = base_icons_dir / "classic_gen1"
        gen2_dir = base_icons_dir / "classic_gen2"

        for d in [gen1_dir / "archetypes", gen1_dir / "by_pokemon", gen2_dir / "archetypes", gen2_dir / "by_pokemon"]:
            d.mkdir(parents=True, exist_ok=True)

        self.stdout.write("Descargando iconos clásicos de Generación 1 (Game Boy - Pokémon Red/Blue)...")
        self.process_gen1(gen1_dir)

        self.stdout.write("Descargando iconos clásicos de Generación 2 (Game Boy Color - Pokémon Crystal)...")
        self.process_gen2(gen2_dir)

        self.stdout.write(self.style.SUCCESS("¡Iconos clásicos de Gen 1 y Gen 2 descargados y organizados con éxito!"))

    def process_gen1(self, gen1_dir: Path):
        session = requests.Session()
        session.headers.update({"User-Agent": "Mozilla/5.0"})

        # URLs en pokered
        base_pokered = "https://raw.githubusercontent.com/pret/pokered/master"

        # 1. Descargar arquetipos de pokered
        # bug, plant, snake, quadruped son hojas de 8x32 que se ensamblan en 16x16
        archetype_images = {}
        for tile_name, icon_key in [
            ('bug', 'bug'),
            ('plant', 'grass'),
            ('snake', 'snake'),
            ('quadruped', 'quadruped')
        ]:
            url = f"{base_pokered}/gfx/icons/{tile_name}.png"
            resp = session.get(url)
            if resp.status_code == 200:
                src = Image.open(BytesIO(resp.content))
                col1 = src.crop((0, 0, 8, 16))
                col2 = src.crop((0, 16, 8, 32))
                stitched = Image.new('L', (16, 16))
                stitched.paste(col1, (0, 0))
                stitched.paste(col2, (8, 0))
                archetype_images[icon_key] = make_transparent_gb(stitched)

        # monster, bird, fairy, seel (water) son de 16x96 (frame 0 = 0..16)
        for sprite_name, icon_key in [
            ('monster', 'mon'),
            ('bird', 'bird'),
            ('fairy', 'fairy'),
            ('seel', 'water'),
        ]:
            url = f"{base_pokered}/gfx/sprites/{sprite_name}.png"
            resp = session.get(url)
            if resp.status_code == 200:
                src = Image.open(BytesIO(resp.content))
                frame0 = src.crop((0, 0, 16, 16))
                archetype_images[icon_key] = make_transparent_gb(frame0)

        # ball, fossil (helix) son de 16x16 directos
        for sprite_name, icon_key in [
            ('poke_ball', 'ball'),
            ('fossil', 'helix'),
        ]:
            url = f"{base_pokered}/gfx/sprites/{sprite_name}.png"
            resp = session.get(url)
            if resp.status_code == 200:
                src = Image.open(BytesIO(resp.content))
                archetype_images[icon_key] = make_transparent_gb(src)

        # Guardar arquetipos procesados
        for k, img in archetype_images.items():
            img.save(gen1_dir / "archetypes" / f"{k}.png")

        # 2. Descargar y parsear mapeo oficial de Gen 1 (151 Pokémon)
        map_url = f"{base_pokered}/data/pokemon/menu_icons.asm"
        resp_map = session.get(map_url)
        if resp_map.status_code == 200:
            lines = [l.strip() for l in resp_map.text.splitlines() if l.strip().startswith("nybble ICON_")]
            for idx, line in enumerate(lines, start=1):
                # 'nybble ICON_GRASS ; Bulbasaur'
                parts = line.split()
                icon_const = parts[1].replace("ICON_", "").lower()
                img = archetype_images.get(icon_const)
                if img:
                    img.save(gen1_dir / "by_pokemon" / f"{idx}.png")

        self.stdout.write(f"  Gen 1: {len(archetype_images)} arquetipos guardados, 151 Pokémon asignados.")

    def process_gen2(self, gen2_dir: Path):
        session = requests.Session()
        session.headers.update({"User-Agent": "Mozilla/5.0"})

        base_crystal = "https://raw.githubusercontent.com/pret/pokecrystal/master"

        # 1. Obtener lista de arquetipos en gfx/icons/
        tree_resp = session.get("https://api.github.com/repos/pret/pokecrystal/git/trees/master?recursive=1")
        if tree_resp.status_code != 200:
            self.stderr.write("No se pudo obtener el árbol de archivos de pokecrystal")
            return

        icon_paths = [
            t['path'] for t in tree_resp.json().get('tree', [])
            if t['path'].startswith('gfx/icons/') and t['path'].endswith('.png')
        ]

        archetype_images = {}
        for p in icon_paths:
            name = Path(p).stem
            url = f"{base_crystal}/{p}"
            resp = session.get(url)
            if resp.status_code == 200:
                src = Image.open(BytesIO(resp.content))
                # Frame 1: parte superior (0, 0, 16, 16)
                frame = src.crop((0, 0, 16, min(16, src.height)))
                rgba = make_transparent_gbc(frame)
                archetype_images[name] = rgba
                rgba.save(gen2_dir / "archetypes" / f"{name}.png")

        # 2. Parsear mapeo oficial de Gen 2 (251 Pokémon)
        map_url = f"{base_crystal}/data/pokemon/menu_icons.asm"
        resp_map = session.get(map_url)
        if resp_map.status_code == 200:
            lines = [l.strip() for l in resp_map.text.splitlines() if l.strip().startswith("db ICON_")]
            for idx, line in enumerate(lines, start=1):
                # 'db ICON_BULBASAUR ; BULBASAUR'
                parts = line.split()
                icon_const = parts[1].replace("ICON_", "").lower()
                img = archetype_images.get(icon_const)
                if img:
                    img.save(gen2_dir / "by_pokemon" / f"{idx}.png")

        self.stdout.write(f"  Gen 2: {len(archetype_images)} arquetipos guardados, {len(lines)} Pokémon asignados.")
