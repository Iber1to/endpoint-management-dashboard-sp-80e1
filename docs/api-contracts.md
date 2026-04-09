# Contratos API

La documentación interactiva OpenAPI está disponible en `http://localhost:8000/docs`.

Todos los endpoints tienen el prefijo `/api`.

---

## Overview

### `GET /api/overview`

Devuelve KPIs para el dashboard principal.

**Respuesta:**
```json
{
  "total_endpoints": 245,
  "recent_endpoints": 198,
  "by_manufacturer": [
    { "manufacturer": "HP", "count": 120 },
    { "manufacturer": "Lenovo", "count": 85 }
  ],
  "by_windows_version": [
    { "windows_version": "24H2", "count": 180 }
  ],
  "security": {
    "total": 245,
    "bitlocker_active": 230,
    "bitlocker_pct": 93.9,
    "tpm_active": 240,
    "tpm_pct": 97.9
  },
  "updates": {
    "total": 245,
    "up_to_date": 210,
    "behind_1_month": 25,
    "behind_2_plus_months": 10,
    "up_to_date_pct": 85.7
  }
}
```

---

## Endpoints

### `GET /api/endpoints`

Lista paginada de endpoints con estado resumido.

**Query params:**

| Param | Tipo | Descripción |
|---|---|---|
| `page` | int | Página (default: 1) |
| `page_size` | int | Registros por página (default: 50, max: 200) |
| `search` | string | Búsqueda por `computer_name` (ilike) |
| `manufacturer` | string | Filtro por fabricante (ilike) |
| `model` | string | Filtro por modelo (ilike) |
| `windows_version` | string | Filtro exacto por versión Windows (`24H2`, `23H2`, etc.) |
| `patch_status` | string | Filtro por estado de parche (`up_to_date`, `behind_1_month`, etc.) |

**Respuesta:**
```json
{
  "items": [
    {
      "id": 1,
      "computer_name": "PC-EJEMPLO-001",
      "manufacturer": "HP",
      "model": "EliteBook 840 G10",
      "os_name": "Microsoft Windows 11 Pro",
      "windows_version": "24H2",
      "full_build": "26100.3775",
      "last_seen_at": "2026-04-07T12:10:10Z",
      "bitlocker_protection_status": 1,
      "tpm_present": true,
      "patch_compliance_status": "up_to_date"
    }
  ],
  "total": 245,
  "page": 1,
  "page_size": 50
}
```

---

### `GET /api/endpoints/{id}`

Detalle completo del endpoint con snapshot actual.

**Respuesta:**
```json
{
  "id": 1,
  "computer_name": "PC-EJEMPLO-001",
  "manufacturer": "HP",
  "model": "EliteBook 840 G10",
  "serial_number": "CND1234567",
  "smbios_uuid": "...",
  "firmware_type": "UEFI",
  "bios_version": "T96 Ver. 01.06.00",
  "last_seen_at": "2026-04-07T12:10:10Z",
  "hardware": {
    "os_name": "Microsoft Windows 11 Pro",
    "windows_version": "24H2",
    "os_build": "26100",
    "os_revision": 3775,
    "full_build": "26100.3775",
    "memory_bytes": 17179869184,
    "cpu_name": "Intel(R) Core(TM) Ultra 5 125U",
    "cpu_cores": 12,
    "last_boot": "2026-04-06T08:00:00Z",
    "uptime_days": 1
  },
  "security": {
    "tpm_present": true,
    "tpm_ready": true,
    "tpm_enabled": true,
    "tpm_activated": true,
    "bitlocker_volume_status": "FullyEncrypted",
    "bitlocker_protection_status": 1,
    "bitlocker_lock_status": 0
  },
  "network_adapters": [...],
  "disks": [...],
  "software_count": 312,
  "patch_compliance_status": "up_to_date"
}
```

---

### `GET /api/endpoints/{id}/software`

Software instalado en el endpoint (snapshot actual).

