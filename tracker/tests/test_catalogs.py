import json
import os
from unittest.mock import patch
from django.test import TestCase, Client
from django.urls import reverse
from tracker.models import Game, Pokedex, UserPokemonCatch
from tracker.catalog_service import CatalogPokemon, CatalogEntry, get_compiled_catalog, get_catalog_entry_by_id
from tracker.tests.mocks import MockQuerySet, MockObjects, Pokemon, PokedexEntry, Move

class CompiledCatalogsAndServiceTests(TestCase):
    """Pruebas unitarias para los catálogos JSON estáticos compilados (Plan B) y CatalogService."""

    def test_all_game_catalogs_exist_and_load(self):
        from tracker.catalog_service import get_compiled_catalog, CATALOGS_DIR
        
        expected_counts = {
            "red": 151,
            "blue": 151,
            "yellow": 151,
            "gold": 251,
            "silver": 251,
            "crystal": 251,
        }
        
        for slug, count in expected_counts.items():
            catalog_file = CATALOGS_DIR / f"{slug}.json"
            self.assertTrue(catalog_file.exists(), f"El archivo de catálogo {slug}.json no existe.")
            
            entries = get_compiled_catalog(slug, force_reload=True)
            self.assertIsNotNone(entries, f"El catálogo compilado para {slug} devolvió None.")
            self.assertEqual(len(entries), count, f"El catálogo de {slug} esperaba {count} entradas, obtuvo {len(entries)}.")
            
            # Verificar primera entrada
            first = entries[0]
            self.assertEqual(first.entry_number, 1)
            expected_starter = "Bulbasaur" if slug in ["red", "blue", "yellow"] else "Chikorita"
            self.assertEqual(first.pokemon.display_name, expected_starter)
            self.assertIsNotNone(first.primary_type_display)
            self.assertIsNotNone(first.modal_data_json)
            self.assertIn(expected_starter, first.modal_data_json)
            
            # Verificar compatibilidad de métodos de íconos en CatalogPokemon
            self.assertTrue(hasattr(first.pokemon, "get_pc_icon_url"))
            self.assertTrue(hasattr(first.pokemon, "get_classic_icon_url"))
            self.assertIsInstance(first.pokemon.get_pc_icon_url(1), str)

    def test_national_catalog_order_and_numbering(self):
        """Verifica que el catálogo nacional de Gen 2 (Gold, Silver, Crystal) ordene de 1 a 251 por número nacional."""
        from tracker.catalog_service import get_compiled_catalog

        for slug in ["gold", "silver", "crystal"]:
            reg_entries = get_compiled_catalog(slug, is_national=False)
            nat_entries = get_compiled_catalog(slug, is_national=True)

            self.assertEqual(len(reg_entries), 251)
            self.assertEqual(len(nat_entries), 251)

            # En modo regional (Johto), la 1ª entrada es Chikorita (#001)
            self.assertEqual(reg_entries[0].entry_number, 1)
            self.assertEqual(reg_entries[0].pokemon.name, "chikorita")

            # En modo nacional, la 1ª entrada es Bulbasaur (#001) y la 152ª es Chikorita (#152)
            self.assertEqual(nat_entries[0].entry_number, 1)
            self.assertEqual(nat_entries[0].pokemon.name, "bulbasaur")
            self.assertEqual(nat_entries[151].entry_number, 152)
            self.assertEqual(nat_entries[151].pokemon.name, "chikorita")
            self.assertEqual(nat_entries[-1].entry_number, 251)
            self.assertEqual(nat_entries[-1].pokemon.name, "celebi")

            # Verificar que los números son estrictamente consecutivos del 1 al 251
            entry_nums = [e.entry_number for e in nat_entries]
            self.assertEqual(entry_nums, list(range(1, 252)))

    def test_nonexistent_catalog_returns_none(self):
        from tracker.catalog_service import get_compiled_catalog
        self.assertIsNone(get_compiled_catalog("black"))
        self.assertIsNone(get_compiled_catalog("invalid_slug"))

    def test_catalog_filter_locations_and_tags(self):
        from tracker.catalog_service import get_compiled_catalog
        
        # Test Red Catalog
        red_cat = get_compiled_catalog("red")
        
        # Starters tag in Red
        bulbasaur = next(e for e in red_cat if e.entry_number == 1)
        self.assertIn("starter", bulbasaur.filter_tags)
        
        # Charizard should also have starter tag (evolution)
        charizard = next(e for e in red_cat if e.entry_number == 6)
        self.assertIn("starter", charizard.filter_tags)
        
        # Legendaries in Red
        mewtwo = next(e for e in red_cat if e.entry_number == 150)
        self.assertIn("legendary", mewtwo.filter_tags)
        self.assertIn("cueva celeste", mewtwo.filter_locations.lower())
        
        # Route 1 in Red
        pidgey = next(e for e in red_cat if e.entry_number == 16)
        rattata = next(e for e in red_cat if e.entry_number == 19)
        self.assertIn("ruta 1", pidgey.filter_locations.lower())
        self.assertIn("ruta 1", rattata.filter_locations.lower())
        
        # Fishing in Red (Magikarp has old rod)
        magikarp = next(e for e in red_cat if e.entry_number == 129)
        self.assertIn("rod_old", magikarp.filter_tags)
        self.assertIn("rod_any", magikarp.filter_tags)

        # Daycare route exclusion in filter_locations (only wild Pokemon match route name)
        ruby_cat = get_compiled_catalog("ruby")
        treecko = next(e for e in ruby_cat if e.pokemon.name == "treecko")
        zigzagoon = next(e for e in ruby_cat if e.pokemon.name == "zigzagoon")
        self.assertNotIn("ruta 117", treecko.filter_locations.lower())
        self.assertIn("guardería", treecko.filter_locations.lower())
        self.assertIn("ruta 117", zigzagoon.filter_locations.lower())

        # Modal data for Treecko still keeps the daycare route
        treecko_modal = json.loads(treecko.modal_data_json)
        self.assertTrue(any("117" in loc.get("area", "") for loc in treecko_modal.get("obtaining", {}).get("locations", [])))

        # Manaphy vs Phione (Manaphy no es obtenible por crianza en guardería, Phione sí)
        diamond_cat = get_compiled_catalog("diamond", is_national=True)
        manaphy = next(e for e in diamond_cat if e.pokemon.name == "manaphy")
        phione = next(e for e in diamond_cat if e.pokemon.name == "phione")
        self.assertNotIn("guardería", manaphy.filter_locations.lower())
        self.assertNotIn("guarderia", manaphy.filter_locations.lower())
        self.assertIn("ranger net", manaphy.filter_locations.lower())
        self.assertIn("guardería", phione.filter_locations.lower())
        
        # Test Crystal Catalog (Headbutt, Surf)
        crystal_cat = get_compiled_catalog("crystal")
        heracross = next(e for e in crystal_cat if e.pokemon.display_name == "Heracross")
        self.assertIn("headbutt", heracross.filter_tags)
        
        quagsire = next(e for e in crystal_cat if e.pokemon.display_name == "Quagsire")
        self.assertIn("surf", quagsire.filter_tags)

        # Fósiles en Red
        omanyte = next(e for e in red_cat if e.entry_number == 138)
        omastar = next(e for e in red_cat if e.entry_number == 139)
        self.assertIn("fossil", omanyte.filter_tags)
        self.assertIn("fossil", omastar.filter_tags)

        # Evolución por piedra en Red
        raichu = next(e for e in red_cat if e.entry_number == 26)
        pikachu = next(e for e in red_cat if e.entry_number == 25)
        self.assertIn("stone", raichu.filter_tags)
        self.assertIn("stone", pikachu.filter_tags)

        # Evolución por intercambio en Red
        alakazam = next(e for e in red_cat if e.entry_number == 65)
        kadabra = next(e for e in red_cat if e.entry_number == 64)
        self.assertIn("trade", alakazam.filter_tags)
        self.assertIn("trade", kadabra.filter_tags)

        # Bebés y amistad en Crystal (Gen 2) vs Red (Gen 1)
        pichu_c = next(e for e in crystal_cat if e.pokemon.name == "pichu")
        self.assertIn("baby", pichu_c.filter_tags)
        self.assertIn("friendship", pichu_c.filter_tags)

        crobat_c = next(e for e in crystal_cat if e.pokemon.name == "crobat")
        self.assertIn("friendship", crobat_c.filter_tags)

        # En Gen 1 no hay bebés ni amistad
        pikachu_red = next(e for e in red_cat if e.entry_number == 25)
        self.assertNotIn("baby", pikachu_red.filter_tags)
        self.assertNotIn("friendship", pikachu_red.filter_tags)

        # Zona Safari en Red vs Crystal
        chansey_red = next(e for e in red_cat if e.entry_number == 113)
        self.assertIn("safari", chansey_red.filter_tags)

        chansey_c = next(e for e in crystal_cat if e.pokemon.name == "chansey")
        self.assertNotIn("safari", chansey_c.filter_tags)


