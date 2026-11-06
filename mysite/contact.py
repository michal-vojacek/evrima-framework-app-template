"""The contact form: an enquiry for a meeting, sent by e-mail.

Enquiries are only e-mailed, never stored, and have no admin page: nothing
personal is kept on the server. Protection: CSRF (framework, every POST), the honeypot (simple
bots) and a rate limit per IP address (one sender flooding the mailbox).
Each result (sent, rejected, bot, failed) is counted by telemetry, without
any of the visitor's data.
"""

import re
from dataclasses import dataclass, field
from datetime import datetime
from zoneinfo import ZoneInfo

from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for

from evrima import mail, telemetry
from evrima.security import honeypot, limiter

contact = Blueprint("contact", __name__)

FORM = "contact"
SENT = "contact-sent"          # flash category read by home.html

# One sender may send a few enquiries an hour (a typo, a second thought), not
# hundreds. Only sent enquiries count: a visitor fixing an error in the form is
# not punished, and rejected posts cost nothing.
RATE_LIMIT = "5 per hour"

LIMITS = {"name": 200, "phone": 40, "email": 254, "website": 500, "time": 200}
EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PHONE_PATTERN = re.compile(r"^\+?[0-9 ()/-]{6,}$")
PRAGUE = ZoneInfo("Europe/Prague")

# The pages that carry the form (templates/_contact.html): the form says which
# one it came from, and the visitor returns there. Only these keys are
# accepted, so the field cannot be used to redirect anywhere else.
PAGES = {
    "home": ("pages.home", "home.html"),
}


@dataclass
class Enquiry:
    """The submitted values, cleaned, and the errors found (field name -> message)."""

    name: str = ""
    phone: str = ""
    email: str = ""
    website: str = ""
    time: str = ""
    errors: dict[str, str] = field(default_factory=dict)

    @classmethod
    def from_form(cls, data) -> "Enquiry":
        """Read and check the form. Every value is one line: line breaks are
        collapsed, so nothing can be smuggled into the e-mail's headers."""
        values = {name: " ".join((data.get(name) or "").split()) for name in LIMITS}
        enquiry = cls(**values)
        errors = enquiry.errors
        for name, limit in LIMITS.items():
            if len(values[name]) > limit:
                errors[name] = f"Zkraťte prosím text na nejvýš {limit} znaků."
        if not enquiry.name:
            errors["name"] = "Napište prosím své jméno."
        if not enquiry.phone and not enquiry.email:
            errors["contact"] = "Vyplňte prosím telefon, nebo e-mail."
        if enquiry.email and "email" not in errors and not EMAIL_PATTERN.match(enquiry.email):
            errors["email"] = "Zkontrolujte prosím e-mail, chybí v něm část adresy."
        if enquiry.phone and "phone" not in errors and not PHONE_PATTERN.match(enquiry.phone):
            errors["phone"] = "Telefon může obsahovat jen číslice, mezery a znak +."
        return enquiry

    def as_text(self, sent_at: datetime) -> str:
        """The e-mail body: plain text, every field on its own line."""
        local = sent_at.astimezone(PRAGUE)
        lines = [
            f"Nová poptávka z webu {current_app.config['SITE_URL']}",
            "",
            f"Jméno: {self.name}",
            f"Telefon: {self.phone or '–'}",
            f"E-mail: {self.email or '–'}",
            f"Web: {self.website or '–'}",
            f"Kdy se hodí: {self.time or '–'}",
            "",
            f"Odesláno: {local.day}. {local.month}. {local.year} {local:%H:%M}",   # Czech style: 5. 11. 2026
        ]
        return "\n".join(lines) + "\n"


def _only_sent(response) -> bool:
    """Count an attempt against the rate limit only when the enquiry was accepted."""
    return response.status_code == 303


@contact.post("/poptavka")
@limiter.limit(RATE_LIMIT, deduct_when=_only_sent)
def send():
    """Check the enquiry, e-mail it, and return to the contact section of the page it came from."""
    endpoint, template = PAGES.get(request.form.get("page", ""), PAGES["home"])
    back = redirect(url_for(endpoint, _anchor="kontakt"), code=303)
    if honeypot.looks_like_bot(request.form, FORM):
        # Looks accepted, so the bot learns nothing; nothing is sent.
        telemetry.event("form", form=FORM, result="bot")
        flash("sent", SENT)
        return back

    enquiry = Enquiry.from_form(request.form)
    if enquiry.errors:
        telemetry.event("form", form=FORM, result="rejected")
        return render_template(template, enquiry=enquiry), 422

    try:
        mail.send(current_app.config["CONTACT_RECIPIENT"], f"Poptávka z webu: {enquiry.name}",
                  enquiry.as_text(datetime.now(PRAGUE)), reply_to=enquiry.email or None)
    except mail.MailError:
        # evrima.mail has logged the failure without the message, i.e. without
        # the visitor's personal data. The visitor gets the other channels.
        enquiry.errors["send"] = "unavailable"
        telemetry.event("form", form=FORM, result="failed")
        return render_template(template, enquiry=enquiry), 503

    telemetry.event("form", form=FORM, result="sent")
    flash("sent", SENT)
    return back
