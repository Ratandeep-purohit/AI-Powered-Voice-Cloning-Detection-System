import type { ReactNode } from 'react';
import { Link } from 'react-router-dom';
import './AuthLayout.css';

const TRUST_ITEMS = [
  'Argon2id password hashing — bank-grade protection',
  'JWT authentication with server-side validation',
  'Multi-tenant data isolation by organization',
  'Immutable security audit log on every event',
];

const MicSvg = () => (
  <svg viewBox="0 0 24 24" aria-hidden="true">
    <path d="M12 2a3 3 0 0 1 3 3v7a3 3 0 0 1-6 0V5a3 3 0 0 1 3-3z"/>
    <path d="M19 10v2a7 7 0 0 1-14 0v-2"/>
    <line x1="12" y1="19" x2="12" y2="23"/>
    <line x1="8" y1="23" x2="16" y2="23"/>
  </svg>
);

const CheckSvg = () => (
  <svg viewBox="0 0 24 24" aria-hidden="true">
    <polyline points="20 6 9 17 4 12" />
  </svg>
);

const BARS = 38;

interface AuthLayoutProps {
  children: ReactNode;
  title: string;
  subtitle: string;
}

export function AuthLayout({ children, title, subtitle }: AuthLayoutProps) {
  return (
    <div className="auth-layout">

      {/* ── Left branding panel ─────────────────────────────── */}
      <aside className="auth-panel-left">
        <Link to="/" className="auth-brand" aria-label="Go to VoiceGuard homepage">
          <div className="auth-brand-mark"><MicSvg /></div>
          <span className="auth-brand-name">VoiceGuard</span>
        </Link>

        <div className="auth-left-body">
          <h2 className="auth-left-heading">
            Detect voice cloning<br />
            <span>before it's a threat.</span>
          </h2>

          <p>
            AI-powered real-time analysis protects your organization
            from synthetic voice impersonation with sub-200ms precision.
          </p>

          {/* Animated waveform visualization */}
          <div className="auth-waveform-wrap" aria-hidden="true">
            <div className="auth-waveform-label">
              <span className="auth-waveform-title">Voice Analysis</span>
              <span className="auth-waveform-badge">
                <span className="auth-waveform-badge-dot" />
                Live
              </span>
            </div>
            <div className="auth-waveform-bars">
              {Array.from({ length: BARS }).map((_, i) => (
                <div
                  key={i}
                  className="auth-waveform-bar"
                  style={{
                    '--spd': `${0.9 + (i % 5) * 0.18}s`,
                    '--dly': `${(i * 0.06) % 1.2}s`,
                    height: `${28 + Math.abs(Math.sin(i * 0.75)) * 40}%`,
                  } as React.CSSProperties}
                />
              ))}
            </div>
          </div>

          {/* Trust indicators */}
          <div className="auth-trust-list">
            {TRUST_ITEMS.map(item => (
              <div key={item} className="auth-trust-item">
                <div className="auth-trust-check"><CheckSvg /></div>
                <span>{item}</span>
              </div>
            ))}
          </div>
        </div>
      </aside>

      {/* ── Right form panel ────────────────────────────────── */}
      <main className="auth-panel-right">
        <div className="auth-form-box">
          {/* Mobile-only logo (left panel is hidden on mobile) */}
          <Link to="/" className="auth-mobile-brand" aria-label="VoiceGuard home">
            <div className="auth-mobile-brand-mark"><MicSvg /></div>
            <span className="auth-mobile-brand-name">VoiceGuard</span>
          </Link>

          <div className="auth-form-heading">
            <h1>{title}</h1>
            <p>{subtitle}</p>
          </div>

          {children}
        </div>
      </main>
    </div>
  );
}
