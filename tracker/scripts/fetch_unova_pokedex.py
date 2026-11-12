"""
Script para descargar y consolidar el orden canónico de la Pokédex Regional de Teselia (156 especies)
para Pokémon Negro desde PokeAPI (Pokedex: original-unova).
Genera: tracker/data/cache/unova_pokedex_156.json
"""
import json
import urllib.request
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
CACHE_FILE = BASE_DIR / "tracker" / "data" / "cache" / "unova_pokedex_156.json"
USER_AGENT = "PokedexGlobal/1.0 (Educational/Collector Tool; https://github.com/Gatozo/pokedexglobal)"


def fetch_original_unova():
    print("Descargando Pokédex Regional de Teselia Original (156 especies) desde PokeAPI...")
    url = "https://pokeapi.co/api/v2/pokedex/original-unova/"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=20) as resp:
        data = json.loads(resp.read().decode("utf-8"))

    unova_156 = {}
    for entry in data.get("pokemon_entries", []):
        entry_num = str(entry["entry_number"])
        species_url = entry["pokemon_species"]["url"]
        nat_id = int(species_url.strip("/").split("/")[-1])
        unova_156[entry_num] = nat_id

    CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(unova_156, f, indent=2, ensure_ascii=False)

    print(f"Éxito: {len(unova_156)} entradas guardadas en {CACHE_FILE}")


if __name__ == "__main__":
    fetch_original_unova()
