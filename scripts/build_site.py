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
}


def icon(name):
    return (f'<span class="icon-disc" aria-hidden="true"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" '
            f'stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">{ICON[name]}</svg></span>')


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
def nav():
    return f"""
<a class="skip" href="#main">Skip to content</a>
<nav class="nav" aria-label="Main">
  <div class="pill">
    <a class="logo" href="#top" aria-label="Get Lucky Golf, back to top"><img src="assets/logos/logo-corner.svg" alt="Get Lucky" width="52" height="40"></a>
    <div class="links">
      <a href="#app">The app</a><a href="#golfzon">Golfzon</a><a href="#gyms">The gyms</a><a href="#ernie">Ernie</a><a href="#numbers">Numbers</a><a href="#deal">The raise</a>
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
      <p class="lede"><strong>One insured swing at a life-changing prize.</strong> We built the app and proved the swing on South African courses. In 2027 it goes onto Golfzon's {n(gz['locations'])} simulator locations and into golf bays inside Planet Fitness and Virgin Active, with Ernie Els as Founding Ambassador.</p>
      <div class="btns">
        <a class="btn btn-lime" href="#raise">See the raise</a>
        <a class="btn btn-outline" href="{app['url']}" target="_blank" rel="noopener">Try the app</a>
      </div>
    </div>
    <figure class="hero-photo"><img src="assets/img/ernie-ace.webp" alt="Ernie Els holding the ball from his 24th career ace" width="1000" height="1155" fetchpriority="high" style="object-position:50% 25%"><figcaption><span class="chip">Ernie Els · Founding Ambassador</span></figcaption></figure>
  </div>
  <div class="wrap">
    <div class="stats tab">
      <div class="stat"><div class="n">{n(gz['locations'])}</div><div class="l">Golfzon locations: the world's largest simulator network</div></div>
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
      <p>Converts into the round at a <strong>{r0(nt['capPreMoneyZAR'])} cap</strong> or a {nt['discountPct']}% discount, whichever is better.</p>
    </div>
    <div class="step">
      <span class="k">Step two · {esc(rd['timing'])}</span>
      <div class="n tab">{rm(rd['amountZAR'])} <small>for {rd['equityPct']:.0f}%</small></div>
      <p>{r0(rd['preMoneyZAR'])} pre-money, {r0(rd['postMoneyZAR'])} post. Minimum ticket {rm(rd['minimumTicketZAR'])}. The bays are funded in their own company.</p>
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
      <h2 class="display-lg" id="moves-h">The swing is proven. <span class="green">These four decide how big it gets.</span></h2>
    </div>
    <div class="bento">
      <a class="tile b1 reveal" href="#app"><img src="assets/img/golf-day-scan.webp" alt="" loading="lazy" width="900" height="1350"><span class="chip live">Live</span>
        <span class="num">01</span><h3>The app</h3><p>Every swing we sell runs through one app: on a course, at a golf day, and next on a simulator.</p></a>
      <a class="tile b2 reveal" href="#golfzon"><img src="assets/img/golfzon-demo.webp" alt="" loading="lazy" width="1200" height="630"><span class="chip live">Integration built</span>
        <span class="num">02</span><h3>Golfzon</h3><p>The insured swing on {n(gz['locations'])} locations, verified by the bay itself.</p></a>
      <a class="tile b3 reveal" href="#gyms"><img src="assets/img/planet-golf-mobile.webp" alt="" loading="lazy" width="1672" height="941" style="object-position:30% 50%"><span class="chip live">Planet Fitness signed</span>
        <span class="num">03</span><h3>The gyms</h3><p>Golf bays inside the gym, booked like padel. {pt['planetFitness']['bays']} signed, {pt['virginActive']['bays']} in talks.</p></a>
      <a class="tile b4 reveal" href="#ernie"><img src="assets/img/ernie-open.webp" alt="" loading="lazy" width="1800" height="1200" style="object-position:40% 40%"><span class="chip">Founding Ambassador</span>
        <span class="num">04</span><h3>Ernie Els</h3><p>A shareholder, not a hired face. His name on the moment, and his doors in Golfzon's markets.</p></a>
    </div>
  </div>
</section>"""


def app_section():
    lo, hi = ladder[0], ladder[-1]
    gd = facts["golfDays"]["october2026"]
    return f"""
<section class="section white" id="app" aria-labelledby="app-h">
  <div class="wrap">
    <div class="head">
      <span class="kicker">01 · The app</span>
      <h2 class="display-lg" id="app-h">We built it. <span class="green">It's live.</span></h2>
      <p class="lede"><strong>One app runs every swing we sell.</strong> Pick a par 3, pick a stake, film the swing. Hole it and the insurer pays the prize, never another golfer. It is live on {app['courses']} South African courses and installs from the browser, no app store needed.</p>
    </div>
    <ol class="track">
      <li class="reveal"><h3>Pick a par 3</h3><p>{app['courses']} courses, and every par 3 of {app['minPar3Metres']} m or more on them.</p></li>
      <li class="reveal"><h3>Pick a stake</h3><p>{rand(lo['stake'])} to win {rand(lo['prize'])}, up to {rand(hi['stake'])} to win {r0(hi['prize'])}.</p></li>
      <li class="reveal"><h3>Pay</h3><p>PayFast today. Apple Pay and Google Pay are built and switch on next.</p></li>
      <li class="reveal"><h3>Film the swing</h3><p>A playing partner films it. The clip is fingerprinted the moment it lands, even on weak signal.</p></li>
      <li class="reveal"><h3>Claim</h3><p>One evidence pack the insurer can check for itself. Two people sign off every payout.</p></li>
    </ol>

    <div class="split" style="margin-top:56px;align-items:stretch">
      <figure class="photo reveal" style="min-height:420px"><img src="assets/img/golf-day.webp" alt="Golfers celebrate at a Get Lucky challenge tee with Indwe and Get Lucky banners, Cape Town Stadium behind" loading="lazy" width="1600" height="1067"><figcaption>A Get Lucky golf day, Cape Town</figcaption></figure>
      <div style="display:grid;gap:22px">
        <ul class="features">
          <li class="reveal">{icon('flag')}<div><h3>Golf days on their own link</h3><p>Every sponsored day gets its own page, and every player gets a free swing. Multi-day trips and dollar prizes too.</p></div></li>
          <li class="reveal">{icon('shield')}<div><h3>Insured, not promised</h3><p>Prizes are underwritten by Santam and placed by Indwe Risk Services (FSP 3425). No golfer's stake funds another golfer's prize.</p></div></li>
          <li class="reveal">{icon('code')}<div><h3>Built to be audited</h3><p>About {app['testsApprox']} automated tests, error monitoring, append-only audit logs and fraud rules on every claim.</p></div></li>
          <li class="reveal">{icon('screen')}<div><h3>Ready for the bay</h3><p>The same app arms a Golfzon bay: scan the QR on the screen, pay, swing. No new app for the golfer to learn.</p></div></li>
        </ul>
        <div class="card card--dark tryit reveal">
          <div class="qr"><img src="assets/logos/install-qr.svg" alt="QR code to install the Get Lucky app" width="112" height="112"></div>
          <div><h3 style="color:var(--cream);font-size:18px">Try it yourself</h3><p>Scan to install the app, or open <a href="{app['url']}" target="_blank" rel="noopener" style="color:var(--lime)">getluckyholeinone.com</a> on your phone.</p></div>
        </div>
      </div>
    </div>

    <div class="proof tab reveal">
      <div><div class="n">{n(tr['paidSwings'])}</div><div class="l">Paid swings in our first twelve months</div></div>
      <div><div class="n">{rm(tr['trailingRevenueZAR'])}</div><div class="l">Traded: {rm(tr['sponsorshipZAR'])} sponsorship, {rm(tr['entriesZAR'])} entries</div></div>
      <div><div class="n">{n(tr['golfDaysPerYear'])}</div><div class="l">Golf days a year across {esc(tr['partnerCourses'])} partner courses</div></div>
      <div><div class="n">{rm(pt['indwe']['sponsorship2027ZAR'], 0)}</div><div class="l">Indwe's sponsorship for 2027, our biggest contract</div></div>
    </div>
    <p class="note" style="margin-top:14px">July 2025 to July 2026, before the app. Golf days booked onto the app this month include {esc(gd[0])} and {esc(gd[1])}.</p>
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
    ten = 10
    return f"""
