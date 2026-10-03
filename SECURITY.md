# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |

---

## 🔒 API Key & Privacy Guarantees

1. **Zero Secret Leakage**:
   - The application stores user-configured API keys strictly in `~/.config/refine_tool/config.json` with local user permissions.
   - Keys are never logged, never transmitted to telemetry, and masked in all CLI outputs (`AIzaSy...****`).
2. **Offline-First Privacy**:
   - When using the Built-in Rule Engine, all processing occurs 100% locally in memory. Zero network requests are made.

---

## Reporting a Vulnerability

If you discover a security vulnerability within Universal Sentence Refiner, please do not open a public issue.

Instead, please send an email to the repository maintainer with:
- A description of the issue.
- Steps or a proof-of-concept to reproduce the vulnerability.
- Affected environment and version.

We will acknowledge receipt within 48 hours and work on a prompt resolution.
