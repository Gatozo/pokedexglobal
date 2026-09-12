from django.core.management.base import BaseCommand
from django.db import transaction
from tracker.models import PokedexEntry
from tracker.utils import resolve_types_for_generation


class Command(BaseCommand):
    help = "Actualiza los tipos históricos (primary_type, secondary_type) en todas las entradas de Pokédex existentes según la generación de su juego."

    def handle(self, *args, **options):
        entries = PokedexEntry.objects.select_related('pokemon', 'pokedex__game').all()
        total = entries.count()
        self.stdout.write(f"Iniciando actualización de tipos para {total} entradas de Pokédex...")

        updated_count = 0
        with transaction.atomic():
            for entry in entries:
                generation = entry.pokedex.game.generation
                pokemon = entry.pokemon
                t1, t2 = resolve_types_for_generation(
                    pokemon.raw_data,
                    pokemon.primary_type,
                    pokemon.secondary_type,
                    generation
                )

                if entry.primary_type != t1 or entry.secondary_type != t2:
                    entry.primary_type = t1
                    entry.secondary_type = t2
                    entry.save(update_fields=['primary_type', 'secondary_type'])
                    updated_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"¡Actualización completada! Se actualizaron {updated_count}/{total} entradas de Pokédex con sus tipos históricos."
            )
        )
