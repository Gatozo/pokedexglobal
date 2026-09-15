# ⚙️ Referencia de Comandos de Gestión (Español)

Los comandos de gestión personalizados de Django residen en el directorio `tracker/management/commands/`. Están diseñados para automatizar la importación, enriquecimiento, respaldo y saneamiento de los datos de la Pokédex.

---

## 1. Resumen de Comandos

| Comando | Archivo | Propósito |
| :--- | :--- | :--- |
| `import_pokedex` | `import_pokedex.py` | Descarga un juego y su Pokédex regional desde PokeAPI, crea los registros `Game`, `Pokedex`, `Pokemon`, `PokedexEntry` y descarga sprites a `media/`. |
| `sync_pokemon_cache` | `sync_pokemon_cache.py` | Sincroniza y guarda el JSON crudo (`raw_data`) de PokeAPI en la tabla `Pokemon` local. |
| `sync_pokemon_details` | `sync_pokemon_details.py` | Enriquece entradas con estadísticas por generación, movimientos por nivel, biomas de encuentro y textos oficiales en español con modo Offline-First. |
| `sync_moves` | `sync_moves.py` | Descarga el catálogo de movimientos de combate con nombres oficiales en español, poder, precisión y PP. |
| `backfill_pokedex_types` | `backfill_pokedex_types.py` | Revisa y actualiza todas las entradas con los tipos elementales históricos canónicos de su generación. |

---

## 2. Especificación Detallada de Comandos

### 2.1 `import_pokedex`
Realiza la ingesta inicial de una edición de videojuego y su lista regional.

```bash
python manage.py import_pokedex [opciones]
```

#### Opciones y Argumentos:
- `--game <slug>`: Slug del juego (por defecto: `"red"`). Ejemplos: `blue`, `yellow`, `gold`, `firered`, `ultra-sun`.
- `--game-name <nombre>`: Nombre descriptivo opcional. Si no se indica, se toma el nombre oficial en español del mapeo interno.
- `--generation <int>`: Número de generación del juego (por defecto: `1`).
- `--pokedex <slug>`: Slug de la Pokédex en PokeAPI (por defecto: `"kanto"`). Ejemplos: `original-johto`, `hoenn`, `national`.
- `--pokedex-name <nombre>`: Nombre descriptivo para la Pokédex (por defecto: `"Pokédex Regional de Kanto"`).
- `--force-refresh`: Fuerza la descarga desde PokeAPI aunque la especie ya exista en la base de datos local.
- `--workers <int>`: Hilos concurrentes de descarga en `ThreadPoolExecutor` (por defecto: `4`).
- `--delay <float>`: Retardo de cortesía en segundos entre peticiones (por defecto: `0.05`).

#### Ejemplos de Uso:
```bash
# Importar Pokémon Rojo (Generación 1, Kanto)
python manage.py import_pokedex --game red --generation 1 --pokedex kanto --workers 4

# Importar Pokémon Oro (Generación 2, Johto)
python manage.py import_pokedex --game gold --generation 2 --pokedex original-johto --pokedex-name "Pokédex de Johto"
```

---

### 2.2 `sync_pokemon_cache`
Descarga y almacena en el campo `raw_data` de `Pokemon` la respuesta completa del endpoint `/pokemon/{id}` de PokeAPI (sonidos, gritos, metadatos y listas de movimientos).

```bash
python manage.py sync_pokemon_cache [opciones]
```

#### Opciones y Argumentos:
- `--all`: Actualiza todos los registros, incluso si ya tienen información en `raw_data`.
- `--workers <int>`: Número de hilos concurrentes (por defecto: `4`).
- `--delay <float>`: Retardo de cortesía en segundos (por defecto: `0.05`).

#### Ejemplo de Uso:
```bash
python manage.py sync_pokemon_cache --workers 6
```

---

### 2.3 `sync_pokemon_details`
Realiza el enriquecimiento detallado de las entradas `PokedexEntry` de un cartucho determinado:
- Texto descriptivo oficial en español (`flavor_text`).
- Zonas de aparición, hábitats y métodos de obtención (`obtaining_info`).
- Estadísticas del cartucho y movimientos aprendidos por nivel (`game_data`).
- Categoría o género biológico en español (`category`).

> **Garantía de Seguridad**: Omite automáticamente cualquier entrada que tenga activo el indicador `is_custom_override = True`, protegiendo los ajustes manuales efectuados por administradores.

```bash
python manage.py sync_pokemon_details [opciones]
```

#### Opciones y Argumentos:
- `--game <slug>`: Slug del juego a procesar (por defecto: `"red"`).
- `--workers <int>`: Hilos concurrentes (por defecto: `5`).
- `--delay <float>`: Retardo entre peticiones (por defecto: `0.05`).

#### Ejemplo de Uso:
```bash
python manage.py sync_pokemon_details --game red --workers 5
```

---

### 2.4 `sync_moves`
Puebla la tabla `Move` con la información canónica de ataques y técnicas de combate.

```bash
python manage.py sync_moves [opciones]
```

#### Opciones y Argumentos:
- `--generation <int>`: Generación de movimientos (por defecto: `1`, movimientos 1 al 165).
- `--workers <int>`: Hilos concurrentes de descarga (por defecto: `10`).
- `--local`: Prioriza la lectura desde el archivo local de caché (`tracker/data/moves_gen1.json`) antes de realizar solicitudes a la red.

#### Ejemplo de Uso:
```bash
python manage.py sync_moves --generation 1 --local
```

---

### 2.5 `backfill_pokedex_types`
Recorre todas las entradas de Pokédex registradas y reasigna los tipos elementales históricos (`primary_type` y `secondary_type`) evaluando el atributo `past_types` de PokeAPI según la generación de cada juego.

```bash
python manage.py backfill_pokedex_types
```

#### Comportamiento:
- Convierte a Magnemite y Magneton en únicamente Eléctrico para juegos de Generación 1.
- Restaura a Clefairy, Clefable, Jigglypuff, Wigglytuff y Togepi al tipo Normal para juegos previos a la Generación 6.
- Ejecuta todas las modificaciones dentro de una transacción atómica de base de datos (`transaction.atomic()`).
