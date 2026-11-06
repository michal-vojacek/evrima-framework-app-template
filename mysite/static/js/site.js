// Small enhancements of the public pages. Every page works without this script.
(function () {
  "use strict";

  // The mobile menu is a <details> element; close it once a link is chosen,
  // otherwise it stays open over the section the visitor jumped to.
  document.querySelectorAll(".mnav a").forEach(function (link) {
    link.addEventListener("click", function () {
      var menu = link.closest("details");
      if (menu) { menu.removeAttribute("open"); }
    });
  });

  // Contact form: show the errors next to the fields before the request is
  // sent. The server checks everything again; this only saves a round trip.
  var form = document.querySelector(".booking");
  if (!form) { return; }
  form.addEventListener("submit", function (event) {
    var name = form.querySelector("#f-name");
    var phone = form.querySelector("#f-phone");
    var email = form.querySelector("#f-email");
    var nameError = form.querySelector("#e-name");
    var contactError = form.querySelector("#e-contact");
    var nameOk = name.value.trim() !== "";
    var contactOk = phone.value.trim() !== "" || (email.value.trim() !== "" && email.checkValidity());
    // The server may have put another message there (e.g. "too long"); these
    // checks show their own, kept in data-msg.
    nameError.textContent = nameError.getAttribute("data-msg");
    contactError.textContent = contactError.getAttribute("data-msg");
    nameError.hidden = nameOk;
    name.setAttribute("aria-invalid", String(!nameOk));
    contactError.hidden = contactOk;
    [phone, email].forEach(function (field) { field.setAttribute("aria-invalid", String(!contactOk)); });
    if (!nameOk || !contactOk) {
      event.preventDefault();
      (nameOk ? phone : name).focus();
      return;
    }
    var button = form.querySelector("button[type=submit]");
    button.disabled = true;
    button.textContent = button.getAttribute("data-busy");
  });
})();
