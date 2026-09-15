# 📚 Pokédex Global Tracker — Documentación Técnica (Español)

Bienvenido a la documentación técnica detallada de **Pokédex Global Tracker**. Aquí encontrarás guías exhaustivas sobre la arquitectura, modelado de datos, tuberías de sincronización, diseño de interfaz, herramientas administrativas y pruebas automatizadas.

---

## 📑 Tabla de Contenidos

| Documento | Descripción |
| :--- | :--- |
| **[1. Arquitectura y Diseño](arquitectura.md)** | Arquitectura de alto nivel, flujo de peticiones cliente-servidor, estrategia Offline-First y modelo de concurrencia. |
| **[2. Modelos de Base de Datos y Esquemas](modelos-de-datos.md)** | Análisis a fondo de los modelos ORM (`Game`, `Pokedex`, `Pokemon`, `PokedexEntry`, `UserPokemonCatch`, `Move`), restricciones, índices y campos JSON. |
| **[3. Referencia de Comandos de Gestión](comandos-de-gestion.md)** | Manual operativo de los 5 comandos de consola CLI (`import_pokedex`, `sync_pokemon_cache`, `sync_pokemon_details`, `sync_moves`, `backfill_pokedex_types`). |
| **[4. Endpoints de API y Vistas](api-y-endpoints.md)** | Especificación de controladores de vista, endpoint AJAX `/api/catch/toggle/`, sesiones anónimas vs usuarios registrados y gestión de errores. |
| **[5. Diseño de Interfaz Estilo Cómic](interfaz-y-componentes.md)** | Sistema de diseño cómic/retro, integración con Tailwind CSS, modales interactivos dinámicos, sistema de audio (gritos en 8 bits vs modernos) y responsividad. |
| **[6. Personalización del Administrador y Fixtures](administracion-y-fixtures.md)** | Personalizaciones del panel Django Admin, mecanismo de protección manual `is_custom_override` y exportador/importador de respaldos JSON. |
| **[7. Guía de Pruebas y Aseguramiento de Calidad](guia-de-pruebas.md)** | Ejecución de la suite de pruebas, casos de prueba (20 tests), aislamiento de red y verificación de canon histórico. |

---

## 🧭 Pilares Técnicos del Proyecto

1. **Django 6.1.1 + Python 3.12+**: Uso de las capacidades modernas de Django, conector nativo `psycopg3` y funciones auxiliares fuertemente tipadas.
2. **Persistencia Relacional en PostgreSQL**: Esquema optimizado con índices compuestos, integridad referencial y campos nativos `JSONField`.
3. **Resiliencia ante PokeAPI**: Algoritmo con control de tasa (*rate-limiting*), retardos de cortesía, retroceso exponencial con variación aleatoria (*jitter*) y almacenamiento en caché local.
4. **Fidelidad Histórica al Canon Pokémon**: Ajuste dinámico de tipos elementales y gritos de audio según la generación del juego seleccionado.
