# 🛡️ Personalización del Administrador y Fixtures (Español)

## 1. Arquitectura del Panel de Administración

El portal de administración de Django accesible en `/admin/` ha sido adaptado con capacidades específicas para la curación de contenido y la supervisión de la plataforma.

### 1.1 Configuración de ModelAdmin
- **`PokedexEntryAdmin`**:
  - `list_editable = ('is_custom_override',)`: Permite activar o desactivar la protección contra sobreescritura directamente desde la lista de registros sin necesidad de entrar a la vista de edición individual.
  - `readonly_fields = ('pokedex', 'pokemon', 'entry_number')`: Protege la relación estructural primaria para evitar desvinculaciones accidentales.
  - Filtros avanzados por Juego, Pokédex y Tipos.
- **`PokemonAdmin`**:
  - Búsqueda por nombre en inglés, nombre en español y número de Pokédex Nacional.
  - Filtros por tipo primario y secundario.
- **`GameAdmin`**:
  - Autocompleta el campo `slug` a partir del nombre del juego.
  - Filtrado por generación.
- **`UserPokemonCatchAdmin`**:
  - Monitoreo en vivo de las capturas de usuarios registrados y sesiones de invitados.

---

## 2. Protección de Ediciones Manuales (`is_custom_override`)

Cuando se introducen correcciones artesanales, notas de eventos o datos de romhacks:
1. Un administrador accede a una entrada `PokedexEntry` (por ejemplo, modificando las notas de obtención en `obtaining_info` o afinando la descripción en español).
2. El administrador marca la casilla `is_custom_override = True`.
3. Al ejecutarse comandos de sincronización automatizada como `sync_pokemon_details`, el script detecta este indicador y omite el registro, protegiéndolo de cualquier cambio automático.
4. Esto asegura la coexistencia pacífica entre procesos de importación masiva y curaduría editorial manual.

---

## 3. Gestión y Respaldo de Fixtures

El módulo `tracker/fixtures_util.py` gestiona la exportación e inspección de los datos estructurales.

### 3.1 Exportador de Fixtures con un Solo Clic
Los superusuarios cuentan con un botón de exportación rápida en el panel administrativo:
- Integrado mediante la personalización de `admin.site.get_urls()` y `admin.site.each_context()`.
- Endpoint: `/admin/tracker/export-fixtures/` (petición `POST`, restringida a superusuarios).
- Modelos respaldados: `tracker.Game`, `tracker.Pokedex` y `tracker.PokedexEntry`.
- Destino: `tracker/fixtures/pokedex_entries.json` en codificación UTF-8 y con sangrado de 2 espacios.

### 3.2 Indicador de Estado del Respaldo
En el contexto de las vistas administrativas se inyecta la información del archivo de respaldo:
- Existencia del archivo en disco (`exists: true/false`).
- Tamaño formateado para humanos (ej: `245.8 KB`).
- Fecha y hora de última modificación.
- Cantidad total de registros exportados.

### 3.3 Restauración de Fixtures desde Consola
Para inicializar o restaurar una base de datos nueva a partir del archivo de respaldo:
```bash
python manage.py loaddata tracker/fixtures/pokedex_entries.json
```
