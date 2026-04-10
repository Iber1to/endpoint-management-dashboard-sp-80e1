# Endpoint Management Dashboard

WebApp de gestión de endpoints para inventario de hardware/software, cumplimiento de seguridad y seguimiento de actualizaciones mensuales de Windows. Los datos se obtienen desde **Azure Blob Storage** mediante autenticación por **SAS Token**.

## Índice

- [Requisitos](#requisitos)
- [Inicio rápido](#inicio-rápido)
- [Variables de entorno](#variables-de-entorno)
- [Estructura del proyecto](#estructura-del-proyecto)
- [Funcionalidades](#funcionalidades)
- [Origen de datos](#origen-de-datos)
- [Desarrollo local](#desarrollo-local)
- [API](#api)

---

## Requisitos

- Docker 24+ y Docker Compose v2
- Una clave Fernet válida para cifrar el SAS token en base de datos

Generar `ENCRYPTION_KEY`:
```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

---

## Inicio rápido

```bash
# 1. Copiar y rellenar variables de entorno
cp .env.example .env

# 2. Editar .env con valores reales (ver sección Variables de entorno)
# POSTGRES_PASSWORD, APP_SECRET_KEY y ENCRYPTION_KEY son obligatorias

# 3. Levantar todos los servicios
docker compose up -d

# 4. La aplicación estará disponible en:
#    Frontend:  http://localhost:3000
#    Backend:   http://localhost:8000
#    API Docs:  http://localhost:8000/docs
```

Las migraciones de base de datos se ejecutan automáticamente al arrancar el contenedor `backend`.

---

## Variables de entorno

Copiar `.env.example` a `.env` y ajustar los valores:

| Variable | Descripción | Obligatoria |
|---|---|---|
| `POSTGRES_DB` | Nombre de la base de datos | Sí |
| `POSTGRES_USER` | Usuario de PostgreSQL | Sí |
| `POSTGRES_PASSWORD` | Contraseña de PostgreSQL | Sí |
| `DATABASE_URL` | URL de conexión completa | Sí |
| `APP_ENV` | Entorno (`production` / `development`) | No |
| `APP_SECRET_KEY` | Clave secreta de la aplicación (≥32 chars) | Sí |
| `ENCRYPTION_KEY` | Clave Fernet para cifrar SAS tokens | Sí |
| `DEFAULT_TIMEZONE` | Zona horaria (`Europe/Madrid`) | No |
| `BACKEND_PORT` | Puerto del backend (default: `8000`) | No |
| `FRONTEND_PORT` | Puerto del frontend (default: `3000`) | No |
| `PATCH_CATALOG_SYNC_INTERVAL_MINUTES` | Frecuencia de sync del catálogo de parches (default: `1440`) | No |
| `INVENTORY_SYNC_INTERVAL_MINUTES` | Frecuencia de evaluación de updates (default: `60`) | No |

> **Importante**: `ENCRYPTION_KEY` debe ser una clave Fernet válida de 32 bytes en base64. Si no se configura, el backend rechazará el arranque con un error claro.

---

## Estructura del proyecto

```
endpoint-dashboard/
├── docker-compose.yml
├── .env.example
├── backend/
│   ├── Dockerfile
│   ├── entrypoint.sh          # Ejecuta migraciones y arranca uvicorn
│   ├── requirements.txt
│   ├── alembic.ini
│   ├── alembic/versions/      # Migraciones de base de datos
│   └── app/
│       ├── main.py
│       ├── core/              # Config, seguridad, logging, scheduler
│       ├── db/models/         # Modelos SQLAlchemy
│       ├── schemas/           # Schemas Pydantic
│       ├── api/routes/        # Endpoints FastAPI
│       ├── services/          # Lógica de negocio
│       └── jobs/              # Tareas programadas
└── frontend/
    ├── Dockerfile
    ├── nginx.conf             # Proxy /api/ → backend:8000
    └── src/
        ├── pages/             # Vistas principales
        ├── components/        # Componentes reutilizables
        ├── services/          # Clientes API
        ├── types/             # Tipos TypeScript
        └── utils/             # Utilidades
```

---

## Funcionalidades

### Dashboard general
Vista ejecutiva con KPIs: total de endpoints, cumplimiento de BitLocker y TPM, estado de parches Windows y distribución por fabricante/versión de SO.

### Inventario de endpoints
Tabla filtrable con búsqueda por hostname, fabricante, modelo, versión de Windows, estado BitLocker/TPM y cumplimiento de updates. Paginación en base de datos.

### Detalle de endpoint
Vista por dispositivo con secciones de hardware, seguridad, red, discos, software instalado, estado de actualizaciones e histórico de snapshots.

### Inventario de software
Vista agregada por aplicación con conteo de instalaciones por endpoint. Filtros por fuente (`Registry` / `Appx`), tipo (`Win32` / `ModernApp`), ocultando componentes del sistema y frameworks.

### Windows Updates
Módulo de seguimiento de parches mensuales basado en `OSBuild.OSRevision`. Correlación automática con el catálogo de Microsoft Learn para determinar KB, mes de parche y estado de cumplimiento (`up_to_date`, `behind_1_month`, `behind_2_plus_months`, `unknown`).

### Catálogo de parches
Tabla de referencia `full_build → KB → patch_month` sincronizada desde [Microsoft Learn](https://learn.microsoft.com/en-us/windows/release-health/windows11-release-information). Soporta sincronización manual y programada.

### Configuración
Pantalla administrativa para configurar Azure Blob Storage (URL, contenedor, SAS token, prefijo). El SAS token se almacena cifrado con Fernet y nunca se expone completo en la API.

### Sincronización
Ingesta manual o programada de blobs. Clasifica automáticamente archivos `hardware_*.json` y `software_*.json`, los correlaciona por endpoint y timestamp, y registra el estado de cada archivo procesado.

---

## Origen de datos

Los archivos se obtienen desde Azure Blob Storage con el siguiente patrón de nombres:

```
hardware_<ENDPOINT>_<YYYYMMDD>_<HHmmss>.json
software_<ENDPOINT>_<YYYYMMDD>_<HHmmss>.json
```

Ejemplo:
```
hardware_00200NPT002_20260407_121010.json
software_00200NPT002_20260407_121010.json
```

El SAS token se configura desde la UI en **Settings** y se almacena cifrado en base de datos. No es necesario modificar ningún archivo de despliegue para rotar el token.

---

## Desarrollo local

### Backend (sin Docker)

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt

# Configurar variables de entorno o crear .env en backend/
set DATABASE_URL=postgresql+psycopg://dashboard:password@localhost:5432/endpoint_dashboard
set ENCRYPTION_KEY=<clave_fernet>

alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

### Frontend (sin Docker)

```bash
cd frontend
npm install
npm run dev
# Disponible en http://localhost:5173
# El proxy de Vite redirige /api → http://localhost:8000
```

---

## API

La documentación interactiva OpenAPI está disponible en `http://localhost:8000/docs` cuando el backend está en ejecución.

Documentación detallada de contratos en [`docs/api-contracts.md`](docs/api-contracts.md).

---

## S4 Operational Additions

### Observability
- `GET /health` (public liveness)
- `GET /health/details` (requires read API key)
- `GET /metrics` (Prometheus format, requires read API key)
- All responses include `X-Request-ID` for trace correlation.

### Production environment template
Use `/.env.production.example` as baseline for production deployments.

### Backend tests and CI
- Local test command:
```bash
PYTHONPATH=backend pytest -q backend/tests
```
- GitHub Actions workflow: `.github/workflows/backend-tests.yml`

### Production runbook
See `docs/runbook-production.md` for deploy, smoke tests, backup/restore, and rollback.
