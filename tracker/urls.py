from django.urls import path
from . import views

app_name = "tracker"

urlpatterns = [
    path("", views.auth_portal_view, name="home"),
    path("login/", views.auth_portal_view, name="login"),
    path("register/", views.register_view, name="register"),
    path("guest/", views.guest_continue_view, name="guest_continue"),
    path("logout/", views.logout_view, name="logout"),
    path("<slug:game_slug>/", views.pokedex_view, name="pokedex_default"),
    path("<slug:game_slug>/<slug:pokedex_slug>/", views.pokedex_view, name="pokedex_detail"),
    path("api/catch/toggle/", views.toggle_catch, name="toggle_catch"),
    path("api/unown-catch/toggle/", views.toggle_unown_catch, name="toggle_unown_catch"),
    path("api/auth/check-username/", views.check_username, name="check_username"),
]


