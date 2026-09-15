/**
 * Dashboard stub — Phase 02 scope only.
 * Shows authenticated user profile. Full dashboard is Phase 04+ scope.
 */
import { useAuth } from "../context/AuthContext";
import "./DashboardPage.css";

export function DashboardPage() {
  const { user, logout } = useAuth();

  return (
    <div className="dashboard-container">
      <header className="dashboard-header">
        <div className="dashboard-brand">
          <span className="brand-icon">🔒</span>
          <span className="brand-name">Voice Guard</span>
        </div>
        <button id="logout-btn" className="logout-btn" onClick={logout}>
          Sign out
        </button>
      </header>

      <main className="dashboard-main">
        <div className="welcome-card">
          <h2 className="welcome-title">Welcome back</h2>
          <p className="welcome-email">{user?.full_name ?? user?.email}</p>
          <span className="role-badge">{user?.role}</span>
        </div>

        <div className="info-grid">
          <div className="info-item">
            <span className="info-label">Organization</span>
            <span className="info-value">{user?.organization_id}</span>
          </div>
          <div className="info-item">
            <span className="info-label">Account Status</span>
            <span className="info-value status-active">Active</span>
          </div>
          <div className="info-item">
            <span className="info-label">Last Login</span>
            <span className="info-value">
              {user?.last_login_at
                ? new Date(user.last_login_at).toLocaleString()
                : "First login"}
            </span>
          </div>
        </div>

        <div className="phase-notice">
          <p>
            🚧 <strong>Phase 02 — Authentication Foundation</strong><br />
            Full analysis dashboard is implemented in Phase 04+.
            Authentication, RBAC, and tenant isolation are fully operational.
          </p>
        </div>
      </main>
    </div>
  );
}
