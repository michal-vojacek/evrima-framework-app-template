"""The contact form: checks, e-mail, honeypot, rate limit and CSRF."""

import re

import pytest

from evrima import mail
from evrima.config import ConfigError
from evrima.security import honeypot

from conftest import BASE_ENV, https_client

VALID = {"name": "Jana Nováková", "phone": "777 123 456", "email": "jana@firma.cz",
         "website": "www.firma.cz", "time": "úterý odpoledne"}


CLOCK = {"filling_in": 0}       # seconds a visitor spends on the form


@pytest.fixture(autouse=True)
def clock(monkeypatch):
    """Let `post()` move the honeypot's clock between rendering and sending the form."""
    real_now = honeypot._now
    offset = {"now": 0}
    monkeypatch.setattr(honeypot, "_now", lambda: real_now() + offset["now"])
    CLOCK["offset"] = offset
    CLOCK["filling_in"] = 0
    yield


@pytest.fixture
def human():
    """A visitor who takes longer than the honeypot's minimum to fill in the form."""
    CLOCK["filling_in"] = 60


def form_fields(client):
    """The hidden fields of the form as the home page renders them (CSRF, honeypot)."""
    CLOCK["offset"]["now"] = 0
    html = client.get("/").get_data(as_text=True)
    if '<form class="booking"' not in html:      # the thanks after a previous enquiry
        html = client.get("/").get_data(as_text=True)
    form = html[html.index('<form class="booking"'):html.index("</form>")]
    return dict(re.findall(r'<input type="hidden" name="([^"]+)" value="([^"]*)"', form)) | {honeypot.TRAP_FIELD: ""}


def post(client, **values):
    """Send the form with the page's hidden fields and `values`, after the time it takes to fill it in."""
    fields = form_fields(client)
    CLOCK["offset"]["now"] = CLOCK["filling_in"]
    return client.post("/poptavka", data={**fields, **values})


def sent(app):
    with app.app_context():
        return list(mail.outbox())


def test_an_enquiry_is_e_mailed_and_thanked_for(app, client, human):
    response = post(client, **VALID)
    assert response.status_code == 303
    assert response.headers["Location"].endswith("/#kontakt")
    [message] = sent(app)
    assert message["To"] == "enquiries@example.com"
    assert message["Reply-To"] == "jana@firma.cz"
    assert message["Subject"] == "Poptávka z webu: Jana Nováková"
    body = message.get_content()
    for value in VALID.values():
        assert value in body
    page = client.get("/").get_data(as_text=True)
    assert "Děkujeme, zpráva je odeslaná." in page
    assert '<form class="booking"' not in page
    # The thanks are shown once; the next visit has the form again.
    assert '<form class="booking"' in client.get("/").get_data(as_text=True)


def test_a_phone_alone_is_enough(app, client, human):
    response = post(client, name="Jana", phone="+420 777 123 456")
    assert response.status_code == 303
    [message] = sent(app)
    assert message["Reply-To"] is None
    assert "E-mail: –" in message.get_content()


@pytest.mark.parametrize("values, error", [
    ({"name": "", "phone": "777123456"}, "Napište prosím své jméno."),
    ({"name": "Jana"}, "Vyplňte prosím telefon, nebo e-mail."),
    ({"name": "Jana", "email": "jana@"}, "Zkontrolujte prosím e-mail, chybí v něm část adresy."),
    ({"name": "Jana", "phone": "zavolejte"}, "Telefon může obsahovat jen číslice, mezery a znak +."),
    ({"name": "J" * 201, "phone": "777123456"}, "Zkraťte prosím text na nejvýš 200 znaků."),
])
def test_a_rejected_form_comes_back_with_its_error_and_values(app, client, human, values, error):
    response = post(client, **values)
    assert response.status_code == 422
    html = response.get_data(as_text=True)
    assert error in html
    assert 'aria-invalid="true"' in html
    for value in values.values():
        if value:
            assert f'value="{value}"' in html
    assert sent(app) == []


def test_line_breaks_cannot_reach_the_e_mail_headers(app, client, human):
    response = post(client, name="Jana\r\nBcc: victim@example.com", phone="777123456")
    assert response.status_code == 303
    [message] = sent(app)
    assert message["Bcc"] is None
    assert message["Subject"] == "Poptávka z webu: Jana Bcc: victim@example.com"


def test_a_bot_is_told_it_succeeded_but_nothing_is_sent(app, client, human):
    response = post(client, **VALID, homepage="http://spam.example")
    assert response.status_code == 303
    assert sent(app) == []


def test_an_instant_submit_sends_nothing(app, client):
    response = post(client, **VALID)
    assert response.status_code == 303
    assert sent(app) == []


def test_without_a_csrf_token_nothing_is_sent(app, client, human):
    fields = form_fields(client)
    del fields["csrf_token"]
    response = client.post("/poptavka", data={**fields, **VALID})
    assert response.status_code == 400
    assert sent(app) == []


def test_only_sent_enquiries_count_against_the_rate_limit(make_app, human):
    app = make_app(env={"RATELIMIT_ENABLED": "true"}, RATELIMIT_ENABLED=True)
    client = https_client(app)
    for _ in range(3):
        assert post(client, name="").status_code == 422     # mistakes are not counted
    for _ in range(5):
        assert post(client, **VALID).status_code == 303
    assert post(client, **VALID).status_code == 429
    assert len(sent(app)) == 5


def test_a_mail_failure_points_to_the_other_channels(app, client, human, monkeypatch):
    def fail(*args, **kwargs):
        raise mail.MailError("down")
    monkeypatch.setattr(mail, "send", fail)
    response = post(client, **VALID)
    assert response.status_code == 503
    html = response.get_data(as_text=True)
    assert "Zprávu se teď nepodařilo odeslat." in html
    assert 'value="Jana Nováková"' in html


def test_an_unknown_page_returns_to_the_home_page(app, client, human):
    response = post(client, name="Jana", phone="777123456", page="https://evil.example/")
    assert response.status_code == 303
    assert response.headers["Location"].endswith("/#kontakt")


def test_the_website_needs_an_enquiry_recipient():
    environ = {key: value for key, value in BASE_ENV.items() if key != "CONTACT_RECIPIENT"}
    from mysite import create_app
    with pytest.raises(ConfigError, match="CONTACT_RECIPIENT"):
        create_app(environ=environ)
