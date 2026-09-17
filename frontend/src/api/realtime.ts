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
  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  const host = window.location.host;
  const path = `${apiBase}/realtime/ws`;
  const url = `${protocol}//${host}${path}?token=${encodeURIComponent(token)}`;
  const socket = new WebSocket(url);
  let retryTimer: number | undefined;
  let closed = false;

  socket.onopen = () => onStateChange(true);
  socket.onmessage = (message) => {
    try {
      onEvent(JSON.parse(message.data) as RealtimeEvent);
    } catch {
      // Ignore malformed events without breaking the live connection.
    }
  };
  socket.onclose = () => {
    onStateChange(false);
    if (!closed) retryTimer = window.setTimeout(() => createRealtimeSocket(onEvent, onStateChange), 5000);
  };
  socket.onerror = () => onStateChange(false);

  return () => {
    closed = true;
    if (retryTimer) window.clearTimeout(retryTimer);
    socket.close();
  };
}