<section class="section on-dark band" id="golfzon" aria-labelledby="gz-h">
  <div class="bgimg" aria-hidden="true"><img src="assets/img/golfzon-course.webp" alt="" loading="lazy" width="1377" height="687"></div>
  <div class="wrap">
    <div class="head">
      <span class="kicker">02 · Golfzon</span>
      <h2 class="display-lg" id="gz-h">{n(gz['locations'])} locations. <span class="lime">Now with something to play for.</span></h2>
      <p class="lede"><strong>Golfzon is the world's largest simulator network</strong>, with more than {gz['roundsPerYear'] / 1e6:.0f} million rounds a year, and the official simulator of the U.S. Open. Its bays already measure every shot. We built the integration that turns one of those shots into an insured swing at up to ${sim_ladder[-1]['prize']:,}.</p>
    </div>
    <figure class="reveal">
      <div class="frame demo-embed" id="demo" data-w="1280" data-h="800">
        <iframe src="{gzf['demoUrl']}" title="Live demo: the Get Lucky challenge on a Golfzon bay" loading="lazy" allow="fullscreen" referrerpolicy="no-referrer"></iframe>
      </div>
      <figcaption class="frame-cap note">This is the live demo we built for Golfzon, running: the bay, every signed message between the two systems, and the golfer's phone. Watch the one-minute tour or take a swing yourself. Golfzon's side is simulated with a demo key. <a class="link-arrow" href="{gzf['demoUrl']}" target="_blank" rel="noopener">Open it full screen</a></figcaption>
    </figure>
    <div class="sixstats tab">
      <div class="stat"><div class="n">{n(gz['locations'])}</div><div class="l">Golfzon locations worldwide</div></div>
      <div class="stat"><div class="n">{gz['roundsPerYear'] / 1e6:.0f}M+</div><div class="l">Rounds a year, held flat in our plan</div></div>
      <div class="stat"><div class="n">U.S. Open</div><div class="l">Golfzon is its official simulator</div></div>
      <div class="stat"><div class="n"><span class="lime">${sim_ladder[-1]['prize'] // 1000}K</span></div><div class="l">Top prize: every tier pays 1,000× the swing</div></div>
    </div>

    <h3 class="display-md" style="margin:56px 0 18px">How a swing works on a Golfzon bay</h3>
    <ol class="track four">
      <li class="reveal"><h3>Scan</h3><p>Scan the QR on the bay screen. It arms that bay and no other.</p></li>
      <li class="reveal"><h3>Pay</h3><p>Pay in the Get Lucky app. Golfzon loads the challenge hole and locks its settings.</p></li>
      <li class="reveal"><h3>Swing</h3><p>One swing. Golfzon signs the shot record the moment the ball stops.</p></li>
      <li class="reveal"><h3>Claim</h3><p>An ace opens a claim with the swing video. The insurer checks Golfzon's signature itself.</p></li>
    </ol>

    <div class="split" style="margin-top:56px;align-items:start">
      <div class="reveal">
        <h3 class="display-sm" style="color:var(--cream)">Why an insurer can cover it</h3>
        <ul class="secure" style="margin-top:18px">
          <li><span><b>Signed by Golfzon, checked by the insurer.</b> A forged ace fails the check.</span></li>
          <li><span><b>Settings locked and fingerprinted.</b> A venue that lowers the difficulty gets the entry refunded, not played.</span></li>
          <li><span><b>One entry, one shot.</b> The first shot counts; anything after it is logged and ignored.</span></li>
          <li><span><b>Unplayed entries expire</b> after {gzf['entryWindowMinutes']} minutes and the stake is refunded.</span></li>
          <li><span><b>The hole rotates weekly,</b> on the hardest setting with no near-cup assist, so it can't be practised.</span></li>
        </ul>
        <p class="note" style="margin-top:16px">After the broker's commission, the cover breaks even at one ace in {n(prod['simInsurerBreakEvenOneIn'])} swings. Golfzon's measured rate across every setting is about one in {n(prod['simAceMeasuredOneIn'])}. Santam has agreed in principle to cover simulator swings; the tiers are bound once priced on Golfzon's own ace data.</p>
      </div>
      <div class="reveal">
        <h3 class="display-sm" style="color:var(--cream)">What a ${ten} swing pays</h3>
        <div class="splitbar tab" role="img" aria-label="A ten dollar swing: {split['getLucky'] / 10:.2f} dollars to Get Lucky, {split['golfzonAndVenue'] / 10:.2f} to Golfzon and the venue, {split['insurer'] / 10:.2f} to the insurer">
          <div class="a" style="flex:{split['getLucky']}">${split['getLucky'] / 10:.2f}<span>Get Lucky {split['getLucky']}%</span></div>
          <div class="b" style="flex:{split['golfzonAndVenue']}">${split['golfzonAndVenue'] / 10:.2f}<span>Golfzon and venue {split['golfzonAndVenue']}%</span></div>
          <div class="c" style="flex:{split['insurer']}">${split['insurer'] / 10:.2f}<span>Insurer {split['insurer']}%</span></div>
        </div>
        <p class="note" style="margin-top:12px">Every tier, from ${sim_ladder[0]['stake']} to ${sim_ladder[-1]['stake']}, pays 1,000× the swing. The split is our proposal to Golfzon.</p>
      </div>
    </div>
    <div class="phases">
      {"".join(f'<div class="phase reveal{" top" if i == 2 else ""}"><span class="k">{esc(p["phase"])} · {esc(p["when"])}</span><h3>{("On the bays", "Featured partner", "Built in")[i]}</h3><p>{esc(p["what"])}.</p></div>' for i, p in enumerate(ph))}
    </div>
    <p class="note" style="margin-top:10px">The phases are Golfzon's own, from its {esc(gz['proposalDate'])} partnership proposal.</p>

    <div class="tablewrap reveal" tabindex="0" role="region" aria-label="The Golfzon ramp">
      <table>
        <thead><tr><th>The plan</th><th class="n">Share of rounds</th><th class="n hide-sm">Average swing</th><th class="n">Swings</th><th class="n">Our share</th></tr></thead>
        <tbody>{rows}</tbody>
        <caption>Forecast. Our {split['getLucky']}% share at R{FX:.2f} to the dollar, on {gz['roundsPerYear'] / 1e6:.0f} million rounds a year held flat. Our target is twice the share at a ${targets['golfzonTicketUSD'][-1]:.0f} average; the plan does not need it. About 94 million of those rounds are in Korea, where a paid-entry prize still needs clearing: on the rest of the network alone the round marks at {x(sens['outsideKorea']['roundMultiple'])} in 2029.</caption>
      </table>
    </div>
  </div>
</section>"""


def gyms_section():
    def bay(t, label, where):
        u = unit[t]
        return f"""<div class="bay reveal"><span class="k">{where}</span><h3>{label}</h3>
      <dl class="tab"><dt>Golfzon {esc(u['model'].split(',')[0])}</dt><dd>{esc(u['model'].split(', ')[1]) if ', ' in u['model'] else 'standard'}</dd>
      <dt>Landed cost</dt><dd>R{u['capexZAR'] / 1e6:.2f}m</dd><dt>Booked hours a day</dt><dd>{u['hoursPerDay']:g} at R{u['yieldZAR']}</dd>
      <dt>Revenue a year</dt><dd>R{u['revenueZAR'] / 1e6:.2f}m</dd></dl>
      <div class="foot"><span class="n">{u['paybackYears']} yrs</span><span>payback · {u['contributionMarginPct']}%<br>contribution</span></div></div>"""
    yr_rows = "".join(
        f'<tr{" class=\"total\"" if y == 2031 else ""}><td>{y}{"<span class=\"t\">PF Q1, VA mid-year</span>" if y == 2027 else ("<span class=\"t\">Fully ramped</span>" if y == 2031 else "")}</td>'
        f'<td class="n">{f["kpis"]["baysLive"][I[y]]}</td><td class="n">{rm(bc["revenueZAR"][I[y]])}</td><td class="n">{rm(bc["ebitdaZAR"][I[y]])}</td>'
        f'<td class="n">{rm(bc["debtClosingZAR"][I[y]])}</td><td class="n hide-sm">{rm(bc["feeZAR"][I[y]])}</td></tr>' for y in (2027, 2028, 2029, 2031))
    return f"""
<section class="section paper" id="gyms" aria-labelledby="gyms-h">
  <div class="wrap">
    <div class="split wide-left" style="align-items:end;margin-bottom:40px">
      <div class="head" style="margin:0">
        <span class="kicker">03 · The gyms</span>
        <h2 class="display-lg" id="gyms-h">Golf bays inside the gym. <span class="green">Booked like padel.</span></h2>
        <p class="lede"><strong>Planet Fitness has signed for {pt['planetFitness']['bays']} bays, first installs in {esc(pt['planetFitness']['firstInstalls'])}.</strong> Virgin Active is in talks for {pt['virginActive']['bays']} more. The gym gives the room and its members and takes {bc['assumptions']['gymSharePct']}% of every rand; it puts in no capital.</p>
      </div>
      <figure class="photo reveal" style="aspect-ratio:16/9"><img src="assets/img/planet-golf-mobile.webp" alt="Concept render: a Planet Golf simulator bay, powered by Golfzon, in a mobile unit outside a Planet Fitness club at dusk" loading="lazy" width="1672" height="941"><figcaption>Concept: Planet Golf, powered by Golfzon, at a Planet Fitness club</figcaption></figure>
    </div>

    <div class="grid c2">
      <article class="party reveal">
        <div class="row"><div class="mark"><img src="assets/logos/planet-fitness.webp" alt="Planet Fitness"></div><span class="chip live">Signed</span></div>
        <div class="facts tab"><div><div class="n">{pf['bays']}</div><div class="l">Bays</div></div><div><div class="n">{pf['clubs']}</div><div class="l">Clubs</div></div><div><div class="n">{esc(pt['planetFitness']['firstInstalls'])}</div><div class="l">First bays</div></div></div>
        <p><strong>Ten Signature and Megaclubs first, two bays each, Sandton first.</strong> Then twenty clubs in 2028 and twelve smaller clubs in 2029. About <strong>{rm(pf['gymShareZAR'][k31])} a year to Planet Fitness</strong> at maturity.</p>
      </article>
      <article class="party reveal">
        <div class="row"><div class="mark"><img src="assets/logos/virgin.webp" alt="Virgin Active"></div><span class="chip talks">In talks</span></div>
        <div class="facts tab"><div><div class="n">{va['bays']}</div><div class="l">Bays</div></div><div><div class="n">{va['clubs']}</div><div class="l">Clubs</div></div><div><div class="n">{esc(pt['virginActive']['modelledFrom'])}</div><div class="l">In the plan</div></div></div>
        <p><strong>Twenty flagship clubs first, then the metro and smaller clubs.</strong> About <strong>{rm(va['gymShareZAR'][k31])} a year to Virgin Active</strong> at maturity. Not signed, so none of its bays is ordered until it is. It added two simulator bays at a London club in September.</p>
      </article>
    </div>

    <div class="grid c3" style="margin-top:16px">
      <div class="card reveal">{icon('clock')}<h3 style="margin-top:14px">Gym, then an hour on the sim</h3><p>Booked in the gym's app by the hour, like a padel court. A R{bc['assumptions']['addOnZARpm']} a month golf add-on includes an hour and member rates.</p></div>
      <div class="card reveal">{icon('users')}<h3 style="margin-top:14px">Leagues across the chain</h3><p>Club against club, Sandton against Umhlanga, on the same network. Coaching and a golf host in every Signature club.</p></div>
      <div class="card reveal">{icon('trophy')}<h3 style="margin-top:14px">The insured shot on every bay</h3><p>The same app and the same Santam cover, from {rand(ladder[0]['stake'])} a swing. Half of simulator players are not course golfers: the bay sells golf to people who would never join a club.</p></div>
    </div>

    <figure class="photo reveal" style="aspect-ratio:2/1;margin-top:16px"><img src="assets/img/planet-golf-rooftop.webp" alt="Concept render: a Planet Golf pavilion, powered by Golfzon, on the rooftop of a Planet Fitness Signature club at dusk, beside a running track" loading="lazy" width="1672" height="941" style="object-position:50% 60%"><figcaption>Concept: a Planet Golf pavilion on a Planet Fitness Signature rooftop</figcaption></figure>

    <h3 class="display-md" style="margin:64px 0 18px">Three bays, one reference design</h3>
    <div class="bays">
      {bay('Signature', 'Signature bay', 'Flagship clubs')}
      {bay('Play', 'Play bay', 'Metro clubs')}
      {bay('Practice', 'Practice bay', 'Smaller clubs')}
    </div>
    <p class="note" style="margin-top:12px">A mature bay at the price that applies from the 41st bay on. Payback is on contribution: after the gym's {bc['assumptions']['gymSharePct']}% and our {st['feePct']}% fee, before staff, finance and the first-year ramp.</p>

    <h3 class="display-md" style="margin:64px 0 10px">The bays sit in their own company</h3>
    <p class="lede" style="margin-bottom:22px">So your money builds Golfzon and the team, not hardware. RMB lends {st['debtPct']}% of every bay; bay investors put up the other {st['investorEquityPct']}%. We run the bays for a fee and share their profit once the bay investors have their money and {st['prefPct']}% a year back.</p>
    <div class="structure" role="group" aria-label="How Get Lucky and the bay company fit together">
      <div class="co you reveal"><span class="k">Where the note and the round go</span><h3>Get Lucky</h3><p>The app, Golfzon, golf days and sponsorship. Runs every bay. No bay debt and no bay capex.</p></div>
      <ul class="flows reveal">
        <li><span class="arr" aria-hidden="true"></span><b>{st['feePct']}%</b><span>of every rand the bays take, our fee for running them</span></li>
        <li><span class="arr" aria-hidden="true"></span><b>{st['getLuckySplitPct']}%</b><span>of the profit, once the bay investors have their capital and {st['prefPct']}% a year back</span></li>
      </ul>
      <div class="co reveal"><span class="k">Where the bays sit</span><h3>The bay company</h3><p>Owns the {bc['totalBays']} bays. RMB lends {st['debtPct']}% of each one; bay investors put up the other {st['investorEquityPct']}% and a R{st['reserveZAR'] / 1e6:.0f}m reserve.</p></div>
    </div>
    <p class="note" style="margin-top:12px">The fee, the {st['prefPct']}% and the split are our proposal to the bay investors, final once they agree them.</p>

    <div class="tablewrap reveal" tabindex="0" role="region" aria-label="The bay company by year">
      <table>
        <thead><tr><th>The bay company</th><th class="n">Bays</th><th class="n">Revenue</th><th class="n">EBITDA</th><th class="n">Debt</th><th class="n hide-sm">Our fee</th></tr></thead>
        <tbody>{yr_rows}</tbody>
        <caption>Forecast, ex VAT. Bays installed by year end, in {bc['totalClubs']} clubs once all three phases are in. EBITDA is after the gyms' {bc['assumptions']['gymSharePct']}%, our {st['feePct']}% fee, staff and the bays' own central team. Debt is RMB's, modelled and not yet committed: {rm(bc['totalCapexZAR'])} of bays in all, {st['debtPct']}% financed over five years after a year interest-only.</caption>
      </table>
    </div>
    <details class="more">
      <summary>What the bay investors put in, and get back</summary>
      <div class="body">
        <p><strong>{rm(inv['calledZAR'])} between 2027 and 2029:</strong> the {st['investorEquityPct']}% on every bay, a R{st['reserveZAR'] / 1e6:.0f}m reserve, and what the bays need while they ramp. On the plan they don't cover their interest and their own overheads until 2029, and the bay investors carry that, not Get Lucky.</p>
        <p><strong>Their capital and {st['prefPct']}% a year come back first.</strong> Distributions start in 2029, once bay EBITDA covers the debt service {st['distributionLockDscr']}×, which is RMB's lock-up. On the plan the bay investors have it all back by {inv['capitalBackBy']} and {rm(inv['distributedZAR'])} paid to them by 2032. From then on the profit splits {st['getLuckySplitPct']}/{100 - st['getLuckySplitPct']} with Get Lucky.</p>
        <p><strong>Golfzon takes half on order and half before shipment,</strong> so the bay company has to be funded before a bay ships: Planet Fitness's {esc(pt['planetFitness']['firstInstalls'])} date depends on its first close and on RMB's facility being in place by then.</p>
      </div>
    </details>
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
      <p class="lede"><strong>Ernie Els is Founding Ambassador:</strong> equity and a share of profit. No fee, no capital, no liability. Santam carries the prize risk.</p>
      <p><strong>His name on the moment.</strong> One swing that changes everything is his story: {ernie['careerAces']} career aces, the latest a 5-iron from 193 yards in a senior major this May.</p>
      <p><strong>His doors, our markets.</strong> Golfzon wants an Ernie Els challenge on its bays. His course-design and Els Club businesses run across Asia, the Middle East and the US, where Golfzon is growing.</p>
      <ul class="honours" aria-label="Ernie Els career honours">
        <li>{ernie['majors']}× Major champion</li><li>World Golf Hall of Fame</li><li>Former world No. 1</li><li>{esc(ernie['wins'])} wins</li><li>{ernie['careerAces']} career aces</li>
      </ul>
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
        pl_row("Net profit", lambda k: mm(f["netProfitZAR"][k]), "", "after tax, with the bay company's payouts to us"),
        pl_row("Cash at year end", lambda k: mm(cash["closingZAR"][k])),
    ])
    gz_course_cost = c["golfzonDirect"][k29] + c["onCourseDirect"][k29]
    order = ["plan", "halfAttach", "halfAttachHalfTicket", "noVirginActive", "hard", "outsideKorea",
             "koreaOutNoVirginActive", "bayUse70", "targets"]
    labels = {"halfAttachHalfTicket": "Half the attach and half the ticket", "hard": "The hard case: all three at once"}
    srows = "".join(
        f'<tr{" class=\"total\"" if k == "plan" else ""}><td>{esc(labels.get(k, sens[k]["case"]))}</td><td class="n hide-sm">{rm(sens[k]["revenue"])}</td>'
        f'<td class="n">{r0(sens[k]["value"])}</td><td class="n">{x(sens[k]["roundMultiple"])}</td>'
        f'<td class="n">{("Lasts to " + sens[k]["cashLastsTo"]) if sens[k]["cashLastsTo"] else rm(sens[k]["lowestCashZAR"])}</td></tr>'
        for k in order)
    tg_rows = [
        ("Golfzon rounds with a swing, 2032", f"{plan['golfzonAttachPct'][k32]}%", f"{targets['golfzonAttachPct'][k32]}%"),
        ("Average Golfzon swing, 2032", f"${plan['golfzonTicketUSD'][k32]:.2f}", f"${targets['golfzonTicketUSD'][k32]:.2f}"),
        ("Signature bay, hours booked a day", f"{plan['bayHoursPerDay']['Signature']:.1f}", f"{targets['bayHoursPerDay']['Signature']:.1f}"),
        ("Central cost, 2032", rm(plan["centralZAR"][k32]), rm(targets["centralZAR"][k32])),
        ("Revenue, 2029", rm(plan["revenueZAR"][k29]), rm(targets["revenueZAR"][k29])),
        ("Revenue, 2032", rm(plan["revenueZAR"][k32]), rm(targets["revenueZAR"][k32])),
    ]
    tg = "".join(f"<tr><td>{a}</td><td class='n'>{b}</td><td class='n'>{c_}</td></tr>" for a, b, c_ in tg_rows)
    tg += (f"<tr class='total'><td>The round, December 2029</td><td class='n'>{x(plan['roundMultiple2029'])}</td><td class='n'>{x(targets['roundMultiple2029'])}</td></tr>"
           f"<tr class='total'><td>The round, 2032</td><td class='n'>{x(plan['roundMultiple2032'])}</td><td class='n'>{x(targets['roundMultiple2032'])}</td></tr>")
    m29 = mv["2029"]
    return f"""
<section class="section white" id="numbers" aria-labelledby="num-h">
  <div class="wrap">
    <div class="head">
      <span class="kicker">05 · The numbers</span>
      <h2 class="display-lg" id="num-h">{rm(rev['total'][0])} to {rm(rev['total'][-1])}. <span class="green">Get Lucky's revenue, forecast.</span></h2>
      <p class="lede"><strong>Built year by year from drivers.</strong> This is Get Lucky's own revenue: our share of every Golfzon and course swing, sponsorship, and the {st['feePct']}% fee for running the bays. The bay company's revenue is its own. The full model is available on request.</p>
    </div>
    <div class="chartcard reveal">
      <h3>Revenue by engine, and EBITDA margin</h3>
      <div class="legend" aria-hidden="true">{legend}</div>
      {chart}
    </div>
    <div class="tablewrap reveal" tabindex="0" role="region" aria-label="Get Lucky's forecast P&amp;L">
      <table>
        <thead><tr><th>Get Lucky, R</th><th class="n">2027</th><th class="n hide-sm">2028</th><th class="n">2029</th><th class="n">2032</th></tr></thead>
        <tbody>{pl}</tbody>
      </table>
    </div>

    <div class="grid c2" style="margin-top:16px">
      <div class="card reveal">
        <h3>Costed, not just forecast</h3>
        <p>Get Lucky in 2029, from revenue to EBITDA. Central cost is a budget; the rest moves with revenue.</p>
        <div class="bridge tab">
          <div><span>Revenue</span><span>{rm(rev['total'][k29])}</span></div>
          <div><span>Golfzon and course costs: payments, claims handling, launches</span><span>−{rm(gz_course_cost)}</span></div>
          <div><span>Central team, technology and markets</span><span>−{rm(c['central'][k29])}</span></div>
          <div><span>Brand</span><span>−{rm(c['brand'][k29])}</span></div>
          <div class="total"><span>EBITDA · {pc(f['ebitdaMarginPct'][k29])}</span><span>{rm(f['ebitdaZAR'][k29])}</span></div>
        </div>
      </div>
      <div class="card reveal">
        <h3>Funded to cash-generative</h3>
        <ul class="ticks" style="margin-top:14px">
          <li><div><b>The lowest quarter-end is {rm(cash['lowestQuarterZAR'])}, in {cash['lowestQuarter']}.</b><span>Tested quarter by quarter: every cost from day one, revenue back-loaded while Golfzon ramps. No bay capex and no bay debt: those sit in the bay company.</span></div></li>
          <li><div><b>In the hard case, the round lasts to {cash['hardCaseCashLastsTo']}.</b><span>Half the Golfzon attach, half the ticket and no Virgin Active, with every cost held at plan: no hire delayed, nothing cut.</span></div></li>
          <li><div><b>No further equity round in the plan.</b><span>EBITDA positive from {cash['ebitdaPositiveFrom']}. The bay company's first payout to us is in {first_payout}.</span></div></li>
        </ul>
      </div>
    </div>

    <div class="split" style="margin-top:64px;align-items:start">
      <div class="reveal">
        <h3 class="display-md">The plan is about half of what we're aiming for</h3>
        <p style="margin-top:12px;color:var(--muted)">Every forecast on this page is <strong style="color:var(--ink)">the plan</strong> unless it says targets. Our targets are what we're building for; the round doesn't need them.</p>
        <div class="tablewrap" tabindex="0" role="region" aria-label="The plan beside our targets">
          <table class="compact"><thead><tr><th></th><th class="n">The plan</th><th class="n">Our targets</th></tr></thead><tbody>{tg}</tbody></table>
        </div>
      </div>
      <div class="reveal">
        <h3 class="display-md">What Get Lucky is worth</h3>
        <p style="margin-top:12px;color:var(--muted)">Get Lucky at <strong style="color:var(--ink)">{val['platformMultiple']}× its revenue</strong>, the fee included. Plus our share of the bay company: the bays at <strong style="color:var(--ink)">{val['baysEbitdaMultiple']}× EBITDA, less their net debt</strong>, once the bay investors have their capital and {st['prefPct']}% a year.</p>
        <p style="margin-top:12px;color:var(--muted)"><strong style="color:var(--ink)">2027 and 2028 are build years, and the method says so.</strong> Until the bay investors are paid back the bay company adds nothing to our value, so Get Lucky marks at {r0(mv['2027']['total'])} in December 2027 and {r0(mv['2028']['total'])} in December 2028, below the round's {r0(rd['postMoneyZAR'])}. December 2029 is the first mark above it.</p>
        <div class="bridge tab">
          <div><span>Get Lucky, {val['platformMultiple']}× {rm(rev['total'][k29])}</span><span>{r0(m29['platform'])}</span></div>
          <div><span>Our share of the bay company: {val['baysEbitdaMultiple']}× {rm(bc['ebitdaZAR'][k29])}, less {rm(bc['debtClosingZAR'][k29] - bc['cashClosingZAR'][k29])} net debt and {rm(bc['hurdleClosingZAR'][k29])} still due to the bay investors</span><span>{r0(m29['bayShare'])}</span></div>
          <div class="total"><span>December 2029</span><span>{r0(m29['total'])}</span></div>
          <div class="total"><span>2032, same method</span><span>{r0(mv['2032']['total'])}</span></div>
        </div>
        <p class="note" style="margin-top:10px">Our half of the bay company is a proposal. At 20%, the round marks at {x(terms['split20']['roundMultiple'])} in 2029.</p>
      </div>
    </div>

    <div class="tablewrap reveal" tabindex="0" role="region" aria-label="2029 sensitivity" style="margin-top:40px">
      <table class="compact">
        <thead><tr><th>December 2029, if…</th><th class="n hide-sm">Revenue</th><th class="n">Value</th><th class="n">Round</th><th class="n">Lowest cash</th></tr></thead>
        <tbody>{srows}</tbody>
        <caption>What {rm(rd['amountZAR'])} in the round is marked at in December 2029, on the same method. Unrealised marks on a private holding, not cash returns. Lowest cash is Get Lucky's lowest quarter-end from 2027 to 2032 with every cost held at plan, on calendar quarters and before working capital. It is the test the round is sized to.</caption>
      </table>
    </div>
    <details class="more">
      <summary>The assumptions that matter</summary>
      <div class="body"><ul>
        <li><strong>Golfzon:</strong> {gz['roundsPerYear'] / 1e6:.0f} million rounds a year held flat, about 94 million of them in Korea; the share of rounds carrying a swing rises {" → ".join(f"{v}%" for v in plan['golfzonAttachPct'])} from 2027 to 2032, at an average swing of {" → ".join(f"${v:.0f}" for v in plan['golfzonTicketUSD'][:5])}. We keep {split['getLucky']}%. Payments 3% of gross, $0.05 a swing in risk and support, launches at 12% of our share.</li>
        <li><strong>The bay company:</strong> 15 bookable hours a day, 360 days. Signature bays booked {plan['bayUtilisationPct']['Signature']}% of those hours at R{unit['Signature']['yieldZAR']}, Play {plan['bayUtilisationPct']['Play']}% at R{unit['Play']['yieldZAR']}, Practice {plan['bayUtilisationPct']['Practice']}% at R{unit['Practice']['yieldZAR']}. 55% of mature use in a bay's first year, 80% in its second. A R{bc['assumptions']['addOnZARpm']} add-on taken by 1.5% of members at clubs with bays. Our fee {st['feePct']}% of its revenue; its own tax at 27%.</li>
        <li><strong>The app, on course:</strong> {n(m['forecast']['kpis']['onCourseSwings'][0])} paid swings in 2027 ({n(tr['paidSwings'])} in our first twelve months) rising to {n(m['forecast']['kpis']['onCourseSwings'][-1])} in 2032, at an average of R{m['forecast']['kpis']['onCourseAvgZAR'][0]} rising to R{m['forecast']['kpis']['onCourseAvgZAR'][-1]}.</li>
        <li><strong>Sponsorship:</strong> Indwe's R3m is contracted for 2027 only. The plan assumes it renews at R3m a year to 2032, with no growth and no new territories.</li>
        <li><strong>Get Lucky:</strong> central team {rm(plan['centralZAR'][0], 0)} in 2027 rising to {rm(plan['centralZAR'][-1], 0)} in 2032; brand 8% of Golfzon, course and sponsorship revenue plus a fixed launch budget. Tax at 27% after the 2027 loss; the bay company's payouts to us are dividends. Net profit is before the Founding Ambassador's share of profit, which the model pays out of cash.</li>
        <li><strong>Timing:</strong> the round lands in {esc(rd['timing'])}. Planet Fitness's first bays in {esc(pt['planetFitness']['firstInstalls'])}, Virgin Active's from mid-2027, each phase paid for the quarter before it goes live.</li>
      </ul></div>
    </details>
  </div>
</section>"""


