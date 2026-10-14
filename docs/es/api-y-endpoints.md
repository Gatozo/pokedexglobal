# 🌐 Endpoints de API y Mapa de Rutas (Español)

## 1. Mapa Completo de Rutas URL

Las rutas principales de la aplicación se definen en `tracker/urls.py` dentro del espacio de nombres `tracker`:

| Patrón URL | Función de Vista | Nombre de Ruta | Propósito |
| :--- | :--- | :--- | :--- |
| `/` | `auth_portal_view` | `tracker:home` | Portal de autenticación inicial (login, registro y acceso como invitado). |
| `/login/` | `auth_portal_view` | `tracker:login` | Alias directo al portal de autenticación. |
| `/register/` | `register_view` | `tracker:register` | Registro de nuevos usuarios con validación reactiva. |
| `/guest/` | `guest_continue_view` | `tracker:guest_continue` | Inicializa una sesión anónima y redirige al selector de juegos. |
| `/logout/` | `logout_view` | `tracker:logout` | Cierre de sesión y redirección al portal de autenticación. |
| `/games/` | `game_selector_view` | `tracker:game_selector` | **Game Hub**: Selector visual de juegos con barras de progreso por edición y generación. |
| `/<slug:game_slug>/` | `pokedex_view` | `tracker:pokedex_default` | Muestra la Pokédex regional de la edición especificada. |
| `/<slug:game_slug>/<slug:pokedex_slug>/` | `pokedex_view` | `tracker:pokedex_detail` | Muestra una sección específica (regional o nacional) del juego. |
| `/api/catch/toggle/` | `toggle_catch` | `tracker:toggle_catch` | Endpoint AJAX `POST` para alternar captura (modo normal o shiny). |
| `/api/unown-catch/toggle/` | `toggle_unown_catch` | `tracker:toggle_unown_catch` | Endpoint AJAX `POST` para alternar captura de formas de Unown. |
| `/api/auth/check-username/` | `check_username` | `tracker:check_username` | Endpoint AJAX para comprobar disponibilidad de nombre de usuario en vivo. |
| `/admin/tracker/export-fixtures/` | `export_fixtures_admin_view` | `admin:export_fixtures` | Exportación administrativa de metadatos de juegos a JSON. |

---

## 2. Especificación Detallada de Vistas

### 2.1 `game_selector_view` (Game Hub)
- **Ruta:** `/games/`
- **Método HTTP:** `GET`
- **Comportamiento:**
  1. Identifica al usuario activo o sesión anónima.
  2. Consulta la lista de juegos activos desde la base de datos o caché.
  3. Para cada juego, calcula la cantidad de Pokémon capturados en modo regional y nacional contrastando `UserPokemonCatch` contra el tamaño de cada catálogo en memoria.
  4. Agrupa las ediciones por generación (Gen 1 a 9) e inyecta paletas de color y porcentajes de completitud.
- **Respuesta:** Renderizado de la plantilla `tracker/game_selector.html`.

### 2.2 `pokedex_view` (Cuadrícula Principal de la Pokédex)
- **Rutas:** `/<slug:game_slug>/` y `/<slug:game_slug>/<slug:pokedex_slug>/`
- **Método HTTP:** `GET`
- **Flujo de Ejecución:**
  1. Obtiene la instancia `Game` correspondiente al slug (404 si no existe).
  2. Determina si la vista corresponde al modo regional o al modo nacional (`is_national`).
  3. Carga las entradas del juego en 0 ms desde `catalog_service.get_compiled_catalog(game.slug)`.
  4. Extrae las capturas del usuario activo en un conjunto en memoria (`set`) para marcar `is_caught` e `is_shiny` en $O(1)$.
  5. Computa estadísticas globales del cartucho (`total_pokemon`, `caught_count`, `caught_percent`, `shiny_caught_count`, `shiny_percent`).
- **Respuesta:** Plantilla HTML renderizada `tracker/pokedex_detail.html`.

---

## 3. Endpoints AJAX de API

### 3.1 `toggle_catch` (Alternar Captura Normal o Shiny)
- **Método HTTP:** `POST` (protegido por `@require_POST` y verificación CSRF).
- **Ruta:** `/api/catch/toggle/`
- **Cabeceras:**
  - `Content-Type: application/json`
  - `X-CSRFToken: <token>`

#### Payload de Petición:
```json
{
  "entry_id": 25,
  "is_shiny": false
}
```
* `entry_id` (int, obligatorio): Identificador único de la entrada en el catálogo compilado.
* `is_shiny` (bool, opcional, por defecto `false`): Si es `true`, conmuta el estado de la variante variocolor; si es `false`, conmuta la captura regular.

#### Respuesta Exitosa (HTTP 200 OK):
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

### 3.2 `toggle_unown_catch` (Alternar Formas de Unown)
- **Método HTTP:** `POST` (protegido por `@require_POST` y CSRF).
- **Ruta:** `/api/unown-catch/toggle/`

#### Payload de Petición:
```json
{
  "game_slug": "crystal",
  "letter": "A",
  "is_shiny": false
}
```

#### Respuesta Exitosa (HTTP 200 OK):
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

### 3.3 `check_username` (Validación de Disponibilidad)
- **Método HTTP:** `GET` o `POST`
- **Ruta:** `/api/auth/check-username/?username=ash_ketchum`

#### Respuesta JSON:
```json
{
  "available": true,
  "username": "ash_ketchum"
}
```
