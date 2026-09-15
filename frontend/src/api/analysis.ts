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
