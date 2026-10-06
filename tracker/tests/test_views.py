import json
from unittest.mock import patch
from django.test import TestCase, Client
from django.urls import reverse
from tracker.models import Game, Pokedex, UserPokemonCatch
from tracker.catalog_service import CatalogPokemon, CatalogEntry, get_compiled_catalog, get_catalog_entry_by_id
from tracker.tests.mocks import MockQuerySet, MockObjects, Pokemon, PokedexEntry, Move

class PokedexTrackerTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.game, _ = Game.objects.get_or_create(slug="red", defaults={"name": "Pokémon Red", "generation": 1})
        self.pokedex, _ = Pokedex.objects.get_or_create(game=self.game, slug="kanto", defaults={"name": "Pokédex de Kanto"})
        self.pokemon = Pokemon({"national_number": 1, "name": "bulbasaur", "display_name": "Bulbasaur", "primary_type": "grass", "secondary_type": "poison"})
        self.entry = PokedexEntry({"id": 1, "entry_number": 1, "pokemon": self.pokemon, "pokedex": self.pokedex})

    def test_pokedex_view_status_and_content(self):
        url = reverse("tracker:pokedex_default", kwargs={"game_slug": "red"})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Bulbasaur")
        self.assertContains(response, "#001")
        self.assertContains(response, "Pokémon Rojo")
        self.assertContains(response, "Planta")
        self.assertEqual(response.context["total_pokemon"], 151)
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
        self.assertEqual(data["percent"], 0.7)

        # 2. Desmarcar (liberar)
        response_toggle = self.client.post(url, data=payload, content_type="application/json")
        self.assertEqual(response_toggle.status_code, 200)
        data_toggle = response_toggle.json()
        self.assertFalse(data_toggle["is_caught"])
        self.assertEqual(data_toggle["caught_count"], 0)
        self.assertEqual(data_toggle["percent"], 0.0)

    def test_localized_text_fallback(self):
        from tracker.utils import get_localized_text, resolve_game_display_name

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
        from tracker.utils import resolve_game_display_name
        from tracker.models import GAME_NAMES_ES

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

    def test_resolve_types_for_generation(self):
        from tracker.utils import resolve_types_for_generation

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
        game_gold, _ = Game.objects.get_or_create(name="Pokémon Gold", slug="gold", defaults={"generation": 2})
        Pokedex.objects.get_or_create(game=game_gold, name="Pokédex de Johto", slug="johto")
        url = reverse("tracker:pokedex_default", kwargs={"game_slug": "gold"})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'tracker/css/pokedex.css')
        self.assertContains(response, 'type-dark')
        self.assertContains(response, 'Siniestro')

    def test_resolve_flavor_text_canonical_and_fallback(self):
        from tracker.utils import resolve_flavor_text

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
        from tracker.utils import resolve_obtaining_info

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
                        "evolution_details": [{"trigger": {"name": "level-up"}, "min_level": 20, "relative_physical_stats": 1}],
                        "evolves_to": []
                    },
                    {
                        "species": {"name": "hitmonchan", "url": "https://pokeapi.co/api/v2/pokemon-species/107/"},
                        "evolution_details": [{"trigger": {"name": "level-up"}, "min_level": 20, "relative_physical_stats": -1}],
                        "evolves_to": []
                    },
                    {
                        "species": {"name": "hitmontop", "url": "https://pokeapi.co/api/v2/pokemon-species/237/"},
                        "evolution_details": [{"trigger": {"name": "level-up"}, "min_level": 20, "relative_physical_stats": 0}],
                        "evolves_to": []
                    }
                ]
            }
        }
        res_gen1_hitmonlee = resolve_obtaining_info(106, "hitmonlee", "red", evolution_chain_data=mock_tyrogue_chain, generation=1)
        self.assertEqual(res_gen1_hitmonlee["badge_label"], "Premio Dojo")
        self.assertIsNone(res_gen1_hitmonlee.get("evolution_info"))

        # En Gen 2, Tyrogue (#236 <= 251) sí es válido con condición de estadísticas
        res_gen2_hitmonlee = resolve_obtaining_info(106, "hitmonlee", "gold", evolution_chain_data=mock_tyrogue_chain, generation=2)
        self.assertIsNotNone(res_gen2_hitmonlee.get("evolution_info"))
        self.assertEqual(res_gen2_hitmonlee["evolution_info"]["from"], "Tyrogue")
        self.assertEqual(res_gen2_hitmonlee["evolution_info"]["condition"], "Nivel 20 si Ataque > Defensa")
        self.assertEqual(res_gen2_hitmonlee["evolution_info"]["text"], "Evoluciona de Tyrogue (Nivel 20 si Ataque > Defensa)")

        res_gen2_hitmonchan = resolve_obtaining_info(107, "hitmonchan", "silver", evolution_chain_data=mock_tyrogue_chain, generation=2)
        self.assertEqual(res_gen2_hitmonchan["evolution_info"]["condition"], "Nivel 20 si Defensa > Ataque")
        self.assertEqual(res_gen2_hitmonchan["evolution_info"]["text"], "Evoluciona de Tyrogue (Nivel 20 si Defensa > Ataque)")

        res_gen2_hitmontop = resolve_obtaining_info(237, "hitmontop", "silver", evolution_chain_data=mock_tyrogue_chain, generation=2)
        self.assertEqual(res_gen2_hitmontop["evolution_info"]["condition"], "Nivel 20 si Ataque = Defensa")
        self.assertEqual(res_gen2_hitmontop["evolution_info"]["text"], "Evoluciona de Tyrogue (Nivel 20 si Ataque = Defensa)")

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
        from tracker.utils import clean_location_name, resolve_encounter_method_label, resolve_obtaining_info

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

    def test_pokemon_blue_exclusives_and_obtaining(self):
        from tracker.utils import resolve_obtaining_info

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
        game_blue, _ = Game.objects.get_or_create(slug="blue", defaults={"name": "Pokémon Blue", "generation": 1})
        pokedex_blue, _ = Pokedex.objects.get_or_create(game=game_blue, slug="kanto", defaults={"name": "Pokédex de Kanto"})
        PokedexEntry.objects.create(pokedex=pokedex_blue, pokemon=self.pokemon, entry_number=1)

        url = reverse("tracker:pokedex_default", kwargs={"game_slug": "blue"})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Pokémon Azul")
        self.assertContains(response, "text-blue-500")
        self.assertContains(response, "bg-blue-600")

    def test_independent_catch_tracking_between_red_and_blue(self):
        game_blue, _ = Game.objects.get_or_create(slug="blue", defaults={"name": "Pokémon Blue", "generation": 1})
        pokedex_blue, _ = Pokedex.objects.get_or_create(game=game_blue, slug="kanto", defaults={"name": "Pokédex de Kanto"})
        entry_blue = get_compiled_catalog("blue")[0]

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




