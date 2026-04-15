import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { type ColumnDef } from "@tanstack/react-table";

import DataTable from "../components/tables/DataTable";
import { softwareService } from "../services/software";
import type { SoftwareAggregatedItem, SoftwareAnalyticsItem } from "../types";

const SOURCE_OPTS = ["", "Appx", "Registry"];

export default function SoftwarePage() {
  const [search, setSearch] = useState("");
  const [publisher, setPublisher] = useState("");
  const [appSource, setAppSource] = useState("");
  const [page, setPage] = useState(1);
  const pageSize = 50;

  const { data, isLoading } = useQuery({
    queryKey: ["software", page, search, publisher, appSource],
    queryFn: () =>
      softwareService.list({
        page,
        page_size: pageSize,
        search: search || undefined,
        publisher: publisher || undefined,
        app_source: appSource || undefined,
      }),
  });

  const { data: analytics, isLoading: analyticsLoading } = useQuery({
    queryKey: ["software-analytics"],
    queryFn: () => softwareService.getAnalytics(),
  });

  const columns: ColumnDef<SoftwareAggregatedItem>[] = [
    {
      accessorKey: "display_name",
      header: "Application",
      cell: ({ row }) => (
        <span className="font-medium text-gray-800">{row.original.display_name || row.original.normalized_name || "--"}</span>
      ),
    },
    {
      accessorKey: "publisher",
      header: "Publisher",
      cell: ({ getValue }) => <span className="text-gray-500 text-xs">{getValue<string>() || "--"}</span>,
    },
    {
      accessorKey: "endpoint_count",
      header: "Endpoints",
      cell: ({ row, getValue }) => {
        const name = row.original.normalized_name;
        if (!name) return <span className="font-semibold text-blue-700">{getValue<number>()}</span>;
        return (
          <Link className="font-semibold text-blue-700 hover:underline" to={`/software/endpoints?name=${encodeURIComponent(name)}`}>
            {getValue<number>()}
          </Link>
        );
      },
    },
    {
      accessorKey: "version_count",
      header: "Versions",
      cell: ({ row, getValue }) => {
        const name = row.original.normalized_name;
        if (!name) return <span>{getValue<number>()}</span>;
        return (
          <Link className="font-semibold text-blue-700 hover:underline" to={`/software/versions?name=${encodeURIComponent(name)}`}>
            {getValue<number>()}
          </Link>
        );
      },
    },
    {
      accessorKey: "latest_version",
      header: "Latest Version",
      cell: ({ getValue }) => <span className="text-xs text-gray-500 font-mono">{getValue<string>() || "--"}</span>,
    },
    {
      accessorKey: "app_type",
      header: "Type",
      cell: ({ getValue }) => <span className="text-xs bg-gray-100 px-2 py-0.5 rounded">{getValue<string>() || "--"}</span>,
    },
    {
      accessorKey: "app_source",
      header: "Source",
      cell: ({ getValue }) => <span className="text-xs bg-blue-50 text-blue-700 px-2 py-0.5 rounded">{getValue<string>() || "--"}</span>,
    },
  ];

  const total = data?.total ?? 0;
  const totalPages = Math.ceil(total / pageSize);

  return (
    <div className="p-8 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-800">Software Inventory</h1>
        <span className="text-sm text-gray-500">{total} applications</span>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
        <BarChartCard
          title="Top 10 Software Installed (Registry)"
          items={analytics?.top_software ?? []}
          loading={analyticsLoading}
        />
        <BarChartCard
          title="Top 10 Publishers (Registry)"
          items={analytics?.top_publishers ?? []}
          loading={analyticsLoading}
        />
      </div>

      <div className="flex flex-wrap gap-3 items-center">
        <input
          className="border border-gray-300 rounded-md px-3 py-2 text-sm w-56 focus:outline-none focus:ring-2 focus:ring-blue-500"
          placeholder="Search application..."
          value={search}
          onChange={(e) => {
            setSearch(e.target.value);
            setPage(1);
          }}
        />
        <input
          className="border border-gray-300 rounded-md px-3 py-2 text-sm w-56 focus:outline-none focus:ring-2 focus:ring-blue-500"
          placeholder="Filter by publisher..."
          value={publisher}
          onChange={(e) => {
            setPublisher(e.target.value);
            setPage(1);
          }}
        />
        <select
          className="border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          value={appSource}
          onChange={(e) => {
            setAppSource(e.target.value);
            setPage(1);
          }}
        >
          {SOURCE_OPTS.map((o) => (
            <option key={o} value={o}>
              {o || "All sources"}
            </option>
          ))}
        </select>
      </div>

      <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
        {isLoading ? <div className="p-8 text-center text-gray-500">Loading software...</div> : <DataTable data={data?.items ?? []} columns={columns} />}
      </div>

      {totalPages > 1 && (
        <div className="flex items-center gap-3 justify-end text-sm">
          <button className="px-3 py-1 border rounded disabled:opacity-40" disabled={page === 1} onClick={() => setPage((p) => p - 1)}>
            Previous
          </button>
          <span>
            Page {page} of {totalPages}
          </span>
          <button className="px-3 py-1 border rounded disabled:opacity-40" disabled={page === totalPages} onClick={() => setPage((p) => p + 1)}>
            Next
          </button>
        </div>
      )}
    </div>
  );
}

function BarChartCard({ title, items, loading }: { title: string; items: SoftwareAnalyticsItem[]; loading: boolean }) {
  const maxValue = items.reduce((max, item) => Math.max(max, item.endpoint_count), 0);
  const palette = ["#2563eb", "#0d9488", "#ea580c", "#7c3aed", "#059669", "#dc2626", "#0891b2", "#b45309", "#4f46e5", "#15803d"];

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-4">
      <h2 className="text-sm font-semibold text-gray-700 uppercase tracking-wide mb-3">{title}</h2>
      {loading ? (
        <div className="text-sm text-gray-500 py-8 text-center">Loading chart...</div>
      ) : items.length === 0 ? (
        <div className="text-sm text-gray-500 py-8 text-center">No data available</div>
      ) : (
        <div className="space-y-2">
          {items.map((item, index) => {
            const pct = maxValue > 0 ? (item.endpoint_count / maxValue) * 100 : 0;
            const barColor = palette[index % palette.length];
            return (
              <div key={`${item.label}-${item.endpoint_count}`} className="grid grid-cols-[1fr_auto] gap-3 items-center">
                <div>
                  <div className="text-xs text-gray-700 truncate" title={item.label}>
                    {item.label}
                  </div>
                  <div className="h-2 rounded bg-gray-100 mt-1 overflow-hidden">
                    <div className="h-full rounded" style={{ width: `${Math.max(pct, 2)}%`, backgroundColor: barColor }} />
                  </div>
                </div>
                <div className="text-xs font-semibold text-gray-700 tabular-nums min-w-[2.5rem] text-right">
                  {item.endpoint_count}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
