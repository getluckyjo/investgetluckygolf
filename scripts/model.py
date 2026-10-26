#!/usr/bin/env python3
"""Build the 2027 plan and write it into data/model.json.

Get Lucky sells one insured swing at a hole-in-one. From 2027 it runs as two
companies, and this script builds both from their own drivers:

  GET LUCKY - the company the note and the round buy into. Asset-light:
    1. The Golfzon network - the challenge on the world's largest simulator
       network (15,029 locations, 100m+ rounds a year), revenue shared
       46 / 30 / 24 with Golfzon and the venue, and the insurer.
    2. On course - the app on South Africa's Top 100 courses and the golf days.
    3. Sponsorship.
    4. A management fee on every rand the gym bays take: Get Lucky designs,
       books, runs and markets the bays for the bay company.
  THE BAY COMPANY - owns the Golfzon bays in Planet Fitness (signed, first
    installs Q1 2027) and Virgin Active (in talks, modelled from mid-2027).
    RMB lends 90% of every bay; bay investors put up the other 10%. They take
    their money back plus a preferred return first; the profit after that is
    split with Get Lucky, which puts in no capital.

Every driver lives in a case (PLAN, TARGETS) and run(case) builds both
companies from it, so the plan, the founder's targets and every sensitivity
go through the same code. Annual, 2027-2032, ZAR ex VAT at the investor FX.

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
NOTE_ZAR = 1_000_000          # convertible note, closes November 2026
NOTE_DISCOUNT = 0.20          # converts at a 20% discount to the round price...
NOTE_CAP_PRE_ZAR = 36_000_000 # ...or at a R36m pre-money cap, whichever is better for the note
ROUND_ZAR = 10_000_000        # Q1 2027: the plan needs about R4m; the rest carries any one risk
ROUND_PRE_ZAR = 56_000_000    # the founder's price: R56m pre, R66m post, about 15% for R10m
OPENING_CASH_2027 = 500_000   # cash on 1 Jan 2027, after the note funds November and December

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
# 3. SPONSORSHIP - Indwe and Santam, R3m confirmed for 2027, held flat
# ============================================================================
SPONSORSHIP = {y: 3_000_000 for y in YEARS}

# ============================================================================
# GET LUCKY - brand, tax, the ambassador
# ============================================================================
BRAND_PCT = 0.08              # of product revenue (Golfzon, on course, sponsorship), on top of the fixed launch
TAX = 0.27
AMBASSADOR_PROFIT_SHARE = 0.05  # the founding ambassador, of Get Lucky's net profit
# Quarterly cash test: share of each year's revenue earned in each quarter.
# 2027 and 2028 back-load as Golfzon and the bays ramp; later years run evenly.
# Costs run evenly from day one.
CASH_WEIGHTS = {2027: [0.10, 0.20, 0.30, 0.40], 2028: [0.19, 0.23, 0.27, 0.31]}

# ============================================================================
# 4. THE BAY COMPANY - Golfzon TwoVision NX, chain pricing quoted October 2026
# ============================================================================
BAY_TYPES = {  # USD hardware: tier 2 = bays 1-40, tier 1 = bay 41 on. Confidential to Golfzon.
    "Signature": dict(t2=43_000, t1=40_000, yld=520, model="TwoVision NX, motion plate"),
    "Play":      dict(t2=35_000, t1=32_000, yld=360, model="TwoVision NX, dual plate"),
    "Practice":  dict(t2=30_000, t1=25_000, yld=240, model="TwoVision NX"),
}
TIER2_BAYS = 40
LANDED = 1.30                 # freight, duty, booth, screen, install on top of hardware
HOURS_OPEN = 15               # bookable hours a day
HOURS_PER_BAY = HOURS_OPEN * 360
SOFTWARE_USD_PM = 99          # Golfzon commercial licence, per bay
MAINTENANCE = 0.03            # of hardware a year: spares and service after the 1-year warranty
CARD = 0.025
BAY_MARKETING = 0.05
ASSET_INS = 0.01              # of capex
CONSUMABLES = 24_000          # per bay a year
LEAGUES_PER_BAY = 40_000      # leagues, events, corporate, at maturity
SPONSOR_PER_BAY = 25_000      # naming partner per bay a year
CHALLENGE_PER_HOUR = 50 * 0.625 * (1 - PREMIUM)   # the insured shot inside the bay, net of premium
ADDON_ZAR_PM = 299            # golf add-on on the member's bill
ADDON_ADOPTION = 0.015        # of members at clubs with bays, at maturity
GYM_SHARE = 0.20              # the gym's concession share
RAMP = {0: 0.55, 1: 0.80}     # of mature use, by bay age in years
DEBT_PCT = 0.90               # RMB asset finance
RATE = 0.105 + 0.015          # prime + 1.5%
IO_M, TERM_M = 12, 60
DEPR_YEARS = 7
# The bay company's terms - proposals, to be agreed with the bay investors:
BAY_FEE = 0.06                # Get Lucky's management fee, of bay company revenue
BAY_PREF = 0.15               # investors' preferred return a year, compounding, on capital not yet returned
BAY_SPLIT_GL = 0.50           # Get Lucky's share of what is distributed after capital and the preferred return
BAY_RESERVE = 3_000_000       # cash the bay company always holds; funded by the investors at the start
BAY_DIST_DSCR = 1.25          # RMB's lock-up: no distribution in a year bay EBITDA covers debt service less than this

CHAINS = {
    "planetFitness": dict(
        name="Planet Fitness", status="Signed", members_per_club=3_500,
        people={2027: 2.0e6, 2028: 3.2e6, 2029: 4.4e6}, people_after=4.8e6,
        central={2027: 1.2e6, 2028: 1.6e6}, central_after=2.0e6,
        phases=[
            dict(name="Phase 1", year=2027, live=0.75, units={"Signature": 20}, clubs=10,
                 note="Q1 2027: two Signature bays in ten Signature and Megaclubs, Sandton first"),
            dict(name="Phase 2", year=2028, live=0.50, units={"Play": 40}, clubs=20,
                 note="Two Play bays in twenty clubs"),
            dict(name="Phase 3", year=2029, live=0.60, units={"Play": 6, "Practice": 6}, clubs=12,
                 note="One bay in twelve smaller clubs"),
        ]),
    "virginActive": dict(
        name="Virgin Active", status="In talks", members_per_club=623_000 / 136,
        people={2027: 4.0e6, 2028: 8.0e6, 2029: 11.0e6}, people_after=12.0e6,
        central={2027: 2.0e6, 2028: 3.0e6}, central_after=4.0e6,
        phases=[
            dict(name="Phase 1", year=2027, live=0.50, units={"Signature": 40}, clubs=20,
                 note="Mid-2027: two Signature bays in twenty flagship clubs"),
            dict(name="Phase 2", year=2028, live=0.25, units={"Play": 100}, clubs=50,
                 note="Two Play bays in fifty metro clubs, ordered a quarter after Planet Fitness's phase two"),
            dict(name="Phase 3", year=2029, live=0.60, units={"Play": 20, "Practice": 40}, clubs=60,
                 note="One bay in sixty smaller clubs"),
        ]),
}

# ============================================================================
# VALUATION
# ============================================================================
PLATFORM_MULTIPLE = 3.0      # x Get Lucky's revenue, flat - the multiple the plan has always used
BAYS_EBITDA_MULTIPLE = 5.0   # x bay company EBITDA, less its net debt

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
    # Share of the bookable 15 hours a day a mature bay is booked
    util={"Signature": 0.30, "Play": 0.25, "Practice": 0.22},
    # Get Lucky's team, technology and launch
    central={2027: 9_000_000, 2028: 14_000_000, 2029: 22_000_000,
             2030: 30_000_000, 2031: 38_000_000, 2032: 45_000_000},
    brand_fixed={2027: 3_000_000, 2028: 2_000_000},   # the global launch with Ernie, then the base
    chains=("planetFitness", "virginActive"),
    bay_use=1.0,            # x planned bay use (the quiet case is 0.7)
    split=BAY_SPLIT_GL,     # Get Lucky's share of the bay company after the hurdle
    sim_premium=SIM_SPLIT["insurer"],   # premium on a simulator swing; above 24% comes out of our 46%
)
TARGETS = dict(  # the founder's targets: the upside, shown beside the plan, never in place of it
    PLAN, key="targets", label="Our targets",
    gz_attach={2027: 0.001, 2028: 0.004, 2029: 0.009, 2030: 0.018, 2031: 0.028, 2032: 0.040},
    gz_ticket={2027: 5.0, 2028: 7.5, 2029: 9.0, 2030: 10.0, 2031: 10.0, 2032: 10.0},
    util={"Signature": 0.40, "Play": 0.33, "Practice": 0.30},
    central={2027: 10_000_000, 2028: 18_000_000, 2029: 30_000_000,
             2030: 45_000_000, 2031: 60_000_000, 2032: 75_000_000},
    brand_fixed={2027: 4_000_000, 2028: 3_000_000},
)


def scaled(case, key, label, attach=1.0, ticket=1.0, rounds=GZ_ROUNDS, chains=None, **over):
    return dict(case, key=key, label=label, gz_rounds=rounds,
                gz_attach={y: v * attach for y, v in case["gz_attach"].items()},
                gz_ticket={y: v * ticket for y, v in case["gz_ticket"].items()},
                chains=chains or case["chains"], **over)


PF_ONLY = ("planetFitness",)
CASES = [
    PLAN,
    scaled(PLAN, "halfAttach", "Golfzon at half the attach", attach=0.5),
    scaled(PLAN, "halfAttachHalfTicket", "Golfzon at half the attach and half the ticket", attach=0.5, ticket=0.5),
    scaled(PLAN, "noVirginActive", "No Virgin Active", chains=PF_ONLY),
    scaled(PLAN, "hard", "Half attach, half ticket, no Virgin Active", attach=0.5, ticket=0.5, chains=PF_ONLY),
    scaled(PLAN, "outsideKorea", "Golfzon outside Korea only", rounds=GZ_ROUNDS - GZ_KOREA_ROUNDS),
    scaled(PLAN, "koreaOutNoVirginActive", "Outside Korea only, and no Virgin Active",
           rounds=GZ_ROUNDS - GZ_KOREA_ROUNDS, chains=PF_ONLY),
    scaled(PLAN, "bayUse70", "Every bay at 70% of planned use", bay_use=0.7),
    TARGETS,
]
# Not in the sensitivity table: the terms still to be agreed, stressed one at a time.
TERM_CASES = [
    scaled(PLAN, "split20", "Get Lucky takes 20% of the bay company after the hurdle, not 50%", split=0.20),
    scaled(PLAN, "simPremium30", "The insurer prices simulator swings at 30%, not 24%", sim_premium=0.30),
]


# ----------------------------------------------------------------------------
def annuity(p, r_m, n):
    return p * r_m / (1 - (1 + r_m) ** -n)


def debt_schedule(principal, start_year):
    r = RATE / 12
    pmt = annuity(principal, r, TERM_M)
    bal, month = principal, 0
    out = {y: dict(interest=0.0, principal=0.0, closing=0.0) for y in YEARS}
    for y in YEARS:
        for _ in range(12):
            if y < start_year or bal <= 1e-6:
                continue
            month += 1
            i = bal * r
            pr = 0.0 if month <= IO_M else min(pmt - i, bal)
            bal -= pr
            out[y]["interest"] += i
            out[y]["principal"] += pr
        out[y]["closing"] = bal if y >= start_year else 0.0
    return out


def price_bays():
    """Hardware per bay by phase, in order placed: the first 40 bays at tier 2."""
    orders = []
    for key, c in CHAINS.items():
        for ph in c["phases"]:
            orders.append((ph["year"], 0 if key == "planetFitness" else 1, key, ph))
    orders.sort(key=lambda o: (o[0], o[1]))
    placed = 0
    for _, _, key, ph in orders:
        hw = 0.0
        for t, n in ph["units"].items():
            for _ in range(n):
                tier = "t2" if placed < TIER2_BAYS else "t1"
                hw += BAY_TYPES[t][tier] * FX
                placed += 1
        ph["hardware"] = hw
        ph["capex"] = hw * LANDED
        ph["bays"] = sum(ph["units"].values())


def run_chain(c, util, util_mult=1.0):
    """One chain's bays inside the bay company, before Get Lucky's fee."""
    rows = {y: dict(bays=0, clubs=0, hours=0.0, hire=0.0, addon=0.0, leagues=0.0, challenge=0.0,
                    sponsorship=0.0, software=0.0, maintenance=0.0, consumables=0.0, asset_ins=0.0,
                    capex=0.0, depreciation=0.0) for y in YEARS}
    debts = [debt_schedule(ph["capex"] * DEBT_PCT, ph["year"]) for ph in c["phases"]]
    for ph in c["phases"]:
        per_bay_hw = ph["hardware"] / ph["bays"]
        for y in YEARS:
            age = y - ph["year"]
            if age < 0:
                continue
            r = rows[y]
            live = ph["live"] if age == 0 else 1.0
            f = live * RAMP.get(age, 1.0)
            if age == 0:
                r["capex"] += ph["capex"]
            if age < DEPR_YEARS:
                r["depreciation"] += ph["capex"] / DEPR_YEARS * live
            r["bays"] += ph["bays"]
            r["clubs"] += ph["clubs"]
            for t, n in ph["units"].items():
                b = BAY_TYPES[t]
                hrs = n * HOURS_PER_BAY * util[t] * util_mult * f
                r["hours"] += hrs
                r["hire"] += hrs * b["yld"]
                r["challenge"] += hrs * CHALLENGE_PER_HOUR
                r["leagues"] += n * LEAGUES_PER_BAY * f
                r["sponsorship"] += n * SPONSOR_PER_BAY * live
                r["software"] += n * SOFTWARE_USD_PM * 12 * FX * live
                r["maintenance"] += n * per_bay_hw * MAINTENANCE * live
                r["consumables"] += n * CONSUMABLES * live
            r["asset_ins"] += ph["capex"] * ASSET_INS * live
            adoption = ADDON_ADOPTION * util_mult * {0: 0.4, 1: 0.75}.get(age, 1.0)
            r["addon"] += ph["clubs"] * c["members_per_club"] * adoption * ADDON_ZAR_PM * 12 * live
    for y in YEARS:
        r = rows[y]
        shared = r["hire"] + r["addon"] + r["leagues"] + r["challenge"]
        r["revenue"] = shared + r["sponsorship"]
        r["fee"] = r["revenue"] * BAY_FEE
        r["gym_share"] = shared * GYM_SHARE
        r["card"] = shared * CARD
        r["marketing"] = r["revenue"] * BAY_MARKETING
        r["people"] = c["people"].get(y, c["people_after"])
        r["central"] = c["central"].get(y, c["central_after"])
        r["opex"] = sum(r[k] for k in ("fee", "gym_share", "card", "marketing", "software", "maintenance",
                                         "consumables", "asset_ins", "people", "central"))
        r["ebitda"] = r["revenue"] - r["opex"]
        r["interest"] = sum(d[y]["interest"] for d in debts)
        r["principal"] = sum(d[y]["principal"] for d in debts)
        r["debt_closing"] = sum(d[y]["closing"] for d in debts)
        r["debt_drawn"] = r["capex"] * DEBT_PCT
    return rows


def unit_economics(t, util):
    """A mature bay of each type, at tier 1 hardware, after Get Lucky's fee."""
    b = BAY_TYPES[t]
    hw = b["t1"] * FX
    capex = hw * LANDED
    hrs = HOURS_PER_BAY * util[t]
    hire = hrs * b["yld"]
    challenge = hrs * CHALLENGE_PER_HOUR
    shared = hire + challenge + LEAGUES_PER_BAY
    revenue = shared + SPONSOR_PER_BAY
    direct = (shared * (GYM_SHARE + CARD) + revenue * (BAY_MARKETING + BAY_FEE) + SOFTWARE_USD_PM * 12 * FX
              + hw * MAINTENANCE + CONSUMABLES + capex * ASSET_INS)
    contribution = revenue - direct
    debt_service = annuity(capex * DEBT_PCT, RATE / 12, TERM_M) * 12
    return dict(type=t, model=b["model"], capexZAR=round(capex), utilisationPct=round(util[t] * 100),
                hoursPerDay=round(hrs / 360, 2), yieldZAR=b["yld"], revenueZAR=round(revenue),
                gymShareZAR=round(shared * GYM_SHARE), feeZAR=round(revenue * BAY_FEE),
                contributionZAR=round(contribution), contributionMarginPct=round(contribution / revenue * 100),
                debtServiceZAR=round(debt_service), paybackYears=round(capex / contribution, 1))


