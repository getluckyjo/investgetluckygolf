#!/usr/bin/env python3
"""Build index.html from data/model.json and data/facts.json.

Nothing on the page is typed twice: every figure is formatted here from the
model, so changing a driver in scripts/model.py and re-running both scripts
updates every sentence that carries it.

    python3 scripts/model.py && python3 scripts/build_site.py

The build fails if the page would carry anything on the banned list
(Golfzon's chain pricing, Ernie's percentage, superseded rounds, retired
features) or if a figure the checks expect is missing.
"""
import html, json, pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
m = json.loads((ROOT / "data/model.json").read_text())
facts = json.loads((ROOT / "data/facts.json").read_text())

FX = m["fx"]
f, d, bc, st, cash, val = m["forecast"], m["deal"], m["bayCompany"], m["structure"], m["cash"], m["valuation"]
nt, rd = d["note"], d["round"]
pt, tr, prod = m["partners"], m["traction"], m["product"]
Y = f["years"]
I = {y: k for k, y in enumerate(Y)}
rev = f["revenueZAR"]
sens = {s["key"]: s for s in val["sensitivity2029"]}
terms = {c["key"]: c for c in val["termCases"]}
plan, targets = val["cases"]["plan"], val["cases"]["targets"]
inv = bc["investors"]
mv = val["milestonesZAR"]
app, gzf, ernie = facts["app"], facts["golfzon"], facts["ernie"]
uof = d["useOfFunds"]["items"]
uof_by = {u["key"]: u for u in uof}

# ------------------------------------------------------------------ formats
neg = lambda v: "−" if v < 0 else ""
rm = lambda v, dp=1: f"{neg(v)}R{abs(v) / 1e6:.{dp}f}m"       # R12.3m
mm = lambda v: f"{neg(v)}{abs(v) / 1e6:.1f}m"                  # 12.3m, for tables
r0 = lambda v: f"R{v / 1e9:.2f}bn" if v >= 1e9 else f"R{v / 1e6:.0f}m"
x = lambda v: f"{v:.2f}×"
n = lambda v: f"{v:,}"
pc = lambda v, dp=1: f"{neg(v)}{abs(v):.{dp}f}%"
rand = lambda v: f"R{v:,}"


def usd(z):
    u = z / FX
    return f"${u / 1e6:.2f}m" if u >= 1e6 else f"${u / 1e3:.0f}k"


def esc(s):
    return html.escape(str(s), quote=True)


EMAIL = "johannes@getluckygolfclub.com"
PHONE, PHONE_TEL = "+27 60 961 5091", "+27609615091"
gz = pt["golfzon"]
pf, va = bc["chains"]["planetFitness"], bc["chains"]["virginActive"]
k27, k28, k29, k31, k32 = I[2027], I[2028], I[2029], I[2031], I[2032]
ladder = prod["saLadderZAR"]
sim_ladder = prod["simLadderUSD"]
split = prod["simSplitPct"]
unit = bc["unit"]
dc = bc["debtCover"]
q70 = sens["bayUse70"]
first_payout = next(y for y in Y if f["bayDistributionsZAR"][I[y]] > 0)


ICON = {
    "flag": '<path d="M6 21V4"/><path d="M6 5h11l-2.5 3.5L17 12H6"/>',
    "shield": '<path d="M12 3l7 3v6c0 4.5-3 7.6-7 9-4-1.4-7-4.5-7-9V6z"/><path d="M9 12l2 2 4-4"/>',
    "code": '<path d="M8 8l-4 4 4 4M16 8l4 4-4 4M13.5 5l-3 14"/>',
    "screen": '<rect x="2.5" y="4" width="19" height="12.5" rx="2"/><path d="M8 20.5h8M12 16.5v4"/>',
    "users": '<circle cx="9" cy="8" r="3.2"/><path d="M3 20c.6-3.4 3-5.4 6-5.4s5.4 2 6 5.4"/><path d="M16 4.8a3.2 3.2 0 010 6.4M21 20c-.4-2.4-1.7-4.1-3.6-4.9"/>',
    "clock": '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
    "trophy": '<path d="M8 4h8v5a4 4 0 01-8 0z"/><path d="M5 5H3v2a3 3 0 003 3M19 5h2v2a3 3 0 01-3 3M12 13v4M8 21h8M9 17h6"/>',
    "pin": '<path d="M12 21s-6.5-5.6-6.5-11a6.5 6.5 0 0113 0c0 5.4-6.5 11-6.5 11z"/><circle cx="12" cy="10" r="2.3"/>',
    "coins": '<ellipse cx="9" cy="7" rx="5.5" ry="2.5"/><path d="M3.5 7v4c0 1.4 2.5 2.5 5.5 2.5s5.5-1.1 5.5-2.5V7"/><path d="M9.5 16.4c.9.1 1.6.1 2.5.1 3 0 5.5-1.1 5.5-2.5v-3.4M14.5 11.7c3 .2 6-.8 6-2.2"/>',
    "card": '<rect x="3" y="5.5" width="18" height="13" rx="2"/><path d="M3 10h18M7 15h3"/>',
    "video": '<rect x="3" y="6.5" width="13" height="11" rx="2"/><path d="M16 10.5l5-3v9l-5-3"/>',
    "file": '<path d="M14 3H7a2 2 0 00-2 2v14a2 2 0 002 2h10a2 2 0 002-2V8z"/><path d="M14 3v5h5M9 14l2 2 4-4"/>',
    "qr": '<path d="M4 8V5a1 1 0 011-1h3M16 4h3a1 1 0 011 1v3M20 16v3a1 1 0 01-1 1h-3M8 20H5a1 1 0 01-1-1v-3"/><rect x="8.5" y="8.5" width="7" height="7" rx="1"/>',
    "key": '<circle cx="8" cy="15" r="4"/><path d="M10.8 12.2L20 3M16 7l3 3M14 9l2 2"/>',
    "globe": '<circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3a14 14 0 010 18M12 3a14 14 0 000 18"/>',
    "gym": '<path d="M6.5 6.5v11M17.5 6.5v11M3.5 9v6M20.5 9v6M6.5 12h11"/>',
    "bank": '<path d="M3 10l9-6 9 6M5 10v8M19 10v8M9.5 10v8M14.5 10v8M3 21h18"/>',
    "scale": '<path d="M12 4v16M6 20h12M5 8h14M7 8l-3 6.5a3 3 0 006 0zM17 8l-3 6.5a3 3 0 006 0z"/>',
    "lock": '<rect x="5" y="11" width="14" height="10" rx="2"/><path d="M8 11V7.5a4 4 0 018 0V11"/>',
    "rotate": '<path d="M20 12a8 8 0 11-2.4-5.7M20 4v5h-5"/>',
    "chart": '<path d="M4 20V11M10 20V5M16 20v-6M2.5 20.5h19"/>',
    "star": '<path d="M12 3.5l2.6 5.4 5.9.8-4.3 4.1 1 5.8L12 16.9l-5.2 2.7 1-5.8-4.3-4.1 5.9-.8z"/>',
}


def icon(name):
    return (f'<span class="icon-disc" aria-hidden="true"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" '
            f'stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">{ICON[name]}</svg></span>')


def more(summary, body, cls="more"):
    """A collapsed panel: the page stays short, the detail is one click away."""
    return f'<details class="{cls}"><summary>{summary}</summary><div class="body">{body}</div></details>'


