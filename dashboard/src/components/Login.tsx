import React, { useState, useEffect } from 'react';
import { GoogleOAuthProvider, GoogleLogin } from '@react-oauth/google';
import { useNavigate } from 'react-router-dom';

const clientId = import.meta.env.VITE_GOOGLE_CLIENT_ID || '';
const API_BASE = '/api/auth';

const ORG_TYPES = [
  { value: 'civilian',     label: '👤 Civilian',          desc: 'Personal use / general access' },
  { value: 'government',   label: '🏛 Civil Government',  desc: 'Municipal / state officials' },
  { value: 'ngo',          label: '🤝 NGO',               desc: 'Non-governmental organizations' },
  { value: 'hospital',     label: '🏥 Hospital',          desc: 'Medical facilities & staff' },
  { value: 'fire_station', label: '🚒 Fire Station',      desc: 'Fire & rescue services' },
  { value: 'police',       label: '🚔 Police',            desc: 'Law enforcement agencies' },
  { value: 'organization', label: '🏢 Organization',      desc: 'Private companies & institutions' },
];

const ROLE_COLORS: Record<string, string> = {
  civilian:     '#3b82f6',
  government:   '#8b5cf6',
  ngo:          '#10b981',
  hospital:     '#ef4444',
  fire_station: '#f97316',
  police:       '#1d4ed8',
  organization: '#6366f1',
};