def irr(flows):
    """flows: [(years from 1 Jan 2027, amount)]. Bisection; None if no sign change."""
    npv = lambda r: sum(a / (1 + r) ** t for t, a in flows)
    lo, hi = -0.95, 5.0
    if npv(lo) * npv(hi) > 0:
        return None
    for _ in range(200):
        mid = (lo + hi) / 2
        if npv(lo) * npv(mid) <= 0:
            hi = mid
        else:
            lo = mid
    return (lo + hi) / 2


# ----------------------------------------------------------------------------
def run(case):
    """Both companies, 2027-2032, from one case's drivers."""
    chains = {k: run_chain(CHAINS[k], case["util"], case["bay_use"]) for k in case["chains"]}

    # ===================== the bay company ===================================
    bay = {}
    loss_cf, cash, hurdle = 0.0, 0.0, 0.0
    for n, y in enumerate(YEARS):
        b = {k: sum(cr[y][k] for cr in chains.values())
             for k in ("revenue", "fee", "opex", "ebitda", "depreciation", "interest", "principal",
                       "debt_closing", "debt_drawn", "capex", "bays", "clubs", "hours", "challenge", "gym_share")}
        pbt = b["ebitda"] - b["depreciation"] - b["interest"]
        taxable = pbt - loss_cf
        b["tax"] = max(taxable, 0) * TAX
        loss_cf = max(-taxable, 0)
        b["pbt"], b["netProfit"] = pbt, pbt - b["tax"]
        service = b["interest"] + b["principal"]
        b["dscr"] = b["ebitda"] / service if service else None
        b["opening"] = cash
        # investors put up the 10% on every bay ordered (and the reserve at the start)
        calls = b["capex"] * (1 - DEBT_PCT) + (BAY_RESERVE if n == 0 else 0.0)
        cash += (b["ebitda"] - b["tax"] - service - b["capex"] + b["debt_drawn"]) + calls
        topup = max(BAY_RESERVE - cash, 0.0)       # ...and anything the bays need to hold the reserve
        cash += topup
        calls += topup
        dist = 0.0
        if cash > BAY_RESERVE and (b["dscr"] is None or b["dscr"] >= BAY_DIST_DSCR):
            dist = cash - BAY_RESERVE
            cash = BAY_RESERVE
        # the waterfall: capital and the preferred return first, then the split
        hurdle = hurdle * (1 + BAY_PREF) + calls * (1 + BAY_PREF) ** 0.5
        first = min(dist, hurdle)
        hurdle -= first
        b["calls"], b["topup"], b["distributed"] = calls, topup, dist
        b["toInvestors"] = first + (dist - first) * (1 - case["split"])
        b["toGetLucky"] = (dist - first) * case["split"]
        b["hurdle"], b["cash"] = hurdle, cash
        # what the bay company is worth today, and who gets it through the same waterfall
        value = max(b["ebitda"] * BAYS_EBITDA_MULTIPLE - b["debt_closing"] + cash, 0.0)
        above = max(value - hurdle, 0.0)
        b["value"] = value
        b["valueGetLucky"] = above * case["split"]
        b["valueInvestors"] = value - b["valueGetLucky"]
        bay[y] = b

    called = sum(bay[y]["calls"] for y in YEARS)
    received = sum(bay[y]["toInvestors"] for y in YEARS)
    flows = ([(y - 2027 + 0.5, -bay[y]["calls"]) for y in YEARS]
             + [(y - 2027 + 1.0, bay[y]["toInvestors"]) for y in YEARS]
             + [(6.0, bay[2032]["valueInvestors"])])
    cum, back = 0.0, None
    for y in YEARS:
        cum += bay[y]["toInvestors"]
        if back is None and called and cum >= sum(bay[x]["calls"] for x in YEARS if x <= y):
            back = y
    investors = dict(calledZAR=called, distributedZAR=received, value2032ZAR=bay[2032]["valueInvestors"],
                     multiple2032=(received + bay[2032]["valueInvestors"]) / called if called else None,
                     irr=irr(flows), capitalBackBy=back)

    # ===================== Get Lucky =========================================
    rows = {}
    for y in YEARS:
        r = {}
        swings = case["gz_rounds"] * case["gz_attach"][y]
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
        r["sponsorship"] = SPONSORSHIP[y]
        r["bayFee"] = bay[y]["fee"]
        r["productRevenue"] = r["gzRevenue"] + r["ocRevenue"] + r["sponsorship"]
        r["revenue"] = r["productRevenue"] + r["bayFee"]
        r["central"] = case["central"][y]
        r["brandFixed"] = case["brand_fixed"].get(y, 0)
        r["brand"] = r["brandFixed"] + r["productRevenue"] * BRAND_PCT
        r["ebitda"] = r["revenue"] - r["gzDirect"] - r["ocDirect"] - r["central"] - r["brand"]
        r["bayDistributions"] = bay[y]["toGetLucky"]
        r["premiumWritten"] = (r["gzPremium"] + r["ocGross"] * PREMIUM
                               + bay[y]["challenge"] / (1 - PREMIUM) * PREMIUM)
        rows[y] = r

    loss_cf, cash = 0.0, OPENING_CASH_2027
    for y in YEARS:
        r = rows[y]
        taxable = r["ebitda"] - loss_cf            # bay company dividends are exempt income
        r["tax"] = max(taxable, 0) * TAX
        loss_cf = max(-taxable, 0)
        r["netProfit"] = r["ebitda"] - r["tax"] + r["bayDistributions"]
        r["ambassadorShare"] = max(r["netProfit"], 0) * AMBASSADOR_PROFIT_SHARE
        r["raise"] = ROUND_ZAR if y == 2027 else 0.0
        r["opening"] = cash
        r["operatingCash"] = r["ebitda"] - r["tax"] - r["ambassadorShare"]
        cash += r["operatingCash"] + r["bayDistributions"] + r["raise"]
        r["closing"] = cash

    # Quarterly cash: costs run evenly; revenue, and the costs that move with it,
    # land by CASH_WEIGHTS; the round lands in Q1 2027; tax, the ambassador's
    # share and the bay company's distribution land in Q4.
    q_cash, q = [], OPENING_CASH_2027
    for y in YEARS:
        r, w = rows[y], CASH_WEIGHTS.get(y, [0.25] * 4)
        fixed = r["central"] + r["brandFixed"]
        variable = r["ebitda"] + fixed
        for i in range(4):
            q += variable * w[i] - fixed / 4 + (ROUND_ZAR if (y, i) == (2027, 0) else 0.0)
            if i == 3:
                q += r["bayDistributions"] - r["tax"] - r["ambassadorShare"]
            q_cash.append((f"Q{i + 1} {y}", q))
    low_label, low = min(q_cash, key=lambda t: t[1])
    short = next((n for n, (_, v) in enumerate(q_cash) if v < 0), None)
    lasts_to = None if short is None else q_cash[short - 1][0]   # last quarter that ends in credit
    r27, w27 = rows[2027], CASH_WEIGHTS[2027]
    fixed27 = r27["central"] + r27["brandFixed"]
    q1_no_round = OPENING_CASH_2027 + (r27["ebitda"] + fixed27) * w27[0] - fixed27 / 4

    # ===================== value =============================================
    vals = {}
    for y in YEARS:
        platform = rows[y]["revenue"] * PLATFORM_MULTIPLE
        vals[y] = dict(platform=platform, bayShare=bay[y]["valueGetLucky"], total=platform + bay[y]["valueGetLucky"])

    return dict(case=case, chains=chains, bay=bay, rows=rows, investors=investors, vals=vals,
                q_cash=q_cash, low=(low_label, low), lasts_to=lasts_to, q1_no_round=q1_no_round)


