/* Get Lucky Golf — investor briefing. Reveal on scroll, the mobile deal bar
   and the ticket calculator. The calculator's inputs are written into the
   page by scripts/build_site.py from data/model.json, so the static HTML and
   the script always agree. */
(function () {
  "use strict";
  var reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  // --- reveal ---------------------------------------------------------------
  var reveals = document.querySelectorAll(".reveal");
  if (!("IntersectionObserver" in window) || reduceMotion) {
    reveals.forEach(function (el) { el.classList.add("in"); });
  } else {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) { if (e.isIntersecting) { e.target.classList.add("in"); io.unobserve(e.target); } });
    }, { rootMargin: "0px 0px -10% 0px" });
    reveals.forEach(function (el) { io.observe(el); });
  }

  // --- mobile deal bar, once the raise band has scrolled past ---------------
  var bar = document.querySelector(".dealbar");
  var band = document.getElementById("raise");
  var deal = document.getElementById("deal");
  // Measured on scroll, not observed: a jump back to the top never crosses the
  // band, so an observer would leave the bar showing over the hero.
  if (bar && band) {
    var sync = function () {
      var pastBand = band.getBoundingClientRect().bottom < 0;
      var d = deal && deal.getBoundingClientRect();
      var inDeal = d && d.top < window.innerHeight && d.bottom > 0;
      bar.classList.toggle("on", pastBand && !inDeal);
    };
    window.addEventListener("scroll", sync, { passive: true });
    window.addEventListener("resize", sync);
    sync();
  }

  // --- ticket calculator ------------------------------------------------------
  var calc = document.getElementById("calculator");
  var range = document.getElementById("calc-range");
  if (!calc || !range) return;
  var D = calc.dataset;
  var num = function (k) { return Number(D[k]); };
  var post = num("post"), fx = num("fx");
  var values = { v29: num("v29"), hard: num("vhard"), v32: num("v32") };
  var el = function (id) { return document.getElementById(id); };
  var out = { amt: el("calc-amt"), usd: el("calc-usd"), stake: el("calc-stake"),
              v29: el("calc-2029"), hard: el("calc-hard"), v32: el("calc-2032") };
  var full = function (v) { return "R" + Math.round(v).toLocaleString("en-US"); };
  var mill = function (v) { return "R" + (v / 1e6).toFixed(2) + "m"; };

  function render() {
    var amount = Number(range.value);
    var stake = amount / post;
    out.amt.textContent = full(amount);
    out.usd.textContent = "≈ $" + Math.round(amount / fx).toLocaleString("en-US");
    out.stake.textContent = (stake * 100).toFixed(2) + "%";
    ["v29", "hard", "v32"].forEach(function (k) {
      out[k].textContent = mill(stake * values[k]) + " · " + (stake * values[k] / amount).toFixed(2) + "×";
    });
    range.setAttribute("aria-valuetext", full(amount));
  }
  range.addEventListener("input", render);
  render();
})();

/* The Golfzon demo shows its three panes from 1,180px wide. On a wide page,
   render it at 1,280 x 800 and scale it to the frame; on narrow screens let
   it lay out natively (it switches to tabs on a phone). It loads only when the
   reader presses play: the demo scrolls its own panes into view as it runs,
   and loaded early it would pull this page down to it. */
(function () {
  "use strict";
  var box = document.getElementById("demo");
  if (!box) return;
  var W = Number(box.dataset.w), H = Number(box.dataset.h);
  function fit() {
    var frame = box.querySelector("iframe"), w = box.clientWidth;
    if (!frame) { box.style.height = Math.round(w * H / W) + "px"; return; }
    if (w >= 900) {
      var s = w / W;
      frame.style.width = W + "px"; frame.style.height = H + "px";
      frame.style.transform = "scale(" + s + ")";
      box.style.height = Math.round(H * s) + "px";
    } else {
      frame.style.width = "100%"; frame.style.height = "100%"; frame.style.transform = "none";
      box.style.height = "880px";
    }
  }
  var start = box.querySelector(".demo-start");
  if (start) start.addEventListener("click", function () {
    var f = document.createElement("iframe");
    f.src = box.dataset.src;
    f.title = box.dataset.title;
    f.setAttribute("allow", "fullscreen");
    f.referrerPolicy = "no-referrer";
    box.innerHTML = "";
    box.appendChild(f);
    fit();
  });
  fit();
  window.addEventListener("resize", fit);
})();