# ------------------------------------------------------------------ the revenue chart
def revenue_chart():
    series = [("Golfzon network", rev["golfzon"], "#d6fb4b"), ("Bay fee", rev["bayFee"], "#8fbf7a"),
              ("The app, on course", rev["onCourse"], "#c9a94e"), ("Sponsorship", rev["sponsorship"], "rgba(245,238,222,.5)")]
    W, H, L, R, T, B = 720, 320, 56, 48, 22, 36
    top = max(rev["total"])
    step = 50e6
    ymax = step * (int(top / step) + 1)
    ph, pw = H - T - B, W - L - R
    band = pw / len(Y)
    bw = band * .56
    y_ = lambda v: T + ph - v / ymax * ph
    m_ = lambda pct: T + ph - (pct + 50) / 150 * ph          # right axis: -50% to 100%
    out = [f'<svg class="chart" viewBox="0 0 {W} {H}" role="img" aria-labelledby="chart-t chart-d">',
           '<title id="chart-t">Get Lucky\'s forecast revenue by engine, and EBITDA margin, 2027 to 2032</title>',
           '<desc id="chart-d">' + esc("; ".join(
               f"{y}: revenue {rm(rev['total'][I[y]])}, EBITDA margin {pc(f['ebitdaMarginPct'][I[y]])}" for y in Y)) + '</desc>']
    v = 0
    while v <= ymax + 1:
        yy = y_(v)
        out.append(f'<line x1="{L}" x2="{W - R}" y1="{yy:.1f}" y2="{yy:.1f}" stroke="rgba(245,238,222,.1)"/>')
        out.append(f'<text x="{L - 8}" y="{yy + 4:.1f}" text-anchor="end" font-size="11" fill="rgba(245,238,222,.6)">R{v / 1e6:.0f}m</text>')
        v += step
    for pct in (-50, 0, 50, 100):
        out.append(f'<text x="{W - R + 8}" y="{m_(pct) + 4:.1f}" font-size="11" fill="rgba(245,238,222,.6)">{pct}%</text>')
    labels = []
    for k, yr in enumerate(Y):
        cx = L + band * k + band / 2
        base = 0.0
        for name, vals, col in series:
            h = vals[k] / ymax * ph
            out.append(f'<rect x="{cx - bw / 2:.1f}" y="{y_(base + vals[k]):.1f}" width="{bw:.1f}" height="{max(h, 0):.1f}" '
                       f'fill="{col}"><title>{esc(name)} {yr}: {rm(vals[k])}</title></rect>')
            base += vals[k]
        labels.append(f'<text x="{cx:.1f}" y="{y_(base) - 8:.1f}" text-anchor="middle" font-size="12" font-weight="700" fill="#f5eede" stroke="#0c160e" stroke-width="4" paint-order="stroke">{rm(base)}</text>')
        out.append(f'<text x="{cx:.1f}" y="{H - 12}" text-anchor="middle" font-size="12" fill="rgba(245,238,222,.7)">{yr}</text>')
    pts = " ".join(f"{L + band * k + band / 2:.1f},{m_(f['ebitdaMarginPct'][k]):.1f}" for k in range(len(Y)))
    out.append(f'<polyline points="{pts}" fill="none" stroke="#f5eede" stroke-width="2" stroke-dasharray="5 4"/>')
    for k in range(len(Y)):
        out.append(f'<circle cx="{L + band * k + band / 2:.1f}" cy="{m_(f["ebitdaMarginPct"][k]):.1f}" r="3.5" fill="#f5eede">'
                   f'<title>EBITDA margin {Y[k]}: {pc(f["ebitdaMarginPct"][k])}</title></circle>')
    out += labels
    out.append("</svg>")
    legend = "".join(f'<span><i style="background:{c}"></i>{esc(nm)}</span>' for nm, _, c in series)
    legend += '<span><i style="background:transparent;border-top:2px dashed #f5eede;height:0;border-radius:0;vertical-align:4px"></i>EBITDA margin (right)</span>'
    return legend, "\n".join(out)




# ------------------------------------------------------------------ sections
# The story, in the order an investor needs it: what we do and the ask; the
# plan in four moves; proof (the app); the two engines (Golfzon, the gyms);
# Ernie; the people; the numbers; what could go wrong; the terms.

def nav():
    return """
<a class="skip" href="#main">Skip to content</a>
<nav class="nav" aria-label="Main">
  <div class="pill">
    <a class="logo" href="#top" aria-label="Get Lucky Golf, back to top"><img src="assets/logos/logo-corner.svg" alt="Get Lucky" width="52" height="40"></a>
    <div class="links">
      <a href="#app">The app</a><a href="#golfzon">Golfzon</a><a href="#gyms">The gyms</a><a href="#ernie">Ernie</a><a href="#team">Team</a><a href="#numbers">Numbers</a><a href="#deal">The raise</a>
    </div>
    <a class="btn btn-lime" href="#deal">The terms</a>
  </div>
</nav>"""


def hero():
    return f"""
<header class="hero on-dark dot-grid" id="top">
  <div class="glow" style="right:-220px;top:-160px" aria-hidden="true"></div>
  <div class="wrap hero-grid">
    <div class="copy">
      <span class="chip live"><span class="live-dot"></span>Investor briefing · October 2026</span>
      <h1 class="display-xl">Golf's biggest shot <span class="lime">goes global.</span></h1>
      <p class="lede"><strong>We sell one insured swing at a life-changing prize.</strong> We built the app and proved it on South African courses. In 2027 it goes onto Golfzon's {n(gz['locations'])} simulator locations and into golf bays in Planet Fitness and Virgin Active, with Ernie Els on board.</p>
      <div class="btns">
        <a class="btn btn-lime" href="#raise">See the raise</a>
        <a class="btn btn-outline" href="{app['url']}" target="_blank" rel="noopener">Try the app</a>
      </div>
    </div>
    <figure class="hero-photo"><img src="assets/img/ernie-ace.webp" alt="Ernie Els holding the ball from his 24th career ace" width="1000" height="1155" fetchpriority="high" style="object-position:50% 25%"><figcaption><span class="chip">Ernie Els · Founding Ambassador</span></figcaption></figure>
  </div>
  <div class="wrap">
    <div class="stats tab">
      <div class="stat"><div class="n">{n(gz['locations'])}</div><div class="l">Golfzon locations, the world's biggest simulator network</div></div>
      <div class="stat"><div class="n">{bc['totalBays']}</div><div class="l">Gym bays: {pt['planetFitness']['bays']} signed with Planet Fitness, {pt['virginActive']['bays']} in talks with Virgin Active</div></div>
      <div class="stat"><div class="n">{app['courses']}</div><div class="l">South African courses live in the app</div></div>
      <div class="stat"><div class="n"><span class="lime">{r0(ladder[-1]['prize'])}</span></div><div class="l">Top prize, insured by Santam</div></div>
    </div>
  </div>
</header>"""


def raiseband():
    return f"""
<section class="raiseband" id="raise" aria-label="The raise at a glance">
  <div class="wrap row">
    <div class="step">
      <span class="k">Step one · now · closes {esc(nt['closes'])}</span>
      <div class="n tab">{rm(nt['amountZAR'])} <small>convertible note</small></div>
      <p>Converts at a <strong>{r0(nt['capPreMoneyZAR'])} cap</strong> or a {nt['discountPct']}% discount to the round, whichever is better.</p>
    </div>
    <div class="step">
      <span class="k">Step two · {esc(rd['timing'])}</span>
      <div class="n tab">{rm(rd['amountZAR'])} <small>for {rd['equityPct']:.0f}%</small></div>
      <p>{r0(rd['preMoneyZAR'])} pre-money, {r0(rd['postMoneyZAR'])} post. {rm(rd['minimumTicketZAR'])} minimum. The bays are funded separately.</p>
    </div>
    <div class="act">
      <a class="btn btn-ink" href="#deal">The terms</a>
      <a class="btn btn-outline" href="mailto:{EMAIL}?subject=Get%20Lucky%20Golf%20%E2%80%94%20the%20note">Book a call</a>
    </div>
  </div>
</section>"""


def moves():
    return f"""
<section class="section paper" aria-labelledby="moves-h">
  <div class="wrap">
    <div class="head">
      <span class="kicker">The plan in four moves</span>
      <h2 class="display-lg" id="moves-h">The swing works. <span class="green">Now we scale it.</span></h2>
    </div>
    <div class="bento">
      <a class="tile b1 reveal" href="#app"><img src="assets/img/golf-day-scan.webp" alt="" loading="lazy" width="900" height="1350"><span class="chip live">Live</span>
        <span class="num">01</span><h3>The app</h3><p>One app runs every swing we sell.</p></a>
      <a class="tile b2 reveal" href="#golfzon"><img src="assets/img/golfzon-demo.webp" alt="" loading="lazy" width="1200" height="630"><span class="chip live">Integration built</span>
        <span class="num">02</span><h3>Golfzon</h3><p>The swing on {n(gz['locations'])} locations, verified by the bay itself.</p></a>
      <a class="tile b3 reveal" href="#gyms"><img src="assets/img/planet-golf-mobile.webp" alt="" loading="lazy" width="1672" height="941" style="object-position:30% 50%"><span class="chip live">Planet Fitness signed</span>
        <span class="num">03</span><h3>The gyms</h3><p>Golf bays in the gym, booked like padel.</p></a>
      <a class="tile b4 reveal" href="#ernie"><img src="assets/img/ernie-open.webp" alt="" loading="lazy" width="1800" height="1200" style="object-position:40% 40%"><span class="chip">Founding Ambassador</span>
        <span class="num">04</span><h3>Ernie Els</h3><p>A shareholder, not a hired face.</p></a>
    </div>
    <figure class="founder reveal">
      <blockquote>
        <p>I built The Duchess with AB InBev and RMB and took it to ten million units in five countries. What it taught me: put a simple product people love into partners who already have the customers.</p>
        <p>That's the play. Golfzon has the bays. Planet Fitness and Virgin Active have the members. Santam carries the risk. Ernie brings the moment. We built the swing and the app that runs it, and this round pays for the team and the Golfzon build, not hardware.</p>
      </blockquote>
      <figcaption><img src="assets/img/team-johannes.webp" alt="" width="44" height="44" loading="lazy"><span class="sig">Johannes</span><span class="who">Johannes le Roux, founder</span></figcaption>
    </figure>
  </div>
</section>"""


