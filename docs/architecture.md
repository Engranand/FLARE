# Architecture

## Milestone 1 implementation

The monorepo has two independently runnable services, with no database or external API dependency at runtime.

The React entry point installs BrowserRouter. App defines routes under DashboardLayout, whose Outlet renders each page. The layout owns responsive navigation, the shared connection indicator and error banner. Overview describes only the target investigation. ResearchPage and EmptyState supply honest, reusable empty states. Settings displays the public API URL without pretending to persist settings.

The useHealth hook handles loading, cancellation, timeout, errors and manual retry. The centralized services/api client reads VITE_API_BASE_URL, performs GET /health and validates the JSON shape before returning a typed HealthResponse. No credentials are sent.

FastAPI's create_app factory accepts explicit settings for isolated tests, configures CORS and mounts a versioned router. Pydantic Settings centralizes environment parsing. API response schemas explicitly limit output to safe fields. The root endpoint gives API metadata; api/routes owns health and system information.

## Request flow

Browser -> useHealth -> API client -> GET /api/v1/health -> API router -> typed JSON -> connection status.

The frontend origin must match FRONTEND_ORIGIN exactly. The API base includes the router prefix. A Connected result only confirms process health, not ingestion or scientific readiness.

## Future pipeline (not implemented)

Official source review -> acquisition manifest and checksums -> immutable raw files -> parser and schema validation -> normalized records -> evidence references -> reviewed analysis.

Raw and processed files are excluded from Git. Future manifests must preserve original source links, access conditions, retrieval dates, hashes, parser version, units and validation outcomes. No acquisition is performed in this milestone.

models is reserved for persistence decisions, services for application use cases, ingestion for acquisition/normalization, analytics for reproducible analysis, and evidence for provenance. rag is only a reserved boundary for a later approved milestone; no retrieval or inference exists. Add abstractions when actual use cases require them.

Scientific analysis must preserve units, uncertainty, missingness and scope limits; findings need auditable evidence links. The proposed dictionary is not a validated NASA schema.

## Verification boundaries

API tests exercise startup, schemas, configuration and CORS using an in-process client. Frontend client tests exercise successful responses, malformed responses, HTTP errors and network errors. Type checks and builds do not establish browser accessibility, scientific validity or production readiness. Authentication, deployment hardening and data storage are outside Milestone 1.
