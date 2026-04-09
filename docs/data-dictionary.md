# Diccionario de datos

Descripción de todas las tablas de la base de datos PostgreSQL.

---

## `endpoints`

Una fila por equipo. Representa la identidad física del dispositivo.

| Columna | Tipo | Descripción |
|---|---|---|
| `id` | integer PK | Identificador interno |
| `endpoint_key` | varchar(255) UNIQUE | `computer_name` en mayúsculas, usado para deduplicación |
| `computer_name` | varchar(255) | Nombre del equipo tal como lo reporta el script |
| `serial_number` | varchar(255) | Número de serie del hardware |
| `smbios_uuid` | varchar(255) | UUID del firmware SMBIOS |
| `manufacturer` | varchar(255) | Fabricante del equipo (HP, Lenovo, Dell…) |
| `model` | varchar(255) | Modelo del equipo |
| `system_sku` | varchar(255) | SKU del sistema |
| `firmware_type` | varchar(50) | `UEFI` o `BIOS` |
| `bios_version` | varchar(255) | Versión del firmware |
| `bios_release_date` | timestamptz | Fecha de publicación del firmware |
| `install_date` | timestamptz | Fecha de instalación del SO |
| `last_seen_at` | timestamptz | Última vez que se importó un archivo del equipo |
| `created_at` | timestamptz | Fecha de creación del registro |
| `updated_at` | timestamptz | Última modificación |

**Índices:** `ix_endpoints_endpoint_key` (UNIQUE), `ix_endpoints_computer_name`

---

## `endpoint_snapshots`

Snapshot lógico por endpoint y fecha. Agrupa los datos de hardware y software de una misma importación.

| Columna | Tipo | Descripción |
|---|---|---|
| `id` | integer PK | Identificador interno |
| `endpoint_id` | integer FK → endpoints | Endpoint al que pertenece |
| `snapshot_at` | timestamptz | Timestamp del snapshot (del nombre del archivo) |
| `registry_date` | varchar | Fecha de registro según el campo `RegistryDate` del JSON |
| `hardware_file_id` | integer FK → inventory_files | Archivo de hardware que originó el snapshot |
| `software_file_id` | integer FK → inventory_files | Archivo de software asociado (nullable) |
| `is_current` | boolean | `true` solo para el snapshot más reciente del endpoint |
| `created_at` | timestamptz | Fecha de creación |

**Índices:** `(endpoint_id, snapshot_at DESC)`, `ix_endpoint_snapshots_endpoint_id`

---

## `endpoint_hardware`

Datos técnicos de SO, CPU, memoria y configuración de actualizaciones. Una fila por snapshot.

| Columna | Tipo | Descripción |
|---|---|---|
| `id` | integer PK | Identificador interno |
| `snapshot_id` | integer FK → endpoint_snapshots | Snapshot al que pertenece |
| `os_name` | varchar(255) | Nombre completo del SO |
| `windows_version` | varchar(50) | Versión de Windows (`24H2`, `23H2`, etc.) |
| `os_build` | varchar(50) | Build base (`26100`) |
| `os_revision` | integer | Revisión (`3775`) |
| `full_build` | varchar(50) | `os_build.os_revision` → `26100.3775` |
| `memory_bytes` | bigint | RAM total en bytes |
| `cpu_manufacturer` | varchar(255) | Fabricante de la CPU |
| `cpu_name` | varchar(500) | Modelo de la CPU |
| `cpu_cores` | integer | Número de núcleos físicos |
| `cpu_logical_processors` | integer | Procesadores lógicos |
| `pc_system_type` | integer | Tipo de sistema (portátil, escritorio…) |
| `pc_system_type_ex` | integer | Tipo de sistema extendido |
| `last_boot` | timestamptz | Última vez que arrancó el equipo |
| `uptime_days` | numeric | Días de uptime en el momento del inventario |
| `default_au_service` | varchar(255) | Servicio de actualización automática configurado |
| `au_metered` | boolean | Si la red está marcada como de uso medido |

---

## `endpoint_security`

Estado de BitLocker y TPM. Una fila por snapshot.

