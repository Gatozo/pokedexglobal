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

        # 1. Pokémon Inicial oficial (Bulbasaur en Rojo)
        res_starter = resolve_obtaining_info(1, "bulbasaur", "red")
        self.assertEqual(res_starter["type"], "starter")
        self.assertEqual(res_starter["badge_label"], "Inicial")
        self.assertIn("Laboratorio del Profesor Oak", res_starter["summary"])
        self.assertEqual(res_starter["locations"][0]["method"], "Elección inicial")

        # 2. Regalo genérico (no inicial)
        mock_encounters_gift = [
            {
                "location_area": {"name": "saffron-city-area"},
                "version_details": [
                    {"version": {"name": "custom_ver"}, "encounter_details": [{"method": {"name": "gift"}}]}
                ]
            }
        ]
        res_gift = resolve_obtaining_info(999, "gift_mon", "custom_ver", encounters_data=mock_encounters_gift)
        self.assertEqual(res_gift["type"], "gift")
        self.assertEqual(res_gift["badge_label"], "Regalo")

        # 3. Evolución (Ivysaur)
        mock_chain = {
            "chain": {
                "species": {"name": "bulbasaur", "url": "https://pokeapi.co/api/v2/pokemon-species/1/"},
                "evolves_to": [
                    {
                        "species": {"name": "ivysaur", "url": "https://pokeapi.co/api/v2/pokemon-species/2/"},
                        "evolution_details": [{"trigger": {"name": "level-up"}, "min_level": 16}],
                        "evolves_to": []
                    }
                ]
            }
        }
        res_evo = resolve_obtaining_info(2, "ivysaur", "red", encounters_data=[], evolution_chain_data=mock_chain, generation=1)
        self.assertEqual(res_evo["type"], "evolution")
        self.assertEqual(res_evo["badge_label"], "Evolución")
        self.assertIn("Nivel 16", res_evo["summary"])

        # 4. Filtro histórico generacional: Hitmonlee en Gen 1 no debe evolucionar de Tyrogue (#236)
        mock_tyrogue_chain = {
            "chain": {
                "species": {"name": "tyrogue", "url": "https://pokeapi.co/api/v2/pokemon-species/236/"},
                "evolves_to": [
                    {
                        "species": {"name": "hitmonlee", "url": "https://pokeapi.co/api/v2/pokemon-species/106/"},
                        "evolution_details": [{"trigger": {"name": "level-up"}, "min_level": 20}],
                        "evolves_to": []
                    }
                ]
            }
        }
        res_gen1_hitmonlee = resolve_obtaining_info(106, "hitmonlee", "red", evolution_chain_data=mock_tyrogue_chain, generation=1)
        self.assertEqual(res_gen1_hitmonlee["badge_label"], "Premio Dojo")
        self.assertIsNone(res_gen1_hitmonlee.get("evolution_info"))

        # En Gen 2, Tyrogue (#236 <= 251) sí es válido
        res_gen2_hitmonlee = resolve_obtaining_info(106, "hitmonlee", "gold", evolution_chain_data=mock_tyrogue_chain, generation=2)
        self.assertIsNotNone(res_gen2_hitmonlee.get("evolution_info"))
        self.assertEqual(res_gen2_hitmonlee["evolution_info"]["from"], "Tyrogue")

        # 5. Exclusivo de versión (Sandshrew #27 en Rojo)
        res_exclusive = resolve_obtaining_info(27, "sandshrew", "red")
        self.assertEqual(res_exclusive["type"], "trade")
        self.assertEqual(res_exclusive["badge_label"], "Intercambio")

        # 6. Snorlax como encuentro estático único bloqueando el camino
        res_snorlax = resolve_obtaining_info(143, "snorlax", "red")
        self.assertTrue(res_snorlax.get("is_unique"))
        self.assertEqual(res_snorlax["locations"][0]["area"], "Bloqueando el camino entre las rutas 12 y 16")
        self.assertEqual(res_snorlax["locations"][0]["method"], "Despertar con Poké Flauta")

        # 7. Intercambios NPC con motes y artículos cuidados
        res_mr_mime_red = resolve_obtaining_info(122, "mr-mime", "red")
        self.assertEqual(res_mr_mime_red["type"], "trade_npc")
        self.assertEqual(
            res_mr_mime_red["summary"],
            "Intercambio en la caseta de la Ruta 2: entrega un Abra a cambio de Mr. Mime (con el mote «Marcel»)"
        )

        res_mr_mime_yellow = resolve_obtaining_info(122, "mr-mime", "yellow")
        self.assertEqual(res_mr_mime_yellow["type"], "trade_npc")
        self.assertEqual(
            res_mr_mime_yellow["summary"],
            "Intercambio en la caseta de la Ruta 2: entrega un Clefairy a cambio de Mr. Mime (con el mote «Miles»)"
        )

        res_farfetchd_red = resolve_obtaining_info(83, "farfetchd", "red")
        self.assertEqual(
            res_farfetchd_red["summary"],
            "Intercambio en Ciudad Carmín: entrega un Spearow a cambio de Farfetch'd (con el mote «Dux»)"
        )

        res_machamp_yellow = resolve_obtaining_info(68, "machamp", "yellow")
        self.assertEqual(
            res_machamp_yellow["summary"],
            "Intercambio en la Vía Subterránea de la Ruta 5: entrega un Cubone a cambio de Machoke (con el mote «Ricky»), que evoluciona inmediatamente a Machamp tras el intercambio"
        )

    def test_location_cleaning_and_biome_encounter_methods(self):
        from .utils import clean_location_name, resolve_encounter_method_label, resolve_obtaining_info

        # 1. Normalización de rutas marítimas a nombres canónicos (Ruta 19, 20, 21)
        self.assertEqual(clean_location_name("kanto-sea-route-19-area"), "Ruta 19")
        self.assertEqual(clean_location_name("kanto-sea-route-20-area"), "Ruta 20")
        self.assertEqual(clean_location_name("kanto-sea-route-21-area"), "Ruta 21")
        self.assertEqual(clean_location_name("kanto-route-1-area"), "Ruta 1")

        # 2. Contextualización del método 'walk' por bioma (Opción A: Hierba alta, Cueva, Interior)
        self.assertEqual(resolve_encounter_method_label("walk", "kanto-route-1-area"), "Hierba alta")
        self.assertEqual(resolve_encounter_method_label("walk", "viridian-forest-area"), "Hierba alta")
        self.assertEqual(resolve_encounter_method_label("walk", "seafoam-islands-b1f"), "Cueva")
        self.assertEqual(resolve_encounter_method_label("walk", "mt-moon-1f"), "Cueva")
        self.assertEqual(resolve_encounter_method_label("walk", "cerulean-cave-1f"), "Cueva")
        self.assertEqual(resolve_encounter_method_label("walk", "pokemon-tower-3f"), "Interior")
        self.assertEqual(resolve_encounter_method_label("walk", "pokemon-mansion-1f"), "Interior")
        # 3. Normalización de áreas de Casino, Laboratorio y Vía Subterránea
        self.assertEqual(clean_location_name("celadon-city-prize-corner"), "Ciudad Azulona (Casino)")
        self.assertEqual(clean_location_name("cinnabar-island-cinnabar-lab"), "Isla Canela (Laboratorio)")
        self.assertEqual(clean_location_name("kanto-underground-path"), "Vía Subterránea")

        # 4. Contextualización de métodos de Casino, Intercambio y Estático
        self.assertEqual(resolve_encounter_method_label("gift", "celadon-city-prize-corner"), "Premio del Casino")
        self.assertEqual(resolve_encounter_method_label("gift", "celadon-city-prize-corner", "red", 147), "Canje de fichas (2.800)")
        self.assertEqual(resolve_encounter_method_label("gift", "celadon-city-prize-corner", "red", 63), "Canje de fichas (180)")
        self.assertEqual(resolve_encounter_method_label("npc-trade", "kanto-route-11-area"), "Intercambio NPC")
        self.assertEqual(resolve_encounter_method_label("static", "kanto-power-plant-area"), "Estático")

        # 5. Obtención de Dratini (Zona Safari + Casino con 2.800 fichas)
        mock_dratini_encounters = [
            {"location_area": {"name": "kanto-safari-zone-area"}, "version_details": [{"version": {"name": "red"}, "encounter_details": [{"method": {"name": "super-rod"}}]}]},
            {"location_area": {"name": "celadon-city-prize-corner"}, "version_details": [{"version": {"name": "red"}, "encounter_details": [{"method": {"name": "gift"}}]}]},
        ]
        res_dratini = resolve_obtaining_info(147, "dratini", "red", encounters_data=mock_dratini_encounters)
        self.assertIn("Zona Safari", res_dratini["summary"])
        self.assertIn("canjeable por 2.800 fichas en el Casino de Ciudad Azulona", res_dratini["summary"])
        areas = [l["area"] for l in res_dratini["locations"]]
        methods = [l["method"] for l in res_dratini["locations"]]
        self.assertIn("Ciudad Azulona (Casino)", areas)
        self.assertIn("Canje de fichas (2.800)", methods)

    def test_comic_modal_rendering_in_template(self):
        self.pokemon.category = "Pokémon Semilla"
        self.pokemon.save()
        self.entry.flavor_text = "Una rara semilla fue plantada en su espalda al nacer."
        self.entry.obtaining_info = {
            "type": "starter",
            "badge_label": "Inicial",
            "badge_color": "emerald",
            "summary": "Pokémon inicial a elegir en el Laboratorio del Profesor Oak",
            "locations": [{"area": "Pueblo Paleta (Laboratorio de Oak)", "method": "Elección inicial"}]
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

    def test_custom_override_protection_in_sync(self):
        from unittest.mock import patch
        from django.core.management import call_command

        # Marcar entrada como personalizada
        self.entry.flavor_text = "Descripción manual protegida"
        self.entry.obtaining_info = {"type": "custom", "summary": "Obtención personalizada"}
        self.entry.is_custom_override = True
        self.entry.save()

        # Mock de descarga de PokeAPI para evitar peticiones de red
        mock_api_data = {
            "pokemon_id": self.pokemon.id,
            "national_number": 1,
            "name": "bulbasaur",
            "species_data": {"flavor_text_entries": [], "genera": []},
            "encounters_data": [],
            "evo_chain_url": None,
        }

        with patch("tracker.management.commands.sync_pokemon_details.Command.fetch_pokemon_api_data", return_value=mock_api_data):
            # Ejecutar sync normal: debe respetar la entrada personalizada
            call_command("sync_pokemon_details", game="red", workers=1, delay=0)
            self.entry.refresh_from_db()
            self.assertEqual(self.entry.flavor_text, "Descripción manual protegida")
            self.assertEqual(self.entry.obtaining_info["summary"], "Obtención personalizada")

            # Ejecutar sync con --force-all: debe sobreescribir la entrada
            call_command("sync_pokemon_details", game="red", workers=1, delay=0, force_all=True)
            self.entry.refresh_from_db()
            self.assertNotEqual(self.entry.flavor_text, "Descripción manual protegida")

    def test_pokemon_blue_exclusives_and_obtaining(self):
        from .utils import resolve_obtaining_info

        # 1. Ekans en Azul: debe figurar como exclusivo de Pokémon Rojo por intercambio
        res_ekans_blue = resolve_obtaining_info(23, "ekans", "blue")
        self.assertEqual(res_ekans_blue["type"], "trade")
        self.assertEqual(res_ekans_blue["badge_label"], "Intercambio")
        self.assertIn("Exclusivo de Pokémon Rojo (obtenible mediante intercambio)", res_ekans_blue["summary"])

        # 2. Sandshrew en Azul: con datos de encuentros debe ser salvaje
        mock_sandshrew_encounters = [
            {
                "location_area": {"name": "kanto-route-4-area"},
                "version_details": [{"version": {"name": "blue"}, "encounter_details": [{"method": {"name": "walk"}}]}]
            }
        ]
        res_sandshrew_blue = resolve_obtaining_info(27, "sandshrew", "blue", encounters_data=mock_sandshrew_encounters)
        self.assertEqual(res_sandshrew_blue["type"], "wild")
        self.assertEqual(res_sandshrew_blue["badge_label"], "Salvaje")
        self.assertIn("Ruta 4", res_sandshrew_blue["summary"])

        # 3. Porygon en Azul: coste de 6.500 fichas
        res_porygon_blue = resolve_obtaining_info(137, "porygon", "blue")
        self.assertEqual(res_porygon_blue["type"], "casino")
        self.assertIn("6.500 fichas", res_porygon_blue["summary"])

        # 4. Nidorino en Azul: salvaje en Zona Safari y canjeable por 1.200 fichas en Casino
        mock_nidorino_encounters = [
            {
                "location_area": {"name": "kanto-safari-zone-area"},
                "version_details": [{"version": {"name": "blue"}, "encounter_details": [{"method": {"name": "walk"}}]}]
            },
            {
                "location_area": {"name": "celadon-city-prize-corner"},
                "version_details": [{"version": {"name": "blue"}, "encounter_details": [{"method": {"name": "gift"}}]}]
            }
        ]
        res_nidorino_blue = resolve_obtaining_info(33, "nidorino", "blue", encounters_data=mock_nidorino_encounters)
        self.assertIn("1.200 fichas", res_nidorino_blue["summary"])
        casino_methods = [l["method"] for l in res_nidorino_blue["locations"] if "Casino" in l["area"]]
        self.assertIn("Canje de fichas (1.200)", casino_methods)

    def test_pokedex_view_pokemon_blue_theming(self):
        game_blue = Game.objects.create(name="Pokémon Blue", slug="blue", generation=1)
        pokedex_blue = Pokedex.objects.create(game=game_blue, name="Pokédex de Kanto", slug="kanto")
        PokedexEntry.objects.create(pokedex=pokedex_blue, pokemon=self.pokemon, entry_number=1)

        url = reverse("tracker:pokedex_default", kwargs={"game_slug": "blue"})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Pokémon Azul")
        self.assertContains(response, "text-blue-500")
        self.assertContains(response, "bg-blue-600")

    def test_independent_catch_tracking_between_red_and_blue(self):
        game_blue = Game.objects.create(name="Pokémon Blue", slug="blue", generation=1)
        pokedex_blue = Pokedex.objects.create(game=game_blue, name="Pokédex de Kanto", slug="kanto")
        entry_blue = PokedexEntry.objects.create(pokedex=pokedex_blue, pokemon=self.pokemon, entry_number=1)

        url_toggle = reverse("tracker:toggle_catch")

        # Capturar en Pokémon Azul
        resp = self.client.post(url_toggle, data={"entry_id": entry_blue.id}, content_type="application/json")
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.json()["is_caught"])

        # Verificar que en Pokémon Rojo sigue como NO capturado
        url_red = reverse("tracker:pokedex_default", kwargs={"game_slug": "red"})
        resp_red = self.client.get(url_red)
        self.assertEqual(resp_red.context["caught_count"], 0)

        # Y en Pokémon Azul figura como capturado
        url_blue = reverse("tracker:pokedex_default", kwargs={"game_slug": "blue"})
        resp_blue = self.client.get(url_blue)
        self.assertEqual(resp_blue.context["caught_count"], 1)