def risk_section():
    return f"""
<section class="section on-dark dot-grid" id="risk" aria-labelledby="risk-h" style="overflow:hidden">
  <div class="glow" style="right:-260px;top:-200px" aria-hidden="true"></div>
  <div class="wrap" style="position:relative">
    <div class="head">
      <span class="kicker">Straight about the risk</span>
      <h2 class="display-lg" id="risk-h">The questions we get asked first.</h2>
    </div>
    <div class="risks">
      <article class="card--glass reveal">
        <h3>Will Golfzon's bays carry this, and what if Korea says no?</h3>
        <p><strong>Phase one needs nothing new from Golfzon.</strong> Its proposal runs the challenge on competition features its bays already have, and we built the working integration. Building it into the game goes through Golfzon's product, engineering and legal review, which is why the plan starts at one round in two thousand.</p>
        <p><strong>Most of the network's rounds are in Korea,</strong> where a paid-entry prize needs clearing. The plan assumes it clears in 2027, so we publish the case without it: on the rest of the network alone, the round marks at {x(sens['outsideKorea']['roundMultiple'])} in 2029. Outside Korea and without Virgin Active, {x(sens['koreaOutNoVirginActive']['roundMultiple'])}, and with every cost held at plan the round lasts to {sens['koreaOutNoVirginActive']['cashLastsTo']}: we would cut costs before then.</p>
      </article>
      <article class="card--glass reveal">
        <h3>Will an insurer cover a simulator ace?</h3>
        <p><strong>Santam has agreed in principle to cover simulator swings.</strong> After the broker's commission the cover breaks even at one ace in {n(prod['simInsurerBreakEvenOneIn'])} swings; Golfzon's measured rate is about one in {n(prod['simAceMeasuredOneIn'])}, which is why the challenge runs on the hardest setting with a rotating hole and capped entries. If the tiers are priced above {split['insurer']}%, the difference comes out of our {split['getLucky']}%: at 30%, the round marks at {x(terms['simPremium30']['roundMultiple'])} in 2029.</p>
        <p><strong>Indwe both sponsors us and earns commission placing the cover.</strong> The book is built to suit any prize-indemnity underwriter, and a second carrier comes onto the panel before the simulator tiers scale.</p>
      </article>
      <article class="card--glass reveal">
        <h3>Who pays for the bays?</h3>
        <p><strong>The bay company, not the round.</strong> RMB has modelled {st['debtPct']}% of each bay's landed cost but has not committed. The bay investors put up the other {st['investorEquityPct']}%, a R{st['reserveZAR'] / 1e6:.0f}m reserve and what the bays need while they ramp: {rm(inv['calledZAR'])} between 2027 and 2029, {rm(bc['investorCallsZAR'][0])} of it in 2027.</p>
        <p><strong>This is the plan's tightest point.</strong> Golfzon wants paying before shipment, so no bay is ordered until both are in place, and Planet Fitness's {esc(pt['planetFitness']['firstInstalls'])} date depends on that. If the bay company's raise is slow, the bays wait and our fee waits with them; Get Lucky never pays for a bay.</p>
      </article>
      <article class="card--glass reveal">
        <h3>What if the bays sit empty, or Virgin Active says no?</h3>
        <p><strong>The plan books a Signature bay for {unit['Signature']['hoursPerDay']:g} of its fifteen hours a day,</strong> and the others for less. At 70% of the plan, bay EBITDA covers the debt service {dc['quiet70']['2029']:.2f}× in 2029 and {dc['quiet70']['2031']:.2f}× at maturity. The bay investors carry that gap, putting in {rm(q70['bayInvestorsCalledZAR'])} rather than {rm(inv['calledZAR'])}, nothing is paid out to Get Lucky before 2032, and the round marks at {x(q70['roundMultiple'])} in 2029.</p>
        <p><strong>Without Virgin Active,</strong> Get Lucky's 2029 revenue is {rm(sens['noVirginActive']['revenue'])} and the round marks at {x(sens['noVirginActive']['roundMultiple'])}.</p>
      </article>
      <article class="card--glass reveal">
        <h3>Isn't this gambling?</h3>
        <p><strong>It is a skill competition with an insured prize.</strong> An entry fee to us and a prize paid by our insurer: no golfer's entry funds another's win, so there is no pot and no counterparty. A written legal opinion covers South Africa, and each market is cleared before we sell there, with Golfzon's legal team on its own territories.</p>
      </article>
    </div>
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
    nuses = nt["useOfFunds"]
    calc_attrs = (f'data-post="{rd["postMoneyZAR"]}" data-round="{rd["amountZAR"]}" data-min="{rd["minimumTicketZAR"]}" '
                  f'data-note="{nt["amountZAR"]}" data-note-equiv="{nt["equivalentAtRoundZAR"]}" data-v29="{rd["value2029ZAR"]}" '
                  f'data-v32="{rd["value2032ZAR"]}" data-vhard="{rd["hardCaseValue2029ZAR"]}" data-fx="{FX}"')
    stake = rd["minimumTicketZAR"] / rd["postMoneyZAR"]
    return f"""
