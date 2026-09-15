/**
 * Dashboard stub — Phase 02 scope only.
 * Presents the authenticated identity in the shared Voice Guard light SaaS design.
 */
import { useAuth } from "../context/AuthContext";
import "./DashboardPage.css";

type IconName = "dashboard" | "analysis" | "upload" | "reports" | "organization" | "settings" | "search" | "bell" | "chevron" | "building" | "status" | "clock" | "check";

function Icon({ name }: { name: IconName }) {
  const paths: Record<IconName, string> = {
    dashboard: "M3 10.5 12 3l9 7.5M5.5 9v11h13V9M9 20v-6h6v6",
    analysis: "M4 12h2l2-5 4 10 2-5h6",
    upload: "M12 16V4m0 0-4 4m4-4 4 4M5 14v5h14v-5",
    reports: "M6 3h9l3 3v15H6zM14 3v4h4M9 11h6M9 15h6",
    organization: "M4 21V6h10v15M14 10h6v11M7 9h4M7 13h4M7 17h4M17 14h1M17 18h1",
    settings: "M12 8.5a3.5 3.5 0 1 0 0 7 3.5 3.5 0 0 0 0-7Zm0-5v2M12 18.5v2M3.5 12h2M18.5 12h2M5.9 5.9l1.4 1.4M16.7 16.7l1.4 1.4M18.1 5.9l-1.4 1.4M7.3 16.7l-1.4 1.4",
    search: "m20 20-4.5-4.5M10.5 17a6.5 6.5 0 1 0 0-13 6.5 6.5 0 0 0 0 13Z",
    bell: "M18 9a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9M10 21h4",
    chevron: "m7 10 5 5 5-5",
    building: "M5 21V5h10v16M15 10h4v11M8 8h4M8 12h4M8 16h4",
    status: "M12 7v5l3 2M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18Z",
    clock: "M12 7v5l3 2M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18Z",
    check: "m6 12 4 4 8-9",
  };

  return (
    <svg className="dashboard-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d={paths[name]} />
    </svg>
  );
}

export function DashboardPage() {
  const { user, logout } = useAuth();
  const displayName = user?.full_name ?? user?.email ?? "User";
  const initials = displayName
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase())
    .join("") || "VG";

  return (
    <div className="dashboard-shell">
      <aside className="dashboard-sidebar">
        <div className="sidebar-brand">
          <div className="brand-mark" aria-hidden="true">✓</div>
          <span>Voice Guard</span>
        </div>

        <nav className="sidebar-nav" aria-label="Primary navigation">
          <div className="sidebar-section-label">Workspace</div>
          <a className="sidebar-link active" href="#dashboard" aria-current="page"><Icon name="dashboard" /> Dashboard</a>
          <a className="sidebar-link" href="#analysis"><Icon name="analysis" /> Analysis</a>
          <a className="sidebar-link" href="#upload"><Icon name="upload" /> Upload</a>
          <a className="sidebar-link" href="#reports"><Icon name="reports" /> Reports</a>
          <div className="sidebar-section-label">Administration</div>
          <a className="sidebar-link" href="#organization"><Icon name="organization" /> Organization</a>
          <a className="sidebar-link" href="#settings"><Icon name="settings" /> Settings</a>
        </nav>

        <div className="phase-card">
          <div className="phase-dot" />
          <div>
            <strong>Phase 02</strong>
            <span>Authentication Foundation</span>
            <small>v0.1.0</small>
          </div>
        </div>
      </aside>

      <div className="dashboard-content">
        <header className="dashboard-topbar">
          <div className="search-box">
            <Icon name="search" />
            <span>Search anything...</span>
          </div>
          <div className="topbar-actions">
            <button className="icon-button" type="button" aria-label="Notifications"><Icon name="bell" /><span className="notification-dot" /></button>
            <button className="profile-chip" type="button" aria-label="Account menu">
              <span className="avatar">{initials}</span>
              <span className="profile-copy"><strong>{displayName}</strong><small>{user?.role ?? "User"}</small></span>
              <Icon name="chevron" />
            </button>
            <button id="logout-btn" className="logout-btn" onClick={logout}>Sign out</button>
          </div>
        </header>

        <main className="dashboard-main" id="dashboard">
          <section className="welcome-card">
            <div className="welcome-copy">
              <span className="eyebrow">Voice Guard workspace</span>
              <h1>Welcome back,</h1>
              <p>{user?.email}</p>
              <span className="role-badge">{user?.role}</span>
            </div>
            <div className="welcome-visual" aria-hidden="true">
              <span className="wave wave-one" /><span className="wave wave-two" /><span className="wave wave-three" />
              <div className="shield-mark">✓</div>
            </div>
          </section>

          <section className="info-grid" aria-label="Account overview">
            <div className="info-item">
              <div className="info-icon blue"><Icon name="building" /></div>
              <div><span className="info-label">Organization</span><span className="info-value">{user?.organization_id}</span></div>
            </div>
            <div className="info-item">
              <div className="info-icon green"><Icon name="status" /></div>
              <div><span className="info-label">Account Status</span><span className="info-value status-active">Active</span></div>
            </div>
            <div className="info-item">
              <div className="info-icon purple"><Icon name="clock" /></div>
              <div><span className="info-label">Last Login</span><span className="info-value">{user?.last_login_at ? new Date(user.last_login_at).toLocaleString() : "First login"}</span></div>
            </div>
          </section>

          <section className="phase-notice">
            <div className="notice-icon"><Icon name="check" /></div>
            <div>
              <h2>Phase 02 — Authentication Foundation</h2>
              <p>Full analysis dashboard is implemented in Phase 04+. Authentication, RBAC, and tenant isolation are fully operational.</p>
            </div>
          </section>
        </main>
      </div>
    </div>
  );
}
