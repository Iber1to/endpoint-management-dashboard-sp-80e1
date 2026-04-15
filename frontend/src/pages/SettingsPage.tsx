import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { settingsService } from "../services/settings";
import { formatDateTime } from "../utils";
import type { BlobSettings } from "../types";

const DEFAULT_FORM = {
  name: "default",
  account_url: "",
  container_name: "",
  sas_token: "",
  blob_prefix: "",
  sync_frequency_minutes: 1440,
  max_files_per_run: 50000,
  max_files_per_run_enabled: false,
  is_active: true,
};

export default function SettingsPage() {
  const qc = useQueryClient();
  const { data: settings } = useQuery({
    queryKey: ["blob-settings"],
    queryFn: () => settingsService.getBlobSettings(),
  });

  const [form, setForm] = useState(DEFAULT_FORM);
  const [testResult, setTestResult] = useState<{ success: boolean; message: string; blobs?: string[] } | null>(null);

  const saveMutation = useMutation({
    mutationFn: () => settingsService.saveBlobSettings(form),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["blob-settings"] });
      setTestResult(null);
    },
  });

  const testMutation = useMutation({
    onMutate: () => {
      setTestResult(null);
    },
    mutationFn: () =>
      settingsService.testConnection({
        account_url: form.account_url,
        container_name: form.container_name,
        sas_token: form.sas_token,
        blob_prefix: form.blob_prefix,
      }),
    onSuccess: (data) => {
      setTestResult({
        success: data.success,
        message: data.success ? "Connection successful!" : `Failed: ${data.error}`,
        blobs: data.sample_blobs,
      });
    },
    onError: (error) => {
      setTestResult({
        success: false,
        message: `Failed: ${getApiErrorMessage(error, "Connection test failed")}`,
      });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (sourceId: number) => settingsService.deleteBlobSettings(sourceId),
    onSuccess: (_, deletedSourceId) => {
      qc.invalidateQueries({ queryKey: ["blob-settings"] });
      const deleted = settings?.find((s) => s.id === deletedSourceId);
      if (deleted && form.name === deleted.name) {
        setForm(DEFAULT_FORM);
      }
      setTestResult(null);
    },
  });

  const handleLoad = (s: BlobSettings) => {
    if (!s) return;
    setForm({
      name: s.name,
      account_url: s.account_url || "",
      container_name: s.container_name || "",
      sas_token: "",
      blob_prefix: s.blob_prefix || "",
      sync_frequency_minutes: Math.max(480, s.sync_frequency_minutes),
      max_files_per_run: s.max_files_per_run ?? 50000,
      max_files_per_run_enabled: s.max_files_per_run_enabled ?? false,
      is_active: s.is_active,
    });
  };

  return (
    <div className="p-8 space-y-8">
      <h1 className="text-2xl font-bold text-gray-800">Settings</h1>

      {settings && settings.length > 0 && (
        <div className="bg-white border border-gray-200 rounded-lg p-5 space-y-3">
          <h2 className="text-sm font-semibold text-gray-600 uppercase">Configured Sources</h2>
          {settings.map((s) => (
            <div key={s.id} className="flex items-center justify-between border-b border-gray-100 pb-3">
              <div>
                <p className="font-medium text-gray-800">{s.name}</p>
                <p className="text-sm text-gray-500">{s.account_url} / {s.container_name}</p>
                <p className="text-xs text-gray-400">
                  Token: {s.sas_token_masked} | Last sync: {formatDateTime(s.last_sync_at)} | Status: {s.last_sync_status || "--"}
                </p>
                {s.last_error && <p className="text-xs text-red-500">{s.last_error}</p>}
              </div>
              <div className="flex items-center gap-3">
                <button
                  className="text-sm text-blue-600 hover:underline"
                  onClick={() => handleLoad(s as Parameters<typeof handleLoad>[0])}
                >
                  Load
                </button>
                <button
                  className="text-sm text-red-600 hover:underline disabled:opacity-40"
                  disabled={deleteMutation.isPending}
                  onClick={() => {
                    const shouldDelete = window.confirm(
                      `Delete source "${s.name}"? This will remove its saved token and settings.`
                    );
                    if (!shouldDelete) return;
                    deleteMutation.mutate(s.id);
                  }}
                >
                  {deleteMutation.isPending ? "Deleting..." : "Delete"}
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      <div className="bg-white border border-gray-200 rounded-lg p-6 space-y-5">
        <h2 className="text-sm font-semibold text-gray-600 uppercase">Blob Storage Configuration</h2>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          <FormField label="Source Name" value={form.name} onChange={(v) => setForm({ ...form, name: v })} />
          <FormField
            label="Storage Account URL"
            value={form.account_url}
            onChange={(v) => setForm({ ...form, account_url: v })}
            placeholder="https://youraccount.blob.core.windows.net"
          />
          <FormField
            label="Container Name"
            value={form.container_name}
            onChange={(v) => setForm({ ...form, container_name: v })}
          />
          <FormField
            label="SAS Token"
            value={form.sas_token}
            onChange={(v) => setForm({ ...form, sas_token: v })}
            type="password"
            placeholder="sv=2020-...&sp=rl&..."
          />
          <FormField
            label="Blob Prefix (optional)"
            value={form.blob_prefix}
            onChange={(v) => setForm({ ...form, blob_prefix: v })}
            placeholder="folder/subfolder/"
          />
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Sync Frequency (minutes)</label>
            <input
              type="number"
              className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              value={form.sync_frequency_minutes}
              min={480}
              onChange={(e) => setForm({ ...form, sync_frequency_minutes: Number(e.target.value) })}
            />
            <p className="mt-1 text-xs text-gray-500">Minimum allowed: 480 minutes (8 hours).</p>
          </div>
        </div>

        <div className="rounded-md border border-gray-200 bg-gray-50 p-4 space-y-3">
          <label className="flex items-center gap-2 text-sm text-gray-700 cursor-pointer">
            <input
              type="checkbox"
              checked={form.max_files_per_run_enabled}
              onChange={(e) => setForm({ ...form, max_files_per_run_enabled: e.target.checked })}
              className="rounded"
            />
            Enable max files per run safeguard
          </label>
          <div className="max-w-xs">
            <label className="block text-sm font-medium text-gray-700 mb-1">max_files_per_run</label>
            <input
              type="number"
              className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100 disabled:text-gray-500"
              value={form.max_files_per_run}
              min={1}
              onChange={(e) => setForm({ ...form, max_files_per_run: Number(e.target.value) })}
              disabled={!form.max_files_per_run_enabled}
            />
          </div>
          <p className="text-xs text-gray-500">
            Disabled by default. Use this only as a safeguard for unusually large backlogs. When enabled, each sync
            execution processes at most the configured number of discovered files.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <label className="flex items-center gap-2 text-sm text-gray-600 cursor-pointer">
            <input
              type="checkbox"
              checked={form.is_active}
              onChange={(e) => setForm({ ...form, is_active: e.target.checked })}
              className="rounded"
            />
            Active
          </label>
        </div>

        {testResult && (
          <div
            className={`rounded-lg px-4 py-3 text-sm ${
              testResult.success
                ? "bg-green-50 border border-green-200 text-green-800"
                : "bg-red-50 border border-red-200 text-red-800"
            }`}
          >
            <p>{testResult.message}</p>
            {testResult.blobs && testResult.blobs.length > 0 && (
              <ul className="mt-2 space-y-0.5">
                {testResult.blobs.map((b) => (
                  <li key={b} className="font-mono text-xs">- {b}</li>
                ))}
              </ul>
            )}
          </div>
        )}

        <div className="flex gap-3">
          <button
            onClick={() => testMutation.mutate()}
            disabled={testMutation.isPending || !form.account_url || !form.sas_token}
            className="px-4 py-2 border border-blue-600 text-blue-600 rounded-md text-sm hover:bg-blue-50 disabled:opacity-40 transition-colors"
          >
            {testMutation.isPending ? "Testing..." : "Test Connection"}
          </button>
          <button
            onClick={() => saveMutation.mutate()}
            disabled={saveMutation.isPending || !form.account_url || !form.sas_token}
            className="px-4 py-2 bg-blue-600 text-white rounded-md text-sm hover:bg-blue-700 disabled:opacity-40 transition-colors"
          >
            {saveMutation.isPending ? "Saving..." : "Save Settings"}
          </button>
        </div>

        {saveMutation.isSuccess && <p className="text-sm text-green-700">Settings saved successfully.</p>}
        {saveMutation.isError && (
          <p className="text-sm text-red-700">
            Failed to save settings: {getApiErrorMessage(saveMutation.error, "Unknown error")}
          </p>
        )}
        {deleteMutation.isSuccess && <p className="text-sm text-green-700">Source deleted successfully.</p>}
        {deleteMutation.isError && (
          <p className="text-sm text-red-700">
            Failed to delete source: {getApiErrorMessage(deleteMutation.error, "Unknown error")}
          </p>
        )}
      </div>
    </div>
  );
}

function getApiErrorMessage(error: unknown, fallback: string): string {
  const maybeError = error as {
    message?: string;
    response?: {
      data?: {
        detail?: unknown;
      };
    };
  };

  const detail = maybeError?.response?.data?.detail;
  if (typeof detail === "string" && detail.trim()) {
    return detail;
  }
  if (detail && typeof detail === "object" && "message" in detail) {
    const nested = (detail as { message?: unknown }).message;
    if (typeof nested === "string" && nested.trim()) {
      return nested;
    }
  }
  if (typeof maybeError?.message === "string" && maybeError.message.trim()) {
    return maybeError.message;
  }
  return fallback;
}

function FormField({
  label,
  value,
  onChange,
  type = "text",
  placeholder,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  type?: string;
  placeholder?: string;
}) {
  return (
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-1">{label}</label>
      <input
        type={type}
        className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
      />
    </div>
  );
}
