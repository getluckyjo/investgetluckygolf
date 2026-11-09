#!/usr/bin/env python3
"""Build the 2027 plan and write it into data/model.json.

Get Lucky sells one insured swing at a hole-in-one: the hole-in-one app, on
course, on simulators and next on the driving range. The round buys into an
asset-light company - no hardware, no debt:
    1. The Golfzon network - the challenge on the world's largest simulator
       network (15,029 locations, 100m+ rounds a year), revenue shared
       46 / 30 / 24 with Golfzon and the venue, and the insurer.
    2. On course - the app on South Africa's Top 100 courses and the golf days.
    3. On course, worldwide - the same app on every par 3 in the world, launched with Ernie.
    4. Sponsorship.
The app is the one interface: it takes every entry, on course, on simulators and on ranges.
The round funds two opportunities: the app worldwide, and simulator integration (Golfzon first).

Every driver lives in a case (PLAN, TARGETS) and run(case) builds the company
from it, so the plan, the founder's targets and every sensitivity go through
the same code. Annual, 2027-2032, ZAR ex VAT at the investor FX.

    python3 scripts/model.py          # rebuild data/model.json
    python3 scripts/model.py --dry    # print the build, write nothing
"""
import json, pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
MODEL = ROOT / "data/model.json"

FX = 18.5
YEARS = list(range(2027, 2033))

# ============================================================================
# THE RAISE - into Get Lucky
# ============================================================================
# One round, no interim raise: the R1m convertible note is withdrawn (4 Nov 2026). Cash
# carries the business to year end; the Fancourt sit-down is costed on its own (about R100k).
# The round is 10% for R6.2m in all (the founder, 5 Nov 2026): R3.4m in cash for 5.5%, and R2.8m of
# development work for 4.5% from a development partner at the same price (option A, 5 Nov 2026).
# The partner is unnamed until the deal is agreed. Its work is the 2027 developers' cost
# (APP_TEAM_SHARE + SIM_TEAM_SHARE of central): still a cost in the P&L, paid in shares, not cash.
ROUND_TOTAL_ZAR = 6_200_000   # cash and development together: exactly 10%
DEV_EQUITY_ZAR = 2_800_000    # development work paid in shares
ROUND_ZAR = ROUND_TOTAL_ZAR - DEV_EQUITY_ZAR   # the cash round: R3.4m for 5.5%
ROUND_PRE_ZAR = 55_800_000    # the founder's price: R55.8m pre, R62m post
OPENING_CASH_2027 = 0         # cash on 1 Jan 2027: conservative, with no note to carry it
# Golfzon: the deck can show the post-signing version, but it goes live "in talks" until the
# agreement is signed (the founder, 5 Nov 2026). Turn this on the day it is signed and rebuild;
# every status line follows. Never publish with it on before the signature.
GOLFZON_SIGNED = False

# ============================================================================
# THE INSURED SWING (the Santam submission, unchanged)
# ============================================================================
PREMIUM = 0.24                # ceded to the insurer on every paid swing
BROKER_COMMISSION = 0.20      # Indwe's commission, of premium (the Santam submission)
SIM_PAYOUT = 1_000            # every simulator tier pays 1,000x the swing
SIM_ACE_MEASURED = 6_992      # Golfzon: about one ace in 6,992 par-3 tee shots, every setting
COURSE_SHARE = 0.10           # on course: the club's share
SIM_SPLIT = {"getLucky": 0.46, "golfzonAndVenue": 0.30, "insurer": 0.24}

# ============================================================================
# 1. THE GOLFZON NETWORK (attach and ticket are case drivers, below)
# ============================================================================
GZ_LOCATIONS = 15_029         # Golfzon, Get Lucky with GOLFZON, Oct 2026
GZ_KOREA = 10_802
GZ_NORTH_AMERICA = 331
GZ_KOREA_ROUNDS = 94_000_000  # research.json korea-sim-rounds: most of the network's rounds are Korean
GZ_ROUNDS = 100_000_000       # "more than 100 million rounds a year", held flat
# Trackman: 50,000+ simulator bays (research.json trackman-bays), and 70,000+ bays on ranges and in
# simulators tracking 150 shots a second (trackman-shots), about 4.7bn shots a year. Not a partner
# yet, so only in a stress case. Its bays are mostly practice (ranges, coaching, fitting, home sims),
# not Korea's evenings of full rounds: take the simulators' share of the shots, half of those hit in
# rounds, at 80 shots a round. About 21 million rounds a year, on the same attach, ticket and split
# as Golfzon, from 2028.
TRACKMAN_BAYS = 50_000
TRACKMAN_SHOTS = 150 * 60 * 60 * 24 * 365
TRACKMAN_ROUNDS = TRACKMAN_SHOTS * (TRACKMAN_BAYS / 70_000) * 0.5 / 80
GZ_PROCESSING = 0.03          # of gross
GZ_OPS_USD = 0.05             # risk, claims and support per swing (the bay verifies the ace)
GZ_MARKETING = 0.12           # of Get Lucky's share: launches, in-game media, the Tour