class FrontendInteractivityInvariantsTests(TestCase):
    """
    Pruebas automatizadas de no-regresión para los invariantes de interactividad temprana:
    - Preloads de módulos ES6 en <head>
    - Despachador prioritario temprano antes de la grilla de tarjetas
    - Carga asíncrona de main.js (type='module' async)
    - Exposición de funciones e interfaces prioritarias en window
    """
    def setUp(self):
        self.game = Game.objects.create(name="Pokémon Emerald", slug="emerald", generation=3)
        self.pokedex = Pokedex.objects.create(game=self.game, name="Pokédex Regional de Hoenn", slug="hoenn")

    def test_frontend_interactivity_invariants(self):
        url = reverse("tracker:pokedex_default", kwargs={"game_slug": "emerald"})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        content = response.content.decode("utf-8")

        # 1. Asegurar etiquetas modulepreload en el <head>
        self.assertIn('<link rel="modulepreload"', content)
        self.assertIn('tracker/js/main.js', content)
        self.assertIn('tracker/js/cards.js', content)
        self.assertIn('tracker/js/modal_comic.js', content)

        # 2. Asegurar que el despachador temprano esté presente antes de la grilla de tarjetas
        early_disp_pos = content.find('id="pokedex-early-dispatcher"')
        grid_pos = content.find('id="pokemon-grid"')
        self.assertNotEqual(early_disp_pos, -1, "El script 'pokedex-early-dispatcher' debe existir")
        self.assertNotEqual(grid_pos, -1, "El contenedor 'pokemon-grid' debe existir")
        self.assertLess(early_disp_pos, grid_pos, "El despachador temprano debe situarse ANTES de la grilla de tarjetas")

        # 3. Asegurar que main.js use type='module' con async
        self.assertIn('<script type="module" async', content)
        self.assertIn('tracker/js/main.js', content)

        # 4. Asegurar funciones clave expuestas inmediatamente en el despachador temprano
        self.assertIn("window.openPokemonModal =", content)
        self.assertIn("window.toggleCatch =", content)
        self.assertIn("window.__pokedexActionQueue =", content)
        self.assertIn("window.__pokedexReady =", content)




