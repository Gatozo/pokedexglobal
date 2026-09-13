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
        self.assertContains(response, "Pokémon Rojo")
        self.assertContains(response, "Planta")
        self.assertEqual(response.context["total_pokemon"], 1)
        self.assertEqual(self.game.display_name, "Pokémon Rojo")
        self.assertEqual(self.pokemon.primary_type_es, "Planta")
        self.assertEqual(self.pokemon.secondary_type_es, "Veneno")

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

    def test_localized_text_fallback(self):
        from .utils import get_localized_text, resolve_game_display_name

        # Caso 1: Tiene español e inglés -> debe devolver español
        entries_with_es = [
            {"name": "Rojo", "language": {"name": "es"}},
            {"name": "Red", "language": {"name": "en"}},
        ]
        self.assertEqual(get_localized_text(entries_with_es), "Rojo")

        # Caso 2: Solo tiene inglés -> fallback automático a inglés
        entries_only_en = [
            {"name": "Colosseum", "language": {"name": "en"}},
            {"name": "Colosseum FR", "language": {"name": "fr"}},
        ]
        self.assertEqual(get_localized_text(entries_only_en), "Colosseum")

        # Caso 3: Ningún idioma soportado -> valor default
        entries_unknown = [
            {"name": "Aka", "language": {"name": "ja"}},
        ]
        self.assertEqual(get_localized_text(entries_unknown, default="Desconocido"), "Desconocido")

    def test_resolve_game_display_name(self):
        from .utils import resolve_game_display_name
        from .models import GAME_NAMES_ES

        # 1. Encontrado en mapeo oficial local
        name = resolve_game_display_name("red", game_translations_map=GAME_NAMES_ES)
        self.assertEqual(name, "Pokémon Rojo")

        # 2. Resuelto desde datos de versión PokeAPI (con español)
        v_data_es = [{"name": "Ultrasol", "language": {"name": "es"}}]
        name = resolve_game_display_name("custom-sun", version_names_data=v_data_es)
        self.assertEqual(name, "Pokémon Ultrasol")

        # 3. Resuelto desde datos de versión PokeAPI (solo inglés)
        v_data_en = [{"name": "Galar Edition", "language": {"name": "en"}}]
        name = resolve_game_display_name("galar-edition", version_names_data=v_data_en)
        self.assertEqual(name, "Pokémon Galar Edition")

        # 4. Fallback final por slug limpio
        name = resolve_game_display_name("legends-za")
        self.assertEqual(name, "Pokémon Legends Za")

    def test_pokemon_type_fallback(self):
        # Tipo desconocido (ej. tipo Stellar o custom) debe hacer fallback a inglés capitalizado sin fallar
        poke = Pokemon(
            national_number=9999,
            name="stellar-mon",
            display_name="StellarMon",
            primary_type="stellar",
            secondary_type="cosmic"
        )
        self.assertEqual(poke.primary_type_es, "Stellar")
        self.assertEqual(poke.secondary_type_es, "Cosmic")

    def test_safe_api_get_retry_and_backoff(self):
        from unittest.mock import patch, MagicMock
        from .utils import safe_api_get

        # 1. Caso exitoso directo
        mock_resp_200 = MagicMock()
        mock_resp_200.status_code = 200
        mock_resp_200.json.return_value = {"id": 1}

        with patch("requests.get", return_value=mock_resp_200) as mock_get:
            resp = safe_api_get("https://example.com/test", pacing_delay=0)
            self.assertIsNotNone(resp)
            self.assertEqual(resp.status_code, 200)
            self.assertEqual(mock_get.call_count, 1)

        # 2. Caso 429 con Retry-After que se recupera en el siguiente intento
        mock_resp_429 = MagicMock()
        mock_resp_429.status_code = 429
        mock_resp_429.headers = {"Retry-After": "0.01"}

        with patch("requests.get", side_effect=[mock_resp_429, mock_resp_200]) as mock_retry:
            with patch("time.sleep"):  # Evitar demoras en el test
                resp = safe_api_get("https://example.com/test-429", base_delay=0.01, pacing_delay=0)
                self.assertIsNotNone(resp)
                self.assertEqual(resp.status_code, 200)
                self.assertEqual(mock_retry.call_count, 2)

    def test_resolve_types_for_generation(self):
        from .utils import resolve_types_for_generation

        # Clefairy raw_data: fairy moderna, pero normal hasta Gen 5
        clefairy_raw = {
            "past_types": [
                {
                    "generation": {"name": "generation-v"},
                    "types": [{"slot": 1, "type": {"name": "normal"}}]
                }
            ]
        }
        # En Gen 1: debe ser normal
        p1, s1 = resolve_types_for_generation(clefairy_raw, "fairy", None, generation=1)
        self.assertEqual(p1, "normal")
        self.assertIsNone(s1)

        # En Gen 5: debe ser normal
        p5, s5 = resolve_types_for_generation(clefairy_raw, "fairy", None, generation=5)
        self.assertEqual(p5, "normal")
        self.assertIsNone(s5)

        # En Gen 6+: debe ser fairy
        p6, s6 = resolve_types_for_generation(clefairy_raw, "fairy", None, generation=6)
        self.assertEqual(p6, "fairy")
        self.assertIsNone(s6)

        # Magnemite raw_data: electric/steel moderno, pero electric en Gen 1
        magnemite_raw = {
            "past_types": [
                {
                    "generation": {"name": "generation-i"},
                    "types": [{"slot": 1, "type": {"name": "electric"}}]
                }
            ]
        }
        pm1, sm1 = resolve_types_for_generation(magnemite_raw, "electric", "steel", generation=1)
        self.assertEqual(pm1, "electric")
        self.assertIsNone(sm1)

        pm2, sm2 = resolve_types_for_generation(magnemite_raw, "electric", "steel", generation=2)
        self.assertEqual(pm2, "electric")
        self.assertEqual(sm2, "steel")

    def test_pokedex_entry_historical_type_properties(self):
        # Entry con tipos históricos definidos
        clefairy = Pokemon.objects.create(
            national_number=35,
            name="clefairy",
            display_name="Clefairy",
            sprite_url="https://example.com/clefairy.png",
            primary_type="fairy",
            secondary_type=None
        )
        entry_gen1 = PokedexEntry.objects.create(
            pokedex=self.pokedex,
            pokemon=clefairy,
            entry_number=35,
            primary_type="normal",
            secondary_type=None
        )
        self.assertEqual(entry_gen1.primary_type_display, "normal")
        self.assertEqual(entry_gen1.primary_type_es, "Normal")
        self.assertIsNone(entry_gen1.secondary_type_display)
        self.assertIsNone(entry_gen1.secondary_type_es)

    def test_pokedex_view_renders_historical_types(self):
        clefairy = Pokemon.objects.create(
            national_number=35,
            name="clefairy",
            display_name="Clefairy",
            sprite_url="https://example.com/clefairy.png",
            primary_type="fairy",
            secondary_type=None
        )
        PokedexEntry.objects.create(
            pokedex=self.pokedex,
            pokemon=clefairy,
            entry_number=35,
            primary_type="normal",
            secondary_type=None
        )
        url = reverse("tracker:pokedex_default", kwargs={"game_slug": "red"})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        # Debe renderizar data-type1="normal" y el badge con "Normal"
        self.assertContains(response, 'data-type1="normal"')
        self.assertContains(response, 'data-type1-es="normal"')
        self.assertContains(response, 'type-normal')

    def test_resolve_flavor_text_canonical_and_fallback(self):
        from .utils import resolve_flavor_text

        # 1. Resolver desde archivo curado red_es.json
        flavor = resolve_flavor_text(1, "red")
        self.assertIn("Una rara semilla", flavor)

        # 2. Resolver con fallback a PokeAPI species_data
        mock_species = {
            "flavor_text_entries": [
                {"flavor_text": "Texto en español de prueba", "language": {"name": "es"}, "version": {"name": "gold"}},
                {"flavor_text": "English test text", "language": {"name": "en"}, "version": {"name": "silver"}}
            ]
        }
        res_es = resolve_flavor_text(999, "gold", species_data=mock_species)
        self.assertEqual(res_es, "Texto en español de prueba")

        res_en = resolve_flavor_text(999, "silver", species_data=mock_species)
        self.assertEqual(res_en, "English test text")

    def test_resolve_obtaining_info(self):
        from .utils import resolve_obtaining_info

        # 1. Regalo en Pueblo Paleta (Bulbasaur)
        mock_encounters_gift = [
            {
                "location_area": {"name": "pallet-town-area"},
                "version_details": [
                    {"version": {"name": "red"}, "encounter_details": [{"method": {"name": "gift"}}]}
                ]
            }
        ]
        res_gift = resolve_obtaining_info(1, "bulbasaur", "red", encounters_data=mock_encounters_gift)
        self.assertEqual(res_gift["type"], "gift")
        self.assertEqual(res_gift["badge_label"], "Regalo / Inicial")
        self.assertIn("Pueblo Paleta", res_gift["summary"])

        # 2. Evolución (Ivysaur)
        mock_chain = {
            "chain": {
                "species": {"name": "bulbasaur"},
                "evolves_to": [
                    {
                        "species": {"name": "ivysaur"},
                        "evolution_details": [{"trigger": {"name": "level-up"}, "min_level": 16}],
                        "evolves_to": []
                    }
                ]
            }
        }
        res_evo = resolve_obtaining_info(2, "ivysaur", "red", encounters_data=[], evolution_chain_data=mock_chain)
        self.assertEqual(res_evo["type"], "evolution")
        self.assertEqual(res_evo["badge_label"], "Evolución")
        self.assertIn("Nivel 16", res_evo["summary"])

        # 3. Exclusivo de versión (Sandshrew #27 en Rojo)
        res_exclusive = resolve_obtaining_info(27, "sandshrew", "red")
        self.assertEqual(res_exclusive["type"], "trade")
        self.assertEqual(res_exclusive["badge_label"], "Intercambio")

    def test_comic_modal_rendering_in_template(self):
        self.pokemon.category = "Pokémon Semilla"
        self.pokemon.save()
        self.entry.flavor_text = "Una rara semilla fue plantada en su espalda al nacer."
        self.entry.obtaining_info = {
            "type": "gift",
            "badge_label": "Regalo / Inicial",
            "badge_color": "emerald",
            "summary": "Entregado como regalo en Pueblo Paleta",
            "locations": [{"area": "Pueblo Paleta", "method": "Regalo / Inicial"}]
        }
        self.entry.save()

        url = reverse("tracker:pokedex_default", kwargs={"game_slug": "red"})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        # Verificar presencia del contenedor del modal estilo cómic
        self.assertContains(response, 'id="comic-modal"')
        self.assertContains(response, 'comic-panel')
        self.assertContains(response, 'comic-bubble')
        self.assertContains(response, 'openPokemonModal(')

        # Verificar datos embebidos en el script JSON
        self.assertContains(response, f'id="entry-data-{self.entry.id}"')
        self.assertContains(response, 'Pokémon Semilla')
        self.assertContains(response, 'Una rara semilla fue plantada')
        self.assertContains(response, 'Pueblo Paleta')


