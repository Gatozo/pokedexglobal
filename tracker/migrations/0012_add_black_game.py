from django.db import migrations

def add_black_game(apps, schema_editor):
    Game = apps.get_model('tracker', 'Game')
    Pokedex = apps.get_model('tracker', 'Pokedex')
    
    black_game, created = Game.objects.get_or_create(
        slug='black',
        defaults={
            'name': 'Pokémon Negro',
            'generation': 5,
        }
    )
    
    # Asegurar la creación de sus Pokédex asociadas
    Pokedex.objects.get_or_create(
        game=black_game,
        slug='unova',
        defaults={
            'name': 'Pokédex Regional de Teselia',
            'is_national': False,
            'pokeapi_name': 'unova'
        }
    )
    
    Pokedex.objects.get_or_create(
        game=black_game,
        slug='national',
        defaults={
            'name': 'Pokédex Nacional',
            'is_national': True,
            'pokeapi_name': 'national'
        }
    )

class Migration(migrations.Migration):

    dependencies = [
        ('tracker', '0011_add_soulsilver_game'),
    ]

    operations = [
        migrations.RunPython(add_black_game),
    ]
