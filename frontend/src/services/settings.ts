import { api } from "./api";
import type { BlobSettings } from "../types";

export const settingsService = {
  getBlobSettings: () =>
    api.get<BlobSettings[]>("/settings/blob").then((r) => r.data),

  saveBlobSettings: (payload: {
    name: string;
    account_url: string;
    container_name: string;
    sas_token: string;
    blob_prefix?: string;
    sync_frequency_minutes?: number;
    is_active?: boolean;
  }) => api.post<BlobSettings>("/settings/blob", payload).then((r) => r.data),

  testConnection: (payload: {
    account_url: string;
    container_name: string;
    sas_token: string;
    blob_prefix?: string;
  }) =>
    api.post<{ success: boolean; containers_visible: boolean; sample_blobs: string[]; error?: string }>(
      "/settings/blob/test",
      payload
    ).then((r) => r.data),
};
