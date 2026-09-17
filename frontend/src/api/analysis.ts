import axios from "axios";

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "/api/v1";

export type AnalysisSession = {
  id: string;
  organization_id: string;
  initiated_by_user_id: string | null;
  source_type: string;
  status: string;
  external_reference: string | null;
  caller_identifier: string | null;
  created_at: string;
  updated_at: string;
  audio_inputs: AudioInput[];
};

export type AudioInput = {
  id: string;
  original_filename: string | null;
  content_type: string;
  detected_format: string;
  size_bytes: number;
  sha256: string;
  intake_status: string;
  rejection_reason: string | null;
  created_at: string;
  validated_at: string | null;
};

export type AnalysisPipelineResult = {
  session_id: string;
  audio_input_id: string;
  processing: {
    id: string;
    audio_input_id: string;
    status: string;
    processed_sample_rate: number | null;
    processed_channels: number | null;
    processed_duration_ms: number | null;
    processed_size_bytes: number | null;
    processed_sha256: string | null;
    normalization_applied: boolean;
    started_at: string | null;
    completed_at: string | null;
  };
  detection: {
    id: string;
    call_id: string;
    audio_segment_id: string | null;
    model_name: string;
    model_version: string | null;
    detection_status: string;
    synthetic_score: number | null;
    synthetic_probability: number | null;
    authentic_probability: number | null;
    confidence: number | null;
    processing_time_ms: number | null;
    analyzed_at: string;
    created_at: string;
  };
  decision: string;
  detector_threshold: number;
  risk: {
    id: string;
    call_id: string;
    voice_analysis_id: string;
    risk_score: number;
    risk_level: string;
    risk_factors: Record<string, unknown>;
    policy_version: string;
    calculated_at: string;
    created_at: string;
  };
  prevention: {
    id: string;
    organization_id: string;
    call_id: string;
    risk_score_id: string;
    risk_score: number;
    risk_level: string;
    response_action: string;
    policy_version: string;
    reason: string;
    created_at: string;
  };
  alert: {
    id: string;
    organization_id: string;
    call_id: string | null;
    risk_score_id: string | null;
    alert_type: string;
    severity: string;
    status: string;
    title: string;
    description: string | null;
    resolved_at: string | null;
    resolved_by_user_id: string | null;
    created_at: string;
  } | null;
  completed_at: string;
};

export async function createAnalysisSession(
  accessToken: string,
  payload: { external_reference?: string; caller_identifier?: string } = {},
): Promise<AnalysisSession> {
  const response = await axios.post<AnalysisSession>(`${API_BASE}/calls`, payload, {
    headers: { Authorization: `Bearer ${accessToken}` },
  });
  return response.data;
}

export async function uploadAnalysisAudio(
  accessToken: string,
  sessionId: string,
  file: File,
): Promise<AnalysisSession> {
  const formData = new FormData();
  formData.append("file", file);
  const response = await axios.post<AnalysisSession>(
    `${API_BASE}/calls/${sessionId}/audio`,
    formData,
    { headers: { Authorization: `Bearer ${accessToken}` } },
  );
  return response.data;
}

export async function runAnalysisPipeline(
  accessToken: string,
  sessionId: string,
  audioInputId: string,
): Promise<AnalysisPipelineResult> {
  const response = await axios.post<AnalysisPipelineResult>(
    `${API_BASE}/calls/${sessionId}/audio/${audioInputId}/analyze`,
    undefined,
    { headers: { Authorization: `Bearer ${accessToken}` } },
  );
  return response.data;
}

export async function runRealtimeAnalysisPipeline(
  accessToken: string,
  sessionId: string,
  audioInputId: string,
): Promise<AnalysisPipelineResult> {
  const response = await axios.post<AnalysisPipelineResult>(
    `${API_BASE}/calls/${sessionId}/audio/${audioInputId}/analyze-realtime`,
    undefined,
    { headers: { Authorization: `Bearer ${accessToken}` } },
  );
  return response.data;
}
