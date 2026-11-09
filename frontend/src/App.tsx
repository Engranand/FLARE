import { Link, Route, Routes } from 'react-router-dom';
import { DashboardLayout } from './layouts/DashboardLayout';
import { Overview } from './pages/Overview';
import { ResearchPage } from './pages/ResearchPage';
import { Settings } from './pages/Settings';

export default function App() {
  return <Routes><Route element={<DashboardLayout />}>
    <Route index element={<Overview />} />
    <Route path="experiments" element={<ResearchPage title="Experiments" description="Explore experimental conditions and source-traceable records." emptyTitle="No experiments ingested" message="Verified BASS-II experimental records will appear here after ingestion. No sample records have been added." />} />
    <Route path="compare" element={<ResearchPage title="Compare Experiments" description="A future workspace for comparing verified experimental conditions." emptyTitle="Comparison awaits verified records" message="Experiment selection and comparison will be implemented after the source data and its units are validated." />} />
    <Route path="evidence" element={<ResearchPage title="Evidence Explorer" description="Inspect the scientific sources behind the research." emptyTitle="No evidence indexed" message="Source documents and traceable evidence references will appear after source review. Document indexing is not implemented yet." />} />
    <Route path="research-gaps" element={<ResearchPage title="Research Gaps" description="A future workspace for evidence-supported research questions." emptyTitle="No research gaps assessed" message="Research gap analysis has not been implemented. Any future assessment must be grounded in verified evidence and explicit limitations." />} />
    <Route path="settings" element={<Settings />} />
    <Route path="*" element={<><h1>Page not found</h1><p>This workspace page does not exist.</p><Link to="/">Return to overview</Link></>} />
  </Route></Routes>;
}