# ============================================================================
# 2. ON COURSE - the app on South Africa's Top 100 courses, and the golf days
# ============================================================================
OC_SWINGS = {2027: 36_000, 2028: 60_000, 2029: 85_000, 2030: 110_000, 2031: 135_000, 2032: 160_000}
OC_AVG_ZAR = {2027: 150, 2028: 175, 2029: 200, 2030: 200, 2031: 200, 2032: 200}
OC_PROCESSING = 0.03
OC_VERIFY_ZAR = 8             # video review and claims handling per swing

# ============================================================================
# 2b. ON COURSE, WORLDWIDE - the same app on every par 3 in the world, launched with Ernie in
# his markets from 2028 (2027 builds the course data, payments and cover). Conservative: by
# 2032 about twice South Africa's paid swings, from a golfer base hundreds of times larger.
# The founder's proposal to plan on, 5 Nov 2026.
# ============================================================================
GL_SWINGS = {2027: 0, 2028: 25_000, 2029: 75_000, 2030: 150_000, 2031: 250_000, 2032: 350_000}
GL_TICKET_USD = 10.0          # average swing outside South Africa
GL_MARKETING = 0.12           # of our share: market launches with Ernie
GL_MARKET_COST = 1_000_000    # a year from the first market: legal clearance and insurer onboarding

# ============================================================================
# 3. SPONSORSHIP - grows with reach. Indwe has approved R3m for 2027, first payment on 1 January
# (the founder, 5 Nov 2026), and it is assumed
# to renew; on top, sponsors pay for the reach we add: about R5 (~$0.27) for every paid
# swing beyond 2027's, on course and on Golfzon - a seventh of what Indwe's R3m pays a
# swing in 2027.
# ============================================================================
SPONSOR_BASE_ZAR = 3_000_000
SPONSOR_PER_SWING_ZAR = 5

# ============================================================================
# GET LUCKY - brand, tax, the ambassador
# ============================================================================
BRAND_PCT = 0.08              # of product revenue (Golfzon, on course, sponsorship), on top of the fixed launch
TAX = 0.27
# Ernie Els, Founding Ambassador: 5% non-diluting equity, topped up inside the pre-money so the
# round still buys its full stake. No profit share, no fee (the founder, 27 Oct 2026).
AMBASSADOR_EQUITY_PCT = 5
# Quarterly cash test: share of each year's revenue earned in each quarter.
# 2027 and 2028 back-load as Golfzon ramps; later years run evenly.
# Costs run evenly from day one.
CASH_WEIGHTS = {2027: [0.10, 0.20, 0.30, 0.40], 2028: [0.19, 0.23, 0.27, 0.31]}

# ============================================================================
# VALUATION
# ============================================================================
PLATFORM_MULTIPLE = 3.0      # x Get Lucky's revenue, flat - the multiple the plan has always used

# ============================================================================
# THE CASES - every driver that differs between the plan and the targets
# ============================================================================
PLAN = dict(
    key="plan", label="The plan",
    # Share of all network rounds that carry a paid swing. Phase 1 (2027) runs on
    # Golfzon's existing competition features; phase 2 (2028) puts it in the
    # Golfzon app and in-game; phase 3 (2029 on) builds it into the game settings.
    gz_attach={2027: 0.0005, 2028: 0.002, 2029: 0.005, 2030: 0.010, 2031: 0.015, 2032: 0.020},
    # Average swing: $1-$100 tiers, each paying 1,000x. The higher tiers open
    # market by market, so the average starts low.
    gz_ticket={2027: 4.0, 2028: 5.0, 2029: 6.0, 2030: 7.0, 2031: 8.0, 2032: 8.0},
    gz_rounds=GZ_ROUNDS,
    # Get Lucky's team, technology and launch (the founder, 4 Nov 2026). 2027 is trimmed for the smaller
    # round (5 Nov 2026): hires into the central team land a little later, R8m not R9m.
    central={2027: 8_000_000, 2028: 13_000_000, 2029: 16_000_000,
             2030: 20_000_000, 2031: 26_000_000, 2032: 31_000_000},
    brand_fixed={2027: 2_000_000, 2028: 2_000_000},   # the global launch with Ernie (trimmed from R3m), then the base
    sim_premium=SIM_SPLIT["insurer"],   # premium on a simulator swing; above 24% comes out of our 46%
)
TARGETS = dict(  # the founder's targets: the upside, shown beside the plan, never in place of it
    PLAN, key="targets", label="Our targets",
    gz_attach={2027: 0.001, 2028: 0.004, 2029: 0.009, 2030: 0.018, 2031: 0.028, 2032: 0.040},
    gz_ticket={2027: 5.0, 2028: 7.5, 2029: 9.0, 2030: 10.0, 2031: 10.0, 2032: 10.0},
    central={2027: 10_000_000, 2028: 17_500_000, 2029: 27_000_000,
             2030: 40_000_000, 2031: 54_000_000, 2032: 68_000_000},
    brand_fixed={2027: 4_000_000, 2028: 3_000_000},
)