| Columna | Tipo | Descripción |
|---|---|---|
| `id` | integer PK | Identificador interno |
| `snapshot_id` | integer FK → endpoint_snapshots | Snapshot al que pertenece |
| `tpm_present` | boolean | TPM presente |
| `tpm_ready` | boolean | TPM listo para uso |
| `tpm_enabled` | boolean | TPM habilitado |
| `tpm_activated` | boolean | TPM activado |
| `tpm_managed_auth_level` | integer | Nivel de gestión de autorización del TPM |
| `bitlocker_mount_point` | varchar(10) | Letra de unidad protegida (e.g., `C:`) |
| `bitlocker_cipher` | varchar(100) | Algoritmo de cifrado (e.g., `XtsAes256`) |
| `bitlocker_volume_status` | varchar(100) | Estado del volumen (`FullyEncrypted`, etc.) |
| `bitlocker_protection_status` | integer | `1` = protegido, `0` = desprotegido |
| `bitlocker_lock_status` | integer | `0` = desbloqueado, `1` = bloqueado |

---

## `endpoint_network_adapters`

Una fila por adaptador de red por snapshot.

| Columna | Tipo | Descripción |
|---|---|---|
| `id` | integer PK | Identificador interno |
| `snapshot_id` | integer FK → endpoint_snapshots | Snapshot al que pertenece |
| `name` | varchar(255) | Nombre del adaptador |
| `interface_alias` | varchar(255) | Alias de interfaz |
| `interface_description` | varchar(500) | Descripción del driver |
| `mac_address` | varchar(50) | Dirección MAC |
| `link_speed` | varchar(50) | Velocidad del enlace |
| `status` | varchar(50) | Estado (`Up`, `Disconnected`, etc.) |
| `net_profile_name` | varchar(255) | Nombre del perfil de red |
| `ipv4_address` | varchar(100) | Dirección IPv4 |
| `ipv6_address` | varchar(255) | Dirección IPv6 |
| `ipv4_default_gateway` | varchar(100) | Gateway por defecto |
| `dns_server` | varchar(500) | Servidores DNS |

---

## `endpoint_disks`

Una fila por disco físico por snapshot.

| Columna | Tipo | Descripción |
|---|---|---|
| `id` | integer PK | Identificador interno |
| `snapshot_id` | integer FK → endpoint_snapshots | Snapshot al que pertenece |
| `device_id` | varchar(255) | ID del dispositivo |
| `friendly_name` | varchar(500) | Nombre legible del disco |
| `serial_number` | varchar(255) | Número de serie del disco |
| `media_type` | varchar(50) | `SSD`, `HDD`, `Unspecified` |
| `bus_type` | varchar(50) | `NVMe`, `SATA`, `USB`, etc. |
| `health_status` | varchar(50) | `Healthy`, `Warning`, `Unhealthy` |
| `operational_status` | varchar(50) | Estado operacional |
| `size_bytes` | bigint | Capacidad total en bytes |
| `wear` | integer | Indicador de desgaste (SSD, 0–100) |
| `temperature` | integer | Temperatura en °C |
| `temperature_max` | integer | Temperatura máxima registrada en °C |
| `read_errors_total` | bigint | Errores de lectura totales |
| `read_errors_uncorrected` | bigint | Errores de lectura no corregidos |
| `write_errors_total` | bigint | Errores de escritura totales |
| `write_errors_uncorrected` | bigint | Errores de escritura no corregidos |

---

## `installed_software`

Inventario crudo de software. Una fila por aplicación y snapshot.

| Columna | Tipo | Descripción |
|---|---|---|
| `id` | integer PK | Identificador interno |
| `snapshot_id` | integer FK → endpoint_snapshots | Snapshot al que pertenece |
| `endpoint_id` | integer FK → endpoints | Endpoint al que pertenece |
| `software_name` | varchar(500) | Nombre original de la aplicación |
| `software_version` | varchar(255) | Versión original |
| `publisher` | varchar(500) | Fabricante / publisher |
| `install_date` | date | Fecha de instalación |
| `architecture` | varchar(50) | `x64`, `x86`, `arm64` |
| `app_type` | varchar(50) | `Win32` o `ModernApp` |
| `app_source` | varchar(50) | `Registry` o `Appx` |
| `app_scope` | varchar(50) | `Machine`, `User`, `AllUsers` |
| `system_component` | boolean | Si es un componente del sistema Windows |
| `windows_installer` | boolean | Si se instaló vía MSI |
| `package_full_name` | varchar(500) | Nombre completo del paquete Appx |
| `package_family_name` | varchar(500) | Familia del paquete Appx |
| `install_location` | text | Ruta de instalación |
| `is_framework` | boolean | Si es un framework o runtime |
| `is_resource_package` | boolean | Si es un paquete de recursos (Appx) |
| `is_bundle` | boolean | Si es un bundle (Appx) |
| `is_development_mode` | boolean | Instalado en modo de desarrollo |
| `is_non_removable` | boolean | No se puede desinstalar |
| `signature_kind` | varchar(50) | Tipo de firma del paquete |
| `normalized_name` | varchar(500) | Nombre normalizado para agrupación |
| `normalized_publisher` | varchar(500) | Publisher normalizado |
| `is_current` | boolean | Versión efectiva actual del producto en el snapshot |
| `superseded_by_software_id` | integer FK → installed_software | Si fue reemplazado por otra versión |
| `dedupe_hash` | varchar(64) | SHA-256 para deduplicación dentro del snapshot |

