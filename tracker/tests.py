from django.test import TestCase, Client
from django.urls import reverse
from .models import Game, Pokedex, Pokemon, PokedexEntry, UserPokemonCatch


class PokedexTrackerTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.game = Game.objects.create(name="Pokémon Red", slug="red", generation=1)
        self.pokedex = Pokedex.objects.create(game=self.game, name="Pokédex de Kanto", slug="kanto")
        self.pokemon = Pokemon.objects.create(
            national_number=1,
            name="bulbasaur",
            display_name="Bulbasaur",
            sprite_url="https://example.com/bulbasaur.png",
            primary_type="grass",
            secondary_type="poison"
        )
        self.entry = PokedexEntry.objects.create(
            pokedex=self.pokedex,
            pokemon=self.pokemon,
            entry_number=1
        )

    def test_pokedex_view_status_and_content(self):
        url = reverse("tracker:pokedex_default", kwargs={"game_slug": "red"})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Bulbasaur")
        self.assertContains(response, "#001")
        self.assertEqual(response.context["total_pokemon"], 1)

    def test_toggle_catch_anonymous_user(self):
        url = reverse("tracker:toggle_catch")
        payload = {"entry_id": self.entry.id}
        
        # 1. Marcar como capturado
        response = self.client.post(url, data=payload, content_type="application/json")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertTrue(data["is_caught"])
        self.assertEqual(data["caught_count"], 1)
        self.assertEqual(data["percent"], 100.0)

        # 2. Desmarcar (liberar)
        response_toggle = self.client.post(url, data=payload, content_type="application/json")
        self.assertEqual(response_toggle.status_code, 200)
        data_toggle = response_toggle.json()
        self.assertFalse(data_toggle["is_caught"])
        self.assertEqual(data_toggle["caught_count"], 0)
        self.assertEqual(data_toggle["percent"], 0.0)
