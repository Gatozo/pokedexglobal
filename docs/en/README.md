# 📚 Pokédex Global Tracker — Technical Documentation (English)

Welcome to the comprehensive technical documentation for **Pokédex Global Tracker**. This documentation covers architectural principles, database modeling, synchronization pipelines, frontend components, administrative tooling, and testing suites.

---

## 📑 Documentation Table of Contents

| Document | Description |
| :--- | :--- |
| **[1. Architecture & Design](architecture.md)** | High-level system architecture, client-server data flow, offline-first strategy, and concurrency models. |
| **[2. Database Models & Schema](database-models.md)** | Deep dive into ORM models (`Game`, `Pokedex`, `Pokemon`, `PokedexEntry`, `UserPokemonCatch`, `Move`), schema constraints, indexes, and JSON structures. |
| **[3. Management Commands Reference](management-commands.md)** | Complete manual for the 5 CLI management commands (`import_pokedex`, `sync_pokemon_cache`, `sync_pokemon_details`, `sync_moves`, `backfill_pokedex_types`). |
| **[4. API Endpoints & Views](api-and-endpoints.md)** | Specification of HTTP views, `/api/catch/toggle/` AJAX endpoint, session-based & authenticated catch tracking, and error handling. |
| **[5. UI & Comic-Book Component Design](ui-and-components.md)** | Detailed guide on the comic-strip aesthetic, Tailwind CSS integration, dynamic modals, sound system (8-bit vs modern audio cries), and responsive layouts. |
| **[6. Admin Customizations & Fixtures](admin-and-fixtures.md)** | Customizations in the Django admin interface, `is_custom_override` manual lock mechanism, and one-click JSON fixture export/import tools. |
| **[7. Testing Guide & Quality Assurance](testing-guide.md)** | Test runner commands, test fixture mocks, coverage across views, models, AJAX endpoints, and historical generation mechanics. |

---

## 🧭 Key Project Highlights

1. **Django 6.1.1 + Python 3.12+**: Utilizing modern Django capabilities, asynchronous-ready adapters (`psycopg3`), and typed utility helpers.
2. **PostgreSQL Relational Storage**: Optimized schema with database-level indexes, foreign key cascading, and native JSONField queries.
3. **PokeAPI Rate-Limiting & Fault Tolerance**: Pacing delays, HTTP 429 backoff, random jitter, and local caching prevent Cloudflare IP blocks.
4. **Historical Canon Accuracy**: Dynamically adjusts Pokémon types and cries to match retro video games instead of modern revisions.
