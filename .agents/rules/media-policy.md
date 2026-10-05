---
trigger: glob
description: Política estricta de preservación, no sobreescritura, estandarización y exclusión de Git para assets multimedia (sprites, imágenes, iconos, audios)
globs:
  - "media/**"
  - "tracker/scripts/**"
---

# Política de Manejo de Assets Multimedia (Media Policy)

Esta regla rige de forma estricta todo tratamiento de archivos de imagen, sprites, iconos, audios y cualquier asset binario en el proyecto.

## 1. Inmutabilidad y Protección de Archivos Existentes
- **Queda terminantemente prohibido editar, recortar, recomprimir, alterar o sobreescribir** cualquier archivo multimedia existente en `media/`, `static/` o subdirectorios.
- Todos los assets existentes deben tratarse de forma estricta como recursos de **solo lectura**.

## 2. Procesamiento No Destructivo
- Si se requiere manipular o procesar assets, debe realizarse obligatoriamente mediante scripts técnicos que traten los archivos de origen como inmutables y nunca reemplacen el archivo original.

## 3. Estandarización de Nombres en Nuevos Assets
- Cuando se incorporen o descarguen nuevos recursos multimedia (sprites, GIFs, audios, iconos) desde fuentes externas y sus nombres de archivo sean extraños, crípticos o incompatibles con las convenciones del proyecto:
  1. **Se permite renombrarlos** a nivel de sistema de archivos para adaptarlos a la nomenclatura estándar del proyecto (por ejemplo: `media/pokemon/icons/gen3/<id>.png`, `media/pokemon/animated/<id>.gif` o `media/pokemon/cries/<id>.ogg`).
  2. **Sin alteración de contenido:** El contenido binario, píxeles y pistas de audio deben permanecer 100% idénticos.
  3. **Obligación de notificación previa:** Es obligatorio informar al usuario qué archivo se renombrará, cuál será su nuevo nombre bajo el estándar y el motivo técnico antes de proceder.

## 4. Consentimiento Previo para Nuevos Archivos Derivados
- No se debe generar ni guardar ningún nuevo archivo derivado (como un `.gif` animado, nuevo formato de audio o variación gráfica) sin antes avisar al usuario, explicar la necesidad y obtener su aprobación explícita.

## 5. Exclusión Estricta de Git
- Ningún archivo de `media/`, sprite, icono o audio debe agregarse al control de versiones (`git add`).
- Deben respetarse siempre las exclusiones de `.gitignore` (`media/`, `*.png`, `*.jpg`, `*.gif`, `*.mp3`, `*.ogg`, etc.) salvo que el usuario lo solicite de manera directa y específica.
