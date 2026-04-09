export interface EndpointListItem {
  id: number;
  computer_name: string;
  manufacturer?: string;
  model?: string;
  os_name?: string;
  windows_version?: string;
  full_build?: string;
  last_seen_at?: string;
  bitlocker_protection_status?: number;
  tpm_present?: boolean;
  patch_compliance_status?: string;
}

export interface EndpointListResponse {
  items: EndpointListItem[];
  total: number;
  page: number;
  page_size: number;
}

export interface HardwareInfo {
  os_name?: string;
  windows_version?: string;
  os_build?: string;
  os_revision?: number;
  full_build?: string;
  memory_bytes?: number;
  cpu_manufacturer?: string;
  cpu_name?: string;
  cpu_cores?: number;
  cpu_logical_processors?: number;
  pc_system_type?: string;
  last_boot?: string;
  uptime_days?: number;
  default_au_service?: string;
  au_metered?: boolean;
}

export interface SecurityInfo {
  tpm_present?: boolean;
  tpm_ready?: boolean;
  tpm_enabled?: boolean;
  tpm_activated?: boolean;
  tpm_managed_auth_level?: number;
  bitlocker_mount_point?: string;
  bitlocker_cipher?: number;
  bitlocker_volume_status?: number;
  bitlocker_protection_status?: number;
  bitlocker_lock_status?: number;
}

export interface NetworkAdapter {
  id: number;
  name?: string;
  interface_description?: string;
  mac_address?: string;
  link_speed?: string;
  status?: string;
  net_profile_name?: string;
  ipv4_address?: string;
  ipv6_address?: string;
  ipv4_default_gateway?: string;
}

export interface Disk {
  id: number;
  device_id?: string;
  friendly_name?: string;
  media_type?: string;
  bus_type?: string;
  health_status?: string;
  operational_status?: string;
  size_bytes?: number;
  wear?: number;
  temperature?: number;
  temperature_max?: number;
}

export interface EndpointDetail {
  id: number;
  computer_name: string;
  manufacturer?: string;
  model?: string;
  serial_number?: string;
  smbios_uuid?: string;
  firmware_type?: string;
  bios_version?: string;
  last_seen_at?: string;
  hardware?: HardwareInfo;
  security?: SecurityInfo;
  network_adapters: NetworkAdapter[];
  disks: Disk[];
  software_count: number;
  patch_compliance_status?: string;
}

export interface InstalledSoftware {
  id: number;
  software_name?: string;
  software_version?: string;
  publisher?: string;
  install_date?: string;
  app_type?: string;
  app_source?: string;
  app_scope?: string;
  system_component?: boolean;
  is_framework?: boolean;
  normalized_name?: string;
  normalized_publisher?: string;
}

export interface SoftwareAggregatedItem {
  normalized_name?: string;
  display_name?: string;
  publisher?: string;
  version_count: number;
  endpoint_count: number;
  latest_version?: string;
  app_type?: string;
  app_source?: string;
}

export interface SoftwareListResponse {
  items: SoftwareAggregatedItem[];
  total: number;
  page: number;
  page_size: number;
}

export interface UpdateStatusItem {
  endpoint_id: number;
  computer_name: string;
  windows_version?: string;
  full_build?: string;
  kb_article?: string;
  patch_month?: string;
  patch_label?: string;
  compliance_status: string;
  months_behind?: number;
  inferred: boolean;
  evaluated_at: string;
}

export interface UpdateComplianceSummary {
  up_to_date: number;
  behind_1_month: number;
  behind_2_plus_months: number;
  unknown: number;
  total: number;
}

export interface UpdateComplianceResponse {
  target_patch?: string;
  summary: UpdateComplianceSummary;
  items: UpdateStatusItem[];
}

export interface PatchReference {
  id: number;
  windows_version?: string;
  os_build?: string;
  os_revision?: number;
  full_build?: string;
  kb_article?: string;
  patch_month?: string;
  patch_label?: string;
  release_date?: string;
  is_preview: boolean;
  is_latest_for_branch: boolean;
}

export interface BlobSettings {
  id: number;
  name: string;
  account_url?: string;
  container_name?: string;
  blob_prefix?: string;
  sas_token_masked?: string;
  sync_frequency_minutes: number;
  is_active: boolean;
  last_sync_at?: string;
  last_sync_status?: string;
  last_error?: string;
}

export interface InventoryFile {
  id: number;
  blob_name: string;
  file_type?: string;
  endpoint_name?: string;
  blob_last_modified?: string;
  status: string;
  error_message?: string;
  processed_at?: string;
}

export interface OverviewData {
  total_endpoints: number;
  recent_endpoints: number;
  by_manufacturer: { manufacturer: string; count: number }[];
  by_windows_version: { windows_version: string; count: number }[];
  security: {
    total: number;
    bitlocker_active: number;
    bitlocker_pct: number;
    tpm_active: number;
    tpm_pct: number;
  };
  updates: {
    total: number;
    up_to_date: number;
    behind_1_month: number;
    behind_2_plus_months: number;
    up_to_date_pct: number;
  };
}
