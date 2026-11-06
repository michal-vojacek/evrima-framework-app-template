"""The website, built on Evrima.

`flask --app mysite run` finds the `create_app` factory below on its own.
Rename the package `mysite` to the website's name (README, "Start a new website").
"""

import os
from collections.abc import Mapping

import evrima
from evrima.config import ConfigError

from mysite.contact import contact
from mysite.pages import pages

# Website decisions for evrima.seo (not environment settings). TODO: fill in.
SEO = {
    # The canonical address, also in development, so canonical links and the
    # sitemap always point to the real website.
    "SITE_URL": "https://example.com",
    "SITEMAP": ["pages.home", "evrima_legal.privacy"],
    # Crawlers kept out of the whole website, e.g. AI training crawlers:
    # ["GPTBot", "CCBot", "Google-Extended"]. Decide with the client.
    "ROBOTS_BLOCKED_AGENTS": [],
    "SECURITY_CONTACT": "mailto:security@example.com",
    "SECURITY_LANGUAGES": "cs, en",
}

# Website decisions for Evrima's public pages (docs/framework.md in Evrima,
# "Consent banner" and "Legal pages").
PUBLIC = {
    "SITE_LANGUAGE": "cs",
    # The privacy policy at /zasady-ochrany-osobnich-udaju, from
    # templates/legal/privacy.html. Add "cookies" for a cookies page.
    "LEGAL_PAGES": ["privacy"],
    # No consent banner: the website sets only a necessary cookie. With
    # third-party scripts or analytics cookies, list the categories here, e.g.
    # ["analytics", "marketing"], and decide in the templates what each needs.
    "CONSENT_CATEGORIES": [],
}


def create_app(config_overrides=None, environ: Mapping[str, str] | None = None):
    """Build the website: Evrima's core, the pages and the contact form.

    CONTACT_RECIPIENT, the address enquiries go to, is the website's own
    setting; a website that cannot deliver enquiries must not start.
    Modules (docs/modules.md in Evrima) go to `modules=[...]`.
    """
    env = os.environ if environ is None else environ
    app = evrima.create_app(__name__, blueprints=[pages, contact],
                            config_overrides={**SEO, **PUBLIC, **(config_overrides or {})}, environ=environ)
    recipient = app.config.get("CONTACT_RECIPIENT") or env.get("CONTACT_RECIPIENT", "").strip()
    if not recipient:
        raise ConfigError(["CONTACT_RECIPIENT is required: the address enquiries from the contact form go to."])
    app.config["CONTACT_RECIPIENT"] = recipient
    return app
