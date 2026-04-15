import { useEffect, useMemo, useRef, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { syncService } from "../services/sync";
import { formatDateTime } from "../utils";
import type { SyncExecution } from "../types";

type ApiErrorDetail = {
  message?: string;
  retry_after_seconds?: number;
};

export default function SyncJobsPage() {
  const qc = useQueryClient();
  const [runError, setRunError] = useState<string | null>(null);
  const [retryAfterSeconds, setRetryAfterSeconds] = useState<number | null>(null);
  const [forceRun, setForceRun] = useState(false);
  const [selectedSyncType, setSelectedSyncType] = useState("all");
  const hadRunInProgressRef = useRef(false);

  const { data: syncStatus } = useQuery({
    queryKey: ["sync-status"],
    queryFn: () => syncService.getStatus(),
    refetchInterval: 5_000,
  });

  const { data: currentRun } = useQuery({
    queryKey: ["sync-current-run"],
    queryFn: () => syncService.getCurrentRun(),
    refetchInterval: 3_000,
  });

  const { data: runTypes } = useQuery({
    queryKey: ["sync-runs-types"],
    queryFn: () => syncService.listRunTypes(),
    refetchInterval: 15_000,
  });

  const { data: runHistory } = useQuery({
    queryKey: ["sync-runs-history", selectedSyncType],
    queryFn: () => syncService.listRuns(500, selectedSyncType),
    refetchInterval: 5_000,
  });

  const runSyncMutation = useMutation({
    mutationFn: () => syncService.runSync({ force: forceRun }),
    onMutate: () => {
      setRunError(null);
      setRetryAfterSeconds(null);
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["sync-current-run"] });
      qc.invalidateQueries({ queryKey: ["sync-runs-history"] });
      qc.invalidateQueries({ queryKey: ["sync-status"] });
      qc.invalidateQueries({ queryKey: ["sync-runs-types"] });
    },
    onError: (error: unknown) => {
      const maybeAxiosError = error as {
        response?: {
          status?: number;
          data?: { detail?: string | ApiErrorDetail };
        };
      };

      const status = maybeAxiosError.response?.status;
      const detail = maybeAxiosError.response?.data?.detail;

      if (typeof detail === "object" && detail?.message) {
        setRunError(detail.message);
        if (typeof detail.retry_after_seconds === "number") {
          setRetryAfterSeconds(detail.retry_after_seconds);
        }
        return;
      }

      if (typeof detail === "string" && detail) {
        setRunError(detail);
        return;
      }

      if (status === 409) {
        setRunError("Ya hay una ejecucion de sincronizacion en curso.");
        return;
      }
      if (status === 429) {
        setRunError("No se puede lanzar una ejecucion manual todavia.");
        return;
      }

      setRunError("Sync failed. Check backend logs for details.");
    },
  });

  const isRunInProgress = currentRun?.status === "queued" || currentRun?.status === "running";

  useEffect(() => {
    if (isRunInProgress) {
      hadRunInProgressRef.current = true;
      return;
    }
    if (!hadRunInProgressRef.current) {
      return;
    }

    hadRunInProgressRef.current = false;
    qc.invalidateQueries({ queryKey: ["sync-runs-history"] });
    qc.invalidateQueries({ queryKey: ["sync-status"] });
    qc.invalidateQueries({ queryKey: ["sync-runs-types"] });
  }, [isRunInProgress, qc]);

  const latestCompletedRun = useMemo(() => {
    return (runHistory ?? []).find((r: SyncExecution) => r.status !== "queued" && r.status !== "running");
  }, [runHistory]);

  const statusColor = (s: string) => {
    if (s === "success") return "text-green-700 bg-green-100";
    if (s === "failed") return "text-red-700 bg-red-100";
    if (s === "partial") return "text-yellow-700 bg-yellow-100";
    if (s === "running") return "text-blue-700 bg-blue-100";
    if (s === "queued") return "text-purple-700 bg-purple-100";
    return "text-gray-600 bg-gray-100";
  };

  const syncTypeLabel = (syncType: string) => {
    if (syncType === "inventory") return "Inventario";
    if (syncType === "patch_catalog") return "Patch Catalog";
    return syncType;
  };

  const availableSyncTypes = useMemo(() => {
    const apiTypes = runTypes ?? [];
    const historyTypes = (runHistory ?? []).map((run) => run.sync_type).filter(Boolean);
    return Array.from(new Set([...apiTypes, ...historyTypes]));
  }, [runHistory, runTypes]);

  const formatSnapshotRange = (run: SyncExecution) => {
    const from = run.stats.snapshot_id_from;
    const to = run.stats.snapshot_id_to;
    if (!from || !to) return "--";
    if (from === to) return `#${from}`;
    return `#${from}-#${to}`;
  };

  return (
    <div className="p-8 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-800">Sync Jobs</h1>
        <div className="flex flex-col items-end gap-2">
          <button
            onClick={() => runSyncMutation.mutate()}
            disabled={runSyncMutation.isPending || isRunInProgress}
            className="px-4 py-2 bg-blue-600 text-white rounded-md text-sm hover:bg-blue-700 disabled:opacity-50 transition-colors"
          >
            {isRunInProgress ? "Sync running..." : runSyncMutation.isPending ? "Starting..." : "Run Sync Now"}
          </button>
          <label className="flex items-center gap-2 text-xs text-gray-600 cursor-pointer select-none">
            <input
              type="checkbox"
              checked={forceRun}
              onChange={(e) => setForceRun(e.target.checked)}
              disabled={isRunInProgress || runSyncMutation.isPending}
            />
            Test mode: bypass 8h guardrail for this manual run
          </label>
        </div>
      </div>

      {runSyncMutation.isSuccess && (
        <div className="bg-green-50 border border-green-200 text-green-800 rounded-lg px-4 py-3 text-sm">
          Sync execution started successfully.
        </div>
      )}
      {runError && (
        <div className="bg-red-50 border border-red-200 text-red-800 rounded-lg px-4 py-3 text-sm space-y-1">
          <p>{runError}</p>
          {retryAfterSeconds !== null && (
            <p className="text-xs">
              Puedes volver a lanzar en aproximadamente {Math.ceil(retryAfterSeconds / 60)} minutos.
            </p>
          )}
        </div>
      )}

      {currentRun && (
        <div className="bg-white border border-gray-200 rounded-lg p-5 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="font-semibold text-gray-800">Current Execution</h2>
            <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${statusColor(currentRun.status)}`}>
              {currentRun.status}
            </span>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <Kpi label="Descubiertos" value={currentRun.stats.total} />
            <Kpi label="Procesados" value={currentRun.stats.processed} />
            <Kpi label="Errores" value={currentRun.stats.errors} />
            <Kpi label="Omitidos" value={currentRun.stats.skipped} />
          </div>
          <p className="text-xs text-gray-600">
            Snapshots creados: {currentRun.stats.snapshots_created ?? 0} ({formatSnapshotRange(currentRun)})
          </p>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
            <TypeBox
              title="Hardware"
              discovered={currentRun.stats.by_type.hardware?.discovered ?? 0}
              processed={currentRun.stats.by_type.hardware?.processed ?? 0}
              errors={currentRun.stats.by_type.hardware?.errors ?? 0}
            />
            <TypeBox
              title="Software"
              discovered={currentRun.stats.by_type.software?.discovered ?? 0}
              processed={currentRun.stats.by_type.software?.processed ?? 0}
              errors={currentRun.stats.by_type.software?.errors ?? 0}
            />
          </div>
          <p className="text-xs text-gray-500">
            Started: {formatDateTime(currentRun.started_at)} | Finished: {formatDateTime(currentRun.finished_at)} |
            Duration: {currentRun.duration_seconds ? `${Math.round(currentRun.duration_seconds)}s` : "--"}
          </p>
          {currentRun.message && <p className="text-xs text-gray-600">{currentRun.message}</p>}
        </div>
      )}

      {(syncStatus ?? []).map(
        (s: { data_source_id: number; name: string; last_sync_at?: string; last_sync_status?: string; last_error?: string }) => (
          <div key={s.data_source_id} className="bg-white border border-gray-200 rounded-lg p-5 space-y-2">
            <div className="flex items-center justify-between">
              <h3 className="font-semibold text-gray-800">{s.name}</h3>
              {s.last_sync_status && (
                <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${statusColor(s.last_sync_status)}`}>
                  {s.last_sync_status}
                </span>
              )}
            </div>
            <p className="text-sm text-gray-500">Last sync: {formatDateTime(s.last_sync_at)}</p>
            {s.last_error && <p className="text-sm text-red-600">Error: {s.last_error}</p>}
          </div>
        )
      )}

      {(!syncStatus || syncStatus.length === 0) && (
        <div className="bg-yellow-50 border border-yellow-200 text-yellow-800 rounded-lg px-4 py-4 text-sm">
          No data sources configured. Go to <strong>Settings</strong> to configure Azure Blob Storage.
        </div>
      )}

      <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <h2 className="text-sm font-semibold text-gray-600 uppercase">Recent Executions</h2>
            <select
              value={selectedSyncType}
              onChange={(event) => setSelectedSyncType(event.target.value)}
              className="border border-gray-300 rounded-md text-xs px-2 py-1 text-gray-700 bg-white"
            >
              <option value="all">Todos</option>
              {availableSyncTypes.map((type) => (
                <option key={type} value={type}>
                  {syncTypeLabel(type)}
                </option>
              ))}
            </select>
          </div>
          {latestCompletedRun && (
            <span className="text-xs text-gray-500">
              Last duration:{" "}
              {latestCompletedRun.duration_seconds ? `${Math.round(latestCompletedRun.duration_seconds)}s` : "--"}
            </span>
          )}
        </div>
        <table className="min-w-full text-sm divide-y divide-gray-100">
          <thead className="bg-gray-50">
            <tr>
              {["Requested", "Tipo", "Status", "Descubiertos", "Procesados", "Errores", "Snapshots", "Duracion", "Resultado"].map((h) => (
                <th key={h} className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-50">
            {(runHistory ?? []).map((run: SyncExecution) => (
              <tr key={run.run_id} className="hover:bg-gray-50">
                <td className="px-4 py-2 text-xs text-gray-500">{formatDateTime(run.requested_at)}</td>
                <td className="px-4 py-2 text-xs text-gray-600">{syncTypeLabel(run.sync_type)}</td>
                <td className="px-4 py-2">
                  <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${statusColor(run.status)}`}>
                    {run.status}
                  </span>
                </td>
                <td className="px-4 py-2">{run.stats.total}</td>
                <td className="px-4 py-2">{run.stats.processed}</td>
                <td className="px-4 py-2">{run.stats.errors}</td>
                <td className="px-4 py-2 text-xs text-gray-600">{formatSnapshotRange(run)}</td>
                <td className="px-4 py-2 text-xs text-gray-500">
                  {run.duration_seconds ? `${Math.round(run.duration_seconds)}s` : "--"}
                </td>
                <td className="px-4 py-2 text-xs text-gray-600">{run.message || "--"}</td>
              </tr>
            ))}
          </tbody>
        </table>
        {(!runHistory || runHistory.length === 0) && (
          <p className="text-center py-8 text-gray-400">No sync executions yet</p>
        )}
      </div>
    </div>
  );
}

function Kpi({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded border border-gray-200 p-3 bg-gray-50">
      <p className="text-xs uppercase text-gray-500">{label}</p>
      <p className="text-lg font-semibold text-gray-800">{value}</p>
    </div>
  );
}

function TypeBox({
  title,
  discovered,
  processed,
  errors,
}: {
  title: string;
  discovered: number;
  processed: number;
  errors: number;
}) {
  return (
    <div className="rounded border border-gray-200 p-3 bg-gray-50">
      <p className="text-xs uppercase text-gray-500 mb-1">{title}</p>
      <p className="text-xs text-gray-700">Descubiertos: {discovered}</p>
      <p className="text-xs text-gray-700">Procesados: {processed}</p>
      <p className="text-xs text-gray-700">Errores: {errors}</p>
    </div>
  );
}

