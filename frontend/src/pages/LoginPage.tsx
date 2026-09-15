import { type FormEvent, useState } from "react";
import { Link, useNavigate, useLocation } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { AuthLayout } from "../components/AuthLayout";

export function LoginPage() {
  const { login, isLoading } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const [email, setEmail]           = useState("");
  const [password, setPassword]     = useState("");
  const [showPass, setShowPass]     = useState(false);
  const [errorMsg, setErrorMsg]     = useState<string | null>(null);

  const from = (location.state as { from?: { pathname: string } })?.from?.pathname ?? "/dashboard";

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setErrorMsg(null);
    try {
      await login(email, password);
      navigate(from, { replace: true });
    } catch {
      setErrorMsg("Invalid email or password. Please check your credentials.");
      setPassword("");
    }
  }

  return (
    <AuthLayout title="Welcome back" subtitle="Sign in to your VoiceGuard account.">
      <form onSubmit={handleSubmit} noValidate style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>

        <div className="form-field">
          <label htmlFor="login-email" className="form-label">Email address</label>
          <input
            id="login-email"
            type="email"
            className="form-input"
            value={email}
            onChange={e => setEmail(e.target.value)}
            autoComplete="email"
            required
            placeholder="you@company.com"
          />
        </div>

        <div className="form-field">
          <label htmlFor="login-password" className="form-label">Password</label>
          <div className="input-wrapper">
            <input
              id="login-password"
              type={showPass ? "text" : "password"}
              className="form-input"
              value={password}
              onChange={e => setPassword(e.target.value)}
              autoComplete="current-password"
              required
              placeholder="Enter your password"
            />
            <button
              type="button"
              className="input-icon-right"
              onClick={() => setShowPass(s => !s)}
              aria-label={showPass ? "Hide password" : "Show password"}
            >
              {showPass ? "Hide" : "Show"}
            </button>
          </div>
        </div>

        {errorMsg && (
          <div className="form-error-msg" role="alert">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" style={{ flexShrink: 0 }}>
              <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>
            </svg>
            {errorMsg}
          </div>
        )}

        <button
          id="login-submit-btn"
          type="submit"
          className="btn btn-primary"
          style={{ width: '100%', marginTop: '.375rem' }}
          disabled={isLoading}
        >
          {isLoading ? "Signing in…" : "Sign in"}
        </button>

        <div className="divider">or</div>

        <p style={{ textAlign: 'center', fontSize: '.875rem', color: 'var(--text-muted)' }}>
          Don't have an account?{' '}
          <Link to="/register" style={{ color: 'var(--brand-600)', fontWeight: 600 }}>
            Create one
          </Link>
        </p>
      </form>
    </AuthLayout>
  );
}
