import { useState } from 'react';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import { getToken } from './services/api';

export default function App() {
  const [authed, setAuthed] = useState(() => !!getToken());

  return authed
    ? <Dashboard onLogout={() => setAuthed(false)} />
    : <Login    onLogin={() => setAuthed(true)} />;
}
