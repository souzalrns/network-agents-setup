# Security policy

## Reporting a vulnerability

Please **do not open a public issue** for security problems. Report them privately through GitHub's
[private vulnerability reporting](https://github.com/souzalrns/network-agents-setup/security/advisories/new)
for this repository. Include the affected file or component, steps to reproduce and the impact you observed.

## What is in place

- Secret scanning (gitleaks), static analysis (semgrep) and CodeQL run on every pull request
  ([`security-scan.yml`](./.github/workflows/security-scan.yml)).
- Every GitHub Action is pinned to a commit SHA.
- Agents in this repository are defensive only: offensive actions and acting in production are
  forbidden by policy and validated in CI ([`config/security-capabilities.yaml`](./config/security-capabilities.yaml)).
- Writes to production systems (database, deployments) are always a human decision, never an agent's.

Architecture and threat model (PT): [`docs/architecture/SECURITY.md`](./docs/architecture/SECURITY.md).