class NationalGenerationBarTests(TestCase):
    """
    Pruebas para la barra de navegación por generaciones/regiones en Pokédex Nacional:
    - No se muestra en Gen 1 (sin Pokédex Nacional).
    - No se muestra en Gen 2 (los 251 se presentan completos sin segmentar).
    - En Gen 3 Nacional se muestran exactamente Kanto, Johto y Hoenn (ocultando Sinnoh y posteriores).
    - Kanto es la región activa por defecto (renderiza 151 tarjetas).
    - Filtrado dinámico por región reduce el DOM a la generación activa (Hoenn 135 tarjetas, Johto 100).
    - El Hero Banner preserva el acumulador total (386).
    - La última región visitada se recuerda en sesión.
    """
    def setUp(self):
        # Gen 1: Red
        self.game_r = Game.objects.create(name="Pokémon Red", slug="red", generation=1)
        self.dex_r = Pokedex.objects.create(game=self.game_r, name="Pokédex de Kanto", slug="kanto", is_national=False)

        # Gen 2: Crystal
        self.game_c = Game.objects.create(name="Pokémon Crystal", slug="crystal", generation=2)
        self.dex_c_reg = Pokedex.objects.create(game=self.game_c, name="Pokédex de Johto", slug="johto", is_national=False)
        self.dex_c_nat = Pokedex.objects.create(game=self.game_c, name="Pokédex Nacional", slug="national", is_national=True)

        # Gen 3: Emerald
        self.game_e = Game.objects.create(name="Pokémon Emerald", slug="emerald", generation=3)
        self.dex_e_reg = Pokedex.objects.create(game=self.game_e, name="Pokédex Regional de Hoenn", slug="hoenn", is_national=False)
        self.dex_e_nat = Pokedex.objects.create(game=self.game_e, name="Pokédex Nacional", slug="national", is_national=True)

    def test_generation_bar_not_shown_in_gen1(self):
        resp = self.client.get(reverse("tracker:pokedex_detail", kwargs={"game_slug": "red", "pokedex_slug": "kanto"}))
        self.assertEqual(resp.status_code, 200)
        self.assertNotContains(resp, "btn-nat-gen-kanto")
        self.assertIsNone(resp.context.get("national_regions_ctx"))

    def test_generation_bar_not_shown_in_gen2(self):
        # Regional Johto
        resp_reg = self.client.get(reverse("tracker:pokedex_detail", kwargs={"game_slug": "crystal", "pokedex_slug": "johto"}))
        self.assertEqual(resp_reg.status_code, 200)
        self.assertNotContains(resp_reg, "btn-nat-gen-kanto")
        self.assertIsNone(resp_reg.context.get("national_regions_ctx"))

        # Nacional Johto (Modo Antiguo 251)
        resp_nat = self.client.get(reverse("tracker:pokedex_detail", kwargs={"game_slug": "crystal", "pokedex_slug": "national"}))
        self.assertEqual(resp_nat.status_code, 200)
        self.assertNotContains(resp_nat, "btn-nat-gen-kanto")
        self.assertIsNone(resp_nat.context.get("national_regions_ctx"))

    def test_generation_bar_not_shown_in_gen3_regional(self):
        resp = self.client.get(reverse("tracker:pokedex_detail", kwargs={"game_slug": "emerald", "pokedex_slug": "hoenn"}))
        self.assertEqual(resp.status_code, 200)
        self.assertNotContains(resp, "btn-nat-gen-kanto")
        self.assertIsNone(resp.context.get("national_regions_ctx"))

    def test_generation_bar_in_gen3_national_default_kanto(self):
        resp = self.client.get(reverse("tracker:pokedex_detail", kwargs={"game_slug": "emerald", "pokedex_slug": "national"}))
        self.assertEqual(resp.status_code, 200)

        # 1. La barra contiene exactamente Kanto, Johto y Hoenn
        self.assertContains(resp, "btn-nat-gen-kanto")
        self.assertContains(resp, "btn-nat-gen-johto")
        self.assertContains(resp, "btn-nat-gen-hoenn")
        # Generaciones posteriores NO existen en este cartucho
        self.assertNotContains(resp, "btn-nat-gen-sinnoh")
        self.assertNotContains(resp, "btn-nat-gen-unova")
        self.assertNotContains(resp, "btn-nat-gen-paldea")

        # 2. Región activa por defecto es Kanto (#1..151)
        ctx = resp.context["national_regions_ctx"]
        self.assertEqual(ctx["active_slug"], "kanto")
        self.assertEqual(len(resp.context["entries"]), 151)
        self.assertEqual(resp.context["entries"][0].pokemon.national_number, 1)
        self.assertEqual(resp.context["entries"][-1].pokemon.national_number, 151)

        # 3. El total global del Hero Banner sigue siendo 386
        self.assertEqual(resp.context["total_pokemon"], 386)

    def test_generation_bar_in_gen3_national_hoenn_filter(self):
        resp = self.client.get(reverse("tracker:pokedex_detail", kwargs={"game_slug": "emerald", "pokedex_slug": "national"}) + "?gen=hoenn")
        self.assertEqual(resp.status_code, 200)

        ctx = resp.context["national_regions_ctx"]
        self.assertEqual(ctx["active_slug"], "hoenn")
        # Exactamente 135 especies de Hoenn (252 Treecko a 386 Deoxys)
        self.assertEqual(len(resp.context["entries"]), 135)
        self.assertEqual(resp.context["entries"][0].pokemon.national_number, 252)
        self.assertEqual(resp.context["entries"][-1].pokemon.national_number, 386)
        self.assertEqual(resp.context["total_pokemon"], 386)

    def test_generation_bar_in_gen3_national_johto_filter(self):
        resp = self.client.get(reverse("tracker:pokedex_detail", kwargs={"game_slug": "emerald", "pokedex_slug": "national"}) + "?gen=johto")
        self.assertEqual(resp.status_code, 200)

        ctx = resp.context["national_regions_ctx"]
        self.assertEqual(ctx["active_slug"], "johto")
        # Exactamente 100 especies de Johto (152 Chikorita a 251 Celebi)
        self.assertEqual(len(resp.context["entries"]), 100)
        self.assertEqual(resp.context["entries"][0].pokemon.national_number, 152)
        self.assertEqual(resp.context["entries"][-1].pokemon.national_number, 251)
        self.assertEqual(resp.context["total_pokemon"], 386)

    def test_generation_bar_session_persistence(self):
        # 1. Visitar con gen=hoenn
        self.client.get(reverse("tracker:pokedex_detail", kwargs={"game_slug": "emerald", "pokedex_slug": "national"}) + "?gen=hoenn")

        # 2. Visitar sin parámetro: recuerda 'hoenn' desde sesión
        resp = self.client.get(reverse("tracker:pokedex_detail", kwargs={"game_slug": "emerald", "pokedex_slug": "national"}))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.context["national_regions_ctx"]["active_slug"], "hoenn")
        self.assertEqual(len(resp.context["entries"]), 135)

    def test_generation_bar_partial_grid_ajax(self):
        url = reverse("tracker:pokedex_detail", kwargs={"game_slug": "emerald", "pokedex_slug": "national"}) + "?gen=hoenn"
        resp = self.client.get(url, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp["X-Active-Slug"], "hoenn")
        self.assertTemplateUsed(resp, "tracker/components/_pokemon_grid_partial.html")
        self.assertNotContains(resp, "<!DOCTYPE html>")
        self.assertNotContains(resp, "<footer")
        self.assertContains(resp, "Treecko")
        self.assertContains(resp, "Deoxys")
        self.assertNotContains(resp, "Bulbasaur")

    def test_generation_bar_partial_grid_query_param(self):
        url = reverse("tracker:pokedex_detail", kwargs={"game_slug": "emerald", "pokedex_slug": "national"}) + "?gen=johto&partial=grid"
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp["X-Active-Slug"], "johto")
        self.assertTemplateUsed(resp, "tracker/components/_pokemon_grid_partial.html")
        self.assertNotContains(resp, "<!DOCTYPE html>")
        self.assertContains(resp, "Chikorita")
        self.assertContains(resp, "Celebi")
        self.assertNotContains(resp, "Treecko")
        self.assertNotContains(resp, "Bulbasaur")

    def test_transfers_modal_has_embedded_entry_data_regardless_of_active_region(self):
        # En Esmeralda Pokédex Nacional, solicitamos la pestaña de Hoenn
        url = reverse("tracker:pokedex_detail", kwargs={"game_slug": "emerald", "pokedex_slug": "national"}) + "?gen=hoenn"
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        # La grilla activa sólo tiene Hoenn (Treecko), no tiene Bulbasaur en la grilla principal
        self.assertContains(resp, 'id="transfers-modal"')
        # El modal de transferir incluye especies de Kanto (ej. Bulbasaur #1) con su script de datos
        transfers_info = resp.context.get("transfers_info")
        self.assertIsNotNone(transfers_info)
        self.assertTrue(transfers_info["has_transfers"])
        first_transfer = transfers_info["transfer_list"][0]
        self.assertIsNotNone(first_transfer["entry_id"])
        self.assertContains(resp, f'id="entry-data-{first_transfer["entry_id"]}"')



