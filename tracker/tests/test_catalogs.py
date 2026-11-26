import json
import os
from unittest.mock import patch
from django.test import TestCase, Client
from django.urls import reverse
from tracker.models import Game, Pokedex, UserPokemonCatch
from tracker.catalog_service import CatalogPokemon, CatalogEntry, get_compiled_catalog, get_catalog_entry_by_id
from tracker.tests.mocks import Pokemon, PokedexEntry, Move

class CompiledCatalogsAndServiceTests(TestCase):
    """Pruebas unitarias para los catálogos JSON estáticos precompilados en memoria y CatalogService."""

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
        self.assertIsNone(get_compiled_catalog("nonexistent_game"))
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

        # summary narratives and location-based evolutions must NOT leak false zones into filter_locations
        black_nat = get_compiled_catalog("black", force_reload=True, is_national=True)
        b_by = {e.pokemon.national_number: e for e in black_nat}
        psyduck_b = b_by[54]
        self.assertIn("guardería", psyduck_b.filter_locations.lower())
        for false_zone in ("ruta 11", "ruta 14", "puente villa"):
            self.assertNotIn(false_zone, psyduck_b.filter_locations.lower())
        self.assertIn("Ruta 11", psyduck_b.obtaining_info["summary"])
        self.assertNotIn("bosque blanco", b_by[16].filter_locations.lower())  # Pidgey
        self.assertNotIn("cueva loza", b_by[639].filter_locations.lower())    # Terrakion
        for evo_id, card_hint in ((462, "Cueva Electrorroca"), (470, "Bosque Azulejo"), (471, "Monte Tuerca"), (476, "Cueva Electrorroca")):
            self.assertEqual(b_by[evo_id].filter_locations, "")
            self.assertIn(card_hint, b_by[evo_id].obtaining_info["summary"])

        # Data fixes across Gen 2, FR/LG, Sinnoh & HG/SS
        for g2_slug in ("gold", "silver", "crystal"):
            g2 = {e.pokemon.national_number: e for e in get_compiled_catalog(g2_slug, force_reload=True)}
            self.assertIn("ruta 33", g2[21].filter_locations.lower())
            self.assertIn("monte mortero", g2[66].filter_locations.lower())
            self.assertIn("ruta 28", g2[78].filter_locations.lower())
            self.assertIn("cueva unión", g2[95].filter_locations.lower())
            self.assertIn("ruta 10", g2[100].filter_locations.lower())
            if g2_slug == "crystal":
                self.assertIn("calle victoria", g2[112].filter_locations.lower())
                self.assertIn("ruta 45", g2[147].filter_locations.lower())
            else:
                self.assertNotIn("calle victoria", g2[112].filter_locations.lower())

        for g3_kanto in ("firered", "leafgreen"):
            fr_cat = {e.pokemon.national_number: e for e in get_compiled_catalog(g3_kanto, force_reload=True)}
            self.assertIn("ruta 6", fr_cat[129].filter_locations.lower())
            self.assertIn("ruta 12", fr_cat[129].filter_locations.lower())
            self.assertNotIn("cualquier masa de agua", fr_cat[129].filter_locations.lower())
            self.assertIn("isla prima", fr_cat[146].filter_locations.lower())

        d_by = {e.pokemon.national_number: e for e in diamond_cat}
        self.assertIn("ruta 212", d_by[137].filter_locations.lower())
        self.assertIn("bosque vetusto", d_by[479].filter_locations.lower())
        self.assertIn("ruta 224", d_by[492].filter_locations.lower())
        self.assertIn("isla plenilunio", d_by[488].filter_locations.lower())

        ss_reg = {e.pokemon.national_number: e for e in get_compiled_catalog("soulsilver", force_reload=True)}
        ss_nat = {e.pokemon.national_number: e for e in get_compiled_catalog("soulsilver", force_reload=True, is_national=True)}
        self.assertEqual(ss_reg[140].obtaining_info["type"], "fossil")
        self.assertEqual(ss_reg[138].obtaining_info["type"], "trade")
        self.assertIn("ruta 26", ss_reg[28].filter_locations.lower())
        self.assertIn("ruta 27", ss_reg[28].filter_locations.lower())
        self.assertIn("monte moon", ss_reg[28].filter_locations.lower())
        self.assertIn("ruta 27", ss_reg[85].filter_locations.lower())
        self.assertNotIn("zona safari", ss_reg[112].filter_locations.lower())
        self.assertNotIn("zona safari", ss_reg[229].filter_locations.lower())
        self.assertIn("silph s.a.", ss_nat[374].filter_locations.lower())
        
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

        # 2. Formas en get_pokemon_forms: lista en orden alfabético estricto
        forms_fr = get_pokemon_forms(201, "firered")
        self.assertEqual(len(forms_fr), 28)
        self.assertEqual(forms_fr[0]["form_key"], "a")
        f_form = next(f for f in forms_fr if f["form_key"] == "f")
        self.assertEqual(f_form["chamber_key"], "hibinca")
        self.assertEqual(len(f_form["locations"]), 1)
        self.assertEqual(f_form["locations"][0]["area"], "Cámara Hibinca (Ruinas Sete)")

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
        self.assertEqual(arceus_obt.get("type"), "event")
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
            get_version_transfers_context,
            get_version_exclusives_context
        )
        self.assertIn("diamond", GAME_COUNTERPARTS)
        self.assertEqual(GAME_COUNTERPARTS["diamond"], ["pearl"])
        self.assertIn("diamond", VERSION_EXCLUSIVES_CATALOG)
        self.assertEqual(len(VERSION_EXCLUSIVES_CATALOG["diamond"]), 20)
        self.assertIn(408, VERSION_EXCLUSIVES_CATALOG["diamond"])  # Cranidos
        self.assertIn(434, VERSION_EXCLUSIVES_CATALOG["diamond"])  # Stunky
        self.assertIn(483, VERSION_EXCLUSIVES_CATALOG["diamond"])  # Dialga

        excl_ctx = get_version_exclusives_context(self.game, self.pk_sinnoh, set())
        self.assertIsNotNone(excl_ctx)
        self.assertEqual(excl_ctx["own_theme"], "diamond")
        self.assertEqual(excl_ctx["counterpart_theme"], "pearl")

        self.assertIn("diamond", VERSION_TRANSFERS_CATALOG)
        self.assertEqual(len(VERSION_TRANSFERS_CATALOG["diamond"]), 90)

        # En la Pokédex Regional de Sinnoh NO debe haber modal de transferencias
        self.assertIsNone(get_version_transfers_context(self.game, self.pk_sinnoh, set()))
        # En la Pokédex Nacional SÍ debe haber las 90 transferencias legítimas
        nat_transfers = get_version_transfers_context(self.game, self.pk_nat, set())
        self.assertIsNotNone(nat_transfers)
        self.assertEqual(nat_transfers["total"], 90)
        self.assertEqual(nat_transfers["mechanic_badge"], "Transferir / GBA")
        # Verificar que especies clave estén presentes en transferencias
        self.assertTrue(any(p["national_number"] == 114 for p in nat_transfers["transfer_list"]))  # Tangela
        self.assertTrue(any(p["national_number"] == 465 for p in nat_transfers["transfer_list"]))  # Tangrowth
        self.assertTrue(any(p["national_number"] == 357 for p in nat_transfers["transfer_list"]))  # Tropius
        self.assertTrue(any(p["national_number"] == 273 for p in nat_transfers["transfer_list"]))  # Seedot (Dual Rubí)
        self.assertTrue(any(p["national_number"] == 270 for p in nat_transfers["transfer_list"]))  # Lotad (Dual Zafiro)
        self.assertTrue(any(p["national_number"] == 204 for p in nat_transfers["transfer_list"]))  # Pineco (Dual Esmeralda)
        # Gengar (#94) NO debe estar en transferencias (Gastly y Haunter son salvajes en Sinnoh y Gengar se obtiene evolucionando por intercambio)
        self.assertFalse(any(p["national_number"] == 94 for p in nat_transfers["transfer_list"]))
        # Verificar que especies obtenibles in-game (Weezing salvaje / Koffing por huevo) NO estén en transferencias
        self.assertFalse(any(p["national_number"] == 109 for p in nat_transfers["transfer_list"]))  # Koffing
        self.assertFalse(any(p["national_number"] == 110 for p in nat_transfers["transfer_list"]))  # Weezing
        self.assertFalse(any(p["national_number"] == 360 for p in nat_transfers["transfer_list"]))  # Wynaut (cría de Wobbuffet)

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

        # Gengar (#94): Evolución por intercambio de Haunter y encuentro salvaje por Inserción Dual (Cualquier GBA)
        gengar = cat_by_num[94]
        self.assertEqual(gengar.obtaining_info.get("type"), "evolution")
        self.assertIn("Haunter", gengar.obtaining_info.get("summary", ""))
        self.assertIn("Vieja Mansión", gengar.obtaining_info.get("summary", ""))
        self.assertEqual(gengar.obtaining_info.get("locations", [])[0]["area"], "Vieja Mansión (Habitación del Cuadro)")
        self.assertEqual(gengar.obtaining_info.get("locations", [])[0]["method"], "Inserción Dual (Cualquier GBA)")

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
        for num in [94, 388, 389, 391, 392, 405, 448, 483, 484, 487, 493]:
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

    def test_diamond_cries_exist_and_resolve_legacy(self):
        from tracker.catalog_service import get_compiled_catalog
        nat_cat = get_compiled_catalog("diamond", is_national=True)
        self.assertIsNotNone(nat_cat)
        # Azelf (#482) y Dialga (#483) deben apuntar a legacy y existir en disco
        azelf = next(e for e in nat_cat if e.pokemon.national_number == 482)
        self.assertEqual(azelf.cry_url, "/media/pokemon/cries/legacy/482.ogg")
        dialga = next(e for e in nat_cat if e.pokemon.national_number == 483)
        self.assertEqual(dialga.cry_url, "/media/pokemon/cries/legacy/483.ogg")
        from django.conf import settings
        self.assertTrue(os.path.exists(os.path.join(settings.MEDIA_ROOT, "pokemon", "cries", "legacy", "482.ogg")))
        self.assertTrue(os.path.exists(os.path.join(settings.MEDIA_ROOT, "pokemon", "cries", "legacy", "483.ogg")))
        self.assertTrue(os.path.exists(os.path.join(settings.MEDIA_ROOT, "pokemon", "cries", "legacy", "387.ogg")))
        self.assertTrue(os.path.exists(os.path.join(settings.MEDIA_ROOT, "pokemon", "cries", "legacy", "493.ogg")))

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

        # 3. Formas: lista en orden alfabético estricto (A-Z)
        forms = get_pokemon_forms(201, "diamond")
        self.assertEqual(len(forms), 28)
        self.assertEqual(forms[0]["form_key"], "a")
        f_form = next(f for f in forms if f["form_key"] == "f")
        self.assertEqual(f_form["name"], "Unown [F]")
        self.assertEqual(f_form["sprite_retro"], "/media/pokemon/sprites/diamond/unown/f.png")

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

    def test_diamond_filter_tags_and_mechanics(self):
        """Valida que Pokémon Diamante active los filtros correctos de Sinnoh (Gran Pantano, Miel, Radar, Dual)."""
        from tracker.catalog_service import get_compiled_catalog

        # Propiedades de modelo
        self.assertTrue(self.game.has_great_marsh)
        self.assertTrue(self.game.has_honey_trees)
        self.assertTrue(self.game.has_poke_radar)
        self.assertTrue(self.game.has_dual_slot)
        self.assertFalse(self.game.has_safari_zone)

        # Tags en catálogo Regional
        reg_cat = get_compiled_catalog("diamond", is_national=False)
        starly = next(e for e in reg_cat if e.pokemon.national_number == 396)
        self.assertIn("great_marsh", starly.filter_tags)

        burmy = next(e for e in reg_cat if e.pokemon.national_number == 412)
        self.assertIn("honey_tree", burmy.filter_tags)

        # Tags en catálogo Nacional
        nat_cat = get_compiled_catalog("diamond", is_national=True)
        nidoran = next(e for e in nat_cat if e.pokemon.national_number == 29)
        self.assertIn("radar", nidoran.filter_tags)

        caterpie = next(e for e in nat_cat if e.pokemon.national_number == 10)
        self.assertIn("dual_slot", caterpie.filter_tags)

        # Tropius (#357) es exclusivamente transferible en Diamante y NO debe recibir el tag great_marsh
        tropius = next(e for e in nat_cat if e.pokemon.national_number == 357)
        self.assertNotIn("great_marsh", tropius.filter_tags)

        # Visibilidad del Poké Radar: solo en Pokédex Nacional, desactivado/oculto en Regional
        resp_reg = self.client.get(reverse("tracker:pokedex_default", kwargs={"game_slug": "diamond"}))
        self.assertEqual(resp_reg.status_code, 200)
        self.assertNotContains(resp_reg, 'data-tag="radar"')
        self.assertNotContains(resp_reg, 'data-tag="swarm"')

        resp_nat = self.client.get(reverse("tracker:pokedex_detail", kwargs={"game_slug": "diamond", "pokedex_slug": "national"}))
        self.assertEqual(resp_nat.status_code, 200)
        self.assertContains(resp_nat, 'data-tag="radar"')
        self.assertContains(resp_nat, 'data-tag="swarm"')

        # Manadas Pokémon (Brotes diarios) en Sinnoh
        self.assertTrue(self.game.has_swarms)
        beldum = next(e for e in nat_cat if e.pokemon.national_number == 374)
        pidgey = next(e for e in nat_cat if e.pokemon.national_number == 16)
        self.assertIn("swarm", beldum.filter_tags)
        self.assertIn("swarm", pidgey.filter_tags)

        # Regalo / NPC: Manaphy, Arceus, Togepi y Porygon NO deben recibir tag gift
        manaphy = next(e for e in nat_cat if e.pokemon.national_number == 490)
        arceus = next(e for e in nat_cat if e.pokemon.national_number == 493)
        togepi = next(e for e in nat_cat if e.pokemon.national_number == 175)
        porygon = next(e for e in nat_cat if e.pokemon.national_number == 137)
        eevee = next(e for e in nat_cat if e.pokemon.national_number == 133)
        self.assertNotIn("gift", manaphy.filter_tags)
        self.assertNotIn("gift", arceus.filter_tags)
        self.assertNotIn("gift", togepi.filter_tags)
        self.assertNotIn("gift", porygon.filter_tags)
        self.assertIn("radar", togepi.filter_tags)
        self.assertEqual(togepi.obtaining_info.get("type"), "wild")
        self.assertEqual(togepi.obtaining_info.get("badge_label"), "Poké Radar")
        self.assertIn("gift", eevee.filter_tags)

        # Cañas de pescar: Giratina no debe tener rod_super (por palabra 'superar')
        # ni Gastly/Rotom rod_old (por 'Vieja Mansión')
        giratina = next(e for e in nat_cat if e.pokemon.national_number == 487)
        gastly = next(e for e in nat_cat if e.pokemon.national_number == 92)
        rotom = next(e for e in nat_cat if e.pokemon.national_number == 479)
        crawdaunt = next(e for e in nat_cat if e.pokemon.national_number == 342)
        self.assertNotIn("rod_super", giratina.filter_tags)
        self.assertNotIn("rod_any", giratina.filter_tags)
        self.assertNotIn("rod_old", gastly.filter_tags)
        self.assertNotIn("rod_any", gastly.filter_tags)
        self.assertNotIn("rod_old", rotom.filter_tags)
        self.assertNotIn("rod_any", rotom.filter_tags)
        self.assertIn("rod_super", crawdaunt.filter_tags)
        self.assertIn("rod_any", crawdaunt.filter_tags)

    def test_gen4_pokemon_alternate_forms(self):
        """Valida que todas las formas canónicas de Gen 4 en Diamante (regional y nacional)
        estén correctamente configuradas, con tipos elementales, notas canónicas, ubicaciones
        y rutas de sprites nativos de Sinnoh."""
        from tracker.catalog_service import get_compiled_catalog
        import json

        diamond_reg = get_compiled_catalog("diamond", is_national=False)
        diamond_nat = get_compiled_catalog("diamond", is_national=True)

        # 1. Castform (#351) en Diamante Nacional: Sprites nativos de Gen 4
        castform = next(e for e in diamond_nat if e.pokemon.national_number == 351)
        self.assertEqual(len(castform.forms), 4)
        self.assertIn("/media/pokemon/sprites/diamond/351.png", castform.forms[0]["sprite_retro"])
        self.assertIn("/media/pokemon/sprites/diamond/castform/sunny.png", castform.forms[1]["sprite_retro"])
        self.assertIn("/media/pokemon/sprites/diamond/castform/rainy.png", castform.forms[2]["sprite_retro"])
        self.assertIn("/media/pokemon/sprites/diamond/castform/snowy.png", castform.forms[3]["sprite_retro"])
        self.assertEqual(castform.forms[1]["modal_retro_sprite_url"], "/media/pokemon/sprites/diamond_animated/castform/sunny.png")
        self.assertEqual(castform.forms[2]["modal_retro_sprite_url"], "/media/pokemon/sprites/diamond_animated/castform/rainy.png")
        self.assertEqual(castform.forms[3]["modal_retro_sprite_url"], "/media/pokemon/sprites/diamond_animated/castform/snowy.png")
        self.assertEqual(castform.forms[1]["primary_type_es"], "Fuego")
        self.assertEqual(castform.forms[2]["primary_type_es"], "Agua")
        self.assertEqual(castform.forms[3]["primary_type_es"], "Hielo")
        self.assertTrue(len(castform.forms[0]["notes"]) > 0)
        self.assertIn("Predicción", castform.forms[0]["notes"][0]["title"])

        # 2. Deoxys (#386) en Diamante Nacional: 4 formas y notas de meteoritos
        deoxys = next(e for e in diamond_nat if e.pokemon.national_number == 386)
        self.assertEqual(len(deoxys.forms), 4)
        form_names = [f["name"] for f in deoxys.forms]
        self.assertEqual(form_names, ["Forma Normal", "Forma Ataque", "Forma Defensa", "Forma Velocidad"])
        self.assertIn("meteorito", deoxys.forms[1]["notes"][0]["text"].lower())
        self.assertIn("Ciudad Rocavelo", deoxys.forms[1]["notes"][0]["text"])

        # 3. Burmy (#412) en Diamante Regional: 3 troncos con notas de entorno y crianza
        burmy = next(e for e in diamond_reg if e.pokemon.national_number == 412)
        self.assertEqual(len(burmy.forms), 3)
        self.assertEqual([f["form_key"] for f in burmy.forms], ["plant", "sandy", "trash"])
        burmy_notes_text = " ".join(f"{n['title']} {n['text']}" for n in burmy.forms[0]["notes"])
        self.assertIn("huevo", burmy_notes_text.lower())
        self.assertIn("eclosi", burmy_notes_text.lower())

        # 4. Wormadam (#413): 3 troncos fijos con tipos elementales distintos
        wormadam = next(e for e in diamond_reg if e.pokemon.national_number == 413)
        self.assertEqual(len(wormadam.forms), 3)
        self.assertEqual(wormadam.forms[0]["secondary_type_es"], "Planta")
        self.assertEqual(wormadam.forms[1]["secondary_type_es"], "Tierra")
        self.assertEqual(wormadam.forms[2]["secondary_type_es"], "Acero")
        self.assertEqual(wormadam.forms[0]["secondary_type"], "grass")
        self.assertEqual(wormadam.forms[1]["secondary_type"], "ground")
        self.assertEqual(wormadam.forms[2]["secondary_type"], "steel")

        # 5. Cherrim (#421): 2 formas (Encapuchada y Soleada) con Don Floral
        cherrim = next(e for e in diamond_reg if e.pokemon.national_number == 421)
        self.assertEqual(len(cherrim.forms), 2)
        self.assertEqual(cherrim.forms[0]["name"], "Forma Encapuchada")
        self.assertEqual(cherrim.forms[1]["name"], "Forma Soleada")
        self.assertIn("Don Floral", cherrim.forms[1]["notes"][0]["tag"])

        # 6. Shellos (#422) y Gastrodon (#423): Mar Oeste vs Mar Este delimitados por Monte Corona
        shellos = next(e for e in diamond_reg if e.pokemon.national_number == 422)
        self.assertEqual(len(shellos.forms), 2)
        self.assertEqual(shellos.forms[0]["name"], "Mar Oeste")
        self.assertEqual(shellos.forms[1]["name"], "Mar Este")
        self.assertIn("Ruta 205", [loc["area"] for loc in shellos.forms[0]["locations"]])
        self.assertIn("Ruta 213", [loc["area"] for loc in shellos.forms[1]["locations"]])

        gastrodon = next(e for e in diamond_reg if e.pokemon.national_number == 423)
        self.assertEqual(len(gastrodon.forms), 2)
        self.assertIn("Ruta 205", [loc["area"] for loc in gastrodon.forms[0]["locations"]])
        self.assertIn("Ruta 213", [loc["area"] for loc in gastrodon.forms[1]["locations"]])

        # 7. Arceus (#493): 17 formas (Normal + 16 tablas elementales, SIN hada ni tabla duende)
        arceus = next(e for e in diamond_nat if e.pokemon.national_number == 493)
        self.assertEqual(len(arceus.forms), 17)
        arceus_types = [f["primary_type"] for f in arceus.forms]
        self.assertNotIn("fairy", arceus_types)
        self.assertIn("normal", arceus_types)
        self.assertIn("fire", arceus_types)
        self.assertIn("water", arceus_types)
        self.assertIn("electric", arceus_types)
        self.assertIn("grass", arceus_types)
        self.assertIn("ice", arceus_types)
        self.assertIn("fighting", arceus_types)
        self.assertIn("poison", arceus_types)
        self.assertIn("ground", arceus_types)
        self.assertIn("flying", arceus_types)
        self.assertIn("psychic", arceus_types)
        self.assertIn("bug", arceus_types)
        self.assertIn("rock", arceus_types)
        self.assertIn("ghost", arceus_types)
        self.assertIn("dragon", arceus_types)
        self.assertIn("steel", arceus_types)
        self.assertIn("dark", arceus_types)

        # 8. Unown (#201): 28 formas intactas
        unown = next(e for e in diamond_reg if e.pokemon.national_number == 201)
        self.assertEqual(len(unown.forms), 28)


class PokemonPearlGen4Tests(TestCase):
    """Pruebas unitarias para Pokémon Perla (Gen 4), catálogos, exclusividades y barras nacionales."""

    def setUp(self):
        self.client = Client()
        self.game, _ = Game.objects.get_or_create(
            slug="pearl",
            defaults={"name": "Pokémon Perla", "generation": 4}
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

    def test_pearl_catalogs_exist_and_counts(self):
        from tracker.catalog_service import get_compiled_catalog, CATALOGS_DIR
        reg_file = CATALOGS_DIR / "pearl.json"
        nat_file = CATALOGS_DIR / "pearl_national.json"
        self.assertTrue(reg_file.exists(), "pearl.json debe existir")
        self.assertTrue(nat_file.exists(), "pearl_national.json debe existir")

        reg_cat = get_compiled_catalog("pearl", is_national=False, force_reload=True)
        nat_cat = get_compiled_catalog("pearl", is_national=True, force_reload=True)
        self.assertEqual(len(reg_cat), 151, "La Pokédex Regional de Sinnoh en Perla debe tener 151 entradas")
        self.assertEqual(len(nat_cat), 493, "La Pokédex Nacional en Perla debe tener 493 entradas")

    def test_pearl_regional_sinnoh_order_and_species(self):
        from tracker.catalog_service import get_compiled_catalog
        reg_cat = get_compiled_catalog("pearl", is_national=False)
        self.assertEqual(reg_cat[0].entry_number, 1)
        self.assertEqual(reg_cat[0].pokemon.name, "turtwig")
        self.assertEqual(reg_cat[0].pokemon.national_number, 387)

        # Dialga es el #149 en la Pokédex de Sinnoh
        dialga = [e for e in reg_cat if e.pokemon.name == "dialga"][0]
        self.assertEqual(dialga.entry_number, 149)
        self.assertEqual(dialga.pokemon.national_number, 483)

        # Palkia es el #150 en la Pokédex de Sinnoh (Legendario insignia de Perla)
        palkia = [e for e in reg_cat if e.pokemon.name == "palkia"][0]
        self.assertEqual(palkia.entry_number, 150)
        self.assertEqual(palkia.pokemon.national_number, 484)
        self.assertEqual(palkia.obtaining_info.get("type"), "legendary")
        self.assertIn("Columna Lanza", palkia.obtaining_info.get("summary", ""))

        # Shieldon (#410) es el #38 en Sinnoh (Fósil exclusivo en Perla)
        shieldon = [e for e in reg_cat if e.pokemon.national_number == 410][0]
        self.assertEqual(shieldon.entry_number, 38)
        self.assertIn("Fósil Coraza", shieldon.obtaining_info.get("summary", ""))

        # Manaphy es el #151 en la Pokédex de Sinnoh
        self.assertEqual(reg_cat[150].entry_number, 151)
        self.assertEqual(reg_cat[150].pokemon.name, "manaphy")
        self.assertEqual(reg_cat[150].pokemon.national_number, 490)

    def test_pearl_national_order_and_regions(self):
        from tracker.catalog_service import get_compiled_catalog
        nat_cat = get_compiled_catalog("pearl", is_national=True)
        self.assertEqual(nat_cat[0].entry_number, 1)
        self.assertEqual(nat_cat[0].pokemon.name, "bulbasaur")
        self.assertEqual(nat_cat[386].entry_number, 387)
        self.assertEqual(nat_cat[386].pokemon.name, "turtwig")
        self.assertEqual(nat_cat[483].entry_number, 484)
        self.assertEqual(nat_cat[483].pokemon.name, "palkia")
        self.assertEqual(nat_cat[492].entry_number, 493)
        self.assertEqual(nat_cat[492].pokemon.name, "arceus")
        arceus_obt = nat_cat[492].obtaining_info
        self.assertEqual(arceus_obt.get("type"), "event")
        self.assertEqual(arceus_obt.get("badge_label"), "Evento de Distribución")
        self.assertIn("Flauta Azur", arceus_obt.get("historical_note", {}).get("text", ""))

        rotom_obt = nat_cat[478].obtaining_info
        self.assertEqual(rotom_obt.get("badge_label"), "Vieja Mansión")
        self.assertIn("Vieja Mansión", rotom_obt.get("summary", ""))
        self.assertEqual(rotom_obt.get("locations", [])[0].get("area"), "Vieja Mansión (Televisor)")

        heatran_obt = nat_cat[484].obtaining_info
        self.assertIn("Montaña Dura", heatran_obt.get("summary", ""))
        self.assertIn("Montaña Dura", heatran_obt.get("locations", [])[0].get("area", ""))

    def test_pearl_exclusives_and_transfers_catalog(self):
        from tracker.exclusives import (
            GAME_COUNTERPARTS,
            VERSION_EXCLUSIVES_CATALOG,
            VERSION_TRANSFERS_CATALOG,
            get_version_transfers_context,
            get_version_exclusives_context
        )
        self.assertIn("pearl", GAME_COUNTERPARTS)
        self.assertEqual(GAME_COUNTERPARTS["pearl"], ["diamond"])
        self.assertIn("pearl", VERSION_EXCLUSIVES_CATALOG)
        self.assertEqual(len(VERSION_EXCLUSIVES_CATALOG["pearl"]), 20)
        self.assertIn(410, VERSION_EXCLUSIVES_CATALOG["pearl"])  # Shieldon
        self.assertIn(431, VERSION_EXCLUSIVES_CATALOG["pearl"])  # Glameow
        self.assertIn(484, VERSION_EXCLUSIVES_CATALOG["pearl"])  # Palkia

        excl_ctx = get_version_exclusives_context(self.game, self.pk_sinnoh, set())
        self.assertIsNotNone(excl_ctx)
        self.assertEqual(excl_ctx["own_theme"], "pearl")
        self.assertEqual(excl_ctx["counterpart_theme"], "diamond")

        self.assertIn("pearl", VERSION_TRANSFERS_CATALOG)
        self.assertEqual(len(VERSION_TRANSFERS_CATALOG["pearl"]), 90)

        # En la Pokédex Regional de Sinnoh NO debe haber modal de transferencias
        self.assertIsNone(get_version_transfers_context(self.game, self.pk_sinnoh, set()))
        # En la Pokédex Nacional SÍ debe haber las 90 transferencias legítimas
        nat_transfers = get_version_transfers_context(self.game, self.pk_nat, set())
        self.assertIsNotNone(nat_transfers)
        self.assertEqual(nat_transfers["total"], 90)
        self.assertEqual(nat_transfers["mechanic_badge"], "Transferir / GBA")
        # Verificar que especies clave estén presentes en transferencias
        self.assertTrue(any(p["national_number"] == 114 for p in nat_transfers["transfer_list"]))  # Tangela
        self.assertTrue(any(p["national_number"] == 465 for p in nat_transfers["transfer_list"]))  # Tangrowth
        self.assertTrue(any(p["national_number"] == 357 for p in nat_transfers["transfer_list"]))  # Tropius
        self.assertTrue(any(p["national_number"] == 273 for p in nat_transfers["transfer_list"]))  # Seedot (Dual Rubí)
        self.assertTrue(any(p["national_number"] == 270 for p in nat_transfers["transfer_list"]))  # Lotad (Dual Zafiro)
        self.assertTrue(any(p["national_number"] == 204 for p in nat_transfers["transfer_list"]))  # Pineco (Dual Esmeralda)
        # Gengar (#94) NO debe estar en transferencias
        self.assertFalse(any(p["national_number"] == 94 for p in nat_transfers["transfer_list"]))
        # Especies obtenibles in-game NO deben estar en transferencias
        self.assertFalse(any(p["national_number"] == 109 for p in nat_transfers["transfer_list"]))  # Koffing
        self.assertFalse(any(p["national_number"] == 110 for p in nat_transfers["transfer_list"]))  # Weezing
        self.assertFalse(any(p["national_number"] == 360 for p in nat_transfers["transfer_list"]))  # Wynaut

    def test_pearl_evolution_items_and_stones(self):
        from tracker.catalog_service import get_compiled_catalog
        nat_cat = get_compiled_catalog("pearl", is_national=True)
        cat_by_num = {e.pokemon.national_number: e for e in nat_cat}

        # Roserade con Piedra Día
        roserade = cat_by_num[407]
        self.assertEqual(roserade.obtaining_info.get("type"), "evolution")
        self.assertIsNotNone(roserade.evolution_stone)
        self.assertEqual(roserade.evolution_stone.get("slug"), "shiny-stone")

        # Honchkrow (#430) en Perla es exclusivo de Diamante (trade) con Piedra Noche
        honchkrow = cat_by_num[430]
        self.assertEqual(honchkrow.obtaining_info.get("type"), "trade")
        self.assertIsNotNone(honchkrow.evolution_stone)
        self.assertEqual(honchkrow.evolution_stone.get("slug"), "dusk-stone")

        # Mismagius (#429) con Piedra Noche
        mismagius = cat_by_num[429]
        self.assertEqual(mismagius.obtaining_info.get("type"), "evolution")
        self.assertIsNotNone(mismagius.evolution_stone)
        self.assertEqual(mismagius.evolution_stone.get("slug"), "dusk-stone")

        # Magmortar (#467): Magmatizador
        magmortar = cat_by_num[467]
        self.assertIsNotNone(magmortar.evolution_stone)
        self.assertEqual(magmortar.evolution_stone.get("slug"), "magmarizer")

        # Electivire (#466): Electrizador (requiere intercambio desde Diamante)
        electivire = cat_by_num[466]
        self.assertIsNotNone(electivire.evolution_stone)
        self.assertEqual(electivire.evolution_stone.get("slug"), "electirizer")

        # Gallade con Piedra Alba
        gallade = cat_by_num[475]
        self.assertEqual(gallade.obtaining_info.get("type"), "evolution")
        self.assertIsNotNone(gallade.evolution_stone)
        self.assertEqual(gallade.evolution_stone.get("slug"), "dawn-stone")

        # Inciensos de 4.ª Generación
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

    def test_pearl_breeding_golden_rule(self):
        from tracker.catalog_service import get_compiled_catalog
        nat_cat = get_compiled_catalog("pearl", is_national=True)
        cat_by_num = {e.pokemon.national_number: e for e in nat_cat}

        # Formas base y bebés sí son eclosionables y mencionan crianza
        for num in [387, 390, 393, 403, 406, 447]:
            entry = cat_by_num[num]
            daycare_locs = [l for l in entry.obtaining_info.get("locations", []) if "guardería" in l.get("area", "").lower()]
            self.assertTrue(len(daycare_locs) > 0, f"#{num} {entry.pokemon.name} base/bebé debe tener Guardería en Sinnoh")

        # Evoluciones y legendarios NUNCA deben tener Guardería
        for num in [94, 388, 389, 391, 392, 405, 448, 483, 484, 487, 493]:
            entry = cat_by_num[num]
            daycare_locs = [l for l in entry.obtaining_info.get("locations", []) if "guardería" in l.get("area", "").lower()]
            self.assertEqual(len(daycare_locs), 0, f"#{num} {entry.pokemon.name} evolucionado/legendario no debe tener Guardería")

    def test_pearl_offline_sprites_exist(self):
        from django.conf import settings
        base_media = settings.MEDIA_ROOT
        self.assertTrue(os.path.exists(os.path.join(base_media, "pokemon", "sprites", "pearl", "1.png")))
        self.assertTrue(os.path.exists(os.path.join(base_media, "pokemon", "sprites", "pearl", "387.png")))
        self.assertTrue(os.path.exists(os.path.join(base_media, "pokemon", "sprites", "pearl", "484.png")))
        self.assertTrue(os.path.exists(os.path.join(base_media, "pokemon", "sprites", "pearl", "493.png")))
        self.assertTrue(os.path.exists(os.path.join(base_media, "pokemon", "sprites", "pearl_shiny", "1.png")))
        self.assertTrue(os.path.exists(os.path.join(base_media, "pokemon", "sprites", "pearl_shiny", "387.png")))
        self.assertTrue(os.path.exists(os.path.join(base_media, "pokemon", "sprites", "pearl_shiny", "484.png")))
        self.assertTrue(os.path.exists(os.path.join(base_media, "pokemon", "sprites", "pearl_shiny", "493.png")))

    def test_pearl_views_and_theming(self):
        resp_reg = self.client.get(reverse("tracker:pokedex_default", kwargs={"game_slug": "pearl"}))
        self.assertEqual(resp_reg.status_code, 200)
        self.assertContains(resp_reg, 'data-game="pearl"')
        self.assertContains(resp_reg, "Turtwig")

        resp_nat = self.client.get(reverse("tracker:pokedex_detail", kwargs={"game_slug": "pearl", "pokedex_slug": "national"}))
        self.assertEqual(resp_nat.status_code, 200)
        self.assertContains(resp_nat, 'id="national-generation-bar"')
        self.assertContains(resp_nat, "Kanto")
        self.assertContains(resp_nat, "Johto")
        self.assertContains(resp_nat, "Hoenn")
        self.assertContains(resp_nat, "Sinnoh")

    def test_pearl_unown_canonical_f_and_chambers(self):
        from tracker.unown_data import get_unown_catalog, get_game_unown_chambers, SINNOH_UNOWN_CHAMBERS
        from tracker.pokemon_forms import get_pokemon_forms
        from django.conf import settings
        from pathlib import Path

        chambers = get_game_unown_chambers("pearl")
        self.assertEqual(chambers, SINNOH_UNOWN_CHAMBERS)

        cat = get_unown_catalog("pearl")
        self.assertEqual(len(cat), 28)
        self.assertEqual(cat[0]["sprite_normal"], "/media/pokemon/sprites/pearl/unown/a.png")
        self.assertEqual(cat[0]["icon_url"], "/media/pokemon/icons/gen4/201-a.png")

        forms = get_pokemon_forms(201, "pearl")
        self.assertEqual(len(forms), 28)
        self.assertEqual(forms[0]["form_key"], "a")
        f_form = next(f for f in forms if f["form_key"] == "f")
        self.assertEqual(f_form["name"], "Unown [F]")
        self.assertEqual(f_form["sprite_retro"], "/media/pokemon/sprites/pearl/unown/f.png")

        base_media = Path(settings.MEDIA_ROOT)
        self.assertTrue((base_media / "pokemon" / "sprites" / "pearl" / "201.png").exists())
        self.assertTrue((base_media / "pokemon" / "sprites" / "pearl" / "unown" / "f.png").exists())

        resp = self.client.get(reverse("tracker:pokedex_default", kwargs={"game_slug": "pearl"}))
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.context["is_sinnoh"])
        self.assertContains(resp, 'id="unown-tab-friend"')
        self.assertContains(resp, 'Ruinas Sosiego')

    def test_pearl_filter_tags_and_mechanics(self):
        from tracker.catalog_service import get_compiled_catalog

        self.assertTrue(self.game.has_great_marsh)
        self.assertTrue(self.game.has_honey_trees)
        self.assertTrue(self.game.has_poke_radar)
        self.assertTrue(self.game.has_dual_slot)
        self.assertTrue(self.game.has_swarms)
        self.assertFalse(self.game.has_safari_zone)

        reg_cat = get_compiled_catalog("pearl", is_national=False)
        starly = next(e for e in reg_cat if e.pokemon.national_number == 396)
        self.assertIn("great_marsh", starly.filter_tags)

        burmy = next(e for e in reg_cat if e.pokemon.national_number == 412)
        self.assertIn("honey_tree", burmy.filter_tags)

        nat_cat = get_compiled_catalog("pearl", is_national=True)
        nidoran = next(e for e in nat_cat if e.pokemon.national_number == 29)
        self.assertIn("radar", nidoran.filter_tags)

        togepi = next(e for e in nat_cat if e.pokemon.national_number == 175)
        self.assertIn("radar", togepi.filter_tags)
        self.assertEqual(togepi.obtaining_info.get("badge_label"), "Poké Radar")
        self.assertEqual(len([e for e in nat_cat if "radar" in e.filter_tags]), 39)

        rattata = next(e for e in nat_cat if e.pokemon.national_number == 19)
        self.assertNotIn("radar", rattata.filter_tags)
        self.assertNotIn("swarm", rattata.filter_tags)

        caterpie = next(e for e in nat_cat if e.pokemon.national_number == 10)
        self.assertIn("dual_slot", caterpie.filter_tags)

        beldum = next(e for e in nat_cat if e.pokemon.national_number == 374)
        self.assertIn("swarm", beldum.filter_tags)
        self.assertEqual(len([e for e in nat_cat if "swarm" in e.filter_tags]), 28)

        tropius = next(e for e in nat_cat if e.pokemon.national_number == 357)
        self.assertNotIn("great_marsh", tropius.filter_tags)

        resp_reg = self.client.get(reverse("tracker:pokedex_default", kwargs={"game_slug": "pearl"}))
        self.assertEqual(resp_reg.status_code, 200)
        self.assertNotContains(resp_reg, 'data-tag="radar"')

        resp_nat = self.client.get(reverse("tracker:pokedex_detail", kwargs={"game_slug": "pearl", "pokedex_slug": "national"}))
        self.assertEqual(resp_nat.status_code, 200)
        self.assertContains(resp_nat, 'data-tag="radar"')

    def test_gen4_pearl_alternate_forms(self):
        from tracker.catalog_service import get_compiled_catalog

        pearl_reg = get_compiled_catalog("pearl", is_national=False)
        pearl_nat = get_compiled_catalog("pearl", is_national=True)

        castform = next(e for e in pearl_nat if e.pokemon.national_number == 351)
        self.assertEqual(len(castform.forms), 4)
        self.assertIn("/media/pokemon/sprites/pearl/351.png", castform.forms[0]["sprite_retro"])
        self.assertIn("/media/pokemon/sprites/pearl/castform/sunny.png", castform.forms[1]["sprite_retro"])
        self.assertEqual(castform.forms[1]["modal_retro_sprite_url"], "/media/pokemon/sprites/pearl_animated/castform/sunny.png")
        self.assertEqual(castform.forms[2]["modal_retro_sprite_url"], "/media/pokemon/sprites/pearl_animated/castform/rainy.png")
        self.assertEqual(castform.forms[3]["modal_retro_sprite_url"], "/media/pokemon/sprites/pearl_animated/castform/snowy.png")

        deoxys = next(e for e in pearl_nat if e.pokemon.national_number == 386)
        self.assertEqual(len(deoxys.forms), 4)

        burmy = next(e for e in pearl_reg if e.pokemon.national_number == 412)
        self.assertEqual(len(burmy.forms), 3)

        wormadam = next(e for e in pearl_reg if e.pokemon.national_number == 413)
        self.assertEqual(len(wormadam.forms), 3)

        cherrim = next(e for e in pearl_reg if e.pokemon.national_number == 421)
        self.assertEqual(len(cherrim.forms), 2)

        shellos = next(e for e in pearl_reg if e.pokemon.national_number == 422)
        self.assertEqual(len(shellos.forms), 2)

        arceus = next(e for e in pearl_nat if e.pokemon.national_number == 493)
        self.assertEqual(len(arceus.forms), 17)


