import { useQuery } from "@tanstack/react-query";
import { updatesService } from "../services/updates";
import { complianceBadge, formatDateTime } from "../utils";
import { PieChart, Pie, Cell, Legend, Tooltip, ResponsiveContainer } from "recharts";

const STATUS_COLORS: Record<string, string> = {
  up_to_date: "#22c55e",
  behind_1_month: "#f59e0b",
  behind_2_plus_months: "#ef4444",
  unknown: "#9ca3af",
};

export default function WindowsUpdatesPage() {
  const { data, isLoading } = useQuery({
    queryKey: ["updates-compliance"],
    queryFn: () => updatesService.getCompliance(),
  });

  if (isLoading) return <div className="p-8 text-gray-500">Loading...</div>;
  if (!data) return <div className="p-8 text-red-500">Failed to load update data</div>;

  const pieData = [
    { name: "Up to date", value: data.summary.up_to_date, fill: STATUS_COLORS.up_to_date },
    { name: "1 month behind", value: data.summary.behind_1_month, fill: STATUS_COLORS.behind_1_month },
    { name: "2+ months behind", value: data.summary.behind_2_plus_months, fill: STATUS_COLORS.behind_2_plus_months },
    { name: "Unknown", value: data.summary.unknown, fill: STATUS_COLORS.unknown },
  ].filter((d) => d.value > 0);

  return (
    <div className="p-8 space-y-8">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-800">Windows Updates</h1>
        {data.target_patch && (
          <span className="text-sm text-gray-500">Target patch: <strong>{data.target_patch}</strong></span>
        )}
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          { label: "Up to date", value: data.summary.up_to_date, color: "green" as const },
          { label: "1 Month Behind", value: data.summary.behind_1_month, color: "yellow" as const },
          { label: "2+ Months Behind", value: data.summary.behind_2_plus_months, color: "red" as const },
          { label: "Unknown", value: data.summary.unknown, color: "gray" as const },
        ].map((s) => (
          <div key={s.label} className={`rounded-lg border p-5 ${
            s.color === "green" ? "bg-green-50 border-green-200 text-green-700" :
            s.color === "yellow" ? "bg-yellow-50 border-yellow-200 text-yellow-700" :
            s.color === "red" ? "bg-red-50 border-red-200 text-red-700" :
            "bg-gray-50 border-gray-200 text-gray-700"
          }`}>
            <p className="text-xs font-semibold uppercase tracking-wide opacity-70">{s.label}</p>
            <p className="mt-1 text-3xl font-bold">{s.value}</p>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h2 className="text-sm font-semibold text-gray-500 uppercase mb-4">Compliance Distribution</h2>
          <ResponsiveContainer width="100%" height={250}>
            <PieChart>
              <Pie data={pieData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={90} label={({ name, percent }) => `${(percent * 100).toFixed(0)}%`}>
                {pieData.map((d, i) => <Cell key={i} fill={d.fill} />)}
              </Pie>
              <Legend />
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-100">
          <h2 className="text-sm font-semibold text-gray-600 uppercase">Endpoints by Patch Status</h2>
        </div>
        <table className="min-w-full text-sm divide-y divide-gray-100">
          <thead className="bg-gray-50">
            <tr>
              {["Endpoint", "Windows", "Build", "Patch Month", "KB", "Status", "Months Behind", "Evaluated"].map((h) => (
                <th key={h} className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-50">
            {data.items.map((item, i) => {
              const { className, label } = complianceBadge(item.compliance_status);
              return (
                <tr key={i} className="hover:bg-gray-50">
                  <td className="px-4 py-3 font-medium text-gray-800">{item.computer_name}</td>
                  <td className="px-4 py-3 text-gray-500">{item.windows_version || "—"}</td>
                  <td className="px-4 py-3 font-mono text-xs text-gray-600">{item.full_build || "—"}</td>
                  <td className="px-4 py-3 text-gray-500">{item.patch_month || "—"}</td>
                  <td className="px-4 py-3 font-mono text-xs">{item.kb_article || "—"}</td>
                  <td className="px-4 py-3"><span className={`px-2 py-0.5 rounded-full text-xs font-medium ${className}`}>{label}</span></td>
                  <td className="px-4 py-3 text-center">{item.months_behind ?? "—"}</td>
                  <td className="px-4 py-3 text-xs text-gray-400">{formatDateTime(item.evaluated_at)}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
        {data.items.length === 0 && <p className="text-center py-8 text-gray-400">No update data available. Run sync and evaluation first.</p>}
      </div>
    </div>
  );
}
