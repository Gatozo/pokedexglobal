import time
import concurrent.futures
import requests
from django.core.management.base import BaseCommand
from django.db import transaction
from tracker.models import Pokemon


class Command(BaseCommand):
    help = "Sincroniza y guarda el JSON crudo (raw_data) de PokeAPI en los Pokémon locales que aún no lo tienen."

    def add_arguments(self, parser):
        parser.add_argument(
            '--all',
            action='store_true',
            help='Fuerza la actualización de raw_data incluso si ya estaba presente'
        )
        parser.add_argument(
            '--workers',
            type=int,
            default=4,
            help='Número de hilos concurrentes para peticiones a PokeAPI (por defecto: 4)'
        )

    def fetch_raw_data(self, pokemon_id, national_number):
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        for attempt in range(3):
            try:
                resp = requests.get(f'https://pokeapi.co/api/v2/pokemon/{national_number}', headers=headers, timeout=12)
                if resp.status_code == 200:
                    return pokemon_id, resp.json()
                elif resp.status_code == 429:
                    time.sleep(1.5 * (attempt + 1))
            except Exception:
                time.sleep(0.4)
        return pokemon_id, None

    def handle(self, *args, **options):
        update_all = options['all']
        workers = options['workers']

        if update_all:
            queryset = Pokemon.objects.all().order_by('national_number')
        else:
            # Seleccionar Pokémon con raw_data vacío
            queryset = Pokemon.objects.filter(raw_data={}).order_by('national_number')

        total = queryset.count()
        if total == 0:
            self.stdout.write(self.style.SUCCESS("Todos los Pokémon ya cuentan con su raw_data sincronizado."))
            return

        self.stdout.write(f"Iniciando sincronización de raw_data para {total} Pokémon (workers: {workers})...")

        targets = list(queryset.values_list('id', 'national_number'))
        results = []

        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
            future_to_poke = {
                executor.submit(self.fetch_raw_data, p_id, num): (p_id, num)
                for p_id, num in targets
            }

            completed = 0
            for future in concurrent.futures.as_completed(future_to_poke):
                p_id, data = future.result()
                if data:
                    results.append((p_id, data))
                completed += 1
                if completed % 25 == 0 or completed == total:
                    self.stdout.write(f"Sincronizados {completed}/{total}...")

        # Guardar en base de datos
        self.stdout.write("Guardando raw_data en la base de datos...")
        with transaction.atomic():
            for p_id, data in results:
                Pokemon.objects.filter(id=p_id).update(raw_data=data)

        self.stdout.write(
            self.style.SUCCESS(
                f"¡Sincronización finalizada con éxito! Se actualizaron {len(results)}/{total} Pokémon con su caché raw_data."
            )
        )
