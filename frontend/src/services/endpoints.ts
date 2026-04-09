import { api } from "./api";
import type { EndpointListResponse, EndpointDetail, InstalledSoftware, UpdateStatusItem } from "../types";

export const endpointsService = {
  list: (params?: Record<string, unknown>) =>
    api.get<EndpointListResponse>("/endpoints", { params }).then((r) => r.data),

  getById: (id: number) =>
    api.get<EndpointDetail>(`/endpoints/${id}`).then((r) => r.data),

  getSoftware: (id: number, params?: Record<string, unknown>) =>
    api.get<InstalledSoftware[]>(`/endpoints/${id}/software`, { params }).then((r) => r.data),

  getUpdates: (id: number) =>
    api.get<UpdateStatusItem[]>(`/endpoints/${id}/updates`).then((r) => r.data),

  getHistory: (id: number) =>
    api.get(`/endpoints/${id}/history`).then((r) => r.data),
};
