import { useEffect, useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { softwareService } from "../services/software";
import type { SoftwareComplianceRule } from "../types";

const CREATE_NEW_LIST_VALUE = "__create_new__";

function decodeProductPattern(pattern?: string): string {
  if (!pattern) return "--";
  let value = pattern.trim();
  if (value.startsWith("^")) value = value.slice(1);
  if (value.endsWith("$")) value = value.slice(0, -1);
  value = value.replace(/\\(.)/g, "$1");
  return value || "--";
}

function getErrorDetail(error: unknown): string {
  const detail = (error as { response?: { data?: { detail?: unknown } } })?.response?.data?.detail;
  if (typeof detail === "string") return detail;
  return "Operation failed";
}

function groupByProfile(rules: SoftwareComplianceRule[]): Array<{ profile: string; rules: SoftwareComplianceRule[] }> {
  const grouped = new Map<string, SoftwareComplianceRule[]>();
  for (const rule of rules) {
    const profile = (rule.profile_name || "Default").trim() || "Default";
    if (!grouped.has(profile)) grouped.set(profile, []);
    grouped.get(profile)?.push(rule);
  }
  return Array.from(grouped.entries())
    .map(([profile, items]) => ({
      profile,
      rules: [...items].sort((a, b) =>
        decodeProductPattern(a.product_match_pattern).localeCompare(decodeProductPattern(b.product_match_pattern))
      ),
    }))
    .sort((a, b) => a.profile.localeCompare(b.profile));
}

export default function SoftwareSettingsPage() {
  const qc = useQueryClient();

  const [selectedComplianceList, setSelectedComplianceList] = useState("Default");
  const [newComplianceListName, setNewComplianceListName] = useState("");
  const [selectedBlacklist, setSelectedBlacklist] = useState("Default");
  const [newBlacklistName, setNewBlacklistName] = useState("");
  const [complianceSoftware, setComplianceSoftware] = useState("");
  const [blacklistSoftware, setBlacklistSoftware] = useState("");
  const [minimumVersion, setMinimumVersion] = useState("");
  const [catalogSearch, setCatalogSearch] = useState("");
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const rulesQuery = useQuery({
    queryKey: ["software-settings-rules-all"],
    queryFn: () => softwareService.listComplianceRules(),
  });

  const catalogQuery = useQuery({
    queryKey: ["software-settings-catalog", catalogSearch],
    queryFn: () => softwareService.listCatalog(catalogSearch || undefined),
  });

  const allRules = rulesQuery.data ?? [];
  const complianceRules = allRules.filter((rule) => rule.is_required && !rule.is_forbidden);
  const blacklistRules = allRules.filter((rule) => rule.is_forbidden);

  const complianceLists = useMemo(
    () =>
      Array.from(new Set(complianceRules.map((rule) => rule.profile_name).filter(Boolean)))
        .map((name) => name.trim())
        .filter(Boolean)
        .sort(),
    [complianceRules]
  );
  const blacklistLists = useMemo(
    () =>
      Array.from(new Set(blacklistRules.map((rule) => rule.profile_name).filter(Boolean)))
        .map((name) => name.trim())
        .filter(Boolean)
        .sort(),
    [blacklistRules]
  );

  useEffect(() => {
    if (selectedComplianceList === CREATE_NEW_LIST_VALUE) return;
    if (complianceLists.length === 0) return;
    if (!complianceLists.includes(selectedComplianceList)) {
      setSelectedComplianceList(complianceLists[0]);
    }
  }, [complianceLists, selectedComplianceList]);

  useEffect(() => {
    if (selectedBlacklist === CREATE_NEW_LIST_VALUE) return;
    if (blacklistLists.length === 0) return;
    if (!blacklistLists.includes(selectedBlacklist)) {
      setSelectedBlacklist(blacklistLists[0]);
    }
  }, [blacklistLists, selectedBlacklist]);

  const effectiveComplianceListName =
    selectedComplianceList === CREATE_NEW_LIST_VALUE ? newComplianceListName.trim() : selectedComplianceList.trim();
  const effectiveBlacklistName =
    selectedBlacklist === CREATE_NEW_LIST_VALUE ? newBlacklistName.trim() : selectedBlacklist.trim();

  const complianceGroups = useMemo(() => groupByProfile(complianceRules), [complianceRules]);
  const blacklistGroups = useMemo(() => groupByProfile(blacklistRules), [blacklistRules]);

  const createComplianceRuleMutation = useMutation({
    mutationFn: () =>
      softwareService.createComplianceRule({
        profile_name: effectiveComplianceListName || "Default",
        software_name: complianceSoftware,
        rule_kind: "minimum_version",
        minimum_version: minimumVersion,
      }),
    onSuccess: (rule) => {
      qc.invalidateQueries({ queryKey: ["software-settings-rules-all"] });
      qc.invalidateQueries({ queryKey: ["software-settings-profiles"] });
      qc.invalidateQueries({ queryKey: ["software-compliance-summary"] });
      setSelectedComplianceList(rule.profile_name || "Default");
      setNewComplianceListName("");
      setComplianceSoftware("");
      setMinimumVersion("");
      setCatalogSearch("");
      setStatusMessage("Software added to compliance list.");
      setErrorMessage(null);
    },
    onError: (error) => {
      setErrorMessage(getErrorDetail(error));
      setStatusMessage(null);
    },
  });

  const createBlacklistRuleMutation = useMutation({
    mutationFn: () =>
      softwareService.createComplianceRule({
        profile_name: effectiveBlacklistName || "Default",
        software_name: blacklistSoftware,
        rule_kind: "forbidden",
      }),
    onSuccess: (rule) => {
      qc.invalidateQueries({ queryKey: ["software-settings-rules-all"] });
      qc.invalidateQueries({ queryKey: ["software-settings-profiles"] });
      qc.invalidateQueries({ queryKey: ["software-compliance-summary"] });
      setSelectedBlacklist(rule.profile_name || "Default");
      setNewBlacklistName("");
      setBlacklistSoftware("");
      setCatalogSearch("");
      setStatusMessage("Software added to blacklist.");
      setErrorMessage(null);
    },
    onError: (error) => {
      setErrorMessage(getErrorDetail(error));
      setStatusMessage(null);
    },
  });

  const deleteRuleMutation = useMutation({
    mutationFn: (ruleId: number) => softwareService.deleteComplianceRule(ruleId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["software-settings-rules-all"] });
      qc.invalidateQueries({ queryKey: ["software-compliance-summary"] });
      setStatusMessage("Rule removed.");
      setErrorMessage(null);
    },
    onError: (error) => {
      setErrorMessage(getErrorDetail(error));
      setStatusMessage(null);
    },
  });

  return (
    <div className="p-8 space-y-6">
      <h1 className="text-2xl font-bold text-gray-800">Software Settings</h1>

      <div className="bg-white border border-gray-200 rounded-lg p-5 space-y-4">
        <h2 className="text-sm font-semibold text-gray-700 uppercase tracking-wide">Compliance Lists (minimum version)</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Compliance List Name</label>
            <select
              value={selectedComplianceList}
              onChange={(e) => setSelectedComplianceList(e.target.value)}
              className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {complianceLists.map((name) => (
                <option key={name} value={name}>
                  {name}
                </option>
              ))}
              <option value={CREATE_NEW_LIST_VALUE}>Create new...</option>
            </select>
            {selectedComplianceList === CREATE_NEW_LIST_VALUE && (
              <input
                type="text"
                value={newComplianceListName}
                onChange={(e) => setNewComplianceListName(e.target.value)}
                className="mt-2 w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="New compliance list name"
              />
            )}
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Software Name</label>
            <input
              type="text"
              value={complianceSoftware}
              onChange={(e) => {
                setComplianceSoftware(e.target.value);
                setCatalogSearch(e.target.value);
              }}
              className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              list="software-catalog"
              placeholder="Search and select software"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Minimum Version</label>
            <input
              type="text"
              value={minimumVersion}
              onChange={(e) => setMinimumVersion(e.target.value)}
              className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="e.g. 125.0.6422.142"
            />
          </div>
        </div>
        <div className="flex justify-end">
          <button
            onClick={() => createComplianceRuleMutation.mutate()}
            disabled={
              createComplianceRuleMutation.isPending ||
              !effectiveComplianceListName ||
              !complianceSoftware.trim() ||
              !minimumVersion.trim()
            }
            className="px-4 py-2 bg-blue-600 text-white rounded-md text-sm hover:bg-blue-700 disabled:opacity-40"
          >
            Add To Compliance List
          </button>
        </div>
      </div>

      <div className="bg-white border border-gray-200 rounded-lg p-5 space-y-4">
        <h2 className="text-sm font-semibold text-gray-700 uppercase tracking-wide">Blacklists</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Blacklist Name</label>
            <select
              value={selectedBlacklist}
              onChange={(e) => setSelectedBlacklist(e.target.value)}
              className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {blacklistLists.map((name) => (
                <option key={name} value={name}>
                  {name}
                </option>
              ))}
              <option value={CREATE_NEW_LIST_VALUE}>Create new...</option>
            </select>
            {selectedBlacklist === CREATE_NEW_LIST_VALUE && (
              <input
                type="text"
                value={newBlacklistName}
                onChange={(e) => setNewBlacklistName(e.target.value)}
                className="mt-2 w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="New blacklist name"
              />
            )}
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Software Name</label>
            <input
              type="text"
              value={blacklistSoftware}
              onChange={(e) => {
                setBlacklistSoftware(e.target.value);
                setCatalogSearch(e.target.value);
              }}
              className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              list="software-catalog"
              placeholder="Search and select software"
            />
          </div>
        </div>
        <div className="flex justify-end">
          <button
            onClick={() => createBlacklistRuleMutation.mutate()}
            disabled={createBlacklistRuleMutation.isPending || !effectiveBlacklistName || !blacklistSoftware.trim()}
            className="px-4 py-2 bg-red-600 text-white rounded-md text-sm hover:bg-red-700 disabled:opacity-40"
          >
            Add To Blacklist
          </button>
        </div>
      </div>

      <datalist id="software-catalog">
        {(catalogQuery.data ?? []).map((item) => (
          <option key={item.normalized_name} value={item.display_name || item.normalized_name} />
        ))}
      </datalist>

      {statusMessage && <p className="text-sm text-green-700">{statusMessage}</p>}
      {errorMessage && <p className="text-sm text-red-700">{errorMessage}</p>}

      <div className="bg-white rounded-lg border border-gray-200 p-4 space-y-4">
        <h3 className="font-semibold text-gray-800">Configured Compliance Lists</h3>
        {complianceGroups.length === 0 ? (
          <p className="text-sm text-gray-500">No compliance lists configured.</p>
        ) : (
          complianceGroups.map((group) => (
            <div key={group.profile} className="border border-gray-200 rounded-md overflow-hidden">
              <div className="bg-gray-50 px-4 py-2 flex items-center justify-between">
                <span className="font-medium text-gray-800">{group.profile}</span>
                <span className="text-xs text-gray-500">{group.rules.length} app(s)</span>
              </div>
              <table className="min-w-full text-sm">
                <thead className="border-t border-gray-200 bg-white">
                  <tr>
                    <th className="px-4 py-2 text-left text-xs font-semibold text-gray-500 uppercase">Software</th>
                    <th className="px-4 py-2 text-left text-xs font-semibold text-gray-500 uppercase">Minimum Version</th>
                    <th className="px-4 py-2 text-left text-xs font-semibold text-gray-500 uppercase">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {group.rules.map((rule) => (
                    <tr key={rule.id} className="border-t border-gray-100">
                      <td className="px-4 py-2 text-gray-700">{decodeProductPattern(rule.product_match_pattern)}</td>
                      <td className="px-4 py-2 text-gray-700 font-mono">{rule.minimum_version || "--"}</td>
                      <td className="px-4 py-2">
                        <button
                          className="text-red-600 text-sm hover:underline disabled:opacity-40"
                          onClick={() => deleteRuleMutation.mutate(rule.id)}
                          disabled={deleteRuleMutation.isPending}
                        >
                          Remove
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ))
        )}
      </div>

      <div className="bg-white rounded-lg border border-gray-200 p-4 space-y-4">
        <h3 className="font-semibold text-gray-800">Configured Blacklists</h3>
        {blacklistGroups.length === 0 ? (
          <p className="text-sm text-gray-500">No blacklists configured.</p>
        ) : (
          blacklistGroups.map((group) => (
            <div key={group.profile} className="border border-gray-200 rounded-md overflow-hidden">
              <div className="bg-gray-50 px-4 py-2 flex items-center justify-between">
                <span className="font-medium text-gray-800">{group.profile}</span>
                <span className="text-xs text-gray-500">{group.rules.length} app(s)</span>
              </div>
              <table className="min-w-full text-sm">
                <thead className="border-t border-gray-200 bg-white">
                  <tr>
                    <th className="px-4 py-2 text-left text-xs font-semibold text-gray-500 uppercase">Software</th>
                    <th className="px-4 py-2 text-left text-xs font-semibold text-gray-500 uppercase">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {group.rules.map((rule) => (
                    <tr key={rule.id} className="border-t border-gray-100">
                      <td className="px-4 py-2 text-gray-700">{decodeProductPattern(rule.product_match_pattern)}</td>
                      <td className="px-4 py-2">
                        <button
                          className="text-red-600 text-sm hover:underline disabled:opacity-40"
                          onClick={() => deleteRuleMutation.mutate(rule.id)}
                          disabled={deleteRuleMutation.isPending}
                        >
                          Remove
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ))
        )}
      </div>
    </div>
  );
}

