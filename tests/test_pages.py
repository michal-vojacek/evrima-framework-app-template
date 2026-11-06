"""Public pages: they render, follow the strict CSP and reference existing files."""

import re
from pathlib import Path

import pytest

STATIC = Path(__file__).resolve().parent.parent / "mysite" / "static"
PAGES = ["/", "/zasady-ochrany-osobnich-udaju"]


@pytest.mark.parametrize("path", PAGES)
def test_page_renders_in_czech(client, path):
    response = client.get(path)
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert html.startswith("<!doctype html>")
    assert '<html lang="cs">' in html


@pytest.mark.parametrize("path", PAGES)
def test_page_has_no_inline_scripts_styles_or_handlers(client, path):
    """The CSP forbids them; the browser would silently ignore them."""
    html = client.get(path).get_data(as_text=True)
    assert "style=" not in html
    assert not re.search(r"<style\b", html)
    assert not re.search(r"\son[a-z]+=", html)
    for script in re.findall(r"<script\b[^>]*>", html):
        # Structured data is a data block, not a script; browsers do not run it.
        assert "src=" in script or 'type="application/ld+json"' in script, script


@pytest.mark.parametrize("path", PAGES)
def test_page_loads_nothing_from_other_hosts(client, path):
    """Fonts, images and scripts are served by the website itself (no third parties)."""
    html = client.get(path).get_data(as_text=True)
    for url in re.findall(r'(?:src|href|srcset)="([^"]+)"', html):
        if url.startswith(("https://uoou.gov.cz/", "https://example.com/", "tel:", "mailto:", "#")):
            continue                       # plain links, nothing is loaded from them
        assert url.startswith("/"), url


@pytest.mark.parametrize("path", PAGES)
def test_every_static_file_exists(client, path):
    html = client.get(path).get_data(as_text=True)
    urls = set(re.findall(r'"(/static/[^"\s]+)"', html))
    for srcset in re.findall(r'srcset="([^"]+)"', html):
        urls.update(part.split()[0] for part in srcset.split(","))
    assert urls
    for url in urls:
        path = url.split("?", 1)[0]                 # without the fingerprint (?v=…)
        assert (STATIC / path.removeprefix("/static/")).is_file(), url


def test_strict_csp_is_sent(client):
    csp = client.get("/").headers["Content-Security-Policy"]
    assert "script-src 'self'" in csp
    assert "unsafe-inline" not in csp


def test_contact_form_carries_a_csrf_token(client):
    html = client.get("/").get_data(as_text=True)
    form = html[html.index('<form class="booking"'):html.index("</form>")]
    assert re.search(r'name="csrf_token" value="[^"]+"', form)


def test_unknown_page_is_a_czech_404(client):
    response = client.get("/neexistuje")
    assert response.status_code == 404
    html = response.get_data(as_text=True)
    assert "Tuhle stránku jsme nenašli" in html
    assert 'content="noindex"' in html
