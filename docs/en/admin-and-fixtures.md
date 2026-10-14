# 🛡️ Admin Panel & Metadata Fixtures (English)

## 1. Django Admin Architecture

The administration portal located at `/admin/` provides supervision of registered games, Pokédex sections, and live user catch activity.

### 1.1 Registered ModelAdmins in `tracker/admin.py`
* **`GameAdmin`**:
  * List display: `name`, `slug`, `generation`, `created_at`.
  * Automatic slug pre-population from game title.
  * Filtering by generation and title search.
* **`PokedexAdmin`**:
  * List display: `name`, `game`, `slug`, `is_national`, `pokeapi_name`.
  * Filtering by parent game and National Pokédex flag.
* **`UserPokemonCatchAdmin`**:
  * Live monitoring of catch records: `user`, `session_key`, `game_slug`, `entry_number`, `entry_id`, `is_caught`, `is_shiny`, `caught_at`.
  * Filters for regular catch state, shiny status, and game edition.

---

## 2. Structural Game Metadata Fixtures (`fixtures_util.py`)

The `tracker/fixtures_util.py` module manages exporting game and pokedex structural definitions for Git version control.

> [!IMPORTANT]
> **Backup Scope:** The fixture exporter strictly backs up metadata from `tracker.Game` and `tracker.Pokedex`.  
> It does not include user catch progress (`UserPokemonCatch`, which resides in the production database) or species data (which is managed as static JSON files under `tracker/data/catalogs/`).

### 2.1 One-Click Admin Exporter
Superusers can export game fixtures directly from the administration dashboard:
* **Endpoint:** `/admin/tracker/export-fixtures/` (protected `POST` action, superuser-only).
* **Destination:** `tracker/fixtures/pokedex_entries.json` in UTF-8 encoding with 2-space indentation.
* **Status Badge:** The admin header displays live information about fixture existence, file size, last modified timestamp, and total exported records.

### 2.2 Restoring Fixtures via CLI
To seed a clean database instance with the registered games and dexes:
```bash
python manage.py loaddata tracker/fixtures/pokedex_entries.json
```