def use_of_funds(p):
    """What the round pays for: Get Lucky's 2027 budget, split by what it builds.
    Revenue pays for most of it and the round for the rest; what the plan never
    touches is the cushion. The round goes into Get Lucky only: the bays are
    funded in the bay company."""
    r = p["rows"][2027]
    golfzon = r["gzDirect"] + 0.35 * r["central"]          # the integration team: 35% of 2027 central
    team = 0.65 * r["central"] + r["ocDirect"]
    brand = r["brand"]
    items = [
        {"key": "team", "label": "Team and operations", "ZAR": round(team, -4),
         "note": "Bay operations for the bay company, claims, finance, the on-course and golf-day desk"},
        {"key": "brand", "label": "Brand and launch with Ernie", "ZAR": round(brand, -4),
         "note": "Launch content with Ernie, leagues and partner activations"},
        {"key": "golfzon", "label": "Golfzon integration and global launch", "ZAR": round(golfzon, -4),
         "note": "Engineering, the signed shot record, the ace data the insurer prices on, market launches"},
    ]
    budget = sum(i["ZAR"] for i in items)
    for i in items:
        i["pct"] = round(i["ZAR"] / budget * 100)
    items[-1]["pct"] = 100 - sum(i["pct"] for i in items[:-1])
    return {"_note": ("Get Lucky's 2027 budget by what it builds (the Golfzon integration team is 35% of 2027 "
                      "central cost). Revenue pays for most of it; the round covers the rest and the cushion."),
            "budget2027ZAR": budget, "revenue2027ZAR": round(r["revenue"], -4), "items": items}


