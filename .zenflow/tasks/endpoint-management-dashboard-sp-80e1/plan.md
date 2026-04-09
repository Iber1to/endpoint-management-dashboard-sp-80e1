# Endpoint Management Dashboard — Implementation Plan

## Overview
Full-stack WebApp: React/Vite frontend + FastAPI backend + PostgreSQL + Docker Compose.
Data source: Azure Blob Storage via SAS Token (`hardware_*.json`, `software_*.json`).

### [x] Step 1: Project scaffolding and Docker Compose
- .gitignore, .env.example
- docker-compose.yml (frontend, backend, postgres)
- backend/Dockerfile, frontend/Dockerfile
- backend requirements.txt, alembic.ini skeleton

### [x] Step 2: Backend — DB models and Alembic
- app/core/config.py, security.py, logging.py
- app/db/base.py, session.py
- All SQLAlchemy models: endpoints, snapshots, hardware, security, network, disks, software, updates, datasource
- Alembic env.py + initial migration

### [x] Step 3: Backend — Services and Jobs
- blob_storage_service.py
- hardware_parser_service.py, software_parser_service.py
- software_normalization_service.py
- inventory_ingestion_service.py
- windows_patch_catalog_service.py
- windows_update_evaluation_service.py
- compliance_service.py
- jobs: sync_inventory_job, sync_patch_catalog_job, evaluate_updates_job
- app/core/scheduler.py

### [x] Step 4: Backend — API routes and schemas
- Pydantic schemas for all domains
- Routes: endpoints, software, updates, settings, sync, rules, overview
- app/main.py with CORS, router registration

### [x] Step 5: Frontend — Foundation
- Vite + React + TypeScript + Tailwind setup
- package.json, vite.config.ts, tailwind.config, tsconfig
- App layout (sidebar nav, header)
- React Router setup
- API service layer (api.ts, endpoints.ts, software.ts, updates.ts, settings.ts, sync.ts)
- Shared types

### [x] Step 6: Frontend — Pages
- OverviewPage (KPI cards + charts)
- EndpointsPage (filterable table with TanStack Table)
- EndpointDetailPage (tabbed: hardware, security, network, disks, software, updates, history)
- SoftwarePage (aggregated software inventory with filters)
- WindowsUpdatesPage (compliance table + charts)
- PatchCatalogPage (catalog management)
- SyncJobsPage (sync status and file list)
- SettingsPage (Blob Storage configuration form)

### [x] Step 7: Security and correctness fixes (code review)
- C1: SAS token passed as credential (not in URL) to Azure SDK
- C2: ENCRYPTION_KEY empty → RuntimeError (no silent fallback)
- C3: decrypt_value propagates exceptions; run_sync catches and records error
- C4: Pagination — windows_version and patch_status filters pushed into SQL subqueries
- C5: Dockerfile: removed `RUN alembic upgrade head || true`; added entrypoint.sh
- C6: docker-compose.yml: removed `:-changeme` password defaults
- C7: Removed hardcoded VITE_API_BASE_URL; nginx proxies /api/ → backend (relative URL)
- I8: N+1 in /updates/compliance fixed with joinedload(WindowsUpdateStatus.endpoint)
- I9: get_db: added explicit db.rollback() on exception before re-raise
- I10: run_sync: each blob's ingest wrapped in db.begin_nested() savepoint
- I11: sync.py: errors collected per source, all sources processed, error summary returned
- I12: overview.py: replaced Python loops with SQL func.count() aggregation
- I13: sync_patch_catalog: clears is_latest_for_branch on affected branches before upsert
- I14: rules.py: regex patterns validated with re.compile() before saving (ReDoS guard)
- I15: backend Dockerfile: adduser + USER appuser (non-root)
- S16: settings.ts: name? → name (required field)
- S17: sas_token_hint stored at save time; GET /settings/blob reads hint directly
- S18: dateutil import moved to module level in software_parser_service.py
- S19: Hardcoded "es-ES" locale replaced with undefined (browser locale)