class PokemonPlatinumGen4Tests(TestCase):
    """Pruebas unitarias para Pokémon Platino (Gen 4), catálogos, exclusividades, formas y mecánicas."""

    def setUp(self):
        self.client = Client()
        self.game, _ = Game.objects.get_or_create(
            slug="platinum",
            defaults={"name": "Pokémon Platino", "generation": 4}
        )
        self.pk_sinnoh, _ = Pokedex.objects.get_or_create(
            game=self.game,
            slug="sinnoh",
            defaults={"name": "Pokédex de Sinnoh", "is_national": False, "pokeapi_name": "extended-sinnoh"}
        )
        self.pk_nat, _ = Pokedex.objects.get_or_create(
            game=self.game,
            slug="national",
            defaults={"name": "Pokédex Nacional", "is_national": True, "pokeapi_name": "national"}
        )

    def test_platinum_catalogs_exist_and_counts(self):
        from tracker.catalog_service import get_compiled_catalog, CATALOGS_DIR
        reg_file = CATALOGS_DIR / "platinum.json"
        nat_file = CATALOGS_DIR / "platinum_national.json"
        self.assertTrue(reg_file.exists(), "platinum.json debe existir")
        self.assertTrue(nat_file.exists(), "platinum_national.json debe existir")

        reg_cat = get_compiled_catalog("platinum", is_national=False, force_reload=True)
        nat_cat = get_compiled_catalog("platinum", is_national=True, force_reload=True)
        self.assertEqual(len(reg_cat), 210, "La Pokédex Regional de Sinnoh en Platino debe tener 210 entradas")
        self.assertEqual(len(nat_cat), 493, "La Pokédex Nacional en Platino debe tener 493 entradas")

    def test_platinum_regional_sinnoh_order_and_species(self):
        from tracker.catalog_service import get_compiled_catalog
        reg_cat = get_compiled_catalog("platinum", is_national=False)
        self.assertEqual(reg_cat[0].entry_number, 1)
        self.assertEqual(reg_cat[0].pokemon.name, "turtwig")
        self.assertEqual(reg_cat[0].pokemon.national_number, 387)

        # Rotom (#479) es el #152 en la Pokédex de Sinnoh ampliada
        rotom = [e for e in reg_cat if e.pokemon.national_number == 479][0]
        self.assertEqual(rotom.entry_number, 152)
        self.assertEqual(rotom.primary_type, "electric")
        self.assertEqual(rotom.secondary_type, "ghost")

        # Giratina (#487) es el #210 en la Pokédex de Sinnoh ampliada (Mascota insignia de Platino)
        giratina = [e for e in reg_cat if e.pokemon.national_number == 487][0]
        self.assertEqual(giratina.entry_number, 210)
        self.assertEqual(giratina.obtaining_info.get("type"), "legendary")
        self.assertIn("Mundo Distorsión", giratina.obtaining_info.get("summary", ""))

        # Manaphy (#490) es el #151 en la Pokédex de Sinnoh
        manaphy = [e for e in reg_cat if e.pokemon.national_number == 490][0]
        self.assertEqual(manaphy.entry_number, 151)

    def test_platinum_gifts_and_encounters(self):
        from tracker.catalog_service import get_compiled_catalog
        reg_cat = get_compiled_catalog("platinum", is_national=False)

        # Eevee (#133) regalo de Tecla en Ciudad Coraz\\u00f3n
        eevee = next(e for e in reg_cat if e.pokemon.national_number == 133)
        self.assertEqual(eevee.obtaining_info.get("type"), "gift")
        self.assertIn("Tecla", eevee.obtaining_info.get("summary", ""))

        # Porygon (#137) regalo en Ciudad Rocavelo
        porygon = next(e for e in reg_cat if e.pokemon.national_number == 137)
        self.assertEqual(porygon.obtaining_info.get("type"), "gift")
        self.assertIn("Ciudad Rocavelo", porygon.obtaining_info.get("summary", ""))

        # Togepi (#175) huevo regalado por Cintia y salvaje con Poké Radar en Ruta 230
        togepi = next(e for e in reg_cat if e.pokemon.national_number == 175)
        self.assertEqual(togepi.obtaining_info.get("type"), "gift")
        self.assertEqual(togepi.obtaining_info.get("badge_label"), "Huevo / Radar")
        self.assertIn("Cintia", togepi.obtaining_info.get("summary", ""))
        self.assertIn("Ruta 230", togepi.obtaining_info.get("summary", ""))
        self.assertIn("radar", togepi.filter_tags)
        self.assertIn("gift", togepi.filter_tags)

        # Happiny (#440) salvaje en Jardín Trofeo y crianza con Incienso Duplo (no regalo de montañero en Platino)
        happiny = next(e for e in reg_cat if e.pokemon.national_number == 440)
        self.assertEqual(happiny.obtaining_info.get("type"), "wild")
        self.assertEqual(happiny.obtaining_info.get("badge_label"), "Jardín Trofeo")
        self.assertIn("Jardín Trofeo", happiny.obtaining_info.get("summary", ""))
        self.assertNotIn("montañero", happiny.obtaining_info.get("summary", "").lower())
        self.assertIn("baby", happiny.filter_tags)
        self.assertNotIn("gift", happiny.filter_tags)

        # Riolu (#447) huevo regalado por Quinoa en Isla Hierro
        riolu = next(e for e in reg_cat if e.pokemon.national_number == 447)
        self.assertEqual(riolu.obtaining_info.get("type"), "gift")
        self.assertIn("Quinoa", riolu.obtaining_info.get("summary", ""))

        # Drifloon (#425) encuentro \único los viernes en Valle E\\u00f3lico
        drifloon = next(e for e in reg_cat if e.pokemon.national_number == 425)
        self.assertIn(drifloon.obtaining_info.get("type"), ["wild", "static"])
        self.assertTrue(len(drifloon.obtaining_info.get("locations", [])) > 0)

    def test_platinum_radar_and_swarm_filter_tags_invariants(self):
        from tracker.catalog_service import get_compiled_catalog
        reg_cat = get_compiled_catalog("platinum", is_national=False, force_reload=True)
        nat_cat = get_compiled_catalog("platinum", is_national=True, force_reload=True)

        for cat in [reg_cat, nat_cat]:
            # Poké Radar invariants: Geodude (#74), Gastly (#92), Piloswine (#221), Dusclops (#356), Chingling (#433)
            # no deben tener la etiqueta 'radar' (cuevas, edificios interiores o DP-only)
            bogus_radar_nums = [74, 92, 221, 356, 433]
            for nat_num in bogus_radar_nums:
                entry = next((e for e in cat if e.pokemon.national_number == nat_num), None)
                if entry:
                    self.assertNotIn("radar", entry.filter_tags, f"#{nat_num} {entry.pokemon.name} no debe tener tag 'radar'")

            # Swarm invariant: Onix (#95) en Isla Hierro B3F no es manada
            onix = next((e for e in cat if e.pokemon.national_number == 95), None)
            if onix:
                self.assertNotIn("swarm", onix.filter_tags, "Onix (#95) no debe tener tag 'swarm'")

    def test_platinum_missing_counterpart_exclusives(self):
        from tracker.exclusives import THIRD_VERSION_COUNTERPART_EXCLUSIVES, get_version_exclusives_context

        self.assertIn("platinum", THIRD_VERSION_COUNTERPART_EXCLUSIVES)
        conf = THIRD_VERSION_COUNTERPART_EXCLUSIVES["platinum"]
        self.assertEqual(conf["counterpart_theme"], "diamond_pearl")
        self.assertEqual(len(conf["exclusive_nums"]), 8)
        expected_missing = [198, 200, 429, 430, 431, 432, 434, 435]
        self.assertEqual(sorted(conf["exclusive_nums"]), expected_missing)

        info = get_version_exclusives_context(self.game, self.pk_sinnoh, set())
        self.assertIsNotNone(info)
        self.assertTrue(info["has_exclusives"])
        self.assertEqual(info["counterpart_total"], 8)
        self.assertEqual(info["counterpart_theme"], "diamond_pearl")

    def test_platinum_transfers(self):
        from tracker.exclusives import VERSION_TRANSFERS_CATALOG, VERSION_TRANSFERS_META, get_version_transfers_context

        self.assertIn("platinum", VERSION_TRANSFERS_CATALOG)
        self.assertEqual(len(VERSION_TRANSFERS_CATALOG["platinum"]), 79)
        origins = VERSION_TRANSFERS_META["platinum"]["origins"]
        self.assertEqual(len(origins), 79)

        t_info = get_version_transfers_context(self.game, self.pk_nat, set())
        self.assertIsNotNone(t_info)
        self.assertTrue(t_info["has_transfers"])
        self.assertEqual(t_info["total"], 79)

        # Inserción Dual exclusiva incluida en Platino
        plat_transfers = set(VERSION_TRANSFERS_CATALOG["platinum"])
        for pid in [10, 11, 12, 13, 14, 15, 23, 24, 27, 28, 37, 38, 58, 59, 204, 205, 213, 216, 217, 270, 271, 272, 273, 274, 275, 302, 303, 335, 336, 337, 338]:
            self.assertIn(pid, plat_transfers)

        # Especies con métodos nativos en Platino NO deben estar en transferencias
        for excluded_id in [94, 114, 125, 126, 207, 239, 240, 357, 465, 466, 467, 472]:
            self.assertNotIn(excluded_id, plat_transfers)

    def test_platinum_rotom_giratina_shaymin_forms(self):
        from tracker.pokemon_forms import get_pokemon_forms
        from tracker.catalog_service import get_compiled_catalog

        # Rotom en Platino: 6 formas, todas El\\u00e9ctrico/Fantasma en Gen 4
        rotom_forms = get_pokemon_forms(479, "platinum")
        self.assertEqual(len(rotom_forms), 6)
        for rf in rotom_forms:
            self.assertEqual(rf["primary_type"], "electric")
            self.assertEqual(rf["secondary_type"], "ghost")
            self.assertIn("/media/pokemon/sprites/platinum/", rf["sprite_retro"])
            self.assertIn("/media/pokemon/sprites/platinum_animated/", rf["modal_retro_sprite_url"])

        # Rotom en Perla: debe ser lista vac\\u00eda
        self.assertEqual(get_pokemon_forms(479, "pearl"), [])

        # Giratina en Platino: 2 formas (Modificada y Origen #10007)
        giratina_forms = get_pokemon_forms(487, "platinum")
        self.assertEqual(len(giratina_forms), 2)
        origen = next(f for f in giratina_forms if f["form_key"] == "origin")
        self.assertEqual(origen["sprite_modern"], "/media/pokemon/home/10007.png")
        self.assertIn("/media/pokemon/sprites/platinum/giratina/origin.png", origen["sprite_retro"])

        # Shaymin en Platino: 2 formas (Tierra y Cielo #10006)
        shaymin_forms = get_pokemon_forms(492, "platinum")
        self.assertEqual(len(shaymin_forms), 2)
        cielo = next(f for f in shaymin_forms if f["form_key"] == "sky")
        self.assertEqual(cielo["sprite_modern"], "/media/pokemon/home/10006.png")
        self.assertIn("/media/pokemon/sprites/platinum/shaymin/sky.png", cielo["sprite_retro"])

    def test_platinum_evolution_stones(self):
        import json
        from pathlib import Path
        from django.conf import settings

        stones_path = Path(settings.BASE_DIR) / "tracker" / "data" / "evolution_stones.json"
        with open(stones_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        platinum_items = [slug for slug, it in data.items() if "platinum" in it.get("games", {})]
        self.assertEqual(len(platinum_items), 39)  # 32 objetos evolutivos/inciensos + 7 fósiles
        # Verificar piedras y objetos clave
        self.assertIn("dusk-stone", platinum_items)
        self.assertIn("dawn-stone", platinum_items)
        self.assertIn("shiny-stone", platinum_items)
        self.assertIn("reaper-cloth", platinum_items)
        self.assertIn("protector", platinum_items)
        self.assertIn("electirizer", platinum_items)
        self.assertIn("magmarizer", platinum_items)

        # Validaciones canonicas de ubicaciones exclusivas y corregidas en Platino vs Diamante/Perla
        dawn_plat_areas = [loc["area"] for loc in data["dawn-stone"]["games"]["platinum"]]
        self.assertIn("Ruta 212", dawn_plat_areas)
        self.assertIn("Ruta 225", dawn_plat_areas)
        self.assertNotIn("Ruta 212", [loc["area"] for loc in data["dawn-stone"]["games"]["diamond"]])

        sea_incense_plat_areas = [loc["area"] for loc in data["sea-incense"]["games"]["platinum"]]
        self.assertIn("Ruta 204 (Sur)", sea_incense_plat_areas)

        full_incense_plat_areas = [loc["area"] for loc in data["full-incense"]["games"]["platinum"]]
        self.assertIn("Ciudad Rocavelo", full_incense_plat_areas)

        luck_incense_plat_areas = [loc["area"] for loc in data["luck-incense"]["games"]["platinum"]]
        self.assertIn("Senda Desolada", luck_incense_plat_areas)

        upgrade_plat_areas = [loc["area"] for loc in data["up-grade"]["games"]["platinum"]]
        self.assertIn("Edificio Galaxia de Ciudad Vetusta", upgrade_plat_areas)
        self.assertIn("Ruta 224", upgrade_plat_areas)
        self.assertIn("Ciudad Vetusta (Casa del Profesor Oak)", upgrade_plat_areas)

        metal_coat_plat_areas = [loc["area"] for loc in data["metal-coat"]["games"]["platinum"]]
        self.assertIn("Ruinas Hierro (Isla Hierro)", metal_coat_plat_areas)

        # En 4.a Generacion, Dusclops (Baya Drasi) y Sneasel (Garra Garfio/Rapida) no portan Tela Terrible ni Garra Afilada
        for g in ["diamond", "pearl", "platinum"]:
            self.assertFalse(any("salvaje" in loc["area"].lower() for loc in data["reaper-cloth"]["games"][g]))
            self.assertFalse(any("salvaje" in loc["area"].lower() for loc in data["razor-claw"]["games"][g]))

    def test_platinum_breeding_and_counterpart_obtaining_methods(self):
        from tracker.catalog_service import get_compiled_catalog
        reg_cat = get_compiled_catalog("platinum", is_national=False, force_reload=True)
        nat_cat = get_compiled_catalog("platinum", is_national=True, force_reload=True)

        # 1. Elekid (#239) y Magby (#240) deben obtenerse canónicamente mediante crianza en Pueblo Sosiego
        elekid = next(e for e in reg_cat if e.pokemon.national_number == 239)
        self.assertEqual(elekid.obtaining_info.get("type"), "breeding")
        self.assertEqual(elekid.obtaining_info.get("badge_label"), "Crianza")
        self.assertIn("Electabuzz", elekid.obtaining_info.get("summary", ""))

        magby = next(e for e in reg_cat if e.pokemon.national_number == 240)
        self.assertEqual(magby.obtaining_info.get("type"), "breeding")
        self.assertEqual(magby.obtaining_info.get("badge_label"), "Crianza")
        self.assertIn("Magmar", magby.obtaining_info.get("summary", ""))

        # 2. Exclusivos de versión en Platino (Murkrow de Diamante, Misdreavus de Perla)
        murkrow = next(e for e in reg_cat if e.pokemon.national_number == 198)
        self.assertEqual(murkrow.obtaining_info.get("type"), "trade")
        self.assertEqual(murkrow.obtaining_info.get("badge_label"), "Exclusivo Diamante")

        misdreavus = next(e for e in reg_cat if e.pokemon.national_number == 200)
        self.assertEqual(misdreavus.obtaining_info.get("type"), "trade")
        self.assertEqual(misdreavus.obtaining_info.get("badge_label"), "Exclusivo Perla")

        # 3. Encuentros estáticos icónicos (Drifloon y Spiritomb)
        drifloon = next(e for e in reg_cat if e.pokemon.national_number == 425)
        self.assertEqual(drifloon.obtaining_info.get("type"), "static")
        self.assertEqual(drifloon.obtaining_info.get("badge_label"), "Evento Semanal")

        spiritomb = next(e for e in reg_cat if e.pokemon.national_number == 442)
        self.assertEqual(spiritomb.obtaining_info.get("type"), "static")
        self.assertEqual(spiritomb.obtaining_info.get("badge_label"), "Torre Sagrada")

        # 4. Asegurar que ningún Pokémon en regional o nacional tenga badge "Especial" (falso evento)
        for cat, name in [(reg_cat, "regional"), (nat_cat, "nacional")]:
            for entry in cat:
                badge = entry.obtaining_info.get("badge_label")
                self.assertNotEqual(badge, "Especial", f"Pokémon {entry.pokemon.name} en Platino {name} no debe tener badge 'Especial'")
                # Comprobar que no haya fugas de nombres de áreas en inglés
                summary = entry.obtaining_info.get("summary", "").lower()
                self.assertNotIn("sinnoh route", summary)
                self.assertNotIn(" area", summary)

    def test_platinum_http_views_and_theme(self):
        resp_reg = self.client.get(reverse("tracker:pokedex_default", kwargs={"game_slug": "platinum"}))
        self.assertEqual(resp_reg.status_code, 200)
        self.assertTrue(resp_reg.context["is_sinnoh"])
        self.assertEqual(resp_reg.context["total_pokemon"], 210)
        self.assertContains(resp_reg, 'data-game="platinum"')
        self.assertContains(resp_reg, "Giratina")

        resp_nat = self.client.get(reverse("tracker:pokedex_detail", kwargs={"game_slug": "platinum", "pokedex_slug": "national"}))
        self.assertEqual(resp_nat.status_code, 200)
        self.assertEqual(resp_nat.context["total_pokemon"], 493)



class PokemonHeartGoldGen4Tests(TestCase):
    """Pruebas unitarias para Pokémon Oro HeartGold (Gen 4), catálogos, exclusividades, formas y mecánicas."""

    def setUp(self):
        self.client = Client()
        self.game, _ = Game.objects.get_or_create(
            slug="heartgold",
            defaults={"name": "Pokémon Oro HeartGold", "generation": 4}
        )
        self.pk_johto, _ = Pokedex.objects.get_or_create(
            game=self.game,
            slug="johto",
            defaults={"name": "Pokédex de Johto", "is_national": False, "pokeapi_name": "updated-johto"}
        )
        self.pk_nat, _ = Pokedex.objects.get_or_create(
            game=self.game,
            slug="national",
            defaults={"name": "Pokédex Nacional", "is_national": True, "pokeapi_name": "national"}
        )

    def test_heartgold_catalogs_exist_and_counts(self):
        from tracker.catalog_service import get_compiled_catalog, CATALOGS_DIR
        reg_file = CATALOGS_DIR / "heartgold.json"
        nat_file = CATALOGS_DIR / "heartgold_national.json"
        self.assertTrue(reg_file.exists(), "heartgold.json debe existir")
        self.assertTrue(nat_file.exists(), "heartgold_national.json debe existir")

        reg_cat = get_compiled_catalog("heartgold", is_national=False, force_reload=True)
        nat_cat = get_compiled_catalog("heartgold", is_national=True, force_reload=True)
        self.assertEqual(len(reg_cat), 256, "La Pokédex Regional de Johto en HeartGold debe tener 256 entradas")
        self.assertEqual(len(nat_cat), 493, "La Pokédex Nacional en HeartGold debe tener 493 entradas")

    def test_heartgold_regional_johto_order_and_species(self):
        from tracker.catalog_service import get_compiled_catalog
        reg_cat = get_compiled_catalog("heartgold", is_national=False)
        # Chikorita (#152) es el #1 en Johto
        self.assertEqual(reg_cat[0].entry_number, 1)
        self.assertEqual(reg_cat[0].pokemon.name, "chikorita")
        self.assertEqual(reg_cat[0].pokemon.national_number, 152)

        # Celebi (#251) es el #256 en Johto
        self.assertEqual(reg_cat[255].entry_number, 256)
        self.assertEqual(reg_cat[255].pokemon.name, "celebi")
        self.assertEqual(reg_cat[255].pokemon.national_number, 251)

        # 5 evoluciones de Gen 4 introducidas en la Pokédex de Johto Actualizada
        evo_map = {
            124: (424, "ambipom"),
            102: (469, "yanmega"),
            181: (463, "lickilicky"),
            183: (465, "tangrowth"),
            197: (473, "mamoswine"),
        }
        for reg_num, (nat_num, p_name) in evo_map.items():
            entry = [e for e in reg_cat if e.entry_number == reg_num][0]
            self.assertEqual(entry.pokemon.national_number, nat_num)
            self.assertEqual(entry.pokemon.name, p_name)

    def test_heartgold_legendaries_and_toponymy(self):
        from tracker.catalog_service import get_compiled_catalog
        reg_cat = get_compiled_catalog("heartgold", is_national=False)

        # Ho-Oh (#250) es el legendario mascota en la Torre Campana
        ho_oh = [e for e in reg_cat if e.pokemon.national_number == 250][0]
        self.assertEqual(ho_oh.obtaining_info.get("type"), "legendary")
        locations_str = str(ho_oh.obtaining_info.get("locations", []))
        self.assertIn("Torre Campana", locations_str)
        self.assertNotIn("Torre Bell", locations_str)
        self.assertIn("45", locations_str)

        # Lugia (#249) en Islas Remolino a nivel 70
        lugia = [e for e in reg_cat if e.pokemon.national_number == 249][0]
        lugia_locs = str(lugia.obtaining_info.get("locations", []))
        self.assertIn("Islas Remolino", lugia_locs)
        self.assertIn("70", lugia_locs)

        # Validación topónimos y textos oficiales canónicos (Pikachu, Magnetotrén, Ruinas Alfa, Ruta Helada)
        pikachu = [e for e in reg_cat if e.pokemon.national_number == 25][0]
        pika_locs = str(pikachu.obtaining_info.get("locations", []))
        self.assertIn("Magnetotrén", pika_locs)
        self.assertNotIn("Magnetotrón", pika_locs)
        self.assertNotIn("Npc trade", pika_locs)
        self.assertEqual(pikachu.obtaining_info.get("badge_label"), "Salvaje / Intercambio")

        # Verificar que no existen anglicismos ni deformaciones en todo el catálogo
        for entry in reg_cat:
            obt_str = str(entry.obtaining_info)
            self.assertNotIn("Magnetotrón", obt_str)
            self.assertNotIn("Ruins Alfa", obt_str)
            self.assertNotIn("Ruta de Hielo", obt_str)
            self.assertNotIn("'Npc trade'", obt_str)
            self.assertNotIn("'Gift egg'", obt_str)
            self.assertNotIn("Zona Safari (Llanura)", obt_str)
            self.assertNotIn("Zona Safari (Terreno Baldío)", obt_str)
            self.assertNotIn("Zona Safari (Marisma)", obt_str)

        # Validación específica de Stantler (#234) en la Zona Safari (ambas modalidades en Prado)
        stantler = [e for e in reg_cat if e.pokemon.national_number == 234][0]
        stantler_locs = str(stantler.obtaining_info.get("locations", []))
        self.assertIn("Zona Safari (Prado)", stantler_locs)
        self.assertNotIn("Zona Safari (Arboleda)", stantler_locs)
        self.assertIn("3 Bloques Planicie (Noche)", stantler_locs)

        # Validación de exclusión de Golem (#76) y Pidgeotto (#17) de la Zona Safari
        golem = [e for e in reg_cat if e.pokemon.national_number == 76][0]
        self.assertEqual(golem.obtaining_info.get("badge_label"), "Evolución")
        self.assertEqual(golem.obtaining_info.get("type"), "evolution")
        self.assertEqual(golem.obtaining_info.get("locations"), [])
        self.assertNotIn("safari", str(golem.obtaining_info).lower())

        pidgeotto = [e for e in reg_cat if e.pokemon.national_number == 17][0]
        self.assertNotIn("safari", str(pidgeotto.obtaining_info).lower())

        # Validación de que ninguna especie fuera de las 153 oficiales de Johto Safari Zone contenga 'Zona Safari'
        serebii_safari_numbers = {
            16, 19, 20, 21, 22, 23, 24, 27, 28, 29, 30, 32, 33, 35, 39, 41, 42, 43, 44, 46, 47, 50, 
            54, 55, 60, 61, 63, 66, 67, 69, 70, 74, 75, 77, 79, 80, 81, 82, 83, 84, 85, 88, 89, 92, 
            93, 95, 96, 97, 98, 99, 100, 104, 105, 108, 109, 110, 111, 112, 113, 115, 118, 119, 122, 
            125, 126, 128, 129, 130, 131, 132, 147, 148, 161, 162, 179, 183, 187, 188, 189, 191, 194, 
            195, 198, 200, 202, 203, 213, 228, 229, 234, 235, 246, 263, 264, 270, 271, 273, 274, 283, 
            284, 285, 286, 288, 298, 299, 304, 305, 307, 308, 309, 310, 313, 314, 315, 324, 327, 328, 
            329, 331, 332, 335, 336, 337, 338, 339, 341, 353, 354, 355, 356, 358, 363, 364, 371, 372, 
            374, 375, 399, 403, 404, 406, 417, 418, 419, 433, 436, 437, 443, 447, 449, 451, 453, 455
        }
        for entry in reg_cat:
            nid = entry.pokemon.national_number
            for loc in entry.obtaining_info.get("locations", []):
                area = loc.get("area", "")
                if "zona safari" in area.lower():
                    self.assertIn(nid, serebii_safari_numbers, f"#{nid} {entry.pokemon.name} no debe aparecer en Zona Safari")

    def test_heartgold_pichu_forms_and_spiky_eared(self):
        from tracker.pokemon_forms import get_pokemon_forms
        from tracker.catalog_service import get_compiled_catalog

        forms = get_pokemon_forms(172, "heartgold")
        self.assertEqual(len(forms), 2)
        self.assertEqual(forms[0]["form_key"], "standard")
        self.assertEqual(forms[1]["form_key"], "spiky_eared")
        self.assertEqual(forms[1]["name"], "Pichu Picoreja")
        self.assertEqual(forms[1]["sprite_retro"], "/media/pokemon/sprites/heartgold/172-spiky-eared.png")
        self.assertEqual(forms[1]["modal_retro_sprite_url"], "/media/pokemon/sprites/heartgold_animated/172-spiky-eared.png")

        # Verificar Unown (28 formas en Gen 4 HG)
        unown_forms = get_pokemon_forms(201, "heartgold")
        self.assertEqual(len(unown_forms), 28)

        # Verificar Rotom (6 formas en HG)
        rotom_forms = get_pokemon_forms(479, "heartgold")
        self.assertEqual(len(rotom_forms), 6)

        # En Pearl, Pichu no tiene formas alternativas
        self.assertEqual(get_pokemon_forms(172, "pearl"), [])

    def test_heartgold_version_exclusives(self):
        from tracker.exclusives import VERSION_EXCLUSIVES_CATALOG, get_version_exclusives_context

        exclusives_hg = VERSION_EXCLUSIVES_CATALOG.get("heartgold", [])
        self.assertEqual(len(exclusives_hg), 21)
        self.assertIn(58, exclusives_hg)   # Growlithe
        self.assertIn(380, exclusives_hg)  # Latias (Exclusivo errante en HeartGold)
        self.assertIn(382, exclusives_hg)  # Kyogre
        self.assertNotIn(381, exclusives_hg) # Latios (SoulSilver)
        self.assertNotIn(37, exclusives_hg) # Vulpix (SoulSilver)
        self.assertNotIn(250, exclusives_hg) # Ho-Oh no es exclusivo (capturable en ambos)
        self.assertNotIn(249, exclusives_hg) # Lugia no es exclusivo (capturable en ambos)

        ctx = get_version_exclusives_context(self.game, self.pk_johto, set())
        self.assertTrue(ctx["has_exclusives"])
        self.assertEqual(ctx["counterpart_slug"], "soulsilver")
        self.assertEqual(ctx["counterpart_theme"], "silver")
        self.assertEqual(ctx["counterpart_total"], 19)
        self.assertEqual(ctx["own_total"], 21)
        # Verificar presencia de exclusivos de SoulSilver en la contraparte
        counterpart_nums = [p["national_number"] for p in ctx["counterpart_list"]]
        self.assertIn(37, counterpart_nums)   # Vulpix
        self.assertIn(381, counterpart_nums)  # Latios (SoulSilver)
        self.assertIn(383, counterpart_nums)  # Groudon
        self.assertNotIn(380, counterpart_nums) # Latias es de HeartGold
        self.assertNotIn(249, counterpart_nums) # Lugia no es exclusivo

    def test_heartgold_transfers(self):
        from tracker.exclusives import VERSION_TRANSFERS_CATALOG, VERSION_TRANSFERS_META

        transfers_hg = VERSION_TRANSFERS_CATALOG.get("heartgold", [])
        self.assertEqual(len(transfers_hg), 42)
        self.assertIn(387, transfers_hg)  # Turtwig
        self.assertIn(408, transfers_hg)  # Cranidos
        self.assertIn(410, transfers_hg)  # Shieldon
        self.assertIn(425, transfers_hg)  # Drifloon
        self.assertIn(431, transfers_hg)  # Glameow
        self.assertIn(434, transfers_hg)  # Stunky
        self.assertIn(470, transfers_hg)  # Leafeon
        self.assertIn(479, transfers_hg)  # Rotom
        self.assertIn(493, transfers_hg)  # Arceus

        meta = VERSION_TRANSFERS_META.get("heartgold", {})
        self.assertIn("Parque Compi", meta.get("mechanic_title", ""))

    def test_heartgold_evolution_stones(self):
        import json
        from tracker.catalog_service import CATALOGS_DIR, get_compiled_catalog
        with open(CATALOGS_DIR.parent / "evolution_stones.json", encoding="utf-8") as f:
            stones_data = json.load(f)

        # 1. Validar Piedra Trueno y fuentes oficiales en castellano (Chica Sara, no Dana)
        thunder_stone = stones_data.get("thunder-stone", {})
        self.assertIn("heartgold", thunder_stone.get("games", {}))
        hg_thunder_locs = thunder_stone["games"]["heartgold"]
        thunder_text = " ".join(f"{loc.get('area')} {loc.get('detail')}" for loc in hg_thunder_locs)
        self.assertIn("Chica Sara", thunder_text)
        self.assertNotIn("Dana", thunder_text)
        self.assertIn("jueves", thunder_text.lower())
        self.assertIn("miércoles y sábados", thunder_text.lower())

        # Validar nombres canónicos en español de NPCs en llamadas del Pokégear
        oval_stone = stones_data.get("oval-stone", {}).get("games", {}).get("heartgold", [])
        oval_text = " ".join(f"{loc.get('area')} {loc.get('detail')}" for loc in oval_stone)
        self.assertIn("Gemelas Lil y Lala", oval_text)
        self.assertNotIn("Kay", oval_text)
        self.assertIn("Ruta 15", oval_text)

        fire_stone = stones_data.get("fire-stone", {}).get("games", {}).get("heartgold", [])
        fire_text = " ".join(f"{loc.get('area')} {loc.get('detail')}" for loc in fire_stone)
        self.assertIn("Escolar Arturo", fire_text)
        self.assertNotIn("Alan", fire_text)

        water_stone = stones_data.get("water-stone", {}).get("games", {}).get("heartgold", [])
        water_text = " ".join(f"{loc.get('area')} {loc.get('detail')}" for loc in water_stone)
        self.assertIn("Pescador Óscar", water_text)
        self.assertNotIn("Juan", water_text)

        dusk_stone = stones_data.get("dusk-stone", {}).get("games", {}).get("heartgold", [])
        dusk_text = " ".join(f"{loc.get('area')} {loc.get('detail')}" for loc in dusk_stone)
        self.assertIn("Motorista Isra", dusk_text)
        self.assertNotIn("Raúl", dusk_text)

        dawn_stone = stones_data.get("dawn-stone", {}).get("games", {}).get("heartgold", [])
        dawn_text = " ".join(f"{loc.get('area')} {loc.get('detail')}" for loc in dawn_stone)
        self.assertIn("Motorista Radomir", dawn_text)
        self.assertNotIn("Mario", dawn_text)

        # 2. Validar que Raichu en el catálogo tiene icon_url y name normalizados
        reg_cat = get_compiled_catalog("heartgold", is_national=False, force_reload=True)
        raichu = [e for e in reg_cat if e.pokemon.national_number == 26][0]
        self.assertIsNotNone(raichu.evolution_stone)
        self.assertEqual(raichu.evolution_stone["slug"], "thunder-stone")
        self.assertEqual(raichu.evolution_stone["name"], "Piedra Trueno")
        self.assertEqual(raichu.evolution_stone["icon_url"], "/media/items/thunder-stone.png")
        self.assertFalse(raichu.evolution_stone.get("is_purchasable", False))

        # 3. Validar bebés e inciensos en Pokédex Nacional
        nat_cat = get_compiled_catalog("heartgold", is_national=True, force_reload=True)
        baby_expectations = {
            360: ("lax-incense", "Incienso Suave"),
            298: ("sea-incense", "Incienso Marino"),
            440: ("luck-incense", "Incienso Duplo"),
            438: ("rock-incense", "Incienso Roca"),
            406: ("rose-incense", "Incienso Floral"),
        }
        for nat_id, (expected_slug, expected_name) in baby_expectations.items():
            entry = [e for e in nat_cat if e.pokemon.national_number == nat_id][0]
            self.assertIsNotNone(entry.evolution_stone, f"Bebé #{nat_id} debe tener evolution_stone")
            self.assertEqual(entry.evolution_stone["slug"], expected_slug)
            self.assertEqual(entry.evolution_stone["name"], expected_name)
            self.assertEqual(entry.evolution_stone["icon_url"], f"/media/items/{expected_slug}.png")

        # 4. Validar ubicaciones canónicas corregidas en HGSS
        odd_incense = stones_data.get("odd-incense", {}).get("games", {}).get("heartgold", [])
        odd_text = " ".join(f"{loc.get('area')} {loc.get('detail')}" for loc in odd_incense)
        self.assertIn("Cueva Celeste (Planta 1)", odd_text)
        self.assertIn("Golpe Roca", odd_text)
        self.assertNotIn("Sótano B1", odd_text)

        magmarizer = stones_data.get("magmarizer", {}).get("games", {}).get("heartgold", [])
        magma_text = " ".join(f"{loc.get('area')} {loc.get('detail')}" for loc in magmarizer)
        self.assertIn("Isla Canela", magma_text)
        self.assertIn("Treparrocas", magma_text)
        self.assertNotIn("Islas Espuma", magma_text)

        dubious = stones_data.get("dubious-disc", {}).get("games", {}).get("heartgold", [])
        dubious_text = " ".join(f"{loc.get('area')} {loc.get('detail')}" for loc in dubious)
        self.assertIn("Ruta 42", dubious_text)
        self.assertIn("Monte Mortero", dubious_text)

        tooth = stones_data.get("deep-sea-tooth", {}).get("games", {}).get("heartgold", [])
        tooth_text = " ".join(f"{loc.get('area')} {loc.get('detail')}" for loc in tooth)
        self.assertIn("Ruta 20", tooth_text)
        self.assertIn("Zahorí", tooth_text)

        scale = stones_data.get("deep-sea-scale", {}).get("games", {}).get("heartgold", [])
        scale_text = " ".join(f"{loc.get('area')} {loc.get('detail')}" for loc in scale)
        self.assertIn("Ruta 19", scale_text)
        self.assertIn("Zahorí", scale_text)

        reaper = stones_data.get("reaper-cloth", {}).get("games", {}).get("heartgold", [])
        reaper_text = " ".join(f"{loc.get('area')} {loc.get('detail')}" for loc in reaper)
        self.assertIn("Monte Plateado (Exterior)", reaper_text)
        self.assertIn("Surf", reaper_text)

        claw = stones_data.get("razor-claw", {}).get("games", {}).get("heartgold", [])
        claw_text = " ".join(f"{loc.get('area')} {loc.get('detail')}" for loc in claw)
        self.assertIn("Frente de Batalla", claw_text)
        self.assertNotIn("Ruta 28", claw_text)

    def test_heartgold_breeding_and_invariants(self):
        from tracker.catalog_service import get_compiled_catalog
        nat_cat = get_compiled_catalog("heartgold", is_national=True)

        # Bebés/Básicos incubables
        pichu = [e for e in nat_cat if e.pokemon.national_number == 172][0]
        self.assertTrue(pichu.is_hatchable)

        # Evoluciones finales NO incubables
        charizard = [e for e in nat_cat if e.pokemon.national_number == 6][0]
        self.assertFalse(charizard.is_hatchable)
        dragonite = [e for e in nat_cat if e.pokemon.national_number == 149][0]
        self.assertFalse(dragonite.is_hatchable)
        tyranitar = [e for e in nat_cat if e.pokemon.national_number == 248][0]
        self.assertFalse(tyranitar.is_hatchable)

    def test_heartgold_http_views_and_theme(self):
        # Detalle Pokédex de Johto
        resp_reg = self.client.get(reverse("tracker:pokedex_detail", kwargs={"game_slug": "heartgold", "pokedex_slug": "johto"}))
        self.assertEqual(resp_reg.status_code, 200)
        self.assertEqual(resp_reg.context["total_pokemon"], 256)
        self.assertContains(resp_reg, 'data-game="heartgold"')
        self.assertContains(resp_reg, "Ho-Oh")
        self.assertContains(resp_reg, '/media/items/thunder-stone.png')
        self.assertContains(resp_reg, 'alt="Piedra Trueno"')

        # Detalle Pokédex Nacional (Gen 3 - Hoenn para verificar cría de Wynaut con Incienso Suave)
        resp_nat = self.client.get(reverse("tracker:pokedex_detail", kwargs={"game_slug": "heartgold", "pokedex_slug": "national"}) + "?gen=hoenn")
        self.assertEqual(resp_nat.status_code, 200)
        self.assertEqual(resp_nat.context["total_pokemon"], 493)
        self.assertContains(resp_nat, '/media/items/lax-incense.png')
        self.assertContains(resp_nat, 'alt="Incienso Suave"')

        # Selector de juegos en Game Hub
        resp_hub = self.client.get(reverse("tracker:game_selector"))
        self.assertEqual(resp_hub.status_code, 200)
        self.assertContains(resp_hub, 'id="card-game-heartgold"')
        self.assertContains(resp_hub, "Pokémon Oro HeartGold")

    def test_heartgold_unown_ruins_of_alph_mechanics_and_forms(self):
        """
        Valida que HeartGold implemente fielmente las Ruinas Alfa de Johto para 28 formas de Unown:
        1. Contexto regional: is_johto=True, is_hgss=True, is_sinnoh=False, is_gen2_johto=False.
        2. Vistas y modal: Ruinas Alfa (28 Formas), pestañas de las 4 cámaras + Sala Secreta (!, ?), guía de HGSS.
        3. Exclusión total de Ruinas Sosiego y nota histórica de Gen 2 (DVs I y V).
        4. Catálogo de formas: orden alfabético estricto (A-Z, !, ?), donde F es el sprite representativo base 201.png.
        5. Métodos de obtención individuales: A-Z apuntan a su cámara y rompecabezas, y !/? indican el requisito de las 26 formas A-Z y 4 acertijos.
        """
        from tracker.unown_data import get_unown_catalog, get_game_unown_chambers, HGSS_UNOWN_CHAMBERS
        from tracker.pokemon_forms import get_unown_forms
        from pathlib import Path
        from django.conf import settings

        # 1. Estructura de cámaras HGSS en orden de progresión natural con rangos de 4.ª Gen (Kabuto -> Aerodactyl -> Omanyte -> Ho-Oh -> Sala Secreta)
        chambers = get_game_unown_chambers("heartgold")
        self.assertEqual(list(chambers.keys()), ["kabuto", "aerodactyl", "omanyte", "ho_oh", "secret_entrance"])
        self.assertEqual(chambers["kabuto"]["letters"], ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j"])
        self.assertEqual(chambers["aerodactyl"]["letters"], ["r", "s", "t", "u", "v"])
        self.assertEqual(chambers["omanyte"]["letters"], ["k", "l", "m", "n", "o", "p", "q"])
        self.assertEqual(chambers["ho_oh"]["letters"], ["w", "x", "y", "z"])
        self.assertEqual(chambers["secret_entrance"]["letters"], ["exclamation", "question"])

        # 2. Catálogo Unown (28 formas)
        catalog = get_unown_catalog("heartgold")
        self.assertEqual(len(catalog), 28)
        self.assertEqual(catalog[0]["letter"], "a")
        self.assertEqual(catalog[0]["chamber_key"], "kabuto")
        self.assertEqual(catalog[9]["letter"], "j")
        self.assertEqual(catalog[9]["chamber_key"], "kabuto")
        self.assertEqual(catalog[10]["letter"], "k")
        self.assertEqual(catalog[10]["chamber_key"], "omanyte")
        self.assertEqual(catalog[16]["letter"], "q")
        self.assertEqual(catalog[16]["chamber_key"], "omanyte")
        self.assertEqual(catalog[17]["letter"], "r")
        self.assertEqual(catalog[17]["chamber_key"], "aerodactyl")
        self.assertEqual(catalog[21]["letter"], "v")
        self.assertEqual(catalog[21]["chamber_key"], "aerodactyl")
        self.assertEqual(catalog[22]["letter"], "w")
        self.assertEqual(catalog[22]["chamber_key"], "ho_oh")
        self.assertEqual(catalog[25]["letter"], "z")
        self.assertEqual(catalog[25]["chamber_key"], "ho_oh")
        self.assertEqual(catalog[26]["letter"], "exclamation")
        self.assertEqual(catalog[26]["chamber_key"], "secret_entrance")
        self.assertEqual(catalog[27]["letter"], "question")
        self.assertEqual(catalog[27]["chamber_key"], "secret_entrance")

        # 3. Formas detalladas para modales (orden alfabético y obtención precisa)
        forms = get_unown_forms("heartgold")
        self.assertEqual(len(forms), 28)
        self.assertEqual(forms[0]["form_key"], "a")
        self.assertIn("Cámara de Kabuto", forms[0]["summary"])
        self.assertEqual(forms[0]["locations"][0]["area"], "Cámara de Kabuto (Ruinas Alfa)")

        # Forma K (desbloqueada en Omanyte en HGSS)
        form_k = [f for f in forms if f["form_key"] == "k"][0]
        self.assertIn("Cámara de Omanyte", form_k["summary"])
        self.assertEqual(form_k["locations"][0]["area"], "Cámara de Omanyte (Ruinas Alfa)")

        # Forma R (desbloqueada en Aerodactyl en HGSS)
        form_r = [f for f in forms if f["form_key"] == "r"][0]
        self.assertIn("Cámara de Aerodactyl", form_r["summary"])
        self.assertEqual(form_r["locations"][0]["area"], "Cámara de Aerodactyl (Ruinas Alfa)")

        # Forma W (desbloqueada en Ho-Oh en HGSS)
        form_w = [f for f in forms if f["form_key"] == "w"][0]
        self.assertIn("Cámara de Ho-Oh", form_w["summary"])
        self.assertEqual(form_w["locations"][0]["area"], "Cámara de Ho-Oh (Ruinas Alfa)")

        # Formas ! y ?
        form_excl = [f for f in forms if f["form_key"] == "exclamation"][0]
        self.assertIn("Sala Secreta de Entrada", form_excl["summary"])
        self.assertIn("26 formas", form_excl["summary"])
        self.assertIn("4 salas secretas", form_excl["summary"])
        self.assertEqual(form_excl["locations"][0]["area"], "Ruinas Alfa (Sala Secreta de Entrada)")

        # 4. Sprite representativo principal (Unown F en 201.png)
        base_media = Path(settings.MEDIA_ROOT)
        hg_sprite_main = base_media / "pokemon" / "sprites" / "heartgold" / "201.png"
        hg_sprite_f = base_media / "pokemon" / "sprites" / "heartgold" / "unown" / "f.png"
        self.assertTrue(hg_sprite_main.exists())
        self.assertTrue(hg_sprite_f.exists())
        self.assertEqual(hg_sprite_main.read_bytes(), hg_sprite_f.read_bytes())

        # 5. Renderizado en vista HTTP
        resp = self.client.get(reverse("tracker:pokedex_detail", kwargs={"game_slug": "heartgold", "pokedex_slug": "johto"}))
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.context["is_johto"])
        self.assertTrue(resp.context["is_hgss"])
        self.assertFalse(resp.context["is_sinnoh"])
        self.assertFalse(resp.context["is_gen2_johto"])
        self.assertEqual(resp.context["unown_total_forms"], 28)

        # Aserciones en el HTML renderizado (pestañas en orden natural de HGSS: Kabuto -> Aerodactyl -> Omanyte -> Ho-Oh -> Sala Secreta)
        self.assertContains(resp, "Ruinas Alfa</span> • <span>28 Formas</span>")
        self.assertContains(resp, 'id="unown-tab-secret_entrance"')
        self.assertContains(resp, 'Cámara Kabuto (A-J)')
        self.assertContains(resp, 'Cámara Aerodactyl (R-V)')
        self.assertContains(resp, 'Cámara Omanyte (K-Q)')
        self.assertContains(resp, 'Cámara Ho-Oh (W-Z)')
        self.assertContains(resp, 'Sala Secreta (!, ?)')

        html_content = resp.content.decode('utf-8')
        pos_kabuto = html_content.index('id="unown-tab-kabuto"')
        pos_aero = html_content.index('id="unown-tab-aerodactyl"')
        pos_oma = html_content.index('id="unown-tab-omanyte"')
        pos_hooh = html_content.index('id="unown-tab-ho_oh"')
        pos_secret = html_content.index('id="unown-tab-secret_entrance"')
        self.assertTrue(pos_kabuto < pos_aero < pos_oma < pos_hooh < pos_secret)
        self.assertContains(resp, 'id="unown-hgss-note"')
        self.assertContains(resp, 'Mecánicas de Encuentro (Ruinas Alfa & Salas Secretas)')
        self.assertNotContains(resp, 'Ruinas Sosiego • 28 Formas')
        self.assertNotContains(resp, 'id="unown-sinnoh-note"')
        self.assertNotContains(resp, 'id="unown-tab-friend"')
        self.assertNotContains(resp, 'id="unown-tab-dead_ends"')
        self.assertNotContains(resp, 'Particularidad Histórica (Shinies en 2ª Gen)')


class GenderDifferencesAndModalDataTests(TestCase):
    """
    Pruebas para el sistema de diferencias de género de Gen 4 en catálogos y modales:
    - Clasificación correcta (diferencia física, sin diferencia, solo hembra, solo macho, sin género).
    - Exclusión en generaciones anteriores (Gen 1-3 retornan None).
    - Presencia de 'gender_info' en modal_data_json para Gen 4 y ausencia en Gen 1-3.
    """

    def test_gender_info_classification_gen4(self):
        from tracker.gender_differences import get_pokemon_gender_info, GENDER_DIFFERENCES_GEN4

        # 1. Especie con diferencias visuales (ej. Pikachu #25, Combee #415)
        pika_info = get_pokemon_gender_info(25, "diamond")
        self.assertIsNotNone(pika_info)
        self.assertEqual(pika_info["gender_type"], "both_with_diff")
        self.assertTrue(pika_info["can_toggle"])
        self.assertTrue(pika_info["has_visual_differences"])
        self.assertTrue(pika_info["female_sprite_available"])
        self.assertEqual(pika_info["default_gender"], "male")
        self.assertEqual(pika_info["difference_note"], GENDER_DIFFERENCES_GEN4[25])

        combee_info = get_pokemon_gender_info(415, "pearl")
        self.assertIsNotNone(combee_info)
        self.assertEqual(combee_info["gender_type"], "both_with_diff")
        self.assertTrue(combee_info["has_visual_differences"])
        self.assertTrue(combee_info["female_sprite_available"])
        self.assertEqual(combee_info["female_sprites"]["retro"], "/media/pokemon/sprites/pearl_animated/female/415.png")
        self.assertEqual(combee_info["female_sprites"]["retro_animated"], "/media/pokemon/sprites/pearl_animated/female/415.png")
        self.assertEqual(combee_info["female_sprites"]["retro_static"], "/media/pokemon/sprites/pearl/female/415.png")

        # Kricketune (#402) en Perla debe resolver sprite animado femenino
        kricket_info = get_pokemon_gender_info(402, "pearl")
        self.assertIsNotNone(kricket_info)
        self.assertEqual(kricket_info["female_sprites"]["retro"], "/media/pokemon/sprites/pearl_animated/female/402.png")

        # 2. Especie con ambos géneros pero sin diferencias visuales (ej. Turtwig #387)
        turtwig_info = get_pokemon_gender_info(387, "diamond")
        self.assertIsNotNone(turtwig_info)
        self.assertEqual(turtwig_info["gender_type"], "both_no_diff")
        self.assertTrue(turtwig_info["can_toggle"])
        self.assertFalse(turtwig_info["has_visual_differences"])
        self.assertFalse(turtwig_info["female_sprite_available"])
        self.assertEqual(turtwig_info["default_gender"], "male")
        self.assertEqual(turtwig_info["difference_note"], "Sin cambios visuales entre géneros")

        # 3. Especie sin género / asexual (ej. Magnemite #81, Dialga #483)
        magnemite_info = get_pokemon_gender_info(81, "diamond")
        self.assertIsNotNone(magnemite_info)
        self.assertEqual(magnemite_info["gender_type"], "genderless")
        self.assertFalse(magnemite_info["can_toggle"])
        self.assertFalse(magnemite_info["has_visual_differences"])
        self.assertFalse(magnemite_info["female_sprite_available"])

        dialga_info = get_pokemon_gender_info(483, "diamond")
        self.assertIsNotNone(dialga_info)
        self.assertEqual(dialga_info["gender_type"], "genderless")

        # 4. Solo hembra (ej. Chansey #113, Blissey #242)
        chansey_info = get_pokemon_gender_info(113, "diamond")
        self.assertIsNotNone(chansey_info)
        self.assertEqual(chansey_info["gender_type"], "female_only")
        self.assertFalse(chansey_info["can_toggle"])
        self.assertEqual(chansey_info["default_gender"], "female")
        self.assertFalse(chansey_info["female_sprite_available"])

        # 5. Solo macho (ej. Tauros #128, Hitmonlee #106)
        tauros_info = get_pokemon_gender_info(128, "diamond")
        self.assertIsNotNone(tauros_info)
        self.assertEqual(tauros_info["gender_type"], "male_only")
        self.assertFalse(tauros_info["can_toggle"])
        self.assertEqual(tauros_info["default_gender"], "male")
        self.assertFalse(tauros_info["female_sprite_available"])

    def test_gender_info_excluded_in_gen1_to_gen3(self):
        from tracker.gender_differences import get_pokemon_gender_info

        # Gen 1, 2 y 3 no deben tener gender_info activo
        self.assertIsNone(get_pokemon_gender_info(25, "red"))
        self.assertIsNone(get_pokemon_gender_info(25, "gold"))
        self.assertIsNone(get_pokemon_gender_info(25, "emerald"))
        self.assertIsNone(get_pokemon_gender_info(25, "fire-red"))

    def test_catalog_modal_data_contains_gender_info_for_gen4(self):
        from tracker.catalog_service import get_compiled_catalog

        # Gen 4: Diamond debe incluir gender_info en modal_data_json
        diamond_entries = get_compiled_catalog("diamond", is_national=True)
        self.assertIsNotNone(diamond_entries)

        pika_entry = next(e for e in diamond_entries if e.pokemon.national_number == 25)
        pika_modal = json.loads(pika_entry.modal_data_json)
        self.assertIn("gender_info", pika_modal)
        self.assertIsNotNone(pika_modal["gender_info"])
        self.assertTrue(pika_modal["gender_info"]["has_visual_differences"])

        # Gen 3: Emerald NO debe incluir gender_info (o debe ser None)
        emerald_entries = get_compiled_catalog("emerald", is_national=False)
        self.assertIsNotNone(emerald_entries)
        treecko = emerald_entries[0]
        treecko_modal = json.loads(treecko.modal_data_json)
        self.assertIsNone(treecko_modal.get("gender_info"))

    def test_modern_back_sprites_for_special_species(self):
        from tracker.catalog_service import get_compiled_catalog
        diamond_entries = get_compiled_catalog("diamond", is_national=True)
        self.assertIsNotNone(diamond_entries)

        # Torchic (#255), Bidoof (#399), Buizel (#418), Floatzel (#419)
        for num in [255, 399, 418, 419]:
            entry = next(e for e in diamond_entries if e.pokemon.national_number == num)
            m_data = json.loads(entry.modal_data_json)
            self.assertEqual(m_data.get("sprite_modern_back"), f"/media/pokemon/home/back/{num}.png")
            self.assertEqual(m_data.get("sprite_modern_shiny_back"), f"/media/pokemon/home/shiny/back/{num}.png")
            if m_data.get("gender_info") and m_data["gender_info"].get("female_sprites"):
                self.assertEqual(m_data["gender_info"]["female_sprites"].get("modern_back"), f"/media/pokemon/home/back/female/{num}.png")
                self.assertEqual(m_data["gender_info"]["female_sprites"].get("modern_shiny_back"), f"/media/pokemon/home/shiny/back/female/{num}.png")

        # Otro Pokémon (ej. Pikachu #25) no debe tener sprite_modern_back
        pika_entry = next(e for e in diamond_entries if e.pokemon.national_number == 25)
        pika_data = json.loads(pika_entry.modal_data_json)
        self.assertEqual(pika_data.get("sprite_modern_back"), "")

    def test_pokemon_forms_artwork_local_and_correct(self):
        """
        Valida que todas las formas de Pokémon (Cherrim, Shellos, Gastrodon, Burmy,
        Wormadam, Arceus, Unown, Deoxys, Castform) usen rutas locales en media
        y no apunten a URLs externas ni a IDs incorrectos (ej. Rotom Heat/Wash/Frost).
        """
        from tracker.pokemon_forms import get_pokemon_forms
        from pathlib import Path
        from django.conf import settings

        media_root = Path(settings.MEDIA_ROOT)

        # 1. Cherrim (#421)
        cherrim_forms = {f["form_key"]: f for f in get_pokemon_forms(421, "diamond")}
        self.assertIn("sunshine", cherrim_forms)
        sunshine = cherrim_forms["sunshine"]
        self.assertEqual(sunshine["sprite_modern"], "/media/pokemon/home/421-sunshine.png")
        self.assertEqual(sunshine["sprite_modern_shiny"], "/media/pokemon/home/shiny/421-sunshine.png")
        self.assertNotIn("10008", sunshine["sprite_modern"])  # NO debe ser Rotom-Heat
        self.assertTrue((media_root / "pokemon" / "home" / "421-sunshine.png").exists())
        self.assertTrue((media_root / "pokemon" / "home" / "shiny" / "421-sunshine.png").exists())

        # 2. Shellos (#422) y Gastrodon (#423)
        shellos_forms = {f["form_key"]: f for f in get_pokemon_forms(422, "diamond")}
        self.assertEqual(shellos_forms["east"]["sprite_modern"], "/media/pokemon/home/422-east.png")
        self.assertNotIn("10009", shellos_forms["east"]["sprite_modern"])  # NO debe ser Rotom-Wash
        self.assertTrue((media_root / "pokemon" / "home" / "422-east.png").exists())

        gastro_forms = {f["form_key"]: f for f in get_pokemon_forms(423, "diamond")}
        self.assertEqual(gastro_forms["east"]["sprite_modern"], "/media/pokemon/home/423-east.png")
        self.assertNotIn("10010", gastro_forms["east"]["sprite_modern"])  # NO debe ser Rotom-Frost
        self.assertTrue((media_root / "pokemon" / "home" / "423-east.png").exists())

        # 3. Burmy (#412) y Wormadam (#413)
        burmy_forms = {f["form_key"]: f for f in get_pokemon_forms(412, "diamond")}
        self.assertEqual(burmy_forms["sandy"]["sprite_modern"], "/media/pokemon/home/412-sandy.png")
        self.assertEqual(burmy_forms["trash"]["sprite_modern"], "/media/pokemon/home/412-trash.png")
        self.assertTrue((media_root / "pokemon" / "home" / "412-sandy.png").exists())

        worm_forms = {f["form_key"]: f for f in get_pokemon_forms(413, "diamond")}
        self.assertEqual(worm_forms["sandy"]["sprite_modern"], "/media/pokemon/home/10004.png")
        self.assertEqual(worm_forms["trash"]["sprite_modern"], "/media/pokemon/home/10005.png")

        # 4. Arceus (#493) - Discrimina tipos elementales
        arceus_forms = {f["form_key"]: f for f in get_pokemon_forms(493, "diamond")}
        self.assertEqual(arceus_forms["normal"]["sprite_modern"], "/media/pokemon/home/493.png")
        self.assertEqual(arceus_forms["fire"]["sprite_modern"], "/media/pokemon/home/493-fire.png")
        self.assertEqual(arceus_forms["water"]["sprite_modern"], "/media/pokemon/home/493-water.png")
        self.assertTrue((media_root / "pokemon" / "home" / "493-fire.png").exists())
        self.assertTrue((media_root / "pokemon" / "home" / "shiny" / "493-fire.png").exists())

        # 5. Unown (#201)
        unown_forms = {f["form_key"]: f for f in get_pokemon_forms(201, "diamond")}
        self.assertEqual(unown_forms["a"]["sprite_modern"], "/media/pokemon/home/201-a.png")
        self.assertEqual(unown_forms["f"]["sprite_modern"], "/media/pokemon/home/201-f.png")
        self.assertEqual(unown_forms["b"]["sprite_modern"], "/media/pokemon/home/201-b.png")
        self.assertTrue((media_root / "pokemon" / "home" / "201-a.png").exists())
        self.assertTrue((media_root / "pokemon" / "home" / "201-f.png").exists())
        self.assertTrue((media_root / "pokemon" / "home" / "shiny" / "201-f.png").exists())

        # 6. Deoxys (#386) y Castform (#351)
        deoxys_forms = {f["form_key"]: f for f in get_pokemon_forms(386, "diamond")}
        self.assertEqual(deoxys_forms["attack"]["sprite_modern"], "/media/pokemon/home/10001.png")
        self.assertTrue((media_root / "pokemon" / "home" / "10001.png").exists())

        cast_forms = {f["form_key"]: f for f in get_pokemon_forms(351, "diamond")}
        self.assertEqual(cast_forms["sunny"]["sprite_modern"], "/media/pokemon/home/10013.png")
        self.assertTrue((media_root / "pokemon" / "home" / "10013.png").exists())


    def test_diamond_modal_animated_sprites_and_gender_and_forms(self):
        """
        Valida que los sprites retro animados (APNG) se apliquen exclusivamente
        en el modal de cómic de Pokémon Diamante:
        1. Las entradas base tienen modal_retro_sprite_url y modal_retro_sprite_shiny_url en diamond_animated.
        2. La cuadrícula de la Pokédex mantiene game_sprite_url estático en diamond.
        3. Los sprites de espalda se mantienen estáticos en diamond/back y diamond_shiny/back.
        4. Las formas alternativas (Deoxys, Burmy, Wormadam, Cherrim, Shellos, Gastrodon, Arceus, Unown, Castform)
           tienen modal_retro_sprite_url y modal_retro_sprite_shiny_url animados.
        5. Las diferencias de género femeninas en Diamante tienen sprites animados retro_animated.
        """
        from tracker.catalog_service import get_compiled_catalog
        from tracker.gender_differences import get_pokemon_gender_info
        from tracker.pokemon_forms import get_pokemon_forms
        import json

        diamond_entries = get_compiled_catalog("diamond", is_national=True)
        self.assertIsNotNone(diamond_entries)

        # 1. Base Pokémon (Turtwig #387, Pikachu #25, Dialga #483)
        turtwig = next(e for e in diamond_entries if e.pokemon.national_number == 387)
        self.assertEqual(turtwig.game_sprite_url, "/media/pokemon/sprites/diamond/387.png")
        self.assertEqual(turtwig.game_sprite_shiny_url, "/media/pokemon/sprites/diamond_shiny/387.png")
        self.assertEqual(turtwig.modal_retro_sprite_url, "/media/pokemon/sprites/diamond_animated/387.png")
        self.assertEqual(turtwig.modal_retro_sprite_shiny_url, "/media/pokemon/sprites/diamond_animated_shiny/387.png")
        self.assertEqual(turtwig.game_sprite_back_url, "/media/pokemon/sprites/diamond/back/387.png")
        self.assertEqual(turtwig.game_sprite_shiny_back_url, "/media/pokemon/sprites/diamond_shiny/back/387.png")

        m_data = json.loads(turtwig.modal_data_json)
        self.assertEqual(m_data["sprite_retro"], "/media/pokemon/sprites/diamond_animated/387.png")
        self.assertEqual(m_data["sprite_retro_shiny"], "/media/pokemon/sprites/diamond_animated_shiny/387.png")
        self.assertEqual(m_data["sprite_retro_back"], "/media/pokemon/sprites/diamond/back/387.png")

        # 2. Diferencias de género femeninas (Pikachu #25)
        pika_gender = get_pokemon_gender_info(25, "diamond")
        self.assertTrue(pika_gender["has_visual_differences"])
        fem_sprites = pika_gender["female_sprites"]
        self.assertIsNotNone(fem_sprites)
        self.assertEqual(fem_sprites["retro"], "/media/pokemon/sprites/diamond_animated/female/25.png")
        self.assertEqual(fem_sprites["retro_shiny"], "/media/pokemon/sprites/diamond_animated_shiny/female/25.png")
        self.assertEqual(fem_sprites["retro_animated"], "/media/pokemon/sprites/diamond_animated/female/25.png")
        self.assertEqual(fem_sprites["retro_static"], "/media/pokemon/sprites/diamond/female/25.png")
        self.assertEqual(fem_sprites["retro_back"], "/media/pokemon/sprites/diamond/back/female/25.png")

        # 3. Formas alternativas animadas en Diamante
        # Deoxys
        deoxys_forms = {f["form_key"]: f for f in get_pokemon_forms(386, "diamond")}
        self.assertEqual(deoxys_forms["normal"]["modal_retro_sprite_url"], "/media/pokemon/sprites/diamond_animated/deoxys/normal.png")
        self.assertEqual(deoxys_forms["attack"]["modal_retro_sprite_url"], "/media/pokemon/sprites/diamond_animated/deoxys/attack.png")
        self.assertEqual(deoxys_forms["defense"]["modal_retro_sprite_url"], "/media/pokemon/sprites/diamond_animated/deoxys/defense.png")
        self.assertEqual(deoxys_forms["speed"]["modal_retro_sprite_url"], "/media/pokemon/sprites/diamond_animated/deoxys/speed.png")

        # Burmy & Wormadam
        burmy_forms = {f["form_key"]: f for f in get_pokemon_forms(412, "diamond")}
        self.assertEqual(burmy_forms["plant"]["modal_retro_sprite_url"], "/media/pokemon/sprites/diamond_animated/burmy/plant.png")
        self.assertEqual(burmy_forms["sandy"]["modal_retro_sprite_url"], "/media/pokemon/sprites/diamond_animated/burmy/sandy.png")
        self.assertEqual(burmy_forms["trash"]["modal_retro_sprite_url"], "/media/pokemon/sprites/diamond_animated/burmy/trash.png")

        worm_forms = {f["form_key"]: f for f in get_pokemon_forms(413, "diamond")}
        self.assertEqual(worm_forms["plant"]["modal_retro_sprite_url"], "/media/pokemon/sprites/diamond_animated/wormadam/plant.png")
        self.assertEqual(worm_forms["sandy"]["modal_retro_sprite_url"], "/media/pokemon/sprites/diamond_animated/wormadam/sandy.png")
        self.assertEqual(worm_forms["trash"]["modal_retro_sprite_url"], "/media/pokemon/sprites/diamond_animated/wormadam/trash.png")

        # Cherrim
        cherrim_forms = {f["form_key"]: f for f in get_pokemon_forms(421, "diamond")}
        self.assertEqual(cherrim_forms["overcast"]["modal_retro_sprite_url"], "/media/pokemon/sprites/diamond_animated/cherrim/overcast.png")
        self.assertEqual(cherrim_forms["sunshine"]["modal_retro_sprite_url"], "/media/pokemon/sprites/diamond_animated/cherrim/sunshine.png")

        # Shellos & Gastrodon
        shellos_forms = {f["form_key"]: f for f in get_pokemon_forms(422, "diamond")}
        self.assertEqual(shellos_forms["west"]["modal_retro_sprite_url"], "/media/pokemon/sprites/diamond_animated/shellos/west.png")
        self.assertEqual(shellos_forms["east"]["modal_retro_sprite_url"], "/media/pokemon/sprites/diamond_animated/shellos/east.png")

        gastro_forms = {f["form_key"]: f for f in get_pokemon_forms(423, "diamond")}
        self.assertEqual(gastro_forms["west"]["modal_retro_sprite_url"], "/media/pokemon/sprites/diamond_animated/gastrodon/west.png")
        self.assertEqual(gastro_forms["east"]["modal_retro_sprite_url"], "/media/pokemon/sprites/diamond_animated/gastrodon/east.png")

        # Arceus
        arceus_forms = {f["form_key"]: f for f in get_pokemon_forms(493, "diamond")}
        self.assertEqual(arceus_forms["normal"]["modal_retro_sprite_url"], "/media/pokemon/sprites/diamond_animated/arceus/normal.png")
        self.assertEqual(arceus_forms["fire"]["modal_retro_sprite_url"], "/media/pokemon/sprites/diamond_animated/arceus/fire.png")
        self.assertEqual(arceus_forms["water"]["modal_retro_sprite_url"], "/media/pokemon/sprites/diamond_animated/arceus/water.png")

        # Unown
        unown_forms = {f["form_key"]: f for f in get_pokemon_forms(201, "diamond")}
        self.assertEqual(unown_forms["a"]["modal_retro_sprite_url"], "/media/pokemon/sprites/diamond_animated/unown/a.png")
        self.assertEqual(unown_forms["exclamation"]["modal_retro_sprite_url"], "/media/pokemon/sprites/diamond_animated/unown/exclamation.png")
        self.assertEqual(unown_forms["question"]["modal_retro_sprite_url"], "/media/pokemon/sprites/diamond_animated/unown/question.png")

        # Castform normal
        cast_forms = {f["form_key"]: f for f in get_pokemon_forms(351, "diamond")}
        self.assertEqual(cast_forms["normal"]["modal_retro_sprite_url"], "/media/pokemon/sprites/diamond_animated/351.png")

        # 4. Validar integridad de fotogramas y diferenciación de formas
        from PIL import Image
        from pathlib import Path
        from django.conf import settings
        media_root = Path(settings.MEDIA_ROOT)
        
        # Cherrim overcast debe tener 30 frames animados (desde Platino) y forma de capullo morado
        cherrim_anim = Image.open(media_root / "pokemon" / "sprites" / "diamond_animated" / "cherrim" / "overcast.png")
        self.assertEqual(getattr(cherrim_anim, "n_frames", 1), 30)

        # Burmy sandy y trash deben tener 22 frames y colores no invertidos
        burmy_sandy = Image.open(media_root / "pokemon" / "sprites" / "diamond_animated" / "burmy" / "sandy.png")
        burmy_trash = Image.open(media_root / "pokemon" / "sprites" / "diamond_animated" / "burmy" / "trash.png")
        self.assertEqual(getattr(burmy_sandy, "n_frames", 1), 22)
        self.assertEqual(getattr(burmy_trash, "n_frames", 1), 22)
        pix_sandy = [p for p in burmy_sandy.convert("RGBA").getdata() if p[3] > 50]
        pix_trash = [p for p in burmy_trash.convert("RGBA").getdata() if p[3] > 50]
        avg_sandy = (sum(p[0] for p in pix_sandy) // len(pix_sandy), sum(p[1] for p in pix_sandy) // len(pix_sandy), sum(p[2] for p in pix_sandy) // len(pix_sandy))
        avg_trash = (sum(p[0] for p in pix_trash) // len(pix_trash), sum(p[1] for p in pix_trash) // len(pix_trash), sum(p[2] for p in pix_trash) // len(pix_trash))
        self.assertGreater(avg_trash[0] - avg_trash[1], avg_sandy[0] - avg_sandy[1])

    def test_platinum_forms_static_and_animated_assets_exist(self):
        """
        Garantiza que todas las formas alternas de Pokémon Platino (Wormadam, Burmy, Castform, etc.)
        tengan tanto sus sprites estáticos (para la cuadrícula de la Pokédex) como animados
        (para el modal cómic) presentes físicamente en media/ sin devolver 404.
        """
        from tracker.pokemon_forms import get_pokemon_forms
        from pathlib import Path
        from django.conf import settings

        media_root = Path(settings.MEDIA_ROOT)

        # 1. Wormadam (#413) en Platino: plant, sandy, trash
        worm_forms = get_pokemon_forms(413, "platinum")
        self.assertEqual(len(worm_forms), 3)
        for f in worm_forms:
            for key in ["sprite_retro", "sprite_retro_shiny", "sprite_retro_back", "sprite_retro_shiny_back",
                        "modal_retro_sprite_url", "modal_retro_sprite_shiny_url"]:
                url = f.get(key)
                if url and url.startswith("/media/"):
                    disk_path = media_root / url.replace("/media/", "")
                    self.assertTrue(disk_path.exists(), f"Falta el archivo para Wormadam {f['form_key']} ({key}): {url}")

        # 2. Burmy (#412) en Platino: plant, sandy, trash
        burmy_forms = get_pokemon_forms(412, "platinum")
        self.assertEqual(len(burmy_forms), 3)
        for f in burmy_forms:
            for key in ["sprite_retro", "sprite_retro_shiny", "sprite_retro_back", "sprite_retro_shiny_back",
                        "modal_retro_sprite_url", "modal_retro_sprite_shiny_url"]:
                url = f.get(key)
                if url and url.startswith("/media/"):
                    disk_path = media_root / url.replace("/media/", "")
                    self.assertTrue(disk_path.exists(), f"Falta el archivo para Burmy {f['form_key']} ({key}): {url}")

        # 3. Castform (#351) en Platino
        cast_forms = get_pokemon_forms(351, "platinum")
        self.assertEqual(len(cast_forms), 4)
        for f in cast_forms:
            for key in ["sprite_retro", "sprite_retro_shiny", "sprite_retro_back", "sprite_retro_shiny_back"]:
                url = f.get(key)
                if url and url.startswith("/media/"):
                    disk_path = media_root / url.replace("/media/", "")
                    self.assertTrue(disk_path.exists(), f"Falta el archivo para Castform {f['form_key']} ({key}): {url}")

    def test_heartgold_forms_static_and_animated_assets_exist(self):
        """
        Garantiza que todas las formas alternas de Pokémon Oro HeartGold (Arceus 17 formas, Castform 4 formas,
        Burmy 3 formas, Wormadam 3 formas) cuenten con sprites estáticos, traseros y animados en media/ sin 404.
        """
        from tracker.pokemon_forms import get_pokemon_forms
        from pathlib import Path
        from django.conf import settings
        from PIL import Image

        media_root = Path(settings.MEDIA_ROOT)

        # 1. Arceus (#493) en HeartGold: 17 formas elementales
        arceus_forms = get_pokemon_forms(493, "heartgold")
        self.assertEqual(len(arceus_forms), 17)
        for f in arceus_forms:
            for key in ["sprite_retro", "sprite_retro_shiny", "sprite_retro_back", "sprite_retro_shiny_back",
                        "modal_retro_sprite_url", "modal_retro_sprite_shiny_url"]:
                url = f.get(key)
                self.assertIsNotNone(url, f"La URL {key} para Arceus {f['form_key']} no debe ser None")
                if url and url.startswith("/media/"):
                    disk_path = media_root / url.replace("/media/", "")
                    self.assertTrue(disk_path.exists(), f"Falta el archivo para Arceus {f['form_key']} ({key}): {url}")

        # 2. Castform (#351) en HeartGold: 4 formas climáticas animadas y estáticas
        cast_forms = get_pokemon_forms(351, "heartgold")
        self.assertEqual(len(cast_forms), 4)
        for f in cast_forms:
            for key in ["sprite_retro", "sprite_retro_shiny", "sprite_retro_back", "sprite_retro_shiny_back",
                        "modal_retro_sprite_url", "modal_retro_sprite_shiny_url"]:
                url = f.get(key)
                self.assertIsNotNone(url, f"La URL {key} para Castform {f['form_key']} no debe ser None")
                if url and url.startswith("/media/"):
                    disk_path = media_root / url.replace("/media/", "")
                    self.assertTrue(disk_path.exists(), f"Falta el archivo para Castform {f['form_key']} ({key}): {url}")

        # 3. Burmy (#412) y Wormadam (#413) en HeartGold: existencia y verificación de color
        for nat_num, name in [(412, "Burmy"), (413, "Wormadam")]:
            forms = get_pokemon_forms(nat_num, "heartgold")
            self.assertEqual(len(forms), 3)
            for f in forms:
                for key in ["sprite_retro", "sprite_retro_shiny", "sprite_retro_back", "sprite_retro_shiny_back",
                            "modal_retro_sprite_url", "modal_retro_sprite_shiny_url"]:
                    url = f.get(key)
                    if url and url.startswith("/media/"):
                        disk_path = media_root / url.replace("/media/", "")
                        self.assertTrue(disk_path.exists(), f"Falta el archivo para {name} {f['form_key']} ({key}): {url}")

            # Validación de no-inversión de colores: Tronco Basura (rosado) vs Tronco Arena (marrón)
            # En estáticos y en animados
            for anim_key, subfolder in [("sprite_retro", name.lower()), ("modal_retro_sprite_url", f"heartgold_animated/{name.lower()}")]:
                f_sandy = next(f for f in forms if f["form_key"] == "sandy")
                f_trash = next(f for f in forms if f["form_key"] == "trash")

                path_sandy = media_root / f_sandy[anim_key].replace("/media/", "")
                path_trash = media_root / f_trash[anim_key].replace("/media/", "")

                img_s = Image.open(path_sandy).convert("RGBA")
                img_t = Image.open(path_trash).convert("RGBA")

                pix_s = [p for p in img_s.getdata() if p[3] > 50]
                pix_t = [p for p in img_t.getdata() if p[3] > 50]

                diff_s = (sum(p[0] for p in pix_s) // len(pix_s)) - (sum(p[1] for p in pix_s) // len(pix_s))
                diff_t = (sum(p[0] for p in pix_t) // len(pix_t)) - (sum(p[1] for p in pix_t) // len(pix_t))

                self.assertGreater(diff_t, diff_s, f"Los colores de {name} ({anim_key}) están invertidos: Basura debe tener mayor componente rojo/rosado que Arena.")


class JohtoSafariZoneTests(TestCase):
    def test_has_johto_safari_property(self):
        from tracker.models import Game
        hg = Game(name="HeartGold", slug="heartgold", generation=4)
        ss = Game(name="SoulSilver", slug="soulsilver", generation=4)
        fr = Game(name="FireRed", slug="firered", generation=3)
        em = Game(name="Emerald", slug="emerald", generation=3)
        dia = Game(name="Diamond", slug="diamond", generation=4)

        self.assertTrue(hg.has_johto_safari)
        self.assertTrue(ss.has_johto_safari)
        self.assertFalse(fr.has_johto_safari)
        self.assertFalse(em.has_johto_safari)
        self.assertFalse(dia.has_johto_safari)

    def test_heartgold_safari_biome_tags(self):
        from tracker.catalog_service import get_compiled_catalog
        catalog = get_compiled_catalog("heartgold", force_reload=True)

        expected_biomes = [
            "safari_albufera", "safari_arboleda", "safari_desierto", "safari_lagos",
            "safari_laguna", "safari_montana", "safari_pantano", "safari_parterre",
            "safari_pena", "safari_prado", "safari_paramo", "safari_sabana"
        ]

        # Verificar que todos los 12 biomas oficiales tienen al menos un pokémon etiquetado
        for biome_tag in expected_biomes:
            matches = [e for e in catalog if biome_tag in e.filter_tags.split()]
            self.assertGreater(len(matches), 0, f"El bioma {biome_tag} no tiene Pokémon asociados")

        # Verificar que 'Bahía Blanca' no existe como tag de bioma
        bahia_matches = [e for e in catalog if "bahia" in e.filter_tags.lower()]
        self.assertEqual(len(bahia_matches), 0, "No debe existir ningún tag con bahia en el catálogo")

        # Verificar que los Pokémon de Acceso al Safari no tienen tag 'safari' por error
        hoothoot = [e for e in catalog if e.pokemon.national_number == 163][0]
        self.assertNotIn("safari", hoothoot.filter_tags.split())

        # Verificar que en modo Regional, Peña tiene exactamente sus 6 especies canónicas y NO tiene especies con bloques
        pena_entries = [e for e in catalog if "safari_pena" in e.filter_tags.split()]
        pena_names = {e.pokemon.display_name for e in pena_entries}
        expected_regional_pena = {"Geodude", "Graveler", "Magnemite", "Magneton", "Magmar", "Wobbuffet"}
        self.assertEqual(pena_names, expected_regional_pena)

        # Verificar que en el catálogo Nacional, Peña contiene 15 especies canónicas (incluyendo las de bloques)
        nat_catalog = get_compiled_catalog("heartgold", force_reload=True, is_national=True)
        nat_pena_entries = [e for e in nat_catalog if "safari_pena" in e.filter_tags.split()]
        nat_pena_names = {e.pokemon.display_name for e in nat_pena_entries}
        self.assertEqual(len(nat_pena_names), 15)
        self.assertTrue({"Fearow", "Paras", "Slowbro", "Beldum", "Lairon"}.issubset(nat_pena_names) or {"Fearow", "Paras", "Slowbro"}.issubset(nat_pena_names))

        # Validar recuentos globales exactos: 75 únicas en Regional y 153 únicas en Nacional
        reg_safari_total = len([e for e in catalog if "safari" in e.filter_tags.split()])
        nat_safari_total = len([e for e in nat_catalog if "safari" in e.filter_tags.split()])
        self.assertEqual(reg_safari_total, 75)
        self.assertEqual(nat_safari_total, 153)

    def test_soulsilver_safari_biome_tags(self):
        from tracker.catalog_service import get_compiled_catalog
        catalog = get_compiled_catalog("soulsilver", force_reload=True)

        expected_biomes = [
            "safari_albufera", "safari_arboleda", "safari_desierto", "safari_lagos",
            "safari_laguna", "safari_montana", "safari_pantano", "safari_parterre",
            "safari_pena", "safari_prado", "safari_paramo", "safari_sabana"
        ]

        # Verificar que todos los 12 biomas oficiales tienen al menos un pokémon etiquetado
        for biome_tag in expected_biomes:
            matches = [e for e in catalog if biome_tag in e.filter_tags.split()]
            self.assertGreater(len(matches), 0, f"El bioma {biome_tag} no tiene Pokémon asociados en SoulSilver")

        # Verificar que 'Bahía Blanca' no existe como tag de bioma
        bahia_matches = [e for e in catalog if "bahia" in e.filter_tags.lower()]
        self.assertEqual(len(bahia_matches), 0, "No debe existir ningún tag con bahia en el catálogo")

        # Verificar que los Pokémon de Acceso al Safari no tienen tag 'safari' por error
        hoothoot = [e for e in catalog if e.pokemon.national_number == 163][0]
        self.assertNotIn("safari", hoothoot.filter_tags.split())

        # Verificar que en modo Regional, Peña tiene exactamente sus 6 especies canónicas y NO tiene especies con bloques
        pena_entries = [e for e in catalog if "safari_pena" in e.filter_tags.split()]
        pena_names = {e.pokemon.display_name for e in pena_entries}
        expected_regional_pena = {"Geodude", "Graveler", "Magnemite", "Magneton", "Magmar", "Wobbuffet"}
        self.assertEqual(pena_names, expected_regional_pena)

        # Verificar que en modo Regional, Albufera tiene exactamente sus 12 especies canónicas sin bloques
        albufera_entries = [e for e in catalog if "safari_albufera" in e.filter_tags.split()]
        albufera_names = {e.pokemon.display_name for e in albufera_entries}
        expected_regional_albufera = {
            "Arbok", "Ekans", "Gloom", "Grimer", "Gyarados", "Koffing",
            "Magikarp", "Oddish", "Poliwag", "Poliwhirl", "Weezing", "Wooper"
        }
        self.assertEqual(albufera_names, expected_regional_albufera)
        # Asegurar que NO se filtran pokémon que requieren bloques en Albufera
        self.assertFalse({"Quagsire", "Jumpluff", "Muk", "Diglett"}.intersection(albufera_names))

        # Verificar que en el catálogo Nacional, Peña contiene 15 especies canónicas (incluyendo las de bloques)
        nat_catalog = get_compiled_catalog("soulsilver", force_reload=True, is_national=True)
        nat_pena_entries = [e for e in nat_catalog if "safari_pena" in e.filter_tags.split()]
        nat_pena_names = {e.pokemon.display_name for e in nat_pena_entries}
        self.assertEqual(len(nat_pena_names), 15)

        # Validar recuentos globales exactos: 75 únicas en Regional y 153 únicas en Nacional
        reg_safari_total = len([e for e in catalog if "safari" in e.filter_tags.split()])
        nat_safari_total = len([e for e in nat_catalog if "safari" in e.filter_tags.split()])
        self.assertEqual(reg_safari_total, 75)
        self.assertEqual(nat_safari_total, 153)


class HeartGoldAdvancedFiltersTests(TestCase):
    """Pruebas exhaustivas para los nuevos filtros mecánicos de Pokémon Oro HeartGold (y SoulSilver)."""

    def setUp(self):
        self.game, _ = Game.objects.get_or_create(slug="heartgold", defaults={"name": "Pokémon Oro HeartGold", "generation": 4})
        self.ss, _ = Game.objects.get_or_create(slug="soulsilver", defaults={"name": "Pokémon Plata SoulSilver", "generation": 4})
        self.crystal, _ = Game.objects.get_or_create(slug="crystal", defaults={"name": "Pokémon Cristal", "generation": 2})
        self.diamond, _ = Game.objects.get_or_create(slug="diamond", defaults={"name": "Pokémon Diamante", "generation": 4})

    def test_game_filter_properties(self):
        """Verifica las propiedades booleanas de mecánicas en el modelo Game."""
        # Golpe Cabeza
        self.assertTrue(self.game.has_headbutt)
        self.assertTrue(self.ss.has_headbutt)
        self.assertTrue(self.crystal.has_headbutt)
        self.assertFalse(self.diamond.has_headbutt)

        # Concurso de Bichos
        self.assertTrue(self.game.has_bug_contest)
        self.assertTrue(self.ss.has_bug_contest)
        self.assertTrue(self.crystal.has_bug_contest)
        self.assertFalse(self.diamond.has_bug_contest)

        # Manadas regionales
        self.assertTrue(self.game.has_regional_swarms)
        self.assertTrue(self.ss.has_regional_swarms)
        self.assertTrue(self.crystal.has_regional_swarms)
        self.assertFalse(self.diamond.has_regional_swarms)

        # Sonidos de Hoenn y Sinnoh
        self.assertTrue(self.game.has_regional_sounds)
        self.assertTrue(self.ss.has_regional_sounds)
        self.assertFalse(self.crystal.has_regional_sounds)
        self.assertFalse(self.diamond.has_regional_sounds)

        # Golpe Roca
        self.assertTrue(self.game.has_rock_smash)
        self.assertTrue(self.ss.has_rock_smash)
        self.assertTrue(self.diamond.has_rock_smash)

        # Pokéwalker
        self.assertTrue(self.game.has_pokewalker)
        self.assertTrue(self.ss.has_pokewalker)
        self.assertFalse(self.diamond.has_pokewalker)

        # Hora del día
        self.assertTrue(self.game.has_time_of_day)
        self.assertTrue(self.crystal.has_time_of_day)
        self.assertTrue(self.diamond.has_time_of_day)

    def test_heartgold_tags_assignment(self):
        """Verifica que el servicio de catálogo asigne las etiquetas quirúrgicas en Regional y Nacional."""
        reg_catalog = get_compiled_catalog("heartgold", force_reload=True, is_national=False)
        nat_catalog = get_compiled_catalog("heartgold", force_reload=True, is_national=True)

        def get_names_with_tag(cat, tag):
            return {e.pokemon.display_name for e in cat if tag in e.filter_tags.split()}

        # 1. Golpe Cabeza
        reg_headbutt = get_names_with_tag(reg_catalog, "headbutt")
        nat_headbutt = get_names_with_tag(nat_catalog, "headbutt")
        self.assertEqual(len(reg_headbutt), 15)
        self.assertEqual(len(nat_headbutt), 24)
        self.assertIn("Heracross", reg_headbutt)
        self.assertIn("Aipom", reg_headbutt)
        self.assertIn("Slakoth", nat_headbutt)
        self.assertIn("Burmy", nat_headbutt)
        self.assertIn("Cherubi", nat_headbutt)

        # 2. Concurso de Bichos
        reg_contest = get_names_with_tag(reg_catalog, "bug_contest")
        nat_contest = get_names_with_tag(nat_catalog, "bug_contest")
        self.assertEqual(len(reg_contest), 10)
        self.assertEqual(len(nat_contest), 21)
        self.assertIn("Scyther", reg_contest)
        self.assertIn("Pinsir", reg_contest)
        self.assertIn("Wurmple", nat_contest)
        self.assertIn("Nincada", nat_contest)
        self.assertIn("Combee", nat_contest)

        # 3. Manadas
        reg_swarms = get_names_with_tag(reg_catalog, "swarm")
        nat_swarms = get_names_with_tag(nat_catalog, "swarm")
        self.assertEqual(len(reg_swarms), 8)
        self.assertEqual(len(nat_swarms), 20)
        self.assertIn("Dunsparce", reg_swarms)
        self.assertIn("Yanma", reg_swarms)
        self.assertIn("Qwilfish", reg_swarms)
        self.assertIn("Poochyena", nat_swarms)
        self.assertIn("Ralts", nat_swarms)

        # 4. Sonidos de Hoenn y Sinnoh (exclusivos de Nacional)
        reg_hoenn = get_names_with_tag(reg_catalog, "hoenn_sound")
        reg_sinnoh = get_names_with_tag(reg_catalog, "sinnoh_sound")
        self.assertEqual(len(reg_hoenn), 0)
        self.assertEqual(len(reg_sinnoh), 0)

        nat_hoenn = get_names_with_tag(nat_catalog, "hoenn_sound")
        nat_sinnoh = get_names_with_tag(nat_catalog, "sinnoh_sound")
        self.assertEqual(len(nat_hoenn), 10)
        self.assertEqual(len(nat_sinnoh), 9)
        self.assertIn("Zigzagoon", nat_hoenn)
        self.assertIn("Whismur", nat_hoenn)
        self.assertIn("Absol", nat_hoenn)
        self.assertNotIn("Mawile", nat_hoenn)
        self.assertNotIn("Gulpin", nat_hoenn)
        self.assertIn("Bidoof", nat_sinnoh)
        self.assertIn("Shinx", nat_sinnoh)
        self.assertIn("Carnivine", nat_sinnoh)

        # 5. Golpe Roca
        reg_rock = get_names_with_tag(reg_catalog, "rock_smash")
        nat_rock = get_names_with_tag(nat_catalog, "rock_smash")
        self.assertIn("Shuckle", reg_rock)
        self.assertIn("Geodude", reg_rock)
        self.assertIn("Dunsparce", reg_rock)
        self.assertIn("Omanyte", nat_rock)
        self.assertIn("Aerodactyl", nat_rock)
        self.assertIn("Anorith", nat_rock)
        self.assertNotIn("Cranidos", nat_rock)
        self.assertNotIn("Shieldon", nat_rock)

        # 6. Pokéwalker (77 en Regional Johto, 118 en Nacional)
        reg_walker = get_names_with_tag(reg_catalog, "pokewalker")
        nat_walker = get_names_with_tag(nat_catalog, "pokewalker")
        self.assertEqual(len(reg_walker), 77)
        self.assertEqual(len(nat_walker), 118)
        self.assertIn("Cleffa", reg_walker)
        self.assertIn("Igglybuff", reg_walker)
        self.assertIn("Magby", reg_walker)
        self.assertIn("Elekid", reg_walker)
        self.assertIn("Smoochum", reg_walker)
        self.assertIn("Feebas", nat_walker)
        self.assertIn("Spiritomb", nat_walker)
        self.assertIn("Munchlax", nat_walker)
        self.assertIn("Torchic", nat_walker)

        # Verificación específica de descripciones y rutas de bebés (Cleffa #173)
        cleffa = next(e for e in reg_catalog if e.pokemon.national_number == 173)
        self.assertNotIn("exclusivamente", cleffa.obtaining_info["summary"].lower())
        self.assertIn("Campo Amistad", cleffa.obtaining_info["summary"])
        cleffa_areas = [l["area"] for l in cleffa.obtaining_info["locations"]]
        self.assertIn("Pokéwalker (Campo Amistad)", cleffa_areas)
        self.assertIn("Ruta 34 (Guardería Pokémon)", cleffa_areas)

        # Verificación toponimia oficial en transferencias (Feebas #349, Snorunt #361, Shellos #422)
        feebas = next(e for e in nat_catalog if e.pokemon.national_number == 349)
        self.assertIn("Cueva Calma", feebas.obtaining_info["summary"])
        feebas_areas = [l["area"] for l in feebas.obtaining_info["locations"]]
        self.assertIn("Pokéwalker (Cueva Calma)", feebas_areas)

        snorunt = next(e for e in nat_catalog if e.pokemon.national_number == 361)
        self.assertIn("Senda Glacial", snorunt.obtaining_info["summary"])
        snorunt_areas = [l["area"] for l in snorunt.obtaining_info["locations"]]
        self.assertIn("Pokéwalker (Senda Glacial)", snorunt_areas)

        # 7. Hora del día (Mañana, Día, Noche)
        reg_morning = get_names_with_tag(reg_catalog, "time_morning")
        reg_day = get_names_with_tag(reg_catalog, "time_day")
        reg_night = get_names_with_tag(reg_catalog, "time_night")
        self.assertIn("Pidgey", reg_morning)
        self.assertIn("Pidgey", reg_day)
        self.assertIn("Hoothoot", reg_night)
        self.assertIn("Spinarak", reg_night)

        # 8. Manaphy (#490) - Nota histórica y exclusión de Guardería directa
        manaphy = next(e for e in nat_catalog if e.pokemon.national_number == 490)
        self.assertIn("Trazos de Luz", manaphy.obtaining_info["summary"])
        manaphy_areas = [l["area"] for l in manaphy.obtaining_info["locations"]]
        self.assertIn("Tienda Pokémon de Johto", manaphy_areas)
        self.assertNotIn("Ruta 34 (Guardería Pokémon)", manaphy_areas)
        self.assertIsNotNone(manaphy.obtaining_info.get("historical_note"))
        self.assertIn("Trazos de Luz", manaphy.obtaining_info["historical_note"]["text"])
        self.assertIn("Phione", manaphy.obtaining_info["historical_note"]["text"])

        # 9. Phione (#489) - Crianza de Manaphy y exclusión de Parque Compi
        phione = next(e for e in nat_catalog if e.pokemon.national_number == 489)
        self.assertEqual(phione.obtaining_info["type"], "baby")
        self.assertEqual(phione.obtaining_info["badge_label"], "Crianza")
        self.assertIn("crianza en la guardería de la ruta 34", phione.obtaining_info["summary"].lower())
        phione_areas = [l["area"] for l in phione.obtaining_info["locations"]]
        self.assertIn("Ruta 34 (Guardería Pokémon)", phione_areas)
        self.assertNotIn("Parque Compi / Intercambio", phione_areas)

        # 10. Spearow (#21) - Desglose de rutas individuales, regalo del guardia y búsqueda
        spearow = next(e for e in reg_catalog if e.pokemon.national_number == 21)
        self.assertNotIn("randy", spearow.obtaining_info["summary"].lower())
        self.assertNotIn("kenya", spearow.obtaining_info["summary"].lower())
        self.assertIn("guardia", spearow.obtaining_info["summary"].lower())
        self.assertLess(len(spearow.obtaining_info["summary"]), 160)
        spearow_areas = [l["area"] for l in spearow.obtaining_info["locations"]]
        self.assertNotIn("Rutas de Johto y Kanto", spearow_areas)
        self.assertIn("Ruta 33", spearow_areas)
        self.assertIn("Ruta 42", spearow_areas)
        self.assertIn("Pueblo Azalea", spearow_areas)
        self.assertIn("Ciudad Trigal (Paso Norte)", spearow_areas)
        self.assertIn("Zona Safari (Pantano)", spearow_areas)
        self.assertIn("Pokéwalker (Bosque Murmullos)", spearow_areas)
        self.assertIn("ruta 33", spearow.filter_locations.lower())
        self.assertIn("ruta 42", spearow.filter_locations.lower())
        gift_loc = next(l for l in spearow.obtaining_info["locations"] if l["area"] == "Ciudad Trigal (Paso Norte)")
        self.assertIn("ESPI", gift_loc["method"])
        self.assertIn("guardia", gift_loc["method"].lower())

        # 11. Tentacool (#72) - Regalo anti-bloqueo y desglose de rutas marítimas
        tentacool = next(e for e in reg_catalog if e.pokemon.national_number == 72)
        tentacool_areas = [l["area"] for l in tentacool.obtaining_info["locations"]]
        self.assertNotIn("Rutas marítimas de Johto y Kanto", tentacool_areas)
        self.assertIn("Ruta 40 (Ruta Marítima)", tentacool_areas)
        self.assertIn("Ruta 41 (Ruta Marítima)", tentacool_areas)
        cianwood_loc = next(l for l in tentacool.obtaining_info["locations"] if l["area"] == "Ciudad Orquídea (Centro Pokémon)")
        self.assertIn("anti-bloqueo", cianwood_loc["method"].lower())
        self.assertIn("pescar", cianwood_loc["method"].lower())

        # 12. Eevee (#133) y Premios de Casino en HeartGold, Crystal, FireRed y LeafGreen
        eevee_hg = next(e for e in reg_catalog if e.pokemon.national_number == 133)
        self.assertEqual(eevee_hg.obtaining_info["badge_label"], "Regalo / Casino")
        self.assertIn("6.666", eevee_hg.obtaining_info["summary"])
        self.assertIn("trigal", eevee_hg.obtaining_info["summary"].lower())
        eevee_areas = [l["area"] for l in eevee_hg.obtaining_info["locations"]]
        self.assertIn("Ciudad Trigal (Casa de Bill)", eevee_areas)
        self.assertIn("Ciudad Azulona (Rincón de Premios)", eevee_areas)
        eevee_casino = next(l for l in eevee_hg.obtaining_info["locations"] if l["area"] == "Ciudad Azulona (Rincón de Premios)")
        self.assertIn("6.666", eevee_casino["method"])

        # Casino en Crystal (Wobbuffet 1.500 fichas y Cubone 800 fichas)
        crys_cat = get_compiled_catalog("crystal", force_reload=True, is_national=False)
        wobb = next(e for e in crys_cat if e.pokemon.national_number == 202)
        wobb_casino = next(l for l in wobb.obtaining_info["locations"] if "casino" in l["area"].lower())
        self.assertIn("1.500", wobb_casino["method"])
        cubone = next(e for e in crys_cat if e.pokemon.national_number == 104)
        cubone_casino = next(l for l in cubone.obtaining_info["locations"] if "casino" in l["area"].lower())
        self.assertIn("800", cubone_casino["method"])

        # Casino en FireRed y LeafGreen (Precios exactos de fichas)
        fr_cat = get_compiled_catalog("firered", force_reload=True, is_national=False)
        clefairy_fr = next(e for e in fr_cat if e.pokemon.national_number == 35)
        self.assertIn("500", next(l["method"] for l in clefairy_fr.obtaining_info["locations"] if "casino" in l["area"].lower()))
        dratini_fr = next(e for e in fr_cat if e.pokemon.national_number == 147)
        self.assertIn("2.800", next(l["method"] for l in dratini_fr.obtaining_info["locations"] if "casino" in l["area"].lower()))

        lg_cat = get_compiled_catalog("leafgreen", force_reload=True, is_national=False)
        clefairy_lg = next(e for e in lg_cat if e.pokemon.national_number == 35)
        self.assertIn("750", next(l["method"] for l in clefairy_lg.obtaining_info["locations"] if "casino" in l["area"].lower()))
        dratini_lg = next(e for e in lg_cat if e.pokemon.national_number == 147)
        self.assertIn("4.600", next(l["method"] for l in dratini_lg.obtaining_info["locations"] if "casino" in l["area"].lower()))

    def test_dratini_and_separated_surf_fishing(self):
        """Verifica que Surf y Pesca están separados en tarjetas independientes y que Dratini mencione a Dbora."""
        from tracker.catalog_service import get_compiled_catalog

        # 1. HeartGold: Dratini
        hg_cat = get_compiled_catalog("heartgold", force_reload=True, is_national=False)
        dratini = next(e for e in hg_cat if e.pokemon.national_number == 147)
        locs = dratini.obtaining_info["locations"]

        den_surf = [l for l in locs if l["area"] == "Guarida Dragón" and l["method"] == "Surf"]
        self.assertEqual(len(den_surf), 1)

        den_fish = [l for l in locs if l["area"] == "Guarida Dragón" and "Pesca" in l["method"]]
        self.assertEqual(len(den_fish), 1)
        self.assertIn("Caña Buena y Supercaña", den_fish[0]["method"])

        temple_gift = next(l for l in locs if "Templo" in l["area"])
        self.assertIn("Débora", temple_gift["method"])
        self.assertIn("Velocidad Extrema", temple_gift["method"])

        # Filtros intactos
        self.assertIn("surf", dratini.filter_tags)
        self.assertIn("rod_good", dratini.filter_tags)
        self.assertIn("rod_super", dratini.filter_tags)

        # Huevos de regalo de Cástor en Ciudad Malva (Mareep, Wooper, Slugma)
        for num in [179, 194, 218]:
            pkmn = next(e for e in hg_cat if e.pokemon.national_number == num)
            malva_loc = next(l for l in pkmn.obtaining_info["locations"] if "Malva" in l["area"])
            self.assertIn("Cástor", malva_loc["method"])
            self.assertNotIn("Primo", malva_loc["method"])
            self.assertIn("Cástor", pkmn.obtaining_info["summary"])

        # 2. Invariante: Ningún Pokémon en HeartGold ni Crystal combina Surf y Pesca en una sola lnea
        for cat_slug in ["heartgold", "crystal"]:
            cat = get_compiled_catalog(cat_slug, force_reload=True, is_national=False)
            for entry in cat:
                for l in entry.obtaining_info.get("locations", []):
                    m_lower = l.get("method", "").lower()
                    if "regalo" in m_lower:
                        continue
                    has_surf = ("surf" in m_lower or "surfeando" in m_lower or "navegando" in m_lower)
                    has_fish = ("pesca" in m_lower or "pescando" in m_lower)
                    self.assertFalse(
                        has_surf and has_fish,
                        f"Encontrada combinación Surf+Pesca en {cat_slug} Pokmon #{entry.pokemon.national_number} {entry.pokemon.display_name}: {l}"
                    )

class PokemonSoulSilverGen4Tests(TestCase):
    """Pruebas unitarias para Pokémon Plata SoulSilver (Gen 4), catálogos, exclusividades, formas y mecánicas."""

    def setUp(self):
        self.game, _ = Game.objects.get_or_create(
            slug="soulsilver",
            defaults={"name": "Pokémon Plata SoulSilver", "generation": 4}
        )
        self.pk_johto, _ = Pokedex.objects.get_or_create(
            game=self.game,
            slug="johto",
            defaults={"name": "Pokédex de Johto", "is_national": False, "pokeapi_name": "updated-johto"}
        )
        self.pk_nat, _ = Pokedex.objects.get_or_create(
            game=self.game,
            slug="national",
            defaults={"name": "Pokédex Nacional", "is_national": True, "pokeapi_name": "national"}
        )

    def test_soulsilver_catalogs_exist_and_counts(self):
        from tracker.catalog_service import get_compiled_catalog, CATALOGS_DIR
        reg_file = CATALOGS_DIR / "soulsilver.json"
        nat_file = CATALOGS_DIR / "soulsilver_national.json"
        self.assertTrue(reg_file.exists(), "soulsilver.json debe existir")
        self.assertTrue(nat_file.exists(), "soulsilver_national.json debe existir")

        reg_cat = get_compiled_catalog("soulsilver", is_national=False, force_reload=True)
        nat_cat = get_compiled_catalog("soulsilver", is_national=True, force_reload=True)
        self.assertEqual(len(reg_cat), 256, "La Pokédex Regional de Johto en SoulSilver debe tener 256 entradas")
        self.assertEqual(len(nat_cat), 493, "La Pokédex Nacional en SoulSilver debe tener 493 entradas")

    def test_soulsilver_legendaries_and_symmetry(self):
        from tracker.catalog_service import get_compiled_catalog
        reg_cat = get_compiled_catalog("soulsilver", is_national=False)

        # Lugia (#249) es el legendario mascota en Islas Remolino
        lugia = [e for e in reg_cat if e.pokemon.national_number == 249][0]
        self.assertEqual(lugia.obtaining_info.get("badge_label"), "Mascota Oficial")
        self.assertIn("Islas Remolino", str(lugia.obtaining_info.get("locations", [])))

        # Ho-Oh (#250) es el legendario post-game en Torre Campana
        ho_oh = [e for e in reg_cat if e.pokemon.national_number == 250][0]
        self.assertEqual(ho_oh.obtaining_info.get("badge_label"), "Legendario Post-Game")
        self.assertIn("Torre Campana", str(ho_oh.obtaining_info.get("locations", [])))

    def test_soulsilver_version_exclusives_and_fossils(self):
        from tracker.catalog_service import get_compiled_catalog
        nat_cat = get_compiled_catalog("soulsilver", is_national=True)
        
        # Sandshrew (#027) disponible en SoulSilver (casino)
        sandshrew = [e for e in nat_cat if e.pokemon.national_number == 27][0]
        self.assertIn("Casino", str(sandshrew.obtaining_info.get("locations", [])))
        
        # Fósil Domo/Raíz (Golpe Roca en Ruinas Alfa -> modal del objeto; Museo de Ciudad Plateada -> restauración)
        kabuto = [e for e in nat_cat if e.pokemon.national_number == 140][0]
        self.assertIn("Ciudad Plateada", str(kabuto.obtaining_info.get("locations", [])))
        self.assertIsNotNone(kabuto.evolution_stone)
        self.assertEqual(kabuto.evolution_stone["slug"], "dome-fossil")
        self.assertIn("Ruinas Alfa", str(kabuto.evolution_stone.get("locations", [])))

    def test_soulsilver_forms_static_and_animated_assets_exist(self):
        from tracker.catalog_service import get_compiled_catalog
        nat_cat = get_compiled_catalog("soulsilver", is_national=True)
        # Validar activos de Arceus
        arceus = [e for e in nat_cat if e.pokemon.national_number == 493][0]
        self.assertTrue(arceus.game_sprite_url.startswith("/media/pokemon/sprites/soulsilver/"))

    def test_soulsilver_ledyba_ruta_36_and_mechanics_parity(self):
        """Valida que Ledyba salga en Ruta 36 con Golpe Cabeza y la paridad de mecánicas de SoulSilver."""
        from tracker.catalog_service import get_compiled_catalog
        reg_cat = get_compiled_catalog("soulsilver", force_reload=True, is_national=False)
        nat_cat = get_compiled_catalog("soulsilver", force_reload=True, is_national=True)

        def get_names_with_tag(cat, tag):
            return {e.pokemon.display_name for e in cat if tag in e.filter_tags.split()}

        # 1. Ledyba (#165) en Ruta 36 con Golpe Cabeza
        ledyba = next(e for e in reg_cat if e.pokemon.national_number == 165)
        self.assertIn("headbutt", ledyba.filter_tags.split())
        r36_locs = [l for l in ledyba.obtaining_info.get("locations", []) if "Ruta 36" in l.get("area", "")]
        self.assertEqual(len(r36_locs), 1, "Ledyba debe tener exactamente una entrada en Ruta 36")
        self.assertIn("Golpe Cabeza", r36_locs[0]["method"])

        # 2. Ledian (#166) en Bosque Verde con Golpe Cabeza
        ledian = next(e for e in reg_cat if e.pokemon.national_number == 166)
        self.assertIn("headbutt", ledian.filter_tags.split())
        bv_locs = [l for l in ledian.obtaining_info.get("locations", []) if "Bosque Verde" in l.get("area", "")]
        self.assertEqual(len(bv_locs), 1, "Ledian debe tener encuentro en Bosque Verde")
        self.assertIn("Golpe Cabeza", bv_locs[0]["method"])

        # 3. Paridad exacta de Golpe Cabeza (15 en Regional, 24 en Nacional)
        reg_hb = get_names_with_tag(reg_cat, "headbutt")
        nat_hb = get_names_with_tag(nat_cat, "headbutt")
        self.assertEqual(len(reg_hb), 15)
        self.assertEqual(len(nat_hb), 24)
        self.assertIn("Ledyba", reg_hb)
        self.assertIn("Ledian", reg_hb)

        # 4. Paridad de Manadas (8 en Regional, 20 en Nacional con Mawile y Gulpin)
        reg_sw = get_names_with_tag(reg_cat, "swarm")
        nat_sw = get_names_with_tag(nat_cat, "swarm")
        self.assertEqual(len(reg_sw), 8)
        self.assertEqual(len(nat_sw), 20)
        self.assertIn("Mawile", nat_sw)
        self.assertIn("Gulpin", nat_sw)

        # 5. Paridad de Pokéwalker (77 en Regional, 118 en Nacional)
        reg_pw = get_names_with_tag(reg_cat, "pokewalker")
        nat_pw = get_names_with_tag(nat_cat, "pokewalker")
        self.assertEqual(len(reg_pw), 77)
        self.assertEqual(len(nat_pw), 118)

        # 6. Verificación de Vulpix (#37) con Ruta 48 y Persian (#53) con encuentros salvajes
        vulpix = next(e for e in reg_cat if e.pokemon.national_number == 37)
        vulpix_areas = {l["area"] for l in vulpix.obtaining_info.get("locations", [])}
        self.assertIn("Ruta 48", vulpix_areas)

        persian = next(e for e in reg_cat if e.pokemon.national_number == 53)
        persian_areas = {l["area"] for l in persian.obtaining_info.get("locations", [])}
        self.assertIn("Ruta 7", persian_areas)
        self.assertIn("Cueva Celeste (P1)", persian_areas)
        self.assertEqual(persian.obtaining_info.get("badge_label"), "Salvaje / Evolución")

        # 7. Verificación de Teddiursa (#216) y Ursaring (#217)
        teddiursa = next(e for e in reg_cat if e.pokemon.national_number == 216)
        teddiursa_areas = {l["area"] for l in teddiursa.obtaining_info.get("locations", [])}
        self.assertTrue(any("Monte Plateado" in a for a in teddiursa_areas))

        ursaring = next(e for e in reg_cat if e.pokemon.national_number == 217)
        self.assertEqual(len(ursaring.obtaining_info.get("locations", [])), 12)

    def test_soulsilver_transfers(self):
        """Valida que Pokémon Plata SoulSilver tenga las 42 transferencias canónicas en su Pokédex Nacional."""
        from tracker.exclusives import VERSION_TRANSFERS_CATALOG, VERSION_TRANSFERS_META, get_version_transfers_context

        transfers_ss = VERSION_TRANSFERS_CATALOG.get("soulsilver", [])
        self.assertEqual(len(transfers_ss), 42)
        self.assertIn(387, transfers_ss)  # Turtwig
        self.assertIn(408, transfers_ss)  # Cranidos
        self.assertIn(410, transfers_ss)  # Shieldon
        self.assertIn(425, transfers_ss)  # Drifloon
        self.assertIn(431, transfers_ss)  # Glameow
        self.assertIn(434, transfers_ss)  # Stunky
        self.assertIn(470, transfers_ss)  # Leafeon
        self.assertIn(479, transfers_ss)  # Rotom
        self.assertIn(493, transfers_ss)  # Arceus

        meta = VERSION_TRANSFERS_META.get("soulsilver", {})
        self.assertIn("Parque Compi", meta.get("mechanic_title", ""))
        self.assertIn("Pokémon Plata SoulSilver", meta.get("description", ""))
        self.assertEqual(len(meta.get("origins", {})), 42)

        # 1. En Pokédex Regional de Johto NO debe haber modal de transferencias
        ctx_reg = get_version_transfers_context(self.game, self.pk_johto, caught_entry_ids=set())
        self.assertIsNone(ctx_reg, "En la Pokédex Regional de Johto no deben mostrarse transferencias de la Nacional")

        # 2. En Pokédex Nacional SÍ debe existir el modal de transferencias
        ctx_nat = get_version_transfers_context(self.game, self.pk_nat, caught_entry_ids=set())
        self.assertIsNotNone(ctx_nat, "El contexto de transferencias debe existir en SoulSilver Nacional")
        self.assertTrue(ctx_nat["has_transfers"])
        self.assertEqual(ctx_nat["total"], 42)
        self.assertEqual(ctx_nat["caught"], 0)
        self.assertEqual(len(ctx_nat["transfer_list"]), 42)


class PokemonBlackGen5Tests(TestCase):
    """Pruebas unitarias para Pokémon Negro (Gen 5 — Teselia), catálogos, Victini #000, exclusividades y mecánicas."""

    def setUp(self):
        self.game, _ = Game.objects.get_or_create(
            slug="black",
            defaults={"name": "Pokémon Negro", "generation": 5}
        )
        self.pk_unova, _ = Pokedex.objects.get_or_create(
            game=self.game,
            slug="unova",
            defaults={"name": "Pokédex Regional de Teselia", "is_national": False, "pokeapi_name": "original-unova"}
        )
        self.pk_nat, _ = Pokedex.objects.get_or_create(
            game=self.game,
            slug="national",
            defaults={"name": "Pokédex Nacional", "is_national": True, "pokeapi_name": "national"}
        )
        self.client = Client()

    def test_black_catalogs_exist_and_counts(self):
        """Valida conteos canónicos: 156 en Regional de Teselia y 649 en Nacional."""
        from tracker.catalog_service import get_compiled_catalog, CATALOGS_DIR
        reg_file = CATALOGS_DIR / "black.json"
        nat_file = CATALOGS_DIR / "black_national.json"
        self.assertTrue(reg_file.exists(), "black.json debe existir")
        self.assertTrue(nat_file.exists(), "black_national.json debe existir")

        reg_cat = get_compiled_catalog("black", is_national=False, force_reload=True)
        nat_cat = get_compiled_catalog("black", is_national=True, force_reload=True)
        self.assertEqual(len(reg_cat), 156, "La Pokédex Regional de Teselia en Negro debe tener 156 entradas")
        self.assertEqual(len(nat_cat), 649, "La Pokédex Nacional en Negro debe tener 649 entradas")

    def test_victini_alternative_a_integrity_and_catch(self):
        """Valida que Victini sea #000 visual pero con id/entry_number > 0 en base de datos y toggle_catch."""
        from tracker.catalog_service import get_compiled_catalog
        reg_cat = get_compiled_catalog("black", is_national=False, force_reload=True)

        victini = reg_cat[0]
        self.assertEqual(victini.display_number, "000")
        self.assertEqual(victini.entry_number, 494)
        self.assertEqual(victini.id, 8000)
        self.assertEqual(victini.pokemon.national_number, 494)
        self.assertEqual(victini.pokemon.display_name, "Victini")

        # Verificar Snivy en posición 1 y Genesect en 155
        snivy = reg_cat[1]
        self.assertEqual(snivy.display_number, "001")
        self.assertEqual(snivy.entry_number, 1)
        self.assertEqual(snivy.id, 8001)

        genesect = reg_cat[155]
        self.assertEqual(genesect.display_number, "155")
        self.assertEqual(genesect.entry_number, 155)
        self.assertEqual(genesect.id, 8155)

        # Probar captura de Victini vía endpoint toggle_catch
        toggle_url = reverse("tracker:toggle_catch")
        payload = {"entry_id": 8000}
        res = self.client.post(toggle_url, data=payload, content_type="application/json")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data.get("success"))
        self.assertTrue(data.get("is_caught"))
        self.assertEqual(data.get("entry_id"), 8000)

        # Verificar liberación
        res2 = self.client.post(toggle_url, data=payload, content_type="application/json")
        self.assertEqual(res2.status_code, 200)
        data2 = res2.json()
        self.assertTrue(data2.get("success"))
        self.assertFalse(data2.get("is_caught"))

    def test_pure_spanish_toponymy_and_linguistic_purity(self):
        """Verifica toponimia 100% en español oficial de España y el método 'Sombra en el agua' (sin remolinos en métodos)."""
        from tracker.catalog_service import get_compiled_catalog
        reg_cat = get_compiled_catalog("black", is_national=False)
        nat_cat = get_compiled_catalog("black", is_national=True)

        forbidden_english = [
            "pinwheel forest", "chargestone cave", "relic castle", "giant chasm",
            "rustling grass", "dust cloud", "rippling water", "npc trade",
            "dragonspiral", "mistralton", "driftveil", "accumula", "nuvema"
        ]

        for cat in [reg_cat, nat_cat]:
            for entry in cat:
                for loc in entry.obtaining_info.get("locations", []):
                    area = loc.get("area", "").lower()
                    method = loc.get("method", "").lower()
                    for term in forbidden_english:
                        self.assertNotIn(term, area, f"Anglicismo encontrado en área de #{entry.pokemon.national_number}: {area}")
                        self.assertNotIn(term, method, f"Anglicismo encontrado en método de #{entry.pokemon.national_number}: {method}")

                    # Verificar pureza lingüística: no usar 'remolino' en métodos de encuentro
                    self.assertNotIn("remolino", method, f"Método con 'remolino' detectado en #{entry.pokemon.national_number}: {method}")

    def test_absence_of_prior_generations_and_b2w2_mechanics(self):
        """Garantiza la ausencia total de mecánicas previas (Caña Vieja/Buena, Safari, etc.) y de secuelas B2W2."""
        from tracker.catalog_service import get_compiled_catalog
        reg_cat = get_compiled_catalog("black", is_national=False)
        nat_cat = get_compiled_catalog("black", is_national=True)

        forbidden_mechanics = [
            "safari", "pokewalker", "honey", "pokeradar", "dual_slot", "headbutt", "rock_smash"
        ]

        for cat in [reg_cat, nat_cat]:
            for entry in cat:
                tags = entry.filter_tags.split()
                for fm in forbidden_mechanics:
                    self.assertNotIn(fm, tags, f"Mecánica prohibida {fm} encontrada en #{entry.pokemon.national_number}")

                # Tampoco caña vieja o caña buena
                self.assertNotIn("rod_old", tags, f"Caña vieja encontrada en #{entry.pokemon.national_number}")
                self.assertNotIn("rod_good", tags, f"Caña buena encontrada en #{entry.pokemon.national_number}")

                # Verificar ausencia de rutas de B2W2 (Ruta 19 a 23)
                for loc in entry.obtaining_info.get("locations", []):
                    area = loc.get("area", "")
                    for r_num in range(19, 24):
                        self.assertNotIn(f"Ruta {r_num}", area, f"Ruta {r_num} de B2W2 encontrada en #{entry.pokemon.national_number}")

    def test_gen5_forms_and_rotom_types(self):
        """Verifica que las formas alternas de Gen 5 existan y Rotom adopte sus tipos elementales secundarios."""
        from tracker.pokemon_forms import get_pokemon_forms

        # Rotom en 5.ª Gen adopta tipo elemental secundario
        rotom_forms = get_pokemon_forms(479, "black")
        self.assertEqual(len(rotom_forms), 6)
        heat = next(f for f in rotom_forms if f["form_key"] == "heat")
        self.assertEqual(heat["secondary_type"], "fire")
        wash = next(f for f in rotom_forms if f["form_key"] == "wash")
        self.assertEqual(wash["secondary_type"], "water")
        frost = next(f for f in rotom_forms if f["form_key"] == "frost")
        self.assertEqual(frost["secondary_type"], "ice")
        fan = next(f for f in rotom_forms if f["form_key"] == "fan")
        self.assertEqual(fan["secondary_type"], "flying")
        mow = next(f for f in rotom_forms if f["form_key"] == "mow")
        self.assertEqual(mow["secondary_type"], "grass")

        # Basculin (Roja y Azul)
        basculin = get_pokemon_forms(550, "black")
        self.assertEqual(len(basculin), 2)

        # Darmanitan (Standard y Modo Daruma)
        darmanitan = get_pokemon_forms(555, "black")
        self.assertEqual(len(darmanitan), 2)
        daruma = next(f for f in darmanitan if f["form_key"] == "zen")
        self.assertEqual(daruma["secondary_type"], "psychic")

        # Deerling & Sawsbuck (4 formas estacionales)
        self.assertEqual(len(get_pokemon_forms(585, "black")), 4)
        self.assertEqual(len(get_pokemon_forms(586, "black")), 4)

        # Meloetta (Lírica y Danza Normal/Lucha)
        meloetta = get_pokemon_forms(648, "black")
        self.assertEqual(len(meloetta), 2)
        pirouette = next(f for f in meloetta if f["form_key"] == "pirouette")
        self.assertEqual(pirouette["secondary_type"], "fighting")

        # Genesect (5 cartuchos)
        self.assertEqual(len(get_pokemon_forms(649, "black")), 5)

    def test_black_all_forms_animated_gifs_and_unova_locations(self):
        """Valida que TODAS las formas en Pokémon Negro usen GIFs animados reales en disco (frente/espalda, normal/shiny) y ubicaciones adaptadas a Teselia."""
        from django.conf import settings
        from pathlib import Path
        from PIL import Image
        from tracker.pokemon_forms import get_pokemon_forms

        media_root = Path(settings.MEDIA_ROOT)
        form_species = [201, 351, 386, 412, 413, 421, 422, 423, 479, 487, 492, 493, 550, 555, 585, 586, 648, 649]
        forbidden_regions = ("Sinnoh", "Hoenn", "Johto", "Kanto", "Árboles de Miel", "Monte Corona", "Pokéwalker")

        checked_gif_paths = set()
        for game_slug in ("black", "black_national"):
            for nid in form_species:
                forms = get_pokemon_forms(nid, game_slug)
                self.assertGreater(len(forms), 1, f"#{nid} debe tener múltiples formas en {game_slug}")
                for form in forms:
                    key = form["form_key"]
                    for static_field in ("sprite_retro", "sprite_retro_back"):
                        url = form.get(static_field, "")
                        self.assertIn("/sprites/black/", url, f"#{nid} {key} ({static_field}) no apunta a black/: {url}")
                    for shiny_static_field in ("sprite_retro_shiny", "sprite_retro_shiny_back"):
                        url = form.get(shiny_static_field, "")
                        self.assertIn("/sprites/black_shiny/", url, f"#{nid} {key} ({shiny_static_field}) no apunta a black_shiny/: {url}")

                    for anim_field in (
                        "modal_retro_sprite_url",
                        "modal_retro_sprite_shiny_url",
                        "modal_retro_sprite_back_url",
                        "modal_retro_sprite_shiny_back_url",
                    ):
                        anim_url = form.get(anim_field, "")
                        self.assertTrue(
                            anim_url.endswith(".gif"),
                            f"#{nid} {key} ({anim_field}) debe ser .gif en {game_slug}: {anim_url}",
                        )
                        self.assertIn("/sprites/black_animated", anim_url)
                        rel_path = anim_url.removeprefix("/media/")
                        if rel_path not in checked_gif_paths:
                            disk_path = media_root / rel_path
                            self.assertTrue(disk_path.exists() and disk_path.stat().st_size > 0, f"Falta GIF en disco: {disk_path}")
                            with Image.open(disk_path) as img:
                                self.assertGreater(getattr(img, "n_frames", 1), 1, f"El GIF debe ser animado (>1 frame): {disk_path}")
                            checked_gif_paths.add(rel_path)

                    if game_slug == "black" and nid in (412, 422, 423):
                        text_blob = f"{form.get('summary', '')} {form.get('locations', '')} {form.get('note', '')}"
                        self.assertIn("Pokétransfer", text_blob, f"#{nid} {key} debe referenciar Pokétransfer")
                        for forbidden in forbidden_regions:
                            self.assertNotIn(forbidden, text_blob, f"#{nid} {key} contiene referencia desactualizada '{forbidden}'")

    def test_media_assets_exist_on_disk(self):
        """Valida que los recursos estáticos, animados, iconos y gritos existan en disco sin archivos de 0 bytes."""
        from django.conf import settings
        from pathlib import Path
        media_root = Path(settings.MEDIA_ROOT)

        # Muestreo representativo de Gen 5: Victini (494), Snivy (495), Reshiram (643), Genesect (649)
        test_ids = [1, 25, 150, 249, 384, 493, 494, 495, 550, 555, 641, 643, 644, 648, 649]
        for nid in test_ids:
            # Sprite estático frente
            sp_png = media_root / "pokemon" / "sprites" / "black" / f"{nid}.png"
            self.assertTrue(sp_png.exists() and sp_png.stat().st_size > 0, f"Falta {sp_png}")

            # Sprite animado frente (.gif)
            sp_gif = media_root / "pokemon" / "sprites" / "black_animated" / f"{nid}.gif"
            self.assertTrue(sp_gif.exists() and sp_gif.stat().st_size > 0, f"Falta {sp_gif}")

            # Sprite animado espalda (.gif)
            sp_back_gif = media_root / "pokemon" / "sprites" / "black_animated" / "back" / f"{nid}.gif"
            self.assertTrue(sp_back_gif.exists() and sp_back_gif.stat().st_size > 0, f"Falta {sp_back_gif}")

            # Icono gen5
            icon = media_root / "pokemon" / "icons" / "gen5" / f"{nid}.png"
            self.assertTrue(icon.exists() and icon.stat().st_size > 0, f"Falta {icon}")

            # Grito
            cry = media_root / "pokemon" / "cries" / "legacy" / f"{nid}.ogg"
            self.assertTrue(cry.exists() and cry.stat().st_size > 0, f"Falta {cry}")

    def test_views_black_integration(self):
        """Valida que las vistas web de Pokémon Negro (Regional, Nacional, Game Hub y Modales) respondan 200 OK."""
        # 1. Pokédex Regional por defecto
        res_reg = self.client.get("/black/")
        self.assertEqual(res_reg.status_code, 200)
        self.assertEqual(res_reg.context["game"].slug, "black")
        self.assertEqual(len(res_reg.context["entries"]), 156)
        content_reg = res_reg.content.decode("utf-8")
        self.assertIn("#000", content_reg)
        self.assertIn("Victini", content_reg)

        # 2. Pokédex Nacional
        res_nat = self.client.get("/black/national/")
        self.assertEqual(res_nat.status_code, 200)
        self.assertEqual(res_nat.context["total_pokemon"], 649)
        res_nat_all = self.client.get("/black/national/?gen=all")
        self.assertEqual(res_nat_all.status_code, 200)
        self.assertEqual(len(res_nat_all.context["entries"]), 649)

        # 3. Game Selector (Hub)
        res_hub = self.client.get("/games/")
        self.assertEqual(res_hub.status_code, 200)
        content_hub = res_hub.content.decode("utf-8")
        self.assertIn("Pokémon Negro", content_hub)
        self.assertIn("Reshiram", content_hub)

        # 4. Modales AJAX
        res_modal_victini = self.client.get("/api/catalog/entry/8000/modal/")
        self.assertEqual(res_modal_victini.status_code, 200)
        v_data = res_modal_victini.json()
        self.assertEqual(v_data["number"], "000")
        self.assertEqual(v_data["name"], "Victini")
        self.assertEqual(v_data["id"], 8000)

        res_modal_snivy = self.client.get("/api/catalog/entry/8001/modal/")
        self.assertEqual(res_modal_snivy.status_code, 200)
        s_data = res_modal_snivy.json()
        self.assertEqual(s_data["number"], "001")
        self.assertEqual(s_data["name"], "Snivy")
        self.assertEqual(s_data["id"], 8001)

    def test_black_version_exclusives_and_white_forest_notice(self):
        """Valida que los exclusivos de Negro y Blanco excluyan a Cottonee/Petilil (por intercambio NPC en Ciudad Esmalte) y tengan la nota del Bosque Blanco."""
        from tracker.exclusives import VERSION_EXCLUSIVES_CATALOG, get_version_exclusives_context
        from tracker.models import Game, Pokedex

        black_excl = VERSION_EXCLUSIVES_CATALOG.get("black", [])
        white_excl = VERSION_EXCLUSIVES_CATALOG.get("white", [])

        # Validar exclusión de la familia Cottonee/Whimsicott y Petilil/Lilligant, #399/#400 (Bidoof/Bibarel) y #313/#314 (Volbeat/Illumise en Gen 5)
        self.assertNotIn(546, black_excl)  # Cottonee
        self.assertNotIn(547, black_excl)  # Whimsicott
        self.assertNotIn(548, white_excl)  # Petilil
        self.assertNotIn(549, white_excl)  # Lilligant
        self.assertNotIn(399, white_excl)  # Bidoof (Bibarel salvaje en Puente Villa en Negro)
        self.assertNotIn(400, white_excl)  # Bibarel
        self.assertNotIn(313, black_excl)  # Volbeat (Illumise cría Volbeat en Blanco)
        self.assertNotIn(314, white_excl)  # Illumise (Volbeat + Ditto cría Illumise en Negro)

        # Validar totales
        self.assertEqual(len(black_excl), 17)
        self.assertEqual(len(white_excl), 117)

        # Validar contexto y aviso
        game = Game.objects.get(slug="black")
        pokedex = game.pokedexes.get(slug="unova")
        ctx = get_version_exclusives_context(game, pokedex, set())
        self.assertIsNotNone(ctx)
        self.assertEqual(ctx["counterpart_theme"], "white")
        self.assertEqual(ctx["counterpart_total"], 117)
        self.assertEqual(ctx["own_total"], 17)
        self.assertIn("Bosque Blanco", ctx["notice"])
        self.assertIn("Cottonee y Petilil", ctx["notice"])
        self.assertIn("Ciudad Esmalte", ctx["notice"])

    def test_black_unown_modal_and_forms(self):
        """Valida que en Pokémon Negro el Bloc Unown y las formas de Unown reflejen Teselia (Pokétransfer), animaciones GIF y forma canónica F."""
        from tracker.catalog_service import get_compiled_catalog, clear_catalog_memory_cache
        from tracker.pokemon_forms import get_pokemon_forms
        from tracker.unown_data import get_unown_catalog
        import json
        from pathlib import Path

        # 1. Vista nacional y modal Unown
        res = self.client.get("/black/national/")
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.context.get("is_unova"))
        self.assertEqual(res.context["unown_total_forms"], 28)

        content = res.content.decode("utf-8")
        self.assertIn("Teselia (Pokétransfer)", content)
        self.assertIn('id="unown-unova-hint"', content)
        self.assertNotIn('id="unown-hoenn-hint"', content)
        self.assertNotIn("Hoenn (Transferencia)", content)
        self.assertIn('id="unown-modal-title"', content)
        self.assertIn("text-white", content)

        # 2. Sprite físico canónico 201.png y 201.gif corresponde a la forma F
        f_png = Path("media/pokemon/sprites/black/unown/f.png").read_bytes()
        main_png = Path("media/pokemon/sprites/black/201.png").read_bytes()
        self.assertEqual(f_png, main_png)

        f_gif = Path("media/pokemon/sprites/black_animated/unown/f.gif").read_bytes()
        main_gif = Path("media/pokemon/sprites/black_animated/201.gif").read_bytes()
        self.assertEqual(f_gif, main_gif)

        # 3. get_unown_catalog retorna 28 formas con sprites estáticos en el bloc y hint de Teselia
        catalog = get_unown_catalog("black")
        self.assertEqual(len(catalog), 28)
        self.assertEqual(catalog[0]["letter"], "a")
        self.assertEqual(catalog[0]["sprite_normal"], "/media/pokemon/sprites/black/unown/a.png")
        self.assertEqual(catalog[0]["sprite_shiny"], "/media/pokemon/sprites/black_shiny/unown/a.png")
        self.assertIn("Laboratorio de Pokétransfer", catalog[0]["secret_hint"])

        # 4. get_pokemon_forms retorna 28 formas con sprite_retro estático (para la tarjeta de Pokédex general) y modal animado
        forms = get_pokemon_forms(201, "black")
        self.assertEqual(len(forms), 28)
        self.assertEqual(forms[0]["form_key"], "a")
        self.assertEqual(forms[5]["form_key"], "f")
        self.assertEqual(forms[-1]["form_key"], "question")

        for f in forms:
            self.assertEqual(f["badge_label"], "Pokétransfer")
            self.assertEqual(f["badge_color"], "slate")
            self.assertEqual(f["type"], "transfer")
            self.assertIn("Laboratorio de Pokétransfer (Ruta 15)", f["locations"][0]["area"])
            # El sprite_retro debe ser estático para la tarjeta general
            self.assertEqual(f["sprite_retro"], f"/media/pokemon/sprites/black/unown/{f['form_key']}.png")
            # El modal_retro_sprite_url debe ser animado únicamente para la tarjeta individual modal
            self.assertEqual(f["modal_retro_sprite_url"], f"/media/pokemon/sprites/black_animated/unown/{f['form_key']}.gif")
            self.assertEqual(f["modal_retro_sprite_shiny_url"], f"/media/pokemon/sprites/black_animated_shiny/unown/{f['form_key']}.gif")
            self.assertEqual(f["modal_retro_sprite_back_url"], f"/media/pokemon/sprites/black_animated/back/unown/{f['form_key']}.gif")

        # Verificar forma 'v' específicamente (mencionada por el usuario)
        v_form = next(f for f in forms if f["form_key"] == "v")
        self.assertEqual(v_form["sprite_retro"], "/media/pokemon/sprites/black/unown/v.png")
        self.assertEqual(v_form["modal_retro_sprite_url"], "/media/pokemon/sprites/black_animated/unown/v.gif")

        # 5. CatalogEntry serializado en modal_data_json
        clear_catalog_memory_cache()
        nat_cat = get_compiled_catalog("black", is_national=True)
        unown_entry = next(e for e in nat_cat if e.pokemon.national_number == 201)
        m_data = json.loads(unown_entry.modal_data_json)
        self.assertEqual(len(m_data["forms"]), 28)
        self.assertEqual(m_data["forms"][0]["form_key"], "a")
        self.assertEqual(m_data["forms"][5]["form_key"], "f")


class GlobalFormContractInvariantsTests(TestCase):
    """
    Contrato global multi-juego para prevenir regresiones al añadir futuras ediciones:
    - Todo catálogo compilado debe estar registrado en GAME_SPRITE_CONFIG (sin fallbacks silenciosos).
    - Todas las URLs retro y animadas deben aislarse por juego, respetar su extensión por generación
      y existir físicamente en MEDIA_ROOT con >1 fotograma animado (salvo la única excepción canónica de Cherrim Soleada en Gen 4).
    - Ninguna forma heredada puede conservar referencias toponímicas de generaciones previas fuera de su transferencia.
    """

    def test_compiled_catalogs_registered_and_unregistered_fails_loudly(self):
        from tracker.catalog_service import CATALOGS_DIR
        from tracker.pokemon_forms import GAME_SPRITE_CONFIG, get_game_sprite_config, get_pokemon_forms

        catalog_slugs = {
            p.stem.removesuffix("_national")
            for p in CATALOGS_DIR.glob("*.json")
        }
        self.assertTrue(catalog_slugs, "Debe haber al menos un catálogo compilado")
        for slug in sorted(catalog_slugs):
            self.assertIn(slug, GAME_SPRITE_CONFIG, f"Catálogo '{slug}' falta en GAME_SPRITE_CONFIG")

        with self.assertRaises(ValueError):
            get_game_sprite_config("unregistered-future-game")
        with self.assertRaises(ValueError):
            get_pokemon_forms(351, "unregistered-future-game")

    def test_all_active_games_forms_assets_isolation_and_locations(self):
        from pathlib import Path
        from django.conf import settings
        from PIL import Image
        from tracker.catalog_service import CATALOGS_DIR
        from tracker.pokemon_forms import GAME_SPRITE_CONFIG, get_pokemon_forms

        media_root = Path(settings.MEDIA_ROOT)
        form_species = [172, 201, 351, 386, 412, 413, 421, 422, 423, 479, 487, 492, 493, 550, 555, 585, 586, 641, 642, 645, 646, 647, 648, 649]
        forbidden_gen5_terms = ("Sinnoh", "Hoenn", "Johto", "Kanto", "Árboles de Miel", "Monte Corona", "Pokéwalker")
        checked_images = {}

        for slug, cfg in GAME_SPRITE_CONFIG.items():
            slug_variants = [slug]
            if (CATALOGS_DIR / f"{slug}_national.json").exists():
                slug_variants.append(f"{slug}_national")

            anim_dir = cfg["anim_dir"]
            anim_ext = cfg["anim_ext"]
            expected_dirs = {cfg["static_dir"], f"{cfg['static_dir']}_shiny"}
            if anim_dir:
                expected_dirs.update({anim_dir, f"{anim_dir}_shiny"})

            for query_slug in slug_variants:
                for nid in form_species:
                    forms = get_pokemon_forms(nid, query_slug)
                    for form in forms:
                        key = form["form_key"]
                        # Excepciones compartidas explícitas de sprites estáticos/dorsales Gen 3-4
                        allowed_dirs = set(expected_dirs)
                        if nid == 201 and cfg["gen"] == 3 and slug != "ruby":
                            allowed_dirs.update({"ruby", "ruby_shiny"})
                        elif nid == 201 and slug == "platinum":
                            allowed_dirs.update({"diamond", "diamond_shiny"})
                        elif nid == 351 and slug in ("firered", "leafgreen") and key != "normal":
                            allowed_dirs.update({"ruby", "ruby_shiny"})
                        elif nid == 421 and slug in ("heartgold", "soulsilver") and key == "sunshine":
                            allowed_dirs.update({"platinum", "platinum_shiny"})

                        if anim_dir:
                            for front_field in ("modal_retro_sprite_url", "modal_retro_sprite_shiny_url"):
                                front_url = form.get(front_field)
                                self.assertIsNotNone(front_url, f"{query_slug} #{nid} {key} falta {front_field}")
                                self.assertTrue(front_url.endswith(anim_ext), f"{query_slug} #{nid} {key} {front_field} debe terminar en {anim_ext}: {front_url}")

                        if cfg["has_animated_back"]:
                            for back_field in ("modal_retro_sprite_back_url", "modal_retro_sprite_shiny_back_url"):
                                back_url = form.get(back_field)
                                self.assertIsNotNone(back_url, f"{query_slug} #{nid} {key} falta {back_field}")
                                self.assertTrue(back_url.endswith(anim_ext), f"{query_slug} #{nid} {key} {back_field} debe terminar en {anim_ext}: {back_url}")

                        for field in (
                            "sprite_retro",
                            "sprite_retro_shiny",
                            "sprite_retro_back",
                            "sprite_retro_shiny_back",
                            "modal_retro_sprite_url",
                            "modal_retro_sprite_shiny_url",
                            "modal_retro_sprite_back_url",
                            "modal_retro_sprite_shiny_back_url",
                        ):
                            url = form.get(field)
                            if not url:
                                continue
                            sprite_folder = url.removeprefix("/media/pokemon/sprites/").split("/", 1)[0]
                            self.assertIn(
                                sprite_folder,
                                allowed_dirs,
                                f"{query_slug} #{nid} {key} ({field}) apunta fuera de {allowed_dirs}: {url}",
                            )

                            rel_path = url.removeprefix("/media/")
                            if rel_path not in checked_images:
                                disk_path = media_root / rel_path
                                self.assertTrue(
                                    disk_path.exists() and disk_path.stat().st_size > 0,
                                    f"Archivo faltante o vacío para {query_slug} #{nid} {key} ({field}): {disk_path}",
                                )
                                n_frames = 1
                                if field.startswith("modal_retro_sprite") and anim_dir and sprite_folder.startswith(anim_dir):
                                    with Image.open(disk_path) as img:
                                        n_frames = getattr(img, "n_frames", 1)
                                checked_images[rel_path] = n_frames

                            if field.startswith("modal_retro_sprite") and anim_dir and sprite_folder.startswith(anim_dir):
                                is_cherrim_gen4_sunshine = (cfg["gen"] == 4 and nid == 421 and key == "sunshine")
                                if not is_cherrim_gen4_sunshine:
                                    self.assertGreater(
                                        checked_images[rel_path],
                                        1,
                                        f"Sprite animado de 1 solo fotograma no permitido en {query_slug} #{nid} {key} ({field}): {url}",
                                    )

                        if cfg["gen"] == 5 and query_slug == slug:
                            text_blob = f"{form.get('summary', '')} {form.get('locations', '')} {form.get('note', '')}"
                            for forbidden in forbidden_gen5_terms:
                                self.assertNotIn(
                                    forbidden,
                                    text_blob,
                                    f"{query_slug} #{nid} {key} conserva término previo '{forbidden}'",
                                )

    def test_gender_differences_follow_game_sprite_config(self):
        from pathlib import Path
        from unittest.mock import patch
        from django.conf import settings
        from tracker.gender_differences import GENDER_DIFFERENCES_GEN5, get_pokemon_gender_info
        from tracker.pokemon_forms import GAME_SPRITE_CONFIG

        with patch.dict("tracker.catalog_service.GAME_GENERATION_MAP", {"unregistered-gen5-game": 5}):
            with self.assertRaises(ValueError):
                get_pokemon_gender_info(25, "unregistered-gen5-game")

        media_root = Path(settings.MEDIA_ROOT)
        checked_paths = set()
        for slug, cfg in GAME_SPRITE_CONFIG.items():
            if cfg["gen"] < 4:
                self.assertIsNone(get_pokemon_gender_info(25, slug))
                continue
            for query_slug in (slug, f"{slug}_national"):
                for nid in (25, 130, 445, 592):
                    info = get_pokemon_gender_info(nid, query_slug)
                    if cfg["gen"] < 5 and nid == 592:
                        continue
                    self.assertIsNotNone(info)
                    fs = info["female_sprites"]
                    self.assertIsNotNone(fs, f"{query_slug} #{nid} debe tener female_sprites")
                    self.assertTrue(fs["retro_animated"].endswith(cfg["anim_ext"]))
                    if cfg["has_animated_back"]:
                        self.assertTrue(fs["retro_animated_back"].endswith(cfg["anim_ext"]))
                        self.assertTrue(fs["retro_shiny_animated_back"].endswith(cfg["anim_ext"]))
                    for k, url in fs.items():
                        if not url or "home/" in url:
                            continue
                        rel = url.removeprefix("/media/")
                        if rel not in checked_paths:
                            p = media_root / rel
                            self.assertTrue(p.exists() and p.stat().st_size > 0, f"Falta female sprite {query_slug} #{nid} ({k}): {p}")
                            checked_paths.add(rel)

        # Ninguna especie con diferencias reales en Gen 4-5 (salvo #277/#278 excluidos) debe faltar en disco
        for slug in ("diamond", "platinum", "heartgold", "black", "white", "black-2"):
            for nid in GENDER_DIFFERENCES_GEN5:
                if nid in (277, 278):
                    continue
                info = get_pokemon_gender_info(nid, slug)
                fs = (info or {}).get("female_sprites")
                if not fs:
                    continue
                for k, url in fs.items():
                    if not url or "home/" in url:
                        continue
                    rel = url.removeprefix("/media/")
                    if rel not in checked_paths:
                        p = media_root / rel
                        self.assertTrue(p.exists() and p.stat().st_size > 0, f"Falta female sprite {slug} #{nid} ({k}): {p}")
                        checked_paths.add(rel)

    def test_all_catalogs_have_valid_spanish_flavor_texts(self):
        """Verifica que todos los catálogos precompilados tengan flavor_text válido, sin vacíos ni alias sin resolver."""
        from tracker.catalog_service import CATALOGS_DIR, get_compiled_catalog

        catalog_files = sorted(CATALOGS_DIR.glob("*.json"))
        self.assertGreater(len(catalog_files), 0)

        for catalog_file in catalog_files:
            slug = catalog_file.stem
            entries = get_compiled_catalog(slug, force_reload=True)
            self.assertIsNotNone(entries, f"No se pudo cargar el catálogo {slug}")
            for entry in entries:
                ft = (entry.flavor_text or "").strip()
                nid = entry.pokemon.national_number
                self.assertTrue(
                    len(ft) >= 20,
                    f"flavor_text vacío o inválido en {slug} #{nid} ({entry.pokemon.name}): {ft!r}",
                )
                for bad_token in ("{{", "}}", "[[", "]]", "<ref", "NombreHaEs"):
                    self.assertNotIn(
                        bad_token,
                        ft,
                        f"Wikitexto residual '{bad_token}' en {slug} #{nid}: {ft!r}",
                    )

        # Verificación puntual de los casos corregidos en Negro, Perla/Platino, SoulSilver y Zafiro
        for slug in ("black", "black_national"):
            by_nid = {e.pokemon.national_number: e for e in get_compiled_catalog(slug)}
            for nid in (550, 555, 592, 593, 641, 642, 645, 647, 648):
                self.assertIn(nid, by_nid)
                self.assertGreater(len(by_nid[nid].flavor_text.strip()), 20)
            self.assertIn("pezuñas", by_nid[647].flavor_text)
            self.assertIn("melodías", by_nid[648].flavor_text)

        for slug in ("pearl_national", "platinum_national"):
            by_nid = {e.pokemon.national_number: e for e in get_compiled_catalog(slug)}
            for nid in (29, 32, 83):
                self.assertGreater(len(by_nid[nid].flavor_text.strip()), 20)

        ss_nat = {e.pokemon.national_number: e for e in get_compiled_catalog("soulsilver_national")}
        self.assertIn("Hace chocar su cabeza", ss_nat[408].flavor_text)

        for slug in ("sapphire", "sapphire_national"):
            by_nid = {e.pokemon.national_number: e for e in get_compiled_catalog(slug)}
            self.assertIn("dos Beldum, uniendo", by_nid[375].flavor_text)

        # Verificación puntual de textos canónicos GB en Gen 1 (Rojo, Azul, Amarillo)
        for slug in ("red", "blue"):
            by_nid = {e.pokemon.national_number: e for e in get_compiled_catalog(slug)}
            self.assertIn("En luna llena", by_nid[94].flavor_text)
            self.assertIn("Almacena energía eléctrica", by_nid[101].flavor_text)

        yellow_by_nid = {e.pokemon.national_number: e for e in get_compiled_catalog("yellow")}
        self.assertIn("se vuelve irritable", yellow_by_nid[26].flavor_text)
        self.assertIn("Engaña a su presa", yellow_by_nid[71].flavor_text)

    def test_black_evolution_filter_tags_include_pre_and_post_evolutions(self):
        """Verifica que Pokémon Negro (regional y nacional) incluya filtros de intercambio, amistad y piedra en preevolución y evolución."""
        from tracker.catalog_service import get_compiled_catalog, clear_catalog_memory_cache

        clear_catalog_memory_cache()
        reg_entries = get_compiled_catalog("black", force_reload=True, is_national=False)
        by_name_reg = {e.pokemon.name: set(e.filter_tags.split()) for e in reg_entries}

        # Por intercambio (4 pares = 8 en Teselia)
        for name in ("boldore", "gigalith", "gurdurr", "conkeldurr", "karrablast", "escavalier", "shelmet", "accelgor"):
            self.assertIn("trade", by_name_reg[name], f"{name} debe tener etiqueta 'trade' en black")

        # Por amistad (2 pares = 4 en Teselia, incluyendo Leavanny salvaje)
        for name in ("woobat", "swoobat", "swadloon", "leavanny"):
            self.assertIn("friendship", by_name_reg[name], f"{name} debe tener etiqueta 'friendship' en black")

        # Por piedra (9 pares = 18 en Teselia: tanto el que evoluciona como el evolucionado)
        for name in (
            "pansage", "simisage", "pansear", "simisear", "panpour", "simipour",
            "munna", "musharna", "cottonee", "whimsicott", "petilil", "lilligant",
            "minccino", "cinccino", "eelektrik", "eelektross", "lampent", "chandelure",
        ):
            self.assertIn("stone", by_name_reg[name], f"{name} debe tener etiqueta 'stone' en black")

        # Nacional (incluyendo especies Gen 1-4 por Poké Transfer y uso directo de black_national)
        for nat_entries in (
            get_compiled_catalog("black", force_reload=True, is_national=True),
            get_compiled_catalog("black_national", force_reload=True),
        ):
            by_name_nat = {e.pokemon.name: set(e.filter_tags.split()) for e in nat_entries}
            for name in ("haunter", "gengar", "feebas", "milotic"):
                self.assertIn("trade", by_name_nat[name], f"{name} debe tener 'trade' en black_national")
            for name in ("pikachu", "raichu", "eevee", "vaporeon", "roselia", "roserade"):
                self.assertIn("stone", by_name_nat[name], f"{name} debe tener 'stone' en black_national")
            for name in ("pichu", "pikachu", "budew", "roselia", "riolu", "lucario"):
                self.assertIn("friendship", by_name_nat[name], f"{name} debe tener 'friendship' en black_national")

    def test_black_seasonal_and_special_spot_filter_tags(self):
        """Verifica filtros estacionales, notas de variación de tasa, sprites de Deerling/Sawsbuck, encuentros especiales y ausencia de falsos positivos horarios."""
        import json as _json
        from tracker.catalog_service import get_compiled_catalog, clear_catalog_memory_cache

        clear_catalog_memory_cache()
        reg_cat = get_compiled_catalog("black", force_reload=True, is_national=False)
        nat_cat = get_compiled_catalog("black", force_reload=True, is_national=True)

        reg_by_num = {e.pokemon.national_number: e for e in reg_cat}
        nat_by_num = {e.pokemon.national_number: e for e in nat_cat}

        # 1. Estaciones: exclusivos estacionales + formas de Deerling/Sawsbuck + especies con tasa variable
        for s_tag in ("season_spring", "season_summer", "season_autumn"):
            self.assertIn(s_tag, reg_by_num[616].filter_tags.split())  # Shelmet
            self.assertIn(s_tag, reg_by_num[536].filter_tags.split())  # Palpitoad
            self.assertIn(s_tag, nat_by_num[226].filter_tags.split())  # Mantine
            self.assertIn(s_tag, nat_by_num[320].filter_tags.split())  # Wailmer
        self.assertNotIn("season_winter", reg_by_num[616].filter_tags.split())

        for w_num in (582, 583, 613, 614, 619, 531):
            self.assertIn("season_winter", reg_by_num[w_num].filter_tags.split())
        for w_nat in (363, 364, 365):
            self.assertIn("season_winter", nat_by_num[w_nat].filter_tags.split())

        # Wailord tiene tasa fija del 5% las 4 estaciones: no debe aparecer en filtro estacional
        for s_tag in ("season_spring", "season_summer", "season_autumn", "season_winter"):
            self.assertNotIn(s_tag, nat_by_num[321].filter_tags.split())
            self.assertIn(s_tag, reg_by_num[585].filter_tags.split())  # Deerling
            self.assertIn(s_tag, reg_by_num[586].filter_tags.split())  # Sawsbuck

        # Especies con cambio de tasa de aparición deben incluir notas en modal_data_json
        for rate_num in (525, 527, 531, 533, 613, 615):
            self.assertTrue(reg_by_num[rate_num].notes, f"#{rate_num} debe tener nota de tasa estacional")
            modal_payload = _json.loads(reg_by_num[rate_num].modal_data_json)
            self.assertTrue(modal_payload.get("notes"))
        self.assertTrue(_json.loads(nat_by_num[320].modal_data_json).get("notes"))

        # Deerling y Sawsbuck exponen sprites estacionales completos (retro, modern, shiny)
        for seasonal_num in (585, 586):
            sprites = _json.loads(reg_by_num[seasonal_num].season_sprites_json)
            self.assertEqual(set(sprites.keys()), {"spring", "summer", "autumn", "winter"})
            self.assertIn("/summer.png", sprites["summer"]["retro"])
            self.assertTrue(sprites["winter"]["modern"])
            self.assertTrue(sprites["autumn"]["retro_shiny"])
            self.assertTrue(sprites["autumn"]["modern_shiny"])

        # 2. Encuentros especiales de Teselia
        self.assertIn("spot_dust", reg_by_num[529].filter_tags.split())    # Drilbur
        self.assertIn("spot_bridge", reg_by_num[580].filter_tags.split())  # Ducklett
        self.assertIn("spot_surf", reg_by_num[594].filter_tags.split())    # Alomomola
        self.assertIn("spot_fishing", reg_by_num[618].filter_tags.split()) # Stunfisk
        self.assertIn("spot_grass", reg_by_num[531].filter_tags.split())   # Audino

        # 3. Hora del día: sin falsos positivos por Piedra Día / Piedra Noche
        self.assertNotIn("time_night", reg_by_num[609].filter_tags.split())  # Chandelure
        self.assertNotIn("time_day", nat_by_num[407].filter_tags.split())    # Roserade
        self.assertNotIn("time_day", nat_by_num[468].filter_tags.split())    # Togekiss
        self.assertNotIn("time_night", nat_by_num[429].filter_tags.split())  # Mismagius

    def test_white_forest_and_dark_grass_filter_tags(self):
        from tracker.catalog_service import get_compiled_catalog

        white_nat = get_compiled_catalog("white_national", force_reload=True)
        black_nat = get_compiled_catalog("black_national", force_reload=True)
        white_reg = get_compiled_catalog("white", force_reload=True)

        wf_white = [e for e in white_nat if "white_forest" in e.filter_tags.split()]
        wf_black = [e for e in black_nat if "white_forest" in e.filter_tags.split()]
        self.assertEqual(len(wf_white), 33)
        self.assertEqual(len(wf_black), 0)
        self.assertNotIn("white_forest", next(e for e in white_nat if e.pokemon.national_number == 399).filter_tags.split())

        dg_reg = [e for e in white_reg if "dark_grass" in e.filter_tags.split()]
        dg_nat = [e for e in white_nat if "dark_grass" in e.filter_tags.split()]
        self.assertGreaterEqual(len(dg_reg), 40)
        self.assertGreaterEqual(len(dg_nat), 80)
        self.assertFalse(any(e.obtaining_info.get("type") == "transfer" for e in dg_nat))

    def test_black_national_swarm_filter_tags_and_transfers_exclusion(self):
        from tracker.catalog_service import get_compiled_catalog
        from tracker.exclusives import NON_UNOVA_TRANSFERS_BLACK

        nat_entries = get_compiled_catalog("black_national")
        nat_by_num = {e.pokemon.national_number: e for e in nat_entries}

        swarm_ids = {56, 83, 84, 102, 161, 193, 204, 228, 235, 236, 285, 311, 313, 353, 360, 449, 453}
        actual_swarm_ids = {
            e.pokemon.national_number
            for e in nat_entries
            if "swarm" in e.filter_tags.split()
        }
        self.assertEqual(actual_swarm_ids, swarm_ids)

        for sid in swarm_ids:
            entry = nat_by_num[sid]
            self.assertEqual(entry.obtaining_info.get("type"), "wild")
            methods = [loc.get("method", "") for loc in entry.obtaining_info.get("locations", [])]
            self.assertIn("Manada diaria", methods)
            self.assertNotIn(sid, NON_UNOVA_TRANSFERS_BLACK)

        # Wobbuffet (#202) debe quedar como evolución de Wynaut (#360) y fuera de Poké Transfer
        wobbuffet = nat_by_num[202]
        self.assertEqual(wobbuffet.obtaining_info.get("type"), "evolution")
        self.assertNotIn(202, NON_UNOVA_TRANSFERS_BLACK)

    def test_black_leafgreen_emerald_official_spanish_locations(self):
        from tracker.catalog_service import get_compiled_catalog

        black_nat = get_compiled_catalog("black_national")
        black_by_num = {e.pokemon.national_number: e for e in black_nat}

        cobalion_areas = [l.get("area", "") for l in black_by_num[638].obtaining_info.get("locations", [])]
        self.assertIn("Cueva Loza (Estancia Orientación)", cobalion_areas)
        self.assertNotIn("Sala del Guía", black_by_num[638].obtaining_info.get("summary", ""))
        self.assertIn("Estancia Orientación", black_by_num[638].obtaining_info.get("summary", ""))

        self.assertNotIn("Reserva Natural", black_by_num[129].obtaining_info.get("summary", ""))
        self.assertIn("Ander", black_by_num[446].obtaining_info.get("summary", ""))
        self.assertIn("Caramelo Furia", black_by_num[555].obtaining_info.get("summary", ""))
        self.assertIn("Trasladador PKMN", black_by_num[570].obtaining_info.get("summary", ""))
        self.assertIn("PiroROM y FulgoROM", black_by_num[649].obtaining_info.get("summary", ""))

        # Puente Fayenza se mantiene con el nombre habitual del juego
        ducklett_areas = [l.get("area", "") for l in black_by_num[580].obtaining_info.get("locations", [])]
        self.assertIn("Puente Fayenza", ducklett_areas)

        for slug in ("leafgreen_national", "emerald_national"):
            entries = get_compiled_catalog(slug)
            all_areas = {l.get("area", "") for e in entries for l in e.obtaining_info.get("locations", [])}
            for raw_token in ("Icefall", "Victory Road", "Mt Ember", "hoenn-safari", "team-magma"):
                self.assertFalse(any(raw_token in area for area in all_areas), f"{raw_token} detectado en {slug}")

    def test_no_mixed_evolution_or_nonsense_obtaining_methods_across_catalogs(self):
        """Audita los 28 catálogos para asegurar que no haya evoluciones mezcladas en locations ni inconsistencias graves."""
        from tracker.catalog_service import get_compiled_catalog, CATALOGS_DIR, clear_catalog_memory_cache
        from tracker.views import _classify_catalog_for_game

        clear_catalog_memory_cache()
        non_wild_kw = (
            "guarder", "crianza", "intercambio", "huevo", "fósil", "fosil",
            "regalo", "evento", "casino", "evoluc", "trasladador",
        )

        for cat_path in sorted(CATALOGS_DIR.glob("*.json")):
            slug_key = cat_path.stem
            entries = get_compiled_catalog(slug_key, force_reload=True)
            for e in entries:
                obt = e.obtaining_info or {}
                t = obt.get("type")
                locs = obt.get("locations") or []
                name = e.pokemon.display_name

                # 1. Ninguna entrada no evolutiva debe mezclar textos de evolución en locations (salvo exclusivos transferidos)
                for l in locs:
                    loc_txt = f"{l.get('area', '')} {l.get('method', '')}".lower()
                    if "evoluc" in loc_txt and not (t == "trade" and "transferido" in loc_txt):
                        self.fail(f"{slug_key}: {name} ({t}) contiene evolución en locations: {l}")

                # 2. No debe haber intercambios NPC duplicados ("Intercambio con NPC" junto a "Intercambio NPC por ...")
                trade_methods = [l.get("method", "").lower() for l in locs if "intercambio" in l.get("method", "").lower()]
                if any("intercambio npc por" in m for m in trade_methods):
                    self.assertNotIn("intercambio con npc", trade_methods, f"{slug_key}: {name} tiene intercambio duplicado")

                # 3. Entradas marcadas 'wild' deben tener ubicaciones y al menos una ubicación salvaje real
                if t == "wild":
                    self.assertTrue(locs, f"{slug_key}: {name} marcado como wild sin locations")
                    self.assertFalse(
                        all(any(k in f"{l.get('area', '')} {l.get('method', '')}".lower() for k in non_wild_kw) for l in locs),
                        f"{slug_key}: {name} marcado como wild pero sin ubicaciones salvajes: {locs}",
                    )

        # 4. Casos puntuales auditados
        black_nat = get_compiled_catalog("black_national")
        black_by_num = {e.pokemon.national_number: e for e in black_nat}
        self.assertEqual([l["area"] for l in black_by_num[637].obtaining_info["locations"]], ["Castillo Ancestral (Planta más profunda)"])
        self.assertEqual([l["area"] for l in black_by_num[555].obtaining_info["locations"]], ["Castillo Ancestral (Entrada)"])
        self.assertEqual([l["area"] for l in black_by_num[571].obtaining_info["locations"]], ["Bosque de los Perdidos"])
        self.assertEqual(black_by_num[571].obtaining_info["type"], "event")
        self.assertEqual(black_by_num[202].obtaining_info["locations"], [])

        res_black = _classify_catalog_for_game(black_nat, "black")
        for e in black_nat:
            if e.obtaining_info.get("type") == "evolution":
                self.assertNotEqual(res_black.get(e.pokemon.national_number), (True, "Salvaje"), f"{e.pokemon.display_name} mal clasificado como Salvaje")
        self.assertFalse(res_black.get(571, (False, None))[0])

        # Zafiro / Esmeralda / Cristal / Oro / Plata / Gen 4
        sapphire_by_num = {e.pokemon.national_number: e for e in get_compiled_catalog("sapphire")}
        self.assertEqual(sapphire_by_num[300].obtaining_info["type"], "wild")
        self.assertIn("Ciudad Arborada", [l["area"] for l in sapphire_by_num[300].obtaining_info["locations"]])
        self.assertNotIn("Pueblo Verdegal", [l["area"] for l in sapphire_by_num[300].obtaining_info["locations"]])
        self.assertEqual(sapphire_by_num[116].obtaining_info["type"], "wild")
        self.assertEqual(sapphire_by_num[312].obtaining_info["type"], "wild")

        emerald_nat = {e.pokemon.national_number: e for e in get_compiled_catalog("emerald_national")}
        self.assertEqual(emerald_nat[251].obtaining_info["type"], "event")
        self.assertEqual(emerald_nat[273].obtaining_info["type"], "wild")
        self.assertEqual(emerald_nat[311].obtaining_info["type"], "wild")
        self.assertEqual(emerald_nat[116].obtaining_info["type"], "wild")

        crystal_by_num = {e.pokemon.national_number: e for e in get_compiled_catalog("crystal")}
        self.assertEqual(crystal_by_num[82].obtaining_info["type"], "evolution")
        self.assertEqual(crystal_by_num[178].obtaining_info["type"], "evolution")

        gold_by_num = {e.pokemon.national_number: e for e in get_compiled_catalog("gold")}
        self.assertEqual(gold_by_num[133].obtaining_info["type"], "gift")

        # Gengar Gen 4 mantiene 'evolution', y evoluciones con incienso sin forma salvaje quedan sin Guardería
        for slug in ("diamond", "pearl", "platinum"):
            g_by_num = {e.pokemon.national_number: e for e in get_compiled_catalog(slug)}
            self.assertEqual(g_by_num[94].obtaining_info["type"], "evolution")
            self.assertEqual(g_by_num[94].obtaining_info["badge_label"], "Evolución")
            self.assertEqual(g_by_num[143].obtaining_info["locations"], [])
            self.assertEqual(g_by_num[226].obtaining_info["locations"], [])

        hg_nat = {e.pokemon.national_number: e for e in get_compiled_catalog("heartgold_national")}
        self.assertIn("Albufera", hg_nat[189].obtaining_info["summary"])
        hg_reg = {e.pokemon.national_number: e for e in get_compiled_catalog("heartgold")}
        self.assertEqual(hg_reg[189].obtaining_info["type"], "evolution")
        self.assertEqual(hg_reg[189].obtaining_info["locations"], [])
        ss_nat = {e.pokemon.national_number: e for e in get_compiled_catalog("soulsilver_national")}
        self.assertEqual(ss_nat[226].obtaining_info["type"], "trade")

    def test_catalog_entry_ids_are_unique_across_games_and_scoped_lookup(self):
        """Garantiza 0 colisiones de entry.id entre juegos distintos y aislamiento por (game_slug, is_national)."""
        from collections import defaultdict
        from tracker.catalog_service import get_compiled_catalog, get_catalog_entry_by_id, CATALOGS_DIR

        ids_by_game = defaultdict(set)
        for cat_path in sorted(CATALOGS_DIR.glob("*.json")):
            with open(cat_path, encoding="utf-8") as fp:
                for raw in json.load(fp):
                    ids_by_game[raw["id"]].add(raw["game_slug"])

        cross_game_collisions = {eid: games for eid, games in ids_by_game.items() if len(games) > 1}
        self.assertEqual(cross_game_collisions, {}, f"Colisiones de ID entre juegos: {list(cross_game_collisions.items())[:5]}")

        # Cargar Esmeralda, luego Cristal, y comprobar resolución aislada por juego y modo
        emerald_reg = get_compiled_catalog("emerald", is_national=False)
        seedot_reg = next(e for e in emerald_reg if e.pokemon.national_number == 273)
        get_compiled_catalog("crystal", is_national=False)

        resolved_reg = get_catalog_entry_by_id(seedot_reg.id, game_slug="emerald", is_national=False)
        self.assertIsNotNone(resolved_reg)
        self.assertEqual(resolved_reg.game_slug, "emerald")
        self.assertEqual(resolved_reg.pokemon.display_name, "Seedot")
        self.assertEqual(resolved_reg.entry_number, 22)

        resolved_nat = get_catalog_entry_by_id(seedot_reg.id, game_slug="emerald", is_national=True)
        self.assertIsNotNone(resolved_nat)
        self.assertEqual(resolved_nat.game_slug, "emerald")
        self.assertEqual(resolved_nat.pokemon.display_name, "Seedot")
        self.assertEqual(resolved_nat.entry_number, 273)

        # HeartGold y SoulSilver tienen rangos disjuntos
        hg_ids = {e.id for e in get_compiled_catalog("heartgold", is_national=False)}
        ss_ids = {e.id for e in get_compiled_catalog("soulsilver", is_national=False)}
        self.assertEqual(hg_ids.intersection(ss_ids), set())

    def test_npc_trade_nicknames_spanish_es_and_clear_phrasing(self):
        """Verifica que los motes de intercambios NPC estén en español de España y asociados al Pokémon recibido."""
        from tracker.catalog_service import get_compiled_catalog, CATALOGS_DIR

        for cat_path in sorted(CATALOGS_DIR.glob("*.json")):
            entries = get_compiled_catalog(cat_path.stem)
            for e in entries:
                for l in (e.obtaining_info or {}).get("locations") or []:
                    m = (l.get("method") or "").lower()
                    self.assertNotIn("intercambio in-game", m, f"{cat_path.stem}: {e.pokemon.display_name} aún tiene texto en inglés: {l}")
                    self.assertNotIn("evento in-game", m, f"{cat_path.stem}: {e.pokemon.display_name} aún tiene texto en inglés: {l}")

        # Gen 3: mote asociado al Pokémon recibido, nunca detrás del Pokémon entregado
        emerald_nat = {e.pokemon.national_number: e for e in get_compiled_catalog("emerald_national")}
        self.assertIn("a cambio de un Seedot (con el mote «SITOT»)", emerald_nat[273].obtaining_info["summary"])
        self.assertIn("a cambio de un Plusle (con el mote «PUSLE»)", emerald_nat[311].obtaining_info["summary"])
        self.assertIn("a cambio de un Horsea (con el mote «HORSI»)", emerald_nat[116].obtaining_info["summary"])
        self.assertIn("a cambio de un Meowth (con el mote «MEOWOW»)", emerald_nat[52].obtaining_info["summary"])

        sapphire_reg = {e.pokemon.national_number: e for e in get_compiled_catalog("sapphire")}
        self.assertIn("a cambio de un Makuhita (con el mote «MAKIT»)", sapphire_reg[296].obtaining_info["summary"])
        self.assertIn("a cambio de un Skitty (con el mote «SKITIT»)", sapphire_reg[300].obtaining_info["summary"])
        self.assertIn("a cambio de un Corsola (con el mote «COROSO»)", sapphire_reg[222].obtaining_info["summary"])

        # Gen 4 HGSS: motes oficiales de España y tarjetas limpias
        hg_nat = {e.pokemon.national_number: e for e in get_compiled_catalog("heartgold_national")}
        self.assertIn("«Musculitos»", hg_nat[66].obtaining_info["summary"])
        self.assertIn("«Trespicolo»", hg_nat[85].obtaining_info["summary"])
        self.assertIn("«Temblores»", hg_nat[95].obtaining_info["summary"])
        self.assertIn("«Calamby»", hg_nat[100].obtaining_info["summary"])
        self.assertIn("«Xaty»", hg_nat[178].obtaining_info["summary"])

        # Gen 4 Sinnoh: sin casas de intercambio listadas como "Salvaje en:" y con motes españoles
        dia_reg = {e.pokemon.national_number: e for e in get_compiled_catalog("diamond")}
        self.assertNotIn("Casa Noroeste", dia_reg[63].obtaining_info["summary"].split("También")[0])
        self.assertIn("«Kazza»", dia_reg[63].obtaining_info["summary"])
        self.assertIn("«Gaspar»", dia_reg[93].obtaining_info["summary"])
        self.assertIn("«Foppa»", dia_reg[129].obtaining_info["summary"])
        self.assertIn("«Charap»", dia_reg[441].obtaining_info["summary"])

    def test_black_audit_victory_road_methods_trades_notes_and_transfers(self):
        """Valida las correcciones de la auditoría de Pokémon Negro (Deino P1/P3, métodos, intercambios, crianza, Snorlax y notas)."""
        from tracker.catalog_service import get_compiled_catalog, clear_catalog_memory_cache
        from tracker.exclusives import NON_UNOVA_TRANSFERS_BLACK
        from tracker.pokemon_forms import get_pokemon_forms
        from tracker.views import _classify_catalog_for_game

        clear_catalog_memory_cache()
        reg_by = {e.pokemon.national_number: e for e in get_compiled_catalog("black", force_reload=True)}
        nat_by = {e.pokemon.national_number: e for e in get_compiled_catalog("black_national", force_reload=True)}

        # 1. Deino en Calle Victoria (P1 y P3) con método Caminando
        deino_locs = {l["area"]: l["method"] for l in reg_by[633].obtaining_info["locations"]}
        self.assertEqual(deino_locs.get("Calle Victoria (P1)"), "Caminando")
        self.assertEqual(deino_locs.get("Calle Victoria (P3)"), "Caminando")
        self.assertNotIn("Calle Victoria (P2)", deino_locs)

        # 2. Excadrill en Calle Victoria con Nube de polvo (sin Hierba movediza en cuevas)
        for l in reg_by[530].obtaining_info["locations"]:
            if "Calle Victoria" in l["area"] or "Boquete Gigante" in l["area"] or "Gruta" in l["area"]:
                self.assertEqual(l["method"], "Nube de polvo")

        # 3. Exteriores de Torre Duodraco y Boquete Gigante con Hierba alta (no Caminando)
        tranquill_locs = {l["area"]: l["method"] for l in reg_by[520].obtaining_info["locations"]}
        self.assertIn("Hierba alta", tranquill_locs["Torre Duodraco (Entrada)"])
        self.assertIn("Hierba alta", tranquill_locs["Torre Duodraco (Exterior)"])
        clefairy_locs = {l["area"]: l["method"] for l in nat_by[35].obtaining_info["locations"]}
        self.assertIn("Hierba alta", clefairy_locs["Boquete Gigante (Bosque Interior)"])
        tangela_locs = {l["area"]: l["method"] for l in nat_by[114].obtaining_info["locations"]}
        self.assertIn("Hierba alta", tangela_locs["Boquete Gigante (Exterior)"])

        # 3b. Charcos en Ciudad Teja / Ruta 8 / Pantano Teja y arena en Ruta 4 / Zona Desierto
        shelmet_locs = {l["area"]: l["method"] for l in reg_by[616].obtaining_info["locations"]}
        self.assertEqual(shelmet_locs["Ciudad Teja"], "Caminando en charcos (Primavera, Verano, Otoño)")
        self.assertEqual(shelmet_locs["Ruta 8"], "Caminando en charcos (Primavera, Verano, Otoño)")
        self.assertEqual(shelmet_locs["Pantano Teja"], "Caminando en charcos (Primavera, Verano, Otoño)")
        palpitoad_locs = {l["area"]: l["method"] for l in reg_by[536].obtaining_info["locations"]}
        self.assertEqual(palpitoad_locs["Ciudad Teja"], "Caminando en charcos (Primavera, Verano, Otoño)")
        stunfisk_locs = {l["area"]: l["method"] for l in reg_by[618].obtaining_info["locations"]}
        self.assertIn("Caminando en charcos (Primavera, Verano, Otoño)", stunfisk_locs["Pantano Teja"])
        sandile_locs = {l["area"]: l["method"] for l in reg_by[551].obtaining_info["locations"]}
        self.assertEqual(sandile_locs["Ruta 4"], "Caminando en la arena")
        self.assertEqual(sandile_locs["Zona Desierto"], "Caminando en la arena")
        self.assertEqual(sandile_locs["Zona Desierto (Entrada)"], "Caminando en la arena")

        # 4. Emolga (Ruta 7 NPC Boldore), Foongus y Amoonguss (Poké Ball camuflada) sin 'Salvaje' genérico
        emolga_locs = {l["area"]: l["method"] for l in reg_by[587].obtaining_info["locations"]}
        self.assertIn("Intercambio NPC por Boldore", emolga_locs["Ruta 7"])
        self.assertNotIn("Salvaje", emolga_locs["Ruta 7"])
        foongus_locs = {l["area"]: l["method"] for l in reg_by[590].obtaining_info["locations"]}
        self.assertIn("Encuentro estático (Poké Ball camuflada)", foongus_locs["Ruta 6"])
        amoonguss_locs = {l["area"]: l["method"] for l in reg_by[591].obtaining_info["locations"]}
        self.assertIn("Encuentro estático (Poké Ball camuflada)", amoonguss_locs["Ruta 10"])

        # 5. Basculin Raya Roja en Ciudad Fayenza (mote Mordiscos) y múltiples zonas acuáticas + motes españoles
        self.assertIn("Forma Raya Roja (mote: Mordiscos)", reg_by[550].obtaining_info["summary"])
        basc_locs = {l["area"]: l["method"] for l in reg_by[550].obtaining_info["locations"]}
        self.assertIn("Calle Victoria (P3)", basc_locs)
        self.assertIn("Mordiscos", basc_locs["Ciudad Fayenza"])
        basc_forms = {f["form_key"]: f for f in get_pokemon_forms(550, "black")}
        self.assertIn("Mordiscos", basc_forms["red_striped"]["notes"][0]["text"])
        self.assertIn("no se obtiene por intercambio interno", basc_forms["blue_striped"]["notes"][0]["text"])
        self.assertIn("Florina", reg_by[548].obtaining_info["summary"])
        self.assertIn("Tripón", nat_by[446].obtaining_info["summary"])
        self.assertIn("Tecno", nat_by[479].obtaining_info["summary"])

        # 6. Snorlax (#143) como evolución de Munchlax (#446), fuera de NON_UNOVA_TRANSFERS_BLACK
        self.assertNotIn(143, NON_UNOVA_TRANSFERS_BLACK)
        self.assertNotIn(446, NON_UNOVA_TRANSFERS_BLACK)
        self.assertEqual(nat_by[143].obtaining_info["type"], "evolution")
        self.assertEqual(nat_by[143].obtaining_info["evolution_info"]["from"], "Munchlax")

        # 7. Notas explicativas en fósiles (post-game + Pokédex Nacional en Monte Tuerca), Zorua y Zoroark
        for fid in (138, 140, 142, 345, 347, 408, 410):
            self.assertIn("Pokédex Nacional", nat_by[fid].obtaining_info["summary"])
            self.assertTrue(nat_by[fid].notes, f"Falta nota explicativa en fósil #{fid}")
            self.assertIn("Pokédex Nacional", nat_by[fid].notes[0]["text"])
        for ufid in (564, 566):
            self.assertTrue(reg_by[ufid].notes, f"Falta nota explicativa en fósil de Teselia #{ufid}")
            self.assertIn("únicamente un fósil", reg_by[ufid].notes[0]["text"])
        self.assertTrue(reg_by[570].notes)
        self.assertIn("Celebi", reg_by[570].notes[0]["text"])
        self.assertNotIn("macho", reg_by[570].notes[0]["text"])
        self.assertTrue(reg_by[571].notes)
        self.assertIn("Bosque de los Perdidos", reg_by[571].notes[0]["text"])
        self.assertNotIn("hembra", reg_by[571].notes[0]["text"])
        self.assertNotIn("hembra", reg_by[571].obtaining_info["summary"])

        # 8. Pureza de traducciones oficiales en español de España en formas y catálogos
        darmanitan_zen = next(f for f in get_pokemon_forms(555, "black") if f["form_key"] == "zen")
        self.assertIn("Caramelo Furia", darmanitan_zen["notes"][0]["text"])
        self.assertNotIn("Furiazafrán", darmanitan_zen["notes"][0]["text"])

        arceus_ground = next(f for f in get_pokemon_forms(493, "black") if f["form_key"] == "ground")
        self.assertEqual(arceus_ground["name"], "Tabla Terrax")
        self.assertNotIn("Terraja", arceus_ground["notes"][0]["text"])

        genesect_burn = next(f for f in get_pokemon_forms(649, "black") if f["form_key"] == "burn")
        self.assertEqual(genesect_burn["name"], "PiroROM")
        self.assertIn("Tecnochoque", genesect_burn["notes"][0]["text"])
        self.assertNotIn("Cromo", genesect_burn["name"])
        self.assertNotIn("Tecno Shock", genesect_burn["notes"][0]["text"])

        # 9. Modal de Transferir en Pokémon Negro: solo especies Gen 1-4 (sin Gen 5) y descripción HTML sin escapar
        self.assertEqual(len(NON_UNOVA_TRANSFERS_BLACK), 178)
        self.assertTrue(all(num < 494 for num in NON_UNOVA_TRANSFERS_BLACK))
        for gen5_id in (494, 570, 571, 645, 647, 648, 649):
            self.assertNotIn(gen5_id, NON_UNOVA_TRANSFERS_BLACK)

        from django.template.loader import render_to_string
        from tracker.exclusives import get_version_transfers_context
        from tracker.models import Game, Pokedex

        black_game = Game(slug="black", name="Pokémon Negro", generation=5)
        black_nat_dex = Pokedex(slug="national", name="Pokédex Nacional", is_national=True)
        transfers_info = get_version_transfers_context(
            black_game, black_nat_dex, set(), entries_by_num=nat_by
        )
        self.assertIsNotNone(transfers_info)
        self.assertEqual(transfers_info["total"], 178)
        self.assertEqual(transfers_info["mechanic_badge"], "Pokétransfer")
        self.assertEqual(transfers_info["notes_count"], 2)
        self.assertIn("Pokémon Dream World", transfers_info["historical_note"])
        self.assertIn("Entralinked", transfers_info["historical_note"])
        rendered_modal = render_to_string(
            "tracker/components/_modal_transfers.html",
            {"transfers_info": transfers_info, "game": black_game},
        )
        self.assertIn("<strong>Pokémon Negro</strong>", rendered_modal)
        self.assertIn("<strong>Pokémon Dream World</strong>", rendered_modal)
        self.assertIn("2 notas", rendered_modal)
        self.assertNotIn("&lt;strong&gt;", rendered_modal)

        # 10. Fósiles como objetos interactivos en todas las generaciones (Gen 1 a Gen 5)
        from tracker.utils import resolve_evolution_stone

        # Gen 1 (Rojo): Fósil Hélix en Monte Moon, restauración en Isla Canela
        red_by = {e.pokemon.national_number: e for e in get_compiled_catalog("red", force_reload=True)}
        self.assertEqual(red_by[138].evolution_stone["slug"], "helix-fossil")
        self.assertEqual(red_by[138].evolution_stone["category"], "fossil")
        self.assertIn("Monte Moon", str(red_by[138].evolution_stone["locations"]))

        # Gen 2 (Oro): No hay restauración de fósiles; no debe asignarse objeto fósil
        gold_by = {e.pokemon.national_number: e for e in get_compiled_catalog("gold", force_reload=True)}
        self.assertIsNone(gold_by[138].evolution_stone)
        self.assertIsNone(gold_by[142].evolution_stone)

        # Gen 3 (Esmeralda / Rubí): Fósiles de Hoenn con ícono y sin fósil para Omanyte (transferencia)
        eme_nat_by = {e.pokemon.national_number: e for e in get_compiled_catalog("emerald_national", force_reload=True)}
        self.assertEqual(eme_nat_by[345].evolution_stone["slug"], "root-fossil")
        self.assertIn("Torre Espejismo", str(eme_nat_by[345].evolution_stone["locations"]))
        self.assertNotIn("Torre Espejismo", str(eme_nat_by[345].obtaining_info["locations"]))
        self.assertIsNone(eme_nat_by[138].evolution_stone)

        # Gen 4 (Diamante / Platino / HeartGold): Fósiles propios, de versión contraria y equipables
        dia_nat_by = {e.pokemon.national_number: e for e in get_compiled_catalog("diamond_national", force_reload=True)}
        self.assertEqual(dia_nat_by[408].evolution_stone["slug"], "skull-fossil")
        self.assertEqual(dia_nat_by[410].evolution_stone["slug"], "armor-fossil")
        self.assertIn("Perla", str(dia_nat_by[410].evolution_stone["locations"]))
        plat_skull = resolve_evolution_stone(item_slug="skull-fossil", game_slug="platinum")
        self.assertIn("impar", str(plat_skull["locations"]))
        hg_nat_by = {e.pokemon.national_number: e for e in get_compiled_catalog("heartgold_national", force_reload=True)}
        self.assertEqual(hg_nat_by[408].evolution_stone["slug"], "skull-fossil")
        self.assertIn("Sinnoh", str(hg_nat_by[408].evolution_stone["locations"]))

        # Gen 5 (Negro): Fósil Coraza en Monte Tuerca en el modal y solo Ciudad Esmalte + Guardería en la tarjeta
        self.assertEqual(nat_by[410].evolution_stone["slug"], "armor-fossil")
        self.assertIn("Monte Tuerca", str(nat_by[410].evolution_stone["locations"]))
        self.assertNotIn("Monte Tuerca", str(nat_by[410].obtaining_info["locations"]))
        self.assertIn("Museo de Ciudad Esmalte", str(nat_by[410].obtaining_info["locations"]))
        self.assertEqual(reg_by[564].evolution_stone["slug"], "cover-fossil")
        self.assertIn("Castillo Ancestral", str(reg_by[564].evolution_stone["locations"]))
        self.assertNotIn("Castillo Ancestral", str(reg_by[564].obtaining_info["locations"]))

        meloetta_step = next(f for f in get_pokemon_forms(648, "black") if f["form_key"] == "pirouette")
        self.assertIn("La melodía del descanso", meloetta_step["notes"][0]["text"])
        self.assertNotIn("Café Sonata", meloetta_step["notes"][0]["text"])

        shaymin_sky = next(f for f in get_pokemon_forms(492, "black") if f["form_key"] == "sky")
        self.assertIn("Gracídea", shaymin_sky["notes"][0]["text"])
        self.assertNotIn("Grácidea", shaymin_sky["notes"][0]["text"])

        # 11. Sprites modernos de Pokémon HOME en formas de Deerling, Sawsbuck y Genesect
        from pathlib import Path
        from django.conf import settings
        for num in (585, 586, 649):
            forms = get_pokemon_forms(num, "black")
            for form in forms:
                fkey = form["form_key"]
                expected_stem = str(num) if (num == 649 and fkey == "normal") else f"{num}-{fkey}"
                self.assertEqual(form["sprite_modern"], f"/media/pokemon/home/{expected_stem}.png")
                self.assertEqual(form["sprite_modern_shiny"], f"/media/pokemon/home/shiny/{expected_stem}.png")
                self.assertTrue((Path(settings.BASE_DIR) / form["sprite_modern"].lstrip("/")).exists())
                self.assertTrue((Path(settings.BASE_DIR) / form["sprite_modern_shiny"].lstrip("/")).exists())

        # 12. Invariante global: modo moderno shiny usa HOME shiny en todas las gens y formas consistentes
        for game_slug, sample_num in (("red", 1), ("gold", 201), ("ruby", 252), ("diamond", 387), ("black", 495)):
            cat = {e.pokemon.national_number: e for e in get_compiled_catalog(game_slug, force_reload=True)}
            entry = cat[sample_num]
            suffix = "-f" if sample_num == 201 else ""
            import json as _json
            self.assertEqual(entry.modern_sprite_shiny_url, f"/media/pokemon/home/shiny/{sample_num}{suffix}.png")
            self.assertEqual(_json.loads(entry.modal_data_json)["sprite_modern_shiny"], entry.modern_sprite_shiny_url)

        form_targets = [
            (172, "heartgold"), (201, "gold"), (351, "ruby"), (386, "platinum"),
            (412, "platinum"), (413, "platinum"), (421, "platinum"), (422, "platinum"),
            (423, "platinum"), (479, "platinum"), (487, "platinum"), (492, "platinum"),
            (493, "platinum"), (550, "black"), (555, "black"), (585, "black"),
            (586, "black"), (648, "black"), (649, "black"),
        ]
        for f_num, f_game in form_targets:
            forms = get_pokemon_forms(f_num, f_game)
            self.assertTrue(forms)
            seen_modern = set()
            for form in forms:
                sm = form["sprite_modern"]
                sms = form["sprite_modern_shiny"]
                self.assertTrue(sm.startswith("/media/pokemon/home/"), f"{f_num} {form['form_key']}: {sm}")
                self.assertTrue(sms.startswith("/media/pokemon/home/shiny/"), f"{f_num} {form['form_key']}: {sms}")
                self.assertEqual(Path(sm).name, Path(sms).name, f"Mismatch normal/shiny para #{f_num} {form['form_key']}")
                self.assertTrue((Path(settings.BASE_DIR) / sm.lstrip("/")).exists(), f"Falta {sm}")
                self.assertTrue((Path(settings.BASE_DIR) / sms.lstrip("/")).exists(), f"Falta {sms}")
                if f_num != 172:
                    self.assertNotIn(sm, seen_modern, f"Sprite moderno duplicado en #{f_num}: {sm}")
                seen_modern.add(sm)

        shellos_sinnoh = get_pokemon_forms(422, "diamond")
        for sf in shellos_sinnoh:
            for loc in sf.get("locations", []):
                self.assertNotIn("Surfing", loc.get("method", ""))

        self.assertEqual(nat_by[466].evolution_stone.get("name_es"), "Electrizador")
        emerald_nat = {e.pokemon.national_number: e for e in get_compiled_catalog("emerald_national", force_reload=True)}
        self.assertIn("Mejora", emerald_nat[233].obtaining_info["summary"])
        self.assertNotIn("Up Grade", emerald_nat[233].obtaining_info["summary"])
        self.assertNotIn("Artisan Cave", emerald_nat[235].obtaining_info["summary"])
        self.assertNotIn("Faraway Island", emerald_nat[151].obtaining_info["summary"])

        # 8. Terminología oficial en español (Zona Nexo, Pokétransfer) y clasificación nativa de las 27 especies de crianza
        for cat_dict in (reg_by, nat_by):
            for entry in cat_dict.values():
                blob = f"{entry.obtaining_info['summary']} {entry.obtaining_info['badge_label']} {entry.obtaining_info['locations']}"
                self.assertNotIn("Entralink", blob)
                self.assertNotIn("Poké Transfer", blob)
                self.assertNotIn("Laboratorio Transfer", blob)

        native_map = _classify_catalog_for_game(list(nat_by.values()), "black")
        self.assertTrue(native_map[143][0])  # Snorlax vía Munchlax
        for bid in (13, 19, 21, 27, 41, 48, 54, 74, 77, 104, 163, 165, 167, 173, 174, 220, 238, 246, 276, 333, 343, 374, 401, 420, 425, 433, 436):
            self.assertNotIn("evento especial en Teselia", nat_by[bid].obtaining_info["summary"])
            self.assertTrue(native_map[bid][0], f"#{bid} {nat_by[bid].pokemon.display_name} debe resolver como nativo por crianza")

        # 9. Auditoría completa de piedras evolutivas, objetos e inciensos en Pokémon Negro
        from tracker.utils import get_evolution_stones_catalog, resolve_evolution_stone
        stones_catalog = get_evolution_stones_catalog()

        # Ningún objeto de Negro debe conservar el precio erróneo de 10 500 ₽ ni inciensos en Puente Progreso
        for slug, item in stones_catalog.items():
            locs = item.get("games", {}).get("black", [])
            blob = json.dumps(locs, ensure_ascii=False)
            self.assertNotIn("10 500", blob, f"{slug} sigue mostrando 10 500 ₽ en black")
            if slug.endswith("-stone"):
                cn = next((l for l in locs if l["area"] == "Ciudad Negra"), None)
                self.assertIsNotNone(cn, f"Falta Ciudad Negra en {slug}")
                self.assertIn("10 000 ₽", cn["detail"])
                self.assertIn("Zona Nexo", cn["detail"])
            if slug.endswith("-incense"):
                self.assertEqual([l["area"] for l in locs], ["Mercado de Ciudad Fayenza"])
                self.assertIn("9 600 ₽", locs[0]["detail"])
                self.assertNotIn("Puente Progreso", blob)

        # Piedra Solar (Sun Stone): Sótano 4 Castillo Ancestral, detrás del Centro Pokémon, Malena 10 000 ₽, Solrock 5 % y Recogida 31-100
        sun = resolve_evolution_stone(item_slug="sun-stone", game_slug="black")
        sun_blob = json.dumps(sun["locations"], ensure_ascii=False)
        self.assertIn("Sótano 4 (S4)", sun_blob)
        self.assertIn("detrás del Centro Pokémon", sun_blob)
        self.assertIn("Malena", sun_blob)
        self.assertIn("Solrock", sun_blob)
        self.assertIn("niveles 31 a 100", sun_blob)
        self.assertNotIn("Concurso de Bichos", sun["availability_note"])
        self.assertEqual(reg_by[549].evolution_stone["locations"], sun["locations"])  # Lilligant

        # Piedra Hoja (Leaf Stone): Centro de Estudios Estacionales (4 Deerling), Ruta 6 sin Surf y elección libre en Ciudad Porcelana
        leaf = resolve_evolution_stone(item_slug="leaf-stone", game_slug="black")
        leaf_blob = json.dumps(leaf["locations"], ensure_ascii=False)
        self.assertIn("Centro de Estudios Estacionales", leaf_blob)
        self.assertIn("Deerling", leaf_blob)
        self.assertIn("elegir libremente", leaf_blob)
        self.assertNotIn("requiere Surf", leaf_blob)

        # Piedra Lunar y Piedra Oval: sin mezclas de B2W2 ni ubicaciones erróneas
        moon = resolve_evolution_stone(item_slug="moon-stone", game_slug="black")
        moon_blob = json.dumps(moon["locations"], ensure_ascii=False)
        self.assertIn("Bosque Azulejo", moon_blob)
        self.assertIn("Lunatone", moon_blob)
        self.assertIn("niveles 41 a 100", moon_blob)
        self.assertNotIn("Museo de Ciudad Esmalte", moon_blob)
        self.assertNotIn("Castillo Ancestral", moon_blob)
        self.assertNotIn("Boquete Gigante", moon_blob)

        oval_blob = json.dumps(stones_catalog["oval-stone"]["games"]["black"], ensure_ascii=False)
        self.assertIn("Sótano 2 (S2)", oval_blob)
        self.assertIn("Surf", oval_blob)

        water = resolve_evolution_stone(item_slug="water-stone", game_slug="black")
        self.assertIn("Ciudad Fayenza", [l["area"] for l in water["locations"]])
        self.assertNotIn("Ruta 3", [l["area"] for l in water["locations"]])
        self.assertNotIn("elegir agua", json.dumps(water["locations"], ensure_ascii=False))

        # Metro Batalla y objetos de evolución en Negro 1 (sin ubicaciones de B2W2)
        for no_bs_slug in ("kings-rock", "up-grade", "protector", "electirizer", "magmarizer", "dubious-disc", "reaper-cloth"):
            bs_locs = stones_catalog[no_bs_slug]["games"]["black"]
            self.assertNotIn("Metro Batalla", json.dumps(bs_locs, ensure_ascii=False), f"{no_bs_slug} no se vende en Metro Batalla de Negro 1")
        kings_areas = [l["area"] for l in stones_catalog["kings-rock"]["games"]["black"]]
        self.assertIn("Ciudad Teja", kings_areas)
        self.assertIn("Habilidad Recogida", kings_areas)
        self.assertIn("niveles 11 a 30", json.dumps(stones_catalog["kings-rock"]["games"]["black"], ensure_ascii=False))
        self.assertNotIn("Pueblo Arcilla", kings_areas)
        self.assertEqual(
            [l["area"] for l in stones_catalog["electirizer"]["games"]["black"]],
            ["Ruta 13", "Ruta 13 (Buscatesoros)"],
        )
        self.assertIn("Corte", stones_catalog["electirizer"]["games"]["black"][0]["detail"])
        self.assertEqual(
            [l["area"] for l in stones_catalog["deep-sea-scale"]["games"]["black"]],
            ["Ruta 13", "Ruta 13 (Buscatesoros)", "Pokémon salvajes"],
        )
        self.assertIn("Fuerza", stones_catalog["deep-sea-scale"]["games"]["black"][0]["detail"])
        metal_blob = json.dumps(stones_catalog["metal-coat"]["games"]["black"], ensure_ascii=False)
        self.assertIn("Metagross", metal_blob)
        self.assertNotIn("Bronzor", metal_blob)
        self.assertEqual([l["area"] for l in stones_catalog["magmarizer"]["games"]["black"]], ["Ruta 13"])
        self.assertIn("Ruta 17", [l["area"] for l in stones_catalog["deep-sea-tooth"]["games"]["black"]])
        self.assertIn("Huntail", json.dumps(stones_catalog["deep-sea-tooth"]["games"]["black"], ensure_ascii=False))
        self.assertIn("Ruta 15", [l["area"] for l in stones_catalog["up-grade"]["games"]["black"]])
        self.assertIn("Santuario Abundancia", [l["area"] for l in stones_catalog["razor-fang"]["games"]["black"]])
        self.assertNotIn("Gligar", json.dumps(stones_catalog["razor-fang"]["games"]["black"], ensure_ascii=False))

        prism_blob = json.dumps(stones_catalog["prism-scale"]["games"]["black"], ensure_ascii=False)
        self.assertIn("Pueblo Arenisca", prism_blob)
        self.assertIn("niveles 51 a 100", prism_blob)
        self.assertNotIn("Puente Villa", prism_blob)
        self.assertNotIn("buscatesoros", prism_blob)

        # Métodos separados en Garra Afilada y objetos de incienso visibles en bebés de Pokédex Nacional
        self.assertEqual(
            [l["area"] for l in stones_catalog["razor-claw"]["games"]["black"]],
            ["Ruta 13", "Ruta 13 (Buscatesoros)", "Metro Batalla"],
        )
        from tracker.utils import INCENSE_BABY_MAP
        for baby_id, expected_incense in INCENSE_BABY_MAP.items():
            baby_entry = nat_by[baby_id]
            self.assertIsNotNone(baby_entry.evolution_stone, f"Falta evolution_stone en bebé #{baby_id}")
            self.assertEqual(baby_entry.evolution_stone["slug"], expected_incense)
            self.assertTrue(
                any("Crianza con Incienso" in l.get("method", "") for l in baby_entry.obtaining_info.get("locations", [])),
                f"Falta método de crianza con incienso en bebé #{baby_id}"
            )
        for gen3_slug in ("firered_national", "leafgreen_national"):
            gen3_by = {e.pokemon.national_number: e for e in get_compiled_catalog(gen3_slug, force_reload=True)}
            self.assertEqual(gen3_by[298].evolution_stone["slug"], "sea-incense")
            self.assertEqual(gen3_by[360].evolution_stone["slug"], "lax-incense")

    def test_legendaries_mythicals_events_and_no_reclutar_across_catalogs(self):
        """Garantiza eliminación total de 'reclutar' (no-NPC), ausencia de fallbacks genéricos y notas claras en legendarios/eventos."""
        import re
        from tracker.catalog_service import get_compiled_catalog, clear_catalog_memory_cache, CATALOGS_DIR
        from tracker.exclusives import GAME_VERSION_EXCLUSIVES_NOTICES
        from tracker.utils import get_evolution_stones_catalog

        clear_catalog_memory_cache()

        # 1. Cero apariciones de 'reclut*' fuera de nombres oficiales de entrenadores (Equipo Galaxia / Equipo Plasma)
        reclut_re = re.compile(r"reclut", re.IGNORECASE)
        for cat_path in sorted(CATALOGS_DIR.glob("*.json")):
            entries = get_compiled_catalog(cat_path.stem, force_reload=True)
            for e in entries:
                blob = json.dumps(
                    {
                        "obtaining": e.obtaining_info,
                        "notes": e.notes,
                        "stone": e.evolution_stone,
                    },
                    ensure_ascii=False,
                )
                for m in reclut_re.finditer(blob):
                    ctx = blob[max(0, m.start() - 30):min(len(blob), m.end() + 40)]
                    self.assertTrue(
                        "Equipo Galaxia" in ctx or "Equipo Plasma" in ctx,
                        f"{cat_path.name} #{e.pokemon.national_number} ({e.pokemon.display_name}) contiene 'reclut' indebido: {ctx}",
                    )

                obt = e.obtaining_info or {}
                summary = obt.get("summary", "")
                badge = obt.get("badge_label", "")
                self.assertNotEqual(badge, "Especial", f"{cat_path.name} #{e.pokemon.national_number} cayó en badge 'Especial'")
                self.assertNotIn("Obtención mediante evento especial", summary)
                self.assertNotIn("Obtención mediante distribución oficial o evento de Nintendo", summary)
                self.assertNotIn("Orión", json.dumps(obt, ensure_ascii=False))
                self.assertNotIn("Oro SoulSilver", json.dumps(obt, ensure_ascii=False))
                self.assertNotIn("Kyogre de SoulSilver", json.dumps(obt, ensure_ascii=False))

        stones_blob = json.dumps(get_evolution_stones_catalog(), ensure_ascii=False)
        self.assertNotIn("reclutable", stones_blob.lower())
        self.assertNotIn("reclutar", stones_blob.lower())
        self.assertNotIn("reclut", GAME_VERSION_EXCLUSIVES_NOTICES["black"].lower())

        # 2. Pokémon Negro: legendarios, singulares, eventos históricos y exclusivos sin Bosque Blanco falso
        black_reg = {e.pokemon.national_number: e for e in get_compiled_catalog("black", force_reload=True)}
        black_nat = {e.pokemon.national_number: e for e in get_compiled_catalog("black_national", force_reload=True)}

        self.assertIn("Pokétransfer", black_nat[493].obtaining_info["summary"])
        self.assertIn("Pokémon Global Link", black_nat[493].obtaining_info["summary"])
        self.assertIn("ARCEUSVOTE", black_nat[493].notes[0]["text"])

        for nid in (150, 151, 243, 244, 245, 251, 382, 383, 384, 385, 386, 483, 484, 487, 489, 490, 491, 492, 493):
            self.assertTrue(black_nat[nid].notes, f"Falta nota explicativa en #{nid} en black_national")

        self.assertNotIn("Bosque Blanco", black_reg[642].obtaining_info["summary"])
        self.assertNotIn("Bosque Blanco", black_reg[644].obtaining_info["summary"])
        self.assertIn("Primavera 2012", black_reg[644].notes[0]["text"])
        self.assertIn("Pantano Teja", black_reg[647].obtaining_info["summary"])
        self.assertIn("Sable Místico", black_reg[647].obtaining_info["summary"])
        self.assertIn("La melodía del descanso", black_reg[648].obtaining_info["summary"])
        self.assertIn("PiroROM y FulgoROM", black_reg[649].obtaining_info["summary"])
        self.assertEqual(black_nat[399].obtaining_info["badge_label"], "Crianza")

        # 3. Platino, Perla, HG/SS y Oro/Plata: notas de eventos y métodos corregidos
        plat_nat = {e.pokemon.national_number: e for e in get_compiled_catalog("platinum_national", force_reload=True)}
        self.assertIn("Flauta Azur", plat_nat[493].obtaining_info["historical_note"]["text"])
        self.assertIn("jamás fue distribuido", plat_nat[493].obtaining_info["historical_note"]["text"])
        self.assertIn("Parque Compi", plat_nat[377].obtaining_info["summary"])

        pearl_nat = {e.pokemon.national_number: e for e in get_compiled_catalog("pearl_national", force_reload=True)}
        for pid in (109, 165, 167, 228, 276, 293, 353, 360):
            self.assertEqual(pearl_nat[pid].obtaining_info["type"], "breeding", f"#{pid} en Perla debe ser breeding")

        ss_nat = {e.pokemon.national_number: e for e in get_compiled_catalog("soulsilver_national", force_reload=True)}
        self.assertIn("Kyogre de HeartGold", ss_nat[384].obtaining_info["summary"])
        self.assertIn("FAL2010", ss_nat[151].obtaining_info["historical_note"]["text"])
        self.assertIn("Giovanni", ss_nat[251].obtaining_info["historical_note"]["text"])
        self.assertIn("Ruinas de Sinjoh", ss_nat[493].obtaining_info["historical_note"]["text"])

        for g2_slug in ("gold", "silver"):
            g2_cat = {e.pokemon.national_number: e for e in get_compiled_catalog(g2_slug, force_reload=True)}
            self.assertIn("exclusivo de Pokémon Cristal", g2_cat[251].obtaining_info["summary"])


class PokemonWhiteGen5Tests(TestCase):
    """Batería integral de validación para Pokémon Blanco (slug 'white', Gen 5)."""

    def test_white_catalog_structure_ids_and_historical_types(self):
        from tracker.catalog_service import get_compiled_catalog, clear_catalog_memory_cache, ensure_all_catalogs_loaded
        from tracker.models import Game

        ensure_all_catalogs_loaded()
        clear_catalog_memory_cache()

        game = Game.objects.get(slug="white")
        self.assertEqual(game.generation, 5)
        self.assertTrue(game.has_retro_sprites)
        self.assertTrue(game.has_swarms)
        self.assertTrue(game.has_seasons)
        self.assertTrue(game.has_special_spots)
        self.assertFalse(game.has_time_of_day)

        reg = get_compiled_catalog("white", force_reload=True, is_national=False)
        nat = get_compiled_catalog("white", force_reload=True, is_national=True)
        self.assertEqual(len(reg), 156)
        self.assertEqual(len(nat), 649)

        # Victini #000 y rangos de ID disjuntos (9000..9155, 9201..9849)
        victini = reg[0]
        self.assertEqual(victini.id, 9000)
        self.assertEqual(victini.entry_number, 494)
        self.assertEqual(victini.display_number, "000")
        self.assertEqual(victini.pokemon.national_number, 494)
        self.assertEqual([e.id for e in reg[1:]], list(range(9001, 9156)))
        self.assertEqual([e.id for e in nat], list(range(9201, 9850)))

        # Fidelidad histórica estricta Gen 5: cero tipo Hada + is_hatchable explícito + 201-f.png en HOME
        for e in nat:
            self.assertNotEqual(e.primary_type, "fairy")
            self.assertNotEqual(e.secondary_type, "fairy")
            self.assertIsNotNone(e.is_hatchable)
        unown = next(e for e in nat if e.pokemon.national_number == 201)
        self.assertEqual(unown.pokemon.sprite_shiny_url, "/media/pokemon/home/shiny/201-f.png")

    def test_white_exclusives_white_forest_hub_and_breeding(self):
        from tracker.catalog_service import get_compiled_catalog
        from tracker.exclusives import (
            VERSION_EXCLUSIVES_CATALOG,
            GAME_VERSION_EXCLUSIVES_NOTICES,
            get_version_exclusives_context,
        )
        from tracker.models import Game
        from tracker.views import _classify_catalog_for_game

        white_excl = VERSION_EXCLUSIVES_CATALOG["white"]
        black_excl = VERSION_EXCLUSIVES_CATALOG["black"]
        self.assertEqual(len(white_excl), 117)
        self.assertEqual(len(black_excl), 17)
        for excluded in (314, 399, 400, 548, 549):
            self.assertNotIn(excluded, white_excl)
        self.assertNotIn(313, black_excl)

        game = Game.objects.get(slug="white")
        pokedex = game.pokedexes.get(slug="unova")
        ctx = get_version_exclusives_context(game, pokedex, set())
        self.assertEqual(ctx["counterpart_theme"], "black")
        self.assertEqual(ctx["own_theme"], "white")
        self.assertEqual(ctx["counterpart_total"], 17)
        self.assertEqual(ctx["own_total"], 117)
        self.assertIn("Bosque Blanco", GAME_VERSION_EXCLUSIVES_NOTICES["white"])

        nat = get_compiled_catalog("white", is_national=True)
        cls = _classify_catalog_for_game(nat, "white")
        by_nid = {e.pokemon.national_number: e for e in nat}

        # Las 33 especies base salvajes del Bosque Blanco son clasificadas como nativas en el Hub (regresión EXTERNAL_KEYWORDS)
        wf_base_ids = (
            16, 29, 32, 43, 63, 66, 69, 81, 92, 111, 137, 175, 179, 187, 194,
            239, 240, 265, 270, 273, 280, 283, 287, 293, 298, 304, 328, 341,
            371, 396, 403, 406, 440,
        )
        for nid in wf_base_ids:
            is_native, badge = cls[nid]
            self.assertTrue(is_native, f"Bosque Blanco #{nid} debe clasificarse como nativo en Pokémon Blanco")
            self.assertEqual(badge, "Salvaje")
            self.assertTrue(any("Bosque Blanco" in loc.get("area", "") for loc in by_nid[nid].obtaining_info["locations"]))
            self.assertTrue(any("Bosque Blanco" in n.get("title", "") for n in by_nid[nid].notes))

        # #399 Bidoof no sale salvaje en Bosque Blanco; se obtiene por crianza de Bibarel
        self.assertEqual(by_nid[399].obtaining_info["badge_label"], "Crianza")
        self.assertIn("Bibarel", by_nid[399].obtaining_info["summary"])
        self.assertFalse(any("Bosque Blanco" in loc.get("area", "") for loc in by_nid[399].obtaining_info["locations"]))

        # #313 Volbeat en Blanco por crianza de Illumise; #314 Illumise en Negro por crianza de Volbeat + Ditto
        self.assertEqual(by_nid[313].obtaining_info["badge_label"], "Crianza")
        self.assertIn("Illumise", by_nid[313].obtaining_info["summary"])
        black_nat = {e.pokemon.national_number: e for e in get_compiled_catalog("black", is_national=True)}
        self.assertEqual(black_nat[314].obtaining_info["badge_label"], "Crianza")
        self.assertIn("Volbeat", black_nat[314].obtaining_info["summary"])

        # Surf vs Hierba alta en Bosque Blanco (Lotad #270 aparece en ambos)
        for surf_id in (194, 270, 283, 341):
            wf_loc = next(l for l in by_nid[surf_id].obtaining_info["locations"] if l["area"] == "Bosque Blanco")
            self.assertIn("Surfeando", wf_loc["method"])
        lotad_wf = next(l for l in by_nid[270].obtaining_info["locations"] if l["area"] == "Bosque Blanco")
        self.assertIn("Hierba alta", lotad_wf["method"])

        # Basculin (#550) en Blanco y Negro cubre agua normal y sombra del agua + Munchlax (#446) en verano + evoluciones precisas
        for b_nat in (by_nid, black_nat):
            basc_r1 = next(l for l in b_nat[550].obtaining_info["locations"] if l["area"] == "Ruta 1")
            for m in ("Surf", "Surf en sombra del agua", "Supercaña", "Supercaña en sombra del agua"):
                self.assertIn(m, basc_r1["method"])
            self.assertIn("season_summer", b_nat[446].filter_tags.split())
            self.assertIn("Ataque > Defensa", b_nat[106].obtaining_info["summary"])
            self.assertIn("Remoraid", b_nat[226].obtaining_info["evolution_info"]["condition"])
            self.assertIn("Poké Ball", b_nat[292].obtaining_info["summary"])
            self.assertEqual(b_nat[350].obtaining_info["evolution_info"]["trigger"], "trade")
            self.assertEqual(b_nat[30].obtaining_info["evolution_info"]["from"], "Nidoran♀")
            self.assertEqual(b_nat[33].obtaining_info["evolution_info"]["from"], "Nidoran♂")
        self.assertTrue(by_nid[489].is_hatchable)

        # Legendarios propios de Blanco también deben ser nativos en el Hub
        self.assertEqual(cls[642], (True, "Único"))
        self.assertEqual(cls[644], (True, "Único"))

        # Inversión de crianza: #010 Caterpie por Metapod/Butterfree, #013 Weedle exclusivo de Negro
        self.assertEqual(cls[10], (True, "Crianza"))
        self.assertEqual(by_nid[13].obtaining_info["badge_label"], "Edición Negro")
        self.assertFalse(cls[13][0])

    def test_white_transfers_swarms_npcs_and_evolution_stones(self):
        from tracker.catalog_service import get_compiled_catalog
        from tracker.exclusives import VERSION_TRANSFERS_CATALOG, get_version_transfers_context
        from tracker.models import Game
        from tracker.pokemon_forms import get_basculin_forms, get_genesect_forms
        from tracker.utils import get_evolution_stones_catalog, resolve_evolution_stone

        white_transfers = VERSION_TRANSFERS_CATALOG.get("white", [])
        self.assertEqual(len(white_transfers), 178)
        self.assertTrue(all(n < 494 for n in white_transfers))

        game = Game.objects.get(slug="white")
        reg_pd = game.pokedexes.get(slug="unova")
        nat_pd = game.pokedexes.get(slug="national")
        self.assertIsNone(get_version_transfers_context(game, reg_pd, set()))
        nat_tr_ctx = get_version_transfers_context(game, nat_pd, set())
        self.assertTrue(nat_tr_ctx["has_transfers"])
        self.assertEqual(nat_tr_ctx["total"], 178)
        self.assertIn("Dream World", nat_tr_ctx["historical_note"])

        nat_by = {e.pokemon.national_number: e for e in get_compiled_catalog("white", is_national=True)}
        # Manadas invertidas
        for swarm_id in (46, 261, 312, 314):
            self.assertIn("swarm", nat_by[swarm_id].filter_tags.split())

        # Basculin Raya Azul común + Cabeza Roca + Mordiscos, Cottonee Cotona, Genesect HidroROM/CrioROM
        self.assertIn("Cabeza Roca", nat_by[550].obtaining_info["summary"])
        self.assertIn("Mordiscos", nat_by[550].obtaining_info["summary"])
        self.assertIn("Cotona", nat_by[546].obtaining_info["summary"])
        self.assertIn("HidroROM", nat_by[649].obtaining_info["summary"])
        self.assertIn("CrioROM", nat_by[649].obtaining_info["summary"])

        basc_forms = get_basculin_forms("white")
        self.assertIn("Mordiscos", basc_forms[1]["notes"][0]["text"])
        self.assertIn("Cabeza Roca", basc_forms[1]["notes"][0]["text"])
        gen_forms = get_genesect_forms("white")
        self.assertIn("Pokémon Blanco", next(f for f in gen_forms if f["form_key"] == "douse")["notes"][0]["text"])

        # Todos los 42 objetos en evolution_stones.json tienen games.white limpio
        stones = get_evolution_stones_catalog(force_reload=True)
        self.assertEqual(len(stones), 42)
        wf_residents = {
            "fire-stone": "Vito",
            "water-stone": "Melas",
            "leaf-stone": "Iraís",
            "thunder-stone": "Ken",
            "moon-stone": "Lila",
            "sun-stone": "Malena",
            "shiny-stone": "Sarah",
            "dusk-stone": "Don",
            "dawn-stone": "Pitu",
            "oval-stone": "Giuseppe",
        }
        for slug, item in stones.items():
            w_locs = item.get("games", {}).get("white", [])
            self.assertTrue(w_locs, f"Falta games.white en {slug}")
            blob = json.dumps(w_locs, ensure_ascii=False)
            self.assertNotIn("Ciudad Negra", blob)
            if slug in wf_residents:
                wf_entry = next((l for l in w_locs if l["area"] == "Bosque Blanco"), None)
                self.assertIsNotNone(wf_entry, f"Falta Bosque Blanco en {slug}")
                self.assertIn(wf_residents[slug], wf_entry["detail"])

        tooth_white_blob = json.dumps(stones["deep-sea-tooth"]["games"]["white"], ensure_ascii=False)
        scale_white_blob = json.dumps(stones["deep-sea-scale"]["games"]["white"], ensure_ascii=False)
        self.assertIn("Raya Roja, raro", tooth_white_blob)
        self.assertNotIn("Huntail", tooth_white_blob)
        self.assertIn("Gorebyss", scale_white_blob)
        self.assertNotIn("remolino", scale_white_blob.lower())
        moon_resolved = resolve_evolution_stone(item_slug="moon-stone", game_slug="white")
        self.assertIn("Bosque Blanco", moon_resolved["availability_note"])
        self.assertNotIn("Ciudad Negra", moon_resolved["availability_note"])

        # Fósiles en White Nacional: locations solo Museo de Ciudad Esmalte + Guardería (no Castillo Ancestral / Monte Tuerca)
        for fid in (138, 140, 142, 345, 347, 408, 410, 564, 566):
            areas = [l["area"] for l in nat_by[fid].obtaining_info["locations"]]
            self.assertEqual(areas, ["Museo de Ciudad Esmalte", "Ruta 3 (Guardería Pokémon)"])

    def test_white_views_ui_palette_and_unown(self):
        from tracker.unown_data import get_game_unown_chambers, get_unown_catalog

        self.assertEqual(get_game_unown_chambers("white"), {})
        uc = get_unown_catalog("white")
        self.assertEqual(len(uc), 28)
        self.assertEqual(uc[0]["sprite_normal"], "/media/pokemon/sprites/white/unown/a.png")

        res_reg = self.client.get("/white/")
        self.assertEqual(res_reg.status_code, 200)
        html_reg = res_reg.content.decode("utf-8")
        self.assertIn('data-game="white"', html_reg)
        self.assertIn("/media/pokemon/icons/gen5/644.png", html_reg)
        self.assertIn("bg-slate-200 text-slate-950", html_reg)

        res_nat = self.client.get("/white/national/")
        self.assertEqual(res_nat.status_code, 200)
        html_nat = res_nat.content.decode("utf-8")
        self.assertIn("Teselia (Pokétransfer)", html_nat)
        self.assertIn("bg-slate-900/10 text-slate-950 border-slate-400", html_nat)

        res_hub = self.client.get("/games/")
        self.assertEqual(res_hub.status_code, 200)
        self.assertIn("Zekrom", res_hub.content.decode("utf-8"))

        # Garantizar que ninguna barra de progreso use borde negro sobre el relleno (evita segmento de 2px al 0%)
        from pathlib import Path
        cards_js = Path("tracker/static/tracker/js/cards.js").read_text(encoding="utf-8")
        self.assertIn("white: 'bg-slate-400'", cards_js)
        self.assertNotIn("white: 'bg-slate-300 border border-slate-950'", cards_js.split("PROGRESS_DOT_THEME")[0])
        self.assertIn("white: 'bg-slate-300 border border-slate-950'", cards_js.split("PROGRESS_DOT_THEME")[1])

    def test_surf_and_rod_filter_tags_exclude_access_prose_and_counterpart_trades(self):
        """Verifica que surf y cañas no den falsos positivos por texto de summary (ej. Cobalion #638, Aerodactyl o exclusivos trade)."""
        from tracker.catalog_service import get_compiled_catalog, CATALOGS_DIR, clear_catalog_memory_cache

        clear_catalog_memory_cache()
        for slug in ("black", "black_national", "white", "white_national", "black-2", "black-2_national"):
            by_nid = {e.pokemon.national_number: e for e in get_compiled_catalog(slug, force_reload=True)}
            self.assertNotIn("surf", by_nid[638].filter_tags.split(), f"Cobalion no debe tener tag 'surf' en {slug}")

        for p in sorted(CATALOGS_DIR.glob("*.json")):
            slug = p.stem
            for e in get_compiled_catalog(slug):
                tags = set(e.filter_tags.split())
                obt = e.obtaining_info or {}
                methods_lower = " ".join(l.get("method", "").lower() for l in (obt.get("locations") or []))
                if "surf" in tags:
                    self.assertIn("surf", methods_lower, f"{slug} #{e.pokemon.national_number} tiene 'surf' sin método Surf")
                if tags & {"rod_old", "rod_good", "rod_super", "rod_any"}:
                    self.assertNotEqual(obt.get("type"), "trade", f"{slug} #{e.pokemon.national_number} trade con tag rod_*")
                    self.assertNotEqual(obt.get("type"), "transfer", f"{slug} #{e.pokemon.national_number} transfer con tag rod_*")


class PokemonBlack2Gen5Tests(TestCase):
    """Batería integral de validación para Pokémon Negro 2 (slug 'black-2', Gen 5)."""

    def test_black2_catalog_structure_ids_and_historical_types(self):
        from tracker.catalog_service import get_compiled_catalog, clear_catalog_memory_cache, ensure_all_catalogs_loaded
        from tracker.models import Game

        ensure_all_catalogs_loaded()
        clear_catalog_memory_cache()

        game = Game.objects.get(slug="black-2")
        self.assertEqual(game.generation, 5)
        self.assertTrue(game.has_retro_sprites)
        self.assertTrue(game.has_swarms)
        self.assertTrue(game.has_seasons)
        self.assertTrue(game.has_special_spots)
        self.assertTrue(game.has_hidden_grottos)
        self.assertTrue(game.has_regional_babies)
        self.assertFalse(game.has_time_of_day)

        # No regresión en Negro/Blanco 1
        black1 = Game.objects.get(slug="black")
        white1 = Game.objects.get(slug="white")
        self.assertFalse(black1.has_hidden_grottos)
        self.assertFalse(white1.has_hidden_grottos)
        self.assertFalse(black1.has_regional_babies)
        self.assertFalse(white1.has_regional_babies)

        reg = get_compiled_catalog("black-2", force_reload=True, is_national=False)
        nat = get_compiled_catalog("black-2", force_reload=True, is_national=True)
        self.assertEqual(len(reg), 301)
        self.assertEqual(len(nat), 649)

        # Victini #000 y rangos de ID disjuntos (10000..10300 y 10401..11049)
        victini = reg[0]
        self.assertEqual(victini.id, 10000)
        self.assertEqual(victini.entry_number, 494)
        self.assertEqual(victini.display_number, "000")
        self.assertEqual(victini.pokemon.national_number, 494)
        self.assertEqual([e.id for e in reg[1:]], list(range(10001, 10301)))
        self.assertEqual([e.id for e in nat], list(range(10401, 11050)))

        # Fidelidad histórica estricta Gen 5: cero tipo Hada + is_hatchable explícito + 201-f.png en HOME
        for e in nat:
            self.assertNotEqual(e.primary_type, "fairy")
            self.assertNotEqual(e.secondary_type, "fairy")
            self.assertIsNotNone(e.is_hatchable)

        nat_by = {e.pokemon.national_number: e for e in nat}
        self.assertTrue(nat_by[489].is_hatchable)  # Phione
        self.assertEqual(nat_by[201].pokemon.sprite_shiny_url, "/media/pokemon/home/shiny/201-f.png")
        self.assertEqual(nat_by[201].modern_sprite_shiny_url, "/media/pokemon/home/shiny/201-f.png")

    def test_black2_exclusives_transfers_and_hub_classification(self):
        from tracker.catalog_service import get_compiled_catalog
        from tracker.exclusives import (
            VERSION_EXCLUSIVES_CATALOG,
            VERSION_TRANSFERS_CATALOG,
            GAME_VERSION_EXCLUSIVES_NOTICES,
            get_version_exclusives_context,
            get_version_transfers_context,
        )
        from tracker.models import Game
        from tracker.views import _classify_catalog_for_game

        b2_excl = VERSION_EXCLUSIVES_CATALOG["black-2"]
        w2_excl = VERSION_EXCLUSIVES_CATALOG["white-2"]
        self.assertEqual(len(b2_excl), 29)
        self.assertEqual(len(w2_excl), 26)
        self.assertEqual(set(b2_excl) & set(w2_excl), set())

        # Volbeat, Illumise, Cottonee y Petilil NO son exclusivos en B2W2
        for non_excl in (313, 314, 546, 547, 548, 549):
            self.assertNotIn(non_excl, b2_excl)
            self.assertNotIn(non_excl, w2_excl)

        game = Game.objects.get(slug="black-2")
        reg_pd = game.pokedexes.get(slug="unova")
        nat_pd = game.pokedexes.get(slug="national")

        excl_ctx = get_version_exclusives_context(game, reg_pd, set())
        self.assertTrue(excl_ctx["has_exclusives"])
        self.assertEqual(excl_ctx["counterpart_theme"], "white2")
        self.assertEqual(excl_ctx["own_theme"], "black2")
        self.assertEqual(excl_ctx["counterpart_total"], 26)
        self.assertEqual(excl_ctx["own_total"], 29)
        self.assertIn("Sistema Clave", GAME_VERSION_EXCLUSIVES_NOTICES["black-2"])

        # Transferencias estrictamente Gen 1-4 (0 especies de Gen 5, incluidos Tornadus/Thundurus/Landorus)
        b2_transfers = VERSION_TRANSFERS_CATALOG["black-2"]
        self.assertTrue(all(n < 494 for n in b2_transfers))
        for gen5_id in (494, 641, 642, 645, 646, 647):
            self.assertNotIn(gen5_id, b2_transfers)
        self.assertIsNone(get_version_transfers_context(game, reg_pd, set()))
        nat_tr_ctx = get_version_transfers_context(game, nat_pd, set())
        self.assertTrue(nat_tr_ctx["has_transfers"])
        self.assertEqual(nat_tr_ctx["total"], len(b2_transfers))
        self.assertIn("Dream World", nat_tr_ctx["historical_note"])
        self.assertIn("RAdar Pokémon", nat_tr_ctx["historical_note"])

        # Clasificación nativa en el Game Hub
        nat = get_compiled_catalog("black-2", is_national=True)
        cls = _classify_catalog_for_game(nat, "black-2")
        for grotto_native in (29, 32, 149, 371):  # Nidoran♀/♂, Dragonite, Bagon en Claros Ocultos
            self.assertTrue(cls[grotto_native][0], f"#{grotto_native} de Claro Oculto debe ser nativo en Negro 2")
        for w2_only in (577, 627, 643):  # Solosis, Rufflet, Reshiram exclusivos de Blanco 2
            self.assertFalse(cls[w2_only][0], f"#{w2_only} exclusivo de Blanco 2 no debe ser nativo en Negro 2")

    def test_black2_new_forms_and_isolation_from_bw1(self):
        from pathlib import Path
        from django.conf import settings
        from tracker.pokemon_forms import get_pokemon_forms

        expected_counts = {641: 2, 642: 2, 645: 2, 646: 3, 647: 2}
        for nid, count in expected_counts.items():
            self.assertEqual(get_pokemon_forms(nid, "black"), [], f"#{nid} no debe exponer formas B2W2 en Negro 1")
            self.assertEqual(get_pokemon_forms(nid, "white"), [], f"#{nid} no debe exponer formas B2W2 en Blanco 1")
            forms = get_pokemon_forms(nid, "black-2")
            self.assertEqual(len(forms), count, f"#{nid} debe tener {count} formas en Negro 2")
            for form in forms:
                for key in ("sprite_retro", "sprite_retro_shiny", "modal_retro_sprite_url", "modal_retro_sprite_shiny_url", "sprite_modern", "sprite_modern_shiny"):
                    url = form[key]
                    self.assertTrue((Path(settings.BASE_DIR) / url.lstrip("/")).exists(), f"Falta {url}")

        # Giratina en Torre Duodraco y Genesect con los 4 ROMs en Negro 2
        giratina_forms = get_pokemon_forms(487, "black-2")
        self.assertIn("Torre Duodraco", str(giratina_forms))
        genesect_forms = get_pokemon_forms(649, "black-2")
        self.assertEqual(len(genesect_forms), 5)
        self.assertIn("Laboratorio P+P", str(genesect_forms))

    def test_black2_hidden_grottos_swarms_gifts_statics_npcs_and_stones(self):
        from tracker.catalog_service import get_compiled_catalog
        from tracker.utils import get_evolution_stones_catalog, resolve_evolution_stone, INCENSE_BABY_MAP

        reg_by = {e.pokemon.national_number: e for e in get_compiled_catalog("black-2", is_national=False)}
        nat_by = {e.pokemon.national_number: e for e in get_compiled_catalog("black-2", is_national=True)}

        # Claros Ocultos: etiqueta hidden_grotto sin contaminar 'surf'
        for hg_id in (371, 572, 149):  # Bagon, Minccino, Dragonite
            self.assertIn("hidden_grotto", nat_by[hg_id].filter_tags.split())
        self.assertNotIn("surf", nat_by[371].filter_tags.split())
        self.assertNotIn("surf", nat_by[572].filter_tags.split())

        # Manadas solo en Nacional (19 especies)
        swarms_nat = [e for e in nat_by.values() if "swarm" in e.filter_tags.split()]
        self.assertEqual(len(swarms_nat), 19)
        self.assertEqual([e for e in reg_by.values() if "swarm" in e.filter_tags.split()], [])

        # Regalos, estáticos e intercambios NPC canónicos de Negro 2
        self.assertIn("Ruga", reg_by[570].obtaining_info["summary"])  # Zorua de N
        self.assertIn("Trufa", reg_by[133].obtaining_info["summary"])  # Eevee en Ciudad Porcelana
        self.assertIn("Guayo", nat_by[443].obtaining_info["summary"])  # Gible variocolor
        self.assertIn("Reserva Natural", reg_by[612].obtaining_info["summary"])  # Haxorus variocolor
        self.assertIn("jueves", reg_by[630].obtaining_info["summary"].lower())  # Mandibuzz Ruta 4
        self.assertIn("Pettulip", reg_by[548].obtaining_info["summary"])  # Petilil intercambio Ruta 4

        # Inciensos resueltos en Regional (#298 Azurill, #458 Mantyke) y los 9 bebés en Nacional
        self.assertEqual(reg_by[298].evolution_stone["slug"], "sea-incense")
        self.assertEqual(reg_by[458].evolution_stone["slug"], "wave-incense")
        for baby_id, expected_incense in INCENSE_BABY_MAP.items():
            self.assertEqual(nat_by[baby_id].evolution_stone["slug"], expected_incense)

        # Todos los 42 objetos evolutivos tienen games["black-2"] y precios/notas exactos de B2W2
        stones = get_evolution_stones_catalog(force_reload=True)
        self.assertEqual(len(stones), 42)
        for slug, item in stones.items():
            b2_locs = item.get("games", {}).get("black-2", [])
            self.assertTrue(b2_locs, f"Falta games['black-2'] en {slug}")

        sea_inc = resolve_evolution_stone(item_slug="sea-incense", game_slug="black-2")
        self.assertNotIn("post-game", sea_inc["availability_note"].lower())
        claw = resolve_evolution_stone(item_slug="razor-claw", game_slug="black-2")
        self.assertIn("8 PB", claw["availability_note"])
        self.assertIn("Pokémon World Tournament", claw["availability_note"])

    def test_black2_views_ui_palette_toolbar_and_unown(self):
        from tracker.unown_data import get_game_unown_chambers, get_unown_catalog

        self.assertEqual(get_game_unown_chambers("black-2"), {})
        uc = get_unown_catalog("black-2")
        self.assertEqual(len(uc), 28)
        self.assertEqual(uc[0]["sprite_normal"], "/media/pokemon/sprites/black-2/unown/a.png")

        res_reg = self.client.get("/black-2/")
        self.assertEqual(res_reg.status_code, 200)
        self.assertEqual(len(res_reg.context["entries"]), 301)
        html_reg = res_reg.content.decode("utf-8")
        self.assertIn('data-game="black-2"', html_reg)
        self.assertIn("/media/pokemon/icons/gen5/10022.png", html_reg)
        self.assertIn("bg-[#0f172a]", html_reg)
        self.assertIn('data-tag="hidden_grotto"', html_reg)
        self.assertIn("Claros Ocultos", html_reg)
        self.assertIn('data-tag="baby"', html_reg)
        self.assertNotIn('id="btn-game-config"', html_reg)

        res_nat = self.client.get("/black-2/national/")
        self.assertEqual(res_nat.status_code, 200)
        self.assertEqual(res_nat.context["total_pokemon"], 649)
        html_nat = res_nat.content.decode("utf-8")
        self.assertIn("Teselia (Pokétransfer)", html_nat)
        self.assertIn('data-tag="hidden_grotto"', html_nat)
        self.assertIn('data-tag="swarm"', html_nat)
        self.assertIn("bg-sky-500/25 text-sky-200 border-sky-400/50", html_nat)

        # Claros Ocultos no aparece en Negro 1 ni Blanco 1
        for bw1_url in ("/black/", "/white/"):
            resp_bw1 = self.client.get(bw1_url)
            self.assertNotIn('data-tag="hidden_grotto"', resp_bw1.content.decode("utf-8"))

        # Game Hub muestra Kyurem Negro
        res_hub = self.client.get("/games/")
        self.assertEqual(res_hub.status_code, 200)
        self.assertIn("Kyurem Negro", res_hub.content.decode("utf-8"))













