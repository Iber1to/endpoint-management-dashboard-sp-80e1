import { useQuery } from "@tanstack/react-query";
import { Link, useSearchParams } from "react-router-dom";
import { type ColumnDef } from "@tanstack/react-table";

import DataTable from "../components/tables/DataTable";
import { softwareService } from "../services/software";
import type { SoftwareVersionItem } from "../types";

export default function SoftwareVersionsPage() {
  const [searchParams] = useSearchParams();
  const normalizedName = searchParams.get("name") || "";

  const { data, isLoading } = useQuery({
    queryKey: ["software-versions", normalizedName],
    queryFn: () => softwareService.listVersions(normalizedName),
    enabled: Boolean(normalizedName),
  });

  const columns: ColumnDef<SoftwareVersionItem>[] = [
    {
      accessorKey: "software_version",
      header: "Version",
      cell: ({ getValue }) => <span className="font-mono text-xs">{getValue<string>() || "--"}</span>,
    },
    {
      accessorKey: "endpoint_count",
      header: "Endpoints",
      cell: ({ row, getValue }) => (
        <Link
          to={`/software/endpoints?name=${encodeURIComponent(normalizedName)}&version=${encodeURIComponent(row.original.software_version || "")}`}
          className="font-semibold text-blue-700 hover:underline"
        >
          {getValue<number>()}
        </Link>
      ),
    },
    {
      id: "export",
      header: "CSV",
      cell: ({ row }) => (
        <a
          href={`/api/software/endpoints/export?normalized_name=${encodeURIComponent(normalizedName)}&software_version=${encodeURIComponent(
            row.original.software_version || ""
          )}`}
          className="text-blue-700 text-sm hover:underline"
        >
          Export
        </a>
      ),
    },
  ];

  return (
    <div className="p-8 space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-800">Software Versions</h1>
        <p className="text-sm text-gray-500">{normalizedName || "Missing software name"}</p>
      </div>

      {!normalizedName ? (
        <div className="bg-yellow-50 border border-yellow-200 rounded-md p-4 text-sm text-yellow-800">Missing software name in URL query parameter.</div>
      ) : (
        <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
          {isLoading ? <div className="p-8 text-center text-gray-500">Loading versions...</div> : <DataTable data={data?.items ?? []} columns={columns} />}
        </div>
      )}
    </div>
  );
}

