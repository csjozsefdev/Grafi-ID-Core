import { useCallback, useEffect, useState } from "react";
import {
  fetchAppSettings,
  getUserErrorMessage,
  openProjectFolderPath,
  resetAppSettings,
  saveAppSettings,
} from "../ipc/client";
import type { AppSettingsData } from "../ipc/types";

interface SettingsDraft {
  default_project_opener: string;
  usage_journal_enabled: boolean;
  debug_timing_enabled: boolean;
  compact_mode: boolean;
}

function applyCompactMode(enabled: boolean) {
  document.documentElement.classList.toggle("grafid-compact", enabled);
}

function toDraft(data: AppSettingsData): SettingsDraft {
  return {
    default_project_opener: data.default_project_opener,
    usage_journal_enabled: data.usage_journal_enabled,
    debug_timing_enabled: data.debug_timing_enabled,
    compact_mode: Boolean(data.compact_mode),
  };
}

export function Settings() {
  const [settings, setSettings] = useState<AppSettingsData | null>(null);
  const [draft, setDraft] = useState<SettingsDraft | null>(null);
  const [settingsError, setSettingsError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  const loadSettings = useCallback(async () => {
    setLoading(true);
    setNotice(null);
    try {
      const data = await fetchAppSettings();
      setSettings(data);
      setDraft(toDraft(data));
      applyCompactMode(Boolean(data.compact_mode));
      setSettingsError(null);
    } catch (err) {
      setSettings(null);
      setDraft(null);
      setSettingsError(getUserErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadSettings();
  }, [loadSettings]);

  const handleSave = async () => {
    if (!draft) return;
    setSaving(true);
    setNotice(null);
    setSettingsError(null);
    try {
      const result = await saveAppSettings({
        default_project_opener: draft.default_project_opener,
        usage_journal_enabled: draft.usage_journal_enabled,
        debug_timing_enabled: draft.debug_timing_enabled,
        compact_mode: draft.compact_mode,
      });
      setSettings(result);
      setDraft(toDraft(result));
      applyCompactMode(Boolean(result.compact_mode));
      setNotice(result.message);
    } catch (err) {
      setSettingsError(getUserErrorMessage(err));
    } finally {
      setSaving(false);
    }
  };

  const handleReset = async () => {
    setSaving(true);
    setNotice(null);
    setSettingsError(null);
    try {
      const result = await resetAppSettings();
      setSettings(result);
      setDraft(toDraft(result));
      setNotice(result.message);
    } catch (err) {
      setSettingsError(getUserErrorMessage(err));
    } finally {
      setSaving(false);
    }
  };

  const openFolder = async (path: string, label: string) => {
    setSettingsError(null);
    setNotice(null);
    try {
      await openProjectFolderPath(path);
      setNotice(`Opened ${label} in File Explorer.`);
    } catch (err) {
      setSettingsError(`${label}: ${getUserErrorMessage(err)}`);
    }
  };

  const options = settings?.opener_options ?? [
    { id: "system", label: "System default" },
    { id: "cursor", label: "Cursor" },
    { id: "vscode", label: "VS Code" },
    { id: "explorer", label: "Explorer only" },
  ];

  return (
    <section className="placeholder-page">
      <h2>Settings</h2>
      <p className="muted">Local preferences stored in config.json in your Graf-Id data folder.</p>

      {loading ? <p className="muted">Loading settings…</p> : null}

      {settingsError ? (
        <div className="placeholder-page__block">
          <p className="error-text">{settingsError}</p>
          <button type="button" onClick={() => void loadSettings()} disabled={saving}>
            Retry
          </button>
        </div>
      ) : null}

      {notice && !settingsError ? (
        <p className="settings-field__notice settings-field__notice--ok" role="status">
          {notice}
        </p>
      ) : null}

      {draft && !loading ? (
        <form
          className="placeholder-page__block settings-form"
          onSubmit={(e) => {
            e.preventDefault();
            void handleSave();
          }}
        >
          <div className="settings-field">
            <label className="settings-field__label" htmlFor="default-project-opener">
              Open projects with
            </label>
            <select
              id="default-project-opener"
              className="settings-field__select"
              value={draft.default_project_opener}
              disabled={saving}
              onChange={(e) =>
                setDraft((prev) =>
                  prev ? { ...prev, default_project_opener: e.target.value } : prev
                )
              }
            >
              {options.map((opt) => (
                <option key={opt.id} value={opt.id}>
                  {opt.label}
                </option>
              ))}
            </select>
            <p className="muted settings-field__hint">
              Used when you click Open Project. Open Folder always uses File Explorer.
            </p>
          </div>

          <div className="settings-field settings-field--checkbox">
            <label>
              <input
                type="checkbox"
                checked={draft.usage_journal_enabled}
                disabled={saving}
                onChange={(e) =>
                  setDraft((prev) =>
                    prev ? { ...prev, usage_journal_enabled: e.target.checked } : prev
                  )
                }
              />
              Usage journal (local only, no telemetry)
            </label>
          </div>

          <div className="settings-field settings-field--checkbox">
            <label>
              <input
                type="checkbox"
                checked={draft.debug_timing_enabled}
                disabled={saving}
                onChange={(e) =>
                  setDraft((prev) =>
                    prev ? { ...prev, debug_timing_enabled: e.target.checked } : prev
                  )
                }
              />
              Debug timing in IPC responses
            </label>
          </div>

          <div className="settings-field settings-field--checkbox">
            <label>
              <input
                type="checkbox"
                checked={draft.compact_mode}
                disabled={saving}
                onChange={(e) =>
                  setDraft((prev) =>
                    prev ? { ...prev, compact_mode: e.target.checked } : prev
                  )
                }
              />
              Compact layout (denser dashboard)
            </label>
          </div>

          <div className="settings-form__actions">
            <button type="submit" disabled={saving}>
              {saving ? "Saving…" : "Save"}
            </button>
            <button type="button" disabled={saving} onClick={() => void handleReset()}>
              Reset defaults
            </button>
          </div>
        </form>
      ) : null}

      {settings ? (
        <div className="placeholder-page__block">
          <h3>Data folders</h3>
          <p className="muted placeholder-page__path">{settings.data_dir}</p>
          <div className="settings-form__actions">
            <button
              type="button"
              disabled={saving}
              onClick={() => void openFolder(settings.data_dir, "data folder")}
            >
              Open data folder
            </button>
            <button
              type="button"
              disabled={saving}
              onClick={() => void openFolder(settings.logs_dir, "logs folder")}
            >
              Open logs folder
            </button>
          </div>
        </div>
      ) : null}
    </section>
  );
}

/** @deprecated Use Settings */
export const SettingsPlaceholder = Settings;
