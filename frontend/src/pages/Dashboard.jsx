import { useState, useEffect, useCallback } from 'react';
import JarvisBackground from '../components/JarvisBackground';
import Sidebar from '../components/Sidebar';
import AIChat from '../components/AIChat';
import { getUser, clearToken, fetchNodes, fetchPods, fetchDeployments, fetchAlerts } from '../services/api';
import '../styles/Dashboard.css';

/* ── Stat Card ──────────────────────────────────────────────────────── */
function StatCard({ label, value, sub, color, icon, loading }) {
  return (
    <div className={`stat-card glass animate-fade-up`} style={{ '--accent': color }}>
      <div className="stat-icon" style={{ background: `${color}18`, borderColor: `${color}30` }}>
        {icon}
      </div>
      <div className="stat-body">
        <span className="stat-label">{label}</span>
        <span className="stat-value font-orbitron" style={{ color }}>
          {loading ? <span className="skeleton-val" /> : value}
        </span>
        <span className="stat-sub">{sub}</span>
      </div>
      <div className="stat-glow" style={{ background: color }} />
    </div>
  );
}

/* ── Resource Table ─────────────────────────────────────────────────── */
function ResourceTable({ title, rows, columns, loading, emptyMsg }) {
  return (
    <div className="resource-table glass animate-fade-up">
      <div className="resource-table-header">
        <h3 className="font-orbitron">{title}</h3>
        <span className="badge badge-cyan">{rows?.length ?? 0}</span>
      </div>
      <div className="resource-table-body">
        {loading ? (
          Array.from({ length: 3 }).map((_, i) => (
            <div key={i} className="table-row skeleton-row">
              {columns.map((_, j) => <span key={j} className="skeleton-cell" />)}
            </div>
          ))
        ) : rows?.length === 0 ? (
          <div className="table-empty">{emptyMsg ?? 'No data'}</div>
        ) : rows?.map((row, i) => (
          <div key={i} className="table-row">
            {columns.map(col => (
              <span key={col.key} className={`table-cell ${col.cls ?? ''}`} style={{ flex: col.flex ?? 1 }}>
                {col.render ? col.render(row) : row[col.key]}
              </span>
            ))}
          </div>
        ))}
      </div>
    </div>
  );
}

/* ── Status badge helper ────────────────────────────────────────────── */
const statusBadge = (status) => {
  const s = (status ?? '').toLowerCase();
  const cls = s === 'ready' || s === 'running' ? 'badge-green'
            : s === 'pending'                   ? 'badge-orange'
            : s === 'failed'  || s === 'error'  ? 'badge-red'
            : 'badge-cyan';
  return <span className={`badge ${cls}`}><span className="dot" />{status}</span>;
};

/* ── Views ──────────────────────────────────────────────────────────── */
const VIEWS = ['overview', 'nodes', 'pods', 'deployments', 'ai', 'alerts'];

