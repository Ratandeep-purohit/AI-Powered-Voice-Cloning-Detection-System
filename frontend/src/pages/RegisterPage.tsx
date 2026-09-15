import { type FormEvent, useMemo, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { apiRegister, setAccessToken } from "../api/auth";
import { AuthLayout } from "../components/AuthLayout";

const STRENGTH_LABELS = ["", "Weak", "Fair", "Good", "Strong"];
const STRENGTH_COLORS = ["", "#ef4444", "#f97316", "#16a34a", "#059669"];

function calcStrength(p: string): number {
  let s = 0;
  if (p.length > 7)  s++;
  if (p.length > 12) s++;
  if (/[A-Z]/.test(p)) s++;
  if (/[0-9]/.test(p)) s++;
  if (/[^a-zA-Z0-9]/.test(p)) s++;
  return Math.min(Math.ceil(s * 4 / 5), 4); // normalize to 1–4
}

export function RegisterPage() {
  const { login } = useAuth();
  const navigate = useNavigate();

  const [orgName,         setOrgName]         = useState("");
  const [email,           setEmail]           = useState("");
  const [password,        setPassword]        = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPass,        setShowPass]        = useState(false);
  const [errorMsg,        setErrorMsg]        = useState<string | null>(null);
  const [isLoading,       setIsLoading]       = useState(false);

  const strength = useMemo(() => (password ? calcStrength(password) : 0), [password]);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setErrorMsg(null);

    if (!orgName.trim()) { setErrorMsg("Organization name is required."); return; }
    if (password.length < 8) { setErrorMsg("Password must be at least 8 characters."); return; }
    if (password !== confirmPassword) { setErrorMsg("Passwords do not match."); return; }

    setIsLoading(true);
    try {
      const slug = orgName.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/(^-|-$)/g, '');
      const res  = await apiRegister({ organization_name: orgName, organization_slug: slug, email, password, role: 'ADMIN' });
      setAccessToken(res.access_token);
      await login(email, password);
      navigate('/dashboard', { replace: true });
    } catch (err: any) {
      const detail = err?.response?.data?.detail;
      setErrorMsg(
        Array.isArray(detail) ? detail[0]?.msg :
        typeof detail === 'string' ? detail :
        'Registration failed. Please check your details.'
      );
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <AuthLayout title="Create your account" subtitle="Get started with VoiceGuard — free.">
      <form onSubmit={handleSubmit} noValidate style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>

        <div className="form-field">
          <label htmlFor="reg-org" className="form-label">Organization name</label>
          <input
            id="reg-org"
            type="text"
            className="form-input"
            value={orgName}
            onChange={e => setOrgName(e.target.value)}
            required
            placeholder="Acme Corp"
            autoComplete="organization"
          />
        </div>

        <div className="form-field">
          <label htmlFor="reg-email" className="form-label">Work email</label>
          <input
            id="reg-email"
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
          <label htmlFor="reg-password" className="form-label">Password</label>
          <div className="input-wrapper">
            <input
              id="reg-password"
              type={showPass ? "text" : "password"}
              className="form-input"
              value={password}
              onChange={e => setPassword(e.target.value)}
              autoComplete="new-password"
              required
              placeholder="Minimum 8 characters"
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

          {/* Password strength indicator */}
          {password.length > 0 && (
            <div style={{ marginTop: '.375rem' }}>
              <div style={{ display: 'flex', gap: '4px', height: '3px', marginBottom: '4px' }}>
                {[1,2,3,4].map(n => (
                  <div
                    key={n}
                    style={{
                      flex: 1,
                      borderRadius: '2px',
                      background: strength >= n ? STRENGTH_COLORS[strength] : 'var(--bg-muted)',
                      transition: 'background .25s',
                    }}
                  />
                ))}
              </div>
              <span style={{ fontSize: '.75rem', color: STRENGTH_COLORS[strength], fontWeight: 600 }}>
                {STRENGTH_LABELS[strength]}
              </span>
            </div>
          )}
        </div>

        <div className="form-field">
          <label htmlFor="reg-confirm" className="form-label">Confirm password</label>
          <input
            id="reg-confirm"
            type={showPass ? "text" : "password"}
            className="form-input"
            value={confirmPassword}
            onChange={e => setConfirmPassword(e.target.value)}
            autoComplete="new-password"
            required
            placeholder="Repeat your password"
          />
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
          id="reg-submit-btn"
          type="submit"
          className="btn btn-primary"
          style={{ width: '100%', marginTop: '.375rem' }}
          disabled={isLoading}
        >
          {isLoading ? "Creating account…" : "Create account"}
        </button>

        <div className="divider">or</div>

        <p style={{ textAlign: 'center', fontSize: '.875rem', color: 'var(--text-muted)' }}>
          Already have an account?{' '}
          <Link to="/login" style={{ color: 'var(--brand-600)', fontWeight: 600 }}>
            Sign in
          </Link>
        </p>
      </form>
    </AuthLayout>
  );
}
