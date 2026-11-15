import { createContext, useContext } from 'react';
import type { ReactNode } from 'react';
import { useResource } from '../hooks/useResource';
import { payload } from '../services/workstation';
import type { Summary, Science } from '../services/workstation';
const Context = createContext<ReturnType<typeof useData> | null>(null);
function useData() { const summary = useResource<Summary>(s => payload('/summary', s), 'summary'); const science = useResource<Science>(s => payload('/science', s), 'science'); return { summary, science }; }
export function WorkstationProvider({ children }: { children: ReactNode }) { const value = useData(); return <Context.Provider value={value}>{children}</Context.Provider>; }
export function useWorkstation() { const context = useContext(Context); if (!context) throw new Error('Workstation provider missing'); return context; }