**Query params:**

| Param | Tipo | Descripción |
|---|---|---|
| `app_source` | string | `Appx` o `Registry` |
| `app_type` | string | `ModernApp` o `Win32` |
| `hide_system` | bool | Ocultar componentes del sistema |

---

### `GET /api/endpoints/{id}/updates`

Historial de evaluaciones de Windows Update para el endpoint.

---

### `GET /api/endpoints/{id}/history`

Lista de snapshots históricos del endpoint.

**Respuesta:**
```json
[
  { "id": 5, "snapshot_at": "2026-04-07T12:10:10Z", "is_current": true, "registry_date": null },
  { "id": 3, "snapshot_at": "2026-03-10T09:00:00Z", "is_current": false, "registry_date": null }
]
```

---

## Software

### `GET /api/software`

Vista agregada de software por nombre normalizado.

**Query params:**

| Param | Tipo | Descripción |
|---|---|---|
| `page` / `page_size` | int | Paginación |
| `app_source` | string | `Appx` o `Registry` |
| `app_type` | string | `ModernApp` o `Win32` |
| `hide_system` | bool | Ocultar `system_component=true` |
| `hide_framework` | bool | Ocultar `is_framework=true` |
| `search` | string | Búsqueda por nombre normalizado |

**Respuesta:**
```json
{
  "items": [
    {
      "normalized_name": "microsoft edge",
      "display_name": "microsoft edge",
      "publisher": "microsoft corporation",
      "version_count": 3,
      "endpoint_count": 245,
      "latest_version": "134.0.3124.72",
      "app_type": "Win32",
      "app_source": "Registry"
    }
  ],
  "total": 580,
  "page": 1,
  "page_size": 50
}
```

---

## Windows Updates

### `GET /api/updates/compliance`

Estado de cumplimiento de parches por endpoint.

**Respuesta:**
```json
{
  "target_patch": "2026-03",
  "summary": {
    "up_to_date": 210,
    "behind_1_month": 25,
    "behind_2_plus_months": 10,
    "unknown": 0,
    "total": 245
  },
  "items": [
    {
      "endpoint_id": 1,
      "computer_name": "PC-EJEMPLO-001",
      "windows_version": "24H2",
      "full_build": "26100.3775",
      "kb_article": "KB5053598",
      "patch_month": "2026-03",
      "patch_label": "2026-03 Update",
      "compliance_status": "up_to_date",
      "months_behind": 0,
      "inferred": false,
      "evaluated_at": "2026-04-07T13:00:00Z"
    }
  ]
}
```

**Estados de `compliance_status`:**

| Valor | Descripción |
|---|---|
| `up_to_date` | Al día con el parche mensual objetivo |
| `behind_1_month` | Un mes de desfase |
| `behind_2_plus_months` | Dos o más meses de desfase |
| `preview_build` | Build de preview |
| `unsupported_branch` | Rama de Windows no soportada |
| `unknown` | No se pudo determinar |

---

### `GET /api/updates/overview`

Resumen de updates por estado y distribución por build.

---

### `GET /api/updates/catalog`

Lista el catálogo de referencia de parches Windows.

**Query params:**

| Param | Tipo | Descripción |
|---|---|---|
| `windows_version` | string | Filtro por versión (`24H2`, `23H2`, etc.) |
| `latest_only` | bool | Solo mostrar el último parche por rama |

**Respuesta (item):**
```json
{
  "id": 1,
  "product_name": "Windows 11",
  "windows_version": "24H2",
  "os_build": "26100",
  "os_revision": 3775,
  "full_build": "26100.3775",
  "kb_article": "KB5053598",
  "patch_month": "2026-03",
  "patch_label": "2026-03 Update",
  "release_date": "2026-03-11",
  "is_security_update": true,
  "is_preview": false,
  "is_latest_for_branch": true,
  "scraped_at": "2026-04-07T00:00:00Z"
}
```

---

### `GET /api/updates/catalog/status`

