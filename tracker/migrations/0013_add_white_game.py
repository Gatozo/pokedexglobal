from django.db import migrations


def add_white_game(apps, schema_editor):
    Game = apps.get_model('tracker', 'Game')
    Pokedex = apps.get_model('tracker', 'Pokedex')

    white_game, _ = Game.objects.get_or_create(
        slug='white',
        defaults={
            'name': 'Pokémon Blanco',
            'generation': 5,
        }
    )

    Pokedex.objects.get_or_create(
        game=white_game,
        slug='unova',
        defaults={
            'name': 'Pokédex Regional de Teselia',
            'is_national': False,
            'pokeapi_name': 'unova',
        }
    )

    Pokedex.objects.get_or_create(
        game=white_game,
        slug='national',
        defaults={
            'name': 'Pokédex Nacional',
            'is_national': True,
            'pokeapi_name': 'national',
        }
    )


class Migration(migrations.Migration):

    dependencies = [
        ('tracker', '0012_add_black_game'),
    ]

    operations = [
        migrations.RunPython(add_white_game),
    ]
