from django.test import TestCase, Client
from django.contrib.auth import get_user_model, authenticate
from django.urls import reverse
from tracker.models import Game, Pokedex, UserPokemonCatch
from tracker.forms import HybridLoginForm, UserRegisterForm
from tracker.views import merge_session_catches_to_user

User = get_user_model()


class AuthenticationBackendTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="AshKetchum",
            email="ash@pueblopaleta.com",
            password="PikachuPassword123!"
        )

    def test_authenticate_with_username_exact(self):
        user = authenticate(username="AshKetchum", password="PikachuPassword123!")
        self.assertIsNotNone(user)
        self.assertEqual(user.pk, self.user.pk)

    def test_authenticate_with_username_case_insensitive(self):
        user = authenticate(username="ashketchum", password="PikachuPassword123!")
        self.assertIsNotNone(user)
        self.assertEqual(user.pk, self.user.pk)

    def test_authenticate_with_email_exact(self):
        user = authenticate(username="ash@pueblopaleta.com", password="PikachuPassword123!")
        self.assertIsNotNone(user)
        self.assertEqual(user.pk, self.user.pk)

    def test_authenticate_with_email_case_insensitive(self):
        user = authenticate(username="ASH@PuebloPaleta.COM", password="PikachuPassword123!")
        self.assertIsNotNone(user)
        self.assertEqual(user.pk, self.user.pk)

    def test_authenticate_with_wrong_password(self):
        user = authenticate(username="AshKetchum", password="WrongPassword999!")
        self.assertIsNone(user)

    def test_authenticate_inactive_user(self):
        self.user.is_active = False
        self.user.save()
        user = authenticate(username="AshKetchum", password="PikachuPassword123!")
        self.assertIsNone(user)


class AuthenticationFormsTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="MistyWater",
            email="misty@cerulean.com",
            password="StarmiePassword123!"
        )

    def test_login_form_valid_with_username(self):
        form = HybridLoginForm(data={"identifier": "mistywater", "password": "StarmiePassword123!"})
        self.assertTrue(form.is_valid())
        self.assertEqual(form.get_user().pk, self.user.pk)

    def test_login_form_valid_with_email(self):
        form = HybridLoginForm(data={"identifier": "MISTY@cerulean.com", "password": "StarmiePassword123!"})
        self.assertTrue(form.is_valid())
        self.assertEqual(form.get_user().pk, self.user.pk)

    def test_login_form_invalid_credentials(self):
        form = HybridLoginForm(data={"identifier": "mistywater", "password": "wrong"})
        self.assertFalse(form.is_valid())
        self.assertIn("Usuario/correo o contraseña incorrectos", form.errors["__all__"][0])

    def test_register_form_valid(self):
        form = UserRegisterForm(data={
            "username": "BrockGym",
            "email": "brock@pewter.com",
            "password": "OnixPassword123!",
            "password_confirm": "OnixPassword123!",
        })
        self.assertTrue(form.is_valid())
        new_user = form.save()
        self.assertEqual(new_user.username, "BrockGym")
        self.assertEqual(new_user.email, "brock@pewter.com")

    def test_register_form_passwords_mismatch(self):
        form = UserRegisterForm(data={
            "username": "BrockGym",
            "email": "brock@pewter.com",
            "password": "OnixPassword123!",
            "password_confirm": "DifferentPassword123!",
        })
        self.assertFalse(form.is_valid())
        self.assertIn("password_confirm", form.errors)

    def test_register_form_duplicate_username_case_insensitive(self):
        form = UserRegisterForm(data={
            "username": "mistywater",
            "email": "other@cerulean.com",
            "password": "ValidPassword123!",
            "password_confirm": "ValidPassword123!",
        })
        self.assertFalse(form.is_valid())
        self.assertIn("username", form.errors)

    def test_register_form_duplicate_email_case_insensitive(self):
        form = UserRegisterForm(data={
            "username": "DifferentUser",
            "email": "MISTY@CERULEAN.COM",
            "password": "ValidPassword123!",
            "password_confirm": "ValidPassword123!",
        })
        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)

    def test_register_form_simple_password_allowed(self):
        form = UserRegisterForm(data={
            "username": "SimpleTrainer",
            "email": "simple@paleta.com",
            "password": "1234",
            "password_confirm": "1234",
        })
        self.assertTrue(form.is_valid())
        user = form.save()
        self.assertTrue(user.check_password("1234"))

    def test_register_form_password_too_long(self):
        form = UserRegisterForm(data={
            "username": "LongTrainer",
            "email": "long@paleta.com",
            "password": "a" * 33,
            "password_confirm": "a" * 33,
        })
        self.assertFalse(form.is_valid())
        self.assertIn("password", form.errors)

    def test_register_form_password_too_short(self):
        form = UserRegisterForm(data={
            "username": "ShortTrainer",
            "email": "short@paleta.com",
            "password": "123",
            "password_confirm": "123",
        })
        self.assertFalse(form.is_valid())
        self.assertIn("password", form.errors)



class ViewsAndFlowTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.game_red, _ = Game.objects.get_or_create(slug="red", defaults={"name": "Pokémon Red", "generation": 1})
        self.game_crystal, _ = Game.objects.get_or_create(slug="crystal", defaults={"name": "Pokémon Crystal", "generation": 2})
        self.pokedex_red, _ = Pokedex.objects.get_or_create(game=self.game_red, slug="kanto", defaults={"name": "Kanto"})
        self.pokedex_crystal, _ = Pokedex.objects.get_or_create(game=self.game_crystal, slug="johto", defaults={"name": "Johto"})

        self.user = User.objects.create_user(
            username="RedTrainer",
            email="red@indigo.com",
            password="ChampionPassword123!"
        )

    def test_root_renders_auth_portal(self):
        response = self.client.get(reverse("tracker:home"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "tracker/auth.html")
        self.assertContains(response, "Iniciar Sesión")
        self.assertContains(response, "Crear Cuenta")
        self.assertContains(response, "Modo Invitado")

    def test_guest_continue_defaults_to_red(self):
        response = self.client.get(reverse("tracker:guest_continue"))
        self.assertRedirects(response, "/red/")

    def test_login_post_with_email(self):
        response = self.client.post(reverse("tracker:home"), {
            "action": "login",
            "identifier": "red@indigo.com",
            "password": "ChampionPassword123!",
        })
        self.assertRedirects(response, "/red/")
        # Verificar que la sesión está autenticada
        self.assertEqual(int(self.client.session["_auth_user_id"]), self.user.pk)

    def test_register_post_creates_and_logs_in(self):
        response = self.client.post(reverse("tracker:home"), {
            "action": "register",
            "username": "BlueRival",
            "email": "blue@oaklabs.com",
            "password": "RivalPassword123!",
            "password_confirm": "RivalPassword123!",
        })
        self.assertRedirects(response, "/red/")
        new_user = User.objects.get(username="BlueRival")
        self.assertEqual(int(self.client.session["_auth_user_id"]), new_user.pk)

    def test_logout_redirects_to_home(self):
        self.client.login(username="RedTrainer", password="ChampionPassword123!")
        response = self.client.get(reverse("tracker:logout"))
        self.assertRedirects(response, reverse("tracker:home"))
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_remember_last_game_visited(self):
        # Visitar Pokémon Cristal
        self.client.get(reverse("tracker:pokedex_default", kwargs={"game_slug": "crystal"}))
        self.assertEqual(self.client.session.get("last_game_slug"), "crystal")

        # Ahora guest continue debe redirigir a /crystal/
        response = self.client.get(reverse("tracker:guest_continue"))
        self.assertRedirects(response, "/crystal/")

    def test_user_progress_isolation(self):
        user_a = User.objects.create_user(username="TrainerA", password="Password123!")
        user_b = User.objects.create_user(username="TrainerB", password="Password123!")

        # User A catches Bulbasaur (#1)
        UserPokemonCatch.objects.create(
            user=user_a,
            game_slug="red",
            entry_number=1,
            entry_id=1,
            is_caught=True
        )

        # User B catches Charmander (#4)
        UserPokemonCatch.objects.create(
            user=user_b,
            game_slug="red",
            entry_number=4,
            entry_id=4,
            is_caught=True
        )

        # Login as User A and view Red
        self.client.login(username="TrainerA", password="Password123!")
        res_a = self.client.get(reverse("tracker:pokedex_default", kwargs={"game_slug": "red"}))
        self.assertEqual(res_a.context["caught_count"], 1)
        self.assertIn(1, res_a.context["caught_entry_ids"])
        self.assertNotIn(4, res_a.context["caught_entry_ids"])

        # Switch to User B
        self.client.login(username="TrainerB", password="Password123!")
        res_b = self.client.get(reverse("tracker:pokedex_default", kwargs={"game_slug": "red"}))
        self.assertEqual(res_b.context["caught_count"], 1)
        self.assertIn(4, res_b.context["caught_entry_ids"])
        self.assertNotIn(1, res_b.context["caught_entry_ids"])

    def test_merge_guest_catches_on_registration(self):
        # Un invitado navega y captura a Pikachu (#25)
        self.client.get(reverse("tracker:pokedex_default", kwargs={"game_slug": "red"}))
        session_key = self.client.session.session_key

        UserPokemonCatch.objects.create(
            session_key=session_key,
            game_slug="red",
            entry_number=25,
            entry_id=25,
            is_caught=True
        )

        # El invitado decide registrarse
        self.client.post(reverse("tracker:home"), {
            "action": "register",
            "username": "YellowTrainer",
            "email": "yellow@viridian.com",
            "password": "PikaPikaPassword123!",
            "password_confirm": "PikaPikaPassword123!",
        })

        new_user = User.objects.get(username="YellowTrainer")
        # Verificar que la captura anónima ahora pertenece a YellowTrainer
        user_catches = UserPokemonCatch.objects.filter(user=new_user, game_slug="red", entry_number=25)
        self.assertTrue(user_catches.exists())
        self.assertTrue(user_catches.first().is_caught)

        # Verificar que no quedan capturas anónimas para esa sesión
        anon_remaining = UserPokemonCatch.objects.filter(session_key=session_key, user__isnull=True)
        self.assertEqual(anon_remaining.count(), 0)

    def test_check_username_available(self):
        res = self.client.get(reverse("tracker:check_username"), {"username": "ProfOak"})
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data["available"])
        self.assertTrue(data["valid_format"])

    def test_check_username_taken_case_insensitive(self):
        res = self.client.get(reverse("tracker:check_username"), {"username": "redtrainer"})
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertFalse(data["available"])
        self.assertTrue(data["valid_format"])
        self.assertIn("ya no está disponible", data["message"])

    def test_check_username_too_short(self):
        res = self.client.get(reverse("tracker:check_username"), {"username": "pk"})
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertFalse(data["available"])
        self.assertFalse(data["valid_format"])
        self.assertIn("al menos 3 caracteres", data["message"])

    def test_check_username_invalid_chars(self):
        res = self.client.get(reverse("tracker:check_username"), {"username": "red kanto!"})
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertFalse(data["available"])
        self.assertFalse(data["valid_format"])
        self.assertIn("Solo se permiten letras", data["message"])

