# 🛡️ Panel de Administración y Respaldo de Metadatos (Español)

## 1. Arquitectura del Panel de Administración

El portal de administración de Django accesible en `/admin/` está diseñado para la supervisión estructural del catálogo de juegos, las secciones de Pokédex y la monitorización de capturas de usuarios.

### 1.1 Modelos Registrados en `tracker/admin.py`
* **`GameAdmin`**:
  * Visualización: `name`, `slug`, `generation`, `created_at`.
  * Autocompletado del campo `slug` a partir del nombre en inglés.
  * Filtros por generación y buscador por nombre.
* **`PokedexAdmin`**:
  * Visualización: `name`, `game`, `slug`, `is_national`, `pokeapi_name`.
  * Filtros por juego asociado e indicador de Pokédex Nacional.
* **`UserPokemonCatchAdmin`**:
  * Supervisión en vivo de las capturas registradas: `user`, `session_key`, `game_slug`, `entry_number`, `entry_id`, `is_caught`, `is_shiny`, `caught_at`.
  * Filtros por estado de captura normal, estado variocolor y edición de juego.

---

## 2. Respaldo de Metadatos Estructurales (`fixtures_util.py`)

El módulo `tracker/fixtures_util.py` automatiza la exportación de las configuraciones de juegos y sus Pokédex asociadas para control de versiones en Git.

> [!IMPORTANT]
> **Alcance del Respaldo:** El mecanismo de exportación de fixtures respalda exclusivamente los metadatos estructurales de las tablas relacionales `tracker.Game` y `tracker.Pokedex`.  
> No incluye el progreso de capturas de los usuarios (`UserPokemonCatch`, que reside en la base de datos de producción) ni los datos de especies de Pokémon (que se gestionan de forma inmutable a través de los catálogos JSON en `tracker/data/catalogs/`).

### 2.1 Botón de Exportación en el Panel de Administración
Los superusuarios disponen de un acceso directo en el encabezado del panel administrativo:
* **Endpoint:** `/admin/tracker/export-fixtures/` (petición protegida por método `POST`, restringida estrictamente a superusuarios).
* **Destino:** `tracker/fixtures/pokedex_entries.json` con codificación UTF-8 y sangrado de 2 espacios.
* **Indicador de Estado:** La interfaz administrativa muestra en todo momento si el archivo de respaldo existe en disco, su peso formateado para humanos, fecha de última modificación y total de registros exportados.

### 2.2 Restauración de Metadatos desde Consola
Para inicializar una nueva instancia de base de datos con los juegos y Pokédex registrados:
```bash
python manage.py loaddata tracker/fixtures/pokedex_entries.json
```
