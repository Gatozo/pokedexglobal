# 🧪 Guía de Pruebas y Aseguramiento de Calidad (Español)

## 1. Filosofía de Pruebas y Cobertura

La suite de pruebas automatizadas de **Pokédex Global Tracker** comprende **173 pruebas unitarias y de integración** organizadas modularmente en `tracker/tests/`:

* **Aislamiento Total de Red (Offline-First)**: Todas las pruebas se ejecutan contra catálogos locales simulados o compilados y bases de datos de pruebas locales, sin emitir tráfico real hacia PokeAPI ni depender de conexiones externas.
* **Integridad Canónica de Datos**: Valida que los tipos históricos, ubicaciones oficiales en español y números de Pokédex coincidan con las reglas de cada generación.
* **Aislamiento de Sesiones y Capturas**: Comprueba que el progreso de capturas se mantenga estrictamente separado entre usuarios autenticados y sesiones de invitados.
* **Verificación de Contrato API**: Evalúa los códigos HTTP y respuestas JSON de los endpoints AJAX (`toggle_catch`, `toggle_unown_catch`, `check_username`).

---

## 2. Ejecución Focalizada con `--keepdb`

De acuerdo con el protocolo técnico del proyecto, las pruebas se deben ejecutar reutilizando la base de datos de pruebas mediante la bandera `--keepdb`, lo que reduce los tiempos de ejecución a tan solo 1 a 5 segundos por módulo.

### Comandos de Ejecución Modular:

* **Autenticación y Sesiones (29 pruebas):**
  ```bash
  python manage.py test tracker.tests.test_auth --keepdb
  ```
* **Vistas, Game Hub e Interactividad (34 pruebas):**
  ```bash
  python manage.py test tracker.tests.test_views --keepdb
  ```
* **Catálogos Compilados y Reglas de Juego (65 pruebas):**
  ```bash
  python manage.py test tracker.tests.test_catalogs --keepdb
  ```
* **Fixtures, Mecánicas de Gen 2 y Unown (45 pruebas):**
  ```bash
  python manage.py test tracker.tests.test_fixtures --keepdb
  ```

### Ejecución de una Prueba Específica:
```bash
python manage.py test tracker.tests.test_views.PokedexTrackerTests.test_toggle_catch_anonymous_user --keepdb
```

### Ejecución de la Suite Completa:
```bash
python manage.py test --keepdb
```

---

## 3. Desglose de Módulos de Prueba

| Módulo | Archivo | Tests | Áreas Evaluadas |
| :--- | :--- | :---: | :--- |
| **Autenticación** | `tracker/tests/test_auth.py` | 29 | Login, registro reactivo, modo invitado, hash de contraseñas y aislamiento de sesión. |
| **Vistas e Interfaz** | `tracker/tests/test_views.py` | 34 | Endpoints AJAX de captura normal y shiny, selector de juegos (Game Hub), gritos de audio e invariantes de plantilla. |
| **Catálogos y Canon** | `tracker/tests/test_catalogs.py` | 65 | Carga de catálogos JSON, tipos históricos por generación, zonas de encuentro en castellano y sprites de cartucho. |
| **Fixtures y Mecánicas** | `tracker/tests/test_fixtures.py` | 45 | Exportación de respaldos (`export_tracker_fixtures`), 26 glifos de Unown, piedras evolutivas y compatibilidad. |
