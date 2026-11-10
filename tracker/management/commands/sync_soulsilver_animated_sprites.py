import os
import shutil
from pathlib import Path
from django.conf import settings
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = "Sincroniza localmente los sprites animados (APNG) de Pokémon Plata SoulSilver desde los assets de Oro HeartGold."

    def handle(self, *args, **options):
        # Directorios de origen (HeartGold)
        hg_normal_dir = Path(settings.MEDIA_ROOT) / "pokemon" / "sprites" / "heartgold_animated"
        hg_shiny_dir = Path(settings.MEDIA_ROOT) / "pokemon" / "sprites" / "heartgold_animated_shiny"
        
        # Directorios de destino (SoulSilver)
        ss_normal_dir = Path(settings.MEDIA_ROOT) / "pokemon" / "sprites" / "soulsilver_animated"
        ss_shiny_dir = Path(settings.MEDIA_ROOT) / "pokemon" / "sprites" / "soulsilver_animated_shiny"

        if not hg_normal_dir.exists() or not hg_shiny_dir.exists():
            self.stdout.write(self.style.ERROR("Directorios de sprites animados de HeartGold no encontrados. Ejecuta sync_heartgold_animated_sprites primero."))
            return

        # Sincronización idempotente
        if not ss_normal_dir.exists():
            shutil.copytree(hg_normal_dir, ss_normal_dir)
            self.stdout.write(self.style.SUCCESS(f"Directorio {ss_normal_dir} creado y poblado."))
        else:
            self.stdout.write(self.style.WARNING(f"Directorio {ss_normal_dir} ya existe, omitiendo."))

        if not ss_shiny_dir.exists():
            shutil.copytree(hg_shiny_dir, ss_shiny_dir)
            self.stdout.write(self.style.SUCCESS(f"Directorio {ss_shiny_dir} creado y poblado."))
        else:
            self.stdout.write(self.style.WARNING(f"Directorio {ss_shiny_dir} ya existe, omitiendo."))

        self.stdout.write(self.style.SUCCESS("Sincronización de sprites animados finalizada."))
