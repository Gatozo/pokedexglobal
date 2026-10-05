---
trigger: model_decision
description: Flujo de ejecución quirúrgica de pruebas Django con --keepdb. Solo aplicar cuando se modifique código activamente o se soliciten pruebas; omitir en charlas de análisis o consultas.
---

# Flujo Quirúrgico de Ejecución de Pruebas

Esta regla define cómo y cuándo los agentes deben ejecutar pruebas automatizadas en el proyecto.

## 1. No Ejecución en Conversaciones Consultivas o de Análisis (Ahorro de Tokens)
- **Queda estrictamente prohibido ejecutar pruebas** durante charlas, preguntas/respuestas, diagnósticos, consultas teóricas o revisiones exploratorias donde no se haya aplicado ningún cambio de código.
- No gastar tokens ni llamadas de herramientas ejecutando pruebas a menos que se haya aplicado una modificación concreta en el código o el usuario lo solicite expresamente.

## 2. Ejecución Focalizada por Módulo (Prohibido correr la suite completa indiscriminadamente)
Cuando se apliquen modificaciones de código, el agente debe deducir automáticamente el área afectada y ejecutar **únicamente** el submódulo correspondiente con `--keepdb`:

- **Autenticación (login, registro, formularios, sesiones, contraseñas):**
  `python manage.py test tracker.tests.test_auth --keepdb`
- **Vistas, componentes HTML, AJAX toggle o interfaz:**
  `python manage.py test tracker.tests.test_views --keepdb`
- **Catálogos de Pokémon y datos regionales (Gen 1, Gen 2, Gen 3):**
  `python manage.py test tracker.tests.test_catalogs --keepdb`
- **Fixtures y mecánicas de Gen 2 (exclusivos, Unown, crianza, piedras):**
  `python manage.py test tracker.tests.test_fixtures --keepdb`
- **Invariante específico de interactividad frontend:**
  `python manage.py test tracker.tests.test_views.FrontendInteractivityInvariantsTests --keepdb`

## 3. Uso Obligatorio de `--keepdb`
- Todo comando de prueba en el entorno de desarrollo debe incluir siempre la bandera `--keepdb` para reutilizar la base de datos de pruebas existente y evitar el costo de destrucción y recreación del esquema.

## 4. Suite Completa Solo con Causa Justificada
- La suite completa (`python manage.py test --keepdb`) únicamente debe ejecutarse cuando:
  1. El usuario lo solicite expresamente (ej: *"corre todas las pruebas"*, *"pasa la suite completa"*).
  2. Se realicen cambios transversales de infraestructura (`pokedex/settings.py`, nuevas migraciones globales de base de datos o refactorizaciones profundas compartidas).
