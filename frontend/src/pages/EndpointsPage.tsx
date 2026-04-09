import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { type ColumnDef } from "@tanstack/react-table";
import { endpointsService } from "../services/endpoints";
import DataTable from "../components/tables/DataTable";
import type { EndpointListItem } from "../types";
import { formatDateTime, complianceBadge, bitlockerStatus } from "../utils";

export default function EndpointsPage() {
  const navigate = useNavigate();
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const pageSize = 50;

  const { data, isLoading } = useQuery({
    queryKey: ["endpoints", page, search],
    queryFn: () => endpointsService.list({ page, page_size: pageSize, search: search || undefined }),
  });

  const columns: ColumnDef<EndpointListItem>[] = [
    {
      accessorKey: "computer_name",
      header: "Hostname",
      cell: ({ row }) => (
        <button
          className="text-blue-600 hover:underline font-medium"
          onClick={() => navigate(`/endpoints/${row.original.id}`)}
        >
          {row.original.computer_name}
        </button>
      ),
    },
    { accessorKey: "manufacturer", header: "Manufacturer" },
    { accessorKey: "model", header: "Model" },
    {
      accessorKey: "windows_version",
      header: "Windows",
      cell: ({ getValue }) => getValue<string>() || "—",
    },
    {
      accessorKey: "full_build",
      header: "Build",
      cell: ({ getValue }) => getValue<string>() || "—",
    },
    {
      accessorKey: "last_seen_at",
      header: "Last Seen",
      cell: ({ getValue }) => formatDateTime(getValue<string>()),
    },
    {
      accessorKey: "bitlocker_protection_status",
      header: "BitLocker",
      cell: ({ getValue }) => {
        const v = getValue<number>();
        return (
          <span className={v === 1 ? "text-green-700 font-medium" : "text-red-600"}>
            {bitlockerStatus(v)}
          </span>
        );
      },
    },
    {
      accessorKey: "tpm_present",
      header: "TPM",
      cell: ({ getValue }) => {
        const v = getValue<boolean | null>();
        return v == null ? "—" : v ? <span className="text-green-700">✓</span> : <span className="text-red-600">✗</span>;
      },
    },
    {
      accessorKey: "patch_compliance_status",
      header: "Patch Status",
      cell: ({ getValue }) => {
        const { className, label } = complianceBadge(getValue<string>());
        return <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${className}`}>{label}</span>;
      },
    },
  ];

  const total = data?.total ?? 0;
  const totalPages = Math.ceil(total / pageSize);

  return (
    <div className="p-8 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-800">Endpoints</h1>
        <span className="text-sm text-gray-500">{total} total</span>
      </div>

      <div className="flex gap-3">
        <input
          className="border border-gray-300 rounded-md px-3 py-2 text-sm w-64 focus:outline-none focus:ring-2 focus:ring-blue-500"
          placeholder="Search by hostname..."
          value={search}
          onChange={(e) => { setSearch(e.target.value); setPage(1); }}
        />
      </div>

      <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
        {isLoading ? (
          <div className="p-8 text-center text-gray-500">Loading endpoints...</div>
        ) : (
          <DataTable data={data?.items ?? []} columns={columns} />
        )}
      </div>

      {totalPages > 1 && (
        <div className="flex items-center gap-3 justify-end text-sm">
          <button
            className="px-3 py-1 border rounded disabled:opacity-40"
            disabled={page === 1}
            onClick={() => setPage((p) => p - 1)}
          >
            Previous
          </button>
          <span>Page {page} of {totalPages}</span>
          <button
            className="px-3 py-1 border rounded disabled:opacity-40"
            disabled={page === totalPages}
            onClick={() => setPage((p) => p + 1)}
          >
            Next
          </button>
        </div>
      )}
    </div>
  );
}