def scaled(case, key, label, attach=1.0, ticket=1.0, rounds=GZ_ROUNDS, **over):
    return dict(case, key=key, label=label, gz_rounds=rounds,
                gz_attach={y: v * attach for y, v in case["gz_attach"].items()},
                gz_ticket={y: v * ticket for y, v in case["gz_ticket"].items()}, **over)


CASES = [
    PLAN,
    scaled(PLAN, "halfAttach", "Golfzon at half the attach", attach=0.5),
    scaled(PLAN, "hard", "Golfzon at half the attach and half the ticket", attach=0.5, ticket=0.5),
    # Golfzon's roll-out a year behind plan: no swings in 2027, each later year at the year before's attach
    dict(PLAN, key="golfzonLate", label="Golfzon a year late",
         gz_attach={y: PLAN["gz_attach"].get(y - 1, 0.0) for y in YEARS}),
    dict(PLAN, key="noGolfzon", label="No Golfzon at all", gz_attach={y: 0.0 for y in YEARS}),
    dict(PLAN, key="globalHalf", label="The app worldwide at half the swings", gl_mult=0.5),
    scaled(PLAN, "outsideKorea", "Golfzon outside Korea only", rounds=GZ_ROUNDS - GZ_KOREA_ROUNDS),
    scaled(PLAN, "outsideKoreaTrackman", "Golfzon outside Korea, plus Trackman from 2028",
           rounds={y: GZ_ROUNDS - GZ_KOREA_ROUNDS + (TRACKMAN_ROUNDS if y >= 2028 else 0) for y in YEARS}),
    TARGETS,
]
# Not in the sensitivity table: a term still to be agreed, stressed on its own.
TERM_CASES = [
    scaled(PLAN, "simPremium30", "The insurer prices simulator swings at 30%, not 24%", sim_premium=0.30),
]