<section class="section on-dark forest raise" id="deal" aria-labelledby="deal-h">
  <div class="glow" style="left:-300px;bottom:-300px" aria-hidden="true"></div>
  <div class="wrap" style="position:relative">
    <div class="head">
      <span class="kicker">06 · The raise</span>
      <h2 class="display-lg" id="deal-h" style="color:var(--cream)">Two steps. <span class="lime">{r0(nt['amountZAR'])} now, {r0(rd['amountZAR'])} in {esc(rd['timing'])}.</span></h2>
      <p class="lede">Both into Get Lucky. The note funds December: the sit-down with Golfzon and Ernie at Fancourt, the first integration build on a real bay, and the bay company's set-up. The round builds Golfzon and the team.</p>
    </div>
    <div class="terms">
      <div class="termcard reveal">
        <span class="k">Step one · now</span>
        <h3>Convertible note</h3>
        <dl class="tab">
          <dt>Amount</dt><dd>{rm(nt['amountZAR'])}<small>≈ {usd(nt['amountZAR'])}</small></dd>
          <dt>Converts at</dt><dd>A {r0(nt['capPreMoneyZAR'])} pre-money cap, or a {nt['discountPct']}% discount to the round, whichever is better</dd>
          <dt>Converts into</dt><dd>{esc(nt['convertsInto'])}</dd>
          <dt>Closes</dt><dd>{esc(nt['closes'])}</dd>
          <dt>At the round's price</dt><dd>R1m converts as R{nt['equivalentAtRoundZAR'] / 1e6:.2f}m<small>{nt['stakePct']}% of the company</small></dd>
          <dt>Conversion</dt><dd>Inside the {r0(rd['preMoneyZAR'])} pre-money</dd>
          <dt>Marked at December 2029</dt><dd>{x(nt['multiple2029'])}<small>{x(nt['hardCaseMultiple2029'])} in the hard case</small></dd>
          <dt>Full terms</dt><dd>Term sheet on request</dd>
        </dl>
        <p class="uses"><strong>What it funds:</strong> {esc(nuses[0][0].lower() + nuses[0][1:])}; {esc(nuses[1][0].lower() + nuses[1][1:])}; {esc(nuses[2][0].lower() + nuses[2][1:])}; and {esc(nuses[3][0].lower() + nuses[3][1:])}. At {r0(rd['preMoneyZAR'])} pre the cap is the better price, so the note converts as if the company were worth {r0(nt['conversionPreMoneyZAR'])}. The conversion is inside the pre-money, so the round still buys exactly {rd['equityPct']:.0f}%.</p>
      </div>
      <div class="termcard reveal">
        <span class="k">Step two · {esc(rd['timing'])}</span>
        <h3>The round</h3>
        <dl class="tab">
          <dt>Raising</dt><dd>{rm(rd['amountZAR'])}<small>≈ {usd(rd['amountZAR'])}</small></dd>
          <dt>Equity</dt><dd>{rd['equityPct']:.0f}%</dd>
          <dt>Pre-money</dt><dd>{r0(rd['preMoneyZAR'])}<small>≈ {usd(rd['preMoneyZAR'])}</small></dd>
          <dt>Post-money</dt><dd>{r0(rd['postMoneyZAR'])}<small>≈ {usd(rd['postMoneyZAR'])}</small></dd>
          <dt>Minimum ticket</dt><dd>{rm(rd['minimumTicketZAR'])}</dd>
          <dt>Marked at December 2029</dt><dd>{x(rd['multiple2029'])}<small>{x(rd['hardCaseMultiple2029'])} in the hard case</small></dd>
          <dt>Marked at 2032</dt><dd>{x(rd['multiple2032'])}</dd>
        </dl>
        <p class="uses"><strong>What it funds: Get Lucky's 2027</strong></p>
        <div class="usebar tab" role="img" aria-label="Use of funds: {esc(', '.join(f"{u['label']} {u['pct']}%" for u in order))}">{bar}</div>
        <ul class="uselist tab">{ulist}</ul>
        <p class="uses">No bay equity: the bays are funded in the bay company. Revenue pays for part of 2027, so at its lowest the plan has used {rm(cash['peakNetSpendZAR'])} and never ends a quarter below {rm(cash['lowestQuarterZAR'])} in the plan. That {rm(cash['lowestQuarterZAR'])} is what carries the hard case to {cash['hardCaseCashLastsTo']}.</p>
      </div>
    </div>

    <ol class="timeline">
      <li class="key"><time>Nov 2026</time><b>The note closes</b><span>{rm(nt['amountZAR'])} at a {r0(nt['capPreMoneyZAR'])} cap.</span></li>
      <li class="key"><time>Dec 2026</time><b>Fancourt</b><span>The sit-down with Golfzon and Ernie's team.</span></li>
      <li class="key"><time>{esc(rd['timing'])}</time><b>The round · Sandton</b><span>{rm(rd['amountZAR'])} closes. The first Planet Fitness bays open.</span></li>
      <li><time>Q2 2027</time><b>Golfzon phase one</b><span>The challenge live on Golfzon bays.</span></li>
      <li><time>Mid-2027</time><b>Virgin Active</b><span>Twenty flagship clubs, on signature.</span></li>
      <li><time>2028</time><b>{f['kpis']['baysLive'][k28]} bays</b><span>Golfzon phase two: in the app and in-game.</span></li>
      <li><time>2029</time><b>{f['kpis']['baysLive'][k29]} bays</b><span>Golfzon phase three: built into the game.</span></li>
    </ol>

    <div class="split" style="margin-top:56px;align-items:start">
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
          <tr><th scope="row">Marked at December 2029 ({r0(rd['value2029ZAR'])})</th><td id="calc-2029">R{stake * rd['value2029ZAR'] / 1e6:.2f}m · {x(stake * rd['value2029ZAR'] / rd['minimumTicketZAR'])}</td></tr>
          <tr><th scope="row">The hard case, December 2029 ({r0(rd['hardCaseValue2029ZAR'])})</th><td id="calc-hard">R{stake * rd['hardCaseValue2029ZAR'] / 1e6:.2f}m · {x(stake * rd['hardCaseValue2029ZAR'] / rd['minimumTicketZAR'])}</td></tr>
          <tr><th scope="row">Marked at 2032 ({r0(rd['value2032ZAR'])})</th><td id="calc-2032">R{stake * rd['value2032ZAR'] / 1e6:.2f}m · {x(stake * rd['value2032ZAR'] / rd['minimumTicketZAR'])}</td></tr>
        </table>
        <p class="note">Illustrative, from the published plan. Unrealised marks, not cash returns.</p>
      </div>
      <div class="reveal">
        <h3 class="display-sm" style="color:var(--cream)">Your rights, and the way out</h3>
        <ul class="ticks" style="margin-top:18px">
          <li><div><b style="color:var(--cream)">Ordinary shares</b><span>The same instrument as the founders. The note converts into them.</span></div></li>
          <li><div><b style="color:var(--cream)">Pre-emption and tag-along</b><span>Your stake is yours to defend, and you exit when the founders do, at the same price.</span></div></li>
          <li><div><b style="color:var(--cream)">Quarterly reporting</b><span>Accounts for Get Lucky and the bay company, bays, swings, claims and the Golfzon roll-out.</span></div></li>
          <li><div><b style="color:var(--cream)">A board seat for the lead investor</b><span>No liquidation preference and no ratchet, offered or asked for.</span></div></li>
        </ul>
        <p style="margin-top:22px"><strong>Who buys this:</strong> a simulator network that wants the prize layer on its own bays; an insurer buying the distribution on risk it already carries; a leisure or gym group buying the operator of {bc['totalBays']} bays and its half of their profit. Or none of them: a cash-generative company that pays dividends.</p>
      </div>
    </div>
  </div>
