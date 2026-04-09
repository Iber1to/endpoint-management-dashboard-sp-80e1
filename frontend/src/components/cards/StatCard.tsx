interface StatCardProps {
  label: string;
  value: string | number;
  sub?: string;
  color?: "blue" | "green" | "red" | "yellow" | "gray";
}

const colorMap = {
  blue: "bg-blue-50 border-blue-200 text-blue-700",
  green: "bg-green-50 border-green-200 text-green-700",
  red: "bg-red-50 border-red-200 text-red-700",
  yellow: "bg-yellow-50 border-yellow-200 text-yellow-700",
  gray: "bg-gray-50 border-gray-200 text-gray-700",
};

export default function StatCard({ label, value, sub, color = "gray" }: StatCardProps) {
  return (
    <div className={`rounded-lg border p-5 ${colorMap[color]}`}>
      <p className="text-xs font-semibold uppercase tracking-wide opacity-70">{label}</p>
      <p className="mt-1 text-3xl font-bold">{value}</p>
      {sub && <p className="mt-1 text-sm opacity-60">{sub}</p>}
    </div>
  );
}
