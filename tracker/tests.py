from unittest.mock import patch
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

    def test_dark_type_badge_rendering(self):
        """Verifica que el tipo siniestro (dark) tenga su clase CSS y se renderice correctamente en español."""
        umbreon = Pokemon.objects.create(
            national_number=197,
            name="umbreon",
            display_name="Umbreon",
            primary_type="dark"
        )
        PokedexEntry.objects.create(
            pokedex=self.pokedex,
            pokemon=umbreon,
            entry_number=185,
            primary_type="dark"
        )
        url = reverse("tracker:pokedex_default", kwargs={"game_slug": "red"})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '.type-dark { background-color: #705848;')
        self.assertContains(response, 'type-dark')
        self.assertContains(response, 'Siniestro')

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

        # 3. Superusuario -> realiza exportación con éxito (mockeado para evitar sobrescribir fixtures en disco)
        self.client.force_login(self.superuser)
        with patch("tracker.admin.export_tracker_fixtures") as mock_export:
            mock_export.return_value = {
                "exists": True,
                "file_name": "pokedex_entries.json",
                "relative_path": "tracker/fixtures/pokedex_entries.json",
                "size_human": "15.0 KB",
                "records_count": 3,
            }
            resp_admin = self.client.post(url, follow=True)
            self.assertEqual(resp_admin.status_code, 200)
            mock_export.assert_called_once()
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
        self.assertEqual(ctx_red["button_label"], "Exclusivos")
        self.assertEqual(ctx_red["full_button_label"], "Exclusivos de Azul")
        self.assertEqual(ctx_red["counterpart_slug"], "blue")
        self.assertEqual(ctx_red["counterpart_short_name"], "Azul")
        self.assertEqual(ctx_red["counterpart_name"], "Pokémon Azul")
        self.assertEqual(ctx_red["counterpart_theme"], "blue")
        self.assertEqual(ctx_red["own_theme"], "red")
        self.assertIn(27, [p["national_number"] for p in ctx_red["counterpart_list"]])

        # 3. Contexto de exclusivos para Azul
        ctx_blue = get_version_exclusives_context(blue_game, blue_dex, set())
        self.assertIsNotNone(ctx_blue)
        self.assertEqual(ctx_blue["button_label"], "Exclusivos")
        self.assertEqual(ctx_blue["full_button_label"], "Exclusivos de Rojo")
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

    def test_yellow_version_transfers_and_missing_pokemon(self):
        from tracker.exclusives import get_version_transfers_context, get_version_exclusives_context, VERSION_TRANSFERS_CATALOG
        from tracker.utils import STARTERS_BY_GAME, YELLOW_SPECIAL_CASES, GAME_CASINO_PRIZES

        yellow_game = Game.objects.create(name="Pokémon Yellow", slug="yellow", generation=1)
        yellow_dex = Pokedex.objects.create(game=yellow_game, name="Pokédex de Kanto", slug="kanto")

        yellow_missing = VERSION_TRANSFERS_CATALOG['yellow']
        for num in yellow_missing:
            p, _ = Pokemon.objects.get_or_create(
                national_number=num,
                defaults={"name": f"poke-{num}", "display_name": f"Poke {num}", "primary_type": "normal"}
            )
            PokedexEntry.objects.get_or_create(pokedex=yellow_dex, pokemon=p, defaults={"entry_number": num})

        # En Amarillo no hay versión gemela, por lo que exclusives es None
        ctx_excl = get_version_exclusives_context(yellow_game, yellow_dex, set())
        self.assertIsNone(ctx_excl)

        # Pero transfers contiene los 13 Pokémon
        ctx_yellow = get_version_transfers_context(yellow_game, yellow_dex, set())
        self.assertIsNotNone(ctx_yellow)
        self.assertEqual(ctx_yellow["button_label"], "Transferir")
        self.assertEqual(ctx_yellow["full_button_label"], "Pokémon a Transferir")
        self.assertEqual(ctx_yellow["mechanic_badge"], "Transferencia Link")
        self.assertEqual(len(ctx_yellow["transfer_list"]), 13)

        # Verificar badges de origen para los Pokémon creados
        list_map = {item["national_number"]: item for item in ctx_yellow["transfer_list"]}
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
        self.assertContains(response, "Pokémon a Transferir")
        self.assertContains(response, "Pokémon Amarillo")
        self.assertContains(response, "id=\"btn-transfers\"")
        self.assertContains(response, "id=\"transfers-modal\"")
        self.assertNotContains(response, "id=\"btn-exclusives\"")

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

    def test_evolution_stones_catalog_and_locations(self):
        import os
        from django.conf import settings
        from .utils import get_evolution_stones_catalog, resolve_evolution_stone

        catalog = get_evolution_stones_catalog()
        self.assertIn("moon-stone", catalog)
        self.assertIn("fire-stone", catalog)
        self.assertIn("water-stone", catalog)
        self.assertIn("thunder-stone", catalog)
        self.assertIn("leaf-stone", catalog)

        # 1. Verificar que cada imagen de piedra existe físicamente en media/items/
        for slug, stone in catalog.items():
            icon_rel = stone["icon_url"].lstrip("/")
            full_path = os.path.join(settings.BASE_DIR, icon_rel)
            self.assertTrue(os.path.exists(full_path), f"La imagen {full_path} para la piedra {slug} no existe.")

        # 2. Verificar datos de Piedra Lunar en Rojo
        moon_stone = resolve_evolution_stone(item_slug="moon-stone", game_slug="red")
        self.assertIsNotNone(moon_stone)
        self.assertEqual(moon_stone["name"], "Piedra Lunar")
        self.assertFalse(moon_stone["is_purchasable"])
        self.assertGreaterEqual(len(moon_stone["locations"]), 4)
        areas = [l["area"] for l in moon_stone["locations"]]
        self.assertTrue(any("Monte Moon" in a for a in areas))
        self.assertTrue(any("Guarida Rocket" in a for a in areas))

        # 3. Verificar datos de Piedra Fuego en Azul
        fire_stone = resolve_evolution_stone(text_hint="usando Piedra Fuego", game_slug="blue")
        self.assertIsNotNone(fire_stone)
        self.assertEqual(fire_stone["slug"], "fire-stone")
        self.assertTrue(fire_stone["is_purchasable"])
        self.assertEqual(fire_stone["price"], 2100)

    def test_evolution_stone_pokedex_entry_property(self):
        import json
        # Crear Pokémon Clefable con obtención por evolución con Piedra Lunar
        pokemon_clefable = Pokemon.objects.create(
            national_number=36,
            name="clefable",
            display_name="Clefable",
            sprite_url="https://example.com/clefable.png",
            primary_type="fairy"
        )
        entry_clefable = PokedexEntry.objects.create(
            pokedex=self.pokedex,
            pokemon=pokemon_clefable,
            entry_number=36,
            obtaining_info={
                "type": "evolution",
                "summary": "Evoluciona de Clefairy usando Piedra Lunar",
                "evolution_info": {
                    "from": "Clefairy",
                    "trigger": "use-item",
                    "condition": "usando Piedra Lunar",
                    "text": "Evoluciona de Clefairy usando Piedra Lunar",
                    "item_slug": "moon-stone",
                    "item_name": "Piedra Lunar",
                    "item_icon": "/media/items/moon-stone.png"
                }
            }
        )

        # La propiedad evolution_stone debe estar presente en Clefable
        stone = entry_clefable.evolution_stone
        self.assertIsNotNone(stone)
        self.assertEqual(stone["slug"], "moon-stone")
        self.assertEqual(stone["name"], "Piedra Lunar")
        self.assertEqual(stone["icon_url"], "/media/items/moon-stone.png")
        self.assertFalse(stone["is_purchasable"])

        # En Bulbasaur (entry normal de setUp) debe ser None
        self.assertIsNone(self.entry.evolution_stone)

        # Verificar serialización en modal_data_json
        modal_json = json.loads(entry_clefable.modal_data_json)
        self.assertIn("evolution_stone", modal_json)
        self.assertEqual(modal_json["evolution_stone"]["slug"], "moon-stone")

    def test_pokemon_cries_local_resolution_and_fallback(self):
        """Verifica que los gritos devuelven rutas locales /media/... o fallback externo según existencia."""
        # Bulbasaur en juego retro (Gen 1)
        cry_url = self.entry.cry_url
        self.assertTrue(cry_url.startswith("/media/pokemon/cries/") or cry_url.startswith("https://"))
        self.assertTrue(self.pokemon.cry_legacy_url.startswith("/media/pokemon/cries/") or self.pokemon.cry_legacy_url.startswith("https://"))

        # Método flexible con selector de grito moderno y variaciones
        modern_url = self.pokemon.get_cry_url(kind="latest")
        self.assertTrue(modern_url.startswith("/media/pokemon/cries/latest/") or modern_url.startswith("https://"))

        # Crear Pikachu en Pokémon Amarillo
        game_yellow = Game.objects.create(name="Pokémon Yellow", slug="yellow", generation=1)
        pokedex_yellow = Pokedex.objects.create(game=game_yellow, name="Pokédex de Kanto", slug="kanto")
        pikachu = Pokemon.objects.create(
            national_number=25,
            name="pikachu",
            display_name="Pikachu",
            sprite_url="https://example.com/pikachu.png",
            primary_type="electric"
        )
        entry_yellow_pika = PokedexEntry.objects.create(
            pokedex=pokedex_yellow,
            pokemon=pikachu,
            entry_number=25
        )

        # En amarillo debe resolver al sonido especial si existe en disco
        yellow_cry = entry_yellow_pika.cry_url
        if yellow_cry.endswith(".wav"):
            self.assertEqual(yellow_cry, "/media/pokemon/cries/yellow/25.wav")
        else:
            self.assertTrue("25" in yellow_cry)

        # Variaciones de Pikachu (Cosplay y Starter Let's Go) y Eevee
        cosplay_cry = pikachu.get_cry_url(kind="latest", variation_id=10080)
        self.assertIn("10080", cosplay_cry)
        eevee_starter_cry = self.pokemon.get_cry_url(kind="latest", variation_id=10159)
        self.assertIn("10159", eevee_starter_cry)

    def test_gold_pokedex_view_and_exclusives(self):
        """Verifica la Pokédex de Johto, Pokédex Nacional y exclusividades de Pokémon Oro."""
        gold_game, _ = Game.objects.get_or_create(name="Pokémon Gold", slug="gold", generation=2)
        Game.objects.get_or_create(name="Pokémon Silver", slug="silver", generation=2)
        johto_dex, _ = Pokedex.objects.get_or_create(game=gold_game, name="Pokédex de Johto", slug="johto")
        nat_dex, _ = Pokedex.objects.get_or_create(game=gold_game, name="Pokédex Nacional", slug="national", is_national=True)

        chikorita, _ = Pokemon.objects.get_or_create(
            national_number=152,
            defaults={"name": "chikorita", "display_name": "Chikorita", "primary_type": "grass"}
        )
        PokedexEntry.objects.get_or_create(pokedex=johto_dex, entry_number=1, defaults={"pokemon": chikorita})
        PokedexEntry.objects.get_or_create(pokedex=nat_dex, entry_number=152, defaults={"pokemon": chikorita})

        # Probar vista por defecto (/gold/ -> Pokédex de Johto)
        url_default = reverse("tracker:pokedex_default", kwargs={"game_slug": "gold"})
        resp_default = self.client.get(url_default)
        self.assertEqual(resp_default.status_code, 200)
        self.assertContains(resp_default, "Pokémon Oro")
        self.assertContains(resp_default, "Pokédex de Johto")
        self.assertContains(resp_default, "Región Johto")
        self.assertContains(resp_default, "Exclusivos de Plata")

        # Probar vista específica (/gold/national/ -> Pokédex Nacional)
        url_nat = reverse("tracker:pokedex_detail", kwargs={"game_slug": "gold", "pokedex_slug": "national"})
        resp_nat = self.client.get(url_nat)
        self.assertEqual(resp_nat.status_code, 200)
        self.assertContains(resp_nat, "Pokédex Nacional")

        # Probar contexto de exclusividades
        from .exclusives import get_version_exclusives_context
        ctx_gold = get_version_exclusives_context(gold_game, johto_dex, set())
        self.assertIsNotNone(ctx_gold)
        self.assertEqual(ctx_gold["counterpart_short_name"], "Plata")
        self.assertEqual(ctx_gold["counterpart_theme"], "silver")
        self.assertEqual(ctx_gold["own_theme"], "gold")
        self.assertEqual(ctx_gold["button_label"], "Exclusivos")
        self.assertEqual(ctx_gold["full_button_label"], "Exclusivos de Plata")

    def test_gold_starters_and_skeletons(self):
        """Verifica la configuración de iniciales de Pokémon Oro con el Profesor Elm y los esqueletos de juegos futuros."""
        from .utils import STARTERS_BY_GAME, resolve_obtaining_info

        # Iniciales de Johto
        self.assertIn('gold', STARTERS_BY_GAME)
        self.assertIn('silver', STARTERS_BY_GAME)
        for starter_id in [152, 155, 158]:
            self.assertIn(starter_id, STARTERS_BY_GAME['gold'])
            info = STARTERS_BY_GAME['gold'][starter_id]
            self.assertEqual(info["type"], "starter")
            self.assertEqual(info["badge_label"], "Inicial")
            self.assertIn("Profesor Elm", info["summary"])
            self.assertIn("Pueblo Primavera", info["summary"])
            self.assertEqual(info["locations"][0]["area"], "Pueblo Primavera (Laboratorio de Elm)")
            self.assertEqual(info["locations"][0]["method"], "Elección inicial")

        # Verificar resolve_obtaining_info para Chikorita en Oro
        res_chikorita = resolve_obtaining_info(152, "chikorita", "gold")
        self.assertEqual(res_chikorita["type"], "starter")
        self.assertEqual(res_chikorita["badge_label"], "Inicial")
        self.assertIn("Profesor Elm", res_chikorita["summary"])

        # Verificar esqueletos de juegos futuros
        for g in ['ruby', 'sapphire', 'emerald', 'firered', 'leafgreen', 'diamond', 'pearl', 'platinum']:
            self.assertIn(g, STARTERS_BY_GAME)

    def test_gold_location_translations_and_biomes(self):
        """Verifica la traducción al español de áreas, cuevas, torres y métodos de encuentro en Johto."""
        from .utils import clean_location_name, resolve_encounter_method_label

        # Pueblos y ciudades
        self.assertEqual(clean_location_name("new-bark-town-area"), "Pueblo Primavera")
        self.assertEqual(clean_location_name("cherrygrove-city-area"), "Ciudad Cerezo")
        self.assertEqual(clean_location_name("violet-city-area"), "Ciudad Malva")
        self.assertEqual(clean_location_name("goldenrod-city-area"), "Ciudad Trigal")
        self.assertEqual(clean_location_name("goldenrod-city-game-corner"), "Ciudad Trigal (Casino)")
        self.assertEqual(clean_location_name("cianwood-city-area"), "Ciudad Orquídea")
        self.assertEqual(clean_location_name("blackthorn-city-area"), "Ciudad Endrino")

        # Mazmorras, cuevas y torres
        self.assertEqual(clean_location_name("sprout-tower-2f"), "Torre Bellsprout (2P)")
        self.assertEqual(clean_location_name("burned-tower-1f"), "Torre Quemada (1P)")
        self.assertEqual(clean_location_name("bell-tower-roof"), "Torre Hojalata (Tejado)")
        self.assertEqual(clean_location_name("slowpoke-well-1f"), "Pozo Slowpoke (1P)")
        self.assertEqual(clean_location_name("union-cave-b2f"), "Cueva Unión (Sótano 2)")
        self.assertEqual(clean_location_name("ice-path-1f"), "Ruta Helada (1P)")
        self.assertEqual(clean_location_name("dragons-den-area"), "Guarida Dragón")
        self.assertEqual(clean_location_name("lake-of-rage-area"), "Lago de la Furia")
        self.assertEqual(clean_location_name("mt-mortar-b1f"), "Monte Mortero (Sótano)")
        self.assertEqual(clean_location_name("mt-silver-top"), "Monte Plateado (Cima)")

        # Rutas con prefijo Johto
        self.assertEqual(clean_location_name("johto-route-29-area"), "Ruta 29")
        self.assertEqual(clean_location_name("johto-sea-route-40-area"), "Ruta 40")
        self.assertEqual(clean_location_name("kanto-victory-road-1-1f"), "Calle Victoria (1P)")

        # Biomas: 'walk' en cuevas debe ser 'Cueva', y en interiores 'Interior'
        self.assertEqual(resolve_encounter_method_label("walk", "dark-cave-violet-city-entrance"), "Cueva")
        self.assertEqual(resolve_encounter_method_label("walk", "sprout-tower-2f"), "Interior")
        self.assertEqual(resolve_encounter_method_label("walk", "johto-route-29-area"), "Hierba alta")

        # Métodos de Gen 2
        self.assertEqual(resolve_encounter_method_label("headbutt-normal", "johto-route-29-area"), "Golpe Cabeza")
        self.assertEqual(resolve_encounter_method_label("rock-smash", "ruins-of-alph-outside"), "Golpe Roca")
        self.assertEqual(resolve_encounter_method_label("squirt-bottle", "johto-route-36-area"), "Regadera")
        self.assertEqual(resolve_encounter_method_label("roaming-grass", "roaming-johto-area"), "Pokémon errante")

    def test_gold_casinos_and_obtaining(self):
        """Verifica precios de casinos de Ciudad Trigal y Ciudad Azulona en Pokémon Oro."""
        from .utils import GAME_CASINO_PRIZES, resolve_obtaining_info

        self.assertIn('gold', GAME_CASINO_PRIZES)
        self.assertEqual(GAME_CASINO_PRIZES['gold'][63], 200)    # Abra (Trigal)
        self.assertEqual(GAME_CASINO_PRIZES['gold'][23], 700)    # Ekans (Trigal)
        self.assertEqual(GAME_CASINO_PRIZES['gold'][147], 2100)  # Dratini (Trigal)
        self.assertEqual(GAME_CASINO_PRIZES['gold'][122], 3333)  # Mr. Mime (Azulona)
        self.assertEqual(GAME_CASINO_PRIZES['gold'][133], 6666)  # Eevee (Azulona)
        self.assertEqual(GAME_CASINO_PRIZES['gold'][137], 9999)  # Porygon (Azulona)

        # Ekans: solo en Casino de Ciudad Trigal
        mock_ekans = [{
            "location_area": {"name": "goldenrod-city-game-corner"},
            "version_details": [{"version": {"name": "gold"}, "encounter_details": [{"method": {"name": "gift"}}]}]
        }]
        res_ekans = resolve_obtaining_info(23, "ekans", "gold", encounters_data=mock_ekans)
        self.assertEqual(res_ekans["type"], "casino")
        self.assertEqual(res_ekans["badge_label"], "Premio Casino")
        self.assertIn("700 fichas", res_ekans["summary"])
        self.assertIn("Casino de Ciudad Trigal", res_ekans["summary"])
        self.assertEqual(res_ekans["locations"][0]["method"], "Canje de fichas (700)")

        # Porygon: en Casino de Ciudad Azulona
        mock_porygon = [{
            "location_area": {"name": "celadon-city-prize-corner"},
            "version_details": [{"version": {"name": "gold"}, "encounter_details": [{"method": {"name": "gift"}}]}]
        }]
        res_porygon = resolve_obtaining_info(137, "porygon", "gold", encounters_data=mock_porygon)
        self.assertEqual(res_porygon["type"], "casino")
        self.assertIn("9.999 fichas", res_porygon["summary"])
        self.assertIn("Casino de Ciudad Azulona", res_porygon["summary"])

    def test_gold_special_cases(self):
        """Verifica casos especiales de Pokémon Oro: exclusivos, Cápsula del Tiempo, regalos y estáticos."""
        from .utils import resolve_obtaining_info, GAME_SPECIAL_CASES

        self.assertIn('gold', GAME_SPECIAL_CASES)

        # Exclusivos de Plata por intercambio (ej. Phanpy #231)
        res_phanpy = resolve_obtaining_info(231, "phanpy", "gold")
        self.assertEqual(res_phanpy["type"], "trade")
        self.assertEqual(res_phanpy["badge_label"], "Intercambio")
        self.assertIn("Exclusivo de Pokémon Plata", res_phanpy["summary"])

        # Iniciales de Kanto transferibles vía Cápsula del Tiempo
        res_bulba = resolve_obtaining_info(1, "bulbasaur", "gold")
        self.assertEqual(res_bulba["type"], "trade")
        self.assertIn("Cápsula del Tiempo", res_bulba["summary"])

        # Intercambio NPC: Onix en Ciudad Malva
        res_onix = resolve_obtaining_info(95, "onix", "gold")
        self.assertEqual(res_onix["type"], "trade_npc")
        self.assertIn("Rocky", res_onix["summary"])

        # Regalo especial: Togepi (Huevo Misterioso)
        res_togepi = resolve_obtaining_info(175, "togepi", "gold")
        self.assertEqual(res_togepi["type"], "gift")
        self.assertEqual(res_togepi["badge_label"], "Huevo Regalo")
        self.assertIn("Huevo Misterioso", res_togepi["summary"])

        # Estático: Sudowoodo con Regadera
        res_sudo = resolve_obtaining_info(185, "sudowoodo", "gold")
        self.assertEqual(res_sudo["type"], "special")
        self.assertIn("Regadera", res_sudo["summary"])

        # Legendario: Ho-Oh y Lugia
        res_hooh = resolve_obtaining_info(250, "ho-oh", "gold")
        self.assertEqual(res_hooh["type"], "legendary")
        self.assertIn("Ala Arcoíris", res_hooh["summary"])

        res_lugia = resolve_obtaining_info(249, "lugia", "gold")
        self.assertEqual(res_lugia["type"], "legendary")
        self.assertIn("Ala Plateada", res_lugia["summary"])

    def test_breeding_baby_pokemon_gold(self):
        """Verifica que los Pokémon bebé sin encuentros salvajes en Oro se obtengan por Crianza y Huevo Extraño."""
        from .utils import resolve_obtaining_info

        # Pichu (#172)
        res_pichu = resolve_obtaining_info(172, "pichu", "gold", encounters_data=[], generation=2)
        self.assertEqual(res_pichu["type"], "breeding")
        self.assertEqual(res_pichu["badge_label"], "Crianza")
        self.assertEqual(res_pichu["badge_color"], "pink")
        self.assertIn("Ruta 34 (Guardería Pokémon)", res_pichu["summary"])
        self.assertIn("Huevo Extraño", res_pichu["summary"])
        self.assertEqual(len(res_pichu["locations"]), 2)
        self.assertEqual(res_pichu["locations"][0]["method"], "Crianza de huevo")
        self.assertIn("Huevo Extraño", res_pichu["locations"][1]["method"])

        # Cleffa (#173) y Smoochum (#238)
        for num, name in [(173, "cleffa"), (238, "smoochum")]:
            res = resolve_obtaining_info(num, name, "gold", encounters_data=[], generation=2)
            self.assertEqual(res["type"], "breeding")
            self.assertEqual(res["badge_label"], "Crianza")
            self.assertEqual(res["badge_color"], "pink")

    def test_wild_base_pokemon_breeding_gold(self):
        """Verifica que los Pokémon fase base salvajes en Gen 2 incluyan Crianza en Guardería y badge compuesto."""
        from .utils import resolve_obtaining_info

        mock_encounters = [{
            "location_area": {"name": "johto-route-32-area"},
            "version_details": [{"version": {"name": "gold"}, "encounter_details": [{"method": {"name": "walk"}}]}]
        }]
        res_mareep = resolve_obtaining_info(179, "mareep", "gold", encounters_data=mock_encounters, generation=2)
        self.assertEqual(res_mareep["type"], "wild")
        self.assertEqual(res_mareep["badge_label"], "Salvaje / Crianza")
        self.assertIn("Guardería Pokémon", res_mareep["summary"])
        areas = [loc["area"] for loc in res_mareep["locations"]]
        self.assertIn("Ruta 32", areas)
        self.assertIn("Ruta 34 (Guardería Pokémon)", areas)

    def test_evolved_pokemon_no_breeding_gold(self):
        """Verifica que formas evolucionadas no reciban método de Crianza (los huevos eclosionan en fase base)."""
        from .utils import resolve_obtaining_info

        mock_evo_chain = {
            "chain": {
                "species": {"name": "pichu", "url": "https://pokeapi.co/api/v2/pokemon-species/172/"},
                "evolves_to": [{
                    "species": {"name": "pikachu", "url": "https://pokeapi.co/api/v2/pokemon-species/25/"},
                    "evolution_details": [{"trigger": {"name": "level-up"}, "min_happiness": 220}],
                    "evolves_to": [{
                        "species": {"name": "raichu", "url": "https://pokeapi.co/api/v2/pokemon-species/26/"},
                        "evolution_details": [{"trigger": {"name": "use-item"}, "item": {"name": "thunder-stone"}}],
                        "evolves_to": []
                    }]
                }]
            }
        }
        res_raichu = resolve_obtaining_info(26, "raichu", "gold", encounters_data=[], evolution_chain_data=mock_evo_chain, generation=2)
        self.assertEqual(res_raichu["type"], "evolution")
        self.assertEqual(res_raichu["badge_label"], "Evolución")
        self.assertNotEqual(res_raichu["badge_label"], "Crianza")
        self.assertEqual(len(res_raichu["locations"]), 0)

    def test_gen1_isolation_no_breeding(self):
        """Verifica que en 1ª Generación (Rojo/Azul/Amarillo) no exista el método de Crianza."""
        from .utils import resolve_obtaining_info

        mock_encounters = [{
            "location_area": {"name": "viridian-forest-area"},
            "version_details": [{"version": {"name": "red"}, "encounter_details": [{"method": {"name": "walk"}}]}]
        }]
        res_pikachu = resolve_obtaining_info(25, "pikachu", "red", encounters_data=mock_encounters, generation=1)
        self.assertEqual(res_pikachu["type"], "wild")
        self.assertEqual(res_pikachu["badge_label"], "Salvaje")
        self.assertNotIn("Crianza", res_pikachu["badge_label"])
        areas = [loc["area"] for loc in res_pikachu["locations"]]
        self.assertNotIn("Guardería", "".join(areas))

    def test_non_breedable_species_gold(self):
        """Verifica que especies no reproductoras (legendarios, Ditto, Unown) no tengan Crianza."""
        from .utils import resolve_obtaining_info

        # Ditto (#132)
        mock_ditto = [{
            "location_area": {"name": "johto-route-34-area"},
            "version_details": [{"version": {"name": "gold"}, "encounter_details": [{"method": {"name": "walk"}}]}]
        }]
        res_ditto = resolve_obtaining_info(132, "ditto", "gold", encounters_data=mock_ditto, generation=2)
        self.assertEqual(res_ditto["badge_label"], "Salvaje")
        self.assertNotIn("Crianza", res_ditto["badge_label"])
        methods = [loc["method"] for loc in res_ditto["locations"]]
        self.assertNotIn("Crianza de huevo", methods)

        # Lugia (#249)
        res_lugia = resolve_obtaining_info(249, "lugia", "gold", generation=2)
        self.assertEqual(res_lugia["type"], "legendary")
        self.assertNotIn("Crianza", res_lugia["badge_label"])

    def test_gen2_evolution_stones_locations_and_not_purchasable(self):
        """Verifica que en Oro las piedras no se puedan comprar y tengan ubicaciones propias de Johto/Kanto Gen 2."""
        from .utils import resolve_evolution_stone

        # Piedra Solar (introducida en Gen 2)
        sun_stone = resolve_evolution_stone(item_slug="sun-stone", game_slug="gold")
        self.assertIsNotNone(sun_stone)
        self.assertEqual(sun_stone["name"], "Piedra Solar")
        self.assertFalse(sun_stone["is_purchasable"])
        self.assertIsNone(sun_stone["price"])
        self.assertGreaterEqual(len(sun_stone["locations"]), 1)
        self.assertTrue(any("Parque Nacional" in loc["area"] for loc in sun_stone["locations"]))

        # Piedra Fuego en Oro (NO se compra en Ciudad Azulona, se obtiene con el abuelo de Bill o PokéGear)
        fire_stone = resolve_evolution_stone(item_slug="fire-stone", game_slug="gold")
        self.assertIsNotNone(fire_stone)
        self.assertFalse(fire_stone["is_purchasable"])
        self.assertIsNone(fire_stone["price"])
        areas = [loc["area"] for loc in fire_stone["locations"]]
        self.assertTrue(any("Ruta 25" in a for a in areas))
        self.assertFalse(any("Centro Comercial de Ciudad Azulona" in a for a in areas))

    def test_gen2_trade_evolution_items(self):
        """Verifica que los objetos de intercambio con objeto equipado existan con datos y ubicaciones de Oro."""
        from .utils import resolve_evolution_stone

        # Revestimiento Metálico
        metal_coat = resolve_evolution_stone(item_slug="metal-coat", game_slug="gold")
        self.assertIsNotNone(metal_coat)
        self.assertEqual(metal_coat["name"], "Revestimiento Metálico")
        self.assertFalse(metal_coat["is_purchasable"])
        areas_mc = [loc["area"] for loc in metal_coat["locations"]]
        self.assertTrue(any("S.S. Aqua" in a for a in areas_mc))

        # Roca del Rey
        kings_rock = resolve_evolution_stone(item_slug="kings-rock", game_slug="gold")
        self.assertIsNotNone(kings_rock)
        self.assertEqual(kings_rock["name"], "Roca del Rey")
        areas_kr = [loc["area"] for loc in kings_rock["locations"]]
        self.assertTrue(any("Pozo Slowpoke" in a for a in areas_kr))

        # Escama Dragón
        dragon_scale = resolve_evolution_stone(item_slug="dragon-scale", game_slug="gold")
        self.assertIsNotNone(dragon_scale)
        self.assertEqual(dragon_scale["name"], "Escama Dragón")
        areas_ds = [loc["area"] for loc in dragon_scale["locations"]]
        self.assertTrue(any("Monte Mortero" in a for a in areas_ds))

        # Mejora
        up_grade = resolve_evolution_stone(item_slug="up-grade", game_slug="gold")
        self.assertIsNotNone(up_grade)
        self.assertEqual(up_grade["name"], "Mejora")
        areas_ug = [loc["area"] for loc in up_grade["locations"]]
        self.assertTrue(any("Silph S.A." in a for a in areas_ug))

    def test_trade_evolution_obtaining_info_and_property(self):
        """Verifica que un Pokémon de evolución por intercambio equipado registre el objeto y su propiedad."""
        from .utils import resolve_obtaining_info

        mock_steelix_chain = {
            "chain": {
                "species": {"name": "onix", "url": "https://pokeapi.co/api/v2/pokemon-species/95/"},
                "evolves_to": [{
                    "species": {"name": "steelix", "url": "https://pokeapi.co/api/v2/pokemon-species/208/"},
                    "evolution_details": [{
                        "trigger": {"name": "trade"},
                        "held_item": {"name": "metal-coat"}
                    }],
                    "evolves_to": []
                }]
            }
        }
        res_steelix = resolve_obtaining_info(208, "steelix", "gold", encounters_data=[], evolution_chain_data=mock_steelix_chain, generation=2)
        evo = res_steelix.get("evolution_info", {})
        self.assertEqual(evo.get("item_slug"), "metal-coat")
        self.assertEqual(evo.get("item_name"), "Revestimiento Metálico")
        self.assertIn("Intercambio equipado con Revestimiento Metálico", evo.get("condition", ""))

        # Crear entrada en Pokédex de Oro y validar la propiedad evolution_stone
        game_gold = Game.objects.create(name="Pokémon Gold", slug="gold", generation=2)
        pokedex_gold = Pokedex.objects.create(game=game_gold, name="Pokédex de Johto", slug="johto")
        pokemon_steelix = Pokemon.objects.create(
            national_number=208,
            name="steelix",
            display_name="Steelix",
            sprite_url="https://example.com/steelix.png",
            primary_type="steel",
            secondary_type="ground"
        )
        entry_steelix = PokedexEntry.objects.create(
            pokedex=pokedex_gold,
            pokemon=pokemon_steelix,
            entry_number=63,
            obtaining_info=res_steelix
        )
        stone = entry_steelix.evolution_stone
        self.assertIsNotNone(stone)
        self.assertEqual(stone["slug"], "metal-coat")
        self.assertEqual(stone["name"], "Revestimiento Metálico")
        self.assertFalse(stone["is_purchasable"])
        self.assertTrue(any("S.S. Aqua" in loc["area"] for loc in stone["locations"]))

    def test_strict_version_isolation_for_evolution_items(self):
        """Verifica que no haya filtración de ubicaciones de objetos evolutivos entre versiones."""
        from .utils import resolve_evolution_stone

        # En Rojo, el Revestimiento Metálico no existe -> locations debe ser vacío
        metal_coat_red = resolve_evolution_stone(item_slug="metal-coat", game_slug="red")
        self.assertIsNotNone(metal_coat_red)
        self.assertEqual(len(metal_coat_red["locations"]), 0)

        # En Oro, la Piedra Trueno tiene ubicaciones de Johto/Kanto Gen 2 y ninguna de la tienda de Azulona
        thunder_stone_gold = resolve_evolution_stone(item_slug="thunder-stone", game_slug="gold")
        self.assertIsNotNone(thunder_stone_gold)
        areas = [l["area"] for l in thunder_stone_gold["locations"]]
        self.assertFalse(any("Centro Comercial de Ciudad Azulona" in a for a in areas))
        self.assertTrue(any("Ruta 25" in a for a in areas) or any("Ruta 38" in a for a in areas))

    def test_gold_version_transfers_and_time_capsule(self):
        """Verifica que en Oro y Plata se genere el contexto de 18 Pokémon a transferir vía Cápsula del Tiempo."""
        from tracker.exclusives import get_version_transfers_context, VERSION_TRANSFERS_CATALOG

        gold_game, _ = Game.objects.get_or_create(name="Pokémon Gold", slug="gold", generation=2)
        johto_dex, _ = Pokedex.objects.get_or_create(game=gold_game, name="Pokédex de Johto", slug="johto")

        transfers_nums = VERSION_TRANSFERS_CATALOG['gold']
        self.assertEqual(len(transfers_nums), 18)
        self.assertNotIn(251, transfers_nums)  # Celebi no es de transferir Gen 1

        for num in transfers_nums:
            p, _ = Pokemon.objects.get_or_create(
                national_number=num,
                defaults={"name": f"poke-{num}", "display_name": f"Poke {num}", "primary_type": "normal"}
            )
            PokedexEntry.objects.get_or_create(pokedex=johto_dex, pokemon=p, defaults={"entry_number": num})

        ctx_trans = get_version_transfers_context(gold_game, johto_dex, set())
        self.assertIsNotNone(ctx_trans)
        self.assertEqual(ctx_trans["button_label"], "Transferir")
        self.assertEqual(ctx_trans["full_button_label"], "Pokémon a Transferir")
        self.assertEqual(ctx_trans["mechanic_badge"], "Cápsula del Tiempo")
        self.assertIn("Cápsula del Tiempo", ctx_trans["description"])
        self.assertEqual(ctx_trans["total"], 18)

        # Probar vista renderizada de Oro: debe contener ambos botones
        url = reverse("tracker:pokedex_default", kwargs={"game_slug": "gold"})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "id=\"btn-exclusives\"")
        self.assertContains(response, "id=\"btn-transfers\"")
        self.assertContains(response, "id=\"transfers-modal\"")

    def test_shinydex_button_generation_exclusivity(self):
        """Verifica que el botón de Shinydex NO aparezca en Gen 1 (Rojo/Azul/Amarillo) y SÍ en Gen >= 2 (Oro)."""
        # Gen 1: Rojo
        url_red = reverse("tracker:pokedex_default", kwargs={"game_slug": "red"})
        res_red = self.client.get(url_red)
        self.assertEqual(res_red.status_code, 200)
        self.assertNotContains(res_red, "id=\"btn-toggle-shinydex\"")

        # Gen 2: Oro
        gold_game, _ = Game.objects.get_or_create(name="Pokémon Gold", slug="gold", generation=2)
        Pokedex.objects.get_or_create(game=gold_game, name="Pokédex de Johto", slug="johto")
        url_gold = reverse("tracker:pokedex_default", kwargs={"game_slug": "gold"})
        res_gold = self.client.get(url_gold)
        self.assertEqual(res_gold.status_code, 200)
        self.assertContains(res_gold, "id=\"btn-toggle-shinydex\"")
        self.assertContains(res_gold, "star-piece.png")

    def test_shinydex_server_side_cookie_rendering(self):
        """Verifica que con la cookie activa, el servidor renderiza directamente la Shinydex instantáneamente."""
        gold_game, _ = Game.objects.get_or_create(name="Pokémon Gold", slug="gold", generation=2)
        johto_dex, _ = Pokedex.objects.get_or_create(game=gold_game, name="Pokédex de Johto", slug="johto")
        p, _ = Pokemon.objects.get_or_create(national_number=152, defaults={"name": "chikorita", "display_name": "Chikorita", "primary_type": "grass"})
        PokedexEntry.objects.get_or_create(pokedex=johto_dex, pokemon=p, defaults={"entry_number": 1})

        url = reverse("tracker:pokedex_default", kwargs={"game_slug": "gold"})
        self.client.cookies["pokedex_shinydex_gold"] = "1"
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, "Progreso Shinydex")
        self.assertContains(res, "drop-shadow-[0_0_10px_rgba(245,158,11,1)]")
        self.assertContains(res, "gold_shiny/152.png")

    def test_shinydex_catch_independence(self):
        """Verifica la total independencia entre la captura normal y la captura shiny."""
        url = reverse("tracker:toggle_catch")

        # 1. Capturar normal
        res_norm = self.client.post(url, data={"entry_id": self.entry.id, "is_shiny": False}, content_type="application/json")
        self.assertEqual(res_norm.status_code, 200)
        d_norm = res_norm.json()
        self.assertTrue(d_norm["is_caught"])
        self.assertFalse(d_norm["is_shiny"])
        self.assertEqual(d_norm["caught_count"], 1)

        # Registro en BD
        catch = UserPokemonCatch.objects.get(pokedex_entry=self.entry)
        self.assertTrue(catch.is_caught)
        self.assertFalse(catch.is_shiny)

        # 2. Capturar shiny
        res_shiny = self.client.post(url, data={"entry_id": self.entry.id, "is_shiny": True}, content_type="application/json")
        self.assertEqual(res_shiny.status_code, 200)
        d_shiny = res_shiny.json()
        self.assertTrue(d_shiny["is_caught"])  # En contexto shiny, is_caught refleja catch_record.is_shiny
        self.assertTrue(d_shiny["is_shiny"])
        self.assertEqual(d_shiny["caught_count"], 1)

        # Registro en BD: ambos deben estar capturados
        catch.refresh_from_db()
        self.assertTrue(catch.is_caught)
        self.assertTrue(catch.is_shiny)

        # 3. Liberar normal (la captura shiny debe permanecer intacta)
        res_rel_norm = self.client.post(url, data={"entry_id": self.entry.id, "is_shiny": False}, content_type="application/json")
        self.assertEqual(res_rel_norm.status_code, 200)
        d_rel_norm = res_rel_norm.json()
        self.assertFalse(d_rel_norm["is_caught"])
        self.assertEqual(d_rel_norm["caught_count"], 0)

        catch.refresh_from_db()
        self.assertFalse(catch.is_caught)
        self.assertTrue(catch.is_shiny)

        # 4. Liberar shiny
        res_rel_shiny = self.client.post(url, data={"entry_id": self.entry.id, "is_shiny": True}, content_type="application/json")
        self.assertEqual(res_rel_shiny.status_code, 200)
        d_rel_shiny = res_rel_shiny.json()
        self.assertFalse(d_rel_shiny["is_caught"])
        self.assertEqual(d_rel_shiny["caught_count"], 0)

        catch.refresh_from_db()
        self.assertFalse(catch.is_caught)
        self.assertFalse(catch.is_shiny)

    def test_pokemon_and_pokedex_entry_shiny_properties(self):
        """Verifica que las propiedades de sprites shiny se generen adecuadamente."""
        self.assertIn("shiny/1.png", self.pokemon.sprite_shiny_url)
        self.assertIn("official-artwork/shiny/1.png", self.pokemon.artwork_shiny_url)
        self.assertIn("shiny/1.png", self.entry.modern_sprite_shiny_url)

        # Para juego Gen 2 Oro
        gold_game, _ = Game.objects.get_or_create(name="Pokémon Gold", slug="gold", generation=2)
        johto_dex, _ = Pokedex.objects.get_or_create(game=gold_game, name="Pokédex de Johto", slug="johto")
        entry_gold, _ = PokedexEntry.objects.get_or_create(pokedex=johto_dex, pokemon=self.pokemon, defaults={"entry_number": 1})
        self.assertTrue(
            entry_gold.game_sprite_shiny_url.endswith("/pokemon/sprites/gold_shiny/1.png") or
            "gold/shiny/1.png" in entry_gold.game_sprite_shiny_url
        )

        # modal_data_json debe incluir las claves shiny
        import json
        data = json.loads(entry_gold.modal_data_json)
        self.assertIn("sprite_retro_shiny", data)
        self.assertIn("sprite_modern_shiny", data)
        self.assertIn("is_shiny_caught", data)






