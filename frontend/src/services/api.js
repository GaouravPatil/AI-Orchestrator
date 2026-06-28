import axios from 'axios';

// ── Base URLs ────────────────────────────────────────────────────────
const AUTH_URL  = 'http://localhost:8080';
const K8S_URL   = 'http://localhost:8001';
const AI_URL    = 'http://localhost:8002';
const MON_URL   = 'http://localhost:8003';

// ── Token helpers ────────────────────────────────────────────────────
export const getToken  = ()       => localStorage.getItem('token');
export const setToken  = (t)      => localStorage.setItem('token', t);
export const clearToken = ()      => localStorage.removeItem('token');
export const getUser   = ()       => {
  const raw = localStorage.getItem('user');
  try { return raw ? JSON.parse(raw) : null; } catch { return null; }
};
export const setUser   = (u)      => localStorage.setItem('user', JSON.stringify(u));

// ── Axios instance with auto-attach token ────────────────────────────
const authHeader = () => ({ Authorization: `Bearer ${getToken()}` });

// ── Auth ─────────────────────────────────────────────────────────────
export const login = async (email, password) => {
  const params = new URLSearchParams({ username: email, password });
  // Try k8s_service /token (same DB, same JWT)
  const res = await axios.post(`${K8S_URL}/token`, params, {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  });
  return res.data; // { access_token, token_type }
};

// ── K8s ──────────────────────────────────────────────────────────────
export const fetchNodes = () =>
  axios.get(`${K8S_URL}/k8s/nodes`, { headers: authHeader() }).then(r => r.data);

export const fetchPods = () =>
  axios.get(`${K8S_URL}/k8s/pods`, { headers: authHeader() }).then(r => r.data);

export const fetchDeployments = () =>
  axios.get(`${K8S_URL}/k8s/deployments`, { headers: authHeader() }).then(r => r.data);

export const fetchNamespaces = () =>
  axios.get(`${K8S_URL}/k8s/namespaces`, { headers: authHeader() }).then(r => r.data);

export const fetchServices = (ns = 'default') =>
  axios.get(`${K8S_URL}/k8s/services?namespace=${ns}`, { headers: authHeader() }).then(r => r.data);

export const scaleDeployment = (name, replicas, namespace = 'default') =>
  axios.put(`${K8S_URL}/k8s/scale`, { name, replicas, namespace }, { headers: authHeader() }).then(r => r.data);

// ── AI ───────────────────────────────────────────────────────────────
export const sendChat = (message, conversation_id = null, namespace = 'default') =>
  axios.post(`${AI_URL}/ai/chat`,
    { message, conversation_id, namespace },
    { headers: authHeader(), timeout: 180000 }
  ).then(r => r.data);

// ── Monitoring ───────────────────────────────────────────────────────
export const fetchClusterHealth = () =>
  axios.get(`${MON_URL}/monitor/health`, { headers: authHeader() }).then(r => r.data)
    .catch(() => null);

export const fetchAlerts = () =>
  axios.get(`${MON_URL}/monitor/alerts`, { headers: authHeader() }).then(r => r.data)
    .catch(() => ({ data: [] }));
