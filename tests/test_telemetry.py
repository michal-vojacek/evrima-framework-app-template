"""Telemetry and cookies of the website: what it sets, and what stays off until it is switched on."""

from conftest import https_client

ON = {"TELEMETRY_ENDPOINT": "https://collector.example.com", "TELEMETRY_TOKEN": "site-token"}


def test_telemetry_is_off_without_an_endpoint(client):
    assert "telemetry.js" not in client.get("/").get_data(as_text=True)


def test_with_an_endpoint_the_script_is_served(make_app):
    html = https_client(make_app(env=ON)).get("/").get_data(as_text=True)
    assert 'data-endpoint="/_evrima/t"' in html
    assert "data-visitors" not in html            # level 1: no visitor cookie


def test_calls_to_action_carry_labels(client):
    assert 'data-track="cta-header"' in client.get("/").get_data(as_text=True)


def test_no_consent_banner_while_the_website_sets_only_necessary_cookies(client):
    html = client.get("/").get_data(as_text=True)
    assert "evrima-consent" not in html and "consent.js" not in html
    assert client.get("/cookies").status_code == 404


def test_the_layout_is_ready_for_the_consent_banner(make_app):
    """Switching it on in PUBLIC needs no change to the layout (docs/consent-and-legal.md)."""
    html = https_client(make_app(CONSENT_CATEGORIES=["analytics"])).get("/").get_data(as_text=True)
    assert "consent.js" in html and 'class="evrima-consent"' in html
    assert 'data-evrima-consent-open>Nastavení cookies</a>' in html
