// oxlint-disable react(set-state-in-effect), react-hooks(exhaustive-deps)
import { useEffect, useMemo, useState } from "react";
import { AnalysisIntakeCard } from "../components/AnalysisIntakeCard";
import { useAuth } from "../context/AuthContext";
import { getAccessToken } from "../api/auth";
import { getDashboardOverview, type DashboardOverview } from "../api/dashboard";
import "./DashboardPage.css";

type IconName = "dashboard" | "analysis" | "upload" | "alerts" | "reports" | "organization" | "settings" | "search" | "bell" | "chevron" | "shield" | "activity" | "risk" | "block" | "check" | "arrow" | "refresh";

const iconPaths: Record<IconName, string> = {
  dashboard: "M3 10.5 12 3l9 7.5M5.5 9v11h13V9M9 20v-6h6v6",
  analysis: "M4 12h2l2-5 4 10 2-5h6",
  upload: "M12 16V4m0 0-4 4m4-4 4 4M5 14v5h14v-5",
  alerts: "M18 9a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9M10 21h4",
  reports: "M6 3h9l3 3v15H6zM14 3v4h4M9 11h6M9 15h6",
  organization: "M4 21V6h10v15M14 10h6v11M7 9h4M7 13h4M7 17h4",
  settings: "M12 8.5a3.5 3.5 0 1 0 0 7 3.5 3.5 0 0 0 0-7Zm0-5v2M12 18.5v2M3.5 12h2M18.5 12h2M5.9 5.9l1.4 1.4M16.7 16.7l1.4 1.4M18.1 5.9l-1.4 1.4M7.3 16.7l-1.4-1.4",
  search: "m20 20-4.5-4.5M10.5 17a6.5 6.5 0 1 0 0-13 6.5 6.5 0 0 0 0 13Z",
  bell: "M18 9a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9M10 21h4",
  chevron: "m7 10 5 5 5-5",
  shield: "M12 3 20 6v6c0 5-3.5 8.5-8 10-4.5-1.5-8-5-8-10V6l8-3Z",
  activity: "M3 12h4l2-6 4 12 2-6h6",
  risk: "M12 3 3.5 19h17L12 3Zm0 5v5m0 3v.01",
  block: "M7 7l10 10M17 7 7 17M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18Z",
  check: "m5 12 4 4L19 6",
  arrow: "M5 12h13m-5-5 5 5-5 5",
  refresh: "M20 11a8 8 0 0 0-14.9-3M4 5v4h4M4 13a8 8 0 0 0 14.9 3M20 19v-4h-4",
};

function Icon({ name }: { name: IconName }) {
  return <svg className="dashboard-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d={iconPaths[name]} /></svg>;
}

