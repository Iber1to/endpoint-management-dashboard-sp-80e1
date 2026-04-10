# Runbook de Producción

## 1) Pre-requisitos
- Docker 24+ y Docker Compose v2
- Acceso al repositorio y al host de despliegue
- Secrets de producción generados:
  - `APP_SECRET_KEY` (>= 32 caracteres aleatorios)
  - `ENCRYPTION_KEY` (Fernet válido)
  - `ADMIN_API_KEY`, `OPERATOR_API_KEY`, `READONLY_API_KEY` (>= 16 caracteres)

Usar como base: `/.env.production.example`.

## 2) Despliegue seguro
1. Crear `.env` en el host con valores reales de producción.
2. Verificar que no se usan valores de test (`admin-test-key`, `operator-test-key`, `read-test-key`).
3. Levantar servicios:
   ```bash
   docker compose up -d --build
   ```
4. Comprobar estado:
   ```bash
   docker compose ps
   docker compose logs --tail=100 backend frontend postgres
   ```

## 3) Smoke tests post-despliegue
1. Health público:
   ```bash
   curl -s http://localhost:8000/health
   ```
2. Health operativo autenticado:
   ```bash
   curl -s -H "X-API-Key: <READONLY_API_KEY>" http://localhost:8000/health/details
   ```
3. Métricas:
   ```bash
   curl -s -H "X-API-Key: <READONLY_API_KEY>" http://localhost:8000/metrics
   ```
4. Flujo crítico:
   - `POST /api/settings/blob`
   - `POST /api/sync/run`
   - `GET /api/updates/compliance`

## 4) Backup y restore PostgreSQL

### Backup
```bash
docker compose exec -T postgres pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB" > backup_endpoint_dashboard.sql
```

### Restore
```bash
cat backup_endpoint_dashboard.sql | docker compose exec -T postgres psql -U "$POSTGRES_USER" "$POSTGRES_DB"
```

## 5) Rotación de secretos
1. Generar nuevo secreto (`APP_SECRET_KEY` y API keys).
2. Actualizar `.env`.
3. Reiniciar backend:
   ```bash
   docker compose up -d --build backend
   ```
4. Validar:
   - `GET /health`
   - `GET /health/details`
   - Peticiones autenticadas con nuevas keys.

Nota: al rotar `ENCRYPTION_KEY` hay que planificar re-cifrado de tokens SAS ya guardados, o volver a guardar configuración de Blob desde Settings.

## 6) Diagnóstico rápido de incidencias
- Estado contenedores:
  ```bash
  docker compose ps
  ```
- Logs backend:
  ```bash
  docker compose logs --tail=200 backend
  ```
- Últimos fallos de sync:
  - `GET /api/sync/status`
  - `GET /api/sync/files?status=error&limit=100`
- Correlación de requests:
  - Revisar cabecera `X-Request-ID` en respuestas y buscar esa traza en logs.

## 7) Rollback
1. Identificar commit estable previo.
2. Volver a ese commit en el host.
3. Rebuild y restart:
   ```bash
   docker compose up -d --build
   ```
4. Repetir smoke tests.

## 8) Checklist mínima de alertas
- Backend no healthy > 2 minutos.
- Frontend no healthy > 2 minutos.
- Error rate HTTP (5xx) sostenida.
- `last_sync_status=error` en orígenes activos.
- Incremento anómalo de `unknown` en `/api/updates/compliance`.
