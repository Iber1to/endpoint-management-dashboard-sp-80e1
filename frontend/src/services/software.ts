import { api } from "./api";
import type { SoftwareListResponse } from "../types";

export const softwareService = {
  list: (params?: Record<string, unknown>) =>
    api.get<SoftwareListResponse>("/software", { params }).then((r) => r.data),
};
