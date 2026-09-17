import { useEffect, useState } from "react";
import { getAccessToken } from "../api/auth";
import { createRealtimeSocket, type RealtimeEvent } from "../api/realtime";
import "./RealtimeStatus.css";

type Props = { onEvent?: (event: RealtimeEvent) => void };

export function RealtimeStatus({ onEvent }: Props) {
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    if (!getAccessToken()) return undefined;
    const cleanup = createRealtimeSocket((event) => {
      onEvent?.(event);
      window.dispatchEvent(new CustomEvent("voiceguard:realtime", { detail: event }));
    }, setConnected);
    return cleanup;
  }, [onEvent]);

  return (
    <span className={`realtime-status ${connected ? "connected" : "offline"}`} title={connected ? "Live security events connected" : "Live security events offline"}>
      <i />
      {connected ? "Live" : "Offline"}
    </span>
  );
}
