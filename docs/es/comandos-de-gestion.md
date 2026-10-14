# ⚙️ Referencia de Comandos de Gestión y Scripts de Catálogo (Español)

Los comandos de gestión personalizados de Django residen en `tracker/management/commands/`. Están enfocados en la sincronización, descarga y normalización de activos multimedia offline (sprites, animaciones, iconos y sonidos de gritos).

Por su parte, la generación y compilación de catálogos de juegos se realiza a través de los constructores dedicados en `tracker/scripts/` bajo el estándar de `guides/especificacion-nuevo-juego.md`.

---

## 1. Comandos de Sincronización Multimedia (`manage.py`)

Todos los comandos se ejecutan a través de la CLI estándar de Django: `python manage.py <comando> [opciones]`.

| Comando | Propósito | Directorio de Destino |
| :--- | :--- | :--- |
| `sync_pokemon_cries` | Descarga y organiza los gritos sonoros vintage (8 bits) y modernos en formato OGG. | `media/pokemon/cries/` |
| `sync_pokemon_icons` | Sincroniza los iconos de menú/PC estándar para las especies de la Pokédex. | `media/pokemon/icons/` |
| `sync_classic_icons` | Descarga iconos de menú con la estética pixel-art clásica de cartucho. | `media/pokemon/icons/classic/` |
| `sync_items` | Sincroniza los iconos oficiales de objetos, piedras evolutivas e ítems clave. | `media/items/` |
| `sync_unown_sprites` | Descarga las 26 a 28 formas alfabéticas de Unown (versiones normales y variocolor). | `media/pokemon/sprites/unown/` |
| `sync_crystal_sprites` | Sincroniza los sprites estáticos del cartucho oficial de Pokémon Cristal. | `media/pokemon/sprites/crystal/` |
| `sync_crystal_animated_sprites` | Descarga los archivos GIF animados con la animación de entrada de Pokémon Cristal. | `media/pokemon/sprites/crystal_animated/` |
| `sync_emerald_animated_sprites` | Descarga los sprites animados exclusivos de Pokémon Esmeralda. | `media/pokemon/sprites/emerald_animated/` |
| `sync_gold_shiny_sprites` | Sincroniza los sprites de variantes variocolor (shiny) de Pokémon Oro. | `media/pokemon/sprites/gold_shiny/` |
| `sync_silver_sprites` | Sincroniza los sprites del cartucho de Pokémon Plata. | `media/pokemon/sprites/silver/` |
| `normalize_gen1_sprites` | Normaliza el escalado y paleta de los sprites clásicos de Generación 1. | `media/pokemon/sprites/` |
| `sync_wikidex_flavor_texts` | Extrae y actualiza las descripciones oficiales en castellano desde WikiDex. | `tracker/data/catalogs/` |

---

## 2. Ejemplos de Uso Operativo

### Sincronización de Gritos de Audio
Descarga los sonidos de gritos tanto en su variante clásica chiptune como en su versión moderna:
```bash
python manage.py sync_pokemon_cries
```

### Sincronización de Sprites Animados de Pokémon Cristal
Aprovisiona las animaciones de batalla en formato GIF para la modal retro:
```bash
python manage.py sync_crystal_animated_sprites
```

### Sincronización de Formas Unown
Descarga el conjunto completo de glifos alfabéticos para la vista de ruinas:
```bash
python manage.py sync_unown_sprites
```

---

## 3. Flujo de Generación y Compilación de Catálogos de Juegos

A diferencia de las versiones iniciales que utilizaban comandos ORM genéricos, la arquitectura actual utiliza **constructores especializados por edición** en `tracker/scripts/`:

* `tracker/scripts/build_ruby_catalog.py`
* `tracker/scripts/build_sapphire_catalog.py`
* `tracker/scripts/build_emerald_catalog.py`
* `tracker/scripts/build_firered_catalog.py`
* `tracker/scripts/build_leafgreen_catalog.py`
* `tracker/scripts/build_diamond_catalog.py`

### Protocolo para Compilar un Nuevo Catálogo:
1. El script define las especies presentes en el juego con su numeración regional y nacional canónica.
2. Aplica los nombres de áreas y métodos de captura oficiales en español de España (evitando slugs en inglés o traducciones automáticas).
3. Resuelve los tipos históricos de la generación (ej. Magnemite Eléctrico puro en Gen 1).
4. Exporta el archivo estático inmutable a `tracker/data/catalogs/<game_slug>.json`.
5. Una vez compilado, el catálogo se versiona directamente en Git y está listo para ser servido por `catalog_service.py` con 0 ms de latencia SQL.

> [!TIP]
> Para la guía técnica completa paso a paso sobre cómo agregar cualquier edición de Gen 1 a Gen 9 y Leyendas, consulta [guides/especificacion-nuevo-juego.md](../../guides/especificacion-nuevo-juego.md).
