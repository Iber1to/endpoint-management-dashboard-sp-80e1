import { api } from "./api";
import type { InventoryFile, SyncExecution, SyncRunAcceptedResponse } from "../types";

export const syncService = {
  runSync: (data_source_id?: number) =>
    api.post<SyncRunAcceptedResponse>("/sync/run", null, { params: data_source_id ? { data_source_id } : undefined }).then((r) => r.data),

  getStatus: () =>
    api.get("/sync/status").then((r) => r.data),

  getCurrentRun: () =>
    api.get<SyncExecution | null>("/sync/runs/current").then((r) => r.data),

  listRuns: (limit = 10) =>
    api.get<SyncExecution[]>("/sync/runs", { params: { limit } }).then((r) => r.data),

  listFiles: (params?: Record<string, unknown>) =>
    api.get<InventoryFile[]>("/sync/files", { params }).then((r) => r.data),

  getOverview: () =>
    api.get("/overview").then((r) => r.data),
};
