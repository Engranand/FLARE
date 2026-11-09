import { API_BASE_URL } from '../services/api';

export function Settings() {
  return <><div className="eyebrow">WORKSPACE CONFIGURATION</div><h1>Settings</h1><p className="page-intro">Connection details for this workspace. Configuration is managed through local environment files.</p><section className="settings-card"><h2>API connection</h2><dl><dt>Configured API base URL</dt><dd><code>{API_BASE_URL}</code></dd><dt>Configuration variable</dt><dd><code>VITE_API_BASE_URL</code></dd></dl><p className="muted">Update frontend/.env and restart Vite to change the connection. Frontend environment values are public; never place credentials here.</p></section></>;
}
