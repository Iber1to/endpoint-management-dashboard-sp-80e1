import { useEffect, useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { type ColumnDef } from "@tanstack/react-table";

import DataTable from "../components/tables/DataTable";
import { softwareService } from "../services/software";
import type { SoftwareComplianceEndpointFindingItem, SoftwareComplianceProfileSummary } from "../types";

const MODE_OPTIONS: Array<{ value: "all" | "forbidden" | "minimum_version"; label: string }> = [
  { value: "all", label: "All findings" },
  { value: "forbidden", label: "Forbidden software" },
  { value: "minimum_version", label: "Minimum version" },
];

function listTypeLabel(value: string): string {
  if (value === "blacklist") return "Blacklist";
  if (value === "compliance_list") return "Compliance List";
  if (value === "mixed") return "Mixed";
  return value || "--";
}

export default function SoftwareCompliancePage() {
  const [selectedProfile, setSelectedProfile] = useState("");
  const [mode, setMode] = useState<"all" | "forbidden" | "minimum_version">("all");
  const [page, setPage] = useState(1);
  const pageSize = 100;

  const summaryQuery = useQuery({
    queryKey: ["software-compliance-summary"],
    queryFn: () => softwareService.getComplianceSummary(),
  });

  useEffect(() => {
    if (!selectedProfile && summaryQuery.data?.items?.length) {
      setSelectedProfile(summaryQuery.data.items[0].profile_name);
    }
  }, [selectedProfile, summaryQuery.data]);

  const findingsQuery = useQuery({
    queryKey: ["software-compliance-findings", selectedProfile, mode, page],
    queryFn: () =>
      softwareService.getComplianceFindings({
        profile_name: selectedProfile,
        mode,
        page,
        page_size: pageSize,
      }),
    enabled: Boolean(selectedProfile),
  });

  const summaryColumns: ColumnDef<SoftwareComplianceProfileSummary>[] = [
    { accessorKey: "profile_name", header: "List Name" },
    {
      accessorKey: "list_type",
      header: "List Type",
      cell: ({ getValue }) => <span>{listTypeLabel(getValue<string>())}</span>,
    },
    { accessorKey: "total_endpoints", header: "Total Endpoints" },
    { accessorKey: "compliant_endpoints", header: "Compliant" },
    {
      accessorKey: "non_compliant_endpoints",
      header: "Non-compliant",
      cell: ({ row, getValue }) => (
        <button
          className="text-blue-700 font-semibold hover:underline"
          onClick={() => {
            setSelectedProfile(row.original.profile_name);
            setMode("all");
            setPage(1);
          }}
        >
          {getValue<number>()}
        </button>
      ),
    },
  ];

  const findingsColumns: ColumnDef<SoftwareComplianceEndpointFindingItem>[] = useMemo(
    () => [
      {
        accessorKey: "computer_name",
        header: "Endpoint",
        cell: ({ row }) => (
          <Link to={`/endpoints/${row.original.endpoint_id}`} className="font-medium text-blue-700 hover:underline">
            {row.original.computer_name}
          </Link>
        ),
      },
      { accessorKey: "finding_type", header: "Finding" },
      { accessorKey: "rule_name", header: "Rule" },
      { accessorKey: "software_name", header: "Software" },
      {
        accessorKey: "software_version",
        header: "Version",
        cell: ({ getValue }) => <span className="font-mono text-xs">{getValue<string>() || "--"}</span>,
      },
      {
        accessorKey: "minimum_version",
        header: "Min Required",
        cell: ({ getValue }) => <span className="font-mono text-xs">{getValue<string>() || "--"}</span>,
      },
      { accessorKey: "severity", header: "Severity" },
    ],
    []
  );

  const exportUrl = selectedProfile
    ? `/api/software/compliance/endpoints/export?profile_name=${encodeURIComponent(selectedProfile)}&mode=${mode}`
    : "#";
  const totalFindings = findingsQuery.data?.total ?? 0;
  const totalPages = Math.ceil(totalFindings / pageSize);

  return (
    <div className="p-8 space-y-6">
      <h1 className="text-2xl font-bold text-gray-800">Software Compliance</h1>

      <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
        {summaryQuery.isLoading ? (
          <div className="p-8 text-center text-gray-500">Loading compliance summary...</div>
        ) : (
          <DataTable data={summaryQuery.data?.items ?? []} columns={summaryColumns} />
        )}
      </div>

      <div className="bg-white rounded-lg border border-gray-200 p-4 space-y-4">
        <div className="flex flex-wrap gap-3 items-center justify-between">
          <div className="flex flex-wrap gap-3 items-center">
            <select
              value={selectedProfile}
              onChange={(e) => {
                setSelectedProfile(e.target.value);
                setPage(1);
              }}
              className="border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {(summaryQuery.data?.items ?? []).map((item) => (
                <option key={item.profile_name} value={item.profile_name}>
                  {item.profile_name}
                </option>
              ))}
            </select>
            <select
              value={mode}
              onChange={(e) => {
                setMode(e.target.value as "all" | "forbidden" | "minimum_version");
                setPage(1);
              }}
              className="border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {MODE_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>
          <a
            href={exportUrl}
            className={`px-4 py-2 rounded-md text-sm transition-colors ${
              selectedProfile ? "bg-blue-600 text-white hover:bg-blue-700" : "bg-gray-200 text-gray-500 pointer-events-none"
            }`}
          >
            Export CSV
          </a>
        </div>

        <div className="border border-gray-200 rounded-lg overflow-hidden">
          {findingsQuery.isLoading ? (
            <div className="p-8 text-center text-gray-500">Loading compliance findings...</div>
          ) : (
            <DataTable data={findingsQuery.data?.items ?? []} columns={findingsColumns} />
          )}
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
    </div>
  );
}
