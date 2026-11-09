import { Database } from 'lucide-react';

export function EmptyState({ title, children }: { title: string; children: React.ReactNode }) {
  return <section className="empty-state"><div className="empty-icon"><Database size={24} aria-hidden="true" /></div><h2>{title}</h2><p>{children}</p><span className="badge">Awaiting verified data</span></section>;
}