def app_section():
    lo, hi = ladder[0], ladder[-1]
    gd = facts["golfDays"]["october2026"]
    steps = [("pin", "Pick a par 3", f"{app['courses']} courses, every par 3 over {app['minPar3Metres']} m."),
             ("coins", "Pick a stake", f"{rand(lo['stake'])} to win {rand(lo['prize'])}, up to {rand(hi['stake'])} to win {r0(hi['prize'])}."),
             ("card", "Pay", "PayFast now. Apple Pay and Google Pay next."),
             ("video", "Film it", "Sealed the moment it lands, even on weak signal."),
             ("file", "Claim", "One evidence pack. Two people sign every payout.")]
    track = "".join(f'<li class="reveal">{icon(i)}<span class="no">{k + 1}</span><h3>{t}</h3><p>{d_}</p></li>' for k, (i, t, d_) in enumerate(steps))
    hood = f"""<ul>
      <li><strong>Built to be audited:</strong> about {app['testsApprox']} automated tests, error monitoring, append-only audit logs and fraud rules on every claim.</li>
      <li><strong>Golf days on their own link:</strong> every sponsored day gets a page, and every player gets a free swing. Multi-day trips and dollar prizes too. This month: {esc(gd[0])} and {esc(gd[1])}.</li>
      <li><strong>The traction above</strong> is July 2025 to July 2026, on the tee, before the app.</li>
    </ul>"""
    return f"""
<section class="section white" id="app" aria-labelledby="app-h">
  <div class="wrap">
    <div class="head">
      <span class="kicker">01 · The app</span>
      <h2 class="display-lg" id="app-h">We built it. <span class="green">It's live.</span></h2>
      <p class="lede"><strong>Pick a par 3, pick a stake, film the swing.</strong> Hole it and Santam pays, never another golfer. Live on {app['courses']} South African courses, and it installs from the browser.</p>
    </div>
    <ol class="track icons">{track}</ol>
    <div class="split" style="margin-top:28px;align-items:stretch">
      <figure class="photo reveal" style="min-height:360px"><img src="assets/img/golf-day.webp" alt="Golfers celebrate at a Get Lucky challenge tee, Cape Town Stadium behind" loading="lazy" width="1600" height="1067"><figcaption>A Get Lucky golf day, Cape Town</figcaption></figure>
      <div style="display:grid;gap:14px;align-content:start">
        <div class="card card--dark tryit reveal">
          <div class="qr"><img src="assets/logos/install-qr.svg" alt="QR code to install the Get Lucky app" width="112" height="112"></div>
          <div><h3 style="color:var(--cream);font-size:18px">Try it yourself</h3><p>Scan to install, or open <a href="{app['url']}" target="_blank" rel="noopener" style="color:var(--lime)">getluckyholeinone.com</a> on your phone.</p></div>
        </div>
        <div class="proof proof--stack tab reveal">
          <div><div class="n">{n(tr['paidSwings'])}</div><div class="l">Paid swings in our first year</div></div>
          <div><div class="n">{rm(tr['trailingRevenueZAR'])}</div><div class="l">Traded: {rm(tr['sponsorshipZAR'])} sponsorship, {rm(tr['entriesZAR'])} entries</div></div>
          <div><div class="n">{n(tr['golfDaysPerYear'])}</div><div class="l">Golf days a year, {esc(tr['partnerCourses'])} partner courses</div></div>
          <div><div class="n">{rm(pt['indwe']['sponsorship2027ZAR'], 0)}</div><div class="l">Indwe's sponsorship for 2027</div></div>
        </div>
      </div>
    </div>
    {more("Under the hood", hood)}
  </div>
</section>"""


def golfzon_section():
    kp = f["kpis"]
    rows = "".join(
        f'<tr{" class=\"total\"" if y == 2032 else ""}><td>{y}</td><td class="n">{kp["golfzonAttachPct"][I[y]]}%</td>'
        f'<td class="n hide-sm">${kp["golfzonTicketUSD"][I[y]]:.2f}</td>'
        f'<td class="n">{n(kp["golfzonSwings"][I[y]]) if kp["golfzonSwings"][I[y]] < 1e6 else f"{kp["golfzonSwings"][I[y]] / 1e6:.1f}m"}</td>'
        f'<td class="n">{rm(rev["golfzon"][I[y]])}</td></tr>' for y in Y)
    ph = gz["phases"]
    steps = [("qr", "Scan", "The QR on the bay screen arms that bay, no other."),
             ("card", "Pay", "In the Get Lucky app. Golfzon locks the hole and settings."),
             ("flag", "Swing", "One shot. Golfzon signs the record when the ball stops."),
             ("file", "Claim", "An ace opens a claim. The insurer checks the signature itself.")]
    track = "".join(f'<li class="reveal">{icon(i)}<span class="no">{k + 1}</span><h3>{t}</h3><p>{d_}</p></li>' for k, (i, t, d_) in enumerate(steps))
    insurable = f"""<ul class="secure">
      <li><span><b>Signed by Golfzon, checked by the insurer.</b> A forged ace fails.</span></li>
      <li><span><b>Settings locked and fingerprinted.</b> A venue that lowers the difficulty gets refunded, not played.</span></li>
      <li><span><b>One entry, one shot,</b> and unplayed entries expire after {gzf['entryWindowMinutes']} minutes.</span></li>
      <li><span><b>The hole rotates weekly</b> on the hardest setting, so nobody can practise it.</span></li>
    </ul>
    <p>After the broker's commission, the cover breaks even at one ace in {n(prod['simInsurerBreakEvenOneIn'])} swings. Golfzon measures about one in {n(prod['simAceMeasuredOneIn'])} across every setting. Santam has agreed in principle; the tiers are bound once priced on Golfzon's own ace data.</p>"""
    ramp = f"""<div class="tablewrap" tabindex="0" role="region" aria-label="The Golfzon ramp">
      <table>
        <thead><tr><th>The plan</th><th class="n">Share of rounds</th><th class="n hide-sm">Average swing</th><th class="n">Swings</th><th class="n">Our share</th></tr></thead>
        <tbody>{rows}</tbody>
        <caption>Our {split['getLucky']}% at R{FX:.2f} to the dollar, on {gz['roundsPerYear'] / 1e6:.0f} million rounds a year held flat. Our target is twice the share at ${targets['golfzonTicketUSD'][-1]:.0f}; the plan doesn't need it. About 94 million of those rounds are in Korea; on the rest alone the round marks at {x(sens['outsideKorea']['roundMultiple'])} in 2029.</caption>
      </table>
    </div>"""
    phases = "".join(f'<div class="phase reveal{" top" if i == 2 else ""}"><span class="k">{esc(p["when"])}</span><h3>{("On the bays", "Featured partner", "Built in")[i]}</h3></div>'
                     for i, p in enumerate(ph))
    return f"""
<section class="section on-dark band" id="golfzon" aria-labelledby="gz-h">
  <div class="bgimg" aria-hidden="true"><img src="assets/img/golfzon-course.webp" alt="" loading="lazy" width="1377" height="687"></div>
  <div class="wrap">
    <div class="head">
      <span class="kicker">02 · Golfzon</span>
      <h2 class="display-lg" id="gz-h">{n(gz['locations'])} locations. <span class="lime">Now with something to play for.</span></h2>
      <p class="lede"><strong>Golfzon is the world's biggest simulator network</strong> and the official simulator of the U.S. Open. Its bays already measure every shot. We built the integration that turns one of those shots into an insured swing at up to ${sim_ladder[-1]['prize']:,}. It's live below: take a swing.</p>
    </div>
    <figure class="reveal">
      <div class="frame demo-embed" id="demo" data-w="1280" data-h="800">
        <iframe src="{gzf['demoUrl']}" title="Live demo: the Get Lucky challenge on a Golfzon bay" loading="lazy" allow="fullscreen" referrerpolicy="no-referrer"></iframe>
      </div>
      <figcaption class="frame-cap note">The live demo we built for Golfzon: the bay, every signed message between us, and the golfer's phone. Golfzon's side is simulated. <a class="link-arrow" href="{gzf['demoUrl']}" target="_blank" rel="noopener">Open it full screen</a></figcaption>
    </figure>
    <div class="sixstats tab">
      <div class="stat"><div class="n">{n(gz['locations'])}</div><div class="l">Golfzon locations worldwide</div></div>
      <div class="stat"><div class="n">{gz['roundsPerYear'] / 1e6:.0f}M+</div><div class="l">Rounds a year, held flat in our plan</div></div>
      <div class="stat"><div class="n">U.S. Open</div><div class="l">Golfzon is its official simulator</div></div>
      <div class="stat"><div class="n"><span class="lime">${sim_ladder[-1]['prize'] // 1000}K</span></div><div class="l">Top prize: every tier pays 1,000×</div></div>
    </div>
    <ol class="track icons four" style="margin-top:40px">{track}</ol>
    <div class="split" style="margin-top:28px;align-items:end">
      <div class="reveal">
        <h3 class="display-sm" style="color:var(--cream)">What a $10 swing pays</h3>
        <div class="splitbar tab" role="img" aria-label="A ten dollar swing: {split['getLucky'] / 10:.2f} dollars to Get Lucky, {split['golfzonAndVenue'] / 10:.2f} to Golfzon and the venue, {split['insurer'] / 10:.2f} to the insurer">
          <div class="a" style="flex:{split['getLucky']}">${split['getLucky'] / 10:.2f}<span>Us {split['getLucky']}%</span></div>
          <div class="b" style="flex:{split['golfzonAndVenue']}">${split['golfzonAndVenue'] / 10:.2f}<span>Golfzon and venue</span></div>
          <div class="c" style="flex:{split['insurer']}">${split['insurer'] / 10:.2f}<span>Insurer</span></div>
        </div>
      </div>
      <div class="reveal">
        <h3 class="display-sm" style="color:var(--cream)">Golfzon's three phases</h3>
        <div class="phases compact">{phases}</div>
      </div>
    </div>
    {more("Why an insurer can cover it", insurable)}
    {more("The Golfzon numbers, year by year", ramp)}
  </div>
</section>"""


