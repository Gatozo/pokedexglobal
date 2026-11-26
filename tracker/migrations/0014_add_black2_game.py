from django.db import migrations


def add_black2_game(apps, schema_editor):
    Game = apps.get_model('tracker', 'Game')
    Pokedex = apps.get_model('tracker', 'Pokedex')

    black2_game, _ = Game.objects.get_or_create(
        slug='black-2',
        defaults={
            'name': 'Pokémon Negro 2',
            'generation': 5,
        }
    )

    Pokedex.objects.get_or_create(
        game=black2_game,
        slug='unova',
        defaults={
            'name': 'Pokédex Regional de Teselia',
            'is_national': False,
            'pokeapi_name': 'updated-unova',
        }
    )

    Pokedex.objects.get_or_create(
        game=black2_game,
        slug='national',
        defaults={
            'name': 'Pokédex Nacional',
            'is_national': True,
            'pokeapi_name': 'national',
        }
    )


class Migration(migrations.Migration):

    dependencies = [
        ('tracker', '0013_add_white_game'),
    ]

    operations = [
        migrations.RunPython(add_black2_game),
    ]
