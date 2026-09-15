# 🌐 Endpoints de API y Vistas (Español)

## 1. Mapa de Rutas URL

Las rutas principales de la aplicación se definen en `tracker/urls.py` dentro del espacio de nombres `tracker`:

| Patrón URL | Función de Vista | Nombre de Ruta | Descripción |
| :--- | :--- | :--- | :--- |
| `/` | `pokedex_view` | `tracker:home` | Muestra la Pokédex del juego por defecto (`red`) y región (`kanto`). |
| `/<slug:game_slug>/` | `pokedex_view` | `tracker:pokedex_default` | Muestra el juego especificado con la Pokédex de Kanto. |
| `/<slug:game_slug>/<slug:pokedex_slug>/` | `pokedex_view` | `tracker:pokedex_detail` | Muestra el juego y la Pokédex regional solicitados. |
| `/api/catch/toggle/` | `toggle_catch` | `tracker:toggle_catch` | Endpoint AJAX por POST para alternar captura. |
| `/admin/tracker/export-fixtures/` | `export_fixtures_admin_view` | `admin:export_fixtures` | Acción administrativa exclusiva para volcar fixtures. |

---

## 2. Especificación de Vistas

### 2.1 `pokedex_view`
- **Método HTTP**: `GET`
- **Parámetros en URL**:
  - `game_slug` (opcional, por defecto `"red"`): Slug del videojuego.
  - `pokedex_slug` (opcional, por defecto `"kanto"`): Slug de la Pokédex regional.
- **Flujo de Ejecución**:
  1. Localiza los objetos `Game` y `Pokedex` correspondientes (HTTP 404 en caso de ausencia).
  2. Consulta las entradas `PokedexEntry` vinculadas con `.select_related("pokemon")` ordenadas por `entry_number`.
  3. Identifica al cliente mediante `_get_user_or_session(request)`.
  4. Extrae los IDs de entradas capturadas para ese usuario o sesión y los convierte en un conjunto (`set`).
  5. Asigna a cada entrada el valor `entry.is_caught = (entry.id in caught_entry_ids)`.
  6. Calcula las estadísticas de progreso (`total_pokemon`, `caught_count`, `caught_percent`).
  7. Inyecta `all_games` para poblar el selector de versiones en el encabezado.
- **Respuesta**: Plantilla HTML renderizada `tracker/pokedex_detail.html`.

---

### 2.2 `toggle_catch` (Endpoint AJAX)
- **Método HTTP**: `POST` (restringido estrictamente mediante `@require_POST`).
- **Ruta**: `/api/catch/toggle/`
- **Cabeceras Obligatorias**:
  - `Content-Type: application/json`
  - `X-CSRFToken: <token_csrf>`

#### Cuerpo de la Petición (Payload):
```json
{
  "entry_id": 25
}
```

#### Respuesta Exitosa (HTTP 200 OK):
```json
{
  "success": true,
  "entry_id": 25,
  "is_caught": true,
  "caught_count": 12,
  "total_count": 151,
  "percent": 7.9
}
```

#### Respuestas de Error:
- **HTTP 400 Bad Request** (Payload JSON malformado o sin clave `entry_id`):
  ```json
  {
    "error": "Payload JSON inválido"
  }
  ```
- **HTTP 404 Not Found**: Si no existe una entrada `PokedexEntry` con el ID especificado.
- **HTTP 405 Method Not Allowed**: Si se accede mediante peticiones GET, PUT o DELETE.

---

## 3. Ejemplo de Integración en el Frontend

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
        throw new Error(`Error en la petición: ${response.status}`);
    }

    const data = await response.json();
    console.log(`Entrada #${data.entry_id} capturada: ${data.is_caught}`);
    console.log(`Progreso: ${data.caught_count}/${data.total_count} (${data.percent}%)`);
    return data;
}
```
