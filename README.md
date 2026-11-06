# Evrima website template

The starting skeleton of a new website built on [Evrima](https://github.com/michal-vojacek/evrima-framework), a lightweight, security-first Flask framework and CMS for simple websites. Copy it, rename one package, fill in the TODOs, and you have a website with:

- a home page, a privacy policy on Evrima's skeleton, Czech error pages and a layout without inline scripts or styles (strict CSP),
- a contact form that e-mails enquiries (nothing is stored), protected by CSRF, a honeypot and a rate limit,
- `robots.txt`, `sitemap.xml`, `/.well-known/security.txt`, canonical links and schema.org data,
- fingerprinted static files cached for a year,
- telemetry without cookies (off until it is configured),
- a consent banner and a cookies page ready to switch on when the website needs them (off: the template sets only a necessary cookie),
- a Dockerfile and a `docker-compose.yml` for the deploy platform (DWM): build on every deploy with the chosen Evrima version, migrations before start, periodic jobs, PostgreSQL and Redis,
- tests (`pytest`).

| Read next | What it covers |
|---|---|
| [docs/deploy.md](docs/deploy.md) | Docker, DWM, settings, the first deploy, updating Evrima |
| [docs/telemetry.md](docs/telemetry.md) | What telemetry collects, how to switch it on, `data-track` labels |
| [docs/consent-and-legal.md](docs/consent-and-legal.md) | Privacy policy, cookies page, consent banner, telemetry level 2: when a website needs which, and how to switch them on |
| [CLAUDE.md](CLAUDE.md) | Working rules for the project (and for an AI assistant working in it) |
| Evrima [`docs/framework.md`](https://github.com/michal-vojacek/evrima-framework/blob/main/docs/framework.md) | The framework: architecture and every decision |
| Evrima [`docs/modules.md`](https://github.com/michal-vojacek/evrima-framework/blob/main/docs/modules.md) | Writing a module with its own admin screens (references, a gallery…) |

## How the pieces fit

```
EVRIMA/                         one folder with the repositories side by side
├── evrima-framework/           the framework (public): installed into every website
├── evrima-telemetry/           the telemetry protocol (docs/protocol.md); the collector is not built yet
├── evrima-framework-app-template/   this template
└── <website>/                  each website: its own repository, made from this template
```

A website is an ordinary Python package that calls `evrima.create_app(...)`. Evrima brings the security baseline, the admin (login, administrators, audit log, uploads, editor), e-mail, migrations, SEO files and telemetry; the website brings its pages, templates, styles, forms and, if it needs them, its own modules. The website never copies framework code: it pins a framework version, and a security fix reaches every website by raising that version.

## Start a new website

1. **Create the repository** from this template (GitHub: "Use this template", or clone it and push to a new private repository), next to `evrima-framework`:

   ```
   cd EVRIMA
   git clone https://github.com/<owner>/<website>.git
   ```

2. **Rename the package** `mysite` to the website's name (a Python identifier, e.g. `kovarna_novak`): the folder, the imports in `mysite/__init__.py` and `tests/`, `FLASK_APP` and the gunicorn target in `Dockerfile`, the image name in `docker-compose.yml`. A search for `mysite` finds them all.

3. **Fill in the TODOs:** `SEO` in `__init__.py` (canonical address, sitemap pages, blocked crawlers, security contact), the business identification in `templates/base.html` (name, IČO, registered address: required on a business website), the schema.org data in `templates/home.html`, the privacy policy in `templates/legal/privacy.html` (every yellow `.placeholder`; then have it checked by a lawyer; a cookies page or the consent banner only when the website needs them: [docs/consent-and-legal.md](docs/consent-and-legal.md)), the styles in `static/css/site.css`.

4. **Local environment** (Python 3.13, Windows commands):

   ```
   py -3.13 -m venv .venv
   .venv\Scripts\python -m pip install -r requirements-dev.txt
   copy .env.example .env                          (put a random SECRET_KEY into .env)
   .venv\Scripts\flask --app mysite evrima db upgrade
   .venv\Scripts\flask --app mysite evrima create-admin you@example.com --name "Your Name"
   $env:PYTHONUTF8 = '1'                           (PowerShell: readable Czech in console e-mails)
   .venv\Scripts\flask --app mysite run --port 5080 --reload
   .venv\Scripts\python -m pytest
   ```

   `requirements-dev.txt` installs Evrima **editable from `../evrima-framework`**, so a change in the framework shows up at once. The admin is at `/admin`; in development e-mails (password reset links, the contact form's enquiries) are printed to the console. Do not use port 5060: browsers block it (`ERR_UNSAFE_PORT`).

5. **Deploy** on DWM: [docs/deploy.md](docs/deploy.md).

## Using the framework

- **Version.** Production always installs an exact released tag: `EVRIMA_VERSION=0.1.0` installs `v0.1.0` from GitHub. Releases follow semantic versioning; `PATCH` and `MINOR` need no change in the website, `MAJOR` does. Read the framework's [CHANGELOG](https://github.com/michal-vojacek/evrima-framework/blob/main/CHANGELOG.md) before raising the version.
- **Configuration.** Environment settings (`.env`, or the stack's settings on DWM) are read by Evrima and checked at startup: an invalid configuration stops the app instead of failing later. Website decisions (SEO) are passed to `create_app` as overrides.
- **Templates.** The website's templates win over the framework's. Never override admin templates; a change to the admin belongs in the framework.
- **Strict CSP.** No `<script>` without `src`, no `style="…"`, no `onclick=…`. JavaScript goes into `static/js/`, styles into `static/css/`. Structured data uses the `json_ld` filter (a data block, allowed).
- **Static files.** Always link them with `url_for('static', filename=…)`: the URL then carries the content hash and is cached for a year. Fonts referenced from CSS are not fingerprinted; they are cached for 30 days, so a replaced font needs a new file name.
- **Images.** Originals (PNG, photos) stay in `src/` (not deployed); the website gets AVIF and WebP exports in several widths in `static/img/` (`<name>-<width>.avif|webp`, e.g. 360, 720 and 1080 px, never wider than the original). The `picture` macro in `templates/_macros.html` writes the `<picture>`: give it the exported widths and a `sizes` that matches the layout on phone, tablet and desktop. `eager=True` for images visible without scrolling, `priority=True` for the largest element of the first view on a phone, at most one per page; everything else is lazy-loaded.
- **Fonts.** Self-hosted variable `woff2` files in `static/fonts/` with their licences, declared in `site.css` with `font-display: swap` and preloaded in `base.html` (`<link rel="preload" as="font" type="font/woff2" crossorigin>`). For Czech, keep the `latin` set and instead of the whole `latin-ext` cut a small file with only the Czech and Slovak letters outside Latin-1 (`pyftsubset` from fonttools, `--unicodes=U+010C-010F,U+011A-011B,U+0139-013A,U+013D-013E,U+0147-0148,U+0154-0155,U+0158-0159,U+0160-0161,U+0164-0165,U+016E-016F,U+017D-017E`, with the same `unicode-range` in `@font-face`); the originals stay in `src/fonts/`. A replaced font needs a new file name (30-day cache).
- **Forms.** Every form has `<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">`. A public form also gets `{{ honeypot("name") }}`, `honeypot.looks_like_bot(request.form, "name")` in its view and `@limiter.limit(...)`. See `mysite/contact.py`. Request bodies are limited to 64 KB on public pages; a form that takes files (an attachment, photos) raises it on its view with `@security.body_limit(10 * 1024 * 1024)` (`from evrima import security`), sized for what the visitors upload.
- **E-mail.** `evrima.mail.send(to, subject, text, reply_to=…)`: plain text over the SMTP in the settings.
- **Admin texts** come from TOML catalogues (`translations/`), never from code. Public website texts are Czech and live in the templates; Evrima's own public texts (consent banner, legal skeletons, fallback error page) follow `SITE_LANGUAGE` in `PUBLIC`.
- **Modules.** A website writes the modules its client needs (`mysite/modules/<name>/`), following Evrima's [docs/modules.md](https://github.com/michal-vojacek/evrima-framework/blob/main/docs/modules.md), and enables them in `create_app(..., modules=[...])`. Many websites need none: content that only the developer changes stays in the templates.
- **Commands** (`flask --app mysite evrima …`): `db upgrade`, `db revision -m "…" --module <name>`, `create-admin`, `set-admin-email`, `set-admin-password`, `media cleanup`, `telemetry ship`, `jobs`, `check-config`, `version`.

## Telemetry

Off by default. With `TELEMETRY_ENDPOINT` and `TELEMETRY_TOKEN` set, the website measures page views and visits, load and response times, form results and clicks on phone, e-mail and outgoing links, without cookies, IP addresses or form contents, and the `jobs` container ships it to the collector every minute. Details and the `data-track` labels: [docs/telemetry.md](docs/telemetry.md).

## Licence

MIT (see [LICENSE](LICENSE)). A website made from the template may use any licence.
