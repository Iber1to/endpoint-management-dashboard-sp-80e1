# Arquitectura del sistema

## Visión general

El sistema es una WebApp de tres capas desplegada mediante Docker Compose:

```
┌──────────────────────────────────────────────────────────┐
│                    Usuario (navegador)                    │
└────────────────────────┬─────────────────────────────────┘
                         │ HTTP :3000
┌────────────────────────▼─────────────────────────────────┐
│              Frontend  (nginx :80)                        │
│   React 18 · Vite · TypeScript · Tailwind CSS            │
│   TanStack Table/Query · Recharts · React Router v6      │
│                                                           │
│   /api/* ──proxy──► backend:8000/api/*                   │
└────────────────────────┬─────────────────────────────────┘
                         │ HTTP :8000
┌────────────────────────▼─────────────────────────────────┐
│              Backend  (uvicorn)                           │
│   FastAPI · SQLAlchemy 2.x · Pydantic v2                 │
│   APScheduler · azure-storage-blob · BeautifulSoup4      │
└────────────────────────┬─────────────────────────────────┘
                         │ TCP :5432
┌────────────────────────▼─────────────────────────────────┐
│              PostgreSQL 16                                │
└───────────────────────────────────────────────────────────┘
                         ▲
         Azure Blob Storage (SAS Token)
```

El frontend nunca se comunica directamente con el backend usando una URL externa. Todas las peticiones `/api/*` son proxiadas por nginx al servicio `backend` dentro de la red Docker interna, sin exponer la URL del backend al navegador.

---

## Servicios Docker

| Servicio | Imagen | Puerto interno | Puerto externo |
|---|---|---|---|
| `postgres` | postgres:16-alpine | 5432 | — |
| `backend` | build local | 8000 | `BACKEND_PORT` (default 8000) |
| `frontend` | build local (nginx) | 80 | `FRONTEND_PORT` (default 3000) |

El backend espera a que postgres esté listo (healthcheck con `pg_isready`) antes de arrancar. El entrypoint ejecuta `alembic upgrade head` antes de iniciar uvicorn.

---

## Flujo de datos

### 1. Ingesta desde Azure Blob Storage

```
Azure Blob Storage
       │
       │  list_blobs()
       ▼
BlobStorageService
       │  clasifica por nombre:
       │  hardware_<endpoint>_<ts>.json
       │  software_<endpoint>_<ts>.json
       ▼
InventoryIngestionService
       ├── HardwareParserService  ──► endpoint, hardware, security, network, disks
       └── SoftwareParserService  ──► installed_software (raw)
              │
              ▼
       SoftwareNormalizationService
              │  normalize_name(), normalize_publisher()
              │  compute_dedupe_hash(), classify_software()
              ▼
       PostgreSQL (snapshot + tablas hijas)
```

Cada blob se procesa dentro de un savepoint (`BEGIN NESTED`) para aislar fallos individuales sin afectar al resto de la sesión.

### 2. Evaluación de Windows Updates

```
endpoint_hardware (OSBuild + OSRevision)
       │
       │  full_build = OSBuild.OSRevision
       ▼
WindowsUpdateEvaluationService
       │  busca coincidencia exacta en windows_patch_reference
       │  si no existe: revisión inferior más cercana (inferred=True)
       ▼
windows_update_status
       │  compliance_status: up_to_date / behind_1_month /
       │                      behind_2_plus_months / unknown
       ▼
/api/updates/compliance
```

### 3. Sincronización del catálogo de parches

```
Microsoft Learn (HTML)
       │  httpx GET
       ▼
WindowsPatchCatalogService
       │  BeautifulSoup4: extrae tablas con columnas build/KB/date
       │  construye full_build, patch_month, kb_article
       │  limpia is_latest_for_branch en ramas afectadas
       ▼
windows_patch_reference (upsert por full_build + kb_article)
```

---

## Estructura del backend

```
app/
├── main.py                  # FastAPI app, CORS, lifespan, routers
├── core/
│   ├── config.py            # Pydantic Settings (env vars)
│   ├── security.py          # Fernet encrypt/decrypt, mask_token
│   ├── logging.py           # Structlog setup
│   └── scheduler.py         # APScheduler (AsyncIOScheduler)
├── db/
│   ├── base.py              # DeclarativeBase
│   ├── session.py           # SessionLocal, get_db (con rollback)
│   └── models/              # 10 ficheros de modelos SQLAlchemy
├── schemas/                 # Pydantic v2 request/response schemas
├── api/routes/              # 7 routers FastAPI
├── services/                # Lógica de negocio (sin dependencias FastAPI)
└── jobs/                    # Funciones invocadas por APScheduler
```

### Tareas programadas (APScheduler)

| Job | Intervalo | Configurable vía |
|---|---|---|
| `sync_patch_catalog` | `PATCH_CATALOG_SYNC_INTERVAL_MINUTES` (default 1440 min) | `.env` |
| `evaluate_all_updates` | `INVENTORY_SYNC_INTERVAL_MINUTES` (default 60 min) | `.env` |

La sincronización de inventario desde Blob Storage se lanza manualmente (`POST /api/sync/run`) o puede activarse desde la UI. La sincronización programada automática de inventario está preparada para activarse mediante el scheduler cuando se configure.

---

## Seguridad

### SAS Token
- Se almacena cifrado con **Fernet** (criptografía simétrica, AES-128-CBC + HMAC-SHA256).
- La clave de cifrado se lee de `ENCRYPTION_KEY`. Si no está configurada, el backend falla al arrancar con un `RuntimeError`.
- La API nunca devuelve el token completo; sólo expone `sas_token_hint` (primeros 4 + `****` + últimos 4 caracteres).
- El token se pasa al Azure SDK como credencial separada, nunca en la URL, para evitar que aparezca en logs o trazas.

### Base de datos
- Contraseñas sin defaults en `docker-compose.yml`; deben configurarse explícitamente en `.env`.
- Transacciones con rollback explícito en el generador `get_db`.
- Savepoints por blob en `run_sync` para aislar errores de parseo.

### Contenedor backend
- Proceso ejecutado como usuario no-root `appuser`.

### Validación de entrada
- Patrones regex en reglas de compliance validados con `re.compile()` antes de persistir (protección contra ReDoS).

---

## Modelo de snapshots

Cada vez que se importa un archivo de hardware se crea un `EndpointSnapshot`. Los snapshots anteriores se marcan `is_current=False`. Las tablas hijas (`endpoint_hardware`, `endpoint_security`, `endpoint_network_adapters`, `endpoint_disks`, `installed_software`) referencian al snapshot activo.

Esto permite:
- Consultar siempre el estado actual mediante `is_current=True`
- Acceder al histórico completo por endpoint ordenado por `snapshot_at`
- Reimportar datos de forma idempotente (el etag del blob evita reprocesar)

---

## Normalización de software

El servicio `SoftwareNormalizationService` aplica:

| Campo | Transformación |
|---|---|
| `normalized_name` | Lowercase, elimina versiones numéricas del nombre, colapsa espacios |
| `normalized_publisher` | Lowercase, elimina Ltd/Inc/Corp, normaliza Microsoft/Adobe/etc. |
| `dedupe_hash` | SHA-256 de `(snapshot_id, software_name, software_version, app_source)` |
| clasificación | Detecta browsers, security tools, collaboration, frameworks, runtimes |

El inventario consolidado filtra por `is_current=True` y agrupa por `normalized_name`.
