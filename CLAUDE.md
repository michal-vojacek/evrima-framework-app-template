# Website on Evrima

This repository is a website built on the Evrima framework, created from `evrima-framework-app-template`. Read [README.md](README.md) first; the framework's rules are in `../evrima-framework/CLAUDE.md` and `docs/framework.md` (the source of truth for the framework), modules in `docs/modules.md`.

## Repositories

- `../evrima-framework`: the framework (public). Installed here editable for development; a website never copies framework code. A change the website needs from the framework is made there, with its tests and a CHANGELOG entry, never worked around here.
- `../evrima-telemetry`: the telemetry protocol (`docs/protocol.md`, the contract of what the website sends); the collector itself is not built yet.
- Nothing from this website (client data, business information, texts) may go into the public framework.

## Working rules

- Propose larger changes first and wait for approval. Record every decision with its date in this file or in `docs/`.
- Code, identifiers, comments and commit messages in English; the website's public texts in Czech (Czech typography: „“, –, non-breaking spaces after one-letter prepositions and between numbers and units).
- Strict CSP: no inline `<script>`, no `style="…"`, no `onclick=…`. Scripts and styles in `static/`.
- Static files only through `url_for('static', …)` (fingerprinted, cached for a year). Fonts and icons hosted here, never from a CDN or Google Fonts.
- No third-party widgets, pixels or scripts; social networks and chat only as plain links. Only if the client explicitly wants one (e.g. Google Analytics): after consent, with the consent banner, a cookies page and the privacy policy updated (docs/consent-and-legal.md).
- Every public form: CSRF token, honeypot, rate limit, server-side checks; errors next to the fields.
- Truthful content only: no unverified numbers, references or quotes. Anything not verified is marked as such.
- Legal and tax information is indicative only, to be verified with a professional. The privacy policy is checked by a lawyer before launch.
- Run the tests before committing: `.venv\Scripts\python -m pytest`. Commit and push only when asked.

## Deploy

DWM builds the image on every deploy from `docker-compose.yml` with the Evrima version from the stack's settings. See [docs/deploy.md](docs/deploy.md). A new environment setting must be added to `.env.example`, to `docker-compose.yml` (`environment:`) and to the table in `docs/deploy.md`.