def gyms_section():
    def bay(t, label, where):
        u = unit[t]
        return f"""<div class="bay"><span class="k">{where}</span><h3>{label}</h3>
      <dl class="tab"><dt>Landed cost</dt><dd>R{u['capexZAR'] / 1e6:.2f}m</dd><dt>Booked a day</dt><dd>{u['hoursPerDay']:g} hrs at R{u['yieldZAR']}</dd>
      <dt>Revenue a year</dt><dd>R{u['revenueZAR'] / 1e6:.2f}m</dd></dl>
      <div class="foot"><span class="n">{u['paybackYears']} yrs</span><span>payback · {u['contributionMarginPct']}%<br>contribution</span></div></div>"""
    yr_rows = "".join(
        f'<tr{" class=\"total\"" if y == 2031 else ""}><td>{y}{"<span class=\"t\">PF Q1, VA mid-year</span>" if y == 2027 else ("<span class=\"t\">Fully ramped</span>" if y == 2031 else "")}</td>'
        f'<td class="n">{f["kpis"]["baysLive"][I[y]]}</td><td class="n">{rm(bc["revenueZAR"][I[y]])}</td><td class="n">{rm(bc["ebitdaZAR"][I[y]])}</td>'
        f'<td class="n">{rm(bc["debtClosingZAR"][I[y]])}</td><td class="n hide-sm">{rm(bc["feeZAR"][I[y]])}</td></tr>' for y in (2027, 2028, 2029, 2031))
    earns = f"""<div class="bays">{bay('Signature', 'Signature bay', 'Flagship clubs')}{bay('Play', 'Play bay', 'Metro clubs')}{bay('Practice', 'Practice bay', 'Smaller clubs')}</div>
    <p>A mature Golfzon TwoVision NX bay at the price from the 41st bay on. Payback is on contribution: after the gym's {bc['assumptions']['gymSharePct']}% and our {st['feePct']}% fee, before staff, finance and the first-year ramp.</p>"""
    table = f"""<div class="tablewrap" tabindex="0" role="region" aria-label="The bay company by year">
      <table>
        <thead><tr><th>The bay company</th><th class="n">Bays</th><th class="n">Revenue</th><th class="n">EBITDA</th><th class="n">Debt</th><th class="n hide-sm">Our fee</th></tr></thead>
        <tbody>{yr_rows}</tbody>
        <caption>Forecast, ex VAT, in {bc['totalClubs']} clubs once all three phases are in. EBITDA is after the gyms' {bc['assumptions']['gymSharePct']}%, our {st['feePct']}% fee, staff and the bays' own team. RMB's debt is modelled, not committed: {rm(bc['totalCapexZAR'])} of bays, {st['debtPct']}% financed over five years after a year interest-only.</caption>
      </table>
    </div>"""
    backers = f"""<p><strong>{rm(inv['calledZAR'])} between 2027 and 2029:</strong> the {st['investorEquityPct']}% on every bay, a R{st['reserveZAR'] / 1e6:.0f}m reserve, and what the bays need while they ramp. They only cover their interest and overheads from 2029, and the bay investors carry that, not Get Lucky.</p>
    <p><strong>Their capital and {st['prefPct']}% a year come back first.</strong> Payouts start once bay EBITDA covers debt service {st['distributionLockDscr']}× (RMB's lock-up). On the plan they're paid back by {inv['capitalBackBy']} and have {rm(inv['distributedZAR'])} by 2032; after that the profit splits {st['getLuckySplitPct']}/{100 - st['getLuckySplitPct']} with Get Lucky.</p>
    <p><strong>Golfzon takes half on order and half before shipment,</strong> so Planet Fitness's {esc(pt['planetFitness']['firstInstalls'])} date depends on the bay company's first close and RMB's facility.</p>"""
    return f"""
<section class="section paper" id="gyms" aria-labelledby="gyms-h">
  <div class="wrap">
    <div class="split wide-left" style="align-items:end;margin-bottom:32px">
      <div class="head" style="margin:0">
        <span class="kicker">03 · The gyms</span>
        <h2 class="display-lg" id="gyms-h">Golf bays in the gym. <span class="green">Booked like padel.</span></h2>
        <p class="lede"><strong>Planet Fitness has signed for {pt['planetFitness']['bays']} bays, first installs in {esc(pt['planetFitness']['firstInstalls'])}.</strong> Virgin Active is in talks for {pt['virginActive']['bays']} more. The gym gives us the space and the members and takes {bc['assumptions']['gymSharePct']}% of every rand. It puts in no capital.</p>
      </div>
      <figure class="photo reveal" style="aspect-ratio:16/9"><img src="assets/img/planet-golf-mobile.webp" alt="Concept render: a Planet Golf simulator bay, powered by Golfzon, in a mobile unit outside a Planet Fitness club at dusk" loading="lazy" width="1672" height="941"><figcaption>Concept: Planet Golf at a Planet Fitness club</figcaption></figure>
    </div>
    <div class="grid c2">
      <article class="party reveal">
        <div class="row"><div class="mark"><img src="assets/logos/planet-fitness.webp" alt="Planet Fitness"></div><span class="chip live">Signed</span></div>
        <div class="facts tab"><div><div class="n">{pf['bays']}</div><div class="l">Bays</div></div><div><div class="n">{pf['clubs']}</div><div class="l">Clubs</div></div><div><div class="n">{esc(pt['planetFitness']['firstInstalls'])}</div><div class="l">First bays</div></div></div>
        <p>Ten flagship clubs first, Sandton first. About <strong>{rm(pf['gymShareZAR'][k31])} a year to Planet Fitness</strong> at maturity.</p>
      </article>
      <article class="party reveal">
        <div class="row"><div class="mark"><img src="assets/logos/virgin.webp" alt="Virgin Active"></div><span class="chip talks">In talks</span></div>
        <div class="facts tab"><div><div class="n">{va['bays']}</div><div class="l">Bays</div></div><div><div class="n">{va['clubs']}</div><div class="l">Clubs</div></div><div><div class="n">{esc(pt['virginActive']['modelledFrom'])}</div><div class="l">In the plan</div></div></div>
        <p>Twenty flagship clubs first. About <strong>{rm(va['gymShareZAR'][k31])} a year to Virgin Active</strong> at maturity. Nothing is ordered until it signs.</p>
      </article>
    </div>
    <div class="split" style="margin-top:16px;align-items:stretch">
      <div style="display:grid;gap:12px">
        <div class="card iconcard reveal">{icon('clock')}<div><h3>Gym, then an hour on the sim</h3><p>Booked in the gym's app like a padel court. A R{bc['assumptions']['addOnZARpm']} add-on includes an hour a month.</p></div></div>
        <div class="card iconcard reveal">{icon('users')}<div><h3>Leagues across the chain</h3><p>Sandton against Umhlanga, on one network, with coaching in every flagship club.</p></div></div>
        <div class="card iconcard reveal">{icon('trophy')}<div><h3>The insured shot on every bay</h3><p>Half of simulator players aren't course golfers. The bay sells golf to people who'd never join a club.</p></div></div>
      </div>
      <figure class="photo reveal" style="min-height:320px"><img src="assets/img/planet-golf-rooftop.webp" alt="Concept render: a Planet Golf pavilion, powered by Golfzon, on the rooftop of a Planet Fitness Signature club at dusk" loading="lazy" width="1672" height="941" style="object-position:50% 60%"><figcaption>Concept: a Planet Golf pavilion on a Planet Fitness Signature rooftop</figcaption></figure>
    </div>

    <h3 class="display-md" style="margin:56px 0 10px">The bays sit in their own company</h3>
    <p class="lede" style="margin-bottom:20px">So your money builds the platform, not hardware. RMB lends {st['debtPct']}% of every bay and bay investors put up {st['investorEquityPct']}%. We run the bays for a fee, and share the profit once the bay investors have their money and {st['prefPct']}% a year back.</p>
    <div class="structure" role="group" aria-label="How Get Lucky and the bay company fit together">
      <div class="co you reveal"><span class="k">Where the note and the round go</span><h3>Get Lucky</h3><p>The app, Golfzon, golf days, sponsorship. Runs every bay. No bay debt, no bay capex.</p></div>
      <ul class="flows reveal">
        <li><span class="arr" aria-hidden="true"></span><b>{st['feePct']}%</b><span>of every rand the bays take, our fee for running them</span></li>
        <li><span class="arr" aria-hidden="true"></span><b>{st['getLuckySplitPct']}%</b><span>of the profit, once bay investors have their capital and {st['prefPct']}% a year</span></li>
      </ul>
      <div class="co reveal"><span class="k">Where the bays sit</span><h3>The bay company</h3><p>Owns the {bc['totalBays']} bays. RMB lends {st['debtPct']}%; bay investors put up {st['investorEquityPct']}% and a R{st['reserveZAR'] / 1e6:.0f}m reserve.</p></div>
    </div>
    <p class="note" style="margin-top:10px">The fee, the {st['prefPct']}% and the split are our proposal to the bay investors, final once they agree them.</p>
    {more("What one bay earns", earns)}
    {more("The bay company, year by year", table)}
    {more("What the bay investors put in, and get back", backers)}
  </div>
</section>"""


