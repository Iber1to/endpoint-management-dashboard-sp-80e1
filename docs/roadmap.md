# Roadmap

## Current Status
- Current released baseline: `v1.0.0`
- Next target release: `v1.1.0`

## v1.1.0 (Backlog Prioritario)

### Sync
1. Sync Jobs: detalle de errores por ejecucion (blob + motivo).
2. Sync Jobs: filtros por fecha/estado/fuente en historico.
3. Sync Jobs: retencion configurable de historial (`sync_runs`).

### Operacion
4. Politica de limpieza para datos temporales de ingesta y observabilidad de crecimiento.
5. Alertas basicas para fallos recurrentes de sync (error ratio por ejecucion).

### Calidad
6. Suite de tests para rutas de sync persistente y reglas de estado (`success/partial/failed`).
7. Playbook de troubleshooting para casos de mismatch en inventario.

## v1.2.0 (Siguiente Ola)
1. Reporte de capacidad para grandes volumenes (estimacion de blobs y tiempo).
2. Telemetria por etapa de sync (list/download/parse/persist).
3. Mejoras de UX en Endpoint History para trazar snapshots por ejecucion.

## Modo de Trabajo Recomendado (GitHub)
1. Crear milestone por version (ejemplo: `v1.1.0`).
2. Crear una issue por mejora concreta (no mezclar varias mejoras en una sola).
3. Etiquetas recomendadas:
   - `type:feature`
   - `type:bug`
   - `area:sync`
   - `priority:P0|P1|P2|P3`
4. Cada issue debe incluir:
   - problema actual,
   - impacto,
   - criterio de aceptacion,
   - plan de validacion.
5. Cerrar milestone solo cuando todo lo planificado este merged y verificado.

