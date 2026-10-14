# 🌐 API Endpoints & Route Map (English)

## 1. Complete URL Route Map

Application routes are registered in `tracker/urls.py` within the `tracker` namespace:

| URL Pattern | View Function | Route Name | Purpose |
| :--- | :--- | :--- | :--- |
| `/` | `auth_portal_view` | `tracker:home` | Initial authentication portal (login, registration, guest access). |
| `/login/` | `auth_portal_view` | `tracker:login` | Direct alias to the authentication portal. |
| `/register/` | `register_view` | `tracker:register` | New user registration with reactive validation. |
| `/guest/` | `guest_continue_view` | `tracker:guest_continue` | Initializes an anonymous guest session and redirects to Game Hub. |
| `/logout/` | `logout_view` | `tracker:logout` | User logout and redirect to auth portal. |
| `/games/` | `game_selector_view` | `tracker:game_selector` | **Game Hub**: Visual edition selector with dual progress bars. |
| `/<slug:game_slug>/` | `pokedex_view` | `tracker:pokedex_default` | Renders the regional Pokédex for the specified game edition. |
| `/<slug:game_slug>/<slug:pokedex_slug>/` | `pokedex_view` | `tracker:pokedex_detail` | Renders a specific Pokédex section (regional or national). |
| `/api/catch/toggle/` | `toggle_catch` | `tracker:toggle_catch` | AJAX `POST` endpoint to toggle catch status (normal or shiny). |
| `/api/unown-catch/toggle/` | `toggle_unown_catch` | `tracker:toggle_unown_catch` | AJAX `POST` endpoint to toggle Unown glyph catch status. |
| `/api/auth/check-username/` | `check_username` | `tracker:check_username` | AJAX endpoint for live username availability validation. |
| `/admin/tracker/export-fixtures/` | `export_fixtures_admin_view` | `admin:export_fixtures` | Administrative action to dump game structural metadata to JSON. |

---

## 2. View Controller Specifications

### 2.1 `game_selector_view` (Game Hub)
- **Route:** `/games/`
- **HTTP Method:** `GET`
- **Execution Flow:**
  1. Identifies current user or guest session key.
  2. Queries all active games from database/cache.
  3. Calculates caught Pokémon counts for regional and national dexes against compiled catalog sizes.
  4. Groups editions by generation and injects visual palettes and completion percentages.
- **Response:** Rendered HTML template `tracker/game_selector.html`.

### 2.2 `pokedex_view` (Main Pokédex Grid)
- **Routes:** `/<slug:game_slug>/` and `/<slug:game_slug>/<slug:pokedex_slug>/`
- **HTTP Method:** `GET`
- **Execution Flow:**
  1. Retrieves `Game` instance by slug (HTTP 404 if not found).
  2. Resolves section type (`is_national`).
  3. Loads entries in 0 ms from `catalog_service.get_compiled_catalog(game.slug)`.
  4. Fetches active user catches into an in-memory `set` to evaluate `is_caught` and `is_shiny` in $O(1)$.
  5. Computes completion stats (`total_pokemon`, `caught_count`, `caught_percent`, `shiny_caught_count`, `shiny_percent`).
- **Response:** Rendered HTML template `tracker/pokedex_detail.html`.

---

## 3. AJAX API Endpoints

### 3.1 `toggle_catch` (Toggle Normal or Shiny Catch)
- **HTTP Method:** `POST` (restricted by `@require_POST` and CSRF verification).
- **Route:** `/api/catch/toggle/`
- **Headers:**
  - `Content-Type: application/json`
  - `X-CSRFToken: <token>`

#### Request Payload:
```json
{
  "entry_id": 25,
  "is_shiny": false
}
```
* `entry_id` (int, required): Unique identifier in the compiled catalog.
* `is_shiny` (bool, optional, defaults to `false`): Toggles shiny status when `true`; toggles regular catch when `false`.

#### Successful Response (HTTP 200 OK):
```json
{
  "success": true,
  "entry_id": 25,
  "is_caught": true,
  "is_shiny": false,
  "caught_count": 12,
  "total_count": 151,
  "percent": 7.9
}
```

---

### 3.2 `toggle_unown_catch` (Toggle Unown Glyphs)
- **HTTP Method:** `POST` (restricted by `@require_POST` and CSRF).
- **Route:** `/api/unown-catch/toggle/`

#### Request Payload:
```json
{
  "game_slug": "crystal",
  "letter": "A",
  "is_shiny": false
}
```

#### Successful Response (HTTP 200 OK):
```json
{
  "success": true,
  "letter": "A",
  "is_shiny": false,
  "is_caught": true,
  "unown_forms_caught": {
    "normal": ["A", "B"],
    "shiny": []
  },
  "overall_caught": true,
  "total_unown_count": 26,
  "caught_unown_count": 2
}
```

---

### 3.3 `check_username` (Username Availability Check)
- **HTTP Method:** `GET` or `POST`
- **Route:** `/api/auth/check-username/?username=ash_ketchum`

#### JSON Response:
```json
{
  "available": true,
  "username": "ash_ketchum"
}
```
