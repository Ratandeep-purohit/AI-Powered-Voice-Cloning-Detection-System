import { useState } from "react";
import { createAnalysisSession, uploadAnalysisAudio, type AnalysisSession } from "../api/analysis";
import { getAccessToken } from "../api/auth";
import "./AnalysisIntakeCard.css";

export function AnalysisIntakeCard() {
  const [file, setFile] = useState<File | null>(null);
  const [session, setSession] = useState<AnalysisSession | null>(null);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");

  const submit = async () => {
    const token = getAccessToken();
    if (!token) {
      setMessage("Your session has expired. Please sign in again.");
      return;
    }
    if (!file) {
      setMessage("Select an audio file first.");
      return;
    }

    setBusy(true);
    setMessage("");
    try {
      const created = await createAnalysisSession(token);
      const ready = await uploadAnalysisAudio(token, created.id, file);
      setSession(ready);
      setMessage("Audio accepted and the analysis session is ready for Phase 04.");
      setFile(null);
    } catch (error: unknown) {
      const detail = error instanceof Error ? error.message : "Audio upload failed.";
      setMessage(detail);
    } finally {
      setBusy(false);
    }
  };

  return (
    <section className="analysis-intake-card" id="upload" aria-labelledby="analysis-intake-title">
      <div className="analysis-intake-copy">
        <span className="eyebrow">Phase 03 · Audio Intake</span>
        <h2 id="analysis-intake-title">Start a voice analysis</h2>
        <p>Upload a supported audio sample. The file is validated and securely registered for the next processing phase.</p>
      </div>
      <div className="analysis-intake-controls">
        <label className="audio-file-input">
          <span>{file ? file.name : "Choose audio file"}</span>
          <input
            type="file"
            accept=".wav,.mp3,.ogg,.flac,.m4a,audio/*"
            onChange={(event) => setFile(event.target.files?.[0] ?? null)}
          />
        </label>
        <button type="button" className="analysis-upload-button" onClick={submit} disabled={busy || !file}>
          {busy ? "Validating…" : "Create session & upload"}
        </button>
      </div>
      {session?.audio_inputs[0] && (
        <div className="analysis-intake-result" role="status">
          <strong>Ready for processing</strong>
          <span>Session {session.id}</span>
          <span>{session.audio_inputs[0].detected_format.toUpperCase()} · {session.audio_inputs[0].size_bytes.toLocaleString()} bytes</span>
        </div>
      )}
      {message && <p className="analysis-intake-message" role="status">{message}</p>}
    </section>
  );
}