</section>"""


def team_section():
    people = [
        ("team-johannes.webp", "Johannes le Roux", "Founder &amp; Managing Director", "Built The Duchess with AB InBev and RMB: ten million units in five countries. Leads Get Lucky, the Golfzon partnership and the gym roll-out."),
        ("team-andrew.webp", "Andrew Davenport", "Founder &amp; Marketing Director", "Founder of DOPE Drinks, fifteen years in beverage and entertainment brands. Runs partnerships, brand, the golf days and the leagues that keep bays busy."),
        ("team-willie.webp", "Willie Ross", "Chief Financial Officer", "Partner at Bellair Road Investment Partners, R5 billion under management. Harvard MBA. Owns the numbers and the financing."),
        ("team-ernie.webp", "Ernie Els", "Founding Ambassador", f"{ernie['majors']} majors, {esc(ernie['wins'])} wins, World Golf Hall of Fame. A shareholder with a share of profit, not a hired face."),
    ]
    cards = "".join(f'<div class="person reveal"><img src="assets/img/{img}" alt="" width="72" height="72" loading="lazy"><div><b>{nm}</b><span class="role">{role}</span></div><p>{bio}</p></div>'
                    for img, nm, role, bio in people)
    return f"""
<section class="section paper" id="team" aria-labelledby="team-h">
  <div class="wrap">
    <div class="head">
      <span class="kicker">The people you would back</span>
      <h2 class="display-lg" id="team-h">Operators who have built brands before.</h2>
    </div>
    <div class="team">{cards}</div>
    <p class="note" style="margin-top:16px">Directors: Michelle Hewitt, Andrew Davenport, Johannes le Roux and Inus Smuts. The app and the Golfzon integration are built in-house.</p>
    <div class="marks" aria-label="Partners">
      <img src="assets/logos/golfzon-white.webp" alt="Golfzon">
      <img src="assets/logos/planet-fitness.webp" alt="Planet Fitness" class="pf">
      <img src="assets/logos/santam-white.png" alt="Santam" class="tall">
      <img src="assets/logos/indwe.svg" alt="Indwe Risk Services" class="indwe">
    </div>
  </div>