**Índices:** `(endpoint_id, snapshot_id)`, `normalized_name`, `(app_source, app_type)`

---

## `software_products`

Catálogo lógico de productos normalizados (mantenido manualmente o por reglas).

| Columna | Tipo | Descripción |
|---|---|---|
| `id` | integer PK | Identificador interno |
| `normalized_name` | varchar(500) UNIQUE | Nombre normalizado de referencia |
| `display_name` | varchar(500) | Nombre para mostrar en UI |
| `publisher` | varchar(500) | Publisher canónico |
| `product_family` | varchar(255) | Familia de producto |
| `software_category` | varchar(100) | Categoría (`browser`, `security`, `runtime`, etc.) |
| `vendor_category` | varchar(100) | Categoría del vendor |
| `is_os_component` | boolean | Componente del SO |
| `is_security_tool` | boolean | Herramienta de seguridad |
| `is_browser` | boolean | Navegador web |
| `is_collaboration_tool` | boolean | Herramienta de colaboración |
| `is_remote_support_tool` | boolean | Herramienta de soporte remoto |
| `is_allowed` | boolean | Autorizado por política corporativa |
| `notes` | text | Notas adicionales |

---

## `software_compliance_rules`

Reglas para evaluar cumplimiento de software por snapshot.

| Columna | Tipo | Descripción |
|---|---|---|
| `id` | integer PK | Identificador interno |
| `name` | varchar(255) | Nombre descriptivo de la regla |
| `rule_type` | varchar(50) | Tipo de regla (`required`, `forbidden`) |
| `product_match_pattern` | varchar(500) | Regex sobre `normalized_name` |
| `publisher_match_pattern` | varchar(500) | Regex sobre `normalized_publisher` |
| `scope` | varchar(50) | Ámbito de aplicación |
| `is_required` | boolean | El software debe estar instalado |
| `is_forbidden` | boolean | El software no debe estar instalado |
| `minimum_version` | varchar(100) | Versión mínima requerida |
| `maximum_version` | varchar(100) | Versión máxima permitida |
| `severity` | varchar(50) | `critical`, `high`, `medium`, `low` |
| `is_active` | boolean | Si la regla está activa |

---

## `endpoint_software_findings`

Hallazgos de compliance calculados por snapshot.

| Columna | Tipo | Descripción |
|---|---|---|
| `id` | integer PK | Identificador interno |
| `endpoint_id` | integer FK → endpoints | Endpoint afectado |
| `snapshot_id` | integer FK → endpoint_snapshots | Snapshot evaluado |
| `software_product_id` | integer FK → software_products | Producto relacionado (nullable) |
| `finding_type` | varchar(50) | `missing_required`, `forbidden_installed`, `outdated_version` |
| `severity` | varchar(50) | Severidad del hallazgo |
| `status` | varchar(50) | `open`, `acknowledged`, `resolved` |
| `details` | text | Descripción del hallazgo |
| `detected_at` | date | Fecha de detección |

---

## `data_sources`

Configuración de orígenes de datos Azure Blob Storage.

| Columna | Tipo | Descripción |
|---|---|---|
| `id` | integer PK | Identificador interno |
| `name` | varchar(255) UNIQUE | Nombre de la configuración |
| `source_type` | varchar(50) | `azure_blob` |
| `account_url` | text | URL de la Storage Account |
| `container_name` | varchar(255) | Nombre del contenedor |
| `blob_prefix` | varchar(500) | Prefijo de blobs a listar |
| `sas_token_encrypted` | text | SAS token cifrado con Fernet |
| `sas_token_hint` | varchar(20) | Hint del token: `sv=2****=rw` |
| `is_active` | boolean | Si el origen está activo |
| `sync_frequency_minutes` | integer | Frecuencia de sync (no usada en sync automático aún) |
| `last_sync_at` | timestamptz | Última sincronización exitosa |
| `last_sync_status` | varchar(50) | `success`, `partial`, `error` |
| `last_error` | text | Último mensaje de error |
| `created_at` | timestamptz | Fecha de creación |
| `updated_at` | timestamptz | Última modificación |

