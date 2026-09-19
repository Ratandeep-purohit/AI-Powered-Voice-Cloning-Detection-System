import { getAccessToken } from "./auth";

export interface RealtimeEvent {
  event_id?: string;
  event_type: string;
  organization_id: string;
  session_id?: string | null;
  occurred_at?: string;
  payload: Record<string, unknown>;
}

export function createRealtimeSocket(
  onEvent: (event: RealtimeEvent) => void,
  onStateChange: (connected: boolean) => void,
): () => void {
  const token = getAccessToken();
  if (!token) return () => undefined;

  const apiBase = import.meta.env.VITE_API_BASE_URL ?? "/api/v1";
  const backendUrl = new URL(apiBase, window.location.origin);
  const protocol = backendUrl.protocol === "https:" ? "wss:" : "ws:";
  const url = `${protocol}//${backendUrl.host}${backendUrl.pathname.replace(/\/$/, "")}/realtime/ws?token=${encodeURIComponent(token)}`;
  const socket = new WebSocket(url);

  socket.onopen = () => onStateChange(true);
  socket.onmessage = (message) => {
    try {
      onEvent(JSON.parse(message.data) as RealtimeEvent);
    } catch {
      // Ignore malformed events without breaking the live connection.
    }
  };
  socket.onclose = () => onStateChange(false);
  socket.onerror = () => onStateChange(false);

  return () => socket.close();
}
