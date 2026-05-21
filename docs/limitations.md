# Limitations

- The starter catalog is for evaluator bootstrap. Production deployments would replace it with the retailer's real catalog and inventory feed.
- There is no canned recall-source data. Scan data comes from Exa Search and Exa Contents.
- The matcher is deterministic by design. It favors explainability over broad fuzzy matching.
- Full user auth is not included in this demo. Production deployments should add SSO before exposing manual scans to multiple teams.
