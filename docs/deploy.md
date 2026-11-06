# Deploy

The website runs on the deploy platform **DWM**, which manages Docker Compose stacks: it clones the website's repository from Git, runs its `docker-compose.yml` and routes the domain to it through Caddy with automatic TLS.

## What happens on every deploy

1. DWM fetches the configured branch or tag of the repository.
2. It writes the stack's settings into an env file. **That file only fills in the `${…}` placeholders of `docker-compose.yml`**; a setting reaches the containers only when the compose file lists it under `environment` (it does, for every setting below).
3. `docker compose up --build` (the stack must have **build enabled** in DWM):
   - the image is built from `Dockerfile`: stage 1 installs Evrima **`v$EVRIMA_VERSION` from GitHub** and the website's `requirements.txt` into a virtual environment, stage 2 copies it with the website package into a slim runtime image running as an unprivileged user;
   - `db` (PostgreSQL) and `redis` start and become healthy;
   - `migrate` runs `flask evrima db upgrade` once and exits; **if it fails, `web` does not start** and the previous containers are not replaced by a broken version;
   - `web` (gunicorn, `0.0.0.0:5000`) and `jobs` start. `web` has a health check on `/health` (database and Redis), and DWM waits for it.

## Services

| Service | What it does | Data |
|---|---|---|
| `web` | the website, gunicorn with gthread workers on port **5000** (`WEB_CONCURRENCY` workers, default 2) | uploads on the volume `media` |
| `migrate` | database migrations of the framework, the website and its modules, once per deploy | – |
| `jobs` | `flask evrima jobs`: telemetry shipping every minute, cleanup of unused uploads and old login records once a day (DWM has no cron) | – |
| `db` | PostgreSQL 17 | volume `db` |
| `redis` | rate limits and the telemetry buffer (append-only file) | volume `redis` |

DWM does not back up volumes: arrange database dumps and a copy of `media` with the hosting's backups.

## Setting up the stack in DWM

1. **Stack:** the repository's HTTPS URL (and a read-only credential if it is private), the branch or tag to deploy, compose path `docker-compose.yml`, **build enabled**.
2. **Settings** (one `KEY=value` per line):

   | Key | Required | Example / note |
   |---|---|---|
   | `EVRIMA_VERSION` | yes | `0.1.0` — the framework release, exact |
   | `SECRET_KEY` | yes | 48+ random characters; changing it logs everyone out |
   | `POSTGRES_PASSWORD` | yes | random; used by `db` and in `DATABASE_URL` |
   | `SITE_HOSTS` | yes | `example.com,www.example.com` |
   | `SMTP_HOST`, `MAIL_SENDER` | yes | e.g. `smtp.gmail.com`, `web@example.com` |
   | `SMTP_PORT`, `SMTP_SECURITY`, `SMTP_USERNAME`, `SMTP_PASSWORD` | as the mail service needs | defaults `587`, `starttls` |
   | `CONTACT_RECIPIENT` | yes | where enquiries go |
   | `TELEMETRY_ENDPOINT`, `TELEMETRY_TOKEN` | no | empty = telemetry off |

   A missing required setting stops the deploy with its name (`${KEY:?…}` in the compose file).
3. **Route:** the domain(s) to service **`web`**, port **5000**. DNS A record of the domain must point to the server; Caddy then obtains the certificate and redirects HTTP to HTTPS.
4. **First administrator**, after the first deploy, in DWM's console of the `web` container:

   ```
   flask evrima create-admin owner@example.com --name "Name"
   ```

## Updating Evrima

1. Read the framework's CHANGELOG between the current and the new version.
2. Change `EVRIMA_VERSION` in the stack's settings and redeploy. The image is rebuilt with the new tag; migrations run before the new version starts.
3. A `MAJOR` version needs the website adapted and tested first (locally against `../evrima-framework` at that tag).

Every telemetry batch carries the running Evrima version; the collector (not built yet) is to list websites that are not on the latest release.

## Test the image locally

```
docker compose --env-file .env.docker up -d --build --wait
```

with a `.env.docker` holding the settings above (`SITE_HOSTS=localhost` and a dummy SMTP host are enough to see the website start). The compose file publishes no port (Caddy reaches `web` inside Docker); for a local look add a small override with `ports: ["127.0.0.1:5081:5000"]` for `web`. Clean up with `docker compose down -v`.

Before a framework version is tagged, a build can use a local wheel: `pip wheel ../evrima-framework --no-deps -w dist`, copy `dist/` into the build stage and pass `--build-arg EVRIMA_SOURCE=/wheels/<file>.whl` (only for testing; never deploy an untagged framework).

## Rules the compose file follows (DWM)

- No `ports:` (DWM resets them; Caddy is the only way in), no `container_name:`, no `network_mode: host`, one replica of `web`.
- `restart: unless-stopped` on every long-running service; `migrate` has `restart: "no"`.
- Named volumes only (anonymous volumes are lost on "Stop deployment").
- Do not add files named `manager-policy.yml` or `manager-edge.yml`: DWM generates them.
- Logs go to stdout and stderr; gunicorn writes no access log (Caddy keeps one).
