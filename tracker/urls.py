from django.urls import path
from . import views

app_name = "tracker"

urlpatterns = [
    path("", views.pokedex_view, name="home"),
    path("<slug:game_slug>/", views.pokedex_view, name="pokedex_default"),
    path("<slug:game_slug>/<slug:pokedex_slug>/", views.pokedex_view, name="pokedex_detail"),
    path("api/catch/toggle/", views.toggle_catch, name="toggle_catch"),
    path("api/unown-catch/toggle/", views.toggle_unown_catch, name="toggle_unown_catch"),
]
