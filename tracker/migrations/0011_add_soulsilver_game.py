from django.db import migrations

def add_soulsilver_game(apps, schema_editor):
    Game = apps.get_model('tracker', 'Game')
    Pokedex = apps.get_model('tracker', 'Pokedex')
    
    # Crear SoulSilver si no existe
    ss_game, created = Game.objects.get_or_create(
        slug='soulsilver',
        defaults={
            'name': 'Pokémon Plata SoulSilver',
            'generation': 4,
        }
    )
    
    if created:
        # Pokedex Regional
        Pokedex.objects.create(
            game=ss_game,
            name='Pokédex de Johto',
            slug='johto',
            is_national=False,
            pokeapi_name='updated-johto'
        )
        
        # Pokedex Nacional
        Pokedex.objects.create(
            game=ss_game,
            name='Pokédex Nacional',
            slug='national',
            is_national=True,
            pokeapi_name='national'
        )

class Migration(migrations.Migration):

    dependencies = [
        ('tracker', '0010_userpokemoncatch_unique_user_game_entry_and_more'),
    ]

    operations = [
        migrations.RunPython(add_soulsilver_game),
    ]