def ernie_section():
    return f"""
<section class="section on-dark ernie" id="ernie" aria-labelledby="ernie-h">
  <div class="bg" aria-hidden="true"><img src="assets/img/ernie-trophies.webp" alt="" loading="lazy" width="1600" height="1067"></div>
  <div class="wrap" style="position:relative">
    <div class="copy">
      <span class="kicker">04 · Ernie Els</span>
      <h2 class="display-lg" id="ernie-h">He doesn't endorse it. <span class="lime">He owns part of it.</span></h2>
      <p class="lede"><strong>Ernie is our Founding Ambassador:</strong> equity and a share of profit. No fee, no capital, no liability.</p>
      <p>{ernie['careerAces']} career aces, the latest a 5-iron from 193 yards in a senior major this May. Golfzon wants an Ernie Els challenge on its bays, and his businesses open doors in Asia, the Middle East and the US.</p>
      <ul class="honours" aria-label="Ernie Els career honours">
        <li>{ernie['majors']}× Major champion</li><li>World Golf Hall of Fame</li><li>Former world No. 1</li><li>{esc(ernie['wins'])} wins</li><li>{ernie['careerAces']} career aces</li>
      </ul>
    </div>
  </div>
</section>"""


def team_section():
    people = [
        ("team-johannes.webp", "Johannes le Roux", "Founder &amp; Managing Director", "Built The Duchess with AB InBev and RMB: ten million units in five countries. Runs Get Lucky, Golfzon and the gym roll-out."),
        ("team-andrew.webp", "Andrew Davenport", "Founder &amp; Marketing Director", "Founder of DOPE Drinks, fifteen years in drinks and entertainment brands. Runs partnerships, brand and the golf days."),
        ("team-willie.webp", "Willie Ross", "Chief Financial Officer", "Partner at Bellair Road Investment Partners, R5 billion under management. Harvard MBA. Owns the numbers and the financing."),
        ("team-ernie.webp", "Ernie Els", "Founding Ambassador", f"{ernie['majors']} majors, {esc(ernie['wins'])} wins, World Golf Hall of Fame."),
    ]
    cards = "".join(f'<div class="person reveal"><img src="assets/img/{img}" alt="" width="72" height="72" loading="lazy"><div><b>{nm}</b><span class="role">{role}</span></div><p>{bio}</p></div>'
                    for img, nm, role, bio in people)
    return f"""
<section class="section paper" id="team" aria-labelledby="team-h">
  <div class="wrap">
    <div class="head">
      <span class="kicker">05 · The team</span>
      <h2 class="display-lg" id="team-h">We've built brands <span class="green">before.</span></h2>
    </div>
    <div class="team">{cards}</div>
    <p class="note" style="margin-top:14px">Directors: Michelle Hewitt, Andrew Davenport, Johannes le Roux and Inus Smuts. The app and the Golfzon integration are built in-house.</p>
    <div class="marks" aria-label="Partners">
      <img src="assets/logos/golfzon-white.webp" alt="Golfzon">
      <img src="assets/logos/planet-fitness.webp" alt="Planet Fitness" class="pf">
      <img src="assets/logos/santam-white.png" alt="Santam" class="tall">
      <img src="assets/logos/indwe.svg" alt="Indwe Risk Services" class="indwe">
    </div>
  </div>
</section>"""


