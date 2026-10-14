# 📚 Pokédex Global Tracker — Technical Documentation (English)

Welcome to the comprehensive technical documentation for **Pokédex Global Tracker**. Here you will find up-to-date guides covering system architecture, data modeling, in-memory catalogs, UI components, administrative tooling, and automated testing.

---

## 📑 Table of Contents

| Document | Description |
| :--- | :--- |
| **[1. Architecture & Design](architecture.md)** | High-level system architecture, client-server data flow, Offline-First strategy, in-memory precompiled catalogs (0 ms SQL), and concurrency model. |
| **[2. Database Models & Schemas](database-models.md)** | In-depth analysis of relational models (`Game`, `Pokedex`, `UserPokemonCatch`), composite indices, constraints, and the JSON `CatalogEntry` schema. |
| **[3. Management Commands & Scripts](management-commands.md)** | Operational manual for media asset synchronization commands (sprites, cries, animations, icons) and catalog builders in `tracker/scripts/`. |
| **[4. API Endpoints & Routes](api-and-endpoints.md)** | Full routing table, auth portal, Game Hub (`/games/`), and AJAX endpoints (`/api/catch/toggle/` and `/api/unown-catch/toggle/`). |
| **[5. Comic-Book UI Design](ui-and-components.md)** | Comic visual aesthetic, Tailwind CSS integration, Game Hub, dynamic modals, shiny tracking, Unown glyphs, and dual audio engine. |
| **[6. Admin Panel & Fixtures](admin-and-fixtures.md)** | Django Admin customizations, catch monitoring, and structural metadata exporter/importer (`tracker.Game` and `tracker.Pokedex`). |
| **[7. Testing & Quality Assurance](testing-guide.md)** | Automated test execution (173 tests), network isolation, `--keepdb` workflow, and canonical rule verification. |

---

## 🧭 Core Architectural Pillars

1. **Django 6.1.1 + Python 3.12+**: Modern Django patterns, native `psycopg3` connector, and strict type hinting.
2. **In-Memory Precompiled Catalogs (0 ms SQL)**: Zero-latency in-memory data delivery via `catalog_service.py` with 0 ms SQL overhead.
3. **Efficient Relational Tracking**: Lean PostgreSQL schema focused on user catch activity (`UserPokemonCatch`) with support for anonymous guests and registered users.
4. **Historical Canonical Fidelity**: Official Spanish locations (WikiDex), generation-accurate typings, and dual-era audio cries (8-bit chiptune vs orchestrated).
