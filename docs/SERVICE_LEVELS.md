# SLI, SLO, SLA and CD status

The commit-candidate pipeline measures p95 latency, error rate, and provenance coverage for the versioned deterministic retrieval workload. Thresholds live in service-levels.json and failure blocks the candidate.

These are build SLOs, not a customer SLA. SLA status is not_offered because NeuCLX has no declared hosted production service or customer contract. CD is not_configured because no deployment target exists. Neither status may be presented as successful deployment.
