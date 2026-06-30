import { useState } from 'react';
import { login, setToken, setUser } from '../services/api';
import JarvisBackground from '../components/JarvisBackground';
import '../styles/Login.css';

export default function Login({ onLogin, onGoToSignup }) {
  const [email, setEmail]       = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading]   = useState(false);
  const [error, setError]       = useState('');
  const [showPass, setShowPass] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!email || !password) { setError('All fields required'); return; }
    setLoading(true);
    setError('');
    try {
      const data = await login(email, password);
      setToken(data.access_token);
      // Decode user info from JWT payload
      const payload = JSON.parse(atob(data.access_token.split('.')[1]));
      setUser({ email: payload.sub, role: payload.role });
      onLogin();
    } catch (err) {
      const detail = err.response?.data?.detail;
      if (!err.response) {
        setError('Cannot reach the server. Make sure the backend is running.');
      } else if (typeof detail === 'string') {
        setError(detail);
      } else {
        setError('Authentication failed. Check credentials.');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-root">
      <JarvisBackground intensity={0.8} />

      {/* Corner decorations */}
      <div className="corner-tl" />
      <div className="corner-br" />

      <div className="login-center">
        {/* Logo */}
        <div className="login-logo animate-fade-up">
          <div className="logo-ring">
            <svg width="40" height="40" viewBox="0 0 40 40" fill="none">
              <circle cx="20" cy="20" r="18" stroke="rgba(0,212,255,0.3)" strokeWidth="1" />
              <circle cx="20" cy="20" r="12" stroke="rgba(0,212,255,0.5)" strokeWidth="1" />
              <circle cx="20" cy="20" r="5"  fill="rgba(0,212,255,0.9)" />
              <line x1="20" y1="2"  x2="20" y2="8"  stroke="rgba(0,212,255,0.7)" strokeWidth="1.5" />
              <line x1="20" y1="32" x2="20" y2="38" stroke="rgba(0,212,255,0.7)" strokeWidth="1.5" />
              <line x1="2"  y1="20" x2="8"  y2="20" stroke="rgba(0,212,255,0.7)" strokeWidth="1.5" />
              <line x1="32" y1="20" x2="38" y2="20" stroke="rgba(0,212,255,0.7)" strokeWidth="1.5" />
            </svg>
          </div>
          <div>
            <h1 className="login-title font-orbitron gradient-text">AI ORCHESTRATOR</h1>
            <p className="login-subtitle">Kubernetes Intelligence Platform</p>
          </div>
        </div>

        {/* Card */}
        <div className="login-card glass animate-fade-up animate-scale-in">
          <div className="scan-overlay" />

          <div className="login-card-header">
            <h2 className="font-orbitron">SYSTEM ACCESS</h2>
            <p>Authenticate to continue</p>
          </div>

          <form onSubmit={handleSubmit} className="login-form">
            <div className="field-group">
              <label>EMAIL ADDRESS</label>
              <div className="input-wrapper">
                <span className="input-icon">
                  <svg width="16" height="16" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.5">
                    <path strokeLinecap="round" d="M21.75 6.75v10.5a2.25 2.25 0 01-2.25 2.25h-15a2.25 2.25 0 01-2.25-2.25V6.75m19.5 0A2.25 2.25 0 0019.5 4.5h-15a2.25 2.25 0 00-2.25 2.25m19.5 0v.243a2.25 2.25 0 01-1.07 1.916l-7.5 4.615a2.25 2.25 0 01-2.36 0L3.32 8.91a2.25 2.25 0 01-1.07-1.916V6.75" />
                  </svg>
                </span>
                <input
                  id="email"
                  className="input"
                  type="email"
                  placeholder="user@example.com"
                  value={email}
                  onChange={e => setEmail(e.target.value)}
                  autoComplete="email"
                />
              </div>
            </div>

            <div className="field-group">
              <label>PASSWORD</label>
              <div className="input-wrapper">
                <span className="input-icon">
                  <svg width="16" height="16" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.5">
                    <path strokeLinecap="round" d="M16.5 10.5V6.75a4.5 4.5 0 10-9 0v3.75m-.75 11.25h10.5a2.25 2.25 0 002.25-2.25v-6.75a2.25 2.25 0 00-2.25-2.25H6.75a2.25 2.25 0 00-2.25 2.25v6.75a2.25 2.25 0 002.25 2.25z" />
                  </svg>
                </span>
                <input
                  id="password"
                  className="input"
                  type={showPass ? 'text' : 'password'}
                  placeholder="••••••••"
                  value={password}
                  onChange={e => setPassword(e.target.value)}
                  autoComplete="current-password"
                />
                <button type="button" className="pass-toggle" onClick={() => setShowPass(s => !s)}>
                  {showPass ? '🙈' : '👁'}
                </button>
              </div>
            </div>

            {error && (
              <div className="login-error">
                <span>⚠</span> {error}
              </div>
            )}

            <button id="login-submit" type="submit" className="btn btn-primary login-btn" disabled={loading}>
              {loading ? (
                <span className="login-loading">
                  <span className="spinner" />
                  AUTHENTICATING...
                </span>
              ) : (
                <>
                  <span>INITIALIZE SESSION</span>
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M5 12h14M12 5l7 7-7 7" />
                  </svg>
                </>
              )}
            </button>
          </form>

          <div className="login-footer">
            <div className="login-footer-row">
              <span className="badge badge-green"><span className="dot" />SYSTEM ONLINE</span>
              <span className="badge badge-cyan">v1.0.0</span>
            </div>
            <p>AI DevOps Orchestrator — Kubernetes Intelligence</p>
            <p style={{ marginTop: '6px' }}>
              No account?{' '}
              <button
                id="go-to-signup"
                onClick={onGoToSignup}
                className="link-btn"
              >
                Create one
              </button>
            </p>
          </div>
        </div>

        {/* Demo hint */}
        <div className="login-hint animate-fade-up">
          <span className="font-mono">demo →</span>
          <code>Garry@example.com</code>
          <span>/</span>
          <code>admin123</code>
        </div>
      </div>
    </div>
  );
}