class PokemonRubyGen3Tests(TestCase):
    def setUp(self):
        self.client = Client()
        self.game, _ = Game.objects.get_or_create(slug="ruby", defaults={"name": "Pokémon Rubí", "generation": 3})
        self.pokedex_hoenn, _ = Pokedex.objects.get_or_create(game=self.game, slug="hoenn", defaults={"name": "Pokédex Regional de Hoenn", "is_national": False})
        self.pokedex_national, _ = Pokedex.objects.get_or_create(game=self.game, slug="national", defaults={"name": "Pokédex Nacional", "is_national": True})

    def test_ruby_catalogs_structure(self):
        # 1. Catálogo regional de Hoenn: exactamente 202 Pokémon (#001 Treecko a #202 Deoxys)
        hoenn_cat = get_compiled_catalog("ruby", is_national=False)
        self.assertIsNotNone(hoenn_cat)
        self.assertEqual(len(hoenn_cat), 202)
        self.assertEqual(hoenn_cat[0].entry_number, 1)
        self.assertEqual(hoenn_cat[0].pokemon.name, "treecko")
        self.assertEqual(hoenn_cat[-1].entry_number, 202)
        self.assertEqual(hoenn_cat[-1].pokemon.name, "deoxys")

        # 2. Catálogo Nacional de Rubí: exactamente 386 Pokémon (#001 Bulbasaur a #386 Deoxys)
        nat_cat = get_compiled_catalog("ruby", is_national=True)
        self.assertIsNotNone(nat_cat)
        self.assertEqual(len(nat_cat), 386)
        self.assertEqual(nat_cat[0].entry_number, 1)
        self.assertEqual(nat_cat[0].pokemon.name, "bulbasaur")
        self.assertEqual(nat_cat[-1].entry_number, 386)
        self.assertEqual(nat_cat[-1].pokemon.name, "deoxys")

        # 3. Paridad de ID entre Regional y Nacional para sincronización de capturas
        treecko_h = next(e for e in hoenn_cat if e.pokemon.name == "treecko")
        treecko_n = next(e for e in nat_cat if e.pokemon.name == "treecko")
        self.assertEqual(treecko_h.id, treecko_n.id)

        # 4. En todas las Pokédex el Unown predeterminado siempre es la forma F
        unown_n = next(e for e in nat_cat if e.pokemon.national_number == 201)
        self.assertEqual(unown_n.game_sprite_url, "/media/pokemon/sprites/ruby/201.png")
        self.assertIn("201-f.png", unown_n.pokemon.sprite_shiny_url)
        self.assertIn("201-f.png", unown_n.pokemon.artwork_shiny_url)

    def test_ruby_views_and_theme(self):
        # Vista regional de Hoenn (/ruby/ o /ruby/hoenn/)
        resp_hoenn = self.client.get(reverse("tracker:pokedex_detail", kwargs={"game_slug": "ruby", "pokedex_slug": "hoenn"}))
        self.assertEqual(resp_hoenn.status_code, 200)
        self.assertContains(resp_hoenn, "Pokédex Regional de Hoenn")
        self.assertContains(resp_hoenn, "Hoenn")
        self.assertEqual(len(resp_hoenn.context["entries"]), 202)

        # Vista nacional (/ruby/national/)
        resp_nat = self.client.get(reverse("tracker:pokedex_detail", kwargs={"game_slug": "ruby", "pokedex_slug": "national"}))
        self.assertEqual(resp_nat.status_code, 200)
        self.assertContains(resp_nat, "Pokédex Nacional")
        self.assertEqual(resp_nat.context["total_pokemon"], 386)
        self.assertEqual(len(resp_nat.context["entries"]), 151)  # Kanto por defecto en barra de generaciones

    def test_ruby_exclusives_and_transfers(self):
        from tracker.exclusives import get_version_exclusives_context, get_version_transfers_context
        # Exclusivos de Rubí vs Zafiro
        excl_ctx = get_version_exclusives_context(self.game, self.pokedex_hoenn, set())
        self.assertIsNotNone(excl_ctx)
        self.assertTrue(excl_ctx["has_exclusives"])
        self.assertEqual(excl_ctx["counterpart_short_name"], "Zafiro")

        # En la Pokédex Regional de Hoenn no hay botón de transferencias externas
        transfers_hoenn = get_version_transfers_context(self.game, self.pokedex_hoenn, set())
        self.assertIsNone(transfers_hoenn)

        # En la Pokédex Nacional existen 184 especies a transferir
        transfers_nat = get_version_transfers_context(self.game, self.pokedex_national, set())
        self.assertIsNotNone(transfers_nat)
        self.assertEqual(transfers_nat["total"], 184)
        self.assertIn("1.ª y 2.ª Generación", transfers_nat["incompatible_warning"])

    def test_ruby_evolution_stones_and_items(self):
        from tracker.utils import resolve_evolution_stone
        # Piedras evolutivas en Rubí
        water = resolve_evolution_stone("water-stone", game_slug="ruby")
        self.assertIsNotNone(water)
        self.assertEqual(water["name"], "Piedra Agua")
        self.assertTrue(any("Naufragio" in loc["area"] for loc in water["locations"]))

        # Objetos de evolución por intercambio en Rubí (Diente Marino entregado en Ciudad Portual con Escáner del Naufragio)
        deep_sea_tooth = resolve_evolution_stone("deep-sea-tooth", game_slug="ruby")
        self.assertIsNotNone(deep_sea_tooth)
        self.assertEqual(deep_sea_tooth["name"], "Diente Marino")
        self.assertTrue(any("Portual" in loc["area"] or "Naufragio" in loc.get("detail", "") for loc in deep_sea_tooth["locations"]))

    def test_ruby_corrections_filters(self):
        # 1. Filtro Golpe Cabeza no debe estar presente en Rubí (solo en 2ª Gen)
        resp_hoenn = self.client.get(reverse("tracker:pokedex_detail", kwargs={"game_slug": "ruby", "pokedex_slug": "hoenn"}))
        self.assertNotContains(resp_hoenn, "Golpe Cabeza")

        hoenn_cat = get_compiled_catalog("ruby", is_national=False)
        pika = next(e for e in hoenn_cat if e.pokemon.national_number == 25)
        raichu = next(e for e in hoenn_cat if e.pokemon.national_number == 26)
        roselia = next(e for e in hoenn_cat if e.pokemon.name == "roselia")
        chimecho = next(e for e in hoenn_cat if e.pokemon.name == "chimecho")
        latias = next(e for e in hoenn_cat if e.pokemon.name == "latias")
        kyogre = next(e for e in hoenn_cat if e.pokemon.name == "kyogre")

        # 2. Pikachu y Raichu no son iniciales
        self.assertNotIn("starter", pika.filter_tags.split())
        self.assertNotIn("starter", raichu.filter_tags.split())

        # 3. Roselia y Chimecho no tienen evolución por amistad en Gen 3
        self.assertNotIn("friendship", roselia.filter_tags.split())
        self.assertNotIn("friendship", chimecho.filter_tags.split())

        # 4. Latias y Kyogre aparecen con etiqueta legendary
        self.assertIn("legendary", latias.filter_tags.split())
        self.assertIn("legendary", kyogre.filter_tags.split())

    def test_unown_gen3_28_forms(self):
        from tracker.unown_data import get_unown_catalog
        unown_ruby = get_unown_catalog("ruby")
        self.assertEqual(len(unown_ruby), 28)
        letters = [u["letter"] for u in unown_ruby]
        self.assertIn("exclamation", letters)
        self.assertIn("question", letters)

        # 1. En Gen 3 los sprites deben apuntar a la ruta de sprites de batalla y no a los iconos de menú
        for form in unown_ruby:
            l = form["letter"]
            self.assertEqual(form["sprite_normal"], f"/media/pokemon/sprites/ruby/unown/{l}.png")
            self.assertEqual(form["sprite_shiny"], f"/media/pokemon/sprites/ruby_shiny/unown/{l}.png")
            self.assertNotIn("/icons/", form["sprite_normal"])

        # 2. En la vista de Rubí, las pestañas de Ruinas Alfa y cámaras no deben mostrarse
        resp_nat = self.client.get(reverse("tracker:pokedex_detail", kwargs={"game_slug": "ruby", "pokedex_slug": "national"}))
        self.assertEqual(resp_nat.status_code, 200)
        self.assertFalse(resp_nat.context["is_johto"])
        self.assertEqual(resp_nat.context["unown_total_forms"], 28)
        self.assertNotContains(resp_nat, 'id="unown-tab-kabuto"')
        self.assertNotContains(resp_nat, 'Cámara Kabuto')
        self.assertNotContains(resp_nat, 'id="unown-chamber-hint"')

        # 3. Toggle de formas especiales (!) y (?) en Gen 3
        unown_entry = resp_nat.context["unown_entry"]
        resp_toggle = self.client.post(
            reverse("tracker:toggle_unown_catch"),
            data=json.dumps({"entry_id": unown_entry.id, "letter": "exclamation", "is_shiny": False}),
            content_type="application/json"
        )
        self.assertEqual(resp_toggle.status_code, 200)
        data = resp_toggle.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["unown_total_forms"], 28)
        self.assertEqual(data["unown_normal_count"], 1)

    def test_incenses_and_breeding_obtaining_methods(self):
        """
        Valida que los inciensos especiales (Incienso Marino, Incienso Suave) se resuelvan
        como objetos estructurados (icono, localizaciones, categoría), y que Pokémon como
        Azurill, Wynaut, Pichu, Igglybuff, Scyther y Pinsir tengan métodos de obtención
        completos por crianza, concurso o regalo en vez de textos genéricos.
        """
        from tracker.utils import resolve_evolution_stone, get_evolution_stones_catalog
        from tracker.catalog_service import get_compiled_catalog

        # 1. Resolver Incienso Marino
        sea_incense = resolve_evolution_stone("sea-incense", game_slug="ruby")
        self.assertIsNotNone(sea_incense)
        self.assertEqual(sea_incense["name"], "Incienso Marino")
        self.assertEqual(sea_incense["category"], "incense")
        self.assertEqual(sea_incense["icon_url"], "/media/items/sea-incense.png")
        self.assertTrue(any("Monte Pírico" in loc["area"] for loc in sea_incense["locations"]))

        # 2. Resolver Incienso Suave
        lax_incense = resolve_evolution_stone("lax-incense", game_slug="ruby")
        self.assertIsNotNone(lax_incense)
        self.assertEqual(lax_incense["name"], "Incienso Suave")
        self.assertEqual(lax_incense["category"], "incense")
        self.assertEqual(lax_incense["icon_url"], "/media/items/lax-incense.png")
        self.assertTrue(any("Monte Pírico" in loc["area"] for loc in lax_incense["locations"]))

        # 3. Validar Azurill (#298) en Rubí
        ruby_entries = get_compiled_catalog("ruby", is_national=False)
        azurill = next(e for e in ruby_entries if e.pokemon.national_number == 298)
        self.assertEqual(azurill.obtaining_info["type"], "breeding")
        self.assertIn("Incienso Marino", azurill.obtaining_info["summary"])
        self.assertIn("Ruta 117", azurill.obtaining_info["summary"])
        self.assertIsNotNone(azurill.evolution_stone)
        self.assertEqual(azurill.evolution_stone["slug"], "sea-incense")
        self.assertEqual(azurill.evolution_stone["name"], "Incienso Marino")

        # 4. Validar Wynaut (#360) en Rubí
        wynaut = next(e for e in ruby_entries if e.pokemon.national_number == 360)
        self.assertIn("Pueblo Lavacalda", wynaut.obtaining_info["summary"])
        self.assertIn("Incienso Suave", wynaut.obtaining_info["summary"])
        self.assertIsNotNone(wynaut.evolution_stone)
        self.assertEqual(wynaut.evolution_stone["slug"], "lax-incense")

        # 5. Validar Pichu (#172) e Igglybuff (#174) en Rubí
        pichu = next(e for e in ruby_entries if e.pokemon.national_number == 172)
        igglybuff = next(e for e in ruby_entries if e.pokemon.national_number == 174)
        self.assertEqual(pichu.obtaining_info["type"], "breeding")
        self.assertIn("Ruta 117", pichu.obtaining_info["summary"])
        self.assertEqual(igglybuff.obtaining_info["type"], "breeding")
        self.assertIn("Ruta 117", igglybuff.obtaining_info["summary"])

        # 6. Validar Scyther (#123) y Pinsir (#127) en Cristal
        crystal_entries = get_compiled_catalog("crystal", is_national=False)
        scyther = next(e for e in crystal_entries if e.pokemon.national_number == 123)
        pinsir = next(e for e in crystal_entries if e.pokemon.national_number == 127)
        self.assertEqual(scyther.obtaining_info["type"], "contest")
        self.assertIn("Concurso de Captura de Bichos", scyther.obtaining_info["summary"])
        self.assertEqual(pinsir.obtaining_info["type"], "contest")
        self.assertIn("Concurso de Captura de Bichos", pinsir.obtaining_info["summary"])

    def test_pokemon_alternate_forms(self):
        """Valida que Castform (#351) y Unown (#201) cuenten con formas alternativas configuradas correctamente."""
        from tracker.catalog_service import get_compiled_catalog
        import json

        # 1. Castform en Pokédex Regional de Rubí
        ruby_entries = get_compiled_catalog("ruby", is_national=False)
        castform = next(e for e in ruby_entries if e.pokemon.national_number == 351)
        self.assertEqual(len(castform.forms), 4)
        
        # Validar claves y tipos de las formas de Castform
        form_keys = [f["form_key"] for f in castform.forms]
        self.assertEqual(form_keys, ["normal", "sunny", "rainy", "snowy"])
        
        types_map = {f["form_key"]: f["primary_type_es"] for f in castform.forms}
        self.assertEqual(types_map["normal"], "Normal")
        self.assertEqual(types_map["sunny"], "Fuego")
        self.assertEqual(types_map["rainy"], "Agua")
        self.assertEqual(types_map["snowy"], "Hielo")

        # Validar presencia de sprites en las formas de Castform
        self.assertIn("castform/sunny.png", castform.forms[1]["sprite_retro"])
        self.assertIn("castform/sunny.png", castform.forms[1]["sprite_retro_shiny"])

        # Validar serialización en modal_data_json
        modal_json = json.loads(castform.modal_data_json)
        self.assertIn("forms", modal_json)
        self.assertEqual(len(modal_json["forms"]), 4)

        # 2. Unown en Pokédex Nacional de Rubí
        ruby_national = get_compiled_catalog("ruby", is_national=True)
        unown = next(e for e in ruby_national if e.pokemon.national_number == 201)
        self.assertEqual(len(unown.forms), 28)
        self.assertEqual(unown.forms[0]["name"], "Unown [A]")
        self.assertEqual(unown.forms[-2]["name"], "Unown [!]")
        self.assertEqual(unown.forms[-1]["name"], "Unown [?]")

        # 3. Pokémon sin formas alternativas (ej: Deoxys, Pikachu, Groudon)
        deoxys = next(e for e in ruby_national if e.pokemon.national_number == 386)
        groudon = next(e for e in ruby_entries if e.pokemon.national_number == 383)
        self.assertEqual(len(deoxys.forms), 0)
        self.assertEqual(len(groudon.forms), 0)

    def test_back_sprites_catalog_and_modal_json(self):
        """Valida que las entradas de catálogo y modales expongan las rutas de sprites de espalda."""
        # 1. Gen 1 (Rojo): Sin shiny pero con espalda
        red_entries = get_compiled_catalog("red")
        bulbasaur = next(e for e in red_entries if e.entry_number == 1)
        self.assertIn("/media/pokemon/sprites/red/back/1.png", bulbasaur.game_sprite_back_url)
        self.assertFalse(bulbasaur.game_sprite_shiny_back_url)

        red_modal = json.loads(bulbasaur.modal_data_json)
        self.assertIn("sprite_retro_back", red_modal)
        self.assertEqual(red_modal["sprite_retro_back"], bulbasaur.game_sprite_back_url)

        # 2. Gen 3 (Rubí): Con espalda normal y shiny
        ruby_entries = get_compiled_catalog("ruby")
        torchic = next(e for e in ruby_entries if e.pokemon.national_number == 255)
        self.assertIn("/media/pokemon/sprites/ruby/back/255.png", torchic.game_sprite_back_url)
        self.assertIn("/media/pokemon/sprites/ruby_shiny/back/255.png", torchic.game_sprite_shiny_back_url)

        ruby_modal = json.loads(torchic.modal_data_json)
        self.assertEqual(ruby_modal["sprite_retro_back"], torchic.game_sprite_back_url)
        self.assertEqual(ruby_modal["sprite_retro_shiny_back"], torchic.game_sprite_shiny_back_url)

        # 3. Formas alternas con espalda (Castform)
        castform = next(e for e in ruby_entries if e.pokemon.national_number == 351)
        for form in castform.forms:
            self.assertIn("sprite_retro_back", form)
            self.assertIn("sprite_retro_shiny_back", form)
            self.assertIn("/back/", form["sprite_retro_back"])
            self.assertIn("/back/", form["sprite_retro_shiny_back"])










