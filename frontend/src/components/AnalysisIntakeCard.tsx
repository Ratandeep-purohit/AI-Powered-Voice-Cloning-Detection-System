import axios from "axios";
import { useEffect, useRef, useState } from "react";
import { createAnalysisSession, runRealtimeAnalysisPipeline, uploadAnalysisAudio, type AnalysisPipelineResult } from "../api/analysis";
import { getAccessToken } from "../api/auth";
import type { RealtimeEvent } from "../api/realtime";
import "./AnalysisIntakeCard.css";

type Stage = "idle" | "upload" | "processing" | "detecting" | "risk" | "prevention" | "alert" | "complete" | "error";

const stages: Exclude<Stage, "idle" | "error" | "complete">[] = ["upload", "processing", "detecting", "risk", "prevention", "alert"];
const stageMeta: Record<(typeof stages)[number], [string, string]> = {
  upload: ["Audio intake", "Validating and securely registering the recording"],
  processing: ["Audio processing", "Standardizing audio for the detector"],
  detecting: ["AI detection", "Running the trained AASIST-family detector"],
  risk: ["Risk scoring", "Calculating the deterministic security risk"],
  prevention: ["Prevention policy", "Evaluating the response policy"],
  alert: ["Alert engine", "Finalizing the security response"],
};

function percentForStage(stage: Stage) {
  if (stage === "complete") return 100;
  const index = stages.indexOf(stage as (typeof stages)[number]);
  return index < 0 ? 0 : Math.round(8 + (index / (stages.length - 1)) * 84);
}

function formatDuration(ms: number | null | undefined) {
  if (!ms) return "—";
  return `${(ms / 1000).toFixed(2)}s`;
}

function riskTone(level: string) {
  return `risk-${level.toLowerCase()}`;
}

function errorDetail(error: unknown) {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail;
    if (typeof detail === "string") return detail;
  }
  return error instanceof Error ? error.message : "The analysis pipeline failed.";
}

function stageFromRealtimeEvent(eventType: string): Stage | null {
  const map: Record<string, Stage> = {
    "analysis.started": "processing",
    "analysis.processing_completed": "detecting",
    "analysis.detection_completed": "risk",
    "analysis.risk_scored": "prevention",
    "analysis.prevention_decided": "alert",
    "alert.created": "alert",
  };
  return map[eventType] ?? null;
}