def main():
    price_bays()
    runs = {c["key"]: run(c) for c in CASES + TERM_CASES}
    p, t = runs["plan"], runs["targets"]
    rows, bay, vals = p["rows"], p["bay"], p["vals"]

    # the quiet case: every bay at 70% of planned use, costs unchanged
    quiet = {k: run_chain(CHAINS[k], PLAN["util"], 0.7) for k in PLAN["chains"]}

    def dscr(rs, y):
        e = sum(r[y]["ebitda"] for r in rs.values())
        d = sum(r[y]["interest"] + r[y]["principal"] for r in rs.values())
        return e / d if d else None

    # --- the round and the note ------------------------------------------------
    post = ROUND_PRE_ZAR + ROUND_ZAR
    round_pct = ROUND_ZAR / post
    # The note converts at the lower of the cap and the discounted round price, so a
    # rand of note buys what pre / conversion-valuation rand buys in the round.
    note_conv_pre = min(NOTE_CAP_PRE_ZAR, ROUND_PRE_ZAR * (1 - NOTE_DISCOUNT))
    note_equiv = NOTE_ZAR * ROUND_PRE_ZAR / note_conv_pre
    note_pct = note_equiv / post
    rm = lambda run_, y: run_["vals"][y]["total"] * round_pct / ROUND_ZAR
    nm = lambda run_, y: run_["vals"][y]["total"] * note_pct / NOTE_ZAR
    hard = runs["hard"]

    sens = []
    for c in CASES:
        r_ = runs[c["key"]]
        y29 = r_["rows"][2029]
        sens.append(dict(key=c["key"], case=c["label"], revenue=round(y29["revenue"]), ebitda=round(y29["ebitda"]),
                         value=round(r_["vals"][2029]["total"]), roundMultiple=round(rm(r_, 2029), 2),
                         value2032=round(r_["vals"][2032]["total"]), roundMultiple2032=round(rm(r_, 2032), 2),
                         lowestCashZAR=round(r_["low"][1]), lowestQuarter=r_["low"][0],
                         cashLastsTo=r_["lasts_to"],
                         bayInvestorsCalledZAR=round(r_["investors"]["calledZAR"]),
                         bayPayoutsToUsZAR=round(sum(r_["bay"][y]["toGetLucky"] for y in YEARS))))

    def case_summary(r_):
        c = r_["case"]
        return {"key": c["key"], "label": c["label"],
                "golfzonAttachPct": [round(c["gz_attach"][y] * 100, 2) for y in YEARS],
                "golfzonTicketUSD": [c["gz_ticket"][y] for y in YEARS],
                "bayHoursPerDay": {k: round(v * HOURS_OPEN, 2) for k, v in c["util"].items()},
                "bayUtilisationPct": {k: round(v * 100) for k, v in c["util"].items()},
                "centralZAR": [c["central"][y] for y in YEARS],
                "revenueZAR": [round(r_["rows"][y]["revenue"]) for y in YEARS],
                "golfzonRevenueZAR": [round(r_["rows"][y]["gzRevenue"]) for y in YEARS],
                "ebitdaZAR": [round(r_["rows"][y]["ebitda"]) for y in YEARS],
                "bayRevenueZAR": [round(r_["bay"][y]["revenue"]) for y in YEARS],
                "valueZAR": [round(r_["vals"][y]["total"]) for y in YEARS],
                "roundMultiple2029": round(rm(r_, 2029), 2), "roundMultiple2032": round(rm(r_, 2032), 2),
                "noteMultiple2029": round(nm(r_, 2029), 2), "noteMultiple2032": round(nm(r_, 2032), 2),
                "lowestCashZAR": round(r_["low"][1]), "lowestQuarter": r_["low"][0],
                "bayInvestorMultiple2032": round(r_["investors"]["multiple2032"], 2),
                "bayInvestorIrrPct": round(r_["investors"]["irr"] * 100, 1)}

    # The insurer's break-even on a simulator swing, on the same basis as the
    # Santam submission's on-course figure: premium after the broker's commission.
    sim_net_premium = SIM_SPLIT["insurer"] * (1 - BROKER_COMMISSION)
    sim_breakeven = SIM_PAYOUT / sim_net_premium          # one ace in this many swings

    # ========================================================================
    # write model.json
    # ========================================================================
    old = json.loads(MODEL.read_text()) if MODEL.exists() else {}
    R = lambda k: [round(rows[y][k]) for y in YEARS]
    B = lambda k: [round(bay[y][k]) for y in YEARS]
    C = lambda key, k: [round(p["chains"][key][y][k]) for y in YEARS]
    inv = p["investors"]
    all_phases = [ph for c in CHAINS.values() for ph in c["phases"]]

    m = {
        "_note": ("Canonical numbers for the site, built by scripts/model.py - do not hand-edit the forecast. "
                  "Re-run the script, then scripts/tie-out.py."),
        "fx": FX,
        "asOf": "26 October 2026",
        "company": old.get("company", {}),
        "structure": {
            "_note": ("Two companies. The note and the round buy into Get Lucky, which is asset-light. The bays "
                      "sit in the bay company, funded 90% by RMB and 10% by bay investors. The bay company's "
                      "terms (fee, preferred return, split) are proposals, to be agreed with the bay investors."),
            "getLucky": "The challenge on Golfzon's network, on course and at golf days; sponsorship; and a fee "
                        "for running the bays. No bay debt, no bay capex.",
            "bayCompany": "Owns the Golfzon bays in Planet Fitness and Virgin Active. RMB lends 90% of every bay; "
                          "bay investors put up the other 10%.",
            "feePct": round(BAY_FEE * 100), "prefPct": round(BAY_PREF * 100),
            "getLuckySplitPct": round(BAY_SPLIT_GL * 100), "debtPct": round(DEBT_PCT * 100),
            "investorEquityPct": round((1 - DEBT_PCT) * 100), "reserveZAR": BAY_RESERVE,
            "distributionLockDscr": BAY_DIST_DSCR,
        },
        "deal": {
            "_note": ("Two steps, both into Get Lucky. A R1.0m convertible note in November 2026, converting at a "
                      "R36m cap or a 20% discount to the round, whichever is better for the note; then R10.0m for "
                      "about 15% at R56m pre in Q1 2027 to roll out the plan. Both prices are the founder's (26 Oct 2026)."),
            "note": {"amountZAR": NOTE_ZAR, "discountPct": round(NOTE_DISCOUNT * 100), "closes": "November 2026",
                     "capPreMoneyZAR": NOTE_CAP_PRE_ZAR, "conversionPreMoneyZAR": round(note_conv_pre),
                     "capApplies": NOTE_CAP_PRE_ZAR < ROUND_PRE_ZAR * (1 - NOTE_DISCOUNT),
                     "convertsInto": "The Q1 2027 round", "equivalentAtRoundZAR": round(note_equiv),
                     "_conversion": ("The round's pre-money includes the shares the note converts into, so the "
                                     "round buys exactly its stated equity and the note's dilution falls on the "
                                     "existing holders."),
                     "stakePct": round(note_pct * 100, 2),
                     "multiple2029": round(nm(p, 2029), 2), "multiple2032": round(nm(p, 2032), 2),
                     "hardCaseMultiple2029": round(nm(hard, 2029), 2),
                     "targetsMultiple2029": round(nm(t, 2029), 2),
                     "useOfFunds": ["The December sit-down with Golfzon and Ernie Els at Fancourt",
                                    "The first build of the Golfzon integration on a real bay",
                                    "Setting up the bay company for the first Planet Fitness bays",
                                    "Working capital into the round"]},
            "round": {"amountZAR": ROUND_ZAR, "preMoneyZAR": ROUND_PRE_ZAR, "postMoneyZAR": post,
                      "equityPct": round(round_pct * 100, 2), "timing": "Q1 2027", "minimumTicketZAR": 1_000_000,
                      "givenAwayPct": round((round_pct + note_pct) * 100, 1),
                      "value2029ZAR": round(vals[2029]["total"]), "value2032ZAR": round(vals[2032]["total"]),
                      "multiple2029": round(rm(p, 2029), 2), "multiple2032": round(rm(p, 2032), 2),
                      "hardCaseValue2029ZAR": round(hard["vals"][2029]["total"]),
                      "hardCaseMultiple2029": round(rm(hard, 2029), 2),
                      "hardCaseMultiple2032": round(rm(hard, 2032), 2),
                      "targetsValue2029ZAR": round(t["vals"][2029]["total"]),
                      "targetsMultiple2029": round(rm(t, 2029), 2), "targetsMultiple2032": round(rm(t, 2032), 2),
                      "multipleBasis": ("Your stake at the round's post-money, marked at the plan's value on "
                                        "31 December. An unrealised mark on a private holding, not a cash return.")},
            "useOfFunds": use_of_funds(p),
            "allocation": {"show": False, "committedZAR": None, "closeDate": None},
            "ambassador": ("Ernie Els is Founding Ambassador: equity and a share of profit, no capital, no "
                           "guarantees, no liability. Terms in the dataroom only - never on the public page."),
        },
        "partners": {
            "golfzon": {"status": "In", "locations": GZ_LOCATIONS, "korea": GZ_KOREA,
                        "northAmerica": GZ_NORTH_AMERICA, "koreaSharePct": 74, "roundsPerYear": GZ_ROUNDS,
                        "tourVenues": 130, "tourCountries": 15, "tourPurseUSD": 300_000,
                        "proposalDate": "1 October 2026",
                        "phases": [
                            {"phase": "Phase 1", "when": "2027", "what": "The Hole-in-One Challenge on Golfzon bays, run on the competition features TwoVision NX already has"},
                            {"phase": "Phase 2", "when": "2028", "what": "Featured partner: in the Golfzon app and in-game, broadcast to its global audience"},
                            {"phase": "Phase 3", "when": "2029 on", "what": "Full integration: the challenge built into Golfzon's game settings"},
                        ],
                        "_pricing": ("Golfzon's chain quote is confidential to Golfzon: it lives in scripts/model.py and "
                                     "the NDA workbook only, never on the page or in this file.")},
            "ernie": {"status": "Onboard", "role": "Founding Ambassador"},
            "planetFitness": {"status": "Signed", "firstInstalls": "Q1 2027",
                              "bays": sum(ph["bays"] for ph in CHAINS["planetFitness"]["phases"]),
                              "clubs": sum(ph["clubs"] for ph in CHAINS["planetFitness"]["phases"])},
            "virginActive": {"status": "In talks", "modelledFrom": "Mid-2027",
                             "bays": sum(ph["bays"] for ph in CHAINS["virginActive"]["phases"]),
                             "clubs": sum(ph["clubs"] for ph in CHAINS["virginActive"]["phases"]),
                             "members": 623_000, "saClubs": 136},
            "santam": {"status": "Underwriter", "fsp": "3416"},
            "indwe": {"status": "Sponsor and broker", "fsp": "3425", "sponsorship2027ZAR": 3_000_000},
            "rmb": {"status": "Asset finance to the bay company, modelled", "debtPct": round(DEBT_PCT * 100),
                    "ratePct": round(RATE * 100, 1)},
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
                "sponsorship": R("sponsorship"),
                "bayFee": R("bayFee"),
                "total": R("revenue"),
            },
            "_revenueBasis": ("Get Lucky's own revenue. Golfzon and on course are Get Lucky's share only: 46% of a "
                              "simulator swing after Golfzon and the venue (30%) and the insurer (24%); 66% of a "
                              "course swing after the club (10%) and the insurer (24%). The bay fee is 6% of the bay "
                              "company's revenue. The bay company's own revenue is not Get Lucky's."),
            "ebitdaZAR": R("ebitda"),
            "ebitdaMarginPct": [round(rows[y]["ebitda"] / rows[y]["revenue"] * 100, 1) for y in YEARS],
            "costZAR": {"golfzonDirect": R("gzDirect"), "onCourseDirect": R("ocDirect"),
                        "central": R("central"), "brand": R("brand")},
            "taxZAR": R("tax"), "bayDistributionsZAR": R("bayDistributions"),
            "netProfitZAR": R("netProfit"), "ambassadorShareZAR": R("ambassadorShare"),
            "kpis": {
                "golfzonAttachPct": [round(PLAN["gz_attach"][y] * 100, 2) for y in YEARS],
                "golfzonTicketUSD": [PLAN["gz_ticket"][y] for y in YEARS],
                "golfzonSwings": R("gzSwings"),
                "baysLive": B("bays"), "baysClubs": B("clubs"),
                "onCourseSwings": R("ocSwings"), "onCourseAvgZAR": [OC_AVG_ZAR[y] for y in YEARS],
                "premiumWrittenZAR": R("premiumWritten"),
            },
            "_premiumNote": ("Premium written is a volume metric, not revenue: the premium the platform "
                             "originates and cedes to the insurer. Get Lucky earns none of it."),
        },
        "bayCompany": {
            "_source": ("The simulatorstrategy bay engine, re-priced at Golfzon's October 2026 chain quote, run as "
                        "its own company. EBITDA is after Get Lucky's fee."),
            "assumptions": {"hoursOpenPerDay": HOURS_OPEN, "hoursPerBayPerYear": HOURS_PER_BAY,
                            "utilisationPct": {k: round(v * 100) for k, v in PLAN["util"].items()},
                            "hoursBookedPerDay": {k: round(v * HOURS_OPEN, 2) for k, v in PLAN["util"].items()},
                            "gymSharePct": round(GYM_SHARE * 100), "feePct": round(BAY_FEE * 100),
                            "debtPct": round(DEBT_PCT * 100), "ratePct": round(RATE * 100, 1),
                            "interestOnlyMonths": IO_M, "termMonths": TERM_M,
                            "addOnZARpm": ADDON_ZAR_PM, "challengeEntryZAR": 50, "challengesPerBookedHour": 0.625},
            "chains": {k: {"name": c["name"], "status": c["status"],
                           "bays": sum(ph["bays"] for ph in c["phases"]),
                           "clubs": sum(ph["clubs"] for ph in c["phases"]),
                           "capexZAR": round(sum(ph["capex"] for ph in c["phases"])),
                           "phases": [{"name": ph["name"], "year": ph["year"], "bays": ph["bays"],
                                       "clubs": ph["clubs"], "units": ph["units"], "capexZAR": round(ph["capex"]),
                                       "note": ph["note"]} for ph in c["phases"]],
                           "revenueZAR": C(k, "revenue"), "ebitdaZAR": C(k, "ebitda"),
                           "gymShareZAR": C(k, "gym_share"), "debtClosingZAR": C(k, "debt_closing")}
                       for k, c in CHAINS.items()},
            "totalBays": sum(ph["bays"] for ph in all_phases),
            "totalClubs": sum(ph["clubs"] for ph in all_phases),
            "totalCapexZAR": round(sum(ph["capex"] for ph in all_phases)),
            "revenueZAR": B("revenue"), "feeZAR": B("fee"), "ebitdaZAR": B("ebitda"),
            "ebitdaMarginPct": [round(bay[y]["ebitda"] / bay[y]["revenue"] * 100, 1) for y in YEARS],
            "depreciationZAR": B("depreciation"), "interestZAR": B("interest"), "principalZAR": B("principal"),
            "taxZAR": B("tax"), "netProfitZAR": B("netProfit"),
            "capexZAR": B("capex"), "debtDrawnZAR": B("debt_drawn"), "debtClosingZAR": B("debt_closing"),
            "investorCallsZAR": B("calls"), "topUpZAR": B("topup"),
            "distributedZAR": B("distributed"), "toInvestorsZAR": B("toInvestors"), "toGetLuckyZAR": B("toGetLucky"),
            "cashClosingZAR": B("cash"), "hurdleClosingZAR": B("hurdle"),
            "dscr": [round(bay[y]["dscr"], 2) if bay[y]["dscr"] else None for y in YEARS],
            "valueZAR": {"total": B("value"), "investors": B("valueInvestors"), "getLucky": B("valueGetLucky")},
            "investors": {"calledZAR": round(inv["calledZAR"]), "distributedZAR": round(inv["distributedZAR"]),
                          "value2032ZAR": round(inv["value2032ZAR"]), "multiple2032": round(inv["multiple2032"], 2),
                          "irrPct": round(inv["irr"] * 100, 1), "capitalBackBy": inv["capitalBackBy"],
                          "_basis": ("Calls mid-year, distributions at year end, and the investors' share of the bay "
                                     "company's value at 31 December 2032 through the same waterfall.")},
            "unit": {t_: unit_economics(t_, PLAN["util"]) for t_ in BAY_TYPES},
            "debtCover": {"_note": "Bay company EBITDA (after Get Lucky's fee) over debt service, both chains.",
                          "plan": {str(y): round(dscr(p["chains"], y), 2) for y in (2029, 2030, 2031)},
                          "quiet70": {str(y): round(dscr(quiet, y), 2) for y in (2029, 2030, 2031)},
                          "quiet70RevenueZAR2031": round(sum(r[2031]["revenue"] for r in quiet.values())),
                          "quiet70EbitdaZAR2031": round(sum(r[2031]["ebitda"] for r in quiet.values()))},
        },
        "cash": {
            "_note": ("Get Lucky's cash. No bay capex and no bay debt: those sit in the bay company. The R10.0m "
                      "round carries the team, the Golfzon build and the launch until the engines pay for "
                      "themselves. No further equity round is assumed."),
            "openingZAR": OPENING_CASH_2027,
            "raiseZAR": R("raise"), "operatingCashZAR": R("operatingCash"),
            "bayDistributionsZAR": R("bayDistributions"), "closingZAR": R("closing"),
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
            "method": ("Get Lucky at a flat 3.0x its revenue (Golfzon, on course, sponsorship and the bay fee), the "
                       "multiple this plan has always used, plus Get Lucky's share of the bay company: the bays at "
                       "5.0x EBITDA less net debt, after the bay investors' capital and preferred return."),
            "platformMultiple": PLATFORM_MULTIPLE, "baysEbitdaMultiple": BAYS_EBITDA_MULTIPLE,
            "milestonesZAR": {str(y): {"platform": round(vals[y]["platform"]), "bayShare": round(vals[y]["bayShare"]),
                                       "total": round(vals[y]["total"])} for y in YEARS},
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
    for label, k in (("Golfzon (GL share)", "gzRevenue"), ("On course", "ocRevenue"), ("Sponsorship", "sponsorship"),
                     ("Bay fee", "bayFee"), ("REVENUE", "revenue"), ("central", "central"), ("brand", "brand"),
                     ("EBITDA", "ebitda"), ("tax", "tax"), ("bay distributions", "bayDistributions"),
                     ("net profit", "netProfit"), ("cash closing", "closing")):
        line(label, [mm(rows[y][k]) for y in YEARS])
    line("margin %", [f"{rows[y]['ebitda'] / rows[y]['revenue'] * 100:.1f}" for y in YEARS])
    print(f"\n{'BAY COMPANY':32}")
    for label, k in (("revenue", "revenue"), ("fee to GL", "fee"), ("EBITDA", "ebitda"), ("interest", "interest"),
                     ("principal", "principal"), ("tax", "tax"), ("capex", "capex"), ("debt closing", "debt_closing"),
                     ("investor calls", "calls"), ("distributed", "distributed"), ("  to investors", "toInvestors"),
                     ("  to Get Lucky", "toGetLucky"), ("hurdle", "hurdle"), ("value", "value"),
                     ("  GL share", "valueGetLucky")):
        line(label, [mm(bay[y][k]) for y in YEARS])
    line("bays live", [bay[y]["bays"] for y in YEARS])
    line("DSCR", [f"{bay[y]['dscr']:.2f}" if bay[y]["dscr"] else "-" for y in YEARS])
    print(f"  investors: called R{inv['calledZAR'] / 1e6:.1f}m, distributed R{inv['distributedZAR'] / 1e6:.1f}m, "
          f"2032 share R{inv['value2032ZAR'] / 1e6:.1f}m, {inv['multiple2032']:.2f}x, IRR {inv['irr'] * 100:.1f}%, "
          f"capital back {inv['capitalBackBy']}")
    print("\n  quarters: " + ", ".join(f"{k} R{v / 1e6:.1f}m" for k, v in p["q_cash"][:12]))
    print(f"  lowest {p['low'][0]} R{p['low'][1] / 1e6:.1f}m   Q1 2027 without the round R{p['q1_no_round'] / 1e6:.1f}m")
    for y in (2027, 2028, 2029, 2032):
        v = vals[y]
        print(f"  value {y}: platform R{v['platform'] / 1e6:.0f}m + bay share R{v['bayShare'] / 1e6:.0f}m = R{v['total'] / 1e6:.0f}m")
    print(f"  round {round_pct * 100:.1f}% at R{post / 1e6:.0f}m post: 2029 {rm(p, 2029):.2f}x  2032 {rm(p, 2032):.2f}x")
    print(f"  note {note_pct * 100:.2f}% (converts at R{note_conv_pre / 1e6:.0f}m pre): 2029 {nm(p, 2029):.2f}x  2032 {nm(p, 2032):.2f}x")
    print(f"  entry multiple on 2027 revenue {post / rows[2027]['revenue']:.2f}x")
    print(f"  simulator break-even 1 in {sim_breakeven:,.0f} vs measured 1 in {SIM_ACE_MEASURED:,} ({SIM_ACE_MEASURED / sim_breakeven:.2f}x)")
    for c in m["valuation"]["termCases"]:
        print(f"  term case: {c['case']}: value R{c['value2029'] / 1e6:.0f}m, round {c['roundMultiple']}x / {c['roundMultiple2032']}x")
    for s in sens:
        print(f"  {s['case']:46} rev R{s['revenue'] / 1e6:6.1f}m EBITDA R{s['ebitda'] / 1e6:6.1f}m value R{s['value'] / 1e6:5.0f}m "
              f"{s['roundMultiple']:5.2f}x  2032 {s['roundMultiple2032']:5.2f}x  low R{s['lowestCashZAR'] / 1e6:5.1f}m {s['lowestQuarter']}  lasts to {s['cashLastsTo']}")
    for t_ in BAY_TYPES:
        u = m["bayCompany"]["unit"][t_]
        print(f"  unit {t_:10} {u['hoursPerDay']}h/day capex R{u['capexZAR'] / 1e6:.2f}m rev R{u['revenueZAR'] / 1e6:.2f}m "
              f"contrib {u['contributionMarginPct']}% payback {u['paybackYears']}y")
    for u in m["deal"]["useOfFunds"]["items"]:
        print(f"  use {u['key']:8} R{u['ZAR'] / 1e6:5.2f}m {u['pct']}%")
    print(f"  debt cover plan {m['bayCompany']['debtCover']['plan']}  quiet70 {m['bayCompany']['debtCover']['quiet70']}")

    if "--dry" not in sys.argv:
        MODEL.write_text(json.dumps(m, indent=2, ensure_ascii=False) + "\n")
        print(f"\nwrote {MODEL.relative_to(ROOT)}")


main()
