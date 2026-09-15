import { useEffect, useRef, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import './Navbar.css';

const NAV_LINKS = [
  { label: 'How It Works', href: '#how-it-works' },
  { label: 'Features',     href: '#features' },
  { label: 'Technology',   href: '#technology' },
];

export function Navbar() {
  const { isAuthenticated, logout } = useAuth();
  const navigate = useNavigate();
  const [scrolled, setScrolled] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 16);
    window.addEventListener('scroll', onScroll, { passive: true });
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) setMenuOpen(false);
    };
    if (menuOpen) document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, [menuOpen]);

  const handleNavClick = (href: string) => {
    setMenuOpen(false);
    if (href.startsWith('#')) {
      const el = document.querySelector(href);
      if (el) el.scrollIntoView({ behavior: 'smooth' });
    }
  };

  const handleLogout = () => { logout(); navigate('/'); };

  return (
    <>
      <nav className={`navbar${scrolled ? ' scrolled' : ''}`} aria-label="Main navigation">
        <div className="container">
          <div className="navbar-inner">
            {/* Logo */}
            <Link to="/" className="navbar-logo" aria-label="VoiceGuard home">
              <div className="navbar-logo-mark" aria-hidden="true">
                <svg viewBox="0 0 24 24" aria-hidden="true">
                  <path d="M12 2a3 3 0 0 1 3 3v7a3 3 0 0 1-6 0V5a3 3 0 0 1 3-3z"/>
                  <path d="M19 10v2a7 7 0 0 1-14 0v-2"/>
                  <line x1="12" y1="19" x2="12" y2="23"/>
                  <line x1="8" y1="23" x2="16" y2="23"/>
                </svg>
              </div>
              <span className="navbar-logo-text">Voice<span>Guard</span></span>
            </Link>

            {/* Desktop links */}
            <div className="navbar-links">
              {NAV_LINKS.map(l => (
                <button key={l.href} className="nav-link" onClick={() => handleNavClick(l.href)}>
                  {l.label}
                </button>
              ))}
            </div>

            {/* Desktop actions */}
            <div className="navbar-actions">
              {isAuthenticated ? (
                <>
                  <Link to="/dashboard" className="btn btn-ghost btn-sm">Dashboard</Link>
                  <button className="btn btn-primary btn-sm" onClick={handleLogout}>Sign out</button>
                </>
              ) : (
                <>
                  <Link to="/login" className="btn btn-ghost btn-sm">Log in</Link>
                  <Link to="/register" className="btn btn-primary btn-sm">Get started</Link>
                </>
              )}
            </div>

            {/* Mobile hamburger */}
            <button
              className="navbar-hamburger"
              onClick={() => setMenuOpen(o => !o)}
              aria-expanded={menuOpen}
              aria-controls="mobile-menu"
              aria-label={menuOpen ? 'Close menu' : 'Open menu'}
            >
              <span className="hamburger-line" />
              <span className="hamburger-line" />
              <span className="hamburger-line" />
            </button>
          </div>
        </div>
      </nav>

      {/* Mobile menu */}
      <div
        id="mobile-menu"
        ref={menuRef}
        className={`navbar-mobile-menu${menuOpen ? ' open' : ''}`}
        aria-hidden={!menuOpen}
      >
        {NAV_LINKS.map(l => (
          <button key={l.href} className="mobile-nav-link" onClick={() => handleNavClick(l.href)}>
            {l.label}
          </button>
        ))}
        <div className="mobile-actions">
          {isAuthenticated ? (
            <>
              <Link to="/dashboard" className="btn btn-secondary" onClick={() => setMenuOpen(false)}>Dashboard</Link>
              <button className="btn btn-primary" onClick={handleLogout}>Sign out</button>
            </>
          ) : (
            <>
              <Link to="/login" className="btn btn-secondary" onClick={() => setMenuOpen(false)}>Log in</Link>
              <Link to="/register" className="btn btn-primary" onClick={() => setMenuOpen(false)}>Get started</Link>
            </>
          )}
        </div>
      </div>
    </>
  );
}
