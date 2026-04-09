import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { syncService } from "../services/sync";
import { formatDateTime } from "../utils";
import type { InventoryFile } from "../types";

export default function SyncJobsPage() {
  const qc = useQueryClient();

  const { data: syncStatus } = useQuery({
    queryKey: ["sync-status"],
    queryFn: () => syncService.getStatus(),
    refetchInterval: 10_000,
  });

  const { data: files, isLoading: filesLoading } = useQuery({
    queryKey: ["sync-files"],
    queryFn: () => syncService.listFiles({ limit: 100 }),
  });

  const runSyncMutation = useMutation({
    mutationFn: () => syncService.runSync(),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["sync-status"] });
      qc.invalidateQueries({ queryKey: ["sync-files"] });
    },
  });

  const statusColor = (s: string) => {
    if (s === "success") return "text-green-700 bg-green-100";
    if (s === "error") return "text-red-700 bg-red-100";
    if (s === "partial") return "text-yellow-700 bg-yellow-100";
    return "text-gray-600 bg-gray-100";
  };

  return (
    <div className="p-8 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-800">Sync Jobs</h1>
        <button
          onClick={() => runSyncMutation.mutate()}
          disabled={runSyncMutation.isPending}
          className="px-4 py-2 bg-blue-600 text-white rounded-md text-sm hover:bg-blue-700 disabled:opacity-50 transition-colors"
        >
          {runSyncMutation.isPending ? "Syncing..." : "Run Sync Now"}
        </button>
      </div>

      {runSyncMutation.isSuccess && (
        <div className="bg-green-50 border border-green-200 text-green-800 rounded-lg px-4 py-3 text-sm">
          Sync complete: {JSON.stringify(runSyncMutation.data?.stats)}
        </div>
      )}
      {runSyncMutation.isError && (
        <div className="bg-red-50 border border-red-200 text-red-800 rounded-lg px-4 py-3 text-sm">
          Sync failed. Check settings configuration.
        </div>
      )}

      {(syncStatus ?? []).map((s: { data_source_id: number; name: string; last_sync_at?: string; last_sync_status?: string; last_error?: string }) => (
        <div key={s.data_source_id} className="bg-white border border-gray-200 rounded-lg p-5 space-y-2">
          <div className="flex items-center justify-between">
            <h3 className="font-semibold text-gray-800">{s.name}</h3>
            {s.last_sync_status && (
              <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${statusColor(s.last_sync_status)}`}>{s.last_sync_status}</span>
            )}
          </div>
          <p className="text-sm text-gray-500">Last sync: {formatDateTime(s.last_sync_at)}</p>
          {s.last_error && <p className="text-sm text-red-600">Error: {s.last_error}</p>}
        </div>
      ))}

      {(!syncStatus || syncStatus.length === 0) && (
        <div className="bg-yellow-50 border border-yellow-200 text-yellow-800 rounded-lg px-4 py-4 text-sm">
          No data sources configured. Go to <strong>Settings</strong> to configure Azure Blob Storage.
        </div>
      )}

      <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-100">
          <h2 className="text-sm font-semibold text-gray-600 uppercase">Recent Files ({(files ?? []).length})</h2>
        </div>
        {filesLoading ? (
          <div className="p-8 text-center text-gray-400">Loading...</div>
        ) : (
          <table className="min-w-full text-sm divide-y divide-gray-100">
            <thead className="bg-gray-50">
              <tr>
                {["Blob Name", "Type", "Endpoint", "Last Modified", "Status", "Error"].map((h) => (
                  <th key={h} className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50">
              {(files ?? []).map((f: InventoryFile) => (
                <tr key={f.id} className="hover:bg-gray-50">
                  <td className="px-4 py-2 font-mono text-xs text-gray-700 max-w-xs truncate">{f.blob_name}</td>
                  <td className="px-4 py-2"><span className="text-xs bg-gray-100 px-2 py-0.5 rounded">{f.file_type || "—"}</span></td>
                  <td className="px-4 py-2 text-gray-600">{f.endpoint_name || "—"}</td>
                  <td className="px-4 py-2 text-xs text-gray-400">{formatDateTime(f.blob_last_modified)}</td>
                  <td className="px-4 py-2">
                    <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${f.status === "processed" ? "bg-green-100 text-green-700" : f.status === "error" ? "bg-red-100 text-red-700" : "bg-gray-100 text-gray-600"}`}>
                      {f.status}
                    </span>
                  </td>
                  <td className="px-4 py-2 text-xs text-red-500 max-w-xs truncate">{f.error_message || ""}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
        {!filesLoading && (!files || files.length === 0) && (
          <p className="text-center py-8 text-gray-400">No files processed yet</p>
        )}
      </div>
    </div>
  );
}