# ----------------------------------------------------------------------------
def run(case):
    """Get Lucky, 2027-2032, from one case's drivers."""
    # ===================== Get Lucky =========================================
    rows = {}
    gz_rounds = lambda y: case["gz_rounds"][y] if isinstance(case["gz_rounds"], dict) else case["gz_rounds"]
    gl = lambda y: GL_SWINGS[y] * case.get("gl_mult", 1.0)                       # paid swings outside South Africa
    swings_2027 = gz_rounds(2027) * case["gz_attach"][2027] + OC_SWINGS[2027] + gl(2027)   # the reach Indwe's R3m buys
    for y in YEARS:
        r = {}
        swings = gz_rounds(y) * case["gz_attach"][y]
        r["gzSwings"] = swings
        r["gzGross"] = swings * case["gz_ticket"][y] * FX
        r["gzRevenue"] = r["gzGross"] * (1 - SIM_SPLIT["golfzonAndVenue"] - case["sim_premium"])
        r["gzPremium"] = r["gzGross"] * case["sim_premium"]
        r["gzDirect"] = (r["gzGross"] * GZ_PROCESSING + swings * GZ_OPS_USD * FX
                         + r["gzRevenue"] * GZ_MARKETING)
        r["ocSwings"] = OC_SWINGS[y]
        r["ocGross"] = OC_SWINGS[y] * OC_AVG_ZAR[y]
        r["ocRevenue"] = r["ocGross"] * (1 - PREMIUM - COURSE_SHARE)
        r["ocDirect"] = r["ocGross"] * OC_PROCESSING + OC_SWINGS[y] * OC_VERIFY_ZAR
        r["glSwings"] = gl(y)
        r["glGross"] = gl(y) * GL_TICKET_USD * FX
        r["glRevenue"] = r["glGross"] * (1 - PREMIUM - COURSE_SHARE)
        r["glDirect"] = (r["glGross"] * OC_PROCESSING + gl(y) * OC_VERIFY_ZAR + r["glRevenue"] * GL_MARKETING
                         + (GL_MARKET_COST if gl(y) else 0.0))
        r["sponsorship"] = SPONSOR_BASE_ZAR + SPONSOR_PER_SWING_ZAR * max(swings + OC_SWINGS[y] + gl(y) - swings_2027, 0)
        r["productRevenue"] = r["gzRevenue"] + r["ocRevenue"] + r["glRevenue"] + r["sponsorship"]
        r["revenue"] = r["productRevenue"]
        r["central"] = case["central"][y]
        r["brandFixed"] = case["brand_fixed"].get(y, 0)
        r["brand"] = r["brandFixed"] + r["productRevenue"] * BRAND_PCT
        r["ebitda"] = r["revenue"] - r["gzDirect"] - r["ocDirect"] - r["glDirect"] - r["central"] - r["brand"]
        r["premiumWritten"] = r["gzPremium"] + (r["ocGross"] + r["glGross"]) * PREMIUM
        rows[y] = r

    loss_cf, cash = 0.0, OPENING_CASH_2027
    for y in YEARS:
        r = rows[y]
        taxable = r["ebitda"] - loss_cf
        r["tax"] = max(taxable, 0) * TAX
        loss_cf = max(-taxable, 0)
        r["netProfit"] = r["ebitda"] - r["tax"]
        r["raise"] = ROUND_ZAR if y == 2027 else 0.0
        r["devInShares"] = DEV_EQUITY_ZAR if y == 2027 else 0.0   # a P&L cost that never leaves as cash
        r["opening"] = cash
        r["operatingCash"] = r["ebitda"] - r["tax"]
        cash += r["operatingCash"] + r["raise"] + r["devInShares"]
        r["closing"] = cash

    # Quarterly cash: costs run evenly; revenue, and the costs that move with it,
    # land by CASH_WEIGHTS; the round lands in Q1 2027; tax lands in Q4.
    q_cash, q = [], OPENING_CASH_2027
    for y in YEARS:
        r, w = rows[y], CASH_WEIGHTS.get(y, [0.25] * 4)
        fixed = r["central"] + r["brandFixed"]
        variable = r["ebitda"] + fixed
        for i in range(4):
            q += variable * w[i] - fixed / 4 + r["devInShares"] / 4 + (ROUND_ZAR if (y, i) == (2027, 0) else 0.0)
            if i == 3:
                q -= r["tax"]
            q_cash.append((f"Q{i + 1} {y}", q))
    low_label, low = min(q_cash, key=lambda t: t[1])
    short = next((n for n, (_, v) in enumerate(q_cash) if v < 0), None)
    lasts_to = None if short is None else q_cash[short - 1][0]   # last quarter that ends in credit
    r27, w27 = rows[2027], CASH_WEIGHTS[2027]
    fixed27 = r27["central"] + r27["brandFixed"]
    q1_no_round = OPENING_CASH_2027 + (r27["ebitda"] + fixed27) * w27[0] - fixed27 / 4 + r27["devInShares"] / 4

    # ===================== value =============================================
    vals = {y: dict(total=rows[y]["revenue"] * PLATFORM_MULTIPLE) for y in YEARS}

    return dict(case=case, rows=rows, vals=vals,
                q_cash=q_cash, low=(low_label, low), lasts_to=lasts_to, q1_no_round=q1_no_round)


APP_TEAM_SHARE = 0.20   # of 2027 central: the developers taking the app to every par 3 in the world
SIM_TEAM_SHARE = 0.15   # of 2027 central: the simulator integration team, Golfzon first


def use_of_funds(p):
    """What the round's cash pays for: two opportunities, through one app. In 2027 revenue already
    pays for the rest of the team and the day-to-day, and the development partner builds the app
    worldwide and simulator integration for its shares, so the cash goes into what is new: the
    launch with Ernie, Golfzon's running costs, and the reserve. The partner's work is shown as its
    stake, never as a rand amount (Willie, 9 Nov 2026: an ongoing partner, not a once-off fee)."""
    r = p["rows"][2027]
    app_dev, sim_dev = APP_TEAM_SHARE * r["central"], SIM_TEAM_SHARE * r["central"]
    assert abs(app_dev + sim_dev - DEV_EQUITY_ZAR) < 1, "the development partner's work is the 2027 developers' cost"
    running = (1 - APP_TEAM_SHARE - SIM_TEAM_SHARE) * r["central"] + r["ocDirect"] + (r["brand"] - r["brandFixed"])
    items = [
        {"key": "app", "label": "The app, worldwide", "short": "The app", "ZAR": round(r["brandFixed"], -4),
         "note": "The launch with Ernie: the public launch and the marketing behind it"},
        {"key": "sims", "label": "Simulator integration", "short": "Simulators", "ZAR": round(r["gzDirect"], -4),
         "note": "Golfzon first: the launch on its bays, payments, and risk and support for every swing"},
    ]
    items.append({"key": "reserve", "label": "Working capital and reserve", "short": "Reserve",
                  "ZAR": ROUND_ZAR - sum(i["ZAR"] for i in items),
                  "note": "What carries any one risk without cutting a cost"})
    for i in items:
        i["pct"] = round(i["ZAR"] / ROUND_ZAR * 100)
    items[-1]["pct"] = 100 - sum(i["pct"] for i in items[:-1])
    post = ROUND_PRE_ZAR + ROUND_TOTAL_ZAR
    return {"_note": ("The round's cash: the launch budget, Golfzon's running costs and the reserve. The development "
                      "partner builds the app worldwide and simulator integration (the 2027 developers: 20% and 15% "
                      "of central cost) for its stake. Revenue pays for the rest of the team and the costs that move with it."),
            "cashZAR": ROUND_ZAR, "revenue2027ZAR": round(r["revenue"], -4), "runningCost2027ZAR": round(running, -4),
            "items": items,
            "partner": {"label": "Development partner", "pct": round(DEV_EQUITY_ZAR / post * 100, 2),
                        "note": "An ongoing partner: builds the app worldwide and simulator integration with us; paid in shares, at the same price"}}


