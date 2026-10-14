# 🧪 Testing Guide & Quality Assurance (English)

## 1. Testing Philosophy & Coverage

The automated test suite of **Pokédex Global Tracker** consists of **173 unit and integration tests** organized across four modular suites in `tracker/tests/`:

* **Offline-First Isolation**: All tests run against local in-memory catalogs or test databases without making outbound HTTP requests to PokeAPI.
* **Canonical Data Integrity**: Validates that historical typings, localized Spanish locations, and Pokédex numbers strictly follow official generation rules.
* **Session & Catch Isolation**: Guarantees that progress remains isolated between authenticated users and guest sessions.
* **API Contract Verification**: Validates status codes, headers, and JSON payloads for AJAX endpoints (`toggle_catch`, `toggle_unown_catch`, `check_username`).

---

## 2. Fast Targeted Execution with `--keepdb`

In accordance with the project workflow, tests must be run using the `--keepdb` flag to reuse the test database, keeping execution times under 1 to 5 seconds per module.

### Modular Test Commands:

* **Authentication & Sessions (29 tests):**
  ```bash
  python manage.py test tracker.tests.test_auth --keepdb
  ```
* **Views, Game Hub & Interactivity (34 tests):**
  ```bash
  python manage.py test tracker.tests.test_views --keepdb
  ```
* **Compiled Catalogs & Canonical Rules (65 tests):**
  ```bash
  python manage.py test tracker.tests.test_catalogs --keepdb
  ```
* **Fixtures, Gen 2 Mechanics & Unown (45 tests):**
  ```bash
  python manage.py test tracker.tests.test_fixtures --keepdb
  ```

### Running a Specific Test:
```bash
python manage.py test tracker.tests.test_views.PokedexTrackerTests.test_toggle_catch_anonymous_user --keepdb
```

### Running the Full Test Suite:
```bash
python manage.py test --keepdb
```

---

## 3. Test Suite Breakdown

| Module | File | Tests | Key Focus Areas |
| :--- | :--- | :---: | :--- |
| **Authentication** | `tracker/tests/test_auth.py` | 29 | Login, reactive registration, guest sessions, password hashing, and session security. |
| **Views & UI** | `tracker/tests/test_views.py` | 34 | AJAX catch endpoints (normal and shiny), Game Hub, cry audio, and template invariants. |
| **Catalogs & Canon** | `tracker/tests/test_catalogs.py` | 65 | JSON catalog loading, historical typings per generation, Spanish location strings, and sprites. |
| **Fixtures & Mechanics** | `tracker/tests/test_fixtures.py` | 45 | Fixture exports (`export_tracker_fixtures`), 26 Unown forms, evolution stones, and breeding. |