def numbers_section():
    legend, chart = revenue_chart()
    c = f["costZAR"]

    def pl_row(label, vals, cls="", note=""):
        t = f'<span class="t">{note}</span>' if note else ""
        return (f'<tr class="{cls}"><td>{label}{t}</td>' + "".join(
            f'<td class="n{" hide-sm" if y == 2028 else ""}">{vals(I[y])}</td>' for y in (2027, 2028, 2029, 2032)) + "</tr>")
    pl = "".join([
        pl_row("Golfzon network", lambda k: mm(rev["golfzon"][k]), "sub"),
        pl_row("The app, on course", lambda k: mm(rev["onCourse"][k]), "sub"),
        pl_row("Sponsorship", lambda k: mm(rev["sponsorship"][k]), "sub"),
        pl_row("Bay fee", lambda k: mm(rev["bayFee"][k]), "sub", f"{st['feePct']}% of the bay company's revenue"),
        pl_row("Revenue", lambda k: mm(rev["total"][k]), "total"),
        pl_row("EBITDA", lambda k: mm(f["ebitdaZAR"][k])),
        pl_row("EBITDA margin", lambda k: pc(f["ebitdaMarginPct"][k]), "sub"),
        pl_row("Net profit", lambda k: mm(f["netProfitZAR"][k]), "", "after tax, with the bay company's payouts"),
        pl_row("Cash at year end", lambda k: mm(cash["closingZAR"][k])),
    ])
    gz_course_cost = c["golfzonDirect"][k29] + c["onCourseDirect"][k29]
    pl_block = f"""<div class="tablewrap" tabindex="0" role="region" aria-label="Get Lucky's forecast P&amp;L">
      <table><thead><tr><th>Get Lucky, R</th><th class="n">2027</th><th class="n hide-sm">2028</th><th class="n">2029</th><th class="n">2032</th></tr></thead><tbody>{pl}</tbody></table>
    </div>
    <p>2029, revenue to EBITDA: {rm(rev['total'][k29])} revenue, less {rm(gz_course_cost)} of Golfzon and course costs (payments, claims handling, launches), {rm(c['central'][k29])} of central team and technology, and {rm(c['brand'][k29])} of brand, leaves {rm(f['ebitdaZAR'][k29])}. Central cost is a budget; the rest moves with revenue.</p>"""
    m29 = mv["2029"]
    value_block = f"""<p>Get Lucky at <strong>{val['platformMultiple']}× its revenue</strong>, the fee included, plus our share of the bay company: the bays at {val['baysEbitdaMultiple']}× EBITDA less net debt, once the bay investors have their capital and {st['prefPct']}% a year.</p>
    <div class="bridge tab">
      <div><span>Get Lucky, {val['platformMultiple']}× {rm(rev['total'][k29])}</span><span>{r0(m29['platform'])}</span></div>
      <div><span>Our share of the bay company: {val['baysEbitdaMultiple']}× {rm(bc['ebitdaZAR'][k29])}, less {rm(bc['debtClosingZAR'][k29] - bc['cashClosingZAR'][k29])} net debt and {rm(bc['hurdleClosingZAR'][k29])} still due to the bay investors</span><span>{r0(m29['bayShare'])}</span></div>
      <div class="total"><span>December 2029</span><span>{r0(m29['total'])}</span></div>
      <div class="total"><span>2032, same method</span><span>{r0(mv['2032']['total'])}</span></div>
    </div>
    <p>2027 and 2028 are build years: until the bay investors are paid back the bay company adds nothing to our value, so Get Lucky marks at {r0(mv['2027']['total'])} in December 2027 and {r0(mv['2028']['total'])} in December 2028, below the round's {r0(rd['postMoneyZAR'])}. Our half of the bay company is a proposal; at 20% the round marks at {x(terms['split20']['roundMultiple'])} in 2029.</p>"""
    order = ["plan", "halfAttach", "halfAttachHalfTicket", "noVirginActive", "hard", "outsideKorea",
             "koreaOutNoVirginActive", "bayUse70", "targets"]
    labels = {"halfAttachHalfTicket": "Half the attach and half the ticket", "hard": "The hard case: all three at once"}
    srows = "".join(
        f'<tr{" class=\"total\"" if k == "plan" else ""}><td>{esc(labels.get(k, sens[k]["case"]))}</td><td class="n hide-sm">{rm(sens[k]["revenue"])}</td>'
        f'<td class="n">{r0(sens[k]["value"])}</td><td class="n">{x(sens[k]["roundMultiple"])}</td>'
        f'<td class="n">{("Lasts to " + sens[k]["cashLastsTo"]) if sens[k]["cashLastsTo"] else rm(sens[k]["lowestCashZAR"])}</td></tr>'
        for k in order)
    stress = f"""<div class="tablewrap" tabindex="0" role="region" aria-label="2029 sensitivity">
      <table class="compact">
        <thead><tr><th>December 2029, if…</th><th class="n hide-sm">Revenue</th><th class="n">Value</th><th class="n">Round</th><th class="n">Lowest cash</th></tr></thead>
        <tbody>{srows}</tbody>
        <caption>Lowest cash is Get Lucky's lowest quarter-end from 2027 to 2032 with every cost held at plan, on calendar quarters and before working capital.</caption>
      </table>
    </div>"""
    tg_rows = [
        ("Golfzon rounds with a swing, 2032", f"{plan['golfzonAttachPct'][k32]}%", f"{targets['golfzonAttachPct'][k32]}%"),
        ("Average Golfzon swing, 2032", f"${plan['golfzonTicketUSD'][k32]:.2f}", f"${targets['golfzonTicketUSD'][k32]:.2f}"),
        ("Signature bay, hours booked a day", f"{plan['bayHoursPerDay']['Signature']:.1f}", f"{targets['bayHoursPerDay']['Signature']:.1f}"),
        ("Central cost, 2032", rm(plan["centralZAR"][k32]), rm(targets["centralZAR"][k32])),
        ("Revenue, 2029", rm(plan["revenueZAR"][k29]), rm(targets["revenueZAR"][k29])),
        ("Revenue, 2032", rm(plan["revenueZAR"][k32]), rm(targets["revenueZAR"][k32])),
        ("The round, 2032", x(plan["roundMultiple2032"]), x(targets["roundMultiple2032"])),
    ]
    tg = "".join(f"<tr><td>{a}</td><td class='n'>{b}</td><td class='n'>{c_}</td></tr>" for a, b, c_ in tg_rows)
    vs = f"""<div class="tablewrap" tabindex="0" role="region" aria-label="The plan next to our targets">
      <table class="compact"><thead><tr><th></th><th class="n">The plan</th><th class="n">Our targets</th></tr></thead><tbody>{tg}</tbody></table>
    </div>"""
    assumptions = f"""<ul>
      <li><strong>Golfzon:</strong> {gz['roundsPerYear'] / 1e6:.0f} million rounds a year held flat, about 94 million of them in Korea; rounds carrying a swing rise {" → ".join(f"{v}%" for v in plan['golfzonAttachPct'])} from 2027 to 2032, at {" → ".join(f"${v:.0f}" for v in plan['golfzonTicketUSD'][:5])} a swing. We keep {split['getLucky']}%; payments 3%, risk and support $0.05 a swing, launches 12% of our share.</li>
      <li><strong>The bays:</strong> 15 bookable hours, 360 days. Signature booked {plan['bayUtilisationPct']['Signature']}% of hours at R{unit['Signature']['yieldZAR']}, Play {plan['bayUtilisationPct']['Play']}% at R{unit['Play']['yieldZAR']}, Practice {plan['bayUtilisationPct']['Practice']}% at R{unit['Practice']['yieldZAR']}; 55% of mature use in year one, 80% in year two.</li>
      <li><strong>The app, on course:</strong> {n(f['kpis']['onCourseSwings'][0])} paid swings in 2027 ({n(tr['paidSwings'])} in our first year) rising to {n(f['kpis']['onCourseSwings'][-1])} in 2032, at R{f['kpis']['onCourseAvgZAR'][0]} to R{f['kpis']['onCourseAvgZAR'][-1]} a swing.</li>
      <li><strong>Sponsorship:</strong> Indwe's R3m is contracted for 2027 only; we assume it renews at R3m a year.</li>
      <li><strong>Get Lucky:</strong> central team {rm(plan['centralZAR'][0], 0)} in 2027 to {rm(plan['centralZAR'][-1], 0)} in 2032; brand 8% of product revenue plus a launch budget; tax at 27% after the 2027 loss. Net profit is before the Founding Ambassador's share of profit, paid from cash.</li>
    </ul>"""
    return f"""
<section class="section white" id="numbers" aria-labelledby="num-h">
  <div class="wrap">
    <div class="head">
      <span class="kicker">06 · The numbers</span>
      <h2 class="display-lg" id="num-h">{rm(rev['total'][0])} to {rm(rev['total'][-1])}. <span class="green">Our revenue, forecast.</span></h2>
      <p class="lede"><strong>This is Get Lucky's own revenue:</strong> our share of every swing, sponsorship and a {st['feePct']}% fee for running the bays. We've planned on about half of what we're aiming for, and it still works.</p>
    </div>
    <div class="chartcard reveal">
      <h3>Revenue by engine, and EBITDA margin</h3>
      <div class="legend" aria-hidden="true">{legend}</div>
      {chart}
    </div>
    <div class="kpis tab reveal">
      <div>{icon('chart')}<div><b>{cash['ebitdaPositiveFrom']}</b><span>EBITDA positive</span></div></div>
      <div>{icon('coins')}<div><b>{rm(f['ebitdaZAR'][k29])}</b><span>EBITDA in 2029, {pc(f['ebitdaMarginPct'][k29])} margin</span></div></div>
      <div>{icon('bank')}<div><b>{rm(cash['lowestQuarterZAR'])}</b><span>Lowest cash, {cash['lowestQuarter']}</span></div></div>
      <div>{icon('lock')}<div><b>None</b><span>Further equity rounds in the plan</span></div></div>
    </div>
    <div class="cases tab">
      <div class="case reveal"><span class="k">The plan</span><b>{x(rd['multiple2029'])}</b><span class="l">What {rm(rd['amountZAR'])} in the round is marked at, December 2029. {x(rd['multiple2032'])} by 2032.</span></div>
      <div class="case hard reveal"><span class="k">The hard case</span><b>{x(rd['hardCaseMultiple2029'])}</b><span class="l">Half the Golfzon attach and ticket, no Virgin Active. Cash lasts to {cash['hardCaseCashLastsTo']} without cutting a cost.</span></div>
      <div class="case up reveal"><span class="k">Our targets</span><b>{x(rd['targetsMultiple2029'])}</b><span class="l">Twice the Golfzon attach at a $10 swing, and busier bays. {x(rd['targetsMultiple2032'])} by 2032.</span></div>
    </div>
    <p class="note" style="margin-top:12px">Unrealised marks on a private holding, not cash returns. Get Lucky is valued at {val['platformMultiple']}× revenue plus our share of the bay company, and marks below the round until 2029.</p>
    {more("The full P&amp;L", pl_block)}
    {more("How we value it", value_block)}
    {more("Every stress case", stress)}
    {more("The plan next to our targets", vs)}
    {more("The assumptions that matter", assumptions)}
  </div>
</section>"""


def risk_section():
    qa = [
        ("globe", "Will Golfzon's bays carry this, and what if Korea says no?",
         f"Phase one runs on features Golfzon's bays already have, and the integration is built. Most rounds are in Korea, where paid-entry prizes still need clearing; the plan assumes 2027. On the rest of the network alone the round marks at {x(sens['outsideKorea']['roundMultiple'])}. Without Korea and without Virgin Active it's {x(sens['koreaOutNoVirginActive']['roundMultiple'])}, and cash would run to {sens['koreaOutNoVirginActive']['cashLastsTo']}; we'd cut costs long before that."),
        ("shield", "Will an insurer cover a simulator ace?",
         f"Santam has agreed in principle. After commission the cover breaks even at one ace in {n(prod['simInsurerBreakEvenOneIn'])}; Golfzon measures about one in {n(prod['simAceMeasuredOneIn'])}. That's why we play the hardest setting, rotate the hole weekly and cap entries. If the premium lands at 30%, not 24%, it comes out of our share and the round marks at {x(terms['simPremium30']['roundMultiple'])}. Indwe both sponsors us and places the cover, so a second carrier joins the panel before the simulator tiers scale."),
        ("bank", "Who pays for the bays?",
         f"The bay company, never Get Lucky. RMB is modelled at {st['debtPct']}% but hasn't committed. Bay investors put up {rm(inv['calledZAR'])} over three years, {rm(bc['investorCallsZAR'][0])} of it in 2027. Golfzon wants paying before shipment, so Planet Fitness's {esc(pt['planetFitness']['firstInstalls'])} date depends on both. This is our tightest point."),
        ("gym", "What if the bays sit empty, or Virgin Active says no?",
         f"At 70% of planned use the bays cover their debt {dc['quiet70']['2029']:.2f}× in 2029 and {dc['quiet70']['2031']:.2f}× at maturity. The bay investors carry the gap ({rm(q70['bayInvestorsCalledZAR'])} instead of {rm(inv['calledZAR'])}) and the round still marks at {x(q70['roundMultiple'])}. Without Virgin Active, {x(sens['noVirginActive']['roundMultiple'])}."),
        ("scale", "Isn't this gambling?",
         "No. It's a skill competition with an insured prize: there's no pot, and no golfer's entry funds another golfer's win. We have a written legal opinion for South Africa and clear each market before we sell there."),
    ]
    items = "".join(f'<details class="qa-item reveal"><summary>{icon(i)}<span>{q}</span></summary><div class="a"><p>{a}</p></div></details>' for i, q, a in qa)
    return f"""
<section class="section on-dark dot-grid" id="risk" aria-labelledby="risk-h" style="overflow:hidden">
  <div class="glow" style="right:-260px;top:-200px" aria-hidden="true"></div>
  <div class="wrap" style="position:relative">
    <div class="head">
      <span class="kicker">07 · The risks</span>
      <h2 class="display-lg" id="risk-h">What could go wrong, <span class="lime">and what we do about it.</span></h2>
    </div>
    <div class="qa-list">{items}</div>
  </div>
</section>"""


