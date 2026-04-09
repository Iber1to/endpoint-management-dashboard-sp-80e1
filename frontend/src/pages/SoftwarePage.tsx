import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { softwareService } from "../services/software";
import DataTable from "../components/tables/DataTable";
import type { SoftwareAggregatedItem } from "../types";
import { type ColumnDef } from "@tanstack/react-table";

const SOURCE_OPTS = ["", "Appx", "Registry"];
const TYPE_OPTS = ["", "ModernApp", "Win32"];

export default function SoftwarePage() {
  const [search, setSearch] = useState("");
  const [appSource, setAppSource] = useState("");
  const [appType, setAppType] = useState("");
  const [hideSystem, setHideSystem] = useState(false);
  const [hideFramework, setHideFramework] = useState(false);
  const [page, setPage] = useState(1);
  const pageSize = 50;

  const { data, isLoading } = useQuery({
    queryKey: ["software", page, search, appSource, appType, hideSystem, hideFramework],
    queryFn: () =>
      softwareService.list({
        page,
        page_size: pageSize,
        search: search || undefined,
        app_source: appSource || undefined,
        app_type: appType || undefined,
        hide_system: hideSystem || undefined,
        hide_framework: hideFramework || undefined,
      }),
  });

  const columns: ColumnDef<SoftwareAggregatedItem>[] = [
    {
      accessorKey: "display_name",
      header: "Application",
      cell: ({ row }) => <span className="font-medium text-gray-800">{row.original.display_name || row.original.normalized_name || "—"}</span>,
    },
    {
      accessorKey: "publisher",
      header: "Publisher",
      cell: ({ getValue }) => <span className="text-gray-500 text-xs">{getValue<string>() || "—"}</span>,
    },
    {
      accessorKey: "endpoint_count",
      header: "Endpoints",
      cell: ({ getValue }) => (
        <span className="font-semibold text-blue-700">{getValue<number>()}</span>
      ),
    },
    {
      accessorKey: "version_count",
      header: "Versions",
    },
    {
      accessorKey: "latest_version",
      header: "Latest Version",
      cell: ({ getValue }) => <span className="text-xs text-gray-500 font-mono">{getValue<string>() || "—"}</span>,
    },
    {
      accessorKey: "app_type",
      header: "Type",
      cell: ({ getValue }) => (
        <span className="text-xs bg-gray-100 px-2 py-0.5 rounded">{getValue<string>() || "—"}</span>
      ),
    },
    {
      accessorKey: "app_source",
      header: "Source",
      cell: ({ getValue }) => (
        <span className="text-xs bg-blue-50 text-blue-700 px-2 py-0.5 rounded">{getValue<string>() || "—"}</span>
      ),
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

      <div className="flex flex-wrap gap-3 items-center">
        <input
          className="border border-gray-300 rounded-md px-3 py-2 text-sm w-56 focus:outline-none focus:ring-2 focus:ring-blue-500"
          placeholder="Search application..."
          value={search}
          onChange={(e) => { setSearch(e.target.value); setPage(1); }}
        />
        <select
          className="border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          value={appSource}
          onChange={(e) => { setAppSource(e.target.value); setPage(1); }}
        >
          {SOURCE_OPTS.map((o) => <option key={o} value={o}>{o || "All sources"}</option>)}
        </select>
        <select
          className="border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          value={appType}
          onChange={(e) => { setAppType(e.target.value); setPage(1); }}
        >
          {TYPE_OPTS.map((o) => <option key={o} value={o}>{o || "All types"}</option>)}
        </select>
        <label className="flex items-center gap-2 text-sm text-gray-600 cursor-pointer">
          <input type="checkbox" checked={hideSystem} onChange={(e) => setHideSystem(e.target.checked)} className="rounded" />
          Hide system components
        </label>
        <label className="flex items-center gap-2 text-sm text-gray-600 cursor-pointer">
          <input type="checkbox" checked={hideFramework} onChange={(e) => setHideFramework(e.target.checked)} className="rounded" />
          Hide frameworks
        </label>
      </div>

      <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
        {isLoading ? (
          <div className="p-8 text-center text-gray-500">Loading software...</div>
        ) : (
          <DataTable data={data?.items ?? []} columns={columns} />
        )}
      </div>

      {totalPages > 1 && (
        <div className="flex items-center gap-3 justify-end text-sm">
          <button className="px-3 py-1 border rounded disabled:opacity-40" disabled={page === 1} onClick={() => setPage((p) => p - 1)}>Previous</button>
          <span>Page {page} of {totalPages}</span>
          <button className="px-3 py-1 border rounded disabled:opacity-40" disabled={page === totalPages} onClick={() => setPage((p) => p + 1)}>Next</button>
        </div>
      )}
    </div>
  );
}