class PokemonSapphireGen3Tests(TestCase):
    def setUp(self):
        self.game, _ = Game.objects.get_or_create(slug="sapphire", defaults={"name": "Pokémon Zafiro", "generation": 3})
        self.pokedex_hoenn, _ = Pokedex.objects.get_or_create(game=self.game, slug="hoenn", defaults={"name": "Pokédex Regional de Hoenn", "is_national": False})
        self.pokedex_nat, _ = Pokedex.objects.get_or_create(game=self.game, slug="national", defaults={"name": "Pokédex Nacional", "is_national": True})

    def test_sapphire_catalogs_structure(self):
        """Valida que los catálogos compilados de Zafiro se carguen con sus 202 y 386 entradas y orden canónico."""
        hoenn_cat = get_compiled_catalog("sapphire", is_national=False)
        self.assertIsNotNone(hoenn_cat)
        self.assertEqual(len(hoenn_cat), 202)
        self.assertEqual(hoenn_cat[0].pokemon.name, "treecko")
        self.assertEqual(hoenn_cat[0].entry_number, 1)

        kyogre = next(e for e in hoenn_cat if e.pokemon.name == "kyogre")
        self.assertEqual(kyogre.entry_number, 198)
        self.assertEqual(kyogre.obtaining_info["type"], "legendary")
        self.assertIn("Cueva del Origen", kyogre.obtaining_info["summary"])

        nat_cat = get_compiled_catalog("sapphire", is_national=True)
        self.assertIsNotNone(nat_cat)
        self.assertEqual(len(nat_cat), 386)
        self.assertEqual(nat_cat[0].pokemon.name, "bulbasaur")
        self.assertEqual(nat_cat[385].pokemon.name, "deoxys")

    def test_sapphire_views_and_theme(self):
        """Verifica que las vistas de Pokédex regional y nacional respondan correctamente en Zafiro."""
        resp_hoenn = self.client.get(reverse("tracker:pokedex_detail", kwargs={"game_slug": "sapphire", "pokedex_slug": "hoenn"}))
        self.assertEqual(resp_hoenn.status_code, 200)
        self.assertContains(resp_hoenn, "Pokédex Regional de Hoenn")

        resp_nat = self.client.get(reverse("tracker:pokedex_detail", kwargs={"game_slug": "sapphire", "pokedex_slug": "national"}))
        self.assertEqual(resp_nat.status_code, 200)
        self.assertContains(resp_nat, "Pokédex Nacional")

    def test_sapphire_exclusives_and_transfers(self):
        """Comprueba que los exclusivos propios de Zafiro y los de Rubí se resuelvan con fidelidad canónica."""
        from tracker.exclusives import get_version_exclusives_context, get_version_transfers_context
        excl_ctx = get_version_exclusives_context(self.game, self.pokedex_hoenn, set())
        self.assertIsNotNone(excl_ctx)
        self.assertEqual(excl_ctx["counterpart_slug"], "ruby")

        own_names = {p["name"] for p in excl_ctx["own_list"]}
        self.assertIn("Lotad", own_names)
        self.assertIn("Lombre", own_names)
        self.assertIn("Ludicolo", own_names)
        self.assertIn("Sableye", own_names)
        self.assertIn("Seviper", own_names)
        self.assertIn("Lunatone", own_names)
        self.assertIn("Kyogre", own_names)
        self.assertIn("Latias", own_names)

        counterpart_names = {p["name"] for p in excl_ctx["counterpart_list"]}
        self.assertIn("Seedot", counterpart_names)
        self.assertIn("Mawile", counterpart_names)
        self.assertIn("Zangoose", counterpart_names)
        self.assertIn("Solrock", counterpart_names)
        self.assertIn("Groudon", counterpart_names)
        self.assertIn("Latios", counterpart_names)

        transfers_ctx = get_version_transfers_context(self.game, self.pokedex_nat, set())
        self.assertIsNotNone(transfers_ctx)
        self.assertEqual(transfers_ctx["total"], 184)


