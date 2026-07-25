# Agent-Reach Runtime

Runtime aislado y reproducible para adquisición de evidencia externa de EDARSA BOS.

## Propósito

Este componente proporciona las herramientas técnicas para consultar páginas web, RSS, YouTube y otras fuentes externas sin integrarlas directamente en el proceso principal del backend.

## Componentes canónicos

- Agent-Reach vendorizado en `third_party/agent-reach`.
- Python 3.11 en un entorno virtual exclusivo.
- Deno con versión fijada.
- yt-dlp y componentes EJS con versiones fijadas.
- FFmpeg y ffprobe instalados durante la construcción.
- Usuario de ejecución no root.
- Healthcheck local sin dependencia obligatoria de Internet.
- Contexto Docker mínimo.

## Archivos

- `Dockerfile`: definición reproducible de la imagen.
- `versions.lock`: versiones de imágenes y herramientas.
- `requirements.lock`: dependencias Python fijadas.
- `yt-dlp.conf`: configuración canónica de extracción.
- `healthcheck.sh`: contrato local de salud.
- `build.sh`: construcción y validación de la imagen.

## Construcción

```bash
infra/agent-reach/build.sh
```

El script construye y valida la imagen localmente. No la publica ni la despliega.

## Integración continua

El workflow `.github/workflows/agent-reach-runtime-audit.yml` ejecuta la construcción en GitHub Actions cuando cambian el runtime o la fuente vendorizada.

El workflow únicamente:

1. valida los archivos canónicos;
2. construye la imagen;
3. ejecuta el healthcheck;
4. verifica que el usuario de ejecución no sea root.

No publica imágenes y no realiza deploy.

## Reglas de arquitectura

1. No instalar dependencias durante el arranque.
2. No depender de rutas bajo `/root`.
3. No ejecutar como usuario root.
4. No instalar Agent-Reach dentro del entorno Python del backend.
5. No escribir directamente en las tablas canónicas de EDARSAHUB.
6. No guardar cookies, tokens ni secretos en Git.
7. No publicar ni desplegar una imagen sin autorización explícita.
8. Toda actualización debe modificar los locks y superar el workflow.

## Estado actual

El runtime está definido como infraestructura canónica, pero todavía no está conectado al backend ni desplegado en producción.
