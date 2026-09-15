# ⚙️ Management Commands Reference (English)

Django management commands located under `tracker/management/commands/` automate the ingestion, enrichment, and maintenance of the Pokédex database.

---

## 1. Commands Summary

| Command | File | Description |
| :--- | :--- | :--- |
| `import_pokedex` | `import_pokedex.py` | Imports a game and regional Pokédex from PokeAPI, creates `Game`, `Pokedex`, `Pokemon`, and `PokedexEntry` records, and downloads sprites to `media/`. |
| `sync_pokemon_cache` | `sync_pokemon_cache.py` | Synchronizes and writes raw PokeAPI JSON (`raw_data`) into all local `Pokemon` rows. |
| `sync_pokemon_details` | `sync_pokemon_details.py` | Enriches entries with generation-specific stats, moves, encounter zones, and Spanish flavor texts using an Offline-First cache. |
| `sync_moves` | `sync_moves.py` | Downloads combat moves (e.g. 1-165 for Gen 1) with Spanish names, damage classes, PP, and power. |
| `backfill_pokedex_types` | `backfill_pokedex_types.py` | Audits and updates all `PokedexEntry` records with generation-accurate historical typings (`past_types`). |

---

## 2. Detailed Command Specifications

### 2.1 `import_pokedex`
Downloads a game and regional Pokédex from PokeAPI, stores basic info, and resolves localized game titles.

```bash
python manage.py import_pokedex [options]
```

#### Arguments & Options:
- `--game <slug>`: Game slug identifier (default: `"red"`). Example: `blue`, `yellow`, `gold`, `firered`.
- `--game-name <name>`: Optional descriptive name. If omitted, the official Spanish name is looked up from `GAME_NAMES_ES`.
- `--generation <int>`: Integer generation number (default: `1`).
- `--pokedex <slug>`: PokeAPI regional dex slug (default: `"kanto"`). Example: `original-johto`, `hoenn`, `national`.
- `--pokedex-name <name>`: Human-readable dex title (default: `"Pokédex Regional de Kanto"`).
- `--force-refresh`: If present, forces re-downloading from PokeAPI even if species already exist locally.
- `--workers <int>`: ThreadPoolExecutor concurrency worker count (default: `4`).
- `--delay <float>`: Polite pacing delay in seconds between network requests (default: `0.05`).

#### Example Usage:
```bash
# Ingest Pokémon Red (Kanto Regional Pokédex)
python manage.py import_pokedex --game red --generation 1 --pokedex kanto --workers 4

# Ingest Pokémon Silver (Generation 2, Johto)
python manage.py import_pokedex --game silver --generation 2 --pokedex original-johto --pokedex-name "Pokédex de Johto"
```

---

### 2.2 `sync_pokemon_cache`
Populates or refreshes the `raw_data` JSONField on the `Pokemon` table. This raw data contains cry audio paths, species associations, and modern type mappings.

```bash
python manage.py sync_pokemon_cache [options]
```

#### Arguments & Options:
- `--all`: Forces update of `raw_data` for all Pokémon, even those that already have data populated.
- `--workers <int>`: Thread count for concurrent requests (default: `4`).
- `--delay <float>`: Delay between requests (default: `0.05`).

#### Example Usage:
```bash
python manage.py sync_pokemon_cache --workers 6
```

---

### 2.3 `sync_pokemon_details`
Performs deep enrichment of `PokedexEntry` records for a specified game. It aggregates:
- Official Spanish flavor text (`flavor_text`).
- In-game encounter locations and biomes (`obtaining_info`).
- Generation-specific level-up moves and stats (`game_data`).
- Genus / category name (`Pokemon.category`).

> **Safety Guarantee**: Entries marked with `is_custom_override = True` are skipped to protect manual modifications made via Django Admin.

```bash
python manage.py sync_pokemon_details [options]
```

#### Arguments & Options:
- `--game <slug>`: The game slug to process (default: `"red"`).
- `--workers <int>`: Concurrency worker count (default: `5`).
- `--delay <float>`: Network request delay (default: `0.05`).

#### Example Usage:
```bash
# Sync detailed info for Pokémon Red
python manage.py sync_pokemon_details --game red --workers 5
```

---

### 2.4 `sync_moves`
Populates the `Move` table with official stats, power, accuracy, PP, effect descriptions, and Spanish localizations.

```bash
python manage.py sync_moves [options]
```

#### Arguments & Options:
- `--generation <int>`: Generation number to import (default: `1`, corresponding to moves 1 through 165).
- `--workers <int>`: Concurrency workers (default: `10`).
- `--local`: Prioritizes loading from offline cached files (e.g. `tracker/data/moves_gen1.json`) before falling back to PokeAPI network calls.

#### Example Usage:
```bash
# Fast offline import of Generation 1 moves
python manage.py sync_moves --generation 1 --local
```

---

### 2.5 `backfill_pokedex_types`
Iterates over all existing `PokedexEntry` rows across all games and recalculates historical typings based on `resolve_types_for_generation()`.

```bash
python manage.py backfill_pokedex_types
```

#### Behavior:
- Checks each Pokémon's `past_types` array in `raw_data`.
- If a game's generation was before a type change (e.g. Magnemite before Gen 2, or Clefairy/Togepi/Jigglypuff before Gen 6), sets `primary_type` and `secondary_type` to their vintage equivalents.
- Executes updates within an atomic database transaction.

#### Example Usage:
```bash
python manage.py backfill_pokedex_types
```