class PokemonEmeraldGen3Tests(TestCase):
    def setUp(self):
        self.game, _ = Game.objects.get_or_create(slug="emerald", defaults={"name": "Pokémon Esmeralda", "generation": 3})
        self.pokedex_hoenn, _ = Pokedex.objects.get_or_create(game=self.game, slug="hoenn", defaults={"name": "Pokédex Regional de Hoenn", "is_national": False})
        self.pokedex_nat, _ = Pokedex.objects.get_or_create(game=self.game, slug="national", defaults={"name": "Pokédex Nacional", "is_national": True})

    def test_emerald_catalogs_structure(self):
        """Valida que los catálogos compilados de Esmeralda se carguen con 202 y 386 entradas con sus datos canónicos."""
        hoenn_cat = get_compiled_catalog("emerald", is_national=False)
        self.assertIsNotNone(hoenn_cat)
        self.assertEqual(len(hoenn_cat), 202)
        self.assertEqual(hoenn_cat[0].pokemon.name, "treecko")
        self.assertEqual(hoenn_cat[0].entry_number, 1)

        # Mascot Rayquaza (#200 en regional)
        rayquaza = next(e for e in hoenn_cat if e.pokemon.name == "rayquaza")
        self.assertEqual(rayquaza.entry_number, 200)
        self.assertEqual(rayquaza.obtaining_info["type"], "legendary")
        self.assertIn("Pilar Celeste", rayquaza.obtaining_info["summary"])

        # Ambos Groudon y Kyogre son capturables en Esmeralda
        kyogre = next(e for e in hoenn_cat if e.pokemon.name == "kyogre")
        self.assertEqual(kyogre.entry_number, 198)
        self.assertIn("Cueva Marina", kyogre.obtaining_info["summary"])

        groudon = next(e for e in hoenn_cat if e.pokemon.name == "groudon")
        self.assertEqual(groudon.entry_number, 199)
        self.assertIn("Cueva Terra", groudon.obtaining_info["summary"])

        # Catálogo Nacional (386)
        nat_cat = get_compiled_catalog("emerald", is_national=True)
        self.assertIsNotNone(nat_cat)
        self.assertEqual(len(nat_cat), 386)
        self.assertEqual(nat_cat[0].pokemon.name, "bulbasaur")
        self.assertEqual(nat_cat[385].pokemon.name, "deoxys")

        # Cueva Cambiante en Esmeralda (Ruta 103)
        zubat = next(e for e in hoenn_cat if e.pokemon.national_number == 41)
        self.assertIn("Cueva Cambiante (Ruta 103)", [l["area"] for l in zubat.obtaining_info["locations"]])

        aipom = next(e for e in nat_cat if e.pokemon.national_number == 190)
        aipom_locs = {l["area"]: l["method"] for l in aipom.obtaining_info["locations"]}
        self.assertIn("Cueva Cambiante (Ruta 103)", aipom_locs)
        self.assertEqual(aipom_locs["Cueva Cambiante (Ruta 103)"], "Evento e-Reader inactivo")

    def test_emerald_views_and_theme(self):
        """Verifica que las vistas de Pokédex regional y nacional respondan correctamente en Esmeralda con su tema verde esmeralda."""
        resp_hoenn = self.client.get(reverse("tracker:pokedex_detail", kwargs={"game_slug": "emerald", "pokedex_slug": "hoenn"}))
        self.assertEqual(resp_hoenn.status_code, 200)
        self.assertContains(resp_hoenn, "Pokédex Regional de Hoenn")
        self.assertContains(resp_hoenn, "emerald")

        resp_nat = self.client.get(reverse("tracker:pokedex_detail", kwargs={"game_slug": "emerald", "pokedex_slug": "national"}))
        self.assertEqual(resp_nat.status_code, 200)
        self.assertContains(resp_nat, "Pokédex Nacional")

    def test_emerald_exclusives_and_missing_counterparts(self):
        """Comprueba que Esmeralda reporte a Rubí y Zafiro como contraparte con los 7 Pokémon faltantes."""
        from tracker.exclusives import get_version_exclusives_context
        excl_ctx = get_version_exclusives_context(self.game, self.pokedex_hoenn, set())
        self.assertIsNotNone(excl_ctx)
        self.assertEqual(excl_ctx["counterpart_short_name"], "Rubí y Zafiro")
        self.assertEqual(excl_ctx["counterpart_theme"], "ruby_sapphire")
        self.assertEqual(excl_ctx["counterpart_total"], 7)
        self.assertEqual(excl_ctx["own_total"], 46)

        counterpart_names = {p["name"] for p in excl_ctx["counterpart_list"]}
        self.assertIn("Surskit", counterpart_names)
        self.assertIn("Masquerain", counterpart_names)
        self.assertIn("Meditite", counterpart_names)
        self.assertIn("Medicham", counterpart_names)
        self.assertIn("Roselia", counterpart_names)
        self.assertIn("Zangoose", counterpart_names)
        self.assertIn("Lunatone", counterpart_names)

        own_names = {p["name"] for p in excl_ctx["own_list"]}
        self.assertIn("Deoxys", own_names)
        self.assertIn("Ditto", own_names)
        self.assertIn("Sudowoodo", own_names)
        self.assertIn("Smeargle", own_names)
        self.assertIn("Mareep", own_names)
        self.assertIn("Houndour", own_names)
        self.assertIn("Miltank", own_names)
        self.assertIn("Mew", own_names)
        self.assertIn("Chikorita", own_names)
        self.assertIn("Cyndaquil", own_names)
        self.assertIn("Totodile", own_names)
        self.assertIn("Meowth", own_names)
        self.assertIn("Lugia", own_names)
        self.assertIn("Ho Oh", own_names)

    def test_emerald_transfers(self):
        """Verifica que las transferencias requeridas en Esmeralda sean 139 (45 menos que R/Z debido a los salvajes, regalos y eventos de Johto/Kanto)."""
        from tracker.exclusives import get_version_transfers_context
        transfers_ctx = get_version_transfers_context(self.game, self.pokedex_nat, set())
        self.assertIsNotNone(transfers_ctx)
        self.assertEqual(transfers_ctx["total"], 139)

        # Verificar que especies como Sudowoodo (#185), Smeargle (#235), Ditto (#132), Mew (#151),
        # Iniciales de Johto (#152, #155, #158), Meowth (#52), Lugia (#249), Ho-Oh (#250) NO están en transferencias
        transfer_nums = {p["national_number"] for p in transfers_ctx["transfer_list"]}
        self.assertNotIn(185, transfer_nums)  # Sudowoodo (Frente de Batalla)
        self.assertNotIn(235, transfer_nums)  # Smeargle (Cueva Taller)
        self.assertNotIn(132, transfer_nums)  # Ditto (Túnel del Desierto)
        self.assertNotIn(179, transfer_nums)  # Mareep (Zona Safari expansión)
        self.assertNotIn(151, transfer_nums)  # Mew (Evento Isla Suprema)
        self.assertNotIn(152, transfer_nums)  # Chikorita (Regalo Prof. Abedul)
        self.assertNotIn(155, transfer_nums)  # Cyndaquil (Regalo Prof. Abedul)
        self.assertNotIn(158, transfer_nums)  # Totodile (Regalo Prof. Abedul)
        self.assertNotIn(52, transfer_nums)   # Meowth (Intercambio Frente de Batalla)
        self.assertNotIn(249, transfer_nums)  # Lugia (Evento Roca Ombligo)
        self.assertNotIn(250, transfer_nums)  # Ho-Oh (Evento Roca Ombligo)
        self.assertIn(1, transfer_nums)       # Bulbasaur (requiere transferencia RF/VH)

    def test_emerald_evolution_stones(self):
        """Comprueba que todos los objetos evolutivos de Gen 3 tengan registradas sus ubicaciones en Esmeralda."""
        import json
        with open("tracker/data/evolution_stones.json", "r", encoding="utf-8") as f:
            stones_data = json.load(f)

        gen3_stones = [
            'moon-stone', 'fire-stone', 'water-stone', 'thunder-stone', 'leaf-stone',
            'sun-stone', 'kings-rock', 'metal-coat', 'dragon-scale', 'up-grade',
            'deep-sea-tooth', 'deep-sea-scale', 'sea-incense', 'lax-incense'
        ]
        for stone_slug in gen3_stones:
            self.assertIn(stone_slug, stones_data)
            self.assertIn("emerald", stones_data[stone_slug]["games"], f"Falta información de {stone_slug} para Pokémon Esmeralda")
            self.assertTrue(len(stones_data[stone_slug]["games"]["emerald"]) > 0)

    def test_emerald_animated_sprites_and_card_integration(self):
        """Valida que las tarjetas de cuadrícula usen PNGs estáticos (sin saturar la página) y el modal cómic use GIFs animados."""
        from django.conf import settings
        from pathlib import Path
        anim_dir = Path(settings.MEDIA_ROOT) / "pokemon" / "sprites" / "emerald_animated"
        shiny_anim_dir = Path(settings.MEDIA_ROOT) / "pokemon" / "sprites" / "emerald_animated_shiny"
        self.assertTrue(anim_dir.exists(), "Debe existir directorio emerald_animated")
        self.assertTrue(shiny_anim_dir.exists(), "Debe existir directorio emerald_animated_shiny")

        hoenn_cat = get_compiled_catalog("emerald", is_national=False)
        treecko = hoenn_cat[0]
        # Cuadrícula general: PNG estático para no saturar la página
        self.assertIn("emerald/252.png", treecko.game_sprite_url)
        self.assertIn("emerald_shiny/252.png", treecko.game_sprite_shiny_url)
        # Modal de ficha individual: GIF animado exclusivo
        self.assertIn("emerald_animated/252.gif", treecko.modal_retro_sprite_url)
        self.assertIn("emerald_animated_shiny/252.gif", treecko.modal_retro_sprite_shiny_url)

        modal_data = json.loads(treecko.modal_data_json)
        self.assertTrue(modal_data["sprite_retro"].endswith("emerald_animated/252.gif"))
        self.assertTrue(modal_data["sprite_retro_shiny"].endswith("emerald_animated_shiny/252.gif"))

    def test_emerald_castform_animated_forms(self):
        """Valida que Castform (#351) y todas sus formas climáticas cuenten con sprites animados (.gif) en el modal de Esmeralda."""
        from django.conf import settings
        from pathlib import Path

        hoenn_cat = get_compiled_catalog("emerald", is_national=False)
        castform = next(e for e in hoenn_cat if e.pokemon.national_number == 351)
        self.assertEqual(len(castform.forms), 4)

        # 1. Comprobar que en el modal individual (modal_retro_sprite_url) todas las formas usan GIFs animados
        expected_gifs = [
            ("normal", "emerald_animated/351.gif", "emerald_animated_shiny/351.gif"),
            ("sunny", "emerald_animated/castform/sunny.gif", "emerald_animated_shiny/castform/sunny.gif"),
            ("rainy", "emerald_animated/castform/rainy.gif", "emerald_animated_shiny/castform/rainy.gif"),
            ("snowy", "emerald_animated/castform/snowy.gif", "emerald_animated_shiny/castform/snowy.gif"),
        ]

        for idx, (f_key, exp_normal, exp_shiny) in enumerate(expected_gifs):
            form = castform.forms[idx]
            self.assertEqual(form["form_key"], f_key)
            self.assertIn(exp_normal, form["modal_retro_sprite_url"])
            self.assertIn(exp_shiny, form["modal_retro_sprite_shiny_url"])

            # Comprobar que los archivos existen en disco y son GIFs válidos
            p_normal = Path(settings.MEDIA_ROOT) / exp_normal.replace("emerald_animated/", "pokemon/sprites/emerald_animated/")
            p_shiny = Path(settings.MEDIA_ROOT) / exp_shiny.replace("emerald_animated_shiny/", "pokemon/sprites/emerald_animated_shiny/")
            self.assertTrue(p_normal.exists(), f"Debe existir archivo {p_normal}")
            self.assertTrue(p_shiny.exists(), f"Debe existir archivo {p_shiny}")

            with open(p_normal, "rb") as f:
                header = f.read(6)
                self.assertIn(header, [b"GIF87a", b"GIF89a"])
            with open(p_shiny, "rb") as f:
                header = f.read(6)
                self.assertIn(header, [b"GIF87a", b"GIF89a"])

        # 2. Comprobar serialización en modal_data_json
        modal_json = json.loads(castform.modal_data_json)
        self.assertEqual(len(modal_json["forms"]), 4)
        for idx, (_, exp_normal, exp_shiny) in enumerate(expected_gifs):
            self.assertIn(exp_normal, modal_json["forms"][idx]["modal_retro_sprite_url"])
            self.assertIn(exp_shiny, modal_json["forms"][idx]["modal_retro_sprite_shiny_url"])

    def test_emerald_type_badges_classes(self):
        """Verifica que las etiquetas de tipo se rendericen en minúsculas y coincidan con los estilos CSS."""
        resp = self.client.get(reverse("tracker:pokedex_detail", kwargs={"game_slug": "emerald", "pokedex_slug": "hoenn"}))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'tracker/css/pokedex.css')
        self.assertContains(resp, 'type-grass')

    def test_emerald_deoxys_speed_form_sprites(self):
        """Verifica que Deoxys en Esmeralda utilice canónicamente la Forma Velocidad tanto en sprites como en icono."""
        from django.conf import settings
        from pathlib import Path
        deoxys_sprite = Path(settings.MEDIA_ROOT) / "pokemon" / "sprites" / "emerald" / "386-speed.png"
        self.assertTrue(deoxys_sprite.exists())
        # En Esmeralda, Deoxys Velocidad (10003.png) tiene 842 bytes, diferente a la forma normal de Rubí/Zafiro (838 bytes)
        self.assertEqual(deoxys_sprite.stat().st_size, 842)

        hoenn_cat = get_compiled_catalog("emerald", is_national=False)
        deoxys_entry = next(e for e in hoenn_cat if e.pokemon.name == "deoxys")
        self.assertIn("emerald/386-speed.png", deoxys_entry.game_sprite_url)
        self.assertIn("10003.png", deoxys_entry.pc_icon_url)

    def test_emerald_canonical_flavor_texts(self):
        """Comprueba que las descripciones de Pokédex correspondan estrictamente al canon de Pokémon Esmeralda."""
        nat_cat = get_compiled_catalog("emerald", is_national=True)
        cat_map = {e.pokemon.national_number: e for e in nat_cat}

        # 1. Deoxys (#386): Exclusivo de Esmeralda destacando velocidad y agilidad
        deoxys = cat_map[386]
        self.assertIn("velocidad y agilidad superiores", deoxys.flavor_text)

        # 2. Rayquaza (#384): Mascota de Esmeralda, texto exclusivo de Esmeralda
        rayquaza = cat_map[384]
        self.assertEqual(
            rayquaza.flavor_text,
            "Este Pokémon vuela sin parar por la capa de ozono. Dicen que, si Kyogre y Groudon fueran a luchar, bajaría a tierra firme."
        )

        # 3. Groudon (#383) y Kyogre (#382): Textos propios de Esmeralda
        groudon = cat_map[383]
        self.assertIn("creador de la tierra", groudon.flavor_text)
        kyogre = cat_map[382]
        self.assertIn("creador del mar", kyogre.flavor_text)

        # 4. Treecko (#252): Inicial de Hoenn con texto de Esmeralda
        treecko = cat_map[252]
        self.assertIn("protector de los árboles del bosque", treecko.flavor_text)

    def test_emerald_breeding_obtaining_methods(self):
        """Comprueba que SOLO los Pokémon eclosionables (primeras etapas, únicos, bebés e inciensos)
        reflejen la Guardería y crianza en Esmeralda, y que las evoluciones (Grovyle, Mightyena, etc.)
        y especies no criables (Rayquaza, Ditto) jamás incluyan Guardería ni crianza."""
        hoenn_cat = get_compiled_catalog("emerald", is_national=False)
        hoenn_map = {e.pokemon.national_number: e for e in hoenn_cat}

        # 1. Primeras etapas y salvajes ordinarios (#261 Poochyena, #263 Zigzagoon, #265 Wurmple, #276 Taillow, #280 Ralts)
        for nat_id in [261, 263, 265, 276, 280]:
            entry = hoenn_map[nat_id]
            self.assertIn("crianza", entry.obtaining_info.get("summary", "").lower())
            loc_areas = [l.get("area", "") for l in entry.obtaining_info.get("locations", [])]
            self.assertTrue(any("Guardería" in a for a in loc_areas))

        # 2. Iniciales de Hoenn: Formas base tienen crianza, evoluciones NO
        # Base: #252 Treecko, #255 Torchic, #258 Mudkip
        for nat_id in [252, 255, 258]:
            entry = hoenn_map[nat_id]
            self.assertIn("crianza", entry.obtaining_info.get("summary", "").lower())
            loc_areas = [l.get("area", "") for l in entry.obtaining_info.get("locations", [])]
            self.assertTrue(any("Guardería" in a for a in loc_areas))

        # Evoluciones de iniciales: #253 Grovyle, #254 Sceptile, #256 Combusken, #257 Blaziken, #259 Marshtomp, #260 Swampert
        for nat_id in [253, 254, 256, 257, 259, 260]:
            entry = hoenn_map[nat_id]
            self.assertNotIn("crianza", entry.obtaining_info.get("summary", "").lower())
            self.assertNotIn("guardería", entry.obtaining_info.get("summary", "").lower())
            loc_areas = [l.get("area", "") for l in entry.obtaining_info.get("locations", [])]
            self.assertFalse(any("Guardería" in a for a in loc_areas), f"Evolución {entry.pokemon.name} no debe tener Guardería")

        # 3. Evoluciones en general (#262 Mightyena, #281 Kirlia, #282 Gardevoir, #305 Lairon, #306 Aggron)
        for nat_id in [262, 281, 282, 305, 306]:
            entry = hoenn_map[nat_id]
            self.assertNotIn("crianza", entry.obtaining_info.get("summary", "").lower())
            loc_areas = [l.get("area", "") for l in entry.obtaining_info.get("locations", [])]
            self.assertFalse(any("Guardería" in a for a in loc_areas), f"Evolución {entry.pokemon.name} no debe tener Guardería")

        # 4. Bebés (#172 Pichu, #298 Azurill, #360 Wynaut) vs Padres sin incienso (#183 Marill, #202 Wobbuffet)
        # Bebés: deben tener crianza/guardería
        for nat_id in [172, 298, 360]:
            entry = hoenn_map[nat_id]
            loc_areas = [l.get("area", "") for l in entry.obtaining_info.get("locations", [])]
            self.assertTrue(any("Guardería" in a for a in loc_areas))

        # Padres que eclosionan sin incienso en Gen 3 (Marill, Wobbuffet): tienen crianza/guardería
        for nat_id in [183, 202]:
            entry = hoenn_map[nat_id]
            self.assertIn("crianza", entry.obtaining_info.get("summary", "").lower())
            loc_areas = [l.get("area", "") for l in entry.obtaining_info.get("locations", [])]
            self.assertTrue(any("Guardería" in a for a in loc_areas))

        # Evoluciones de bebés (#25 Pikachu, #26 Raichu, #184 Azumarill): NO tienen crianza
        for nat_id in [25, 26, 184]:
            entry = hoenn_map[nat_id]
            self.assertNotIn("crianza", entry.obtaining_info.get("summary", "").lower())
            loc_areas = [l.get("area", "") for l in entry.obtaining_info.get("locations", [])]
            self.assertFalse(any("Guardería" in a for a in loc_areas))

        # 5. Fósiles (#345 Lileep, #347 Anorith), Regalos únicos (#351 Castform, #374 Beldum)
        for nat_id in [345, 347, 351, 374]:
            entry = hoenn_map[nat_id]
            self.assertIn("crianza", entry.obtaining_info.get("summary", "").lower())
            loc_areas = [l.get("area", "") for l in entry.obtaining_info.get("locations", [])]
            self.assertTrue(any("Guardería" in a for a in loc_areas))

        # 6. Especies de etapa única (#302 Sableye, #303 Mawile, #311 Plusle, #335 Zangoose, #337 Lunatone)
        for nat_id in [302, 303, 311, 335, 337]:
            entry = hoenn_map[nat_id]
            self.assertIn("crianza", entry.obtaining_info.get("summary", "").lower())
            loc_areas = [l.get("area", "") for l in entry.obtaining_info.get("locations", [])]
            self.assertTrue(any("Guardería" in a for a in loc_areas))

        # 7. No criables / Legendarios (#384 Rayquaza, #382 Kyogre, #383 Groudon, #386 Deoxys)
        for nat_id in [384, 382, 383, 386]:
            entry = hoenn_map[nat_id]
            self.assertNotIn("crianza", entry.obtaining_info.get("summary", "").lower())
            loc_areas = [l.get("area", "") for l in entry.obtaining_info.get("locations", [])]
            self.assertFalse(any("Guardería" in a for a in loc_areas))

        # 8. Conteo canónico en Pokédex Regional: exactamente 97 eclosionables vs 105 no eclosionables
        regional_hatchable = [e for e in hoenn_cat if any("Guardería" in l.get("area", "") for l in e.obtaining_info.get("locations", []))]
        self.assertEqual(len(regional_hatchable), 97)
        self.assertEqual(len(hoenn_cat) - len(regional_hatchable), 105)

        # 9. Conteo canónico en Pokédex Nacional: exactamente 181 eclosionables vs 205 no eclosionables
        nat_cat = get_compiled_catalog("emerald", is_national=True)
        nat_hatchable = [e for e in nat_cat if any("Guardería" in l.get("area", "") for l in e.obtaining_info.get("locations", []))]
        self.assertEqual(len(nat_hatchable), 181)
        self.assertEqual(len(nat_cat) - len(nat_hatchable), 205)

        # 10. Comprobación nacional: Ditto (#132), Mewtwo (#150), Charizard (#6) no tienen guardería
        nat_map = {e.pokemon.national_number: e for e in nat_cat}
        for nat_id in [6, 132, 150, 201]:
            entry = nat_map[nat_id]
            loc_areas = [l.get("area", "") for l in entry.obtaining_info.get("locations", [])]
            self.assertFalse(any("Guardería" in a for a in loc_areas))
            self.assertNotIn("crianza", entry.obtaining_info.get("summary", "").lower())

    def test_gen3_evolution_methods_and_obtaining_clarity(self):
        """Verifica la claridad canónica sin ambigüedad de los métodos de evolución y obtención en Gen 3 (R/Z/E):
        - Milotic (#350): Belleza 170+ mediante Pokécubos secos (sin mención errónea a Pañuelo Azul).
        - Feebas (#349): Pesca en exactamente 6 casillas aleatorias en Ruta 119.
        - Espeon/Umbreon (#196/#197): Felicidad alta en español (Día)/(Noche) sin términos en inglés.
        - Línea de Tyrogue (#106, #107, #237): Comparaciones estadísticas explícitas (Ataque >, <, = Defensa).
        """
        for game_slug in ["ruby", "sapphire", "emerald"]:
            nat_cat = get_compiled_catalog(game_slug, is_national=True)
            cat_map = {e.pokemon.national_number: e for e in nat_cat}

            # 1. Milotic (#350)
            milotic = cat_map[350]
            m_obt = milotic.obtaining_info
            m_evo = m_obt.get("evolution_info", {})
            self.assertIn("170+", m_obt.get("summary", ""))
            self.assertIn("Belleza", m_obt.get("summary", ""))
            self.assertIn("Pokécubos", m_obt.get("summary", ""))
            self.assertNotIn("Pañuelo Azul", m_obt.get("summary", ""))
            self.assertNotIn("Pañuelo Azul", m_evo.get("condition", ""))
            self.assertEqual(m_evo.get("condition"), "Subir de nivel con 170+ de Belleza (dándole Pokécubos Azules o Índigo)")

            # 2. Feebas (#349)
            feebas = cat_map[349]
            f_summary = feebas.obtaining_info.get("summary", "")
            self.assertIn("6 casillas aleatorias", f_summary)
            self.assertIn("Ruta 119", f_summary)

            # 3. Espeon (#196) y Umbreon (#197)
            espeon_evo = cat_map[196].obtaining_info.get("evolution_info", {})
            umbreon_evo = cat_map[197].obtaining_info.get("evolution_info", {})
            self.assertIn("(Día)", espeon_evo.get("condition", ""))
            self.assertNotIn("(day)", espeon_evo.get("condition", ""))
            self.assertIn("(Noche)", umbreon_evo.get("condition", ""))
            self.assertNotIn("(night)", umbreon_evo.get("condition", ""))

            # 4. Tyrogue: Hitmonlee (#106), Hitmonchan (#107), Hitmontop (#237)
            self.assertIn("Ataque > Defensa", cat_map[106].obtaining_info.get("evolution_info", {}).get("condition", ""))
            self.assertIn("Ataque < Defensa", cat_map[107].obtaining_info.get("evolution_info", {}).get("condition", ""))
            self.assertIn("Ataque = Defensa", cat_map[237].obtaining_info.get("evolution_info", {}).get("condition", ""))




