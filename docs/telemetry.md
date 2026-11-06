# Telemetry

Evrima measures how the website works and what visitors do, by default **without cookies, IP addresses, user agents, query strings or form contents**, and sends it to the telemetry collector ([evrima-telemetry](https://github.com/michal-vojacek/evrima-telemetry)). The exact contract is the collector's [`docs/protocol.md`](https://github.com/michal-vojacek/evrima-telemetry/blob/main/docs/protocol.md).

## Switching it on

The collector (evrima-telemetry) is not built yet; until it runs, leave telemetry off.

1. In the collector, add the website: give it a name, copy the generated token (shown once).
2. In the website's settings (`.env` or DWM):

   ```
   TELEMETRY_ENDPOINT=https://telemetry.example.com
   TELEMETRY_TOKEN=<the token>
   ```

   The endpoint must be HTTPS in production; a token is required with an endpoint.
3. Redeploy. The `jobs` container ships the buffer every minute (`flask evrima telemetry ship` does one run by hand).

Empty `TELEMETRY_ENDPOINT` = off: nothing is collected and the browser script is not served.

## What is collected

| Event | Where from | Gives |
|---|---|---|
| `request` | server, every request except static files, uploads, `/health` | number of requests, response times, error rates (by endpoint name, never the URL) |
| `error` | server, unhandled exception | the exception's class only, never its message |
| `form` | the website's form view: `telemetry.event("form", form="contact", result="sent")` | sent / rejected / bot / failed enquiries |
| `pageview` | browser script | page views, **visits** (a page view whose referrer is another website: no visitor identifier), external referrer host, device class, load times |
| `click` | browser script | clicks on `tel:`, `mailto:`, links to other websites (their host) and on anything with `data-track` |

Every batch also carries the **running Evrima version**, so the collector can show websites left on an old release.

## Labels on links: `data-track`

Any link or button can carry a label (letters, digits, `-`, `_`, at most 40 characters):

```html
<a class="btn btn-primary" href="#kontakt" data-track="cta-hero">Kontaktujte nás</a>
<a href="tel:+420…" data-track="phone">…</a>
<a href="https://mapy.com/…" data-track="map">Jak k nám</a>
<a href="https://www.facebook.com/…" data-track="facebook">Facebook</a>
```

Phone, e-mail and external links are counted even without a label (an external link is then labelled by its host); internal links only with one. Never put personal data into a label.

## How it travels

The page sends events with `navigator.sendBeacon` to the website itself (`POST /_evrima/t`), never to a third party; the server checks each against the protocol and keeps it in Redis (at most 100 000 events). The `jobs` container sends them in gzip batches of 1 000 with the token; a batch leaves Redis only after the collector accepted it. When the collector is down, the website notices nothing.

## Privacy policy

The privacy policy skeleton describes this measurement on its own while telemetry is on (no cookies, no IP addresses). Level 1 needs no consent banner. Level 2 (unique and returning visitors) needs one: `CONSENT_CATEGORIES` with e.g. `analytics` and `TELEMETRY_VISITORS = "analytics"` in `PUBLIC`; the visitor cookie is then set only after consent (docs/framework.md in Evrima, "Telemetry").
