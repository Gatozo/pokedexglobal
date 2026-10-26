"""
Script para descargar y consolidar el orden canónico de la Pokédex Regional de Sinnoh Expandida (210 especies)
para Pokémon Platino desde PokeAPI (Pokedex ID 6: extended-sinnoh).
Genera: tracker/data/cache/sinnoh_pokedex_210.json
"""
import json
import urllib.request
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
CACHE_FILE = BASE_DIR / "tracker" / "data" / "cache" / "sinnoh_pokedex_210.json"
USER_AGENT = "PokedexGlobal/1.0 (Educational/Collector Tool; https://github.com/Gatozo/pokedexglobal)"


def fetch_extended_sinnoh():
    print("Descargando Pokédex Regional de Sinnoh Expandida (210 especies) desde PokeAPI...")
    url = "https://pokeapi.co/api/v2/pokedex/6/"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=20) as resp:
        data = json.loads(resp.read().decode("utf-8"))

    sinnoh_210 = {}
    for entry in data.get("pokemon_entries", []):
        entry_num = str(entry["entry_number"])
        species_url = entry["pokemon_species"]["url"]
        # url format: https://pokeapi.co/api/v2/pokemon-species/<id>/
        nat_id = int(species_url.strip("/").split("/")[-1])
        sinnoh_210[entry_num] = nat_id

    CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(sinnoh_210, f, indent=2, ensure_ascii=False)

    print(f"Éxito: {len(sinnoh_210)} entradas guardadas en {CACHE_FILE}")


if __name__ == "__main__":
    fetch_extended_sinnoh()
