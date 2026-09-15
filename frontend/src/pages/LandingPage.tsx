import { useEffect, useRef } from 'react';
import { Link } from 'react-router-dom';
import { Navbar } from '../components/Navbar';
import { Footer } from '../components/Footer';
import './LandingPage.css';

import type { SVGProps } from 'react';

const IconUser = (p: SVGProps<SVGSVGElement>) => <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" {...p}><circle cx="12" cy="8" r="4"/><path d="M6 20v-1a6 6 0 0 1 12 0v1"/></svg>;
const IconKey = (p: SVGProps<SVGSVGElement>) => <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" {...p}><circle cx="7" cy="17" r="4"/><path d="M10.7 13.3L21 3"/><path d="M18 5l2 2"/><path d="M15 8l2 2"/></svg>;
const IconPhone = (p: SVGProps<SVGSVGElement>) => <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" {...p}><path d="M22 16.9a19 19 0 0 1-5.6-.9 2 2 0 0 0-2 .5l-2.5 2.5a15.1 15.1 0 0 1-6.9-6.9l2.5-2.5a2 2 0 0 0 .5-2 19 19 0 0 1-.9-5.6A2 2 0 0 0 5.1 2H3a2 2 0 0 0-2 2 18 18 0 0 0 18 18 2 2 0 0 0 2-2v-2a2 2 0 0 0-1.9-2.1z"/></svg>;
const IconClock = (p: SVGProps<SVGSVGElement>) => <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" {...p}><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>;
const IconActivity = (p: SVGProps<SVGSVGElement>) => <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" {...p}><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>;
const IconLink = (p: SVGProps<SVGSVGElement>) => <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" {...p}><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07L11.7 5.25"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07L14.29 18.74"/></svg>;
const IconGlobe = (p: SVGProps<SVGSVGElement>) => <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" {...p}><circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15 15 0 0 1 4 10 15 15 0 0 1-4 10A15 15 0 0 1 8 12a15 15 0 0 1 4-10z"/></svg>;
const IconCpu = (p: SVGProps<SVGSVGElement>) => <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" {...p}><rect x="4" y="4" width="16" height="16" rx="2"/><rect x="9" y="9" width="6" height="6"/><line x1="9" y1="1" x2="9" y2="4"/><line x1="15" y1="1" x2="15" y2="4"/><line x1="9" y1="20" x2="9" y2="23"/><line x1="15" y1="20" x2="15" y2="23"/><line x1="20" y1="9" x2="23" y2="9"/><line x1="20" y1="14" x2="23" y2="14"/><line x1="1" y1="9" x2="4" y2="9"/><line x1="1" y1="14" x2="4" y2="14"/></svg>;
const IconLock = (p: SVGProps<SVGSVGElement>) => <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" {...p}><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>;
const IconCheck = (p: SVGProps<SVGSVGElement>) => <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" {...p}><polyline points="20 6 9 17 4 12"/></svg>;


const WAVEFORM_BARS = 36;