class PokemonFireRedGen3Tests(TestCase):
    """
    Suite de pruebas completa para la integración oficial de Pokémon Rojo Fuego (Gen 3):
    - Catálogo Regional de Kanto (151 especies, IDs 2483 a 2633).
    - Catálogo Nacional (386 especies, IDs 2483 a 2868).
    - Invariantes de Crianza canónica en Isla Quarta (Guardería Pokémon).
    - Forma de Ataque nativa de Deoxys (#386 con icono PC #10001).
    - Bestias Errantes (Raikou, Entei, Suicune) condicionadas al inicial.
    - Catálogo de Exclusivos y Transferencias con Verde Hoja.
    - Barra de Generaciones Nacional en Rojo Fuego (Kanto, Johto, Hoenn).
    - Disponibilidad de Sprites Estáticos Offline (normal, shiny, back normal, back shiny).
    """

    def setUp(self):
        self.game, _ = Game.objects.get_or_create(slug="firered", defaults={"name": "Pokémon Rojo Fuego", "generation": 3})
        self.pk_kanto, _ = Pokedex.objects.get_or_create(game=self.game, slug="kanto", defaults={"name": "Pokédex de Kanto", "is_national": False})
        self.pk_nat, _ = Pokedex.objects.get_or_create(game=self.game, slug="national", defaults={"name": "Pokédex Nacional", "is_national": True})

    def test_firered_regional_catalog_structure(self):
        cat = get_compiled_catalog("firered", is_national=False)
        self.assertIsNotNone(cat)
        self.assertEqual(len(cat), 151)
        self.assertEqual(cat[0].entry_number, 1)
        self.assertEqual(cat[0].pokemon.name, "bulbasaur")
        self.assertEqual(cat[0].id, 2483)
        self.assertEqual(cat[-1].entry_number, 151)
        self.assertEqual(cat[-1].pokemon.name, "mew")
        self.assertEqual(cat[-1].id, 2633)

        # IDs estrictamente consecutivos
        ids = [e.id for e in cat]
        self.assertEqual(ids, list(range(2483, 2634)))

        # Validar descripciones canónicas sin artefactos wikitext ni mezclas (100% oficial Rojo Fuego GBA)
        self.assertEqual(
            cat[0].flavor_text,
            "Este Pokémon nace con una semilla en el lomo. Con el tiempo, la semilla brota."
        )
        self.assertNotIn("NombreHaEs", cat[0].flavor_text)
        self.assertNotIn("{{", cat[0].flavor_text)
        self.assertNotIn("|", cat[0].flavor_text)

    def test_firered_national_catalog_structure(self):
        cat = get_compiled_catalog("firered", is_national=True)
        self.assertIsNotNone(cat)
        self.assertEqual(len(cat), 386)
        self.assertEqual(cat[0].pokemon.national_number, 1)
        self.assertEqual(cat[0].pokemon.name, "bulbasaur")
        self.assertEqual(cat[0].id, 2483)
        self.assertEqual(cat[151].pokemon.national_number, 152)
        self.assertEqual(cat[151].pokemon.name, "chikorita")
        self.assertEqual(cat[251].pokemon.national_number, 252)
        self.assertEqual(cat[251].pokemon.name, "treecko")
        self.assertEqual(cat[-1].pokemon.national_number, 386)
        self.assertEqual(cat[-1].pokemon.name, "deoxys")
        self.assertEqual(cat[-1].id, 2868)

        # IDs estrictamente consecutivos
        ids = [e.id for e in cat]
        self.assertEqual(ids, list(range(2483, 2869)))

    def test_firered_breeding_invariants(self):
        from tracker.catalog_service import get_compiled_catalog
        cat = get_compiled_catalog("firered", is_national=True)
        cat_map = {e.pokemon.national_number: e for e in cat}

        # 1. Especies base con crianza habilitada (Isla Quarta)
        for nat_id in [1, 4, 7, 172, 175]:
            entry = cat_map[nat_id]
            self.assertTrue(entry.is_hatchable, f"Pokémon #{nat_id} debería ser hatchable")
            areas = [loc.get("area", "") for loc in entry.obtaining_info.get("locations", [])]
            self.assertIn("Isla Quarta (Guardería Pokémon)", areas)
            self.assertNotIn("Ruta 5", " ".join(areas))
            if "crianza" in entry.obtaining_info.get("summary", "").lower():
                self.assertIn("(también obtenible mediante crianza)", entry.obtaining_info.get("summary", ""))

        # 2. Evoluciones y legendarios NO criables
        for nat_id in [3, 6, 9, 25, 144, 145, 146, 150, 151, 386]:
            entry = cat_map[nat_id]
            self.assertFalse(entry.is_hatchable, f"Pokémon #{nat_id} no debería ser hatchable")
            areas = [loc.get("area", "") for loc in entry.obtaining_info.get("locations", [])]
            self.assertFalse(any("Guardería" in a for a in areas), f"#{nat_id} no debe tener guardería")
            self.assertNotIn("crianza", entry.obtaining_info.get("summary", "").lower())

    def test_firered_deoxys_attack_forme(self):
        cat = get_compiled_catalog("firered", is_national=True)
        cat_map = {e.pokemon.national_number: e for e in cat}
        deoxys = cat_map[386]

        self.assertEqual(deoxys.pokemon.name, "deoxys")
        self.assertEqual(deoxys.game_sprite_url, "/media/pokemon/sprites/firered/386.png")
        self.assertEqual(deoxys.pc_icon_url, "/media/pokemon/icons/gen3/10001.png")
        self.assertIn("Isla Origen", deoxys.obtaining_info.get("summary", ""))

    def test_firered_roaming_beasts_summary(self):
        cat = get_compiled_catalog("firered", is_national=True)
        cat_map = {e.pokemon.national_number: e for e in cat}

        raikou = cat_map[243]
        entei = cat_map[244]
        suicune = cat_map[245]

        self.assertIn("Squirtle", raikou.obtaining_info.get("summary", ""))
        self.assertIn("Bulbasaur", entei.obtaining_info.get("summary", ""))
        self.assertIn("Charmander", suicune.obtaining_info.get("summary", ""))

    def test_firered_exclusives_and_transfers_catalog(self):
        from tracker.exclusives import (
            GAME_COUNTERPARTS,
            VERSION_EXCLUSIVES_CATALOG,
            VERSION_TRANSFERS_CATALOG,
            VERSION_TRANSFERS_META,
        )

        self.assertIn("firered", GAME_COUNTERPARTS)
        self.assertEqual(GAME_COUNTERPARTS["firered"], ["leafgreen"])

        self.assertIn("firered", VERSION_EXCLUSIVES_CATALOG)
        self.assertEqual(len(VERSION_EXCLUSIVES_CATALOG["firered"]), 22)
        self.assertIn(23, VERSION_EXCLUSIVES_CATALOG["firered"])  # Ekans
        self.assertIn(43, VERSION_EXCLUSIVES_CATALOG["firered"])  # Oddish
        self.assertIn(58, VERSION_EXCLUSIVES_CATALOG["firered"])  # Growlithe
        self.assertIn(123, VERSION_EXCLUSIVES_CATALOG["firered"]) # Scyther
        self.assertIn(125, VERSION_EXCLUSIVES_CATALOG["firered"]) # Electabuzz

        self.assertIn("leafgreen", VERSION_EXCLUSIVES_CATALOG)
        self.assertEqual(len(VERSION_EXCLUSIVES_CATALOG["leafgreen"]), 23)
        self.assertIn(27, VERSION_EXCLUSIVES_CATALOG["leafgreen"])  # Sandshrew
        self.assertIn(37, VERSION_EXCLUSIVES_CATALOG["leafgreen"])  # Vulpix
        self.assertIn(69, VERSION_EXCLUSIVES_CATALOG["leafgreen"])  # Bellsprout
        self.assertIn(126, VERSION_EXCLUSIVES_CATALOG["leafgreen"]) # Magmar
        self.assertIn(127, VERSION_EXCLUSIVES_CATALOG["leafgreen"]) # Pinsir

        self.assertIn("firered", VERSION_TRANSFERS_CATALOG)
        self.assertEqual(len(VERSION_TRANSFERS_CATALOG["firered"]), 167)
        self.assertIn(152, VERSION_TRANSFERS_CATALOG["firered"]) # Chikorita
        self.assertIn(190, VERSION_TRANSFERS_CATALOG["firered"]) # Aipom (Cueva Cambiante inactiva)
        self.assertIn(252, VERSION_TRANSFERS_CATALOG["firered"]) # Treecko
        self.assertIn(382, VERSION_TRANSFERS_CATALOG["firered"]) # Kyogre

        self.assertIn("altering_cave_note", VERSION_TRANSFERS_META["firered"])
        self.assertIn("Zubat", VERSION_TRANSFERS_META["firered"]["altering_cave_note"])
        self.assertIn("Cueva Cambiante inactiva", VERSION_TRANSFERS_META["firered"]["origins"][190])

        from tracker.exclusives import get_version_transfers_context
        # En la Pokédex Regional de Kanto NO debe haber transferencias
        self.assertIsNone(get_version_transfers_context(self.game, self.pk_kanto, set()))
        # En la Pokédex Nacional SÍ debe haber las 167 transferencias
        nat_transfers = get_version_transfers_context(self.game, self.pk_nat, set())
        self.assertIsNotNone(nat_transfers)
        self.assertEqual(nat_transfers["total"], 167)

    def test_firered_evolution_stones_data(self):
        import json
        import os
        from django.conf import settings

        stones_path = os.path.join(settings.BASE_DIR, "tracker", "data", "evolution_stones.json")
        with open(stones_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.assertIn("fire-stone", data)
        self.assertIn("firered", data["fire-stone"]["games"])
        self.assertIn("Centro Comercial de Azulona (4F)", [l["area"] for l in data["fire-stone"]["games"]["firered"]])
        self.assertIn("firered", data["water-stone"]["games"])
        self.assertIn("firered", data["thunder-stone"]["games"])
        self.assertIn("firered", data["leaf-stone"]["games"])
        self.assertIn("moon-stone", data)
        self.assertIn("firered", data["moon-stone"]["games"])
        self.assertIn("firered", data["sun-stone"]["games"])
        self.assertIn("firered", data["up-grade"]["games"])

    def test_firered_views_and_national_regions_bar(self):
        # 1. Vista regional por defecto (151 entradas, sin barra nacional de regiones)
        resp_reg = self.client.get(reverse("tracker:pokedex_default", kwargs={"game_slug": "firered"}))
        self.assertEqual(resp_reg.status_code, 200)
        self.assertContains(resp_reg, "Bulbasaur")
        self.assertContains(resp_reg, "Mew")
        self.assertEqual(len(resp_reg.context["entries"]), 151)
        self.assertFalse(any(e.pokemon.name == "chikorita" for e in resp_reg.context["entries"]))
        self.assertIsNone(resp_reg.context.get("national_regions_ctx"))

        # 2. Vista nacional: activa kanto por defecto (151 entradas)
        resp_nat = self.client.get(reverse("tracker:pokedex_detail", kwargs={"game_slug": "firered", "pokedex_slug": "national"}))
        self.assertEqual(resp_nat.status_code, 200)
        self.assertIsNotNone(resp_nat.context.get("national_regions_ctx"))
        ctx = resp_nat.context["national_regions_ctx"]
        self.assertEqual(ctx["active_slug"], "kanto")
        self.assertEqual(len(resp_nat.context["entries"]), 151)

        # 3. Filtrar Johto en nacional (100 entradas)
        resp_johto = self.client.get(reverse("tracker:pokedex_detail", kwargs={"game_slug": "firered", "pokedex_slug": "national"}) + "?gen=johto")
        self.assertEqual(resp_johto.status_code, 200)
        self.assertEqual(len(resp_johto.context["entries"]), 100)
        self.assertEqual(resp_johto.context["entries"][0].pokemon.national_number, 152)
        self.assertEqual(resp_johto.context["entries"][-1].pokemon.national_number, 251)

        # 4. Filtrar Hoenn en nacional (135 entradas)
        resp_hoenn = self.client.get(reverse("tracker:pokedex_detail", kwargs={"game_slug": "firered", "pokedex_slug": "national"}) + "?gen=hoenn")
        self.assertEqual(resp_hoenn.status_code, 200)
        self.assertEqual(len(resp_hoenn.context["entries"]), 135)
        self.assertEqual(resp_hoenn.context["entries"][0].pokemon.national_number, 252)
        self.assertEqual(resp_hoenn.context["entries"][-1].pokemon.national_number, 386)

    def test_firered_offline_sprites_exist(self):
        import os
        from django.conf import settings

        base_media = settings.MEDIA_ROOT
        # Normal, shiny, back, shiny back
        self.assertTrue(os.path.exists(os.path.join(base_media, "pokemon", "sprites", "firered", "1.png")))
        self.assertTrue(os.path.exists(os.path.join(base_media, "pokemon", "sprites", "firered", "386.png")))
        self.assertTrue(os.path.exists(os.path.join(base_media, "pokemon", "sprites", "firered_shiny", "1.png")))
        self.assertTrue(os.path.exists(os.path.join(base_media, "pokemon", "sprites", "firered_shiny", "386.png")))
        self.assertTrue(os.path.exists(os.path.join(base_media, "pokemon", "sprites", "firered", "back", "1.png")))
        self.assertTrue(os.path.exists(os.path.join(base_media, "pokemon", "sprites", "firered", "back", "386.png")))
        self.assertTrue(os.path.exists(os.path.join(base_media, "pokemon", "sprites", "firered_shiny", "back", "1.png")))
        self.assertTrue(os.path.exists(os.path.join(base_media, "pokemon", "sprites", "firered_shiny", "back", "386.png")))

    def test_unown_firered_tanoby_chambers_and_letter_click_obtaining(self):
        """
        Valida que en Pokémon Rojo Fuego / Verde Hoja:
        1. Las Ruinas Sete cuenten con las 7 cámaras oficiales (Anémuna, Tulipdos, Trisante, Quarciso, Hibinca, Seiris, Pasiete).
        2. La forma canónica predeterminada en la Pokédex sea Unown F (primer elemento en forms).
        3. Cada forma individual incluya su ubicación exacta y tasa sin mezclar las de otras cámaras.
        4. En la vista de Rojo Fuego Nacional se muestren las pestañas de las cámaras de Ruinas Sete.
        """
        from tracker.unown_data import get_unown_catalog, TANOBY_UNOWN_CHAMBERS, get_game_unown_chambers
        from tracker.pokemon_forms import get_pokemon_forms

        # 1. Catálogo y cámaras de Ruinas Sete
        chambers = get_game_unown_chambers("firered")
        self.assertEqual(len(chambers), 7)
        self.assertIn("anemuna", chambers)
        self.assertIn("hibinca", chambers)
        self.assertIn("pasiete", chambers)
        self.assertEqual(chambers["anemuna"]["rates"]["a"], "99%")
        self.assertEqual(chambers["anemuna"]["rates"]["question"], "1%")
        self.assertEqual(chambers["hibinca"]["rates"]["f"], "13%")
        self.assertEqual(chambers["pasiete"]["rates"]["z"], "99%")
        self.assertEqual(chambers["pasiete"]["rates"]["exclamation"], "1%")

        # 2. Formas en get_pokemon_forms: F debe ser la primera en firered
        forms_fr = get_pokemon_forms(201, "firered")
        self.assertEqual(len(forms_fr), 28)
        self.assertEqual(forms_fr[0]["form_key"], "f")
        self.assertEqual(forms_fr[0]["chamber_key"], "hibinca")
        self.assertEqual(len(forms_fr[0]["locations"]), 1)
        self.assertEqual(forms_fr[0]["locations"][0]["area"], "Cámara Hibinca (Ruinas Sete)")

        # 3. Ubicaciones exactas aisladas por letra
        forms_by_key = {f["form_key"]: f for f in forms_fr}
        self.assertEqual(forms_by_key["a"]["locations"][0]["area"], "Cámara Anémuna (Ruinas Sete)")
        self.assertEqual(forms_by_key["c"]["locations"][0]["area"], "Cámara Tulipdos (Ruinas Sete)")
        self.assertEqual(forms_by_key["n"]["locations"][0]["area"], "Cámara Trisante (Ruinas Sete)")
        self.assertEqual(forms_by_key["p"]["locations"][0]["area"], "Cámara Quarciso (Ruinas Sete)")
        self.assertEqual(forms_by_key["v"]["locations"][0]["area"], "Cámara Seiris (Ruinas Sete)")
        self.assertEqual(forms_by_key["z"]["locations"][0]["area"], "Cámara Pasiete (Ruinas Sete)")

        # 4. En Johto, verificar aislamiento de cámaras
        forms_gold = get_pokemon_forms(201, "gold")
        self.assertEqual(len(forms_gold), 26)
        self.assertEqual(forms_gold[0]["form_key"], "a")
        gold_by_key = {f["form_key"]: f for f in forms_gold}
        self.assertEqual(gold_by_key["a"]["locations"][0]["area"], "Cámara de Kabuto (Ruinas Alfa)")
        self.assertEqual(gold_by_key["l"]["locations"][0]["area"], "Cámara de Omanyte (Ruinas Alfa)")
        self.assertEqual(gold_by_key["s"]["locations"][0]["area"], "Cámara de Aerodactyl (Ruinas Alfa)")
        self.assertEqual(gold_by_key["x"]["locations"][0]["area"], "Cámara de Ho-Oh (Ruinas Alfa)")

        # 5. Renderizado en vista de Rojo Fuego
        resp = self.client.get(reverse("tracker:pokedex_detail", kwargs={"game_slug": "firered", "pokedex_slug": "national"}))
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.context["is_tanoby"])
        self.assertContains(resp, 'id="unown-tab-anemuna"')
        self.assertContains(resp, 'id="unown-tab-hibinca"')
        self.assertContains(resp, 'Ruinas Sete')
        self.assertContains(resp, 'openUnownLetterCard')

    def test_unown_obtaining_compatibility_hoenn(self):
        """
        Valida que en los juegos de Hoenn (Esmeralda, Rubí, Zafiro):
        1. get_game_unown_chambers retorne un diccionario vacío (no existen ruinas ni cámaras salvajes en Hoenn).
        2. get_unown_catalog retorne las 28 formas con indicador de no disponible en Hoenn y sin asociar cámaras de Johto.
        3. get_pokemon_forms retorne las 28 formas con método de obtención 'Transferencia' (slate),
           explicando que requiere Rojo Fuego / Verde Hoja o Pokémon Colosseum, sin mezclar 'Salvaje' ni Ruinas Alfa.
        4. En la vista de Pokédex Nacional de Esmeralda, el modal de Unown no renderice pestañas de Ruinas Alfa
           y contenga el texto informativo de Hoenn y badges de Transfer.
        """
        from tracker.unown_data import get_unown_catalog, get_game_unown_chambers
        from tracker.pokemon_forms import get_pokemon_forms

        for game_slug in ["emerald", "ruby", "sapphire"]:
            # 1. No hay cámaras en Hoenn
            chambers = get_game_unown_chambers(game_slug)
            self.assertEqual(chambers, {})

            # 2. Catálogo sin ruinas de Johto
            catalog = get_unown_catalog(game_slug)
            self.assertEqual(len(catalog), 28)
            for item in catalog:
                self.assertEqual(item["chamber_key"], "")
                self.assertEqual(item["chamber_name"], "No disponible en Hoenn")
                self.assertEqual(item["chamber_badge_class"], "hidden")

            # 3. Formas con método Transferencia puro
            forms = get_pokemon_forms(201, game_slug)
            self.assertEqual(len(forms), 28)
            for form in forms:
                self.assertEqual(form["badge_label"], "Transferencia")
                self.assertEqual(form["badge_color"], "slate")
                self.assertEqual(form["type"], "transfer")
                self.assertIn("No disponible en Hoenn", form["summary"])
                self.assertIn("Rojo Fuego", form["summary"])
                self.assertNotIn("Salvaje", form["badge_label"])
                self.assertNotIn("Ruinas Alfa", form["summary"])
                self.assertEqual(len(form["locations"]), 1)
                self.assertEqual(form["locations"][0]["area"], "Transferencia externa (GBA / GameCube)")

        # 4. Vista de Pokédex Nacional de Esmeralda
        em_game, _ = Game.objects.get_or_create(slug="emerald", defaults={"name": "Pokémon Esmeralda", "generation": 3})
        Pokedex.objects.get_or_create(game=em_game, slug="national", defaults={"name": "Pokédex Nacional", "is_national": True})
        resp = self.client.get(reverse("tracker:pokedex_detail", kwargs={"game_slug": "emerald", "pokedex_slug": "national"}))
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(resp.context["is_johto"])
        self.assertFalse(resp.context["is_tanoby"])
        self.assertNotContains(resp, 'id="unown-tab-kabuto"')
        self.assertNotContains(resp, 'id="unown-tab-anemuna"')
        self.assertContains(resp, 'Unown no aparece en estado salvaje en esta región')
        self.assertContains(resp, 'Transfer')


