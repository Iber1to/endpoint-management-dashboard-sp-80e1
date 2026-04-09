export function formatBytes(bytes?: number | null): string {
  if (bytes == null) return "—";
  const gb = bytes / 1024 ** 3;
  if (gb >= 1) return `${gb.toFixed(1)} GB`;
  const mb = bytes / 1024 ** 2;
  return `${mb.toFixed(0)} MB`;
}

export function formatDate(dateStr?: string | null): string {
  if (!dateStr) return "—";
  const d = new Date(dateStr);
  if (isNaN(d.getTime())) return "—";
  return d.toLocaleDateString(undefined, { year: "numeric", month: "short", day: "numeric" });
}

export function formatDateTime(dateStr?: string | null): string {
  if (!dateStr) return "—";
  const d = new Date(dateStr);
  if (isNaN(d.getTime())) return "—";
  return d.toLocaleString(undefined, { year: "numeric", month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" });
}

export const COMPLIANCE_COLORS: Record<string, string> = {
  up_to_date: "text-green-700 bg-green-100",
  behind_1_month: "text-yellow-700 bg-yellow-100",
  behind_2_plus_months: "text-red-700 bg-red-100",
  unknown: "text-gray-600 bg-gray-100",
  preview_build: "text-purple-700 bg-purple-100",
  unsupported_branch: "text-red-800 bg-red-200",
};

export const COMPLIANCE_LABELS: Record<string, string> = {
  up_to_date: "Up to date",
  behind_1_month: "1 month behind",
  behind_2_plus_months: "2+ months behind",
  unknown: "Unknown",
  preview_build: "Preview",
  unsupported_branch: "Unsupported",
};

export function complianceBadge(status?: string | null) {
  const s = status || "unknown";
  return {
    className: COMPLIANCE_COLORS[s] || "text-gray-600 bg-gray-100",
    label: COMPLIANCE_LABELS[s] || s,
  };
}

export function bitlockerStatus(code?: number | null): string {
  const map: Record<number, string> = { 0: "Off", 1: "On", 2: "Unknown" };
  return code != null ? (map[code] ?? String(code)) : "—";
}
