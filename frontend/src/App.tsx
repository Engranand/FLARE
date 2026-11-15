import { lazy, Suspense } from 'react';
import { Link, Navigate, Route, Routes } from 'react-router-dom';
import { DashboardLayout } from './layouts/DashboardLayout';
import { Overview } from './pages/Overview';
import { State } from './components/ScientificUI';
const Explorer=lazy(()=>import('./pages/Explorer').then(m=>({default:m.Explorer})));
const Experiments=lazy(()=>import('./pages/Experiments').then(m=>({default:m.Experiments})));
const Atmosphere=lazy(()=>import('./pages/AnalysisPages').then(m=>({default:m.Atmosphere})));
const FlameBehaviour=lazy(()=>import('./pages/AnalysisPages').then(m=>({default:m.FlameBehaviour})));
const ResearchGaps=lazy(()=>import('./pages/AnalysisPages').then(m=>({default:m.ResearchGaps})));
const Comparison=lazy(()=>import('./pages/Comparison').then(m=>({default:m.Comparison})));
const EvidenceExplorer=lazy(()=>import('./pages/EvidenceExplorer').then(m=>({default:m.EvidenceExplorer})));
const Assistant=lazy(()=>import('./pages/Assistant').then(m=>({default:m.Assistant})));
const Settings=lazy(()=>import('./pages/Settings').then(m=>({default:m.Settings})));
export default function App(){return <Suspense fallback={<State loading/>}><Routes><Route element={<DashboardLayout/>}><Route index element={<Navigate to="/overview" replace/>}/><Route path="overview" element={<Overview/>}/><Route path="explorer" element={<Explorer/>}/><Route path="experiments" element={<Experiments/>}/><Route path="atmosphere" element={<Atmosphere/>}/><Route path="flame-behaviour" element={<FlameBehaviour/>}/><Route path="comparison" element={<Comparison/>}/><Route path="compare" element={<Navigate to="/comparison" replace/>}/><Route path="evidence" element={<EvidenceExplorer/>}/><Route path="assistant" element={<Assistant/>}/><Route path="research-gaps" element={<ResearchGaps/>}/><Route path="settings" element={<Settings/>}/><Route path="*" element={<><h1>Page not found</h1><Link to="/overview">Return to overview</Link></>}/></Route></Routes></Suspense>}
