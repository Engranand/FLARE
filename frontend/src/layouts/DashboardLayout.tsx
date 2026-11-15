import { useState } from 'react';
import { NavLink, Outlet, useLocation, useNavigate } from 'react-router-dom';
import { Flame, LayoutDashboard, FlaskConical, GitCompareArrows, BookOpen, ScanSearch, Settings, Menu, PanelLeftClose, Search, Sun, Moon, Wind, Microscope, MessageSquare, Database, RefreshCw } from 'lucide-react';
import { useHealth } from '../hooks/useHealth';
import { WorkstationProvider } from '../components/WorkstationProvider';
const groups = [
  { title: 'WORKSPACE', links: [['/overview','Overview',LayoutDashboard],['/explorer','Scientific Explorer',Microscope],['/experiments','Experiment Database',Database]] },
  { title: 'ANALYSIS', links: [['/atmosphere','Atmosphere Analysis',Wind],['/flame-behaviour','Flame Behaviour',Flame],['/comparison','Condition Comparison',GitCompareArrows]] },
  { title: 'INTELLIGENCE', links: [['/evidence','Evidence Explorer',BookOpen],['/assistant','AI Research Assistant',MessageSquare],['/research-gaps','Research Gaps',ScanSearch]] },
  { title: 'SYSTEM', links: [['/settings','Settings',Settings]] },
] as const;
export function DashboardLayout() {
  const [open,setOpen] = useState(false); const [collapsed,setCollapsed] = useState(false); const [search,setSearch] = useState('');
  const [light,setLight] = useState(() => localStorage.getItem('flare-theme') === 'light');
  const {status,retry} = useHealth(); const location = useLocation(); const navigate = useNavigate();
  const title = groups.flatMap(g => [...g.links]).find(l => l[0] === location.pathname)?.[1] ?? 'Workspace';
  const theme = () => { setLight(v => !v); localStorage.setItem('flare-theme', light ? 'dark' : 'light'); };
  return <WorkstationProvider><div className={`app-shell ${collapsed ? 'collapsed' : ''} ${light ? 'light' : ''}`}>
    <a className="skip-link" href="#main-content">Skip to content</a>
    <aside className={`sidebar ${open ? 'is-open' : ''}`}><NavLink className="brand" to="/overview"><span className="brand-mark"><Flame size={25} /></span><span className="nav-copy">FLARE<small>Scientific Intelligence Platform</small></span></NavLink>
      <nav aria-label="Main navigation">{groups.map(g => <div className="nav-group" key={g.title}><div className="nav-label">{g.title}</div>{g.links.map(([path,label,Icon]) => <NavLink key={path} to={path} title={label} onClick={() => setOpen(false)}><Icon size={18} /><span className="nav-copy">{label}</span></NavLink>)}</div>)}</nav>
      <div className="sidebar-footer"><FlaskConical size={18} /><span className="nav-copy">Evidence before inference<small>Spacecraft fire safety · M10.6</small></span></div>
      <button className="collapse-control" onClick={() => setCollapsed(!collapsed)} aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}><PanelLeftClose size={17} /><span className="nav-copy">Collapse sidebar</span></button>
    </aside>
    <div className="workspace"><header className="topbar"><div className="breadcrumbs"><button className="icon-button mobile-menu" onClick={() => setOpen(!open)} aria-label="Toggle navigation" aria-expanded={open}><Menu size={20}/></button><span>Workspace</span><span>/</span><strong>{title}</strong></div><div className="top-actions"><form className="global-search" onSubmit={e => { e.preventDefault(); navigate(`/explorer?q=${encodeURIComponent(search)}`); }}><Search size={15}/><input aria-label="Search scientific records" placeholder="Search records…" value={search} onChange={e => setSearch(e.target.value)}/></form><button className="icon-button" aria-label="Toggle appearance" onClick={theme}>{light ? <Moon size={18}/> : <Sun size={18}/>}</button><span className="connection">API {status}</span><button className="icon-button" aria-label="Retry API connection" onClick={retry}><RefreshCw size={14}/></button></div></header>
    <main id="main-content" tabIndex={-1}><Outlet /></main><footer className="workspace-footer"><span>FLARE / NASA source-grounded research</span><span>Observed · Derived · Traceable</span></footer></div>
  </div></WorkstationProvider>;
}
