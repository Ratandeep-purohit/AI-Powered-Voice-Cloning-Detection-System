const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000/api/v1'

export default function App() {
  return (
    <main className="app-shell">
      <section className="status-card" aria-labelledby="app-title">
        <p className="eyebrow">SYSTEM FOUNDATION</p>
        <h1 id="app-title">Voice Cloning Detection System</h1>
        <p className="status-text">Development foundation is ready.</p>
        <div className="status-row">
          <span className="status-dot" aria-hidden="true" />
          <span>Frontend online</span>
        </div>
        <p className="api-url">API base: {apiBaseUrl}</p>
      </section>
    </main>
  )
}
