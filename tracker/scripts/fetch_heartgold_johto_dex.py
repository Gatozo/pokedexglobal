"""
Script para descargar y consolidar el orden canónico de la Pokédex de Johto Actualizada (256 especies)
para Pokémon Oro HeartGold desde PokeAPI (Pokedex ID 7: updated-johto).
Genera: tracker/data/cache/johto_updated_pokedex_256.json
"""
import json
import urllib.request
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
CACHE_FILE = BASE_DIR / "tracker" / "data" / "cache" / "johto_updated_pokedex_256.json"
USER_AGENT = "PokedexGlobal/1.0 (Educational/Collector Tool; https://github.com/Gatozo/pokedexglobal)"


def fetch_updated_johto():
    print("Descargando Pokédex de Johto Actualizada (256 especies) desde PokeAPI...")
    url = "https://pokeapi.co/api/v2/pokedex/7/"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=25) as resp:
        data = json.loads(resp.read().decode("utf-8"))

    johto_256 = {}
    for entry in data.get("pokemon_entries", []):
        entry_num = str(entry["entry_number"])
        species_url = entry["pokemon_species"]["url"]
        # url format: https://pokeapi.co/api/v2/pokemon-species/<id>/
        nat_id = int(species_url.strip("/").split("/")[-1])
        johto_256[entry_num] = nat_id

    CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(johto_256, f, indent=2, ensure_ascii=False)

    print(f"Éxito: {len(johto_256)} entradas guardadas en {CACHE_FILE}")
    if len(johto_256) != 256:
        print(f"ADVERTENCIA: Se esperaban 256 especies y se descargaron {len(johto_256)}")


if __name__ == "__main__":
    fetch_updated_johto()
