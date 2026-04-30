import { useState, useEffect } from 'react'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

function App() {
  const [incidents, setIncidents] = useState([]);
  const [selectedIncident, setSelectedIncident] = useState(null);
  const [signals, setSignals] = useState([]);
  const [metrics, setMetrics] = useState(null);
  const [rcaForm, setRcaForm] = useState({ category: 'INFRASTRUCTURE', fix: '', prevention: '' });
  const [loadingSignals, setLoadingSignals] = useState(false);
  const [healthStatus, setHealthStatus] = useState({ api: 'checking', redis: 'checking', db: 'checking' });
  const [currentTime, setCurrentTime] = useState(new Date());

  useEffect(() => {
    const timer = setInterval(() => setCurrentTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  const fetchIncidents = async () => {
    try {
      const res = await fetch(`${API_URL}/api/incidents`);
      const data = await res.json();
      setIncidents(data);
    } catch (err) {
      console.error("Failed to fetch incidents:", err);
    }
  };

  const checkHealth = async () => {
    try {
      const res = await fetch(`${API_URL}/health`);
      const data = await res.json();
      setHealthStatus({ 
        api: data.status === 'ok' ? 'up' : 'down',
        redis: data.dependencies?.redis === 'healthy' ? 'up' : 'down',
        db: data.dependencies?.postgres === 'healthy' ? 'up' : 'down'
      });
    } catch {
      setHealthStatus({ api: 'down', redis: 'down', db: 'down' });
    }
  };

  useEffect(() => {
    fetchIncidents();
    checkHealth();
    const interval = setInterval(() => {
      fetchIncidents();
      checkHealth();
    }, 3000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    if (!selectedIncident) return;
    const fetchData = async () => {
      setLoadingSignals(true);
      try {
        const [sigRes, metRes] = await Promise.all([
          fetch(`${API_URL}/api/incidents/${selectedIncident.id}/signals`),
          fetch(`${API_URL}/api/metrics/${selectedIncident.component_id}`)
        ]);
        setSignals(await sigRes.json());
        setMetrics(await metRes.json());
      } catch (err) {
        console.error("Failed to fetch details:", err);
      } finally {
        setLoadingSignals(false);
      }
    };
    fetchData();
  }, [selectedIncident]);

  const handleRcaSubmit = async (e) => {
    e.preventDefault();
    if (!selectedIncident) return;

    try {
      const res = await fetch(`${API_URL}/api/incidents/${selectedIncident.id}/rca`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          rca_category: rcaForm.category,
          fix_applied: rcaForm.fix,
          prevention_steps: rcaForm.prevention
        })
      });
      if (res.ok) {
        await fetchIncidents();
        setSelectedIncident(null);
        setRcaForm({ category: 'INFRASTRUCTURE', fix: '', prevention: '' });
      } else {
        const errData = await res.json();
        alert(`RCA Validation Failed: ${errData.detail}`);
      }
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '300px 1fr 400px', height: '100vh', gap: '20px', padding: '20px' }}>
      
      {/* LEFT: System Health & Architecture */}
      <aside className="glass-panel" style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '24px' }}>
        <div>
          <h2 style={{ fontSize: '1.5rem', fontWeight: '700', marginBottom: '4px' }}>IMS ENGINE</h2>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.8rem' }}>{currentTime.toLocaleTimeString()} | Native Linux Engine</p>
        </div>

        <div style={{ padding: '16px', background: 'rgba(255,255,255,0.03)', borderRadius: '12px', border: '1px solid rgba(255,255,255,0.05)' }}>
          <p style={{ fontSize: '0.7rem', fontWeight: '700', color: 'var(--text-secondary)', marginBottom: '12px', textTransform: 'uppercase' }}>Stack Observer</p>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ fontSize: '0.85rem' }}>Core API</span>
              <span style={{ height: '8px', width: '8px', borderRadius: '50%', background: healthStatus.api === 'up' ? '#10b981' : '#ef4444' }}></span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ fontSize: '0.85rem' }}>Redis (Buffer)</span>
              <span style={{ height: '8px', width: '8px', borderRadius: '50%', background: healthStatus.redis === 'up' ? '#10b981' : '#ef4444' }}></span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ fontSize: '0.85rem' }}>Postgres (SoT)</span>
              <span style={{ height: '8px', width: '8px', borderRadius: '50%', background: healthStatus.db === 'up' ? '#10b981' : '#ef4444' }}></span>
            </div>
          </div>
        </div>

        <div style={{ padding: '16px', background: 'rgba(0, 242, 255, 0.05)', borderRadius: '12px' }}>
          <p style={{ fontSize: '0.7rem', fontWeight: '700', color: 'var(--accent-color)', marginBottom: '8px', textTransform: 'uppercase' }}>Architecture Explanation</p>
          <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', lineHeight: '1.4' }}>
            High-volume signals are buffered in Redis before being debounced (10s window) and persisted as transactional Work Items in PostgreSQL.
          </p>
        </div>
      </aside>

      {/* MIDDLE: Incident Monitor */}
      <main className="glass-panel" style={{ display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
        <div style={{ padding: '24px', borderBottom: '1px solid var(--glass-border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h1 style={{ fontSize: '1.25rem', fontWeight: '700' }}>Active Incident Feed</h1>
        </div>
        
        <div style={{ flex: 1, overflowY: 'auto', padding: '20px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
          {incidents.length === 0 ? (
            <div style={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-secondary)' }}>
              Monitoring stack for signals...
            </div>
          ) : (
            incidents.map((inc, index) => (
              <div 
                key={inc.id} 
                className={`incident-card glass-panel severity-${inc.severity} animate-in`}
                style={{ 
                  padding: '16px', 
                  animationDelay: `${index * 0.05}s`,
                  background: selectedIncident?.id === inc.id ? 'rgba(255,255,255,0.05)' : 'var(--card-bg)'
                }}
                onClick={() => setSelectedIncident(inc)}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                  <span style={{ fontWeight: '700', fontSize: '1rem' }}>{inc.component_id}</span>
                  <div style={{ display: 'flex', gap: '8px' }}>
                     <span style={{ fontSize: '0.65rem', background: 'rgba(255,255,255,0.1)', padding: '2px 6px', borderRadius: '4px' }}>{inc.severity}</span>
                     <span style={{ fontSize: '0.65rem', color: 'var(--accent-color)', border: '1px solid var(--accent-color)', padding: '1px 6px', borderRadius: '4px' }}>DEBOUNCED</span>
                  </div>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                   <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
                      <span style={{ fontSize: '0.8rem', fontWeight: '800', color: inc.state === 'CLOSED' ? '#10b981' : '#f59e0b' }}>
                        [{inc.state}]
                      </span>
                      <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                         Grouped Signals: {inc.signal_count}
                      </span>
                   </div>
                   <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>{new Date(inc.start_time).toLocaleTimeString()}</span>
                </div>
              </div>
            ))
          )}
        </div>
      </main>

      {/* RIGHT: RCA & Audit Log */}
      <section className="glass-panel" style={{ overflowY: 'auto', padding: '24px' }}>
        {!selectedIncident ? (
          <div style={{ height: '100%', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', color: 'var(--text-secondary)', textAlign: 'center' }}>
            <div style={{ fontSize: '3rem', marginBottom: '20px' }}>🔍</div>
            <h3>Investigation Panel</h3>
            <p style={{ fontSize: '0.85rem', marginTop: '8px' }}>Select an incident to audit raw signals and submit RCA.</p>
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
            <h2 style={{ fontSize: '1.4rem' }}>{selectedIncident.component_id}</h2>
            
            <div style={{ display: 'flex', justifyContent: 'space-between', background: 'rgba(0, 242, 255, 0.05)', padding: '12px', borderRadius: '8px' }}>
              <span style={{ fontSize: '0.8rem' }}>Signals / Minute</span>
              <span style={{ fontSize: '0.9rem', fontWeight: '700', color: 'var(--accent-color)' }}>{metrics?.signals_per_min || 0}</span>
            </div>

            <div className="glass-panel" style={{ padding: '16px', background: 'rgba(0,0,0,0.2)' }}>
              <h4 style={{ fontSize: '0.7rem', color: 'var(--text-secondary)', marginBottom: '12px', textTransform: 'uppercase' }}>Audit Log (MongoDB)</h4>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', maxHeight: '150px', overflowY: 'auto', fontSize: '0.8rem' }}>
                {loadingSignals ? "Decrypting..." : signals.map(sig => (
                  <div key={sig._id} style={{ display: 'flex', gap: '10px', borderBottom: '1px solid rgba(255,255,255,0.05)', paddingBottom: '4px' }}>
                    <span style={{ color: 'var(--accent-color)', fontFamily: 'monospace' }}>[{new Date(sig.timestamp).toLocaleTimeString()}]</span>
                    <span>{sig.error}</span>
                  </div>
                ))}
              </div>
            </div>

            {selectedIncident.state !== 'CLOSED' ? (
              <form onSubmit={handleRcaSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                <h3 style={{ fontSize: '1.1rem' }}>Root Cause Analysis</h3>
                
                <select 
                  style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid var(--glass-border)', color: 'white', padding: '10px', borderRadius: '8px' }}
                  value={rcaForm.category}
                  onChange={e => setRcaForm({...rcaForm, category: e.target.value})}
                  required
                >
                  <option value="INFRASTRUCTURE">Infrastructure Failure</option>
                  <option value="DATABASE">Database Issue</option>
                  <option value="NETWORK">Network Outage</option>
                  <option value="CODE_BUG">Code Bug</option>
                </select>

                <textarea 
                  style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid var(--glass-border)', color: 'white', padding: '10px', borderRadius: '8px', minHeight: '80px' }}
                  value={rcaForm.fix}
                  onChange={e => setRcaForm({...rcaForm, fix: e.target.value})}
                  required
                  placeholder="Mandatory: Remediation steps..."
                />

                <textarea 
                  style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid var(--glass-border)', color: 'white', padding: '10px', borderRadius: '8px', minHeight: '80px' }}
                  value={rcaForm.prevention}
                  onChange={e => setRcaForm({...rcaForm, prevention: e.target.value})}
                  required
                  placeholder="Mandatory: Prevention strategy..."
                />

                <button 
                  type="submit"
                  style={{ background: 'var(--accent-color)', color: '#000', fontWeight: '800', padding: '14px', borderRadius: '8px', border: 'none', cursor: 'pointer' }}
                >
                  RESOLVE & CLOSE
                </button>
              </form>
            ) : (
              <div style={{ padding: '20px', borderRadius: '8px', border: '1px solid #10b981', background: 'rgba(16, 185, 129, 0.05)' }}>
                <h3 style={{ color: '#10b981', marginBottom: '12px' }}>RCA Report (Archived)</h3>
                <div style={{ fontSize: '0.85rem', display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  <p><strong>MTTR:</strong> {selectedIncident.mttr_minutes?.toFixed(1)} mins</p>
                  <p><strong>Cause:</strong> {selectedIncident.rca_category}</p>
                  <p><strong>Fix:</strong> {selectedIncident.fix_applied}</p>
                </div>
              </div>
            )}
          </div>
        )}
      </section>
    </div>
  )
}

export default App