class FixtureExportTests(TestCase):
    def setUp(self):
        from django.contrib.auth.models import User
        self.client = Client()
        self.superuser = User.objects.create_superuser(
            username="admin_test",
            email="admin@test.com",
            password="password123"
        )
        self.staff_user = User.objects.create_user(
            username="staff_test",
            email="staff@test.com",
            password="password123",
            is_staff=True,
            is_superuser=False
        )
        self.game = Game.objects.create(name="Pokémon Red", slug="red", generation=1)
        self.pokedex = Pokedex.objects.create(game=self.game, name="Pokédex de Kanto", slug="kanto")
        self.pokemon = Pokemon.objects.create(
            national_number=1,
            name="bulbasaur",
            display_name="Bulbasaur",
            sprite_url="https://example.com/bulbasaur.png",
            primary_type="grass"
        )
        self.entry = PokedexEntry.objects.create(
            pokedex=self.pokedex,
            pokemon=self.pokemon,
            entry_number=1
        )

    def test_export_fixtures_util(self):
        import tempfile
        from pathlib import Path
        from tracker.fixtures_util import export_tracker_fixtures, get_fixture_info

        with tempfile.TemporaryDirectory() as tmp_dir:
            temp_path = Path(tmp_dir) / "test_fixtures.json"
            info = export_tracker_fixtures(temp_path)
            self.assertTrue(info["exists"])
            self.assertEqual(info["records_count"], 3)  # Game, Pokedex, PokedexEntry
            self.assertTrue(temp_path.exists())

            # Verificar get_fixture_info
            info_check = get_fixture_info(temp_path)
            self.assertEqual(info_check["records_count"], 3)

    def test_export_fixtures_admin_view_permissions(self):
        url = reverse("admin:export_fixtures")

        # 1. Anónimo -> redirige a login
        resp_anon = self.client.post(url)
        self.assertEqual(resp_anon.status_code, 302)
        self.assertIn("/admin/login/", resp_anon.url)

        # 2. Staff no superusuario -> redirige a admin:index con mensaje de error
        self.client.force_login(self.staff_user)
        resp_staff = self.client.post(url, follow=True)
        self.assertEqual(resp_staff.status_code, 200)
        messages = list(resp_staff.context["messages"])
        self.assertTrue(any("Solo los superadministradores" in m.message for m in messages))

        # 3. Superusuario -> realiza exportación con éxito
        self.client.force_login(self.superuser)
        resp_admin = self.client.post(url, follow=True)
        self.assertEqual(resp_admin.status_code, 200)
        admin_messages = list(resp_admin.context["messages"])
        self.assertTrue(any("Respaldo actualizado con éxito" in m.message for m in admin_messages))

    def test_admin_index_context_contains_fixture_info(self):
        self.client.force_login(self.superuser)
        resp = self.client.get(reverse("admin:index"))
        self.assertEqual(resp.status_code, 200)
    def test_pc_icon_url_and_fallback(self):
        icon_url = self.pokemon.get_pc_icon_url(generation=1)
        self.assertTrue(icon_url.startswith("/media/pokemon/icons/") or icon_url.startswith("https://"))
        self.assertIn("1.png", icon_url)
        self.assertEqual(self.entry.pc_icon_url, icon_url)

    def test_version_exclusives_catalog_and_context(self):
        from tracker.exclusives import get_version_exclusives_context, VERSION_EXCLUSIVES_CATALOG, GAME_COUNTERPARTS

        # 1. Crear juego azul y entradas necesarias
        blue_game = Game.objects.create(name="Pokémon Blue", slug="blue", generation=1)
        blue_dex = Pokedex.objects.create(game=blue_game, name="Pokédex de Kanto", slug="kanto")
        sandshrew = Pokemon.objects.create(
            national_number=27,
            name="sandshrew",
            display_name="Sandshrew",
            sprite_url="https://example.com/sandshrew.png",
            primary_type="ground"
        )
        entry_sandshrew = PokedexEntry.objects.create(
            pokedex=self.pokedex,  # en el pokedex de Red
            pokemon=sandshrew,
            entry_number=27
        )

        # 2. Contexto de exclusivos para Rojo
        ctx_red = get_version_exclusives_context(self.game, self.pokedex, set())
        self.assertIsNotNone(ctx_red)
        self.assertEqual(ctx_red["button_label"], "Exclusivos de Azul")
        self.assertEqual(ctx_red["counterpart_slug"], "blue")
        self.assertEqual(ctx_red["counterpart_short_name"], "Azul")
        self.assertEqual(ctx_red["counterpart_name"], "Pokémon Azul")
        self.assertEqual(ctx_red["counterpart_theme"], "blue")
        self.assertEqual(ctx_red["own_theme"], "red")
        self.assertIn(27, [p["national_number"] for p in ctx_red["counterpart_list"]])

        # 3. Contexto de exclusivos para Azul
        ctx_blue = get_version_exclusives_context(blue_game, blue_dex, set())
        self.assertIsNotNone(ctx_blue)
        self.assertEqual(ctx_blue["button_label"], "Exclusivos de Rojo")
        self.assertEqual(ctx_blue["counterpart_slug"], "red")
        self.assertEqual(ctx_blue["counterpart_short_name"], "Rojo")
        self.assertEqual(ctx_blue["counterpart_name"], "Pokémon Rojo")
        self.assertEqual(ctx_blue["counterpart_theme"], "red")
        self.assertEqual(ctx_blue["own_theme"], "blue")

    def test_pokedex_view_renders_exclusives_button_and_modal(self):
        # Crear contraparte Blue para que se active el botón
        Game.objects.get_or_create(name="Pokémon Blue", slug="blue", generation=1)

        url = reverse("tracker:pokedex_default", kwargs={"game_slug": "red"})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Exclusivos de Azul")
        self.assertContains(response, "id=\"btn-exclusives\"")
        self.assertContains(response, "id=\"exclusives-modal\"")
        self.assertContains(response, "id=\"tab-btn-counterpart\"")
        self.assertContains(response, "id=\"tab-btn-own\"")

    def test_yellow_version_exclusives_and_missing_pokemon(self):
        from tracker.exclusives import get_version_exclusives_context, YELLOW_MISSING_POKEMON, YELLOW_ORIGIN_MAP
        from tracker.utils import STARTERS_BY_GAME, YELLOW_SPECIAL_CASES, GAME_CASINO_PRIZES

        yellow_game = Game.objects.create(name="Pokémon Yellow", slug="yellow", generation=1)
        yellow_dex = Pokedex.objects.create(game=yellow_game, name="Pokédex de Kanto", slug="kanto")

        for num in YELLOW_MISSING_POKEMON:
            p, _ = Pokemon.objects.get_or_create(
                national_number=num,
                defaults={"name": f"poke-{num}", "display_name": f"Poke {num}", "primary_type": "normal"}
            )
            PokedexEntry.objects.get_or_create(pokedex=yellow_dex, pokemon=p, defaults={"entry_number": num})

        ctx_yellow = get_version_exclusives_context(yellow_game, yellow_dex, set())
        self.assertIsNotNone(ctx_yellow)
        self.assertTrue(ctx_yellow["is_yellow"])
        self.assertEqual(ctx_yellow["button_label"], "Pokémon a Transferir (13)")
        self.assertEqual(ctx_yellow["counterpart_name"], "Pokémon Rojo y Pokémon Azul")
        self.assertEqual(ctx_yellow["counterpart_short_name"], "Rojo y Azul")
        self.assertEqual(ctx_yellow["counterpart_theme"], "amber")
        self.assertEqual(ctx_yellow["own_theme"], "amber")
        self.assertEqual(len(ctx_yellow["counterpart_list"]), 13)
        self.assertEqual(len(ctx_yellow["own_list"]), 0)

        # Verificar badges de origen para los Pokémon creados
        list_map = {item["national_number"]: item for item in ctx_yellow["counterpart_list"]}
        self.assertEqual(list_map[13]["origin_badge"], "Rojo / Azul")
        self.assertEqual(list_map[23]["origin_badge"], "Rojo")
        self.assertEqual(list_map[52]["origin_badge"], "Azul")

        # Verificar configuración de Amarillo en utils
        self.assertIn(25, STARTERS_BY_GAME['yellow'])
        self.assertEqual(STARTERS_BY_GAME['yellow'][25]["locations"][0]["area"], "Pueblo Paleta (Laboratorio de Oak)")
        self.assertIn(1, YELLOW_SPECIAL_CASES)  # Bulbasaur de regalo
        self.assertIn(4, YELLOW_SPECIAL_CASES)  # Charmander de regalo
        self.assertIn(7, YELLOW_SPECIAL_CASES)  # Squirtle de regalo
        self.assertIn(68, YELLOW_SPECIAL_CASES) # Machamp intercambio NPC
        self.assertIn('yellow', GAME_CASINO_PRIZES)

    def test_yellow_pokedex_view_rendering(self):
        Game.objects.get_or_create(name="Pokémon Red", slug="red", generation=1)
        Game.objects.get_or_create(name="Pokémon Blue", slug="blue", generation=1)
        yellow_game, _ = Game.objects.get_or_create(name="Pokémon Yellow", slug="yellow", generation=1)
        yellow_dex, _ = Pokedex.objects.get_or_create(game=yellow_game, name="Pokédex de Kanto", slug="kanto")

        pikachu = Pokemon.objects.create(
            national_number=25,
            name="pikachu",
            display_name="Pikachu",
            primary_type="electric"
        )
        PokedexEntry.objects.create(pokedex=yellow_dex, pokemon=pikachu, entry_number=25)

        url = reverse("tracker:pokedex_default", kwargs={"game_slug": "yellow"})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Pokémon a Transferir (13)")
        self.assertContains(response, "Pokémon Amarillo")
        self.assertContains(response, "id=\"btn-exclusives\"")
        self.assertContains(response, "id=\"exclusives-modal\"")

    def test_items_catalog_and_utils(self):
        from .utils import get_items_catalog, get_item

        catalog = get_items_catalog()
        self.assertIn("items", catalog)
        self.assertIn("by_id", catalog)
        self.assertGreater(catalog["meta"].get("total_items", 0), 2000)

        # Comprobar Poké Ball
        poke_ball = get_item("poke-ball")
        self.assertIsNotNone(poke_ball)
        self.assertEqual(poke_ball["name_es"], "Poké Ball")
        self.assertEqual(poke_ball["pocket"], "pokeballs")
        self.assertTrue(poke_ball["has_sprite"])
        self.assertTrue(poke_ball["sprite_url"].endswith("poke-ball.png"))

        # Comprobar consulta por ID
        item_master = get_item(1)
        self.assertIsNotNone(item_master)
        self.assertEqual(item_master["slug"], "master-ball")

        # Comprobar Fósil Hélix
        helix = get_item("helix-fossil")
        self.assertIsNotNone(helix)
        self.assertEqual(helix["name_es"], "Fósil Hélix")
        self.assertTrue(helix["has_sprite"])

