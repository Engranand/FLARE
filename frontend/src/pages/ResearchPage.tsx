import { EmptyState } from '../components/EmptyState';

export function ResearchPage({ title, description, emptyTitle, message }: { title: string; description: string; emptyTitle: string; message: string }) {
  return <><div className="eyebrow">RESEARCH WORKSPACE</div><h1>{title}</h1><p className="page-intro">{description}</p><EmptyState title={emptyTitle}>{message}</EmptyState></>;
}