// ── Google button as separate component — MUST be rendered inside GoogleOAuthProvider ──
interface GoogleBtnProps {
  mode: 'signin' | 'signup';
  onStore: (data: any) => void;
  onError: (msg: string) => void;
}
function GoogleLoginButton({ mode, onStore, onError }: GoogleBtnProps) {
  return (
    <div style={{ display: 'flex', justifyContent: 'center', marginTop: 10 }}>
      <GoogleLogin
        onSuccess={async (credentialResponse) => {
          try {
            const res = await fetch(`${API_BASE}/google`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ token: credentialResponse.credential }),
            });
            const data = await res.json();
            if (!res.ok) throw new Error(data.detail || 'Google login failed');
            onStore(data);
          } catch (err: any) {
            onError(err.message || 'Google sign-in failed on server');
          }
        }}
        onError={() => onError('Google login was cancelled or failed')}
        useOneTap={mode === 'signin'}
        theme="filled_black"
        shape="pill"
        text={mode === 'signup' ? "signup_with" : "signin_with"}
      />
    </div>
  );
}
// ── Main login form — NO Google hooks here ──
function LoginForm() {
  const navigate = useNavigate();
  const [mode, setMode] = useState<'signin' | 'signup'>('signin');
  const [orgType, setOrgType] = useState('civilian');
  const [orgId, setOrgId] = useState('');
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const _store = (data: { access_token: string; user: any }) => {
    localStorage.setItem('hres_token', data.access_token);
    localStorage.setItem('hres_user', JSON.stringify(data.user));
    navigate('/', { replace: true });
  };

  const handleEmailSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const endpoint = mode === 'signup' ? `${API_BASE}/register` : `${API_BASE}/login`;
      const body = mode === 'signup'
        ? { email, password, name, org_type: orgType, org_id: orgId || undefined }
        : { email, password };
      const res = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Authentication failed');
      _store(data);
    } catch (err: any) {
      setError(err.message || 'Something went wrong');
    } finally {
      setLoading(false);
    }
  };

  const accentColor = ROLE_COLORS[orgType] || '#8b5cf6';
  const selectedOrg = ORG_TYPES.find(o => o.value === orgType);
  const needsOrgId = ['government', 'hospital', 'fire_station', 'police', 'ngo', 'organization'].includes(orgType);

  return (
    <div className="login-container">
      <div className="login-bg-orb" style={{ background: `radial-gradient(circle, ${accentColor}22 0%, transparent 70%)` }} />
      <div className="login-box" style={{ '--accent': accentColor } as React.CSSProperties}>

        {/* Header */}
        <div className="login-header">
          <div className="login-logo">
            <div className="login-logo-ring" style={{ borderColor: accentColor }} />
            <span className="login-logo-text">HRES</span>
          </div>
          <h1 className="login-title">Heat Response Emergency System</h1>
          <p className="login-subtitle">
            {mode === 'signin' ? 'Sign in to your account' : 'Create your organization account'}
          </p>
        </div>

        {/* Mode Toggle */}
        <div className="login-mode-toggle">
          <button className={`mode-btn ${mode === 'signin' ? 'active' : ''}`}
            onClick={() => { setMode('signin'); setError(null); }}
            style={mode === 'signin' ? { background: accentColor } : {}}>
            Sign In
          </button>
          <button className={`mode-btn ${mode === 'signup' ? 'active' : ''}`}
            onClick={() => { setMode('signup'); setError(null); }}
            style={mode === 'signup' ? { background: accentColor } : {}}>
            Sign Up
          </button>
        </div>

        {/* Error */}
        {error && <div className="login-error"><span>⚠</span> {error}</div>}

        {/* Form */}
        <form className="login-form" onSubmit={handleEmailSubmit}>

          {/* Org Type — now visible on signin too as requested */}
          <div className="org-selector">
            <label className="field-label">Organization Type</label>
            <div className="org-grid">
              {ORG_TYPES.map(org => (
                <button key={org.value} type="button"
                  className={`org-tile ${orgType === org.value ? 'selected' : ''}`}
                  style={orgType === org.value ? { borderColor: ROLE_COLORS[org.value], background: `${ROLE_COLORS[org.value]}18` } : {}}
                  onClick={() => setOrgType(org.value)} title={org.desc}>
                  <span className="org-icon">{org.label.split(' ')[0]}</span>
                  <span className="org-label">{org.label.split(' ').slice(1).join(' ')}</span>
                </button>
              ))}
            </div>
            {selectedOrg && <p className="org-desc" style={{ color: accentColor }}>{selectedOrg.desc}</p>}
          </div>

          {/* Name — signup only */}
          {mode === 'signup' && (
            <div className="field-group">
              <label className="field-label">Full Name</label>
              <input className="login-input" type="text" placeholder="Your full name"
                value={name} onChange={e => setName(e.target.value)} required />
            </div>
          )}

          {/* Org ID — official orgs only */}
          {mode === 'signup' && needsOrgId && (
            <div className="field-group">
              <label className="field-label">
                Organization ID / Registration Number
                <span className="field-optional"> (optional)</span>
              </label>
              <input className="login-input" type="text"
                placeholder={orgType === 'hospital' ? 'HOS-2024-01234' : orgType === 'government' ? 'GOV/MUN/2024' : 'REG-12345'}
                value={orgId} onChange={e => setOrgId(e.target.value)} />
            </div>
          )}

          {/* Email */}
          <div className="field-group">
            <label className="field-label">Email Address</label>
            <input className="login-input" type="email" placeholder="you@organization.com"
              value={email} onChange={e => setEmail(e.target.value)} required autoComplete="username" />
          </div>

          {/* Password */}
          <div className="field-group">
            <label className="field-label" style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span>
                Password
                {mode === 'signup' && <span className="field-optional"> (min 6 characters)</span>}
              </span>
              {mode === 'signin' && (
                <a href="#" onClick={(e) => { e.preventDefault(); alert("Please contact your organization administrator to reset your password."); }} 
                   style={{ fontSize: 11, color: accentColor, textDecoration: 'none', opacity: 0.8 }}>
                  Forgot password?
                </a>
              )}
            </label>
            <input className="login-input" type="password"
              placeholder={mode === 'signin' ? '••••••••' : 'Create a strong password'}
              value={password} onChange={e => setPassword(e.target.value)} required
              autoComplete={mode === 'signin' ? 'current-password' : 'new-password'} />
          </div>

          {/* Submit */}
          <button type="submit" className="login-submit" disabled={loading}
            style={{ background: `linear-gradient(135deg, ${accentColor}, ${accentColor}cc)` }}>
            {loading ? <span className="login-spinner" /> : (mode === 'signin' ? 'Sign In →' : 'Create Account →')}
          </button>
        </form>

        {/* Divider */}
        <div className="login-divider"><span>or continue with</span></div>

        {/* Google button — only rendered when inside provider */}
        {clientId ? (
          <GoogleLoginButton mode={mode} onStore={_store} onError={(msg) => setError(msg)} />
        ) : (
          <div className="google-unavailable">
            Google Sign-In not configured.
            Set <code>VITE_GOOGLE_CLIENT_ID</code> in the root <code>.env</code> file.
          </div>
        )}

        <p className="login-footer-text">
          By continuing, you agree to HRES's Terms of Service. All data is encrypted and handled securely.
        </p>
      </div>
    </div>
  );
}

// ── Root export — wraps in provider only when clientId is available ──
export function Login() {
  // Check token validity — redirect to dashboard if already logged in
  useEffect(() => {
    const token = localStorage.getItem('hres_token');
    if (!token) return;
    try {
      const payload = JSON.parse(atob(token.split('.')[1].replace(/-/g, '+').replace(/_/g, '/')));
      if (payload?.exp && Date.now() / 1000 < payload.exp - 60) {
        window.location.replace('/');
      } else {
        localStorage.removeItem('hres_token');
        localStorage.removeItem('hres_user');
      }
    } catch { /* invalid token — clear it */ localStorage.removeItem('hres_token'); }
  }, []);

  // Always wrap in GoogleOAuthProvider when clientId is set
  // GoogleLoginButton is ONLY rendered inside LoginForm when clientId is truthy
  if (clientId) {
    return (
      <GoogleOAuthProvider clientId={clientId}>
        <LoginForm />
      </GoogleOAuthProvider>
    );
  }
  return <LoginForm />;
}
