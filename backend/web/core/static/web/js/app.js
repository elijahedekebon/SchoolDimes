/* SchoolDimes web — the little client-side behaviour the pages need:
   dialogs (modal / drawer) filled by HTMX, toasts, copy buttons, tabs,
   show-if fields, the student picker and the onboarding stepper.
   Everything else is server-rendered; data never leaves through here. */
(function () {
  "use strict";

  function openDialogFor(el) {
    var dialog = el && el.closest ? el.closest("dialog") : null;
    if (dialog && !dialog.open) dialog.showModal();
  }

  function closeDialog(dialog) {
    if (!dialog) return;
    dialog.close();
    var slot = dialog.querySelector(".dialog-slot");
    if (slot) slot.innerHTML = "";
  }

  function toast(message) {
    var box = document.getElementById("sd-toasts");
    if (!box || !message) return;
    var t = document.createElement("div");
    t.className = "toast";
    t.textContent = message;
    box.appendChild(t);
    setTimeout(function () { t.remove(); }, 4000);
  }
  window.sdToast = toast;

  function applyShowIf(root) {
    (root || document).querySelectorAll("[data-show-if]").forEach(function (el) {
      var form = el.closest("form") || document;
      var parts = el.dataset.showIf.split("=");
      var name = parts[0], values = (parts[1] || "").split("|");
      var input = form.querySelector('[name="' + name + '"]:checked') || form.querySelector('select[name="' + name + '"], input[name="' + name + '"]:not([type=radio])');
      var value = input ? (input.type === "checkbox" ? String(input.checked) : input.value) : "";
      var show = values[0] === "*" ? value !== "" : values.indexOf(value) !== -1;
      el.classList.toggle("hidden", !show);
      el.querySelectorAll("input, select, textarea").forEach(function (f) { f.disabled = !show; });
    });
  }

  // CSRF on every HTMX request (attribute inheritance is off, see base.html).
  document.addEventListener("htmx:configRequest", function (evt) {
    var meta = document.querySelector('meta[name="csrf-token"]');
    if (meta) evt.detail.headers["X-CSRFToken"] = meta.content;
  });

  document.addEventListener("htmx:afterSwap", function (evt) {
    openDialogFor(evt.detail.target);
    applyShowIf(evt.detail.target);
    initSteppers(evt.detail.target);
  });

  document.addEventListener("sd-close", function (evt) {
    var d = evt.target && evt.target.closest ? evt.target.closest("dialog") : null;
    closeDialog(d);
  });
  document.addEventListener("sd-toast", function (evt) {
    toast((evt.detail && (evt.detail.message || (evt.detail.value && evt.detail.value.message))) || "");
  });

  document.addEventListener("click", function (evt) {
    var t = evt.target;
    var closer = t.closest("[data-close]");
    if (closer) {
      var d = closer.closest("dialog");
      closeDialog(d);
      return;
    }
    var copy = t.closest("[data-copy]");
    if (copy) {
      var src = document.querySelector(copy.dataset.copy);
      var text = src ? src.textContent.trim() : "";
      if (navigator.clipboard) navigator.clipboard.writeText(text);
      var label = copy.textContent;
      copy.textContent = copy.dataset.copiedLabel || "Copied";
      copy.classList.add("c-green");
      setTimeout(function () { copy.textContent = label; copy.classList.remove("c-green"); }, 1500);
      return;
    }
    var tab = t.closest("[data-tab]");
    if (tab) {
      var tabs = tab.closest(".tabs");
      tabs.querySelectorAll("[data-tab]").forEach(function (b) { b.classList.toggle("active", b === tab); });
      var group = tabs.dataset.tabs;
      if (group && !tab.hasAttribute("hx-get")) {
        document.querySelectorAll('[data-tab-panel^="' + group + ':"]').forEach(function (p) {
          p.classList.toggle("hidden", p.dataset.tabPanel !== group + ":" + tab.dataset.tab);
        });
      }
      return;
    }
    var option = t.closest("[data-pick]");
    if (option) {
      var picker = option.closest(".picker");
      var hidden = picker.querySelector("input[type=hidden]");
      var shown = picker.querySelector("input[type=search]");
      hidden.value = option.dataset.pick;
      shown.value = option.dataset.label;
      picker.querySelector(".picker-results").innerHTML = "";
      hidden.dispatchEvent(new Event("change", { bubbles: true }));
      return;
    }
    if (t.closest("[data-toggle-nav]")) {
      document.getElementById("shell-navbar").classList.toggle("open");
      return;
    }
    // close picker result lists when clicking elsewhere
    document.querySelectorAll(".picker-results").forEach(function (r) { if (!r.closest(".picker").contains(t)) r.innerHTML = ""; });
    // close open menus when clicking elsewhere
    document.querySelectorAll("details.menu[open]").forEach(function (m) { if (!m.contains(t)) m.removeAttribute("open"); });
    // clicking the backdrop of a modal does not close it (Mantine default for these dialogs)
  });

  // A cleared picker search clears its value too.
  document.addEventListener("input", function (evt) {
    var picker = evt.target.closest && evt.target.closest(".picker");
    if (picker && evt.target.type === "search" && evt.target.value === "") {
      var hidden = picker.querySelector("input[type=hidden]");
      if (hidden.value) { hidden.value = ""; hidden.dispatchEvent(new Event("change", { bubbles: true })); }
    }
  });

  document.addEventListener("change", function (evt) { applyShowIf(evt.target.closest("form") || document); });

  // Contributor page: "Continue UGX 5,000" follows the amount as it is typed.
  document.addEventListener("input", function (evt) {
    if (evt.target.name !== "amount") return;
    var btn = evt.target.form && evt.target.form.querySelector("[data-continue]");
    if (!btn) return;
    var m = /^(\d+)(?:\.(\d{1,2}))?$/.exec(evt.target.value.trim());
    var ok = m && (Number(m[1]) > 0 || Number(m[2] || 0) > 0);
    var whole = m ? m[1].replace(/^0+(?=\d)/, "").replace(/\B(?=(\d{3})+(?!\d))/g, ",") : "";
    var frac = m && m[2] && Number(m[2]) ? "." + (m[2] + "0").slice(0, 2) : "";
    btn.textContent = btn.dataset.continue.replace("__AMOUNT__", ok ? "UGX " + whole + frac : "").trim();
  });

  // Dialogs with data-no-dismiss can't be closed with Escape (device token modal).
  document.addEventListener("cancel", function (evt) {
    if (evt.target.querySelector && evt.target.querySelector("[data-no-dismiss]")) evt.preventDefault();
  }, true);

  // Onboarding stepper: one form, steps shown one at a time; "Next" only when
  // the current step's required fields are valid (same as the React Stepper).
  function initSteppers(root) {
    (root || document).querySelectorAll("[data-stepper]").forEach(function (form) {
      if (form.dataset.ready) return;
      form.dataset.ready = "1";
      var steps = form.querySelectorAll("[data-step]");
      var markers = form.querySelectorAll("[data-step-marker]");
      var back = form.querySelector("[data-step-back]");
      var next = form.querySelector("[data-step-next]");
      var submit = form.querySelector("[data-step-submit]");
      var current = Number(form.dataset.start || 0);
      function valid() {
        var step = steps[current];
        if (!step) return true;
        var ok = true;
        step.querySelectorAll("input, select, textarea").forEach(function (f) { if (!f.disabled && !f.checkValidity()) ok = false; });
        var group = step.querySelector("[data-require-one]");
        if (group && !group.querySelector("input:checked")) ok = false;
        return ok;
      }
      function show() {
        steps.forEach(function (s, i) { s.classList.toggle("hidden", i !== current); });
        markers.forEach(function (m, i) { m.classList.toggle("active", i === current); m.classList.toggle("done", i < current); });
        back.disabled = current === 0;
        next.classList.toggle("hidden", current >= steps.length - 1);
        submit.classList.toggle("hidden", current < steps.length - 1);
        next.disabled = !valid();
      }
      form.addEventListener("input", show);
      form.addEventListener("change", show);
      back.addEventListener("click", function () { if (current > 0) { current--; show(); } });
      next.addEventListener("click", function () { if (valid() && current < steps.length - 1) { current++; show(); } });
      show();
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    applyShowIf(document);
    initSteppers(document);
  });
})();
