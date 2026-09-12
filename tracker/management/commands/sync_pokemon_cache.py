import concurrent.futures
from django.core.management.base import BaseCommand
from django.db import transaction
from tracker.models import Pokemon
from tracker.utils import safe_api_get


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
        parser.add_argument(
            '--delay',
            type=float,
            default=0.05,
            help='Pausa de cortesía voluntaria en segundos entre peticiones (por defecto: 0.05)'
        )

    def fetch_raw_data(self, pokemon_id, national_number, pacing_delay=0.05):
        resp = safe_api_get(f'https://pokeapi.co/api/v2/pokemon/{national_number}', pacing_delay=pacing_delay)
        if resp and resp.status_code == 200:
            return pokemon_id, resp.json()
        return pokemon_id, None

    def handle(self, *args, **options):
        update_all = options['all']
        workers = options['workers']
        pacing_delay = options.get('delay', 0.05)

        if update_all:
            queryset = Pokemon.objects.all().order_by('national_number')
        else:
            # Seleccionar Pokémon con raw_data vacío
            queryset = Pokemon.objects.filter(raw_data={}).order_by('national_number')

        total = queryset.count()
        if total == 0:
            self.stdout.write(self.style.SUCCESS("Todos los Pokémon ya cuentan con su raw_data sincronizado."))
            return

        self.stdout.write(f"Iniciando sincronización de raw_data para {total} Pokémon (workers: {workers}, delay: {pacing_delay}s)...")

        targets = list(queryset.values_list('id', 'national_number'))
        results = []

        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
            future_to_poke = {
                executor.submit(self.fetch_raw_data, p_id, num, pacing_delay): (p_id, num)
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
