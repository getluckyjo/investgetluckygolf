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
  if (bar && band && "IntersectionObserver" in window) {
    var pastBand = false, inDeal = false;
    var sync = function () { bar.classList.toggle("on", pastBand && !inDeal); };
    new IntersectionObserver(function (es) { es.forEach(function (e) { pastBand = !e.isIntersecting && e.boundingClientRect.top < 0; sync(); }); }).observe(band);
    if (deal) new IntersectionObserver(function (es) { es.forEach(function (e) { inDeal = e.isIntersecting; sync(); }); }).observe(deal);
  }

  // --- ticket calculator ------------------------------------------------------
  var calc = document.getElementById("calculator");
  var range = document.getElementById("calc-range");
  if (!calc || !range) return;
  var D = calc.dataset;
  var num = function (k) { return Number(D[k]); };
  var post = num("post"), fx = num("fx");
  var values = { v29: num("v29"), hard: num("vhard"), v32: num("v32") };
  // A rand of note buys what equivalent / amount rand buys in the round: the
  // better of the cap and the discount, worked out in the model.
  var gross = { round: 1, note: num("noteEquiv") / num("note") };
  var limits = {
    round: { min: num("min"), max: num("round"), step: 250000 },
    note: { min: 100000, max: num("note"), step: 50000 }
  };
  var el = function (id) { return document.getElementById(id); };
  var out = { amt: el("calc-amt"), usd: el("calc-usd"), stake: el("calc-stake"), stakeL: el("calc-stake-l"),
              v29: el("calc-2029"), hard: el("calc-hard"), v32: el("calc-2032") };
  var buttons = calc.querySelectorAll("[data-mode]");
  var mode = "round";
  var full = function (v) { return "R" + Math.round(v).toLocaleString("en-US"); };
  var mill = function (v) { return "R" + (v / 1e6).toFixed(2) + "m"; };

  function render() {
    var amount = Number(range.value);
    var stake = amount * gross[mode] / post;
    out.amt.textContent = full(amount);
    out.usd.textContent = "≈ $" + Math.round(amount / fx).toLocaleString("en-US");
    out.stakeL.textContent = mode === "note" ? "Your stake once the note converts" : "Your stake at R" + Math.round(post / 1e6) + "m post";
    out.stake.textContent = (stake * 100).toFixed(2) + "%";
    ["v29", "hard", "v32"].forEach(function (k) {
      out[k].textContent = mill(stake * values[k]) + " · " + (stake * values[k] / amount).toFixed(2) + "×";
    });
    range.setAttribute("aria-valuetext", full(amount));
  }
  function setMode(next) {
    mode = next;
    var l = limits[mode];
    range.min = l.min; range.max = l.max; range.step = l.step;
    range.value = mode === "note" ? l.max : l.min;
    buttons.forEach(function (b) { b.setAttribute("aria-pressed", String(b.getAttribute("data-mode") === mode)); });
    render();
  }
  buttons.forEach(function (b) { b.addEventListener("click", function () { setMode(b.getAttribute("data-mode")); }); });
  range.addEventListener("input", render);
  render();
})();

/* The Golfzon demo shows its three panes from 1,180px wide. On a wide page,
   render it at 1,280 x 800 and scale it to the frame; on narrow screens let
   it lay out natively (it switches to tabs on a phone). */
(function () {
  "use strict";
  var box = document.getElementById("demo");
  if (!box) return;
  var frame = box.querySelector("iframe");
  var W = Number(box.dataset.w), H = Number(box.dataset.h);
  function fit() {
    var w = box.clientWidth;
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
  fit();
  window.addEventListener("resize", fit);
})();
