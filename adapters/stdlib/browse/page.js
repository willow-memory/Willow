// page.js: browse's one script. It fills the right panel with what is at a
// place you click, without leaving the page, and it asks for a model's
// sentence about an answer when one was asked for (--say). Every link it
// handles is a real link: with scripts off, or when the fetch fails, the
// link is followed, and code's own line is the whole reply.
(function () {
  "use strict";
  var shell = document.querySelector(".shell");
  var aside = document.getElementById("detail");
  if (!shell || !aside || !window.fetch) return;
  function show(html) {
    aside.innerHTML = html; // the page's own reply, escaped where it was made
    shell.classList.add("open");
  }
  // a model's sentence about an answer is asked for after the page is up,
  // one at a time: code's line is already there, and stands either way
  var slots = Array.prototype.slice.call(document.querySelectorAll("[data-say]"));
  (function next() {
    var el = slots.shift();
    if (!el) return;
    fetch(el.getAttribute("data-say"), { credentials: "same-origin" })
      .then(function (r) { return r.ok ? r.text() : ""; })
      .then(function (html) { el.outerHTML = html; next(); })
      .catch(next);
  })();
  document.addEventListener("click", function (e) {
    if (e.defaultPrevented || e.button !== 0 || e.metaKey || e.ctrlKey || e.shiftKey) return;
    var t = e.target.closest ? e.target : e.target.parentElement;
    if (!t) return;
    if (t.closest("[data-close]")) {
      e.preventDefault();
      aside.innerHTML = "";
      shell.classList.remove("open");
      return;
    }
    var a = t.closest("a[data-place]");
    if (!a) return;
    e.preventDefault();
    fetch(a.href + "&part=1", { credentials: "same-origin" })
      .then(function (r) { return r.ok ? r.text() : Promise.reject(r.status); })
      .then(show)
      .catch(function () { location.href = a.href; });
  });
})();