def deal_section():
    colours = {"team": "var(--green)", "brand": "var(--green-light)", "golfzon": "var(--lime)", "reserve": "var(--night)"}
    text_col = {"golfzon": "var(--green)"}
    order = sorted(uof, key=lambda u: -u["pct"])
    bar = "".join(
        f'<div style="flex:{u["pct"]};background:{colours[u["key"]]};color:{text_col.get(u["key"], "var(--cream)")}" title="{esc(u["label"])}, {u["pct"]}%">'
        + (f'{u["pct"]}%<span>{esc(u["label"].split(" ")[0])}</span>' if u["pct"] >= 10 else "") + "</div>" for u in order)
    labels = {"team": "Team and operations, including running the bays"}
    ulist = "".join(f'<li><i style="background:{colours[u["key"]]};{"outline:1px solid var(--line-strong)" if u["key"] == "golfzon" else ""}"></i>'
                    f'<span>{esc(labels.get(u["key"], u["label"]))}</span><b>{rm(u["ZAR"])}</b></li>' for u in order)
    calc_attrs = (f'data-post="{rd["postMoneyZAR"]}" data-round="{rd["amountZAR"]}" data-min="{rd["minimumTicketZAR"]}" '
                  f'data-note="{nt["amountZAR"]}" data-note-equiv="{nt["equivalentAtRoundZAR"]}" data-v29="{rd["value2029ZAR"]}" '
                  f'data-v32="{rd["value2032ZAR"]}" data-vhard="{rd["hardCaseValue2029ZAR"]}" data-fx="{FX}"')
    stake = rd["minimumTicketZAR"] / rd["postMoneyZAR"]
    rights = """<ul class="ticks">
      <li><div><b>Ordinary shares</b><span>The same instrument as the founders. The note converts into them.</span></div></li>
      <li><div><b>Pre-emption and tag-along</b><span>Your stake is yours to defend, and you exit when we do, at the same price.</span></div></li>
      <li><div><b>Quarterly reporting</b><span>Accounts for Get Lucky and the bay company, bays, swings, claims and the Golfzon roll-out.</span></div></li>
      <li><div><b>A board seat for the lead</b><span>No liquidation preference and no ratchet, offered or asked for.</span></div></li>
    </ul>"""
    exits = f"""<p>A simulator network that wants the prize layer on its own bays. An insurer buying distribution on risk it already carries. A leisure or gym group buying the operator of {bc['totalBays']} bays and its half of their profit. Or none of them: a cash-generative company that pays dividends.</p>"""
    return f"""
<section class="section on-dark forest raise" id="deal" aria-labelledby="deal-h">
  <div class="glow" style="left:-300px;bottom:-300px" aria-hidden="true"></div>
  <div class="wrap" style="position:relative">
    <div class="head">
      <span class="kicker">08 · The raise</span>
      <h2 class="display-lg" id="deal-h" style="color:var(--cream)">Two steps. <span class="lime">{r0(nt['amountZAR'])} now, {r0(rd['amountZAR'])} in {esc(rd['timing'])}.</span></h2>
      <p class="lede">Both into Get Lucky. The note gets us through December: the sit-down with Golfzon and Ernie at Fancourt, the first build on a real bay, and the bay company set up. The round funds the team and the Golfzon roll-out.</p>
    </div>
    <div class="terms">
      <div class="termcard reveal">
        <span class="k">Step one · now</span>
        <h3>Convertible note</h3>
        <dl class="tab">
          <dt>Amount</dt><dd>{rm(nt['amountZAR'])}<small>≈ {usd(nt['amountZAR'])}</small></dd>
          <dt>Converts at</dt><dd>A {r0(nt['capPreMoneyZAR'])} pre-money cap, or a {nt['discountPct']}% discount to the round, whichever is better</dd>
          <dt>Closes</dt><dd>{esc(nt['closes'])}, into the {esc(rd['timing'])} round</dd>
          <dt>At the round's price</dt><dd>R1m converts as R{nt['equivalentAtRoundZAR'] / 1e6:.2f}m<small>{nt['stakePct']}% of the company</small></dd>
          <dt>Marked at December 2029</dt><dd>{x(nt['multiple2029'])}<small>{x(nt['hardCaseMultiple2029'])} in the hard case</small></dd>
        </dl>
        <p class="uses">At {r0(rd['preMoneyZAR'])} pre the cap is the better price, so the note converts as if we were worth {r0(nt['conversionPreMoneyZAR'])}. It converts inside the pre-money, so the round still buys exactly {rd['equityPct']:.0f}%. Term sheet on request.</p>
      </div>
      <div class="termcard reveal">
        <span class="k">Step two · {esc(rd['timing'])}</span>
        <h3>The round</h3>
        <dl class="tab">
          <dt>Raising</dt><dd>{rm(rd['amountZAR'])} for {rd['equityPct']:.0f}%<small>≈ {usd(rd['amountZAR'])}</small></dd>
          <dt>Pre / post</dt><dd>{r0(rd['preMoneyZAR'])} / {r0(rd['postMoneyZAR'])}<small>≈ {usd(rd['preMoneyZAR'])} / {usd(rd['postMoneyZAR'])}</small></dd>
          <dt>Minimum ticket</dt><dd>{rm(rd['minimumTicketZAR'])}</dd>
          <dt>Marked at December 2029</dt><dd>{x(rd['multiple2029'])}<small>{x(rd['hardCaseMultiple2029'])} in the hard case · {x(rd['multiple2032'])} by 2032</small></dd>
        </dl>
        <p class="uses"><strong>What it pays for: our 2027</strong></p>
        <div class="usebar tab" role="img" aria-label="Use of funds: {esc(', '.join(f"{u['label']} {u['pct']}%" for u in order))}">{bar}</div>
        <ul class="uselist tab">{ulist}</ul>
        <p class="uses">No bay equity. Revenue covers part of 2027, so at our lowest point we've used {rm(cash['peakNetSpendZAR'])} and still hold {rm(cash['lowestQuarterZAR'])}. That cushion carries the hard case to {cash['hardCaseCashLastsTo']}.</p>
      </div>
    </div>

    <ol class="timeline">
      <li class="key"><time>Nov 2026</time><b>The note closes</b><span>{rm(nt['amountZAR'])} at a {r0(nt['capPreMoneyZAR'])} cap.</span></li>
      <li class="key"><time>Dec 2026</time><b>Fancourt</b><span>Sit-down with Golfzon and Ernie's team.</span></li>
      <li class="key"><time>{esc(rd['timing'])}</time><b>The round · Sandton</b><span>{rm(rd['amountZAR'])} closes. First Planet Fitness bays.</span></li>
      <li><time>Q2 2027</time><b>Golfzon phase one</b><span>Live on Golfzon bays.</span></li>
      <li><time>Mid-2027</time><b>Virgin Active</b><span>Twenty clubs, on signature.</span></li>
      <li><time>2028</time><b>{f['kpis']['baysLive'][k28]} bays</b><span>In the Golfzon app and in-game.</span></li>
      <li><time>2029</time><b>{f['kpis']['baysLive'][k29]} bays</b><span>Built into Golfzon's game.</span></li>
    </ol>

    <div class="split" style="margin-top:48px;align-items:start">
      <div class="calc reveal" id="calculator" {calc_attrs}>
        <h3>What your ticket becomes</h3>
        <div class="toggle" role="group" aria-label="Instrument">
          <button type="button" data-mode="round" aria-pressed="true">The round</button>
          <button type="button" data-mode="note" aria-pressed="false">The note</button>
        </div>
        <div class="amount tab"><span id="calc-amt">{rand(rd['minimumTicketZAR'])}</span><span class="usd" id="calc-usd">≈ ${rd['minimumTicketZAR'] / FX:,.0f}</span></div>
        <label class="sr-only" for="calc-range">Ticket in rand</label>
        <input type="range" id="calc-range" min="{rd['minimumTicketZAR']}" max="{rd['amountZAR']}" step="250000" value="{rd['minimumTicketZAR']}">
        <table class="tab" aria-live="polite">
          <caption class="sr-only">What the ticket is marked at</caption>
          <tr><th scope="row" id="calc-stake-l">Your stake at {r0(rd['postMoneyZAR'])} post</th><td id="calc-stake">{stake * 100:.2f}%</td></tr>
          <tr><th scope="row">December 2029 ({r0(rd['value2029ZAR'])})</th><td id="calc-2029">R{stake * rd['value2029ZAR'] / 1e6:.2f}m · {x(stake * rd['value2029ZAR'] / rd['minimumTicketZAR'])}</td></tr>
          <tr><th scope="row">The hard case, December 2029 ({r0(rd['hardCaseValue2029ZAR'])})</th><td id="calc-hard">R{stake * rd['hardCaseValue2029ZAR'] / 1e6:.2f}m · {x(stake * rd['hardCaseValue2029ZAR'] / rd['minimumTicketZAR'])}</td></tr>
          <tr><th scope="row">2032 ({r0(rd['value2032ZAR'])})</th><td id="calc-2032">R{stake * rd['value2032ZAR'] / 1e6:.2f}m · {x(stake * rd['value2032ZAR'] / rd['minimumTicketZAR'])}</td></tr>
        </table>
        <p class="note">Illustrative, from the plan. Unrealised marks, not cash returns.</p>
      </div>
      <div class="reveal">
        <h3 class="display-sm" style="color:var(--cream)">Your rights</h3>
        <div style="margin-top:16px">{rights}</div>
        {more("Who buys this, one day", exits)}
      </div>
    </div>
  </div>
</section>"""