function CountUp({ value, decimals = 0 }: { value: number; decimals?: number }) {
  const [display, setDisplay] = useState(0);
  useEffect(() => {
    let frame = 0;
    const duration = 700;
    const started = performance.now();
    const tick = (now: number) => {
      const progress = Math.min((now - started) / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      setDisplay(value * eased);
      if (progress < 1) frame = requestAnimationFrame(tick);
    };
    frame = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(frame);
  }, [value]);
  return <>{display.toFixed(decimals)}</>;
}

function formatRelativeTime(value: string): string {
  const diff = Math.max(0, Date.now() - new Date(value).getTime());
  const minutes = Math.floor(diff / 60000);
  if (minutes < 1) return "Just now";
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  return `${Math.floor(hours / 24)}d ago`;
}

function severityClass(value: string): string {
  return `severity-${value.toLowerCase()}`;
}

function riskClass(value: string | null): string {
  return value ? `risk-${value.toLowerCase()}` : "risk-neutral";
}

function TrendChart({ data }: { data: DashboardOverview["trend"] }) {
  const max = Math.max(1, ...data.map((point) => Math.max(point.calls, point.alerts, point.high_risk)));
  const width = 760;
  const height = 230;
  const padX = 20;
  const padY = 24;
  const step = data.length > 1 ? (width - padX * 2) / (data.length - 1) : 0;
  const y = (value: number) => height - padY - (value / max) * (height - padY * 2);
  const points = (key: "calls" | "alerts" | "high_risk") => data.map((point, index) => `${padX + index * step},${y(point[key])}`).join(" ");

  return (
    <div className="trend-chart" aria-label="Seven day activity trend">
      <svg viewBox={`0 0 ${width} ${height}`} role="img">
        <defs>
          <linearGradient id="trend-fill" x1="0" x2="0" y1="0" y2="1"><stop offset="0%" stopColor="#6ea8ff" stopOpacity=".18" /><stop offset="100%" stopColor="#6ea8ff" stopOpacity="0" /></linearGradient>
        </defs>
        {[0, 1, 2, 3].map((line) => {
          const lineY = padY + ((height - padY * 2) / 3) * line;
          return <line key={line} x1={padX} x2={width - padX} y1={lineY} y2={lineY} className="chart-grid" />;
        })}
        <polygon points={`${points("calls")} ${width - padX},${height - padY} ${padX},${height - padY}`} fill="url(#trend-fill)" />
        <polyline points={points("calls")} className="chart-line chart-calls" />
        <polyline points={points("alerts")} className="chart-line chart-alerts" />
        <polyline points={points("high_risk")} className="chart-line chart-risk" />
        {data.map((point, index) => <circle key={point.day} cx={padX + index * step} cy={y(point.calls)} r="4" className="chart-dot" />)}
      </svg>
      <div className="chart-labels">{data.map((point) => <span key={point.day}>{new Date(`${point.day}T00:00:00`).toLocaleDateString(undefined, { weekday: "short" })}</span>)}</div>
    </div>
  );
}

export function DashboardPage() {
  const { user, logout } = useAuth();
  const [overview, setOverview] = useState<DashboardOverview | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const displayName = user?.full_name ?? user?.email ?? "Analyst";
  const initials = displayName.split(/\s+/).filter(Boolean).slice(0, 2).map((part) => part[0]?.toUpperCase()).join("") || "VG";

  const loadOverview = async (silent = false) => {
    const token = getAccessToken();
    if (!token) return;
    if (silent) setRefreshing(true); else setLoading(true);
    try {
      const data = await getDashboardOverview(token);
      setOverview(data);
      setError(null);
    } catch {
      setError("Dashboard data could not be refreshed. Your account is still signed in.");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    void loadOverview();
    const timer = window.setInterval(() => void loadOverview(true), 30000);
    return () => window.clearInterval(timer);
  }, []);

  const totalRisk = useMemo(() => overview?.risk_distribution.reduce((sum, item) => sum + item.count, 0) ?? 0, [overview]);
  const metric = (key: string) => overview?.metrics[key]?.value ?? 0;

  return (
    <div className="dashboard-shell">
      <aside className="dashboard-sidebar">
        <div className="sidebar-brand"><div className="brand-mark"><Icon name="shield" /></div><div><strong>VoiceGuard</strong><small>Security Console</small></div></div>
        <nav className="sidebar-nav" aria-label="Primary navigation">
          <div className="sidebar-section-label">Workspace</div>
          <a className="sidebar-link active" href="#dashboard"><Icon name="dashboard" /> <span>Overview</span></a>
          <a className="sidebar-link" href="#analysis"><Icon name="analysis" /> <span>Analysis</span></a>
          <a className="sidebar-link" href="#upload"><Icon name="upload" /> <span>Audio Intake</span></a>
          <a className="sidebar-link" href="#alerts"><Icon name="alerts" /> <span>Alerts</span>{overview && <b className="nav-count">{overview.active_alert_count}</b>}</a>
          <a className="sidebar-link" href="#reports"><Icon name="reports" /> <span>Reports</span></a>
          <div className="sidebar-section-label">Administration</div>
          <a className="sidebar-link" href="#organization"><Icon name="organization" /> <span>Organization</span></a>
          <a className="sidebar-link" href="#settings"><Icon name="settings" /> <span>Settings</span></a>
        </nav>
        <div className="sidebar-footer"><span className="online-pulse" /><div><strong>Detection engine online</strong><small>AASIST · balanced-v1</small></div></div>
      </aside>

      <div className="dashboard-content">
        <header className="dashboard-topbar">
          <div className="search-box"><Icon name="search" /><span>Search calls, alerts, sessions...</span><kbd>⌘ K</kbd></div>
          <div className="topbar-actions">
            <button className={`refresh-button ${refreshing ? "is-refreshing" : ""}`} type="button" onClick={() => void loadOverview(true)} aria-label="Refresh dashboard"><Icon name="refresh" /></button>
            <button className="icon-button" type="button" aria-label="Notifications"><Icon name="bell" /><span className="notification-dot" /></button>
            <button className="profile-chip" type="button" aria-label="Account menu"><span className="avatar">{initials}</span><span className="profile-copy"><strong>{displayName}</strong><small>{user?.role ?? "Analyst"}</small></span><Icon name="chevron" /></button>
            <button id="logout-btn" className="logout-btn" onClick={() => void logout()}>Sign out</button>
          </div>
        </header>

        <main className="dashboard-main" id="dashboard">
          <section className="hero-strip">
            <div className="hero-copy"><div className="live-label"><span className="live-dot" /> Live security overview</div><h1>Good evening, {displayName.split(" ")[0]}.</h1><p>Here’s what your voice security environment looks like right now.</p><div className="hero-meta"><span><Icon name="organization" /> {overview?.organization_name ?? "Your organization"}</span><span><Icon name="check" /> Policy engine active</span></div></div>
            <div className="hero-orbit" aria-hidden="true"><div className="orbit orbit-a" /><div className="orbit orbit-b" /><div className="orbit-core"><Icon name="shield" /></div><span className="orbit-node node-one" /><span className="orbit-node node-two" /><span className="orbit-node node-three" /></div>
          </section>

          {error && <div className="dashboard-error" role="status"><Icon name="risk" /> {error}</div>}

          {loading && !overview ? <section className="skeleton-grid" aria-label="Loading dashboard"><span /><span /><span /><span /></section> : (
            <>
              <section className="metric-grid" aria-label="Security metrics">
                <article className="metric-card metric-blue"><div className="metric-top"><span className="metric-icon"><Icon name="activity" /></span><span className="metric-trend">{overview?.metrics.calls?.delta_percent !== null && overview?.metrics.calls?.delta_percent !== undefined ? `${overview.metrics.calls.delta_percent >= 0 ? "+" : ""}${overview.metrics.calls.delta_percent}%` : "—"}</span></div><strong><CountUp value={Number(metric("calls"))} /></strong><span className="metric-name">Analysis sessions</span><small>{overview?.metrics.calls?.caption}</small></article>
                <article className="metric-card metric-violet"><div className="metric-top"><span className="metric-icon"><Icon name="analysis" /></span><span className="metric-badge">Completed</span></div><strong><CountUp value={Number(metric("analyses"))} /></strong><span className="metric-name">Detector runs</span><small>{overview?.metrics.analyses?.caption}</small></article>
                <article className="metric-card metric-amber"><div className="metric-top"><span className="metric-icon"><Icon name="risk" /></span><span className="metric-badge">Deterministic</span></div><strong><CountUp value={Number(metric("average_risk"))} decimals={1} /></strong><span className="metric-name">Average risk score</span><small>{overview?.metrics.average_risk?.caption}</small></article>
                <article className={`metric-card metric-${overview?.critical_alert_count ? "rose" : "green"}`}><div className="metric-top"><span className="metric-icon"><Icon name="alerts" /></span><span className="metric-badge">{overview?.critical_alert_count ? `${overview.critical_alert_count} critical` : "No critical"}</span></div><strong><CountUp value={Number(metric("active_alerts"))} /></strong><span className="metric-name">Active alerts</span><small>{overview?.metrics.active_alerts?.caption}</small></article>
              </section>

              <section className="dashboard-grid-main">
                <article className="panel trend-panel" id="analysis"><div className="panel-heading"><div><span className="panel-kicker">Security activity</span><h2>Detection activity</h2></div><div className="chart-legend"><span><i className="legend-call" /> Sessions</span><span><i className="legend-alert" /> Alerts</span><span><i className="legend-risk" /> High risk</span></div></div><TrendChart data={overview?.trend ?? []} /><div className="trend-foot"><span><b>{overview?.active_alert_count ?? 0}</b> active alerts</span><span><b>{overview?.blocked_action_count ?? 0}</b> blocked policy actions</span><span>Updated {overview ? formatRelativeTime(overview.generated_at) : "—"}</span></div></article>

                <article className="panel risk-panel"><div className="panel-heading"><div><span className="panel-kicker">Risk posture</span><h2>Risk distribution</h2></div><span className="panel-total">{totalRisk} scored</span></div><div className="risk-list">{(overview?.risk_distribution ?? []).map((item) => <div className="risk-row" key={item.level}><div className="risk-row-head"><span className={`risk-pill ${riskClass(item.level)}`}>{item.level}</span><strong>{item.count}</strong></div><div className="risk-bar"><span className={`risk-fill ${riskClass(item.level)}`} style={{ width: `${item.percentage}%` }} /></div><small>{item.percentage.toFixed(1)}% of scored calls</small></div>)}</div></article>
              </section>

              <section className="dashboard-grid-secondary">
                <article className="panel alerts-panel" id="alerts"><div className="panel-heading"><div><span className="panel-kicker">Response queue</span><h2>Recent alerts</h2></div><span className="live-label compact"><span className="live-dot" /> {overview?.active_alert_count ?? 0} active</span></div>{overview?.recent_alerts.length ? <div className="alert-list">{overview.recent_alerts.map((alert) => <div className="alert-row" key={alert.id}><span className={`severity-marker ${severityClass(alert.severity)}`} /><div className="alert-copy"><strong>{alert.title}</strong><span>{formatRelativeTime(alert.created_at)} · {alert.status.replace("_", " ").toLowerCase()}</span></div>{alert.risk_score !== null && <span className={`score-chip ${severityClass(alert.severity)}`}>{alert.risk_score.toFixed(1)}</span>}<Icon name="arrow" /></div>)}</div> : <div className="empty-state"><span className="empty-icon"><Icon name="check" /></span><strong>No active alert activity</strong><p>The response queue is clear for this organization.</p></div>}</article>

                <article className="panel analysis-panel"><div className="panel-heading"><div><span className="panel-kicker">Detector feed</span><h2>Latest analyses</h2></div><span className="model-chip">AASIST</span></div><div className="analysis-list">{(overview?.recent_analyses ?? []).map((item) => <div className="analysis-row" key={item.id}><span className={`analysis-status ${riskClass(item.risk_level)}`}><Icon name={item.risk_level === "CRITICAL" || item.risk_level === "HIGH" ? "risk" : "check"} /></span><div className="analysis-copy"><strong>{item.risk_level ?? item.detection_status}</strong><span>{item.model_version ?? item.model_name} · {formatRelativeTime(item.analyzed_at)}</span></div><div className="analysis-values"><strong>{item.risk_score !== null ? item.risk_score.toFixed(1) : "—"}</strong><small>risk</small></div></div>)}</div></article>
              </section>

              <AnalysisIntakeCard />

              <section className="workflow-panel" id="reports"><div><span className="panel-kicker">Decision pipeline</span><h2>Detection → decision → response</h2><p>Every security outcome remains traceable through the deterministic risk, policy and alert layers.</p></div><div className="workflow-steps"><span><i>01</i> Audio</span><b>→</b><span><i>02</i> Detection</span><b>→</b><span><i>03</i> Risk</span><b>→</b><span><i>04</i> Policy</span><b>→</b><span className="workflow-current"><i>05</i> Alert</span></div></section>
            </>
          )}
        </main>
      </div>
    </div>
  );
}
