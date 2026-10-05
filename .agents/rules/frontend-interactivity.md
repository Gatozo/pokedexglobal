---
description: Invariante crítico de arquitectura frontend para interactividad inmediata y carga prioritaria de modales y tarjetas
globs:
  - "tracker/templates/**"
  - "tracker/static/**"
---

# Invariante de Arquitectura Frontend: Interactividad Inmediata

## 1. Principio Fundamental
Queda estrictamente prohibido introducir cambios, rediseños o refactorizaciones que bloqueen, retrasen o impidan que las tarjetas de Pokémon, botones de captura, filtros, modales o controles de audio funcionen de manera instantánea mientras la página continúa cargando o analizando el DOM.

## 2. Componentes Obligatorios e Inamovibles

### A. Preload de Módulos en `<head>` (`tracker/templates/tracker/pokedex_detail.html`)
- El `<head>` DEBE conservar siempre las etiquetas `<link rel="modulepreload">` para todos los módulos JavaScript de la aplicación (`main.js`, `cards.js`, `filters.js`, `modal_comic.js`, etc.).
- Esto permite la descarga paralela multiplexada desde el milisegundo cero sin esperar a que el parser llegue al final del documento.

### B. Capa Temprana de Despacho Prioritario (`tracker/templates/tracker/components/_scripts.html`)
- `_scripts.html` DEBE incluirse en `pokedex_detail.html` ANTES de la grilla `#pokemon-grid`.
- El bloque `<script id="pokedex-early-dispatcher">` es OBLIGATORIO y no debe moverse ni eliminarse:
  1. Expone inmediatamente stubs funcionales en `window` para `openPokemonModal`, `toggleCatch`, `openExclusivesModal`, `openTransfersModal`, `openStoneModal`, `toggleFilterPanel`, `setStatusFilter`, `setSpriteStyle`, etc.
  2. Implementa renderizado optimista instantáneo (<5 ms) para el modal cómic leyendo directamente el bloque `#entry-data-{id}` ya presente en el elemento de la tarjeta visible.
  3. Mantiene una cola de acciones `window.__pokedexActionQueue` para diferir cualquier sincronización con la API sin perder clics del usuario.
  4. Registra un interceptor en fase de captura (`capture: true`) en el `document` para capturar clics antes del bubble normal.

### C. Módulos ES6 con Carga Asíncrona (`_scripts.html` y `main.js`)
- La inclusión del módulo principal DEBE mantener el atributo `async`:
  `<script type="module" async src="{% static 'tracker/js/main.js' %}"></script>`
- En `tracker/static/tracker/js/main.js`:
  1. Al inicializarse, DEBE marcar `window.__pokedexReady = true`.
  2. DEBE procesar y vaciar inmediatamente `window.__pokedexActionQueue`.
  3. DEBE utilizar una función que compruebe `document.readyState !== 'loading'` antes de enganchar a `DOMContentLoaded` para evitar eventos perdidos por ejecución asíncrona.

## 3. Pruebas Automatizadas
Cualquier cambio en la interfaz debe someterse a la prueba específica con `--keepdb` para garantizar que el invariante siga pasando satisfactoriamente de forma casi instantánea:
`python manage.py test tracker.tests.test_views.FrontendInteractivityInvariantsTests --keepdb`
