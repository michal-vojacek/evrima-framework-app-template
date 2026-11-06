"""Search engines: robots.txt, sitemap, security.txt, canonical links. Adjust to the website's SEO settings."""

import re

from mysite import SEO


def test_sitemap_lists_the_public_pages(client):
    body = client.get("/sitemap.xml").get_data(as_text=True)
    assert re.findall(r"<loc>([^<]+)</loc>", body) == [
        SEO["SITE_URL"] + "/", SEO["SITE_URL"] + "/zasady-ochrany-osobnich-udaju"]


def test_robots_points_to_the_sitemap_and_keeps_out_of_the_admin(client):
    text = client.get("/robots.txt").get_data(as_text=True)
    assert "Disallow: /admin/" in text
    assert f"Sitemap: {SEO['SITE_URL']}/sitemap.xml" in text


def test_security_txt_names_the_contact(client):
    text = client.get("/.well-known/security.txt").get_data(as_text=True)
    assert f"Contact: {SEO['SECURITY_CONTACT']}" in text


def test_pages_have_a_canonical_link_without_query_string(client):
    html = client.get("/?utm_source=x").get_data(as_text=True)
    assert f'<link rel="canonical" href="{SEO["SITE_URL"]}/">' in html
