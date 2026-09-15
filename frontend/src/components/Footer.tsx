import { Link } from 'react-router-dom';
import './Footer.css';

const MicSvg = () => (
  <svg viewBox="0 0 24 24" aria-hidden="true">
    <path d="M12 2a3 3 0 0 1 3 3v7a3 3 0 0 1-6 0V5a3 3 0 0 1 3-3z"/>
    <path d="M19 10v2a7 7 0 0 1-14 0v-2"/>
    <line x1="12" y1="19" x2="12" y2="23"/>
    <line x1="8" y1="23" x2="16" y2="23"/>
  </svg>
);

const FOOTER_LINKS: Record<string, string[]> = {
  Product: ['Features', 'How It Works', 'Technology', 'Integrations'],
  Company: ['About', 'Security', 'Privacy Policy', 'Terms'],
  Support: ['Documentation', 'API Reference', 'Status', 'Contact'],
};

export function Footer() {
  return (
    <footer className="footer" aria-label="Site footer">
      <div className="container">
        <div className="footer-top">
          {/* Brand */}
          <div>
            <Link to="/" className="footer-logo" aria-label="VoiceGuard home">
              <div className="footer-logo-mark"><MicSvg /></div>
              <span className="footer-logo-text">Voice<span>Guard</span></span>
            </Link>
            <p className="footer-brand-desc">
              Real-time AI detection of synthetic voice impersonation.
              Protect your enterprise with millisecond-precision analysis.
            </p>
            <div className="footer-badges">
              <span className="footer-badge">SOC 2 Ready</span>
              <span className="footer-badge">ISO 27001</span>
              <span className="footer-badge">GDPR Compliant</span>
            </div>
          </div>

          {/* Links */}
          <div className="footer-links-grid">
            {Object.entries(FOOTER_LINKS).map(([section, links]) => (
              <div key={section} className="footer-links-col">
                <h3 className="footer-col-title">{section}</h3>
                <ul>
                  {links.map(l => (
                    <li key={l}><Link to="#" className="footer-link">{l}</Link></li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </div>

        <div className="footer-bottom">
          <p className="footer-copy">© {new Date().getFullYear()} VoiceGuard AI. All rights reserved.</p>
          <p className="footer-tagline">Built for enterprise security teams.</p>
        </div>
      </div>
    </footer>
  );
}