def faq_section():
    qa = [
        ("What exactly am I buying?",
         f"Now: a convertible note in Get Lucky Golf Club (Pty) Ltd, {rm(nt['amountZAR'])} in total, converting into the {esc(rd['timing'])} round at a {r0(nt['capPreMoneyZAR'])} cap or a {nt['discountPct']}% discount, whichever is better for you. Then: ordinary shares, {rm(rd['amountZAR'])} for {rd['equityPct']:.0f}% at {r0(rd['preMoneyZAR'])} pre-money, from {rm(rd['minimumTicketZAR'])}. Both are in Get Lucky, not the bay company."),
        ("Why two companies?",
         f"A bay is an asset that debt can finance; the platform is a growth business that equity should. Split them and your money builds Golfzon and the team, Get Lucky carries no bay debt, and the bays are funded by investors who want an asset-backed investment that pays out. We still earn {st['feePct']}% of everything the bays take, and half their profit once the bay investors are paid back."),
        ("Can I invest in the bay company too?",
         f"Yes, separately. Bay investors put up {rm(inv['calledZAR'])} between 2027 and 2029 and take their capital and {st['prefPct']}% a year first; then the profit splits {st['getLuckySplitPct']}/{100 - st['getLuckySplitPct']} with us. Those terms are our proposal. Ask us for the bay company pack."),
        ("What does Ernie get?",
         f"Equity and a share of profit as Founding Ambassador. No fee, no capital, no guarantees, no liability. His equity is already in the {r0(rd['preMoneyZAR'])} pre-money; the full terms, including how it's treated when we issue shares, are available under NDA."),
        ("What if someone wins R1m, or $100,000?",
         "The insurer pays, and it's the best marketing day of our year. 24% of every entry goes to the insurer as premium, on the same swing that creates the risk."),
    ]
    items = "".join(f'<details><summary>{q}</summary><div class="a"><p>{a}</p></div></details>' for q, a in qa)
    return f"""
<section class="section white" id="faq" aria-labelledby="faq-h">
  <div class="wrap">
    <div class="head"><span class="kicker">Straight answers</span><h2 class="display-lg" id="faq-h">Investor FAQ</h2></div>
    <div class="faq">{items}</div>
  </div>
</section>"""


def cta_section():
    return f"""
<section class="section paper" id="contact" aria-labelledby="cta-h">
  <div class="wrap">
    <div class="cta">
      <span class="kicker" style="color:var(--green)">Next step</span>
      <h2 class="display-lg" id="cta-h">Let's talk.</h2>
      <p><strong>The note closes in {esc(nt['closes'])}.</strong> I'll take you through the model, the Golfzon demo and the Planet Fitness roll-out, and answer anything this page doesn't.</p>
      <div class="btns">
        <a class="btn btn-ink" href="mailto:{EMAIL}?subject=Get%20Lucky%20Golf%20%E2%80%94%20investor%20call">Book a call</a>
        <a class="btn btn-outline" href="{app['url']}" target="_blank" rel="noopener" style="border-color:rgba(52,82,49,.4);color:var(--green)">Try the app</a>
      </div>
      <div class="contact"><a href="mailto:{EMAIL}">{EMAIL}</a><a href="tel:{PHONE_TEL}">{PHONE}</a></div>
    </div>
  </div>
</section>"""


def footer():
    return f"""
<footer>
  <div class="wrap">
    <img src="assets/logos/logo-dark-bg.webp" alt="Get Lucky Golf Club" width="64" height="48">
    <p>Get Lucky Golf Club (Pty) Ltd · Registration 2025/047585/07 · 6 Crescent Road, Wynberg, Cape Town · <a href="mailto:{EMAIL}">{EMAIL}</a> · {PHONE}</p>
    <p>This page is an invitation to discuss a private investment and is not an offer to the public in terms of the Companies Act, 2008. Every forward-looking figure, including forecasts, valuations and the marks shown for an investment, is illustrative, based on stated assumptions and partner proposals, and is not a guarantee of return. Investment in an early-stage business carries risk, including the loss of capital. Golfzon, Planet Fitness, Virgin Active, Santam, Indwe and RMB are the marks of their owners. Images marked "concept" are renders. Independent advice is recommended.</p>
    <p>Sources: Golfzon, "Get Lucky with GOLFZON" partnership proposal, {esc(gz['proposalDate'])} · National Golf Foundation, The Golf Simulator Opportunity, 2025. Forecast as at {esc(m['asOf'])}.</p>
  </div>
</footer>
<div class="dealbar" aria-label="The raise"><span><strong>{rm(nt['amountZAR'])} note now</strong> · {rm(rd['amountZAR'])} in Q1</span><a class="btn btn-lime" href="#deal">The terms</a></div>"""


def page():
    desc = (f"Get Lucky Golf sells one insured swing at a hole-in-one. The app is live; in 2027 it goes onto Golfzon's "
            f"{n(gz['locations'])} locations and into gym bays in Planet Fitness (signed) and Virgin Active (in talks), with "
            f"Ernie Els as Founding Ambassador. A {rm(nt['amountZAR'])} convertible note now, {rm(rd['amountZAR'])} in {rd['timing']}.")
    body = "".join([nav(), hero(), '<main id="main">', raiseband(), moves(), app_section(), golfzon_section(), gyms_section(),
                    ernie_section(), team_section(), numbers_section(), risk_section(), deal_section(), faq_section(),
                    cta_section(), "</main>", footer()])
    return f"""<!DOCTYPE html>
<html lang="en-ZA">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Get Lucky Golf — Investor briefing 2027</title>
<meta name="description" content="{esc(desc)}">
<meta name="robots" content="noindex, nofollow">
<meta name="theme-color" content="#0c160e">
<meta property="og:title" content="Get Lucky Golf — Golf's biggest shot goes global">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:image" content="assets/img/golfzon-demo.webp">
<link rel="icon" type="image/png" href="assets/logos/app-icon-192.png">
<link rel="apple-touch-icon" href="assets/logos/app-icon-192.png">
<link rel="preload" href="assets/fonts/PosterGothicRoundATF-Heavy.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="assets/img/ernie-ace.webp" as="image">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Caveat:wght@500;600&display=swap" rel="stylesheet">
<link rel="stylesheet" href="css/site.css">
</head>
<body>
<script>document.body.classList.add("js")</script>
{body}
<script src="js/site.js" defer></script>
</body>
</html>
"""


# ------------------------------------------------------------------ guards
BANNED = [
    (r"\$43,000|\$40,000|\$35,000|\$32,000|\$30,000|\$25,000|\$99[ -]a[ -]month|Tier 1 pricing|Tier 2 pricing|FOB Busan|1\.3× (the )?hardware",
     "Golfzon's confidential chain pricing"),
    (r"5% non-diluting|5% of (the company's )?net profit|5% of Get Lucky|5% of any sale|founding 5%|holds 5%", "Ernie's percentage"),
    (r"R126m|R140m post|R14\.0m for 10%|R53\.3m|R8\.0m for 15%|R4\.0m for 10%", "a superseded round"),
    (r"(?i)\bregistry\b|\bgames\b|game of chance|icons cup|back an icon|\bbet(s|ting)?\b|bet on yourself|\bjackpot\b|golf gods",
     "retired features and language: games, the registry, betting"),
    (r"(?i)whatsapp|\bunlimited\b|\bpivot\b|old plan|previous plan", "retired framings"),
    (r"(?i)signed with (golfzon|virgin active)|virgin active (has )?signed|exclusive with golfzon", "a signature that does not exist"),
    (r"4,167", "the simulator break-even before commission"),
]


def main():
    out = page()
    text = re.sub(r"<[^>]+>", " ", out)
    fails = [f"{why}: {mo.group(0)!r}" for pat, why in BANNED for mo in re.finditer(pat, text)]
    must = [rm(rev["total"][0]), rm(rev["total"][-1]), x(rd["multiple2029"]), x(rd["hardCaseMultiple2029"]),
            r0(rd["preMoneyZAR"]), r0(nt["capPreMoneyZAR"]), n(gz["locations"])]
    fails += [f"missing {s!r}" for s in must if s not in out]
    if fails:
        print("build refused:\n  " + "\n  ".join(fails))
        sys.exit(1)
    (ROOT / "index.html").write_text(out)
    print(f"wrote index.html ({len(out) // 1024} KB)")


main()
