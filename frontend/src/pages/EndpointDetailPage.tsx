import { useState } from "react";
import { useParams, Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { endpointsService } from "../services/endpoints";
import { formatBytes, formatDateTime, complianceBadge, bitlockerStatus } from "../utils";

const TABS = ["Summary", "Hardware", "Security", "Network", "Disks", "Software", "Updates", "History"] as const;
type Tab = typeof TABS[number];

export default function EndpointDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [tab, setTab] = useState<Tab>("Summary");

  const { data: ep, isLoading } = useQuery({
    queryKey: ["endpoint", id],
    queryFn: () => endpointsService.getById(Number(id)),
    enabled: !!id,
  });

  const { data: software } = useQuery({
    queryKey: ["endpoint-software", id],
    queryFn: () => endpointsService.getSoftware(Number(id)),
    enabled: tab === "Software" && !!id,
  });

  const { data: updates } = useQuery({
    queryKey: ["endpoint-updates", id],
    queryFn: () => endpointsService.getUpdates(Number(id)),
    enabled: tab === "Updates" && !!id,
  });

  const { data: history } = useQuery({
    queryKey: ["endpoint-history", id],
    queryFn: () => endpointsService.getHistory(Number(id)),
    enabled: tab === "History" && !!id,
  });

  if (isLoading) return <div className="p-8 text-gray-500">Loading...</div>;
  if (!ep) return <div className="p-8 text-red-500">Endpoint not found</div>;

  const { className: patchClass, label: patchLabel } = complianceBadge(ep.patch_compliance_status);
  const hw = ep.hardware;
  const sec = ep.security;

  return (
    <div className="p-8 space-y-6">
      <div className="flex items-center gap-3">
        <Link to="/endpoints" className="text-blue-600 hover:underline text-sm">← Endpoints</Link>
        <h1 className="text-2xl font-bold text-gray-800">{ep.computer_name}</h1>
        <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${patchClass}`}>{patchLabel}</span>
      </div>

      <div className="flex gap-1 border-b border-gray-200">
        {TABS.map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`px-4 py-2 text-sm font-medium transition-colors ${tab === t ? "border-b-2 border-blue-600 text-blue-600" : "text-gray-500 hover:text-gray-800"}`}
          >
            {t}
          </button>
        ))}
      </div>

      {tab === "Summary" && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <InfoCard title="Identity">
            <Field label="Computer Name" value={ep.computer_name} />
            <Field label="Manufacturer" value={ep.manufacturer} />
            <Field label="Model" value={ep.model} />
            <Field label="Serial Number" value={ep.serial_number} />
            <Field label="BIOS Version" value={ep.bios_version} />
            <Field label="Firmware Type" value={ep.firmware_type} />
            <Field label="Last Seen" value={formatDateTime(ep.last_seen_at)} />
          </InfoCard>
          <InfoCard title="Quick Stats">
            <Field label="OS" value={hw?.os_name} />
            <Field label="Windows Version" value={hw?.windows_version} />
            <Field label="Build" value={hw?.full_build} />
            <Field label="RAM" value={formatBytes(hw?.memory_bytes)} />
            <Field label="CPU" value={hw?.cpu_name} />
            <Field label="Software Count" value={String(ep.software_count)} />
          </InfoCard>
        </div>
      )}

      {tab === "Hardware" && hw && (
        <InfoCard title="Hardware">
          <Field label="OS Name" value={hw.os_name} />
          <Field label="Windows Version" value={hw.windows_version} />
          <Field label="OS Build" value={hw.os_build} />
          <Field label="OS Revision" value={String(hw.os_revision ?? "—")} />
          <Field label="Full Build" value={hw.full_build} />
          <Field label="RAM" value={formatBytes(hw.memory_bytes)} />
          <Field label="CPU Manufacturer" value={hw.cpu_manufacturer} />
          <Field label="CPU" value={hw.cpu_name} />
          <Field label="Cores" value={hw.cpu_cores != null ? `${hw.cpu_cores} cores / ${hw.cpu_logical_processors} logical` : "—"} />
          <Field label="System Type" value={hw.pc_system_type} />
          <Field label="Last Boot" value={formatDateTime(hw.last_boot)} />
          <Field label="Uptime (days)" value={String(hw.uptime_days ?? "—")} />
          <Field label="Update Service" value={hw.default_au_service} />
          <Field label="Metered Connection" value={hw.au_metered != null ? (hw.au_metered ? "Yes" : "No") : "—"} />
        </InfoCard>
      )}

      {tab === "Security" && sec && (
        <InfoCard title="Security">
          <Field label="TPM Present" value={sec.tpm_present ? "Yes" : "No"} />
          <Field label="TPM Ready" value={sec.tpm_ready ? "Yes" : "No"} />
          <Field label="TPM Enabled" value={sec.tpm_enabled ? "Yes" : "No"} />
          <Field label="TPM Activated" value={sec.tpm_activated ? "Yes" : "No"} />
          <Field label="TPM Auth Level" value={String(sec.tpm_managed_auth_level ?? "—")} />
          <Field label="BitLocker Mount" value={sec.bitlocker_mount_point} />
          <Field label="BitLocker Protection" value={bitlockerStatus(sec.bitlocker_protection_status)} />
          <Field label="BitLocker Volume Status" value={String(sec.bitlocker_volume_status ?? "—")} />
          <Field label="BitLocker Lock Status" value={String(sec.bitlocker_lock_status ?? "—")} />
        </InfoCard>
      )}

      {tab === "Network" && (
        <div className="space-y-4">
          {ep.network_adapters.map((na) => (
            <InfoCard key={na.id} title={na.name || "Adapter"}>
              <Field label="Description" value={na.interface_description} />
              <Field label="MAC Address" value={na.mac_address} />
              <Field label="IPv4" value={na.ipv4_address} />
              <Field label="IPv6" value={na.ipv6_address} />
              <Field label="Gateway" value={na.ipv4_default_gateway} />
              <Field label="Speed" value={na.link_speed} />
              <Field label="Status" value={na.status} />
              <Field label="Network" value={na.net_profile_name} />
            </InfoCard>
          ))}
          {ep.network_adapters.length === 0 && <p className="text-gray-400">No network adapters found</p>}
        </div>
      )}

      {tab === "Disks" && (
        <div className="space-y-4">
          {ep.disks.map((d) => (
            <InfoCard key={d.id} title={d.friendly_name || `Disk ${d.device_id}`}>
              <Field label="Media Type" value={d.media_type} />
              <Field label="Bus Type" value={d.bus_type} />
              <Field label="Health" value={d.health_status} />
              <Field label="Status" value={d.operational_status} />
              <Field label="Size" value={formatBytes(d.size_bytes)} />
              <Field label="Wear" value={d.wear != null ? `${d.wear}%` : "—"} />
              <Field label="Temperature" value={d.temperature != null ? `${d.temperature}°C (max ${d.temperature_max}°C)` : "—"} />
            </InfoCard>
          ))}
          {ep.disks.length === 0 && <p className="text-gray-400">No disks found</p>}
        </div>
      )}

      {tab === "Software" && (
        <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
          <table className="min-w-full text-sm divide-y divide-gray-100">
            <thead className="bg-gray-50">
              <tr>
                {["Name", "Version", "Publisher", "Type", "Source", "Scope", "Install Date"].map((h) => (
                  <th key={h} className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50">
              {(software ?? []).map((sw) => (
                <tr key={sw.id} className="hover:bg-gray-50">
                  <td className="px-4 py-2 font-medium text-gray-800">{sw.software_name || "—"}</td>
                  <td className="px-4 py-2 text-gray-500">{sw.software_version || "—"}</td>
                  <td className="px-4 py-2 text-gray-500">{sw.normalized_publisher || "—"}</td>
                  <td className="px-4 py-2"><span className="text-xs bg-gray-100 px-2 py-0.5 rounded">{sw.app_type || "—"}</span></td>
                  <td className="px-4 py-2"><span className="text-xs bg-blue-50 text-blue-700 px-2 py-0.5 rounded">{sw.app_source || "—"}</span></td>
                  <td className="px-4 py-2 text-gray-500">{sw.app_scope || "—"}</td>
                  <td className="px-4 py-2 text-gray-500">{sw.install_date || "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
          {(!software || software.length === 0) && <p className="text-center py-8 text-gray-400">No software data</p>}
        </div>
      )}

      {tab === "Updates" && (
        <div className="space-y-4">
          {(updates ?? []).map((u, i) => {
            const { className, label } = complianceBadge(u.compliance_status);
            return (
              <div key={i} className="bg-white border border-gray-200 rounded-lg p-5 flex items-center justify-between">
                <div>
                  <p className="font-medium">{u.full_build || "—"}</p>
                  <p className="text-sm text-gray-500">{u.patch_label || u.patch_month || "—"} · {u.kb_article || "KB unknown"}</p>
                  {u.inferred && <p className="text-xs text-yellow-600 mt-1">⚠ Inferred (no exact catalog match)</p>}
                </div>
                <span className={`px-3 py-1 rounded-full text-sm font-medium ${className}`}>{label}</span>
              </div>
            );
          })}
          {(!updates || updates.length === 0) && <p className="text-gray-400">No update status data</p>}
        </div>
      )}

      {tab === "History" && (
        <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
          <table className="min-w-full text-sm divide-y divide-gray-100">
            <thead className="bg-gray-50">
              <tr>
                {["Snapshot", "Date", "Current"].map((h) => (
                  <th key={h} className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50">
              {(history ?? []).map((s: { id: number; snapshot_at: string; is_current: boolean }) => (
                <tr key={s.id} className="hover:bg-gray-50">
                  <td className="px-4 py-2 text-gray-600">#{s.id}</td>
                  <td className="px-4 py-2">{formatDateTime(s.snapshot_at)}</td>
                  <td className="px-4 py-2">{s.is_current ? <span className="text-green-700 font-medium">✓ Current</span> : "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

function InfoCard({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="bg-white rounded-lg border border-gray-200 p-5">
      <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-4">{title}</h3>
      <dl className="space-y-2">{children}</dl>
    </div>
  );
}

function Field({ label, value }: { label: string; value?: string | null }) {
  return (
    <div className="flex justify-between items-start">
      <dt className="text-sm text-gray-500 shrink-0 mr-4">{label}</dt>
      <dd className="text-sm text-gray-800 text-right font-medium">{value || "—"}</dd>
    </div>
  );
}