</section>"""


def faq_section():
    qa = [
        ("What exactly am I buying?",
         f"Now: a convertible note in Get Lucky Golf Club (Pty) Ltd, {rm(nt['amountZAR'])} in total, converting into the {esc(rd['timing'])} round at a {r0(nt['capPreMoneyZAR'])} pre-money cap or a {nt['discountPct']}% discount to its price, whichever is better for you. In {esc(rd['timing'])}: ordinary shares, {rm(rd['amountZAR'])} for {rd['equityPct']:.0f}% at {r0(rd['preMoneyZAR'])} pre-money and {r0(rd['postMoneyZAR'])} post, from a {rm(rd['minimumTicketZAR'])} minimum. The note converts inside the pre-money, so the round buys exactly {rd['equityPct']:.0f}%. Both are in Get Lucky, not the bay company."),
        ("Why two companies?",
         f"Because the bays and the platform are different investments. A bay is an asset that debt can finance; the platform is a growth business that equity should. With the bays in their own company, your money builds Golfzon and the team instead of buying hardware, Get Lucky carries no bay debt, and the bays are funded by investors who want an asset-backed investment that pays out. Get Lucky still earns {st['feePct']}% of everything the bays take, and half their profit once the bay investors have their capital and {st['prefPct']}% a year back."),
        ("Why is Virgin Active in the plan if it is not signed?",
         f"Because it is the same deal as Planet Fitness, which is signed, at chain scale, and Virgin Active added two simulator bays at a London club in September. We show it as in talks and model it from mid-2027 rather than from the start. Without it, Get Lucky's 2029 revenue is {rm(sens['noVirginActive']['revenue'])} and the round marks at {x(sens['noVirginActive']['roundMultiple'])}."),
        ("Can I invest in the bay company too?",
         f"Yes, separately. The bay investors put up {rm(inv['calledZAR'])} between 2027 and 2029 and take their capital and a {st['prefPct']}% a year preferred return first; after that the profit splits {st['getLuckySplitPct']}/{100 - st['getLuckySplitPct']} with Get Lucky. On the plan they have it all back by {inv['capitalBackBy']}. Those terms are our proposal, final once the bay investors agree them. Ask us for the bay company's pack."),
        ("What does Ernie get?",
         f"Equity and a share of profit as Founding Ambassador. No fee, no capital, no guarantees and no liability, and his counsel signs off any use of his name. His equity is already in the {r0(rd['preMoneyZAR'])} pre-money; the terms, including how it is treated when we issue shares, are available under NDA."),
        ("What if someone wins R1m, or $100,000?",
         "The insurer pays, and it is the best marketing day of the year. Every prize is fully underwritten, with 24% of every entry ceded as premium on the same swing that creates the risk."),
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
      <span class="kicker" style="color:var(--green)">The first tee is waiting</span>
      <h2 class="display-lg" id="cta-h">Some rounds you watch. This one you own.</h2>
      <p><strong>The note closes in {esc(nt['closes'])}.</strong> Book a call and we will walk you through the model, the Golfzon demo and the Planet Fitness roll-out.</p>
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
    <p>This page is an invitation to discuss a private investment and is not an offer to the public in terms of the Companies Act, 2008. Every forward-looking figure, including forecasts, valuations and the marks shown for an investment, is illustrative, based on stated assumptions and partner proposals, and is not a guarantee of return. Investment in an early-stage business carries risk, including the loss of capital. Golfzon, Planet Fitness, Virgin Active, Santam, Indwe and RMB are the marks of their owners. Independent advice is recommended.</p>
    <p>Sources: Golfzon, "Get Lucky with GOLFZON" partnership proposal, {esc(gz['proposalDate'])} · National Golf Foundation, The Golf Simulator Opportunity, 2025 · Moneyweb, 16 July 2026 (Brait FY26). Forecast as at {esc(m['asOf'])}.</p>
  </div>
</footer>
<div class="dealbar" aria-label="The raise"><span><strong>{rm(nt['amountZAR'])} note now</strong> · {rm(rd['amountZAR'])} in Q1</span><a class="btn btn-lime" href="#deal">The terms</a></div>"""


def page():
    desc = (f"Get Lucky Golf sells one insured swing at a hole-in-one. The app is live; in 2027 it goes onto Golfzon's "
            f"{n(gz['locations'])} locations and into gym bays in Planet Fitness (signed) and Virgin Active (in talks), with "
            f"Ernie Els as Founding Ambassador. A {rm(nt['amountZAR'])} convertible note now, {rm(rd['amountZAR'])} in {rd['timing']}.")
    body = "".join([nav(), hero(), '<main id="main">', raiseband(), moves(), app_section(), golfzon_section(), gyms_section(),
                    ernie_section(), numbers_section(), risk_section(), deal_section(), team_section(), faq_section(),
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
<meta property="og:title" content="Get Lucky Golf — Golf's biggest shot, on the world's largest simulator network">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:image" content="assets/img/golfzon-demo.webp">
<link rel="icon" type="image/png" href="assets/logos/app-icon-192.png">
<link rel="apple-touch-icon" href="assets/logos/app-icon-192.png">
<link rel="preload" href="assets/fonts/PosterGothicRoundATF-Heavy.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="assets/img/ernie-ace.webp" as="image">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
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
