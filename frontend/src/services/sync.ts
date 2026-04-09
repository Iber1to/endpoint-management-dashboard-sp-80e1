import { api } from "./api";
import type { InventoryFile } from "../types";

export const syncService = {
  runSync: (data_source_id?: number) =>
    api.post("/sync/run", null, { params: data_source_id ? { data_source_id } : undefined }).then((r) => r.data),

  getStatus: () =>
    api.get("/sync/status").then((r) => r.data),

  listFiles: (params?: Record<string, unknown>) =>
    api.get<InventoryFile[]>("/sync/files", { params }).then((r) => r.data),

  getOverview: () =>
    api.get("/overview").then((r) => r.data),
};
