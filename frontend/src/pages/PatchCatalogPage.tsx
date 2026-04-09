import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { updatesService } from "../services/updates";
import { formatDate } from "../utils";
import type { PatchReference } from "../types";

export default function PatchCatalogPage() {
  const qc = useQueryClient();

  const { data: status } = useQuery({
    queryKey: ["catalog-status"],
    queryFn: () => updatesService.getCatalogStatus(),
  });

  const { data: catalog, isLoading } = useQuery({
    queryKey: ["patch-catalog"],
    queryFn: () => updatesService.getCatalog(),
  });

  const syncMutation = useMutation({
    mutationFn: () => updatesService.syncCatalog(),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["patch-catalog"] });
      qc.invalidateQueries({ queryKey: ["catalog-status"] });
    },
  });

  return (
    <div className="p-8 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-800">Patch Catalog</h1>
        <button
          onClick={() => syncMutation.mutate()}
          disabled={syncMutation.isPending}
          className="px-4 py-2 bg-blue-600 text-white rounded-md text-sm hover:bg-blue-700 disabled:opacity-50 transition-colors"
        >
          {syncMutation.isPending ? "Syncing..." : "Sync from Microsoft Learn"}
        </button>
      </div>

      {status && (
        <div className="grid grid-cols-3 gap-4">
          <div className="bg-white border border-gray-200 rounded-lg p-5">
            <p className="text-xs text-gray-500 uppercase font-semibold">Total Builds</p>
            <p className="text-3xl font-bold text-blue-700 mt-1">{status.total_builds}</p>
          </div>
          <div className="bg-white border border-gray-200 rounded-lg p-5">
            <p className="text-xs text-gray-500 uppercase font-semibold">Last Synced</p>
            <p className="text-lg font-semibold mt-1">{status.last_synced_at ? new Date(status.last_synced_at).toLocaleString() : "Never"}</p>
          </div>
          <div className="bg-white border border-gray-200 rounded-lg p-5">
            <p className="text-xs text-gray-500 uppercase font-semibold">Catalog Version</p>
            <p className="text-lg font-semibold mt-1">{status.catalog_version || "—"}</p>
          </div>
        </div>
      )}

      {syncMutation.isSuccess && (
        <div className="bg-green-50 border border-green-200 text-green-800 rounded-lg px-4 py-3 text-sm">
          Catalog synced successfully: {syncMutation.data?.result?.synced ?? 0} entries updated.
        </div>
      )}
      {syncMutation.isError && (
        <div className="bg-red-50 border border-red-200 text-red-800 rounded-lg px-4 py-3 text-sm">
          Sync failed. Check backend logs.
        </div>
      )}

      <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-100">
          <h2 className="text-sm font-semibold text-gray-600 uppercase">Build → KB → Patch Month</h2>
        </div>
        {isLoading ? (
          <div className="p-8 text-center text-gray-400">Loading catalog...</div>
        ) : (
          <table className="min-w-full text-sm divide-y divide-gray-100">
            <thead className="bg-gray-50">
              <tr>
                {["Windows Version", "Full Build", "OS Build", "Revision", "KB Article", "Patch Month", "Release Date", "Latest", "Preview"].map((h) => (
                  <th key={h} className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50">
              {(catalog ?? []).map((ref: PatchReference) => (
                <tr key={ref.id} className={`hover:bg-gray-50 ${ref.is_latest_for_branch ? "bg-green-50" : ""}`}>
                  <td className="px-4 py-2 font-medium">{ref.windows_version || "—"}</td>
                  <td className="px-4 py-2 font-mono text-xs text-gray-700">{ref.full_build || "—"}</td>
                  <td className="px-4 py-2 font-mono text-xs">{ref.os_build || "—"}</td>
                  <td className="px-4 py-2 font-mono text-xs">{ref.os_revision || "—"}</td>
                  <td className="px-4 py-2 font-mono text-xs text-blue-700">{ref.kb_article || "—"}</td>
                  <td className="px-4 py-2">{ref.patch_month || "—"}</td>
                  <td className="px-4 py-2 text-gray-500">{formatDate(ref.release_date)}</td>
                  <td className="px-4 py-2">{ref.is_latest_for_branch ? <span className="text-green-700 font-semibold">✓</span> : ""}</td>
                  <td className="px-4 py-2">{ref.is_preview ? <span className="text-purple-600 text-xs">Preview</span> : ""}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
        {!isLoading && (!catalog || catalog.length === 0) && (
          <p className="text-center py-8 text-gray-400">No patch catalog data. Click "Sync from Microsoft Learn" to populate.</p>
        )}
      </div>
    </div>
  );
}
