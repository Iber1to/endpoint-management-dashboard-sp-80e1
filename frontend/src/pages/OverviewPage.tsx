import { useQuery } from "@tanstack/react-query";
import { syncService } from "../services/sync";
import { updatesService } from "../services/updates";
import StatCard from "../components/cards/StatCard";
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend,
} from "recharts";
import type { OverviewData } from "../types";

const PIE_COLORS = ["#3b82f6", "#22c55e", "#f59e0b", "#ef4444", "#8b5cf6", "#06b6d4"];

export default function OverviewPage() {
  const { data, isLoading, error } = useQuery<OverviewData>({
    queryKey: ["overview"],
    queryFn: () => syncService.getOverview(),
  });

  const { data: updatesOverview } = useQuery({
    queryKey: ["updates-overview"],
    queryFn: () => updatesService.getOverview(),
  });

  if (isLoading) return <div className="p-8 text-gray-500">Loading...</div>;
  if (error || !data) return <div className="p-8 text-red-500">Failed to load overview data</div>;

  const patchData = [
    { name: "Up to date", value: data.updates.up_to_date, fill: "#22c55e" },
    { name: "1 month behind", value: data.updates.behind_1_month, fill: "#f59e0b" },
    { name: "2+ months behind", value: data.updates.behind_2_plus_months, fill: "#ef4444" },
    { name: "Unknown", value: data.updates.total - data.updates.up_to_date - data.updates.behind_1_month - data.updates.behind_2_plus_months, fill: "#9ca3af" },
  ].filter((d) => d.value > 0);

  return (
    <div className="p-8 space-y-8">
      <h1 className="text-2xl font-bold text-gray-800">Overview</h1>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard label="Total Endpoints" value={data.total_endpoints} color="blue" />
        <StatCard label="Recent Inventory (30d)" value={data.recent_endpoints} color="green" />
        <StatCard label="BitLocker Active" value={`${data.security.bitlocker_pct}%`} sub={`${data.security.bitlocker_active} / ${data.security.total}`} color={data.security.bitlocker_pct >= 90 ? "green" : "yellow"} />
        <StatCard label="TPM Enabled" value={`${data.security.tpm_pct}%`} sub={`${data.security.tpm_active} / ${data.security.total}`} color={data.security.tpm_pct >= 90 ? "green" : "yellow"} />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <StatCard label="Up to Date" value={data.updates.up_to_date} color="green" />
        <StatCard label="1 Month Behind" value={data.updates.behind_1_month} color="yellow" />
        <StatCard label="2+ Months Behind" value={data.updates.behind_2_plus_months} color="red" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h2 className="text-sm font-semibold text-gray-600 uppercase mb-4">Endpoints by Manufacturer</h2>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={data.by_manufacturer.slice(0, 10)} layout="vertical">
              <XAxis type="number" tick={{ fontSize: 12 }} />
              <YAxis type="category" dataKey="manufacturer" width={120} tick={{ fontSize: 11 }} />
              <Tooltip />
              <Bar dataKey="count" fill="#3b82f6" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h2 className="text-sm font-semibold text-gray-600 uppercase mb-4">Windows Version Distribution</h2>
          <ResponsiveContainer width="100%" height={220}>
            <PieChart>
              <Pie data={data.by_windows_version} dataKey="count" nameKey="windows_version" cx="50%" cy="50%" outerRadius={80} label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}>
                {data.by_windows_version.map((_, i) => (
                  <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>

        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h2 className="text-sm font-semibold text-gray-600 uppercase mb-4">Patch Compliance</h2>
          <ResponsiveContainer width="100%" height={220}>
            <PieChart>
              <Pie data={patchData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={80} label={({ name, percent }) => `${(percent * 100).toFixed(0)}%`}>
                {patchData.map((d, i) => (
                  <Cell key={i} fill={d.fill} />
                ))}
              </Pie>
              <Legend />
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {updatesOverview && (
          <div className="bg-white rounded-lg border border-gray-200 p-6">
            <h2 className="text-sm font-semibold text-gray-600 uppercase mb-4">Top Builds</h2>
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={updatesOverview.by_build?.slice(0, 8)} layout="vertical">
                <XAxis type="number" tick={{ fontSize: 12 }} />
                <YAxis type="category" dataKey="full_build" width={90} tick={{ fontSize: 11 }} />
                <Tooltip />
                <Bar dataKey="count" fill="#8b5cf6" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>
    </div>
  );
}
