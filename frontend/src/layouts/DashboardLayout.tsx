import { useState } from 'react';
import { NavLink, Outlet } from 'react-router-dom';
import { Flame, LayoutDashboard, FlaskConical, GitCompareArrows, BookOpen, ScanSearch, Settings, Menu, X, RefreshCw } from 'lucide-react';
import { useHealth } from '../hooks/useHealth';

const navigation = [
  { path: '/', label: 'Overview', icon: LayoutDashboard },
  { path: '/experiments', label: 'Experiments', icon: FlaskConical },
  { path: '/compare', label: 'Compare Experiments', icon: GitCompareArrows },
  { path: '/evidence', label: 'Evidence Explorer', icon: BookOpen },
  { path: '/research-gaps', label: 'Research Gaps', icon: ScanSearch },
  { path: '/settings', label: 'Settings', icon: Settings },
];

export function DashboardLayout() {
  const [open, setOpen] = useState(false);
  const { status, error, retry } = useHealth();
  return <div className="app-shell">
    <a className="skip-link" href="#main-content">Skip to content</a>
    <aside className={`sidebar ${open ? 'is-open' : ''}`} id="sidebar">
      <NavLink to="/" className="brand" onClick={() => setOpen(false)}><Flame size={28} aria-hidden="true" /><span>FLARE<small>SCIENTIFIC INTELLIGENCE</small></span></NavLink>
      <div className="nav-label">RESEARCH WORKSPACE</div>
      <nav aria-label="Main navigation">{navigation.map(({ path, label, icon: Icon }) => <NavLink key={path} to={path} end={path === '/'} onClick={() => setOpen(false)}><Icon size={18} aria-hidden="true" />{label}</NavLink>)}</nav>
      <div className="sidebar-footer"><span className="badge">Milestone 01</span><p>Spacecraft fire safety<br />Foundation workspace</p></div>
    </aside>
    <div className="workspace">
      <header className="topbar"><div className="header-left"><button className="menu-button icon-button" aria-label={open ? 'Close navigation' : 'Open navigation'} aria-expanded={open} aria-controls="sidebar" onClick={() => setOpen(!open)}>{open ? <X size={20} /> : <Menu size={20} />}</button><span>Research workspace <span className="header-divider">/</span> <span className="muted">BASS-II</span></span></div><div className="connection" role="status"><span className={`status-dot ${status.toLowerCase()}`} />API {status}<button className="icon-button" onClick={retry} disabled={status === 'Checking'} aria-label="Recheck backend connection"><RefreshCw size={14} /></button></div></header>
      {error && <div className="error-banner" role="alert">Backend unavailable: {error} <span>Start the backend, then recheck the connection above.</span></div>}
      <main id="main-content" tabIndex={-1}><Outlet /></main>
      <footer className="workspace-footer">FLARE · Scientific Intelligence Platform for Spacecraft Fire Safety<span>No experimental data ingested</span></footer>
    </div>
  </div>;
}
