"""Public pages of the website.

Addresses are Czech and have no language prefix. A new page: a view here, a
template in templates/, its endpoint in SEO["SITEMAP"] (mysite/__init__.py).
The privacy policy is served by Evrima (evrima.legal, LEGAL_PAGES in
mysite/__init__.py) from templates/legal/privacy.html.
"""

from flask import Blueprint, render_template

pages = Blueprint("pages", __name__)


@pages.get("/")
def home():
    """The home page."""
    return render_template("home.html")