---

## `inventory_files`

Control de blobs procesados. Permite reimportación idempotente.

| Columna | Tipo | Descripción |
|---|---|---|
| `id` | integer PK | Identificador interno |
| `data_source_id` | integer FK → data_sources | Origen de datos |
| `blob_name` | text | Nombre completo del blob en el contenedor |
| `file_type` | varchar(50) | `hardware` o `software` |
| `endpoint_name` | varchar(255) | Nombre del endpoint extraído del nombre del archivo |
| `blob_last_modified` | timestamptz | Última modificación del blob en Azure |
| `etag` | varchar(255) | ETag del blob (usado para deduplicación) |
| `content_hash` | varchar(64) | Hash del contenido (opcional) |
| `processed_at` | timestamptz | Cuándo fue procesado |
| `status` | varchar(50) | `pending`, `processed`, `error` |
| `error_message` | text | Detalle del error si `status=error` |

**Índice único:** `(blob_name, etag)` — evita reprocesar el mismo blob.

---

## `windows_patch_reference`

Catálogo de referencia de builds y parches mensuales de Windows. Sincronizado desde Microsoft Learn.

| Columna | Tipo | Descripción |
|---|---|---|
| `id` | integer PK | Identificador interno |
| `product_name` | varchar(255) | `Windows 11` |
| `windows_version` | varchar(50) | `24H2`, `23H2`, `22H2`, etc. |
| `release_channel` | varchar(100) | Canal de publicación |
| `os_build` | varchar(50) | Build base (`26100`) |
| `os_revision` | integer | Revisión (`3775`) |
| `full_build` | varchar(50) | `26100.3775` |
| `kb_article` | varchar(50) | Artículo KB (`KB5053598`) |
| `patch_month` | varchar(20) | Mes del parche en `YYYY-MM` |
| `patch_label` | varchar(255) | Etiqueta legible (`2026-03 Update`) |
| `release_date` | date | Fecha de publicación oficial |
| `source_url` | text | URL de Microsoft Learn de donde se extrajo |
| `source_type` | varchar(50) | `microsoft_learn` |
| `is_security_update` | boolean | Si es una actualización de seguridad |
| `is_preview` | boolean | Si es una build de preview |
| `is_latest_for_branch` | boolean | Si es el último parche publicado para esta rama |
| `scraped_at` | timestamptz | Cuándo se realizó el scraping |
| `catalog_version` | varchar(50) | Versión del catálogo (`YYYYMMDD`) |

**Índice único:** `(full_build, kb_article)`

**Versiones conocidas de Windows 11:**

| `os_build` | `windows_version` |
|---|---|
| `22000` | 21H2 |
| `22621` | 22H2 |
| `22631` | 23H2 |
| `26100` | 24H2 |
| `26200` | 25H2 |

---

## `windows_update_status`

Estado de actualización calculado por endpoint y snapshot.

| Columna | Tipo | Descripción |
|---|---|---|
| `id` | integer PK | Identificador interno |
| `endpoint_id` | integer FK → endpoints | Endpoint evaluado |
| `snapshot_id` | integer FK → endpoint_snapshots | Snapshot base de la evaluación |
| `windows_version` | varchar(50) | Versión de Windows del endpoint |
| `os_build` | varchar(50) | Build base |
| `os_revision` | integer | Revisión instalada |
| `full_build` | varchar(50) | `os_build.os_revision` |
| `patch_month` | varchar(20) | Mes del parche determinado |
| `patch_label` | varchar(255) | Etiqueta del parche |
| `kb_article` | varchar(50) | KB asociada |
| `compliance_status` | varchar(50) | Estado de cumplimiento (ver tabla abajo) |
| `months_behind` | integer | Meses de desfase respecto al último parche |
| `inferred` | boolean | `true` si no hay coincidencia exacta en el catálogo |
| `evaluated_at` | timestamptz | Cuándo se evaluó |

**Índice único:** `(endpoint_id, snapshot_id)`

**Valores de `compliance_status`:**

| Valor | Condición |
|---|---|
| `up_to_date` | `months_behind = 0` |
| `behind_1_month` | `months_behind = 1` |
| `behind_2_plus_months` | `months_behind >= 2` |
| `preview_build` | Build de preview |
| `unsupported_branch` | Rama no en catálogo |
| `unknown` | No hay datos suficientes |
