import axios from "axios";

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "/api/v1";

export type DashboardMetric = {
  value: number;
  delta_percent: number | null;
  caption: string;
};

export type DashboardOverview = {
  organization_id: string;
  organization_name: string;
  generated_at: string;
  metrics: Record<string, DashboardMetric>;
  trend: { day: string; calls: number; alerts: number; high_risk: number }[];
  risk_distribution: { level: string; count: number; percentage: number }[];
  recent_alerts: {
    id: string;
    title: string;
    severity: string;
    status: string;
    risk_score: number | null;
    created_at: string;
    call_id: string | null;
  }[];
  recent_analyses: {
    id: string;
    call_id: string;
    model_name: string;
    model_version: string | null;
    detection_status: string;
    synthetic_probability: number | null;
    authentic_probability: number | null;
    confidence: number | null;
    risk_score: number | null;
    risk_level: string | null;
    analyzed_at: string;
  }[];
  active_alert_count: number;
  critical_alert_count: number;
  blocked_action_count: number;
};

export async function getDashboardOverview(accessToken: string): Promise<DashboardOverview> {
  const response = await axios.get<DashboardOverview>(`${API_BASE}/dashboard/overview`, {
    headers: { Authorization: `Bearer ${accessToken}` },
  });
  return response.data;
}
