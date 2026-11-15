# M10.6 implementation map

The existing React/Vite application and FastAPI/SQLAlchemy application remain the entry points. No migration, ingestion, original dataset, or M9 calculation changes are required.

| Workspace | Existing authority | Necessary presentation adapter |
|---|---|---|
| Overview | M9 verified result tool; database catalog | GET workstation/summary; GET workstation/science |
| Explorer / inspector | observation, source_record, source_field, evidence_reference | GET workstation/observations with bounded pagination and exact filters |
| Experiments | investigation and source_document | summary catalog with actual record coverage |
| Atmosphere / flame | authenticated M9 source loader and P1–P4 classifiers | science distributions, exclusions and specimen grouping |
| Comparison | M9 median and quartile routines; authenticated BASS-II population | POST workstation/comparison, within one source and investigation only |
| Evidence | M10.4 PostgreSQL full-text retrieval tool | GET workstation/evidence, plus passage detail navigation |
| Assistant | POST intelligence/execute, synthesize=true | Existing M10.2 plan, M10.3 read-only execution, M10.5 validation |
| Research gaps | M9 exclusion classifications, source metadata | science quality partitions, explicitly separate proposed questions |
| Settings | health and system/info | Local appearance preference; real connection status |

All new database reads use the configured application engine, explicit read-only transactions, statement timeouts, bound values and fixed SQL. Existing application has no HTTP account authentication; this milestone does not invent identities or claim new account security. No arbitrary SQL or source path is accepted. M9 charts use the existing SHA-256 authenticated original loader; only chart binning is new. Persisted quantitative claims continue through the seal-verifying tool. Chart populations and persisted analytical results are labeled separately.
