import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link, useSearchParams } from "react-router-dom";
import { type ColumnDef } from "@tanstack/react-table";

import DataTable from "../components/tables/DataTable";
import { softwareService } from "../services/software";
import type { SoftwareEndpointInstallItem } from "../types";

export default function SoftwareEndpointsPage() {
  const [searchParams] = useSearchParams();
  const normalizedName = searchParams.get("name") || "";
  const softwareVersion = searchParams.get("version") || "";

  const [page, setPage] = useState(1);
  const pageSize = 100;

  const { data, isLoading } = useQuery({
    queryKey: ["software-endpoints", normalizedName, softwareVersion, page],
    queryFn: () =>
      softwareService.listEndpoints({
        normalized_name: normalizedName,
        software_version: softwareVersion || undefined,
        page,
        page_size: pageSize,
      }),
    enabled: Boolean(normalizedName),
  });

  const columns: ColumnDef<SoftwareEndpointInstallItem>[] = [
    {
      accessorKey: "computer_name",
      header: "Endpoint",
      cell: ({ row }) => (
        <Link to={`/endpoints/${row.original.endpoint_id}`} className="font-medium text-blue-700 hover:underline">
          {row.original.computer_name}
        </Link>
      ),
    },
    { accessorKey: "software_name", header: "Application" },
    {
      accessorKey: "software_version",
      header: "Version",
      cell: ({ getValue }) => <span className="font-mono text-xs">{getValue<string>() || "--"}</span>,
    },
    { accessorKey: "publisher", header: "Publisher" },
  ];

  const total = data?.total ?? 0;
  const totalPages = Math.ceil(total / pageSize);
  const exportUrl = `/api/software/endpoints/export?normalized_name=${encodeURIComponent(normalizedName)}${
    softwareVersion ? `&software_version=${encodeURIComponent(softwareVersion)}` : ""
  }`;

  return (
    <div className="p-8 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-800">Software Installations</h1>
          <p className="text-sm text-gray-500">
            {normalizedName}
            {softwareVersion ? ` / ${softwareVersion}` : ""}
          </p>
        </div>
        <a href={exportUrl} className="px-4 py-2 bg-blue-600 text-white rounded-md text-sm hover:bg-blue-700 transition-colors">
          Export CSV
        </a>
      </div>

      {!normalizedName ? (
        <div className="bg-yellow-50 border border-yellow-200 rounded-md p-4 text-sm text-yellow-800">Missing software name in URL query parameter.</div>
      ) : (
        <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
          {isLoading ? <div className="p-8 text-center text-gray-500">Loading installations...</div> : <DataTable data={data?.items ?? []} columns={columns} />}
        </div>
      )}

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

