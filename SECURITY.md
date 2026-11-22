# Security

## Scope

Spectra-AIO is a local, lightweight recon/OSINT helper intended for legal, authorized security research and analysis of your own digital footprint.

## Reporting

If you find a security issue in this repository:
- Do not publish exploit details before a fix is available.
- Open a private security advisory on GitHub if enabled, or contact the repository owner directly.

## Operational Notes

- Bind to `127.0.0.1` by default; do not expose the backend publicly without authentication and a reverse proxy.
- Keep `.env`, tokens, and local databases out of git.
- Treat external OSINT results as heuristic; verify before acting.
- Use `SPECTRA_PROXY_MODE=direct|tor|custom` intentionally; `direct` is less private.
