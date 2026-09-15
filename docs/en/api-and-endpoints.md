# 🌐 API Endpoints & Views Specification (English)

## 1. URL Routing Map

The application routes are registered in `tracker/urls.py` under the `tracker` namespace:

| Pattern | View Function | Route Name | Description |
| :--- | :--- | :--- | :--- |
| `/` | `pokedex_view` | `tracker:home` | Renders default game (`red`) and Pokédex (`kanto`). |
| `/<slug:game_slug>/` | `pokedex_view` | `tracker:pokedex_default` | Renders the specified game with default `kanto` dex. |
| `/<slug:game_slug>/<slug:pokedex_slug>/` | `pokedex_view` | `tracker:pokedex_detail` | Renders the specified game and regional dex. |
| `/api/catch/toggle/` | `toggle_catch` | `tracker:toggle_catch` | AJAX POST endpoint to toggle catch status. |
| `/admin/tracker/export-fixtures/` | `export_fixtures_admin_view` | `admin:export_fixtures` | Superuser-only POST action to dump fixtures. |

---

## 2. Views Specification

### 2.1 `pokedex_view`
- **Method**: `GET`
- **Path Parameters**:
  - `game_slug` (optional, default `"red"`): Slug of the target game.
  - `pokedex_slug` (optional, default `"kanto"`): Slug of the target Pokédex.
- **Behavior**:
  1. Retrieves `Game` and `Pokedex` objects (returning HTTP 404 if missing).
  2. Queries all associated `PokedexEntry` instances using `.select_related("pokemon")` sorted by `entry_number`.
  3. Identifies the client using `_get_user_or_session(request)`.
  4. Queries caught entries for this specific user/session and converts them to a hash set.
  5. Annotates each entry with `entry.is_caught = (entry.id in caught_entry_ids)`.
  6. Computes completion statistics (`total_pokemon`, `caught_count`, `caught_percent`).
  7. Passes `all_games` to populate the game selector navigation bar.
- **Response**: Rendered HTML template `tracker/pokedex_detail.html`.

---

### 2.2 `toggle_catch` (AJAX Endpoint)
- **Method**: `POST` (strictly enforced via `@require_POST`)
- **URL**: `/api/catch/toggle/`
- **Headers Required**:
  - `Content-Type: application/json`
  - `X-CSRFToken: <csrf_token>`

#### Request Payload:
```json
{
  "entry_id": 15
}
```

#### Successful Response (HTTP 200):
```json
{
  "success": true,
  "entry_id": 15,
  "is_caught": true,
  "caught_count": 42,
  "total_count": 151,
  "percent": 27.8
}
```

#### Error Responses:
- **HTTP 400 Bad Request** (Malformed JSON or missing payload):
  ```json
  {
    "error": "Payload JSON inválido"
  }
  ```
- **HTTP 404 Not Found** (`PokedexEntry` matching `entry_id` does not exist):
  Standard Django 404 handler.
- **HTTP 405 Method Not Allowed** (If accessed via GET/PUT/DELETE):
  Standard Django 405 handler.

---

## 3. Client-Side Integration Example

```javascript
async function toggleCatch(entryId, csrfToken) {
    const response = await fetch('/api/catch/toggle/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken,
        },
        body: JSON.stringify({ entry_id: entryId })
    });

    if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    console.log(`Entry #${data.entry_id} caught: ${data.is_caught}`);
    console.log(`Progress: ${data.caught_count} / ${data.total_count} (${data.percent}%)`);
    return data;
}
```
