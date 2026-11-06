# Legal pages, cookies and the consent banner

Evrima ships the groundwork; the website decides what it needs. Everything below is switched in `PUBLIC` in `mysite/__init__.py` (website decisions, passed to `create_app`). Framework details: Evrima `docs/framework.md`, "Consent banner" and "Legal pages".

Legal texts are indicative only. Have the privacy policy, the cookies page and the banner's wording checked by a lawyer before launch.

## Which case is the website?

| The website… | It needs |
|---|---|
| sets only necessary cookies (the template as it is: the session that protects the contact form) and uses telemetry level 1 or none | the privacy policy only. No banner, no cookies page (the policy says what the one cookie does). |
| embeds a third-party service that sets cookies or tracks visitors (Google Analytics, a Facebook pixel, a YouTube or map embed, a chat widget) | the consent banner, a cookies page and a mention in the privacy policy |
| uses telemetry level 2 (unique and returning visitors) | the consent banner with the category it depends on, and the cookies page |

## Privacy policy

`"LEGAL_PAGES": ["privacy"]` serves it at `/zasady-ochrany-osobnich-udaju` from `templates/legal/privacy.html`, which extends Evrima's skeleton (`evrima/legal/privacy.cs.html`) and fills its blocks:

| Block | Filled by |
|---|---|
| `legal_controller`, `legal_purposes`, `legal_recipients`, `legal_retention`, `legal_effective` | the website (the skeleton shows a yellow "Doplňte" note until then) |
| `legal_statistics` | Evrima, while telemetry is on (and the level 2 identifier when it is used) |
| `legal_cookies` | Evrima links the cookies page when there is one; the template overrides it with its one-cookie sentence. **Delete that override when the website gets a cookies page.** |
| `legal_rights`, `legal_intro`, `legal_heading` | Evrima; override only for a reason |

Link it with `legal_url('privacy')`. Its endpoint for the sitemap is `evrima_legal.privacy`. Other addresses: `"LEGAL_PAGES": {"privacy": "/ochrana-udaju"}`.

## Cookies page

Add `"cookies"`: `"LEGAL_PAGES": ["privacy", "cookies"]` (address `/cookies`). Without a website template it renders Evrima's skeleton directly, which already lists Evrima's own cookies from the settings: the form session cookie, `evrima_admin` (administrators only), `evrima_consent` (with the banner), `evrima_vid` (telemetry level 2). The website adds its own and third-party cookies in `templates/legal/cookies.html`:

```jinja
{% extends "evrima/legal/cookies.cs.html" %}
{% from "evrima/legal/_macros.html" import cookie_row %}
{% block category_cookies %}{% if category == "analytics" %}
  {{ cookie_row("_ga", "Google", "Rozlišení návštěvníků v Google Analytics", "2 roky") }}
{% endif %}{% endblock %}
```

`category_cookies` is rendered once per consent category (`category` is set); `necessary_cookies` adds rows to the necessary table. Take names and lifetimes from the service's own documentation and check them in the browser (DevTools, Application, Cookies) after consent.

## Consent banner

1. **Categories:** `"CONSENT_CATEGORIES": ["analytics", "marketing"]`. Necessary cookies are never listed. Evrima has Czech and English texts for `analytics`, `marketing` and `preferences`; another category needs `consent.category.<name>.name` and `.description` in `mysite/translations/*.toml` (the website will not start without them).
2. **The layout** already contains everything (`templates/base.html`): `{{ consent_head() }}` in `<head>`, `{{ consent_banner() }}` before `</body>` and the "Nastavení cookies" link in the footer. All of it renders nothing while `CONSENT_CATEGORIES` is empty.
3. **The cookies page** (above), linked from the banner automatically.
4. **What each service needs is the website's decision.** Evrima only stores which categories the visitor allowed. Either:
   - leave a script out of the page until consent, on the server: `{% if consent("marketing") %}<script src="…"></script>{% endif %}` (it appears after the next page load), or
   - load it from the website's own script in `static/js/` and react at once: `evrimaConsent.has("analytics")` on load, and `document.addEventListener("evrima:consent", e => …)` with `e.detail.categories` after every change. This is the place for a service with its own consent switches (e.g. Google's consent mode, where one tag depends on both analytics and advertising consent).
5. **CSP:** a third-party script needs its hosts in `"CSP"` (e.g. `{"script-src": ["https://www.googletagmanager.com"], "connect-src": [...]}`); take the list from the service's CSP documentation. No inline snippets: the service's "paste this `<script>`" code goes into a file in `static/js/`.
6. **Withdrawn consent:** Evrima deletes its own `evrima_vid`. Third-party cookies set before stay until they expire; the service's own consent switch or the website's script handles them.
7. **New service later:** raise `"CONSENT_VERSION"` (1 → 2), so every visitor is asked again, and update the cookies page and the privacy policy.

The look: override the custom properties of `.evrima-consent` (colours, radius, font) in `static/css/site.css`, or the whole template (`templates/consent/banner.html`, `consent/settings.html`; copy Evrima's and keep the form's fields and `data-evrima-consent*` attributes). Keep "Odmítnout vše" as visible as "Přijmout vše" and nothing ticked in advance.

## Telemetry level 2

Unique and returning visitors, only with consent: a category in `CONSENT_CATEGORIES` and `"TELEMETRY_VISITORS": "analytics"`. Evrima then stores a random id in `evrima_vid` for 13 months after consent, adds it to page views and clicks, lists the cookie on the cookies page and mentions it in the privacy policy skeleton. The figures cover only visitors who consented. See [telemetry.md](telemetry.md).
