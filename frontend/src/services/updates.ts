import { api } from "./api";
import type { UpdateComplianceResponse, PatchReference } from "../types";

export const updatesService = {
  getCompliance: () =>
    api.get<UpdateComplianceResponse>("/updates/compliance").then((r) => r.data),

  getCatalog: (params?: Record<string, unknown>) =>
    api.get<PatchReference[]>("/updates/catalog", { params }).then((r) => r.data),

  getCatalogStatus: () =>
    api.get("/updates/catalog/status").then((r) => r.data),

  syncCatalog: () =>
    api.post("/updates/catalog/sync").then((r) => r.data),

  evaluateUpdates: () =>
    api.post("/updates/evaluate").then((r) => r.data),

  getOverview: () =>
    api.get("/updates/overview").then((r) => r.data),
};
