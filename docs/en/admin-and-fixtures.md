# 🛡️ Admin Customizations & Fixtures Guide (English)

## 1. Django Admin Architecture

The administration portal located at `/admin/` provides tools for curating Pokémon game metadata and managing user capture records.

### 1.1 Model Admin Configuration
- **`PokedexEntryAdmin`**:
  - `list_editable = ('is_custom_override',)`: Enables inline toggling of the override protection flag directly from the change list table.
  - `readonly_fields = ('pokedex', 'pokemon', 'entry_number')`: Locks primary structural relations to prevent accidental unlinking.
  - Filters by Game, Pokédex, and Type.
- **`PokemonAdmin`**:
  - Display columns: National Number, Display Name, Primary Type, Secondary Type.
  - Searchable by name, display name, and number.
- **`GameAdmin`**:
  - Auto-populates `slug` from `name`.
  - Filterable by generation.
- **`UserPokemonCatchAdmin`**:
  - Monitors live user capture activities with filters for caught status and Pokédex.

---

## 2. Manual Override Protection (`is_custom_override`)

When ingesting community contributions or custom romhack mechanics:
1. An administrator edits a `PokedexEntry` (e.g. setting an exclusive event encounter location in `obtaining_info` or a custom Spanish description).
2. The administrator sets `is_custom_override = True`.
3. When automated CLI jobs (such as `sync_pokemon_details`) run, any entry with `is_custom_override = True` is skipped.
4. This architecture guarantees that automated crawlers will never obliterate human-curated edits.

---

## 3. Fixture Management & Backup Tooling

The module `tracker/fixtures_util.py` handles database serialization and state verification.

### 3.1 One-Click Admin Fixture Exporter
Superusers have access to a one-click fixture export button in the Django Admin header:
- Injected via monkey-patching `admin.site.get_urls()` and `admin.site.each_context()`.
- Endpoint: `/admin/tracker/export-fixtures/` (`POST` method, superuser authorization required).
- Dumps: `tracker.Game`, `tracker.Pokedex`, and `tracker.PokedexEntry`.
- Destination: `tracker/fixtures/pokedex_entries.json` formatted with 2-space indentation and UTF-8 encoding.

### 3.2 Fixture Health Status Ingestion
Every admin page context receives `fixture_info`, reporting:
- Whether the backup file exists (`exists: true/false`).
- Human-readable file size (e.g. `245.8 KB`).
- Last modified datetime timestamp.
- Total JSON record count.

### 3.3 Restoring Fixtures via CLI
To restore a fresh database from the backup file:
```bash
python manage.py loaddata tracker/fixtures/pokedex_entries.json
```