export default function Dashboard({ onLogout }) {
  const user = getUser();
  const [activeView, setActiveView] = useState('overview');
  const [data, setData]   = useState({ nodes: null, pods: null, deployments: null, alerts: null });
  const [loading, setLoading] = useState(true);
  const [greeting] = useState(() => {
    const h = new Date().getHours();
    return h < 12 ? 'Good Morning' : h < 18 ? 'Good Afternoon' : 'Good Evening';
  });

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [nodes, pods, deployments, alerts] = await Promise.allSettled([
        fetchNodes(), fetchPods(), fetchDeployments(), fetchAlerts(),
      ]);
      setData({
        nodes:       nodes.status === 'fulfilled'       ? nodes.value?.data ?? []       : [],
        pods:        pods.status === 'fulfilled'        ? pods.value?.data ?? []        : [],
        deployments: deployments.status === 'fulfilled' ? deployments.value?.data ?? [] : [],
        alerts:      alerts.status === 'fulfilled'      ? alerts.value?.data ?? []      : [],
      });
    } finally { setLoading(false); }
  }, []);

  useEffect(() => { load(); }, [load]);

  const handleLogout = () => { clearToken(); onLogout(); };

  /* ── Derived counts ── */
  const nodesReady  = data.nodes?.filter(n => n.status === 'Ready').length ?? 0;
  const podsRunning = data.pods?.filter(p => (p.status ?? '').toLowerCase() === 'running').length ?? 0;
  const alertCount  = data.alerts?.length ?? 0;

  /* ── Column defs ── */
  const nodeCols = [
    { key: 'name',           flex: 2, cls: 'font-mono text-cyan' },
    { key: 'role',           flex: 1, cls: 'text-muted' },
    { key: 'status',         flex: 1, render: r => statusBadge(r.status) },
    { key: 'kubelet_version',flex: 1, cls: 'font-mono text-muted', render: r => r.kubelet_version ?? '-' },
  ];
  const podCols = [
    { key: 'name',      flex: 3, cls: 'font-mono text-sm' },
    { key: 'namespace', flex: 1, cls: 'text-muted' },
    { key: 'status',    flex: 1, render: r => statusBadge(r.status) },
    { key: 'node',      flex: 2, cls: 'text-muted text-sm', render: r => r.node ?? '-' },
  ];
  const deployCols = [
    { key: 'name',      flex: 2, cls: 'font-mono text-cyan' },
    { key: 'namespace', flex: 1, cls: 'text-muted' },
    { key: 'ready',     flex: 1, render: r => <span className="badge badge-green">{r.ready ?? r.replicas ?? '-'} ready</span> },
    { key: 'image',     flex: 2, cls: 'text-muted text-sm', render: r => (r.image ?? '-').split('/').pop() },
  ];

  return (
    <div className="dashboard-root">
      <JarvisBackground intensity={0.6} />

      <Sidebar
        active={activeView}
        onNav={setActiveView}
        user={user}
        onLogout={handleLogout}
      />

      <main className="dashboard-main">
        {/* ── Top bar ── */}
        <header className="dash-topbar">
          <div className="dash-topbar-left">
            <div className="welcome-block">
              <p className="welcome-greeting">{greeting},</p>
              <h1 className="welcome-name font-orbitron gradient-text">
                {user?.email?.split('@')[0] ?? 'Commander'}
              </h1>
            </div>
          </div>
          <div className="dash-topbar-right">
            <span className="badge badge-green animate-glow"><span className="dot" />Cluster Online</span>
            <button className="btn btn-ghost refresh-btn" onClick={load} title="Refresh">
              <svg width="14" height="14" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                <path strokeLinecap="round" d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0l3.181 3.183a8.25 8.25 0 0013.803-3.7M4.031 9.865a8.25 8.25 0 0113.803-4.566l3.181 3.182m0-4.991v4.99" />
              </svg>
              Refresh
            </button>
            <div className="topbar-time font-mono">
              {new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })}
            </div>
          </div>
        </header>

        {/* ── Content ── */}
        <div className="dash-content">

          {/* OVERVIEW */}
          {(activeView === 'overview') && (
            <div className="view stagger">
              {/* Stats row */}
              <div className="stats-row stagger">
                <StatCard label="NODES"       value={`${nodesReady}/${data.nodes?.length ?? 0}`} sub="Ready"     color="var(--cyan)"   loading={loading} icon={<svg width="20" height="20" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.5"><path strokeLinecap="round" d="M5.25 14.25h13.5m-13.5 0a3 3 0 01-3-3m3 3a3 3 0 100 6h13.5a3 3 0 100-6m-16.5-3a3 3 0 013-3h13.5a3 3 0 013 3m-19.5 0a4.5 4.5 0 01.9-2.7L5.737 5.1a3.375 3.375 0 012.7-1.35h7.126c1.062 0 2.062.5 2.7 1.35l2.587 3.45a4.5 4.5 0 01.9 2.7m0 0a3 3 0 01-3 3m0 3h.008v.008h-.008v-.008z" /></svg>} />
                <StatCard label="PODS"        value={`${podsRunning}/${data.pods?.length ?? 0}`} sub="Running"   color="var(--green)"  loading={loading} icon={<svg width="20" height="20" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.5"><path strokeLinecap="round" d="M20.25 6.375c0 2.278-3.694 4.125-8.25 4.125S3.75 8.653 3.75 6.375m16.5 0c0-2.278-3.694-4.125-8.25-4.125S3.75 4.097 3.75 6.375m16.5 0v11.25c0 2.278-3.694 4.125-8.25 4.125s-8.25-1.847-8.25-4.125V6.375m16.5 2.625c0 2.278-3.694 4.125-8.25 4.125s-8.25-1.847-8.25-4.125" /></svg>} />
                <StatCard label="DEPLOYMENTS" value={data.deployments?.length ?? 0}              sub="Total"     color="var(--blue)"   loading={loading} icon={<svg width="20" height="20" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.5"><path strokeLinecap="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 013 19.875v-6.75zM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V8.625z" /></svg>} />
                <StatCard label="ALERTS"      value={alertCount}                                  sub={alertCount === 0 ? 'All clear' : 'Active'} color={alertCount > 0 ? 'var(--orange)' : 'var(--green)'} loading={loading} icon={<svg width="20" height="20" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.5"><path strokeLinecap="round" d="M14.857 17.082a23.848 23.848 0 005.454-1.31A8.967 8.967 0 0118 9.75v-.7V9A6 6 0 006 9v.75a8.967 8.967 0 01-2.312 6.022c1.733.64 3.56 1.085 5.455 1.31m5.714 0a24.255 24.255 0 01-5.714 0m5.714 0a3 3 0 11-5.714 0" /></svg>} />
              </div>

              {/* Two-panel: nodes + AI */}
              <div className="overview-grid">
                <div className="overview-left stagger">
                  <ResourceTable title="NODES"       rows={data.nodes}       columns={nodeCols}    loading={loading} emptyMsg="No nodes found" />
                  <ResourceTable title="DEPLOYMENTS" rows={data.deployments} columns={deployCols}  loading={loading} emptyMsg="No deployments" />
                </div>
                <div className="overview-right">
                  <AIChat />
                </div>
              </div>
            </div>
          )}

          {/* NODES */}
          {activeView === 'nodes' && (
            <div className="view stagger">
              <div className="view-header">
                <h2 className="font-orbitron gradient-text">CLUSTER NODES</h2>
                <span className="badge badge-green"><span className="dot" />{data.nodes?.length ?? 0} nodes</span>
              </div>
              <div className="node-grid stagger">
                {loading ? Array.from({length: 3}).map((_,i) => <div key={i} className="node-card glass skeleton-card animate-fade-up" />) :
                data.nodes?.map((n, i) => (
                  <div key={i} className="node-card glass animate-fade-up">
                    <div className="node-card-header">
                      <svg width="16" height="16" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.5"><path strokeLinecap="round" d="M5.25 14.25h13.5m-13.5 0a3 3 0 01-3-3m3 3a3 3 0 100 6h13.5a3 3 0 100-6m-16.5-3a3 3 0 013-3h13.5a3 3 0 013 3" /></svg>
                      <span className="font-mono node-name">{n.name}</span>
                      {statusBadge(n.status)}
                    </div>
                    <div className="node-card-grid">
                      {[
                        ['Role',       n.role ?? '-'],
                        ['Version',    n.kubelet_version ?? '-'],
                        ['OS',         n.os ?? '-'],
                        ['Arch',       n.architecture ?? '-'],
                      ].map(([k, v]) => (
                        <div key={k} className="node-stat">
                          <span className="node-stat-key">{k}</span>
                          <span className="node-stat-val font-mono">{v}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* PODS */}
          {activeView === 'pods' && (
            <div className="view stagger">
              <div className="view-header">
                <h2 className="font-orbitron gradient-text">PODS</h2>
                <span className="badge badge-green"><span className="dot" />{podsRunning} running</span>
              </div>
              <ResourceTable title="ALL PODS" rows={data.pods} columns={podCols} loading={loading} emptyMsg="No pods found" />
            </div>
          )}

          {/* DEPLOYMENTS */}
          {activeView === 'deployments' && (
            <div className="view stagger">
              <div className="view-header">
                <h2 className="font-orbitron gradient-text">DEPLOYMENTS</h2>
                <span className="badge badge-cyan">{data.deployments?.length ?? 0} total</span>
              </div>
              <ResourceTable title="ALL DEPLOYMENTS" rows={data.deployments} columns={deployCols} loading={loading} emptyMsg="No deployments" />
            </div>
          )}

          {/* AI CHAT */}
          {activeView === 'ai' && (
            <div className="view view-ai">
              <AIChat />
            </div>
          )}

          {/* ALERTS */}
          {activeView === 'alerts' && (
            <div className="view stagger">
              <div className="view-header">
                <h2 className="font-orbitron gradient-text">ALERTS</h2>
                {alertCount > 0
                  ? <span className="badge badge-orange"><span className="dot" />{alertCount} active</span>
                  : <span className="badge badge-green"><span className="dot" />All clear</span>}
              </div>
              {loading ? (
                <div className="table-empty">Loading…</div>
              ) : alertCount === 0 ? (
                <div className="alerts-empty glass">
                  <svg width="48" height="48" fill="none" viewBox="0 0 24 24" stroke="var(--green)" strokeWidth="1">
                    <path strokeLinecap="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <p>No active alerts. Cluster is healthy.</p>
                </div>
              ) : (
                <div className="alerts-list stagger">
                  {data.alerts.map((a, i) => (
                    <div key={i} className="alert-item glass animate-fade-up">
                      <div className={`alert-dot ${a.severity === 'critical' ? 'badge-red' : 'badge-orange'}`} />
                      <div className="alert-body">
                        <span className="alert-name">{a.name ?? a.alert_name ?? 'Alert'}</span>
                        <span className="alert-msg text-muted">{a.message ?? a.description ?? ''}</span>
                      </div>
                      <span className={`badge ${a.severity === 'critical' ? 'badge-red' : 'badge-orange'}`}>{a.severity ?? 'warning'}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
