import os
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from django.core.management.base import BaseCommand
from django.conf import settings

POKEAPI_CRIES_BASE = "https://raw.githubusercontent.com/PokeAPI/cries/main/cries/pokemon"
POKEYELLOW_BASE = "https://raw.githubusercontent.com/pret/pokeyellow/master/audio/pikachu_cries"

# Formas especiales y variaciones con audio específico
SPECIAL_VARIATIONS = {
    # Pikachu Cosplay (Gen 6 ORAS)
    10080: "pikachu-rock-star",
    10081: "pikachu-belle",
    10082: "pikachu-pop-star",
    10083: "pikachu-phd",
    10084: "pikachu-libre",
    10085: "pikachu-cosplay",
    # Pikachu Gorras de Ash (Gen 7)
    10094: "pikachu-original-cap",
    10095: "pikachu-hoenn-cap",
    10096: "pikachu-sinnoh-cap",
    10097: "pikachu-unova-cap",
    10098: "pikachu-kalos-cap",
    10099: "pikachu-alola-cap",
    10148: "pikachu-partner-cap",
    # Pikachu Starter (Let's Go, Pikachu! - Gen 7 voz anime)
    10158: "pikachu-starter",
    # Pikachu Gorra Trotamundos y Gigamax (Gen 8)
    10160: "pikachu-world-cap",
    10199: "pikachu-gmax",
    # Eevee Starter (Let's Go, Eevee! - Gen 7 voz anime)
    10159: "eevee-starter",
    # Eevee Gigamax (Gen 8)
    10205: "eevee-gmax",
}


def download_file(session: requests.Session, url: str, dest_path: Path, overwrite: bool = False) -> bool:
    if dest_path.exists() and not overwrite and dest_path.stat().st_size > 0:
        return False  # Ya existe

    dest_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        resp = session.get(url, timeout=10)
        if resp.status_code == 200 and len(resp.content) > 0:
            with open(dest_path, "wb") as f:
                f.write(resp.content)
            return True
    except Exception:
        pass
    return False


class Command(BaseCommand):
    help = "Descarga localmente los gritos de Pokémon (retro/legacy, modernos/latest, variaciones de Pikachu/Eevee y Pokémon Amarillo)"

    def add_arguments(self, parser):
        parser.add_argument(
            '--all',
            action='store_true',
            help='Descarga todos los gritos disponibles en PokeAPI (Gen 1 a Gen 9 y todos los legacy)',
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=0,
            help='Número máximo de Pokémon para descargar sus gritos (ej: 251)',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Fuerza la sobreescritura de archivos existentes',
        )
        parser.add_argument(
            '--workers',
            type=int,
            default=12,
            help='Número de hilos concurrentes para la descarga (default: 12)',
        )

    def handle(self, *args, **options):
        download_all = options['all']
        limit_val = options.get('limit', 0)
        overwrite = options['force']
        max_workers = options['workers']

        media_root = Path(settings.MEDIA_ROOT)
        cries_dir = media_root / "pokemon" / "cries"
        legacy_dir = cries_dir / "legacy"
        latest_dir = cries_dir / "latest"
        yellow_dir = cries_dir / "yellow"

        legacy_dir.mkdir(parents=True, exist_ok=True)
        latest_dir.mkdir(parents=True, exist_ok=True)
        yellow_dir.mkdir(parents=True, exist_ok=True)

        tasks = []
        session = requests.Session()

        # Determinar rango de Pokémon a descargar
        if limit_val > 0:
            max_num = limit_val
            max_legacy = limit_val
        else:
            max_num = 1025 if download_all else 151
            max_legacy = 649 if download_all else 151

        self.stdout.write(
            self.style.NOTICE(
                f"Preparando descarga de audios (Modo: Rango 1-{max_num})..."
            )
        )

        # 1. Gritos Retro (Legacy)
        for num in range(1, max_legacy + 1):
            url = f"{POKEAPI_CRIES_BASE}/legacy/{num}.ogg"
            dest = legacy_dir / f"{num}.ogg"
            tasks.append((url, dest))

        # 2. Gritos Modernos (Latest)
        for num in range(1, max_num + 1):
            url = f"{POKEAPI_CRIES_BASE}/latest/{num}.ogg"
            dest = latest_dir / f"{num}.ogg"
            tasks.append((url, dest))

        # 3. Variaciones especiales (Pikachu y Eevee)
        for var_id in SPECIAL_VARIATIONS.keys():
            url = f"{POKEAPI_CRIES_BASE}/latest/{var_id}.ogg"
            dest = latest_dir / f"{var_id}.ogg"
            tasks.append((url, dest))

        # 4. Grito especial de Pokémon Amarillo (Game Boy clásico con voz digitalizada)
        yellow_pika_url = f"{POKEYELLOW_BASE}/pikachu_cry_1.wav"
        yellow_dest = yellow_dir / "25.wav"
        tasks.append((yellow_pika_url, yellow_dest))

        self.stdout.write(f"Iniciando descarga concurrente de {len(tasks)} archivos de audio con {max_workers} hilos...")

        downloaded_count = 0
        skipped_count = 0
        failed_count = 0

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_file = {
                executor.submit(download_file, session, url, dest, overwrite): (url, dest)
                for url, dest in tasks
            }

            for future in as_completed(future_to_file):
                url, dest = future_to_file[future]
                try:
                    res = future.result()
                    if res:
                        downloaded_count += 1
                    else:
                        if dest.exists() and dest.stat().st_size > 0:
                            skipped_count += 1
                        else:
                            failed_count += 1
                except Exception:
                    failed_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Sincronización de audios completada con éxito:\n"
                f"  - Descargados: {downloaded_count}\n"
                f"  - Ya existían (omitidos): {skipped_count}\n"
                f"  - No disponibles/Fallos: {failed_count}\n"
                f"Archivos guardados en: {cries_dir}"
            )
        )
