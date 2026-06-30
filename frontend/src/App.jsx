import { useState } from 'react';
import Login    from './pages/Login';
import Signup   from './pages/Signup';
import Dashboard from './pages/Dashboard';
import { getToken } from './services/api';

export default function App() {
  // view: 'login' | 'signup' | 'dashboard'
  const [view, setView] = useState(() => (getToken() ? 'dashboard' : 'login'));

  if (view === 'dashboard')
    return <Dashboard onLogout={() => setView('login')} />;

  if (view === 'signup')
    return <Signup onGoToLogin={() => setView('login')} />;

  // default: login
  return <Login onLogin={() => setView('dashboard')} onGoToSignup={() => setView('signup')} />;
}
