import { api } from "./api";
import type {
  SoftwareAnalyticsResponse,
  SoftwareCatalogItem,
  SoftwareComplianceEndpointFindingListResponse,
  SoftwareComplianceRule,
  SoftwareComplianceSummaryResponse,
  SoftwareEndpointInstallListResponse,
  SoftwareListResponse,
  SoftwareVersionListResponse,
} from "../types";

export const softwareService = {
  list: (params?: Record<string, unknown>) =>
    api.get<SoftwareListResponse>("/software", { params }).then((r) => r.data),

  listCatalog: (search?: string) =>
    api
      .get<SoftwareCatalogItem[]>("/software/catalog", { params: { search } })
      .then((r) => r.data),

  getAnalytics: () =>
    api.get<SoftwareAnalyticsResponse>("/software/analytics").then((r) => r.data),

  listEndpoints: (params: {
    normalized_name: string;
    software_version?: string;
    page?: number;
    page_size?: number;
  }) => api.get<SoftwareEndpointInstallListResponse>("/software/endpoints", { params }).then((r) => r.data),

  listVersions: (normalized_name: string) =>
    api.get<SoftwareVersionListResponse>("/software/versions", { params: { normalized_name } }).then((r) => r.data),

  listComplianceProfiles: () => api.get<string[]>("/software/settings/profiles").then((r) => r.data),

  listComplianceRules: (profile_name?: string) =>
    api.get<SoftwareComplianceRule[]>("/software/settings/rules", { params: { profile_name } }).then((r) => r.data),

  createComplianceRule: (payload: {
    profile_name: string;
    software_name: string;
    rule_kind: "forbidden" | "minimum_version";
    minimum_version?: string;
    severity?: string;
  }) => api.post<SoftwareComplianceRule>("/software/settings/rules", payload).then((r) => r.data),

  deleteComplianceRule: (ruleId: number) =>
    api.delete(`/software/settings/rules/${ruleId}`).then(() => undefined),

  getComplianceSummary: (profile_name?: string) =>
    api.get<SoftwareComplianceSummaryResponse>("/software/compliance/summary", { params: { profile_name } }).then((r) => r.data),

  getComplianceFindings: (params: {
    profile_name: string;
    mode?: "all" | "forbidden" | "minimum_version";
    page?: number;
    page_size?: number;
  }) => api.get<SoftwareComplianceEndpointFindingListResponse>("/software/compliance/endpoints", { params }).then((r) => r.data),
};