def main():
    runs = {c["key"]: run(c) for c in CASES + TERM_CASES}
    p, t, hard = runs["plan"], runs["targets"], runs["hard"]
    rows, vals = p["rows"], p["vals"]

    # --- the round ---------------------------------------------------------------
    post = ROUND_PRE_ZAR + ROUND_TOTAL_ZAR
    round_pct = ROUND_ZAR / post                     # the cash investors' stake
    rm = lambda run_, y: run_["vals"][y]["total"] * round_pct / ROUND_ZAR

    # A sale in 2032 at the same yardstick, for the round: in at the end of Q1 2027, out on
    # 31 December 2032. The marks leave out Get Lucky's cash; a buyer pays for it (or it is
    # paid out as dividends on the way), so the cash-included figure is shown as extra.
    EXIT_YEAR, HOLD_YEARS = 2032, 5.75
    a_year = lambda mult: (mult ** (1 / HOLD_YEARS) - 1) * 100
    exit_cash = rows[EXIT_YEAR]["closing"]
    with_cash = (vals[EXIT_YEAR]["total"] + exit_cash) * round_pct / ROUND_ZAR
    exit_view = {
        "year": EXIT_YEAR, "holdYears": HOLD_YEARS, "valueZAR": round(vals[EXIT_YEAR]["total"]),
        "ebitdaMultiple": round(vals[EXIT_YEAR]["total"] / rows[EXIT_YEAR]["ebitda"], 1),
        "multiple": round(rm(p, EXIT_YEAR), 2), "aYearPct": round(a_year(rm(p, EXIT_YEAR))),
        "hardCaseValueZAR": round(hard["vals"][EXIT_YEAR]["total"]),
        "hardCaseMultiple": round(rm(hard, EXIT_YEAR), 2), "hardCaseAYearPct": round(a_year(rm(hard, EXIT_YEAR))),
        "cashZAR": round(exit_cash), "withCashMultiple": round(with_cash, 2), "withCashAYearPct": round(a_year(with_cash)),
        "_basis": ("Illustrative: the round's stake sold on 31 December 2032 at the plan's value, held from the end "
                   "of Q1 2027. withCash adds Get Lucky's closing cash, before any dividend tax."),
    }

    sens = []
    for c in CASES:
        r_ = runs[c["key"]]
        y29 = r_["rows"][2029]
        sens.append(dict(key=c["key"], case=c["label"], revenue=round(y29["revenue"]), ebitda=round(y29["ebitda"]),
                         value=round(r_["vals"][2029]["total"]), roundMultiple=round(rm(r_, 2029), 2),
                         value2032=round(r_["vals"][2032]["total"]), roundMultiple2032=round(rm(r_, 2032), 2),
                         lowestCashZAR=round(r_["low"][1]), lowestQuarter=r_["low"][0],
                         cashLastsTo=r_["lasts_to"]))

    def case_summary(r_):
        c = r_["case"]
        return {"key": c["key"], "label": c["label"],
                "golfzonAttachPct": [round(c["gz_attach"][y] * 100, 2) for y in YEARS],
                "golfzonTicketUSD": [c["gz_ticket"][y] for y in YEARS],
                "centralZAR": [c["central"][y] for y in YEARS],
                "revenueZAR": [round(r_["rows"][y]["revenue"]) for y in YEARS],
                "golfzonRevenueZAR": [round(r_["rows"][y]["gzRevenue"]) for y in YEARS],
                "ebitdaZAR": [round(r_["rows"][y]["ebitda"]) for y in YEARS],
                "valueZAR": [round(r_["vals"][y]["total"]) for y in YEARS],
                "roundMultiple2029": round(rm(r_, 2029), 2), "roundMultiple2032": round(rm(r_, 2032), 2),
                "lowestCashZAR": round(r_["low"][1]), "lowestQuarter": r_["low"][0]}

    # The insurer's break-even on a simulator swing, on the same basis as the
    # Santam submission's on-course figure: premium after the broker's commission.
    sim_net_premium = SIM_SPLIT["insurer"] * (1 - BROKER_COMMISSION)
    sim_breakeven = SIM_PAYOUT / sim_net_premium          # one ace in this many swings

    # ========================================================================
    # write model.json
    # ========================================================================
    old = json.loads(MODEL.read_text()) if MODEL.exists() else {}
    R = lambda k: [round(rows[y][k]) for y in YEARS]

    m = {
        "_note": ("Canonical numbers for the site, built by scripts/model.py - do not hand-edit the forecast. "
                  "Re-run the script, then scripts/build_site.py."),
        "fx": FX,
        "asOf": "4 November 2026",
        "company": old.get("company", {}),
        "structure": {
            "_note": ("One company, asset-light: the round buys into Get Lucky, which owns no hardware and carries "
                      "no debt."),
            "getLucky": "The hole-in-one app: on course, on Golfzon's network and at golf days; and sponsorship.",
        },
        "deal": {
            "_note": ("The round, into Get Lucky: 10% for R6.2m at R55.8m pre (R62m post) in Q1 2027: R3.4m in cash for "
                      "5.5% and R2.8m of development work for 4.5% from a development partner (being agreed). The price "
                      "is the founder's."),
            "round": {"amountZAR": ROUND_ZAR, "preMoneyZAR": ROUND_PRE_ZAR, "postMoneyZAR": post,
                      "equityPct": round(round_pct * 100, 2), "timing": "Q1 2027", "minimumTicketZAR": 1_000_000,
                      "totalZAR": ROUND_TOTAL_ZAR, "totalPct": round(ROUND_TOTAL_ZAR / post * 100, 2),
                      "devZAR": DEV_EQUITY_ZAR, "devPct": round(DEV_EQUITY_ZAR / post * 100, 2),
                      "devPartner": "A development partner (being agreed)",
                      "value2029ZAR": round(vals[2029]["total"]), "value2032ZAR": round(vals[2032]["total"]),
                      "multiple2029": round(rm(p, 2029), 2), "multiple2032": round(rm(p, 2032), 2),
                      "hardCaseValue2029ZAR": round(hard["vals"][2029]["total"]),
                      "hardCaseMultiple2029": round(rm(hard, 2029), 2),
                      "hardCaseMultiple2032": round(rm(hard, 2032), 2),
                      "targetsValue2029ZAR": round(t["vals"][2029]["total"]),
                      "targetsMultiple2029": round(rm(t, 2029), 2), "targetsMultiple2032": round(rm(t, 2032), 2),
                      "exit": exit_view,
                      "multipleBasis": ("Your stake at the round's post-money, marked at the plan's value on "
                                        "31 December. An unrealised mark on a private holding, not a cash return.")},
            "useOfFunds": use_of_funds(p),
            "allocation": {"show": False, "committedZAR": None, "closeDate": None},
            "ambassador": {"name": "Ernie Els", "role": "Founding Ambassador", "equityPct": AMBASSADOR_EQUITY_PCT,
                           "_terms": ("Non-diluting equity, topped up inside the pre-money; no profit share, no fee, "
                                      "no capital, no guarantees, no liability.")},
        },
        "partners": {
            "trackman": {"status": "Not a partner", "bays": TRACKMAN_BAYS,
                         "roundsPerYear": round(TRACKMAN_ROUNDS, -6), "fromYear": 2028},
            "golfzon": {"signed": GOLFZON_SIGNED,
                        "status": "Signed partner" if GOLFZON_SIGNED else "In talks: Golfzon's own three-phase proposal",
                        "_status": ("The deck is the post-signing version: the agreement is signed before we raise "
                                    "(the founder, 4 Nov 2026). Do not send the page before it is."),
                        "locations": GZ_LOCATIONS, "korea": GZ_KOREA,
                        "northAmerica": GZ_NORTH_AMERICA, "koreaSharePct": 74, "roundsPerYear": GZ_ROUNDS,
                        "tourVenues": 130, "tourCountries": 15, "tourPurseUSD": 300_000,
                        "proposalDate": "1 October 2026",
                        "phases": [
                            {"phase": "Phase 1", "when": "2027", "what": "The Hole-in-One Challenge on Golfzon bays, run on the competition features TwoVision NX already has"},
                            {"phase": "Phase 2", "when": "2028", "what": "Featured partner: in the Golfzon app and in-game, broadcast to its global audience"},
                            {"phase": "Phase 3", "when": "2029 on", "what": "Full integration: the challenge built into Golfzon's game settings"},
                        ],
                        "_pricing": ("Golfzon's chain quote is confidential to Golfzon: it lives in the NDA workbook only, "
                                     "never on the page or in this repo.")},
            "ernie": {"status": "Onboard", "role": "Founding Ambassador"},
            "santam": {"status": "Underwriter", "fsp": "3416"},
            "indwe": {"status": "Sponsor and broker", "fsp": "3425", "sponsorship2027ZAR": SPONSOR_BASE_ZAR,
                      "sponsorship2027Status": "Approved", "firstPayment": "1 January 2027"},
        },
        "traction": old.get("traction", {}),
        "product": {
            "saLadderZAR": [{"stake": 50, "prize": 25_000}, {"stake": 100, "prize": 60_000},
                            {"stake": 250, "prize": 200_000}, {"stake": 500, "prize": 500_000},
                            {"stake": 1_000, "prize": 1_000_000}],
            "simLadderUSD": [{"stake": s, "prize": s * 1000} for s in (1, 5, 20, 50, 100)],
            "simSplitPct": {k: round(v * 100) for k, v in SIM_SPLIT.items()},
            "courseSplitPct": {"getLucky": 66, "course": 10, "insurer": 24},
            "simInsurerBreakEvenOneIn": round(sim_breakeven),
            "simAceMeasuredOneIn": SIM_ACE_MEASURED,
            "simHeadroom": round(SIM_ACE_MEASURED / sim_breakeven, 2),
            "_simBreakEven": ("Premium after the broker's 20% commission over the 1,000x prize, the same basis as the "
                              "submission's 2.51x on course. Measured rate across every Golfzon setting."),
        },
        "insuranceModel": old.get("insuranceModel", {}),
        "forecast": {
            "_source": "scripts/model.py - Get Lucky, annual, 2027 to 2032. Every figure is FORECAST.",
            "years": YEARS,
            "revenueZAR": {
                "golfzon": R("gzRevenue"),
                "onCourse": R("ocRevenue"),
                "global": R("glRevenue"),
                "sponsorship": R("sponsorship"),
                "total": R("revenue"),
            },
            "_revenueBasis": ("Get Lucky's own revenue. Golfzon and on course are Get Lucky's share only: 46% of a "
                              "simulator swing after Golfzon and the venue (30%) and the insurer (24%); 66% of a "
                              "course swing after the club (10%) and the insurer (24%), in South Africa and worldwide."),
            "ebitdaZAR": R("ebitda"),
            "ebitdaMarginPct": [round(rows[y]["ebitda"] / rows[y]["revenue"] * 100, 1) for y in YEARS],
            "costZAR": {"golfzonDirect": R("gzDirect"), "onCourseDirect": R("ocDirect"), "globalDirect": R("glDirect"),
                        "central": R("central"), "brand": R("brand")},
            "taxZAR": R("tax"), "netProfitZAR": R("netProfit"),
            "kpis": {
                "golfzonAttachPct": [round(PLAN["gz_attach"][y] * 100, 2) for y in YEARS],
                "golfzonTicketUSD": [PLAN["gz_ticket"][y] for y in YEARS],
                "golfzonSwings": R("gzSwings"),
                "onCourseSwings": R("ocSwings"), "onCourseAvgZAR": [OC_AVG_ZAR[y] for y in YEARS],
                "globalSwings": R("glSwings"), "globalTicketUSD": GL_TICKET_USD,
                "globalMarketCostZAR": GL_MARKET_COST, "globalMarketingPct": round(GL_MARKETING * 100),
                "premiumWrittenZAR": R("premiumWritten"),
            },
            "_premiumNote": ("Premium written is a volume metric, not revenue: the premium the platform "
                             "originates and cedes to the insurer. Get Lucky earns none of it."),
        },
        "cash": {
            "_note": ("Get Lucky's cash, from R0 on 1 January 2027 (no note). No hardware and no debt. The R9.0m "
                      "round carries the team, the Golfzon build and the launch until the engines pay for "
                      "themselves. No further equity round is assumed."),
            "openingZAR": OPENING_CASH_2027,
            "raiseZAR": R("raise"), "operatingCashZAR": R("operatingCash"), "devInSharesZAR": R("devInShares"),
            "closingZAR": R("closing"),
            "quarterlyClosingZAR": {k: round(v) for k, v in p["q_cash"]},
            "lowestQuarter": p["low"][0], "lowestQuarterZAR": round(p["low"][1]),
            "q1WithoutRoundZAR": round(p["q1_no_round"]),
            "hardCaseLowestQuarter": hard["low"][0], "hardCaseLowestZAR": round(hard["low"][1]),
            "hardCaseCashLastsTo": hard["lasts_to"],
            "peakNetSpendZAR": round(OPENING_CASH_2027 + ROUND_ZAR - p["low"][1]),
            "_peakNetSpend": "How much of the opening cash and the round the plan has used at its lowest quarter-end.",
            "_hardCase": ("The hard case holds every cost at plan: no hire is delayed and nothing is cut. "
                          "cashLastsTo is the last quarter that ends in credit; None means it never runs short."),
            "ebitdaPositiveFrom": next((y for y in YEARS if rows[y]["ebitda"] > 0), None),
        },
        "valuation": {
            "method": ("Get Lucky at a flat 3.0x its revenue (Golfzon, on course and sponsorship), the multiple this "
                       "plan has always used."),
            "platformMultiple": PLATFORM_MULTIPLE,
            "milestonesZAR": {str(y): {"total": round(vals[y]["total"])} for y in YEARS},
            "entryMultipleOnRevenue2027": round(post / rows[2027]["revenue"], 2),
            "postAsShareOf2029Value": round(post / vals[2029]["total"], 2),
            "sensitivity2029": sens,
            "termCases": [{"key": c["key"], "case": c["label"],
                           "value2029": round(runs[c["key"]]["vals"][2029]["total"]),
                           "roundMultiple": round(rm(runs[c["key"]], 2029), 2),
                           "roundMultiple2032": round(rm(runs[c["key"]], 2032), 2)} for c in TERM_CASES],
            "cases": {"plan": case_summary(p), "targets": case_summary(t)},
        },
        "research": "data/research.json",
    }

    # ---- print the build --------------------------------------------------
    mm = lambda v: f"{v / 1e6:9.1f}"
    line = lambda label, vals_: print(f"  {label:30}" + "".join(f"{v:>10}" for v in vals_))
    print(f"{'GET LUCKY':32}" + "".join(f"{y:>10}" for y in YEARS))
    line("Golfzon swings (m)", [f"{rows[y]['gzSwings'] / 1e6:.2f}" for y in YEARS])
    for label, k in (("Golfzon (GL share)", "gzRevenue"), ("On course", "ocRevenue"), ("On course, worldwide", "glRevenue"),
                     ("Sponsorship", "sponsorship"),
                     ("REVENUE", "revenue"), ("central", "central"), ("brand", "brand"),
                     ("EBITDA", "ebitda"), ("tax", "tax"), ("net profit", "netProfit"), ("cash closing", "closing")):
        line(label, [mm(rows[y][k]) for y in YEARS])
    line("margin %", [f"{rows[y]['ebitda'] / rows[y]['revenue'] * 100:.1f}" for y in YEARS])
    print("\n  quarters: " + ", ".join(f"{k} R{v / 1e6:.1f}m" for k, v in p["q_cash"][:12]))
    print(f"  lowest {p['low'][0]} R{p['low'][1] / 1e6:.1f}m   Q1 2027 without the round R{p['q1_no_round'] / 1e6:.1f}m"
          f"   peak net spend R{m['cash']['peakNetSpendZAR'] / 1e6:.1f}m")
    for y in (2027, 2028, 2029, 2032):
        print(f"  value {y}: R{vals[y]['total'] / 1e6:.0f}m")
    print(f"  round {round_pct * 100:.1f}% at R{post / 1e6:.0f}m post: 2029 {rm(p, 2029):.2f}x  2032 {rm(p, 2032):.2f}x")
    print(f"  entry multiple on 2027 revenue {post / rows[2027]['revenue']:.2f}x")
    print(f"  simulator break-even 1 in {sim_breakeven:,.0f} vs measured 1 in {SIM_ACE_MEASURED:,} ({SIM_ACE_MEASURED / sim_breakeven:.2f}x)")
    for c in m["valuation"]["termCases"]:
        print(f"  term case: {c['case']}: value R{c['value2029'] / 1e6:.0f}m, round {c['roundMultiple']}x / {c['roundMultiple2032']}x")
    for s_ in sens:
        print(f"  {s_['case']:46} rev R{s_['revenue'] / 1e6:6.1f}m EBITDA R{s_['ebitda'] / 1e6:6.1f}m value R{s_['value'] / 1e6:5.0f}m "
              f"{s_['roundMultiple']:5.2f}x  2032 {s_['roundMultiple2032']:5.2f}x  low R{s_['lowestCashZAR'] / 1e6:5.1f}m {s_['lowestQuarter']}  lasts to {s_['cashLastsTo']}")
    for u in m["deal"]["useOfFunds"]["items"]:
        print(f"  use {u['key']:8} R{u['ZAR'] / 1e6:5.2f}m {u['pct']}%")
    if "--dry" not in sys.argv:
        MODEL.write_text(json.dumps(m, indent=2, ensure_ascii=False) + "\n")
        print(f"\nwrote {MODEL.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