class PokemonLeafGreenGen3Tests(TestCase):
    """
    Suite de pruebas completa para la integración oficial de Pokémon Verde Hoja (Gen 3):
    - Catálogo Regional de Kanto (151 especies, IDs 2869 a 3019).
    - Catálogo Nacional (386 especies, IDs 2869 a 3254).
    - Invariantes de Crianza canónica en Isla Quarta (Guardería Pokémon).
    - Forma de Defensa nativa de Deoxys (#386 con icono PC #10002).
    - Intercambios NPC específicos de Verde Hoja (Ruta 5 por Nidoran♀, Ruta 18 por Slowbro).
    - Catálogo de Exclusivos y Transferencias con Rojo Fuego.
    - Barra de Generaciones Nacional en Verde Hoja (Kanto, Johto, Hoenn).
    - Disponibilidad de Sprites Estáticos Offline (normal, shiny, back normal, back shiny).
    """

    def setUp(self):
        self.game, _ = Game.objects.get_or_create(slug="leafgreen", defaults={"name": "Pokémon Verde Hoja", "generation": 3})
        self.pk_kanto, _ = Pokedex.objects.get_or_create(game=self.game, slug="kanto", defaults={"name": "Pokédex de Kanto", "is_national": False})
        self.pk_nat, _ = Pokedex.objects.get_or_create(game=self.game, slug="national", defaults={"name": "Pokédex Nacional", "is_national": True})

    def test_leafgreen_regional_catalog_structure(self):
        cat = get_compiled_catalog("leafgreen", is_national=False)
        self.assertIsNotNone(cat)
        self.assertEqual(len(cat), 151)
        self.assertEqual(cat[0].entry_number, 1)
        self.assertEqual(cat[0].pokemon.name, "bulbasaur")
        self.assertEqual(cat[0].id, 2869)
        self.assertEqual(cat[-1].entry_number, 151)
        self.assertEqual(cat[-1].pokemon.name, "mew")
        self.assertEqual(cat[-1].id, 3019)

        # IDs estrictamente consecutivos
        ids = [e.id for e in cat]
        self.assertEqual(ids, list(range(2869, 3020)))

        # Validar descripciones canónicas sin artefactos wikitext
        self.assertNotIn("NombreHaEs", cat[0].flavor_text)
        self.assertNotIn("{{", cat[0].flavor_text)
        self.assertNotIn("|", cat[0].flavor_text)

    def test_leafgreen_national_catalog_structure(self):
        cat = get_compiled_catalog("leafgreen", is_national=True)
        self.assertIsNotNone(cat)
        self.assertEqual(len(cat), 386)
        self.assertEqual(cat[0].pokemon.national_number, 1)
        self.assertEqual(cat[0].pokemon.name, "bulbasaur")
        self.assertEqual(cat[0].id, 2869)
        self.assertEqual(cat[151].pokemon.national_number, 152)
        self.assertEqual(cat[151].pokemon.name, "chikorita")
        self.assertEqual(cat[251].pokemon.national_number, 252)
        self.assertEqual(cat[251].pokemon.name, "treecko")
        self.assertEqual(cat[-1].pokemon.national_number, 386)
        self.assertEqual(cat[-1].pokemon.name, "deoxys")
        self.assertEqual(cat[-1].id, 3254)

        # IDs estrictamente consecutivos
        ids = [e.id for e in cat]
        self.assertEqual(ids, list(range(2869, 3255)))

    def test_leafgreen_breeding_invariants(self):
        """Regla de Oro de Crianza: Formas evolucionadas NUNCA tienen Guardería ni mención de crianza."""
        cat = get_compiled_catalog("leafgreen", is_national=True)
        cat_by_num = {e.pokemon.national_number: e for e in cat}

        # Formas evolucionadas
        for num in [6, 9, 3, 26, 130, 248, 149]:
            entry = cat_by_num[num]
            daycare_locs = [l for l in entry.obtaining_info.get("locations", []) if "guardería" in l.get("area", "").lower() or "crianza" in l.get("method", "").lower()]
            self.assertEqual(daycare_locs, [], f"#{num} {entry.pokemon.name} evolucionado no debe tener Guardería")
            self.assertNotIn("crianza", entry.obtaining_info.get("summary", "").lower(), f"#{num} {entry.pokemon.name} evolucionado no debe mencionar crianza")

        # Formas base fértiles y bebés sí tienen Guardería
        for num in [1, 4, 7, 175, 239, 240]:
            entry = cat_by_num[num]
            daycare_locs = [l for l in entry.obtaining_info.get("locations", []) if "guardería" in l.get("area", "").lower()]
            self.assertTrue(len(daycare_locs) > 0, f"#{num} {entry.pokemon.name} base/bebé debe tener Guardería en Sevii")

    def test_leafgreen_deoxys_defense_forme(self):
        cat = get_compiled_catalog("leafgreen", is_national=True)
        deoxys = [e for e in cat if e.pokemon.national_number == 386][0]
        self.assertIn("Forma Defensa", deoxys.obtaining_info.get("summary", ""))
        self.assertEqual(deoxys.pc_icon_url, "/media/pokemon/icons/gen3/10002.png")
        self.assertEqual(deoxys.game_sprite_url, "/media/pokemon/sprites/leafgreen/386.png")

    def test_leafgreen_ingame_trades(self):
        cat = get_compiled_catalog("leafgreen", is_national=True)
        cat_by_num = {e.pokemon.national_number: e for e in cat}

        # #32 Nidoran♂ recibido por Nidoran♀ en Ruta 5
        nidoran_m = cat_by_num[32]
        self.assertEqual(nidoran_m.obtaining_info.get("type"), "trade_npc")
        self.assertIn("Nidrán", nidoran_m.obtaining_info.get("summary", ""))
        self.assertIn("Nidoran♀", nidoran_m.obtaining_info.get("summary", ""))

        # #108 Lickitung recibido por Slowbro en Ruta 18
        licki = cat_by_num[108]
        self.assertEqual(licki.obtaining_info.get("type"), "trade_npc")
        self.assertIn("Slowbro", licki.obtaining_info.get("summary", ""))

    def test_leafgreen_exclusives_and_transfers_catalog(self):
        from tracker.exclusives import (
            GAME_COUNTERPARTS,
            VERSION_EXCLUSIVES_CATALOG,
            VERSION_TRANSFERS_CATALOG
        )
        self.assertIn("leafgreen", GAME_COUNTERPARTS)
        self.assertEqual(GAME_COUNTERPARTS["leafgreen"], ["firered"])
        self.assertIn("leafgreen", VERSION_EXCLUSIVES_CATALOG)
        self.assertEqual(len(VERSION_EXCLUSIVES_CATALOG["leafgreen"]), 23)
        self.assertIn(27, VERSION_EXCLUSIVES_CATALOG["leafgreen"])  # Sandshrew
        self.assertIn(37, VERSION_EXCLUSIVES_CATALOG["leafgreen"])  # Vulpix
        self.assertIn(69, VERSION_EXCLUSIVES_CATALOG["leafgreen"])  # Bellsprout
        self.assertIn(79, VERSION_EXCLUSIVES_CATALOG["leafgreen"])  # Slowpoke
        self.assertIn(120, VERSION_EXCLUSIVES_CATALOG["leafgreen"]) # Staryu
        self.assertIn(126, VERSION_EXCLUSIVES_CATALOG["leafgreen"]) # Magmar
        self.assertIn(127, VERSION_EXCLUSIVES_CATALOG["leafgreen"]) # Pinsir

        self.assertIn("leafgreen", VERSION_TRANSFERS_CATALOG)
        self.assertEqual(len(VERSION_TRANSFERS_CATALOG["leafgreen"]), 167)

        from tracker.exclusives import get_version_transfers_context
        # En la Pokédex Regional de Kanto NO debe haber transferencias
        self.assertIsNone(get_version_transfers_context(self.game, self.pk_kanto, set()))
        # En la Pokédex Nacional SÍ debe haber las 167 transferencias
        nat_transfers = get_version_transfers_context(self.game, self.pk_nat, set())
        self.assertIsNotNone(nat_transfers)
        self.assertEqual(nat_transfers["total"], 167)

    def test_leafgreen_offline_sprites_exist(self):
        from django.conf import settings
        base_media = settings.MEDIA_ROOT
        self.assertTrue(os.path.exists(os.path.join(base_media, "pokemon", "sprites", "leafgreen", "1.png")))
        self.assertTrue(os.path.exists(os.path.join(base_media, "pokemon", "sprites", "leafgreen", "386.png")))
        self.assertTrue(os.path.exists(os.path.join(base_media, "pokemon", "sprites", "leafgreen_shiny", "1.png")))
        self.assertTrue(os.path.exists(os.path.join(base_media, "pokemon", "sprites", "leafgreen_shiny", "386.png")))

    def test_leafgreen_views_and_national_regions_bar(self):
        resp_reg = self.client.get(reverse("tracker:pokedex_default", kwargs={"game_slug": "leafgreen"}))
        self.assertEqual(resp_reg.status_code, 200)
        self.assertContains(resp_reg, "Pokédex de Kanto")
        self.assertContains(resp_reg, "Bulbasaur")

        resp_nat = self.client.get(reverse("tracker:pokedex_detail", kwargs={"game_slug": "leafgreen", "pokedex_slug": "national"}))
        self.assertEqual(resp_nat.status_code, 200)
        self.assertContains(resp_nat, 'id="national-generation-bar"')
        self.assertContains(resp_nat, "Kanto")
        self.assertContains(resp_nat, "Johto")
        self.assertContains(resp_nat, "Hoenn")

    def test_leafgreen_filter_tags_across_national_regions(self):
        cat = get_compiled_catalog("leafgreen", is_national=True)
        # Kanto (Stone, Trade)
        raichu = next(e for e in cat if e.pokemon.name.lower() == "raichu")
        alakazam = next(e for e in cat if e.pokemon.name.lower() == "alakazam")
        self.assertIn("stone", raichu.filter_tags)
        self.assertIn("trade", alakazam.filter_tags)

        # Johto (Baby, Friendship, Stone)
        pichu = next(e for e in cat if e.pokemon.name.lower() == "pichu")
        crobat = next(e for e in cat if e.pokemon.name.lower() == "crobat")
        bellossom = next(e for e in cat if e.pokemon.name.lower() == "bellossom")
        self.assertIn("baby", pichu.filter_tags)
        self.assertIn("friendship", crobat.filter_tags)
        self.assertIn("stone", bellossom.filter_tags)

        # Hoenn (Stone, Baby)
        ludicolo = next(e for e in cat if e.pokemon.name.lower() == "ludicolo")
        shiftry = next(e for e in cat if e.pokemon.name.lower() == "shiftry")
        wynaut = next(e for e in cat if e.pokemon.name.lower() == "wynaut")
        self.assertIn("stone", ludicolo.filter_tags)
        self.assertIn("stone", shiftry.filter_tags)
        self.assertIn("baby", wynaut.filter_tags)