Estado de la última sincronización del catálogo.

```json
{
  "total_builds": 48,
  "last_synced_at": "2026-04-07T00:00:00Z",
  "catalog_version": "20260407"
}
```

---

### `POST /api/updates/catalog/sync`

Lanza una sincronización manual del catálogo desde Microsoft Learn.

```json
{ "success": true, "result": { "synced": 48 } }
```

---

### `POST /api/updates/evaluate`

Reevalúa el estado de updates para todos los endpoints.

```json
{ "success": true, "result": { "evaluated": 245, "errors": 0 } }
```

---

## Settings

### `GET /api/settings/blob`

Lista las configuraciones de origen de datos.

**Respuesta (item):**
```json
{
  "id": 1,
  "name": "produccion",
  "account_url": "https://mystorageaccount.blob.core.windows.net",
  "container_name": "inventory",
  "blob_prefix": "endpoints/",
  "sas_token_masked": "sv=2****=rw",
  "sync_frequency_minutes": 60,
  "is_active": true,
  "last_sync_at": "2026-04-07T12:00:00Z",
  "last_sync_status": "success",
  "last_error": null
}
```

> El token SAS nunca se devuelve completo. Solo se expone el hint (primeros 4 + `****` + últimos 4 chars).

---

### `POST /api/settings/blob`

Crea o actualiza una configuración de Blob Storage.

**Cuerpo:**
```json
{
  "name": "produccion",
  "account_url": "https://mystorageaccount.blob.core.windows.net",
  "container_name": "inventory",
  "sas_token": "sv=2022-11-02&ss=b&...",
  "blob_prefix": "endpoints/",
  "sync_frequency_minutes": 60,
  "is_active": true
}
```

El token SAS se cifra con Fernet antes de persistir. Si `name` ya existe, actualiza el registro.

---

### `POST /api/settings/blob/test`

Prueba la conexión con Azure Blob Storage sin guardar la configuración.

**Cuerpo:**
```json
{
  "account_url": "https://mystorageaccount.blob.core.windows.net",
  "container_name": "inventory",
  "sas_token": "sv=2022-11-02&ss=b&...",
  "blob_prefix": "endpoints/"
}
```

**Respuesta:**
```json
{
  "success": true,
  "containers_visible": true,
  "sample_blobs": [
    "endpoints/hardware_PC001_20260407_120000.json",
    "endpoints/software_PC001_20260407_120000.json"
  ],
  "error": null
}
```

---

## Sync

### `POST /api/sync/run`

Lanza una sincronización manual de todos los orígenes activos (o uno específico).

**Query params:**

| Param | Tipo | Descripción |
|---|---|---|
| `data_source_id` | int | (Opcional) ID de origen específico |

**Respuesta:**
```json
{
  "success": true,
  "stats": {
    "total": 120,
    "processed": 118,
    "errors": 2,
    "skipped": 0
  },
  "error": null
}
```

---

### `GET /api/sync/status`

Estado de sincronización de cada origen.

---

### `GET /api/sync/files`

Lista de archivos de inventario procesados con su estado.

**Query params:** `data_source_id`, `status` (`pending`/`processed`/`error`), `limit`.

---

## Rules

### `GET /api/rules/software`

Lista todas las reglas de compliance de software.

### `POST /api/rules/software`

Crea una regla de compliance. Los campos `product_match_pattern` y `publisher_match_pattern` son regex validadas antes de persistir.

**Cuerpo:**
```json
{
  "name": "CrowdStrike requerido",
  "rule_type": "required",
  "product_match_pattern": "crowdstrike",
  "publisher_match_pattern": "crowdstrike",
  "is_required": true,
  "is_forbidden": false,
  "severity": "critical",
  "is_active": true
}
```

### `DELETE /api/rules/software/{rule_id}`

Elimina una regla por ID.

---

## Health

### `GET /health`

Verificación de salud del servicio.

```json
{ "status": "ok" }
```