export function AnalysisIntakeCard() {
  const [file, setFile] = useState<File | null>(null);
  const [stage, setStage] = useState<Stage>("idle");
  const [result, setResult] = useState<AnalysisPipelineResult | null>(null);
  const [error, setError] = useState("");
  const stageRef = useRef<Stage>("idle");
  const sessionRef = useRef<string | null>(null);

  useEffect(() => {
    stageRef.current = stage;
  }, [stage]);

  useEffect(() => {
    const handleRealtime = (event: Event) => {
      const detail = (event as CustomEvent<RealtimeEvent>).detail;
      if (!detail?.session_id || detail.session_id !== sessionRef.current) return;
      const nextStage = stageFromRealtimeEvent(detail.event_type);
      if (nextStage && stageRef.current !== "complete" && stageRef.current !== "error") setStage(nextStage);
      if (detail.event_type === "analysis.failed") {
        const reason = detail.payload?.reason;
        setError(typeof reason === "string" ? reason : "The analysis pipeline failed.");
        setStage("error");
      }
    };
    window.addEventListener("voiceguard:realtime", handleRealtime);
    return () => window.removeEventListener("voiceguard:realtime", handleRealtime);
  }, []);

  const submit = async () => {
    const token = getAccessToken();
    if (!token) {
      setError("Your session has expired. Please sign in again.");
      setStage("error");
      return;
    }
    if (!file) return;

    setResult(null);
    setError("");
    setStage("upload");
    sessionRef.current = null;

    try {
      const created = await createAnalysisSession(token);
      sessionRef.current = created.id;
      const ready = await uploadAnalysisAudio(token, created.id, file);
      const audio = ready.audio_inputs[0];
      if (!audio) throw new Error("Audio registration completed without an audio input.");

      setStage("processing");
      const pipeline = await runRealtimeAnalysisPipeline(token, ready.id, audio.id);
      setResult(pipeline);
      setStage("complete");
      setFile(null);
    } catch (caught: unknown) {
      setError(errorDetail(caught));
      setStage("error");
    }
  };

  const busy = stages.includes(stage as (typeof stages)[number]);
  const progress = percentForStage(stage);
  const currentIndex = stages.indexOf(stage as (typeof stages)[number]);

  return (
    <section className={`analysis-intake-card ${busy ? "is-running" : ""}`} aria-labelledby="analysis-intake-title">
      <div className="analysis-intake-copy">
        <span className="eyebrow">Protected analysis pipeline</span>
        <h2 id="analysis-intake-title">Analyze a voice recording</h2>
        <p>One upload runs through audio processing, AI detection, risk scoring, prevention policy and security alerting.</p>
      </div>

      {!busy && stage !== "complete" && (
        <div className="analysis-intake-controls">
          <label className="audio-file-input">
            <span>{file ? file.name : "Choose audio file"}</span>
            <input type="file" accept=".wav,.mp3,.ogg,.flac,.m4a" onChange={(event) => setFile(event.target.files?.[0] ?? null)} />
          </label>
          <button type="button" className="analysis-upload-button" onClick={() => void submit()} disabled={!file}>
            Run full analysis <span>→</span>
          </button>
        </div>
      )}

      {busy && (
        <div className="pipeline-run" aria-live="polite">
          <div className="pipeline-run-top"><div><strong>{stageMeta[stage as (typeof stages)[number]]?.[0]}</strong><span>{stageMeta[stage as (typeof stages)[number]]?.[1]}</span></div><b>{progress}%</b></div>
          <div className="pipeline-progress"><i style={{ width: `${progress}%` }} /></div>
          <div className="pipeline-steps">
            {stages.map((key, index) => {
              const state = index < currentIndex ? "done" : index === currentIndex ? "current" : "waiting";
              return <div className={`pipeline-step ${state}`} key={key}><span>{state === "done" ? "✓" : index + 1}</span><div><strong>{stageMeta[key][0]}</strong><small>{state === "current" ? stageMeta[key][1] : state === "done" ? "Completed" : "Waiting"}</small></div></div>;
            })}
          </div>
        </div>
      )}

      {stage === "error" && <div className="analysis-error" role="alert"><strong>Analysis failed</strong><span>{error}</span><button type="button" onClick={() => { setStage("idle"); setError(""); sessionRef.current = null; }}>Try again</button></div>}

      {stage === "complete" && result && (
        <div className="analysis-result" role="status">
          <div className="result-banner"><div><span className="success-mark">✓</span><div><strong>Analysis complete</strong><span>Session {result.session_id}</span></div></div><span className={`decision-pill ${result.decision.toLowerCase()}`}>{result.decision}</span></div>
          <div className="result-grid">
            <article><span>Detector verdict</span><strong>{result.decision === "SPOOF" ? "Synthetic voice" : "Authentic voice"}</strong><small>{((result.detection.synthetic_probability ?? 0) * 100).toFixed(1)}% synthetic probability · {((result.detection.confidence ?? 0) * 100).toFixed(1)}% confidence</small></article>
            <article className={riskTone(result.risk.risk_level)}><span>Risk score</span><strong>{result.risk.risk_score.toFixed(1)} <small>/ 100</small></strong><small>{result.risk.risk_level} risk</small></article>
            <article><span>Policy response</span><strong>{result.prevention.response_action.replaceAll("_", " ")}</strong><small>{result.prevention.reason}</small></article>
            <article><span>Model</span><strong>{result.detection.model_version ?? "AASIST"}</strong><small>Inference {formatDuration(result.detection.processing_time_ms)} · {result.processing.processed_sample_rate ?? 16000}Hz mono</small></article>
          </div>
          {result.alert && <div className="result-alert"><span>●</span><div><strong>{result.alert.title}</strong><small>{result.alert.description ?? "Security alert generated from the detected risk."}</small></div><b>{result.alert.severity}</b></div>}
          <button type="button" className="new-analysis-button" onClick={() => { setStage("idle"); setResult(null); sessionRef.current = null; }}>Analyze another recording</button>
        </div>
      )}
    </section>
  );
}
