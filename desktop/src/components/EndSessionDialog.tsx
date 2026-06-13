import { useEffect, useState } from "react";
import { closeProjectSession, getUserErrorMessage } from "../ipc/client";

interface EndSessionDialogProps {
  open: boolean;
  projectId: number | null;
  onClose: () => void;
  onEnded: () => void;
}

export function EndSessionDialog({
  open: isOpen,
  projectId,
  onClose,
  onEnded,
}: EndSessionDialogProps) {
  const [doneToday, setDoneToday] = useState("");
  const [unfinished, setUnfinished] = useState("");
  const [nextStep, setNextStep] = useState("");
  const [blocker, setBlocker] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (!isOpen) {
      setDoneToday("");
      setUnfinished("");
      setNextStep("");
      setBlocker("");
      setError(null);
      setSaving(false);
    }
  }, [isOpen]);

  if (!isOpen || projectId === null) {
    return null;
  }

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setSaving(true);
    setError(null);
    try {
      await closeProjectSession(projectId, {
        exit_note: doneToday.trim() || undefined,
        unfinished: unfinished.trim() || undefined,
        next_step: nextStep.trim() || undefined,
        blocker: blocker.trim() || undefined,
      });
      onEnded();
      onClose();
    } catch (err) {
      setError(getUserErrorMessage(err));
    } finally {
      setSaving(false);
    }
  };

  const handleSkip = async () => {
    setSaving(true);
    setError(null);
    try {
      await closeProjectSession(projectId, { skip_notes: true });
      onEnded();
      onClose();
    } catch (err) {
      setError(getUserErrorMessage(err));
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="modal-backdrop" role="presentation" onClick={onClose}>
      <div
        className="modal"
        role="dialog"
        aria-labelledby="end-session-title"
        onClick={(e) => e.stopPropagation()}
      >
        <h2 id="end-session-title">End session</h2>
        <p className="muted">Capture where you left off for the next resume.</p>
        <form onSubmit={handleSubmit} className="modal__form">
          <label>
            What did you do today?
            <textarea
              value={doneToday}
              onChange={(e) => setDoneToday(e.target.value)}
              rows={2}
              disabled={saving}
            />
          </label>
          <label>
            What is still unfinished?
            <textarea
              value={unfinished}
              onChange={(e) => setUnfinished(e.target.value)}
              rows={2}
              disabled={saving}
            />
          </label>
          <label>
            What is the next step?
            <textarea
              value={nextStep}
              onChange={(e) => setNextStep(e.target.value)}
              rows={2}
              disabled={saving}
            />
          </label>
          <label>
            Any blocker?
            <textarea
              value={blocker}
              onChange={(e) => setBlocker(e.target.value)}
              rows={2}
              disabled={saving}
            />
          </label>
          {error ? <p className="error-text">{error}</p> : null}
          <div className="modal__actions">
            <button type="button" onClick={handleSkip} disabled={saving}>
              Skip notes
            </button>
            <button type="button" onClick={onClose} disabled={saving}>
              Cancel
            </button>
            <button type="submit" className="startup__button" disabled={saving}>
              {saving ? "Saving…" : "End session"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