export function LandingPage() {
  const observerRef = useRef<IntersectionObserver | null>(null);

  useEffect(() => {
    observerRef.current = new IntersectionObserver(
      entries => entries.forEach(e => { if (e.isIntersecting) e.target.classList.add('visible'); }),
      { threshold: 0.1, rootMargin: '0px 0px -40px 0px' }
    );
    document.querySelectorAll('.reveal').forEach(el => observerRef.current?.observe(el));
    return () => observerRef.current?.disconnect();
  }, []);

  return (
    <>
      <Navbar />
      <main>

        {/* ── HERO ──────────────────────────────────────────────── */}
        <section className="hero">
          <div className="container hero-inner">

            {/* Left content */}
            <div className="hero-content reveal">
              <div className="hero-eyebrow">
                <span className="hero-eyebrow-dot" aria-hidden="true" />
                AI-Powered Voice Security
              </div>

              <h1 className="hero-headline">
                Stop voice cloning<br />
                <span className="gradient-text">before it strikes.</span>
              </h1>

              <p className="hero-subline">
                Real-time detection of synthetic voice impersonation attacks.
                Protect your organization with sub-200ms AI analysis.
              </p>

              <div className="hero-cta">
                <Link to="/register" className="btn btn-primary btn-lg">Get started free</Link>
                <button
                  className="btn btn-secondary btn-lg"
                  onClick={() => document.querySelector('#how-it-works')?.scrollIntoView({ behavior: 'smooth' })}
                >
                  See how it works
                </button>
              </div>

              <div className="hero-stats reveal reveal-delay-1">
                <div className="hero-stat">
                  <span className="hero-stat-value">&lt;200ms</span>
                  <span className="hero-stat-label">Detection latency</span>
                </div>
                <div className="hero-stat">
                  <span className="hero-stat-value">99.8%</span>
                  <span className="hero-stat-label">Accuracy rate</span>
                </div>
                <div className="hero-stat">
                  <span className="hero-stat-value">Zero</span>
                  <span className="hero-stat-label">Audio stored</span>
                </div>
              </div>
            </div>

            {/* Right visualization */}
            <div className="hero-visual reveal reveal-delay-2" aria-hidden="true">
              <div className="hero-viz-card">
                <div className="viz-header">
                  <span className="viz-title">Live Analysis</span>
                  <span className="viz-status">
                    <span className="viz-status-dot" /> Active
                  </span>
                </div>

                {/* Animated waveform */}
                <div className="hero-waveform">
                  {Array.from({ length: WAVEFORM_BARS }).map((_, i) => (
                    <div
                      key={i}
                      className="hero-wave-bar"
                      style={{
                        '--spd': `${0.8 + (i % 7) * 0.15}s`,
                        animationDelay: `${(i * 0.05) % 1}s`,
                        height: `${32 + Math.abs(Math.sin(i * 0.8)) * 44}%`,
                      } as React.CSSProperties}
                    />
                  ))}
                </div>

                <div className="viz-metrics">
                  <div className="viz-metric">
                    <div className="viz-metric-label">Synthetic probability</div>
                    <div className="viz-metric-value danger">89.4%</div>
                    <div className="viz-prob-bar">
                      <div className="viz-prob-fill" style={{ width: '89.4%' }} />
                    </div>
                  </div>
                  <div className="viz-metric">
                    <div className="viz-metric-label">Biometric match</div>
                    <div className="viz-metric-value warn">Low</div>
                  </div>
                </div>
              </div>

              <div className="hero-badge-float">
                <div className="hero-badge-indicator" />
                <div>
                  <div className="hero-badge-text">Threat blocked</div>
                  <div className="hero-badge-sub">CEO impersonation attempt</div>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* ── TRUST BAR ─────────────────────────────────────────── */}
        <section className="trust-bar" aria-label="Trusted by enterprises">
          <div className="container trust-bar-inner reveal">
            <span className="trust-bar-label">Protecting teams at</span>
            <div className="trust-bar-items">
              <span className="trust-bar-item">Global Banking</span>
              <span className="trust-bar-item">Healthcare</span>
              <span className="trust-bar-item">Government</span>
              <span className="trust-bar-item">Enterprise Tech</span>
              <span className="trust-bar-item">Financial Services</span>
            </div>
          </div>
        </section>

        {/* ── PROBLEM ───────────────────────────────────────────── */}
        <section id="problem" className="section problem-section">
          <div className="container">
            <div className="lp-head reveal">
              <div className="section-label">Threat Landscape</div>
              <h2>Voice is no longer proof of identity.</h2>
              <p>
                Generative AI has commoditized voice cloning. Three seconds of audio
                is enough for attackers to bypass biometric authentication.
              </p>
            </div>

            <div className="problem-grid">
              <div className="problem-card reveal reveal-delay-1">
                <div className="problem-card-icon"><IconUser /></div>
                <h3>Executive Impersonation</h3>
                <p>
                  Attackers clone C-suite voices to authorize fraudulent wire
                  transfers and confidential data disclosures.
                </p>
                <div className="problem-stat">$243k average loss per incident</div>
              </div>

              <div className="problem-card reveal reveal-delay-2">
                <div className="problem-card-icon"><IconKey /></div>
                <h3>Biometric Bypass</h3>
                <p>
                  Legacy "voice is my password" authentication is trivially
                  defeated by modern synthetic audio generation.
                </p>
                <div className="problem-stat">100% bypass rate on legacy systems</div>
              </div>

              <div className="problem-card reveal reveal-delay-3">
                <div className="problem-card-icon"><IconPhone /></div>
                <h3>Spear Vishing</h3>
                <p>
                  Targeted calls cloning trusted vendor or IT support voices
                  extract credentials and sensitive corporate data.
                </p>
                <div className="problem-stat">300% increase in 2024</div>
              </div>
            </div>
          </div>
        </section>

        {/* ── HOW IT WORKS ──────────────────────────────────────── */}
        <section id="how-it-works" className="section how-section">
          <div className="container">
            <div className="lp-head reveal">
              <div className="section-label">Platform Pipeline</div>
              <h2>Four stages to absolute voice certainty.</h2>
              <p>
                Our edge-native architecture processes live audio with
                detection artifacts invisible to the human ear.
              </p>
            </div>

            <div className="steps-grid">
              <div className="step-card step-1 reveal reveal-delay-1">
                <div className="step-number">01</div>
                <h3>Capture</h3>
                <p>Ingests real-time streams from VoIP, SIP, WebRTC, or file uploads with zero latency overhead.</p>
              </div>
              <div className="step-card step-2 reveal reveal-delay-2">
                <div className="step-number">02</div>
                <h3>Extract</h3>
                <p>Isolates speech components and extracts acoustic, phonetic, and prosodic feature vectors.</p>
              </div>
              <div className="step-card step-3 reveal reveal-delay-3">
                <div className="step-number">03</div>
                <h3>Analyze</h3>
                <p>Dual-engine AI identifies synthetic artifacts and cross-references speaker biometric profiles.</p>
              </div>
              <div className="step-card step-4 reveal reveal-delay-4">
                <div className="step-number">04</div>
                <h3>Act</h3>
                <p>Triggers webhooks, terminates sessions, or alerts analysts — all within a single audio frame.</p>
              </div>
            </div>
          </div>
        </section>

        {/* ── FEATURES ──────────────────────────────────────────── */}
        <section id="features" className="section features-section">
          <div className="container">
            <div className="lp-head reveal">
              <div className="section-label">Core Capabilities</div>
              <h2>Enterprise-grade audio defense.</h2>
              <p>Designed to integrate into existing zero-trust communication environments.</p>
            </div>

            <div className="features-grid">
              <div className="feature-card reveal reveal-delay-1">
                <div className="feature-icon" style={{ background: '#eff6ff' }}>
                  <IconClock style={{ stroke: '#1d4ed8' }} />
                </div>
                <h3>Sub-200ms Latency</h3>
                <p>Operates invisibly in real-time channels without degrading audio quality or increasing call delay.</p>
              </div>

              <div className="feature-card reveal reveal-delay-2">
                <div className="feature-icon" style={{ background: '#fef2f2' }}>
                  <IconActivity style={{ stroke: '#dc2626' }} />
                </div>
                <h3>Liveness Detection</h3>
                <p>Identifies micro-tremors, breathing patterns, and glottal pulse signatures invisible to synthetic models.</p>
              </div>

              <div className="feature-card reveal reveal-delay-3">
                <div className="feature-icon" style={{ background: '#f0fdf4' }}>
                  <IconLink style={{ stroke: '#16a34a' }} />
                </div>
                <h3>Drop-in Integrations</h3>
                <p>Native connectors for Twilio, Zoom, Microsoft Teams, AWS Connect, and enterprise SIP trunks.</p>
              </div>
            </div>
          </div>
        </section>

        {/* ── ARCHITECTURE ──────────────────────────────────────── */}
        <section id="technology" className="section arch-section">
          <div className="container arch-inner">

            {/* Layers diagram */}
            <div className="arch-layers reveal">
              <div className="arch-layer">
                <div className="arch-layer-icon" style={{ background: '#eef2ff' }}>
                  <IconGlobe style={{ stroke: '#4f46e5' }} />
                </div>
                <div className="arch-layer-text">
                  <h4>Edge Ingestion</h4>
                  <p>Global points of presence, &lt;50ms to nearest node</p>
                </div>
              </div>
              <div className="arch-connector" />
              <div className="arch-layer">
                <div className="arch-layer-icon" style={{ background: '#fffbeb' }}>
                  <IconCpu style={{ stroke: '#d97706' }} />
                </div>
                <div className="arch-layer-text">
                  <h4>Inference Engine</h4>
                  <p>Transformer + Wav2Vec2 models on GPU</p>
                </div>
              </div>
              <div className="arch-connector" />
              <div className="arch-layer">
                <div className="arch-layer-icon" style={{ background: '#f0fdfa' }}>
                  <IconLock style={{ stroke: '#0d9488' }} />
                </div>
                <div className="arch-layer-text">
                  <h4>Zero-Knowledge Processing</h4>
                  <p>In-memory only, audio never persisted</p>
                </div>
              </div>
            </div>

            {/* Content */}
            <div className="arch-content reveal reveal-delay-2">
              <div className="section-label">Privacy First</div>
              <h2>Built for the strictest compliance regimes.</h2>
              <p>
                We never store raw audio. Analysis occurs entirely in volatile memory
                within compliant, isolated tenant boundaries.
              </p>
              <div className="arch-bullets">
                {[
                  'Audio is processed in RAM and discarded after each frame.',
                  'All metadata is strictly isolated per organization tenant.',
                  'Cryptographic audit logs ensure immutable security history.',
                  'Role-based access control limits visibility to authorized staff.',
                ].map(text => (
                  <div key={text} className="arch-bullet">
                    <div className="arch-bullet-check"><IconCheck /></div>
                    <span>{text}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </section>

        {/* ── FINAL CTA ─────────────────────────────────────────── */}
        <section className="cta-section">
          <div className="container cta-inner reveal">
            <h2>Ready to secure your voice channels?</h2>
            <p>
              Deploy VoiceGuard across your organization today and block
              synthetic voice attacks before they compromise your data.
            </p>
            <div className="cta-actions">
              <Link to="/register" className="btn btn-white btn-lg">Start free trial</Link>
              <Link to="/login" className="btn btn-outline-white btn-lg">Sign in</Link>
            </div>
          </div>
        </section>

      </main>
      <Footer />
    </>
  );
}
