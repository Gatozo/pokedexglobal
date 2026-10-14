# 📚 Pokédex Global Tracker — Documentación Técnica (Español)

Bienvenido a la documentación técnica detallada de **Pokédex Global Tracker**. Aquí encontrarás guías exhaustivas y actualizadas sobre la arquitectura, el modelado de datos, el servicio de catálogos en memoria, los componentes de interfaz, las herramientas de administración y las pruebas automatizadas.

---

## 📑 Tabla de Contenidos

| Documento | Descripción |
| :--- | :--- |
| **[1. Arquitectura y Diseño](arquitectura.md)** | Arquitectura de alto nivel, flujo de peticiones cliente-servidor, estrategia Offline-First, catálogos precompilados en memoria (0 ms SQL) y modelo de concurrencia. |
| **[2. Modelos de Base de Datos y Esquemas](modelos-de-datos.md)** | Análisis de los modelos ORM relacionales (`Game`, `Pokedex`, `UserPokemonCatch`), índices compuestos, restricciones únicas y estructura JSON de `CatalogEntry`. |
| **[3. Comandos de Gestión y Scripts](comandos-de-gestion.md)** | Manual operativo de comandos CLI para sincronización de activos multimedia (sprites, animaciones, iconos y gritos) y constructores de catálogo en `tracker/scripts/`. |
| **[4. Endpoints de API y Mapa de Rutas](api-y-endpoints.md)** | Especificación de controladores de vista, portal de autenticación, Game Hub (`/games/`), endpoints AJAX `/api/catch/toggle/` e `/api/unown-catch/toggle/`. |
| **[5. Diseño de Interfaz Estilo Cómic](interfaz-y-componentes.md)** | Sistema de diseño cómic/retro, integración con Tailwind CSS, Game Hub generacional, modales dinámicos, modo shiny, glifos de Unown y motor de audio dual. |
| **[6. Panel de Administración y Respaldo](administracion-y-fixtures.md)** | Personalizaciones del panel Django Admin, supervisión de capturas y exportador/importador de metadatos estructurales de juegos (`tracker.Game` y `tracker.Pokedex`). |
| **[7. Guía de Pruebas y Calidad](guia-de-pruebas.md)** | Ejecución de la suite modular de pruebas (173 tests), aislamiento de red, uso de `--keepdb` y verificación del canon histórico. |

---

## 🧭 Pilares Técnicos del Proyecto

1. **Django 6.1.1 + Python 3.12+**: Capacidades modernas de Django, conector nativo `psycopg3` y tipado estricto.
2. **Catálogos Precompilados en Memoria (0 ms SQL)**: Acceso instantáneo a los datos de la Pokédex en memoria vía `catalog_service.py` con 0 ms de latencia SQL.
3. **Persistencia Relacional Eficiente**: Esquema PostgreSQL optimizado para el progreso de capturas (`UserPokemonCatch`) con soporte para invitados y usuarios registrados.
4. **Fidelidad Canónica**: Toponimia oficial en castellano (WikiDex), resolución de tipos históricos por generación y motor de audio chiptune (8 bits) y orquestado.
