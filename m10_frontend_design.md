# FLARE Milestone 10: Scientific Intelligence Frontend Design

**Project**: FLARE — Scientific Intelligence Platform for Spacecraft Fire Safety  
**Milestone**: M10 — Evidence-Grounded Scientific Intelligence Layer  
**Document**: UI/UX Architecture, Component Hierarchy, and Visual Design  
**Version**: 1.0.0 (Authoritative Design)  
**Status**: DESIGN & SPECIFICATION ONLY  

---

## 1. UI Philosophy & Non-Disruptive Integration

The M10 Frontend Design builds directly upon the existing React 19 + Tailwind CSS 4 architecture in [frontend/src/](file:///c:/Users/anand/OneDrive/Documents/ChatGPT/FLARE/frontend/src/). Rather than reinventing existing layouts, M10 activates the currently placeholder workspace pages ([ResearchPage.tsx](file:///c:/Users/anand/OneDrive/Documents/ChatGPT/FLARE/frontend/src/pages/ResearchPage.tsx), [Overview.tsx](file:///c:/Users/anand/OneDrive/Documents/ChatGPT/FLARE/frontend/src/pages/Overview.tsx)) and introduces an **Evidence-Grounded Intelligence Assistant Pane** seamlessly embedded within the [DashboardLayout.tsx](file:///c:/Users/anand/OneDrive/Documents/ChatGPT/FLARE/frontend/src/layouts/DashboardLayout.tsx).

```mermaid
graph TD
    subgraph DashboardLayout [DashboardLayout.tsx]
        Nav[Sidebar Navigation]
        Header[Top Navigation Header]
        
        subgraph MainContentArea [Dynamic Route Outlet]
            OverviewPage[Overview.tsx (Active System Metrics)]
            ExpPage[Experiments.tsx (Observations Explorer)]
            IntelPage[ScientificIntelligence.tsx (New M10 View)]
            EvidencePage[EvidenceExplorer.tsx (Document Tree)]
        end
        
        subgraph SideDrawer [Slide-Over Evidence Drawer]
            DocViewer[Document Source Viewer]
            SealBadge[Cryptographic Seal Inspector]
            CellCoord[Tabular Row & Cell Provenance]
        end
    end

    Nav --> MainContentArea
    IntelPage --> SideDrawer
    EvidencePage --> SideDrawer
```

---

## 2. Core User Experience Components

### 2.1 The Scientific Query Interface (`ScientificQueryBar.tsx`)
- Located at the top of the Intelligence view and on the Overview dashboard.
- Features:
  - Natural-language search input with domain-specific autocomplete (suggests materials like "PMMA", "Nomex III", "SIBAL fabric", and variables like "initial O2", "airflow velocity", "CO drift").
  - Scientific domain mode selector: `Experimental Only (EM)` vs `Include Simulations (NS)`.
  - Fast-action suggestion chips:
    - *"What was the median oxygen depletion across BASS-II?"*
    - *"Show calibrated airflow velocities for steady scalar runs."*
    - *"Compare virgin burns vs re-burns for cast PMMA rods."*
    - *"Why was RQ_comb deferred in BASS-II analysis?"*

---

### 2.2 Evidence-Grounded Answer Canvas (`AnswerCanvas.tsx`)
- Renders the structured markdown response from the M10 execution pipeline.
- Features:
  - **Inline Interactive Citations**: Citations appear as clickable interactive badges (e.g., `[RESULT:ambient_initial_o2_median]`, `[DOC:71e792bf#p4]`). Clicking a badge opens the Slide-Over Evidence Drawer.
  - **Epistemological Badges**: Every paragraph or data point includes a color-coded epistemological pill:
    - `EM`: Emerald Green (`bg-emerald-950 text-emerald-300 border-emerald-800`)
    - `DQ`: Sky Blue (`bg-sky-950 text-sky-300 border-sky-800`)
    - `RT`: Slate Gray (`bg-slate-900 text-slate-300 border-slate-700`)
    - `NS`: Amber/Orange warning (`bg-amber-950 text-amber-300 border-amber-800`) — clearly labeled *"Numerical Simulation"*.
  - **Interactive Follow-Up Chips**: Suggested relevant follow-up questions generated deterministically from related M9 protocols.

---

### 2.3 Numerical Result Cards (`MetricResultCard.tsx`)
- Positioned alongside or below the narrative answer.
- Displays deterministic metrics computed by M9 with complete metrological precision:
  ```text
  +-------------------------------------------------------------------------+
  |  Baseline Pre-Ignition Oxygen Mole Fraction Median                      |
  |  Protocol: M9-P1-ENV-STATS  |  Sample Size: N = 129                     |
  |                                                                         |
  |             0.182 mol/mol  (18.2% by vol)                               |
  |             95% Order-Statistic CI: [0.175, 0.188] mol/mol              |
  |                                                                         |
  |  Quality Flags:  [ VALID_NUMERIC ]   [ FULL_SAMPLE_100_PCT ]            |
  |  Seal Status:    [ SHA-256 SEAL VERIFIED ]                              |
  +-------------------------------------------------------------------------+
  ```

---

### 2.4 Scientific Uncertainty & Limitation Alerts (`LimitationAlert.tsx`)
- Renders callouts directly below answers when experimental constraints apply.
- Displays:
  - **Sensor Drift Alert**: Informs the user when CO readings include signed negative drift ($-1, -2, -3\text{ ppm}$) resulting from microgravity sensor zero-drift.
  - **Hot-Wire Lag Alert**: Informs the user when airflow velocities are restricted to steady scalar runs due to the 60s hot-wire lag.
  - **Unvented Chamber Covariate Alert**: Informs the user that $CO_2$ (up to $1.9\%$) and $CO$ (up to $950\text{ ppm}$) accumulated inside the unvented chamber during daily testing blocks.
  - **Prohibited Concept Notice**: Displays a structured explanation if the user inquired about an ungrounded concept (e.g. Biot numbers or slab LOI regressions).

---

### 2.5 Slide-Over Evidence Inspector Drawer (`EvidenceInspectorDrawer.tsx`)
- Glides out from the right pane when any citation badge is clicked.
- Displays:
  - Document Title, Author, Publication Date.
  - Exact file location: `PSI-25_Experimental table_BASS-II.csv` (Line 45).
  - Cryptographic Verification: Computes and displays the SHA-256 digest with a green lock badge.
  - Original observation context: Displays the exact CSV row cells in a tabular snippet.
  - Download / View Original link.

---

## 3. Frontend Component Hierarchy

```text
frontend/src/
├── components/
│   ├── intelligence/
│   │   ├── ScientificQueryBar.tsx         # Natural-language query input & suggestion chips
│   │   ├── AnswerCanvas.tsx               # Markdown narrative with interactive citation pills
│   │   ├── MetricResultCard.tsx           # Deterministic M9 numerical cards with CI & units
│   │   ├── LimitationAlert.tsx            # Quality flags, sensor drift, & chamber alerts
│   │   ├── EpistemologicalTag.tsx         # EM, NS, DQ, RT, UN color badges
│   │   ├── EvidenceInspectorDrawer.tsx    # Slide-over pane showing authentic source evidence
│   │   ├── ChartContainer.tsx             # Boxplots, histograms, and range bars
│   │   └── FollowUpSuggestions.tsx        # Next logical research queries
│   └── EmptyState.tsx                     # Existing reusable empty state component
├── pages/
│   ├── Overview.tsx                       # Dashboard overview with quick query bar
│   ├── ScientificIntelligence.tsx         # Dedicated M10 interactive research workspace
│   ├── ResearchPage.tsx                   # Existing generic research wrapper
│   └── Settings.tsx                       # API endpoint & auth configuration
├── services/
│   ├── api.ts                             # Extended fetch client with M10 intelligence endpoints
│   └── sse.ts                             # Server-Sent Events client for streaming turns
└── types/
    ├── api.ts                             # API response types
    └── intelligence.ts                    # M10 query, citation, and card types
```

---

## 4. UI Theme & Style Architecture

The interface uses the existing Tailwind CSS 4 dark aerospace aesthetic already established in FLARE:
- **Backgrounds**: Slate-950 (`#020617`), Slate-900 (`#0f172a`), Slate-800 (`#1e293b`).
- **Borders & Dividers**: Slate-700 (`#334155`), Slate-800 (`#1e293b`).
- **Typography**: Inter / System Sans for prose; JetBrains Mono / SF Mono for numerical values, units, citations, and formulas.
- **Accents**:
  - Verification & Safety: Emerald-400 / Emerald-500.
  - Derived & Analytical: Sky-400 / Sky-500.
  - Simulations & Warnings: Amber-400 / Amber-500.
  - Prohibitions & Errors: Rose-400 / Rose-500.
