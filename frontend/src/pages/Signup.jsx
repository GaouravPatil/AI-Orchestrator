import { useState } from 'react';
import { signup } from '../services/api';
import JarvisBackground from '../components/JarvisBackground';
import '../styles/Login.css';

export default function Signup({ onGoToLogin }) {
  const [fullName, setFullName]     = useState('');
  const [email, setEmail]           = useState('');
  const [password, setPassword]     = useState('');
  const [confirm, setConfirm]       = useState('');
  const [loading, setLoading]       = useState(false);
  const [error, setError]           = useState('');
  const [success, setSuccess]       = useState(false);
  const [showPass, setShowPass]     = useState(false);
  const [showConf, setShowConf]     = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    if (!fullName || !email || !password || !confirm) {
      setError('All fields are required.');
      return;
    }
    if (password !== confirm) {
      setError('Passwords do not match.');
      return;
    }
    if (password.length < 8) {
      setError('Password must be at least 8 characters.');
      return;
    }

    setLoading(true);
    try {
      await signup(fullName, email, password);
      setSuccess(true);
      // Auto-redirect to login after 2 seconds
      setTimeout(() => onGoToLogin(), 2000);
    } catch (err) {
      const detail = err.response?.data?.detail;
      if (!err.response) {
        // Network error — service is down or unreachable
        setError('Cannot reach the server. Make sure the backend is running.');
      } else if (typeof detail === 'string') {
        // 400 from our own endpoint e.g. "Email already exists"
        setError(detail);
      } else if (Array.isArray(detail)) {
        // 422 Pydantic validation — extract first human-readable message
        setError(detail[0]?.msg || 'Validation error. Check your inputs.');
      } else {
        setError(`Registration failed (HTTP ${err.response.status}). Try again.`);
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

      <div className="login-center" style={{ maxWidth: '460px' }}>
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
            <h2 className="font-orbitron">CREATE ACCOUNT</h2>
            <p>Register to access the platform</p>
          </div>

          {success ? (
            <div className="signup-success">
              <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <div>
                <p className="signup-success-title">Account Created!</p>
                <p className="signup-success-sub">Redirecting to login…</p>
              </div>
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="login-form">
              {/* Full Name */}
              <div className="field-group">
                <label>FULL NAME</label>
                <div className="input-wrapper">
                  <span className="input-icon">
                    <svg width="16" height="16" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.5">
                      <path strokeLinecap="round" d="M15.75 6a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0zM4.501 20.118a7.5 7.5 0 0114.998 0A17.933 17.933 0 0112 21.75c-2.676 0-5.216-.584-7.499-1.632z" />
                    </svg>
                  </span>
                  <input
                    id="signup-name"
                    className="input"
                    type="text"
                    placeholder="John Doe"
                    value={fullName}
                    onChange={e => setFullName(e.target.value)}
                    autoComplete="name"
                  />
                </div>
              </div>

              {/* Email */}
              <div className="field-group">
                <label>EMAIL ADDRESS</label>
                <div className="input-wrapper">
                  <span className="input-icon">
                    <svg width="16" height="16" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.5">
                      <path strokeLinecap="round" d="M21.75 6.75v10.5a2.25 2.25 0 01-2.25 2.25h-15a2.25 2.25 0 01-2.25-2.25V6.75m19.5 0A2.25 2.25 0 0019.5 4.5h-15a2.25 2.25 0 00-2.25 2.25m19.5 0v.243a2.25 2.25 0 01-1.07 1.916l-7.5 4.615a2.25 2.25 0 01-2.36 0L3.32 8.91a2.25 2.25 0 01-1.07-1.916V6.75" />
                    </svg>
                  </span>
                  <input
                    id="signup-email"
                    className="input"
                    type="email"
                    placeholder="user@example.com"
                    value={email}
                    onChange={e => setEmail(e.target.value)}
                    autoComplete="email"
                  />
                </div>
              </div>

              {/* Password */}
              <div className="field-group">
                <label>PASSWORD</label>
                <div className="input-wrapper">
                  <span className="input-icon">
                    <svg width="16" height="16" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.5">
                      <path strokeLinecap="round" d="M16.5 10.5V6.75a4.5 4.5 0 10-9 0v3.75m-.75 11.25h10.5a2.25 2.25 0 002.25-2.25v-6.75a2.25 2.25 0 00-2.25-2.25H6.75a2.25 2.25 0 00-2.25 2.25v6.75a2.25 2.25 0 002.25 2.25z" />
                    </svg>
                  </span>
                  <input
                    id="signup-password"
                    className="input"
                    type={showPass ? 'text' : 'password'}
                    placeholder="Min. 6 characters"
                    value={password}
                    onChange={e => setPassword(e.target.value)}
                    autoComplete="new-password"
                  />
                  <button type="button" className="pass-toggle" onClick={() => setShowPass(s => !s)}>
                    {showPass ? '🙈' : '👁'}
                  </button>
                </div>
              </div>

              {/* Confirm Password */}
              <div className="field-group">
                <label>CONFIRM PASSWORD</label>
                <div className="input-wrapper">
                  <span className="input-icon">
                    <svg width="16" height="16" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.5">
                      <path strokeLinecap="round" d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z" />
                    </svg>
                  </span>
                  <input
                    id="signup-confirm"
                    className="input"
                    type={showConf ? 'text' : 'password'}
                    placeholder="Re-enter password"
                    value={confirm}
                    onChange={e => setConfirm(e.target.value)}
                    autoComplete="new-password"
                  />
                  <button type="button" className="pass-toggle" onClick={() => setShowConf(s => !s)}>
                    {showConf ? '🙈' : '👁'}
                  </button>
                </div>
              </div>

              {error && (
                <div className="login-error">
                  <span>⚠</span> {error}
                </div>
              )}

              <button id="signup-submit" type="submit" className="btn btn-primary login-btn" disabled={loading}>
                {loading ? (
                  <span className="login-loading">
                    <span className="spinner" />
                    REGISTERING...
                  </span>
                ) : (
                  <>
                    <span>CREATE ACCOUNT</span>
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M5 12h14M12 5l7 7-7 7" />
                    </svg>
                  </>
                )}
              </button>
            </form>
          )}

          <div className="login-footer">
            <div className="login-footer-row">
              <span className="badge badge-green"><span className="dot" />SYSTEM ONLINE</span>
              <span className="badge badge-cyan">v1.0.0</span>
            </div>
            <p>
              Already have an account?{' '}
              <button
                id="go-to-login"
                onClick={onGoToLogin}
                className="link-btn"
              >
                Sign In
              </button>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