class PokemonDiamondGen4Tests(TestCase):
    """Pruebas unitarias para Pokémon Diamante (Gen 4), catálogos, exclusividades y barras nacionales."""

    def setUp(self):
        self.client = Client()
        self.game, _ = Game.objects.get_or_create(
            slug="diamond",
            defaults={"name": "Pokémon Diamante", "generation": 4}
        )
        self.pk_sinnoh, _ = Pokedex.objects.get_or_create(
            game=self.game,
            slug="sinnoh",
            defaults={"name": "Pokédex de Sinnoh", "is_national": False, "pokeapi_name": "original-sinnoh"}
        )
        self.pk_nat, _ = Pokedex.objects.get_or_create(
            game=self.game,
            slug="national",
            defaults={"name": "Pokédex Nacional", "is_national": True, "pokeapi_name": "national"}
        )

    def test_diamond_catalogs_exist_and_counts(self):
        from tracker.catalog_service import get_compiled_catalog, CATALOGS_DIR
        reg_file = CATALOGS_DIR / "diamond.json"
        nat_file = CATALOGS_DIR / "diamond_national.json"
        self.assertTrue(reg_file.exists(), "diamond.json debe existir")
        self.assertTrue(nat_file.exists(), "diamond_national.json debe existir")

        reg_cat = get_compiled_catalog("diamond", is_national=False, force_reload=True)
        nat_cat = get_compiled_catalog("diamond", is_national=True, force_reload=True)
        self.assertEqual(len(reg_cat), 151, "La Pokédex Regional de Sinnoh en Diamante debe tener 151 entradas")
        self.assertEqual(len(nat_cat), 493, "La Pokédex Nacional en Diamante debe tener 493 entradas")

    def test_diamond_regional_sinnoh_order_and_species(self):
        from tracker.catalog_service import get_compiled_catalog
        reg_cat = get_compiled_catalog("diamond", is_national=False)
        self.assertEqual(reg_cat[0].entry_number, 1)
        self.assertEqual(reg_cat[0].pokemon.name, "turtwig")
        self.assertEqual(reg_cat[0].pokemon.national_number, 387)

        # Dialga es el #149 en la Pokédex de Sinnoh
        dialga = [e for e in reg_cat if e.pokemon.name == "dialga"][0]
        self.assertEqual(dialga.entry_number, 149)
        self.assertEqual(dialga.pokemon.national_number, 483)

        # Palkia es el #150 en la Pokédex de Sinnoh
        palkia = [e for e in reg_cat if e.pokemon.name == "palkia"][0]
        self.assertEqual(palkia.entry_number, 150)
        self.assertEqual(palkia.pokemon.national_number, 484)

        # Manaphy es el #151 en la Pokédex de Sinnoh
        self.assertEqual(reg_cat[150].entry_number, 151)
        self.assertEqual(reg_cat[150].pokemon.name, "manaphy")
        self.assertEqual(reg_cat[150].pokemon.national_number, 490)

    def test_diamond_national_order_and_regions(self):
        from tracker.catalog_service import get_compiled_catalog
        nat_cat = get_compiled_catalog("diamond", is_national=True)
        self.assertEqual(nat_cat[0].entry_number, 1)
        self.assertEqual(nat_cat[0].pokemon.name, "bulbasaur")
        self.assertEqual(nat_cat[386].entry_number, 387)
        self.assertEqual(nat_cat[386].pokemon.name, "turtwig")
        self.assertEqual(nat_cat[482].entry_number, 483)
        self.assertEqual(nat_cat[482].pokemon.name, "dialga")
        self.assertEqual(nat_cat[492].entry_number, 493)
        self.assertEqual(nat_cat[492].pokemon.name, "arceus")
        arceus_obt = nat_cat[492].obtaining_info
        self.assertEqual(arceus_obt.get("type"), "gift")
        self.assertEqual(arceus_obt.get("badge_label"), "Evento de Distribución")
        self.assertIn("Flauta Azur", arceus_obt.get("historical_note", {}).get("text", ""))
        self.assertIn("eventos oficiales de distribución", arceus_obt.get("summary", "").lower())

        # Rotom y Heatran con nombres oficiales en español (Vieja Mansión, Montaña Dura)
        rotom_obt = nat_cat[478].obtaining_info
        self.assertEqual(rotom_obt.get("badge_label"), "Vieja Mansión")
        self.assertIn("Vieja Mansión", rotom_obt.get("summary", ""))
        self.assertEqual(rotom_obt.get("locations", [])[0].get("area"), "Vieja Mansión (Televisor)")

        heatran_obt = nat_cat[484].obtaining_info
        self.assertIn("Montaña Dura", heatran_obt.get("summary", ""))
        self.assertIn("Montaña Dura", heatran_obt.get("locations", [])[0].get("area", ""))

    def test_diamond_exclusives_and_transfers_catalog(self):
        from tracker.exclusives import (
            GAME_COUNTERPARTS,
            VERSION_EXCLUSIVES_CATALOG,
            VERSION_TRANSFERS_CATALOG,
            get_version_transfers_context
        )
        self.assertIn("diamond", GAME_COUNTERPARTS)
        self.assertEqual(GAME_COUNTERPARTS["diamond"], ["pearl"])
        self.assertIn("diamond", VERSION_EXCLUSIVES_CATALOG)
        self.assertEqual(len(VERSION_EXCLUSIVES_CATALOG["diamond"]), 20)
        self.assertIn(408, VERSION_EXCLUSIVES_CATALOG["diamond"])  # Cranidos
        self.assertIn(434, VERSION_EXCLUSIVES_CATALOG["diamond"])  # Stunky
        self.assertIn(483, VERSION_EXCLUSIVES_CATALOG["diamond"])  # Dialga

        self.assertIn("diamond", VERSION_TRANSFERS_CATALOG)
        self.assertEqual(len(VERSION_TRANSFERS_CATALOG["diamond"]), 48)

        # En la Pokédex Regional de Sinnoh NO debe haber modal de transferencias
        self.assertIsNone(get_version_transfers_context(self.game, self.pk_sinnoh, set()))
        # En la Pokédex Nacional SÍ debe haber las 48 transferencias del Parque Compi
        nat_transfers = get_version_transfers_context(self.game, self.pk_nat, set())
        self.assertIsNotNone(nat_transfers)
        self.assertEqual(nat_transfers["total"], 48)
        self.assertEqual(nat_transfers["mechanic_badge"], "Parque Compi")

    def test_diamond_evolution_items_and_stones(self):
        from tracker.catalog_service import get_compiled_catalog
        nat_cat = get_compiled_catalog("diamond", is_national=True)
        cat_by_num = {e.pokemon.national_number: e for e in nat_cat}

        # Roserade con Piedra Día
        roserade = cat_by_num[407]
        self.assertEqual(roserade.obtaining_info.get("type"), "evolution")
        self.assertIsNotNone(roserade.evolution_stone)
        self.assertEqual(roserade.evolution_stone.get("slug"), "shiny-stone")

        # Honchkrow con Piedra Noche
        honchkrow = cat_by_num[430]
        self.assertEqual(honchkrow.obtaining_info.get("type"), "evolution")
        self.assertIsNotNone(honchkrow.evolution_stone)
        self.assertEqual(honchkrow.evolution_stone.get("slug"), "dusk-stone")

        # Gallade con Piedra Alba
        gallade = cat_by_num[475]
        self.assertEqual(gallade.obtaining_info.get("type"), "evolution")
        self.assertIsNotNone(gallade.evolution_stone)
        self.assertEqual(gallade.evolution_stone.get("slug"), "dawn-stone")

        # Steelix (#208): Especie salvaje pero con evolución por intercambio con Revestimiento Metálico
        steelix = cat_by_num[208]
        self.assertIsNotNone(steelix.evolution_stone, "Steelix debe tener Revestimiento Metálico como evolution_stone")
        self.assertEqual(steelix.evolution_stone.get("slug"), "metal-coat")
        self.assertIsNotNone(steelix.obtaining_info.get("evolution_info"), "Steelix debe preservar evolution_info de Onix")

        # Chansey (#113): Especie salvaje que evoluciona de Happiny con Piedra Oval
        chansey = cat_by_num[113]
        self.assertIsNotNone(chansey.evolution_stone, "Chansey debe tener Piedra Oval como evolution_stone")
        self.assertEqual(chansey.evolution_stone.get("slug"), "oval-stone")
        self.assertIn("Piedra Oval", chansey.obtaining_info.get("evolution_info", {}).get("text", ""))

        # Mismagius (#429): Exclusivo transferible/intercambio en Diamante que evoluciona con Piedra Noche
        mismagius = cat_by_num[429]
        self.assertIsNotNone(mismagius.evolution_stone, "Mismagius debe tener Piedra Noche como evolution_stone")
        self.assertEqual(mismagius.evolution_stone.get("slug"), "dusk-stone")

        # Comprobación de bebés e inciensos de 4.ª Generación
        incense_expectations = {
            406: ("rose-incense", "Incienso Floral"),
            433: ("pure-incense", "Incienso Puro"),
            438: ("rock-incense", "Incienso Roca"),
            439: ("odd-incense", "Incienso Raro"),
            440: ("luck-incense", "Incienso Duplo"),
            446: ("full-incense", "Incienso Lento"),
            458: ("wave-incense", "Incienso Aqua"),
            298: ("sea-incense", "Incienso Marino"),
            360: ("lax-incense", "Incienso Suave"),
        }
        for nat_id, (slug, name) in incense_expectations.items():
            baby_entry = cat_by_num[nat_id]
            self.assertIsNotNone(baby_entry.evolution_stone, f"Bebé #{nat_id} debe tener evolution_stone con {slug}")
            self.assertEqual(baby_entry.evolution_stone.get("slug"), slug)
            daycare = next((l for l in baby_entry.obtaining_info.get("locations", []) if "guardería" in l.get("area", "").lower()), None)
            self.assertIsNotNone(daycare, f"Bebé #{nat_id} debe tener Guardería")
            self.assertIn(name, daycare.get("method", ""), f"Guardería de bebé #{nat_id} debe especificar {name}")

    def test_diamond_breeding_golden_rule(self):
        from tracker.catalog_service import get_compiled_catalog
        nat_cat = get_compiled_catalog("diamond", is_national=True)
        cat_by_num = {e.pokemon.national_number: e for e in nat_cat}

        # Formas base y bebés sí son eclosionables y mencionan crianza
        for num in [387, 390, 393, 403, 406, 447]:
            entry = cat_by_num[num]
            daycare_locs = [l for l in entry.obtaining_info.get("locations", []) if "guardería" in l.get("area", "").lower()]
            self.assertTrue(len(daycare_locs) > 0, f"#{num} {entry.pokemon.name} base/bebé debe tener Guardería en Sinnoh")

        # Evoluciones y legendarios NUNCA deben tener Guardería
        for num in [388, 389, 391, 392, 405, 448, 483, 484, 487, 493]:
            entry = cat_by_num[num]
            daycare_locs = [l for l in entry.obtaining_info.get("locations", []) if "guardería" in l.get("area", "").lower()]
            self.assertEqual(len(daycare_locs), 0, f"#{num} {entry.pokemon.name} evolucionado/legendario no debe tener Guardería")

    def test_diamond_offline_sprites_exist(self):
        from django.conf import settings
        base_media = settings.MEDIA_ROOT
        self.assertTrue(os.path.exists(os.path.join(base_media, "pokemon", "sprites", "diamond", "1.png")))
        self.assertTrue(os.path.exists(os.path.join(base_media, "pokemon", "sprites", "diamond", "387.png")))
        self.assertTrue(os.path.exists(os.path.join(base_media, "pokemon", "sprites", "diamond", "483.png")))
        self.assertTrue(os.path.exists(os.path.join(base_media, "pokemon", "sprites", "diamond", "493.png")))
        self.assertTrue(os.path.exists(os.path.join(base_media, "pokemon", "sprites", "diamond_shiny", "1.png")))
        self.assertTrue(os.path.exists(os.path.join(base_media, "pokemon", "sprites", "diamond_shiny", "387.png")))
        self.assertTrue(os.path.exists(os.path.join(base_media, "pokemon", "sprites", "diamond_shiny", "483.png")))
        self.assertTrue(os.path.exists(os.path.join(base_media, "pokemon", "sprites", "diamond_shiny", "493.png")))

    def test_diamond_views_and_theming(self):
        resp_reg = self.client.get(reverse("tracker:pokedex_default", kwargs={"game_slug": "diamond"}))
        self.assertEqual(resp_reg.status_code, 200)
        self.assertContains(resp_reg, 'data-game="diamond"')
        self.assertContains(resp_reg, "Turtwig")

        resp_nat = self.client.get(reverse("tracker:pokedex_detail", kwargs={"game_slug": "diamond", "pokedex_slug": "national"}))
        self.assertEqual(resp_nat.status_code, 200)
        self.assertContains(resp_nat, 'id="national-generation-bar"')
        self.assertContains(resp_nat, "Kanto")
        self.assertContains(resp_nat, "Johto")
        self.assertContains(resp_nat, "Hoenn")
        self.assertContains(resp_nat, "Sinnoh")

    def test_diamond_unown_canonical_f_and_chambers(self):
        """
        Valida que en Pokémon Diamante:
        1. get_game_unown_chambers retorne las 3 estructuras de Ruinas Sosiego (friend, dead_ends, secret).
        2. get_unown_catalog retorne las 28 formas con rutas /media/pokemon/sprites/diamond/unown/ e iconos gen4.
        3. get_pokemon_forms retorne las 28 formas con la forma F como primera por defecto.
        4. Las ubicaciones de Sinnoh detallen la Ruta Central FRIEND, las salas sin salida y la cámara superior vía Túnel Ruinamaníaco.
        5. Los archivos de sprites de Unown para Diamante existan en el sistema de archivos.
        6. La vista de Diamante renderice is_sinnoh=True, las pestañas de Ruinas Sosiego y la guía de encuentro.
        """
        from tracker.unown_data import get_unown_catalog, get_game_unown_chambers, SINNOH_UNOWN_CHAMBERS
        from tracker.pokemon_forms import get_pokemon_forms
        from django.conf import settings
        from pathlib import Path

        # 1. Cámaras de Sinnoh
        chambers = get_game_unown_chambers("diamond")
        self.assertEqual(chambers, SINNOH_UNOWN_CHAMBERS)
        self.assertIn("friend", chambers)
        self.assertIn("dead_ends", chambers)
        self.assertIn("secret", chambers)
        self.assertEqual(chambers["friend"]["letters"], ["f", "r", "i", "e", "n", "d"])
        self.assertEqual(chambers["secret"]["letters"], ["exclamation", "question"])

        # 2. Catálogo de 28 formas con assets de Diamante y Gen 4
        cat = get_unown_catalog("diamond")
        self.assertEqual(len(cat), 28)
        self.assertEqual(cat[0]["sprite_normal"], "/media/pokemon/sprites/diamond/unown/a.png")
        self.assertEqual(cat[0]["icon_url"], "/media/pokemon/icons/gen4/201-a.png")

        # 3. Formas: F debe ser la primera por defecto
        forms = get_pokemon_forms(201, "diamond")
        self.assertEqual(len(forms), 28)
        self.assertEqual(forms[0]["form_key"], "f")
        self.assertEqual(forms[0]["name"], "Unown [F]")
        self.assertEqual(forms[0]["sprite_retro"], "/media/pokemon/sprites/diamond/unown/f.png")

        # 4. Ubicaciones exactas
        forms_by_key = {f["form_key"]: f for f in forms}
        self.assertIn("Ruinas Sosiego (Ruta Central - Sala F)", forms_by_key["f"]["locations"][0]["area"])
        self.assertEqual(forms_by_key["f"]["locations"][0]["method"], "Salvaje (Tasa: 100%)")
        self.assertIn("Ruinas Sosiego (Salas Sin Salida)", forms_by_key["a"]["locations"][0]["area"])
        self.assertIn("Cámara Superior Secreta", forms_by_key["exclamation"]["locations"][0]["area"])
        self.assertIn("Túnel Ruinamaniaco", forms_by_key["exclamation"]["locations"][0]["method"])

        # 5. Existencia de sprites en disco
        base_media = Path(settings.MEDIA_ROOT)
        self.assertTrue((base_media / "pokemon" / "sprites" / "diamond" / "201.png").exists())
        self.assertTrue((base_media / "pokemon" / "sprites" / "diamond" / "unown" / "f.png").exists())
        self.assertTrue((base_media / "pokemon" / "sprites" / "diamond" / "unown" / "exclamation.png").exists())
        self.assertTrue((base_media / "pokemon" / "sprites" / "diamond" / "unown" / "question.png").exists())

        # 6. Renderizado en vista
        resp = self.client.get(reverse("tracker:pokedex_default", kwargs={"game_slug": "diamond"}))
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.context["is_sinnoh"])
        self.assertContains(resp, 'id="unown-tab-friend"')
        self.assertContains(resp, 'id="unown-tab-dead_ends"')
        self.assertContains(resp, 'id="unown-tab-secret"')
        self.assertContains(resp, 'Ruinas Sosiego')
        self.assertContains(resp, 'id="unown-sinnoh-note"')








