# 🧪 Testing Guide & Quality Assurance (English)

## 1. Test Suite Philosophy

The test suite located in `tracker/tests.py` provides automated coverage across critical domain workflows:
- **Zero External Network Dependencies**: All unit tests run against local SQLite/PostgreSQL memory fixtures without hitting PokeAPI over the network.
- **Contract Verification**: Validates JSON payloads, status codes, and error formats for the AJAX catch toggle API.
- **Data Integrity Tests**: Ensures historical typing rules, localized string fallbacks, and custom override locks behave as specified.

---

## 2. Test Execution

To run the entire test suite:
```bash
python manage.py test
```

To run only the tracker application tests:
```bash
python manage.py test tracker
```

To run a specific test method:
```bash
python manage.py test tracker.tests.PokedexTrackerTests.test_toggle_catch_anonymous_user
```

To run with verbose output:
```bash
python manage.py test -v 2
```

---

## 3. Overview of Test Cases (20 Tests)

| Test Method | Focus Area | Verification Criteria |
| :--- | :--- | :--- |
| `test_pokedex_view_status_and_content` | Main View | Confirms HTTP 200 status, entry context count, localized game name, and Spanish type rendering. |
| `test_toggle_catch_anonymous_user` | AJAX Endpoint | Validates session creation, `is_caught` toggle to `True`, capture percentage (100%), and subsequent release toggle back to `False`. |
| `test_toggle_catch_authenticated_user` | AJAX Endpoint | Verifies capture record association with a registered `auth.User` instance rather than a session key. |
| `test_toggle_catch_invalid_payload` | Error Handling | Asserts that malformed JSON payloads return HTTP 400 with descriptive error messages. |
| `test_toggle_catch_nonexistent_entry` | Error Handling | Asserts that invalid `entry_id` values return HTTP 404. |
| `test_localized_text_fallback` | Internationalization | Tests 3-tier cascade: primary language (`es`) -> fallback language (`en`) -> default fallback string. |
| `test_resolve_types_for_generation` | Historical Typings | Tests Magnemite (Electric in Gen 1; Electric/Steel in Gen 2+) and Clefairy (Normal in Gen 1; Fairy in Gen 6+). |
| `test_sync_pokemon_details_override` | Data Protection | Proves that entries flagged with `is_custom_override=True` remain untouched during automated synchronizations. |
| `test_export_fixtures_util` | Fixtures System | Verifies that `export_tracker_fixtures()` generates valid JSON containing expected model entries and valid metadata. |
| `test_pokedex_view_404` | Routing | Confirms that non-existent game or pokedex slugs properly trigger HTTP 404 responses. |

---

## 4. Continuous Integration (CI) Guidance

When deploying to continuous integration pipelines (GitHub Actions, GitLab CI):
1. Provision a PostgreSQL service container.
2. Inject test database environment variables:
   ```env
   DB_NAME=test_pokedex_db
   DB_USER=postgres
   DB_PASSWORD=postgres
   DB_HOST=127.0.0.1
   DB_PORT=5432
   ```
3. Run migrations and execute `python manage.py test --no-input`.
