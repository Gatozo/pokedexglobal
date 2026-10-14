# 🏛️ Architecture and System Design (English)

## 1. System Overview

**Pokédex Global Tracker** is engineered as a high-performance Django web platform tailored for multi-generational Pokémon tracking and historical canon preservation.

The system is built upon a strategic decoupling between **canonical static data** and **dynamic user progress**:
1. **In-Memory Immutable Catalogs (0 ms SQL)**: Pokémon species, regional numbering, stats, historical typings, official encounter methods in Spanish, and sprite paths are not queried from heavy database tables on every request. Instead, they are loaded into memory from precompiled JSON files managed by `catalog_service.py`.
2. **Lightweight Relational Persistence**: PostgreSQL exclusively stores game structural entities (`Game`, `Pokedex`) and user catch records (`UserPokemonCatch`), supporting both anonymous guest sessions and authenticated user accounts.
3. **Retro-Interactive User Experience**: Comic-book aesthetic (Ben-Day dots, hard ink drop shadows), dynamic chiptune/orchestrated cries, generational Game Hub, shiny variant tracking, and Unown glyph albums.

---

## 2. System Architecture Diagram

```mermaid
graph TB
    subgraph Client ["Client Layer (Browser)"]
        Browser["Web Browser (Desktop / Mobile)"]
        DOM["DOM + Comic-Book Components"]
        AudioEngine["HTML5 Audio Engine (8-bit vs Modern Cries)"]
        Hub["Game Hub (Game Selector & Progress)"]
        CatchState["Reactive Catch State (Normal / Shiny / Unown)"]
    end

    subgraph Django ["Django 6.1 Server (Backend)"]
        subgraph Middleware
            SecMid["Security Middleware"]
            SessMid["Session Middleware"]
            AuthMid["Authentication Middleware"]
            CsrfMid["CSRF Protection"]
        end

        subgraph Controllers ["Views & Controllers"]
            AuthView["auth_portal_view / guest_continue_view"]
            HubView["game_selector_view (Game Hub)"]
            DexView["pokedex_view(game_slug, pokedex_slug)"]
            AjaxCatch["toggle_catch (POST - Normal & Shiny)"]
            AjaxUnown["toggle_unown_catch (POST - Unown Forms)"]
            AdminSite["Custom Admin Panel & Exporter"]
        end

        subgraph Services ["Domain Services"]
            CatService["catalog_service.py (In-Memory Catalog Service)"]
            FixtureUtil["fixtures_util.py (Game Metadata Exporter)"]
        end
    end

    subgraph Storage ["Storage & Persistence"]
        subgraph PostgreSQL ["PostgreSQL Database"]
            T_Game[(tracker_game)]
            T_Dex[(tracker_pokedex)]
            T_Catch[(tracker_userpokemoncatch)]
        end

        subgraph StaticFiles ["Local Disk Storage"]
            CatalogsJSON["tracker/data/catalogs/<slug>.json"]
            MediaRoot["media/pokemon/ (Sprites, Cries, Icons)"]
            FixturesJSON["tracker/fixtures/pokedex_entries.json"]
        end
    end

    Browser --> DOM
    DOM --> AudioEngine
    DOM --> Hub
    DOM --> CatchState

    CatchState --> AjaxCatch
    CatchState --> AjaxUnown
    Hub --> HubView
    DOM --> DexView
    DOM --> AuthView

    DexView --> CatService
    AjaxCatch --> CatService
    CatService --> CatalogsJSON

    DexView --> T_Game
    DexView --> T_Dex
    DexView --> T_Catch

    AjaxCatch --> T_Catch
    AjaxUnown --> T_Catch

    AdminSite --> FixtureUtil
    FixtureUtil --> T_Game
    FixtureUtil --> T_Dex
    FixtureUtil --> FixturesJSON
```

---

## 3. System Evolution: In-Memory Precompiled Catalogs Architecture (0 ms SQL)

> [!NOTE]
> **Design Rationale:** In early versions, species and pokedex entries were stored as traditional Django ORM tables (`Pokemon`, `PokedexEntry`, `Move`). This resulted in thousands of static database rows, complex $N+1$ queries for grid rendering, and recurring database migration overhead when introducing new games.

To eliminate this bottleneck and provide an instant, zero-latency *Offline-First* experience:
1. **Precompiled Immutable Catalogs**: Canonical game data is compiled into static JSON files under `tracker/data/catalogs/<game_slug>.json`.
2. **In-Memory `CatalogService`**: When handling requests, `tracker.catalog_service` deserializes and caches catalog entries (`_CATALOG_CACHE`), validating file `mtime` for hot-reloads during development.
3. **Dedicated Relational Tracking**: PostgreSQL resources are dedicated to indexing user progress (`UserPokemonCatch`) with optimized composite indices.

---

## 4. Catch Lifecycle and Tracking Mechanics

### 4.1 Dual User Identity (Guest vs Authenticated)
The platform allows immediate catching without forced registration by utilizing Django anonymous sessions:

```mermaid
sequenceDiagram
    autonumber
    actor User as User / Browser
    participant View as views.toggle_catch
    participant Session as Django Session Engine
    participant Cat as catalog_service
    participant DB as UserPokemonCatch (PostgreSQL)

    User->>View: POST /api/catch/toggle/ {"entry_id": 25, "is_shiny": false}
    View->>Cat: get_catalog_entry_by_id(25)
    Cat-->>View: CatalogEntry(game_slug="red", entry_number=25)
    View->>Session: Inspect request.user and request.session
    alt Authenticated User
        Session-->>View: user = request.user, session_key = None
        View->>DB: get_or_create(game_slug="red", entry_number=25, user=user)
    else Anonymous Guest
        opt Session without assigned key
            Session->>Session: request.session.save()
        end
        Session-->>View: user = None, session_key = session.session_key
        View->>DB: get_or_create(game_slug="red", entry_number=25, session_key=session_key)
    end
    View->>DB: Toggle is_caught (or is_shiny) and update timestamp
    View->>DB: Count active catches for this game
    View-->>User: 200 OK JSON {success: true, is_caught: true, caught_count: 12, percent: 7.9}
    User->>User: Update retro card border, shiny star, and progress bar
```

### 4.2 Dual Mode Tracking (Normal vs Shiny)
* The `/api/catch/toggle/` endpoint accepts the boolean flag `is_shiny`.
* The database stores `is_caught` and `is_shiny` independently on the same `UserPokemonCatch` record identified by `(game_slug, entry_number)`.
* This allows live switching between normal and shiny modes without page reloads.

### 4.3 Unown Glyph Tracking
* For titles with ruins (Gen 2 Gold/Silver/Crystal, Gen 3 FireRed/LeafGreen), `/api/unown-catch/toggle/` updates the native `JSONField(unown_forms_caught)`.
* Payload structure: `{"normal": ["A", "F", "R"], "shiny": ["A"]}`.
* Catching at least one glyph registers Unown as caught in the overall Pokédex while preserving individual letter tracking in the dedicated album modal.

---

## 5. Performance Optimizations

1. **$O(1)$ Catalog Access**: Instant in-memory retrieval without database locks or transaction overhead.
2. **In-Memory Set Lookup**: In `pokedex_view`, user catches for the active game are fetched in a single indexed query (`values_list('entry_number', flat=True)`) and evaluated in constant time $O(1)$.
3. **Composite Database Indices**:
   * `[user, game_slug]`
   * `[session_key, game_slug]`
   * `[game_slug, entry_number]`
4. **Reactive Cache Invalidation**: Django signals (`post_save`, `post_delete`) on `Game` invalidate the `all_games_catalog` cache key upon admin edits.
