# 🧪 Guía de Pruebas y Aseguramiento de Calidad (Español)

## 1. Filosofía de Pruebas

La suite de pruebas automatizadas en `tracker/tests.py` garantiza la estabilidad de los flujos críticos del proyecto:
- **Aislamiento Total de Red**: Todas las pruebas se ejecutan contra bases de datos en memoria o fixtures locales simuladas, sin emitir tráfico real hacia PokeAPI.
- **Verificación de Contrato API**: Comprueba el formato de las respuestas JSON, códigos de estado HTTP y manejo de errores del endpoint AJAX de captura.
- **Validación de Integridad y Reglas de Negocio**: Verifica la resolución de tipos históricos, la cascada de traducción idiomática y la protección de datos personalizados.

---

## 2. Ejecución de Pruebas

Para ejecutar la suite completa de pruebas:
```bash
python manage.py test
```

Para ejecutar únicamente las pruebas de la aplicación tracker:
```bash
python manage.py test tracker
```

Para ejecutar una prueba específica:
```bash
python manage.py test tracker.tests.PokedexTrackerTests.test_toggle_catch_anonymous_user
```

Para ejecutar con reporte detallado:
```bash
python manage.py test -v 2
```

---

## 3. Catálogo de Casos de Prueba (20 Pruebas)

| Caso de Prueba | Área Evaluada | Criterio de Aprobación |
| :--- | :--- | :--- |
| `test_pokedex_view_status_and_content` | Vista Principal | Confirma código de estado HTTP 200, conteo de entradas en el contexto, nombre oficial del juego y renderizado de tipos en español. |
| `test_toggle_catch_anonymous_user` | Endpoint AJAX | Verifica generación automática de sesión, marcado de captura en `True`, porcentaje de completitud (100%) y liberación posterior a `False`. |
| `test_toggle_catch_authenticated_user` | Endpoint AJAX | Comprueba la vinculación de la captura a una instancia `auth.User` en lugar de una cookie de sesión. |
| `test_toggle_catch_invalid_payload` | Manejo de Errores | Asegura que peticiones JSON corruptas devuelvan HTTP 400 con mensaje de error informativo. |
| `test_toggle_catch_nonexistent_entry` | Manejo de Errores | Comprueba que identificadores de entrada inexistentes retornen código HTTP 404. |
| `test_localized_text_fallback` | Internacionalización | Prueba la cascada de 3 niveles: idioma primario (`es`) -> idioma secundario (`en`) -> texto de respaldo por defecto. |
| `test_resolve_types_for_generation` | Tipos Históricos | Valida que Magnemite sea Eléctrico puro en Gen 1 y Eléctrico/Acero en Gen 2+, y que Clefairy sea Normal en Gen 1 y Hada en Gen 6+. |
| `test_sync_pokemon_details_override` | Protección de Datos | Demuestra que los registros con `is_custom_override=True` se conservan intactos ante sincronizaciones automáticas. |
| `test_export_fixtures_util` | Sistema de Fixtures | Verifica que `export_tracker_fixtures()` genere un archivo JSON sintácticamente válido con todos los registros y metadatos correctos. |
| `test_pokedex_view_404` | Enrutamiento | Confirma que slugs de juego o Pokédex inexistentes devuelvan código HTTP 404. |

---

## 4. Integración Continua (CI/CD)

Para incorporar esta suite en flujos de integración continua (GitHub Actions, GitLab CI):
1. Iniciar un contenedor de servicio con PostgreSQL.
2. Definir las variables de entorno de conexión en el entorno de pruebas:
   ```env
   DB_NAME=test_pokedex_db
   DB_USER=postgres
   DB_PASSWORD=postgres
   DB_HOST=127.0.0.1
   DB_PORT=5432
   ```
3. Aplicar migraciones y ejecutar `python manage.py test --no-input`.
