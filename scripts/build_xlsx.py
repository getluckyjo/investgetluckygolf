#!/usr/bin/env python3
"""Write the plan as a live-formula workbook for review: data/get-lucky-model.xlsx.

Every driver comes from scripts/model.py; every calculation in the workbook is a
formula, so a reviewer can change a blue input and watch the plan move. The
Checks sheet holds the Python model's own results for every case, so the
workbook shows whether it still ties to scripts/model.py.

    python3 scripts/model.py && python3 scripts/build_xlsx.py

Not deployed: data/ is in .vercelignore.
"""
import importlib.util, io, pathlib, shutil, subprocess, sys, tempfile

from openpyxl import Workbook, load_workbook
from openpyxl.cell.rich_text import CellRichText, TextBlock
from openpyxl.cell.text import InlineFont
from openpyxl.drawing.image import Image as XLImage
from openpyxl.drawing.spreadsheet_drawing import AnchorMarker, OneCellAnchor
from openpyxl.drawing.xdr import XDRPositiveSize2D
from openpyxl.formatting.rule import FormulaRule
from openpyxl.utils.units import pixels_to_EMU
from openpyxl.comments import Comment
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter as L
from openpyxl.workbook.defined_name import DefinedName
from openpyxl.worksheet.datavalidation import DataValidation

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "data/get-lucky-model.xlsx"
spec = importlib.util.spec_from_file_location("model", ROOT / "scripts/model.py")
M = importlib.util.module_from_spec(spec)
spec.loader.exec_module(M)          # drivers only: model.py runs its build under __main__
Y = M.YEARS
YC = [L(3 + i) for i in range(len(Y))]          # C..H, one column a year
QC = [L(3 + i) for i in range(len(Y) * 4)]      # C..Z, one column a quarter
QL = [f"Q{q + 1} {y}" for y in Y for q in range(4)]

# The cases, as levers on the plan's drivers. Each row must rebuild the case in model.py exactly
# (checked below), so the workbook and the Python model can't drift apart quietly.
SCEN = [  # name, key, attach x, ticket x, drivers, a year late, Korea in, Trackman from 2028, simulator premium
    ("The plan", "plan", 1, 1, "Plan", 0, 1, 0, M.SIM_SPLIT["insurer"]),
    ("Golfzon at half the attach", "halfAttach", 0.5, 1, "Plan", 0, 1, 0, M.SIM_SPLIT["insurer"]),
    ("The hard case: half the attach and half the ticket", "hard", 0.5, 0.5, "Plan", 0, 1, 0, M.SIM_SPLIT["insurer"]),
    ("Golfzon a year late", "golfzonLate", 1, 1, "Plan", 1, 1, 0, M.SIM_SPLIT["insurer"]),
    ("Golfzon outside Korea only", "outsideKorea", 1, 1, "Plan", 0, 0, 0, M.SIM_SPLIT["insurer"]),
    ("Golfzon outside Korea, plus Trackman from 2028", "outsideKoreaTrackman", 1, 1, "Plan", 0, 0, 1, M.SIM_SPLIT["insurer"]),
    ("Our targets", "targets", 1, 1, "Targets", 0, 1, 0, M.SIM_SPLIT["insurer"]),
    ("The insurer prices simulator swings at 30%", "simPremium30", 1, 1, "Plan", 0, 1, 0, 0.30),
]
CASE = {c["key"]: c for c in M.CASES + M.TERM_CASES}
for _, key, am, tm, drv, late, korea, tman, prem in SCEN:
    c, base = CASE[key], (M.TARGETS if drv == "Targets" else M.PLAN)
    for i, y in enumerate(Y):
        a = (base["gz_attach"].get(y - 1, 0.0) if late else base["gz_attach"][y]) * am
        rounds = M.GZ_ROUNDS - (0 if korea else M.GZ_KOREA_ROUNDS) + (M.TRACKMAN_ROUNDS if tman and y >= 2028 else 0)
        case_rounds = c["gz_rounds"][y] if isinstance(c["gz_rounds"], dict) else c["gz_rounds"]
        assert abs(c["gz_attach"][y] - a) < 1e-12 and abs(c["gz_ticket"][y] - base["gz_ticket"][y] * tm) < 1e-9, key
        assert abs(case_rounds - rounds) < 1 and c["central"] == base["central"] and c["sim_premium"] == prem, key

# ------------------------------------------------------------------ styles
ARIAL = "Arial"
# Get Lucky's palette (css/site.css): night and forest for structure, lime for what you can change,
# paper and cream for quiet fills. Text keeps the modelling convention: blue in, ink calc, green link.
NIGHT, FOREST, GREEN, GREEN_LIGHT, LIME = "0C160E", "1E3120", "345231", "4A7A3D", "D6FB4B"
CREAM, PAPER, SURFACE, INK, MUTED, GOLD = "F5EEDE", "F7F8F4", "EBEDEA", "0F1B12", "536157", "C9A94E"
LIME_TINT = "F1FAD2"
F = lambda **k: Font(name=ARIAL, size=10, **k)
INPUT, LINK, CALC = F(color="0000FF"), F(color=GREEN_LIGHT), F(color=INK)
NOTE, HELPER = F(italic=True, color=MUTED), F(color=MUTED)
BOLD, TITLE, WHITE = F(bold=True, color=INK), Font(name=ARIAL, size=15, bold=True, color=CREAM), F(bold=True, color=CREAM)
SUB = F(bold=True, color=GREEN)
HEAD = PatternFill("solid", fgColor=FOREST)
BAND = PatternFill("solid", fgColor=NIGHT)
KEY = PatternFill("solid", fgColor=LIME)
OUTFILL = PatternFill("solid", fgColor=LIME_TINT)
TOTALFILL = PatternFill("solid", fgColor=PAPER)
THIN = Border(top=Side(style="thin", color=GREEN))
RULE = Border(bottom=Side(style="thin", color=SURFACE))
UNDER = Border(bottom=Side(style="thin", color=GREEN))
RM = '"R"#,##0.0,,"m";("R"#,##0.0,,"m");"-"'
R0 = '"R"#,##0;("R"#,##0);"-"'
N0 = '#,##0;(#,##0);"-"'
PCT, PCT2 = '0.0%;(0.0%);"-"', '0.00%;(0.00%);"-"'
USD = '"$"#,##0.00;("$"#,##0.00);"-"'
MULT = '0.00"×";(0.00"×");"-"'
FLAG = '0;-0;"-"'
DIFF = '[>=0.5]"R"#,##0;[<=-0.5]("R"#,##0);"-"'

wb = Workbook()
NAMES = {}


def name(nm, ws, ref):
    NAMES[nm] = f"'{ws.title}'!{ref}" if " " in ws.title else f"{ws.title}!{ref}"
    wb.defined_names[nm] = DefinedName(nm, attr_text=NAMES[nm])


def cell(ws, ref, v, font=CALC, fmt=None, fill=None, note=None, bold=False):
    c = ws[ref]
    c.value = v
    c.font = Font(name=ARIAL, size=font.sz, bold=bold or font.b, italic=font.i, color=font.color)
    if fmt:
        c.number_format = fmt
    if fill:
        c.fill = fill
    if note:
        c.comment = Comment(note, "Get Lucky model")
    return c


def header(ws, row, text, last="H"):
    """A forest band across the table, the title in cream capitals."""
    for col in range(1, ws[f"{last}1"].column + 1):
        ws.cell(row=row, column=col).fill = HEAD
    x = cell(ws, f"A{row}", text.upper(), WHITE)
    x.alignment = Alignment(horizontal="left", vertical="center", indent=1)
    ws.row_dimensions[row].height = 20


def years(ws, row, cols=YC, labels=None):
    """Column heads for a table inside a section: green, ruled underneath."""
    for c_ in ["A", "B"] + list(cols):
        ws[f"{c_}{row}"].border = UNDER
    for c_, y in zip(cols, labels or [str(y) for y in Y]):
        x = cell(ws, f"{c_}{row}", y, SUB)
        x.alignment = Alignment(horizontal="right")


def total_row(ws, row, cols):
    for c_ in cols:
        ws[f"{c_}{row}"].border = THIN
        ws[f"{c_}{row}"].fill = TOTALFILL


# ================================================================== Read me
rd = wb.active
rd.title = "Read me"
lines = [
    ("Get Lucky Golf: the 2027 plan, for review", TITLE),
    ("As at 4 November 2026. Built by scripts/build_xlsx.py from the drivers in scripts/model.py.", CALC),
    ("", CALC),
    ("What this is", BOLD),
    ("Get Lucky's forecast, 2027-2032, ZAR ex VAT: our share of every insured swing on Golfzon's simulator network and on course,", CALC),
    ("and sponsorship. One round: R9.0m at R56m pre-money in Q1 2027. No interim raise, no hardware, no debt.", CALC),
    ("", CALC),
    ("How to use it", BOLD),
    ("1. Pick a case in Model!C2 (lime). The Model and Round sheets follow it.", CALC),
    ("2. Change any blue cell on Assumptions; every number moves with it. Black cells are formulas; green cells link to another sheet.", CALC),
    ("3. Stress cases shows every case side by side, each fully calculated in its own block below the summary.", CALC),
    ("4. Checks compares the workbook with scripts/model.py's own results. It reads TRUE until you change an input, which is expected.", CALC),
    ("", CALC),
    ("Colours", BOLD),
    ("LEGEND", CALC),
    ("", CALC),
    ("The method, in short", BOLD),
    ("Golfzon: rounds a year x share of rounds with a paid swing (attach) x average swing in USD x FX = gross; Get Lucky keeps", CALC),
    ("46% after Golfzon and the venue (30%) and the insurer (24%). On course: paid swings x average swing; we keep 66% after the", CALC),
    ("club (10%) and the insurer (24%). Sponsorship: Indwe's R3m, plus R5 for every paid swing beyond 2027's.", CALC),
    ("Costs: Golfzon payments, claims and launches; on-course payments and verification; the central team; brand at 8% plus a", CALC),
    ("launch budget. Tax at 27% after losses carried forward. Value: 3.0x each year's revenue. The round's mark = value x its stake.", CALC),
    ("Quarterly cash: revenue (and the costs that move with it) lands by the weights on Assumptions; fixed costs run evenly; the", CALC),
    ("round lands in Q1 2027; tax lands in Q4.", CALC),
    ("", CALC),
    ("Sources", BOLD),
    ("Golfzon network, rounds and phases: Golfzon's 'Get Lucky with GOLFZON' proposal, October 2026. Ace rate: Golfzon's measured", CALC),
    ("rate across every setting. Insurance terms: the Santam submission. Indwe's R3m: the 2027 sponsorship. Trackman: research.json.", CALC),
    ("The round, the central team, the launch budget and the targets: the founder (26 Oct and 4 Nov 2026). Forecast, not a promise.", CALC),
]
# The cover: a night band with the logo, a lime rule, then the notes in one clean column.
for c_, w in zip("ABC", (3, 124, 3)):
    rd.column_dimensions[c_].width = w
for c_ in "ABC":
    rd[f"{c_}1"].fill = BAND
    rd[f"{c_}2"].fill = KEY
rd.row_dimensions[1].height = 62
rd.row_dimensions[2].height = 4
x = cell(rd, "B1", "INVESTOR MODEL  ·  2027–2032  ·  CONFIDENTIAL", F(bold=True, color=LIME))
x.alignment = Alignment(horizontal="right", vertical="center")
from PIL import Image as PILImage
buf = io.BytesIO()
PILImage.open(ROOT / "assets/logos/logo-dark-bg.webp").save(buf, format="PNG")
buf.seek(0)
logo = XLImage(buf)
lh = 46
lw = round(lh * logo.width / logo.height)
logo.anchor = OneCellAnchor(_from=AnchorMarker(col=1, colOff=0, row=0, rowOff=pixels_to_EMU(8)),
                            ext=XDRPositiveSize2D(pixels_to_EMU(lw), pixels_to_EMU(lh)))
rd.add_image(logo)
IFt = lambda **k: InlineFont(rFont=ARIAL, sz=10, **k)
legend = CellRichText(
    TextBlock(IFt(color="0000FF", b=True), "Blue"), TextBlock(IFt(color=INK), " an input you can change      "),
    TextBlock(IFt(color=INK, b=True), "Black"), TextBlock(IFt(color=INK), " a formula      "),
    TextBlock(IFt(color=GREEN_LIGHT, b=True), "Green"), TextBlock(IFt(color=INK), " a link to another sheet      "),
    TextBlock(IFt(color=GREEN, b=True), "Lime fill"), TextBlock(IFt(color=INK), " a key lever      "),
    TextBlock(IFt(color=MUTED), "Grey: helper rows"))
row = 4
for t, f_ in lines:
    if f_ is TITLE:
        cell(rd, f"B{row}", t, Font(name=ARIAL, size=20, bold=True, color=FOREST))
        rd.row_dimensions[row].height = 30
    elif t == "LEGEND":
        rd[f"B{row}"].value = legend
        rd.row_dimensions[row].height = 18
    elif f_ is BOLD:
        x = cell(rd, f"B{row}", t.upper(), SUB)
        x.border = UNDER
        x.alignment = Alignment(vertical="bottom")
        rd.row_dimensions[row].height = 24
    elif not t:
        rd.row_dimensions[row].height = 8
    else:
        cell(rd, f"B{row}", t, NOTE if t.startswith("As at") else CALC)
        rd.row_dimensions[row].height = 15
    row += 1

# ================================================================== Assumptions
A = wb.create_sheet("Assumptions")
A.column_dimensions["A"].width = 52
A.column_dimensions["B"].width = 14
for c_ in "CDEFGH":
    A.column_dimensions[c_].width = 12
A.column_dimensions["I"].width = 64
cell(A, "A1", "Assumptions: blue cells are inputs", TITLE)
ROWS = {}
r = 3


def scalar(label, nm, v, fmt, note, key=False, calc=False):
    global r
    cell(A, f"A{r}", label)
    cell(A, f"B{r}", v, CALC if calc else INPUT, fmt, KEY if key else None)
    cell(A, f"I{r}", note, NOTE)
    name(nm, A, f"$B${r}")
    r += 1


def per_year(label, key, vals, fmt, note):
    global r
    cell(A, f"A{r}", label)
    for c_, v in zip(YC, vals):
        cell(A, f"{c_}{r}", v, INPUT, fmt)
    cell(A, f"I{r}", note, NOTE)
    ROWS[key] = r
    r += 1


header(A, r, "THE ROUND", "I"); r += 1
scalar("Round size, R", "Round_ZAR", M.ROUND_ZAR, R0, "The founder's raise, Q1 2027", key=True)
scalar("Pre-money, R", "Pre_ZAR", M.ROUND_PRE_ZAR, R0, "The founder's price; Ernie Els's 5% is topped up inside it", key=True)
scalar("Post-money, R", "Post_ZAR", "=Pre_ZAR+Round_ZAR", R0, "Pre-money plus the round", calc=True)
scalar("The round's stake", "Round_Stake", "=Round_ZAR/Post_ZAR", PCT2, "Round / post-money", calc=True)
scalar("Minimum ticket, R", "Min_Ticket", 1_000_000, R0, "")
scalar("Opening cash, 1 January 2027, R", "Opening_Cash", M.OPENING_CASH_2027, R0, "Conservative: no note, so nothing carried in (4 Nov 2026)", key=True)
scalar("Rand to the US dollar", "FX_ZAR", M.FX, '0.00', "The investor FX")
r += 1
header(A, r, "THE GOLFZON NETWORK", "I"); r += 1
scalar("Rounds a year, held flat", "GZ_Rounds", M.GZ_ROUNDS, N0, "Golfzon: 'more than 100 million rounds a year'")
scalar("  of which in Korea", "Korea_Rounds", M.GZ_KOREA_ROUNDS, N0, "research.json korea-sim-rounds")
scalar("Trackman: shots tracked a second", "TM_Shots_Sec", 150, N0, "research.json trackman-shots: 70,000+ bays on ranges and in simulators")
scalar("Trackman: simulator bays", "TM_Sim_Bays", M.TRACKMAN_BAYS, N0, "research.json trackman-bays")
scalar("Trackman: all bays tracking shots", "TM_All_Bays", 70_000, N0, "research.json trackman-shots")
scalar("Trackman: share of simulator shots hit in rounds", "TM_Round_Share", 0.5, PCT, "Mostly practice: half the shots taken in rounds")
scalar("Trackman: shots a round", "TM_Shots_Round", 80, N0, "")
scalar("Trackman: rounds a year", "Trackman_Rounds", "=TM_Shots_Sec*60*60*24*365*(TM_Sim_Bays/TM_All_Bays)*TM_Round_Share/TM_Shots_Round", N0,
       "Only in a stress case; not a partner", calc=True)
scalar("Golfzon and the venue's share of a swing", "Venue_Share", M.SIM_SPLIT["golfzonAndVenue"], PCT, "Golfzon's proposal")
scalar("Payments, of gross", "GZ_Processing", M.GZ_PROCESSING, PCT, "")
scalar("Risk, claims and support, USD a swing", "GZ_Ops_USD", M.GZ_OPS_USD, USD, "The bay verifies the ace")
scalar("Launch marketing, of our share", "GZ_Marketing", M.GZ_MARKETING, PCT, "Launches, in-game media, the Tour")
years(A, r); cell(A, f"A{r}", "Per year", SUB); r += 1
per_year("Attach: share of rounds with a paid swing, plan", "attachPlan", [M.PLAN["gz_attach"][y] for y in Y], PCT2,
         "Phase 1 (2027) on existing features; phase 2 (2028) in the app and in-game; phase 3 (2029 on) in the game settings")
per_year("Attach, our targets", "attachTargets", [M.TARGETS["gz_attach"][y] for y in Y], PCT2, "The founder's targets: the upside, never the plan")
per_year("Average swing, USD, plan", "ticketPlan", [M.PLAN["gz_ticket"][y] for y in Y], USD, "$1-$100 tiers, each paying 1,000x; higher tiers open market by market")
per_year("Average swing, USD, our targets", "ticketTargets", [M.TARGETS["gz_ticket"][y] for y in Y], USD, "")
r += 1
header(A, r, "ON COURSE: THE APP", "I"); r += 1
years(A, r); cell(A, f"A{r}", "Per year", SUB); r += 1
per_year("Paid swings", "ocSwings", [M.OC_SWINGS[y] for y in Y], N0, "10,000 paid swings in the first year, on the tee, before the app")
per_year("Average swing, R", "ocAvg", [M.OC_AVG_ZAR[y] for y in Y], R0, "R50 to win R25,000, up to R1,000 to win R1m")
scalar("Insurer's premium, of every course swing", "OC_Premium", M.PREMIUM, PCT, "The Santam submission")
scalar("The club's share", "Club_Share", M.COURSE_SHARE, PCT, "")
scalar("Payments, of gross", "OC_Processing", M.OC_PROCESSING, PCT, "")
scalar("Video review and claims, R a swing", "OC_Verify", M.OC_VERIFY_ZAR, R0, "")
r += 1
header(A, r, "SPONSORSHIP", "I"); r += 1
scalar("Indwe's sponsorship, R a year", "Sponsor_Base", M.SPONSOR_BASE_ZAR, R0, "Contracted for 2027; assumed to renew")
scalar("Sponsorship per paid swing beyond 2027's, R", "Sponsor_Per_Swing", M.SPONSOR_PER_SWING_ZAR, R0, "About a seventh of what Indwe's R3m pays a swing in 2027")
r += 1
header(A, r, "GET LUCKY'S COSTS", "I"); r += 1
years(A, r); cell(A, f"A{r}", "Per year", SUB); r += 1
per_year("Central team and technology, plan, R", "centralPlan", [M.PLAN["central"][y] for y in Y], RM, "The founder, 4 Nov 2026")
per_year("Central team and technology, our targets, R", "centralTargets", [M.TARGETS["central"][y] for y in Y], RM, "")
per_year("Launch budget, plan, R", "launchPlan", [M.PLAN["brand_fixed"].get(y, 0) for y in Y], RM, "The global launch with Ernie, then the base")
per_year("Launch budget, our targets, R", "launchTargets", [M.TARGETS["brand_fixed"].get(y, 0) for y in Y], RM, "")
scalar("Brand, of revenue, on top of the launch budget", "Brand_Pct", M.BRAND_PCT, PCT, "")
scalar("Tax rate", "Tax_Rate", M.TAX, PCT, "After losses carried forward")
r += 1
header(A, r, "QUARTERLY CASH: SHARE OF EACH YEAR'S REVENUE BY QUARTER", "I"); r += 1
years(A, r, "CDEF", ["Q1", "Q2", "Q3", "Q4"]); r += 1
for label, key, w in (("2027", "w2027", M.CASH_WEIGHTS[2027]), ("2028", "w2028", M.CASH_WEIGHTS[2028]), ("2029 on", "wLater", [0.25] * 4)):
    cell(A, f"A{r}", label)
    for c_, v in zip("CDEF", w):
        cell(A, f"{c_}{r}", v, INPUT, PCT)
    cell(A, f"I{r}", "Back-loaded while Golfzon ramps; costs run evenly from day one" if key == "w2027" else "",
         NOTE)
    ROWS[key] = r
    r += 1
r += 1
header(A, r, "VALUE, RETURNS AND INSURANCE", "I"); r += 1
scalar("Value: multiple of each year's revenue", "Rev_Multiple", M.PLATFORM_MULTIPLE, '0.0"×"', "The multiple this plan has always used")
scalar("Held to a sale, years (end Q1 2027 to 31 Dec 2032)", "Hold_Years", 5.75, '0.00', "Illustrative")
scalar("Golfzon integration team, share of 2027 central cost", "GZ_Team_Share", 0.35, PCT, "For the use of funds")
scalar("Simulator prize, times the swing", "Prize_Multiple", M.SIM_PAYOUT, N0, "Every tier pays 1,000x")
scalar("Broker's commission, of premium", "Broker_Commission", M.BROKER_COMMISSION, PCT, "Indwe, the Santam submission")
scalar("Measured simulator ace rate: one in", "Ace_Measured", M.SIM_ACE_MEASURED, N0, "Golfzon, par-3 tee shots across every setting")
r += 1
header(A, r, "THE CASES (pick one in Model!C2)", "I"); r += 1
heads = ["Case", "Attach ×", "Ticket ×", "Drivers", "A year late", "Korea in", "Trackman 2028+", "Sim premium"]
for i, h in enumerate(heads):
    x = cell(A, f"{L(1 + i)}{r}", h, SUB)
    x.border = UNDER
    x.alignment = Alignment(horizontal="left" if i in (0, 3) else "right")
cell(A, f"I{r}", "1 = yes, 0 = no. Drivers: Plan or Targets (attach, ticket, central team, launch budget).", NOTE)
r += 1
s0 = r
for nm_, key, am, tm, drv, late, korea, tman, prem in SCEN:
    vals = [nm_, am, tm, drv, late, korea, tman, prem]
    fmts = [None, '0.00"×"', '0.00"×"', None, '0', '0', '0', PCT]
    for i, (v, fm) in enumerate(zip(vals, fmts)):
        x = cell(A, f"{L(1 + i)}{r}", v, BOLD if i == 0 else INPUT, fm)
        x.border = RULE
    r += 1
s1 = r - 1
for i, nm_ in enumerate(["Scen_Names", "Scen_Attach", "Scen_Ticket", "Scen_Drivers", "Scen_Late", "Scen_Korea", "Scen_Trackman", "Scen_Premium"]):
    name(nm_, A, f"${L(1 + i)}${s0}:${L(1 + i)}${s1}")
A.freeze_panes = "B3"


# ================================================================== one case, fully calculated
def block(ws, t, case_ref):
    """Write one case from row t: its levers, the annual P&L and cash, the quarterly cash test and
    its outputs. case_ref is the cell holding the case's name. Returns the rows it used."""
    R = {}
    look = lambda col: f"=INDEX({col},MATCH({case_ref},Scen_Names,0))"
    params = [("Attach multiplier", "am", "Scen_Attach", '0.00"×"'), ("Ticket multiplier", "tm", "Scen_Ticket", '0.00"×"'),
              ("Drivers", "drv", "Scen_Drivers", None), ("Golfzon a year late (1 = yes)", "late", "Scen_Late", "0"),
              ("Korea in (1 = yes)", "korea", "Scen_Korea", "0"), ("Trackman from 2028 (1 = yes)", "tman", "Scen_Trackman", "0"),
              ("Simulator premium", "prem", "Scen_Premium", PCT)]
    for i, (label, k, col, fm) in enumerate(params, 1):
        cell(ws, f"A{t + i}", label, HELPER).alignment = Alignment(horizontal="left", indent=1)
        cell(ws, f"C{t + i}", look(col), LINK, fm).alignment = Alignment(horizontal="right")
        R[k] = f"$C${t + i}"
    hdr = t + 9
    header(ws, hdr, "Get Lucky, annual", "Z")
    for c_, y in zip(YC, Y):
        x = cell(ws, f"{c_}{hdr}", str(y), WHITE)
        x.alignment = Alignment(horizontal="right", vertical="center")
    rows = ["rounds", "attachBase", "attach", "ticket", "swings", "gross", "share", "gzRev", "gzPrem", "gzDirect",
            "ocSwings", "ocGross", "ocRev", "ocDirect", "spons", "rev", "central", "launch", "brand", "ebitda", "margin",
            "taxable", "tax", "losscf", "net", "raise", "open", "close", "value", "mark", "premWritten", "pos"]
    rr = {k: hdr + 1 + i for i, k in enumerate(rows)}
    labels = {
        "rounds": ("Golfzon rounds a year", N0), "attachBase": ("Attach before any delay", PCT2),
        "attach": ("Attach: share of rounds with a paid swing", PCT2), "ticket": ("Average swing, USD", USD),
        "swings": ("Golfzon paid swings", N0), "gross": ("Golfzon gross, all parties", RM),
        "share": ("Get Lucky's share of a simulator swing", PCT), "gzRev": ("Revenue: Golfzon, our share", RM),
        "gzPrem": ("Premium to the insurer, simulators", RM), "gzDirect": ("Golfzon costs: payments, claims, launches", RM),
        "ocSwings": ("On course paid swings", N0), "ocGross": ("On course gross", RM), "ocRev": ("Revenue: on course, our share", RM),
        "ocDirect": ("On course costs: payments, verification", RM), "spons": ("Revenue: sponsorship", RM),
        "rev": ("REVENUE", RM), "central": ("Central team and technology", RM), "launch": ("Launch budget", RM),
        "brand": ("Brand: launch budget plus 8% of revenue", RM), "ebitda": ("EBITDA", RM), "margin": ("EBITDA margin", PCT),
        "taxable": ("Taxable, after losses brought forward", RM), "tax": ("Tax", RM), "losscf": ("Losses carried forward", RM),
        "net": ("Net profit", RM), "raise": ("The round", RM), "open": ("Cash, 1 January", RM), "close": ("Cash, 31 December", RM),
        "value": ("Value: revenue x the multiple", RM), "mark": ("The round marked at, 31 December", MULT),
        "premWritten": ("Premium written for the insurer (volume, not revenue)", RM), "pos": ("EBITDA positive? (1 = yes)", FLAG),
    }
    for i, (c_, y) in enumerate(zip(YC, Y)):
        p = YC[i - 1] if i else None
        g = lambda k: f"{c_}{rr[k]}"
        a_ = lambda key: f"Assumptions!{c_}${ROWS[key]}"
        pick = lambda plan, tg: f'IF({R["drv"]}="Targets",{a_(tg)},{a_(plan)})'
        f_ = {
            "rounds": f'=GZ_Rounds-IF({R["korea"]}=1,0,Korea_Rounds)+IF(AND({R["tman"]}=1,VALUE({c_}${hdr})>=2028),Trackman_Rounds,0)',
            "attachBase": f"={pick('attachPlan', 'attachTargets')}",
            "attach": (f'=IF({R["late"]}=1,0,{g("attachBase")})*{R["am"]}' if i == 0
                       else f'=IF({R["late"]}=1,{p}{rr["attachBase"]},{g("attachBase")})*{R["am"]}'),
            "ticket": f"={pick('ticketPlan', 'ticketTargets')}*{R['tm']}",
            "swings": f"={g('rounds')}*{g('attach')}",
            "gross": f"={g('swings')}*{g('ticket')}*FX_ZAR",
            "share": f"=1-Venue_Share-{R['prem']}",
            "gzRev": f"={g('gross')}*{g('share')}",
            "gzPrem": f"={g('gross')}*{R['prem']}",
            "gzDirect": f"={g('gross')}*GZ_Processing+{g('swings')}*GZ_Ops_USD*FX_ZAR+{g('gzRev')}*GZ_Marketing",
            "ocSwings": f"={a_('ocSwings')}",
            "ocGross": f"={g('ocSwings')}*{a_('ocAvg')}",
            "ocRev": f"={g('ocGross')}*(1-OC_Premium-Club_Share)",
            "ocDirect": f"={g('ocGross')}*OC_Processing+{g('ocSwings')}*OC_Verify",
            "spons": f"=Sponsor_Base+Sponsor_Per_Swing*MAX({g('swings')}+{g('ocSwings')}-($C{rr['swings']}+$C{rr['ocSwings']}),0)",
            "rev": f"={g('gzRev')}+{g('ocRev')}+{g('spons')}",
            "central": f"={pick('centralPlan', 'centralTargets')}",
            "launch": f"={pick('launchPlan', 'launchTargets')}",
            "brand": f"={g('launch')}+{g('rev')}*Brand_Pct",
            "ebitda": f"={g('rev')}-{g('gzDirect')}-{g('ocDirect')}-{g('central')}-{g('brand')}",
            "margin": f"=IF({g('rev')}=0,0,{g('ebitda')}/{g('rev')})",
            "taxable": f"={g('ebitda')}" if i == 0 else f"={g('ebitda')}-{p}{rr['losscf']}",
            "tax": f"=MAX({g('taxable')},0)*Tax_Rate",
            "losscf": f"=MAX(-{g('taxable')},0)",
            "net": f"={g('ebitda')}-{g('tax')}",
            "raise": f"=IF(VALUE({c_}${hdr})=2027,Round_ZAR,0)",
            "open": "=Opening_Cash" if i == 0 else f"={p}{rr['close']}",
            "close": f"={g('open')}+{g('ebitda')}-{g('tax')}+{g('raise')}",
            "value": f"={g('rev')}*Rev_Multiple",
            "mark": f"={g('value')}*Round_Stake/Round_ZAR",
            "premWritten": f"={g('gzPrem')}+{g('ocGross')}*OC_Premium",
            "pos": f"=IF({g('ebitda')}>0,1,0)",
        }
        for k in rows:
            font = HELPER if k in ("attachBase", "pos") else LINK if k in ("ticket", "ocSwings", "central", "launch") else CALC
            cell(ws, g(k), f_[k], font, labels[k][1], bold=k in ("rev", "ebitda", "close"))
    for k in rows:
        x = cell(ws, f"A{rr[k]}", labels[k][0], HELPER if k in ("attachBase", "pos") else CALC, bold=k in ("rev", "ebitda", "close"))
        if k in ("rev", "ebitda", "close"):
            total_row(ws, rr[k], ["A", "B"] + YC)
        else:
            x.alignment = Alignment(horizontal="left", indent=1)
    # --- quarterly cash ---
    q0 = rr["pos"] + 2
    header(ws, q0, "Quarterly cash test", "Z")
    for c_, lb in zip(QC, QL):
        x = cell(ws, f"{c_}{q0}", lb, WHITE)
        x.alignment = Alignment(horizontal="right", vertical="center")
    qrows = ["w", "ops", "round", "qtax", "qclose", "neg", "cum"]
    qr = {k: q0 + 1 + i for i, k in enumerate(qrows)}
    qlab = {"w": ("Share of the year's revenue", PCT), "ops": ("Operating cash in the quarter", RM), "round": ("The round", RM),
            "qtax": ("Tax, paid in Q4", RM), "qclose": ("Cash at the quarter end", RM), "neg": ("Below zero? (1 = yes)", FLAG),
            "cum": ("Quarters below zero so far", FLAG)}
    for k in qrows:
        x = cell(ws, f"A{qr[k]}", qlab[k][0], HELPER if k in ("neg", "cum") else CALC, bold=k == "qclose")
        if k == "qclose":
            total_row(ws, qr[k], ["A", "B"] + QC)
        else:
            x.alignment = Alignment(horizontal="left", indent=1)
    for k_, (c_, lb) in enumerate(zip(QC, QL)):
        yc, qi = YC[k_ // 4], k_ % 4
        wrow = ROWS["w2027"] if k_ < 4 else ROWS["w2028"] if k_ < 8 else ROWS["wLater"]
        prev = QC[k_ - 1] if k_ else None
        fixed = f"({yc}{rr['central']}+{yc}{rr['launch']})"
        qf = {
            "w": f"=Assumptions!${'CDEF'[qi]}${wrow}",
            "ops": f"=({yc}{rr['ebitda']}+{fixed})*{c_}{qr['w']}-{fixed}/4",
            "round": f'=IF({c_}${q0}="Q1 2027",Round_ZAR,0)',
            "qtax": f'=IF(LEFT({c_}${q0},2)="Q4",-{yc}{rr["tax"]},0)',
            "qclose": (f"=Opening_Cash+{c_}{qr['ops']}+{c_}{qr['round']}+{c_}{qr['qtax']}" if k_ == 0
                       else f"={prev}{qr['qclose']}+{c_}{qr['ops']}+{c_}{qr['round']}+{c_}{qr['qtax']}"),
            "neg": f"=IF({c_}{qr['qclose']}<0,1,0)",
            "cum": f"={c_}{qr['neg']}" if k_ == 0 else f"={prev}{qr['cum']}+{c_}{qr['neg']}",
        }
        for k in qrows:
            cell(ws, f"{c_}{qr[k]}", qf[k], LINK if k == "w" else HELPER if k in ("neg", "cum") else CALC, qlab[k][1], bold=k == "qclose")
    # --- outputs ---
    o0 = qr["cum"] + 2
    header(ws, o0, "This case in brief", "Z")
    span = lambda k: f"$C${qr[k]}:$Z${qr[k]}"
    labs = f"$C${q0}:$Z${q0}"
    first_neg = f"MATCH(1,{span('cum')},0)"
    outs = [
        ("lowest", "Lowest cash at a quarter end", f"=MIN({span('qclose')})", RM),
        ("lowQ", "Lowest quarter", f"=INDEX({labs},MATCH(C{o0 + 1},{span('qclose')},0))", None),
        ("lasts", "Cash lasts to (last quarter in credit)",
         f'=IF(ISNA({first_neg}),"Never runs short",IF({first_neg}=1,"Short in Q1 2027",INDEX({labs},{first_neg}-1)))', None),
        ("q1nr", "Q1 2027 without the round",
         f"=Opening_Cash+(C{rr['ebitda']}+C{rr['central']}+C{rr['launch']})*Assumptions!$C${ROWS['w2027']}-(C{rr['central']}+C{rr['launch']})/4", RM),
        ("posFrom", "EBITDA positive from",
         f'=IF(ISNA(MATCH(1,$C${rr["pos"]}:$H${rr["pos"]},0)),"Not by 2032",INDEX($C${hdr}:$H${hdr},MATCH(1,$C${rr["pos"]}:$H${rr["pos"]},0)))', None),
        ("peak", "Most of the opening cash and the round in use at once", f"=Opening_Cash+Round_ZAR-C{o0 + 1}", RM),
    ]
    O = {}
    for i, (k, label, fm_, nf) in enumerate(outs, 1):
        x = cell(ws, f"A{o0 + i}", label, bold=True)
        x.border = RULE
        ws[f"B{o0 + i}"].border = RULE
        x = cell(ws, f"C{o0 + i}", fm_, CALC, nf, OUTFILL, bold=True)
        x.alignment = Alignment(horizontal="right")
        x.border = RULE
        O[k] = f"$C${o0 + i}"
    return dict(rr=rr, qr=qr, O=O, hdr=hdr, end=o0 + len(outs))


def sheet_cols(ws):
    ws.column_dimensions["A"].width = 50
    ws.column_dimensions["B"].width = 4
    for c_ in QC:
        ws.column_dimensions[c_].width = 12


# ================================================================== Model (the chosen case)
Mo = wb.create_sheet("Model")
sheet_cols(Mo)
cell(Mo, "A1", "Get Lucky, 2027-2032: the chosen case (ZAR ex VAT, R m unless stated)", TITLE)
cell(Mo, "A2", "Case: pick one from the list", BOLD)
cell(Mo, "C2", "The plan", INPUT, None, KEY, note="Pick a case. Every sheet but Stress cases follows it.", bold=True)
Mo.merge_cells("C2:F2")
box = Side(style="medium", color=GREEN)
for c_ in "CDEF":
    Mo[f"{c_}2"].fill = KEY
    Mo[f"{c_}2"].border = Border(top=box, bottom=box, left=box if c_ == "C" else None, right=box if c_ == "F" else None)
Mo["C2"].alignment = Alignment(horizontal="left", vertical="center", indent=1)
Mo["A2"].alignment = Alignment(vertical="center")
Mo.row_dimensions[2].height = 22
dv = DataValidation(type="list", formula1=f"=Assumptions!$A${s0}:$A${s1}", allow_blank=False)
Mo.add_data_validation(dv)
dv.add("C2")
MB = block(Mo, 3, "$C$2")
cell(Mo, "A3", "CASE LEVERS", SUB)
Mo.freeze_panes = f"C{MB['hdr'] + 1}"

# ================================================================== Round (the chosen case, and the plan's use of funds)
Rs = wb.create_sheet("Round")
Rs.column_dimensions["A"].width = 52
for c_ in "BCDEFGH":
    Rs.column_dimensions[c_].width = 13
cell(Rs, "A1", "The round: what R9.0m buys, and what it is marked at", TITLE)
cell(Rs, "A2", "Marks and the sale follow the case in Model!C2:", NOTE)
cell(Rs, "C2", "=Model!C2", LINK)
rr_ = MB["rr"]
lines_r = [
    ("Raising", "=Round_ZAR", R0), ("Pre-money", "=Pre_ZAR", R0), ("Post-money", "=Post_ZAR", R0),
    ("The round's stake", "=Round_Stake", PCT2), ("Ernie Els, inside the pre-money", 0.05, PCT),
    ("Post-money on 2027 revenue", f"=Post_ZAR/Model!C{rr_['rev']}", '0.0"×"'),
    ("Post-money on 2028 revenue", f"=Post_ZAR/Model!D{rr_['rev']}", '0.0"×"'),
    ("Post-money on 2029 revenue", f"=Post_ZAR/Model!E{rr_['rev']}", '0.0"×"'),
]
r = 4
header(Rs, r - 1, "THE TERMS")
for label, fm_, nf in lines_r:
    cell(Rs, f"A{r}", label)
    cell(Rs, f"C{r}", fm_, INPUT if not str(fm_).startswith("=") else (LINK if "Model!" in str(fm_) else CALC), nf)
    r += 1
Rs["C8"].comment = Comment("Ernie's 5% is topped up inside the pre-money, so the round buys its full stake. Shown for reference.", "Get Lucky model")
r += 1
header(Rs, r, "THE ROUND MARKED AT, EACH 31 DECEMBER"); r += 1
years(Rs, r); r += 1
cell(Rs, f"A{r}", "Get Lucky's value")
for c_ in YC:
    cell(Rs, f"{c_}{r}", f"=Model!{c_}{rr_['value']}", LINK, RM)
vr = r; r += 1
cell(Rs, f"A{r}", "The round's stake, marked")
for c_ in YC:
    cell(Rs, f"{c_}{r}", f"={c_}{vr}*Round_Stake", CALC, RM)
r += 1
cell(Rs, f"A{r}", "The round's multiple", bold=True)
for c_ in YC:
    cell(Rs, f"{c_}{r}", f"={c_}{vr}*Round_Stake/Round_ZAR", CALC, MULT, bold=True)
total_row(Rs, r, ["A", "B"] + YC)
mr = r; r += 2
header(Rs, r, "A SALE ON 31 DECEMBER 2032 (ILLUSTRATIVE)"); r += 1
sale = [
    ("Value in 2032", f"=H{vr}", RM),
    ("That is, times 2032 EBITDA", f"=IF(Model!H{rr_['ebitda']}=0,0,H{vr}/Model!H{rr_['ebitda']})", '0.0"×"'),
    ("The round's multiple", f"=H{mr}", MULT),
    ("A year, from the end of Q1 2027", f"=C{r + 2}^(1/Hold_Years)-1", PCT),
    ("Cash on the balance sheet, 2032", f"=Model!H{rr_['close']}", RM),
    ("With the cash counted in", f"=(H{vr}+C{r + 4})*Round_Stake/Round_ZAR", MULT),
    ("A year, with the cash", f"=C{r + 5}^(1/Hold_Years)-1", PCT),
]
for label, fm_, nf in sale:
    cell(Rs, f"A{r}", label)
    cell(Rs, f"C{r}", fm_, LINK if "Model!" in fm_ else CALC, nf)
    r += 1
r += 1
header(Rs, r, "YOUR TICKET"); r += 1
cell(Rs, f"A{r}", "Ticket, R")
cell(Rs, f"C{r}", 1_000_000, INPUT, R0, KEY)
tr = r; r += 1
for label, fm_, nf in [("Your stake", f"=C{tr}/Post_ZAR", PCT2), ("Marked at December 2029", f"=C{tr}/Post_ZAR*E{vr}", R0),
                       ("A sale in 2032", f"=C{tr}/Post_ZAR*H{vr}", R0)]:
    cell(Rs, f"A{r}", label)
    cell(Rs, f"C{r}", fm_, CALC, nf)
    r += 1
r += 1

# ================================================================== Stress cases (every case at once)
St = wb.create_sheet("Stress cases")
sheet_cols(St)
cell(St, "A1", "Every case side by side (each calculated in full below)", TITLE)
cols = ["Revenue 2029", "EBITDA 2029", "Value 2029", "Round 2029", "Value 2032", "Round 2032", "Lowest cash", "Lowest quarter", "Cash lasts to"]
for i, h in enumerate(cols):
    x = cell(St, f"{L(3 + i)}3", h, WHITE)
    x.alignment = Alignment(horizontal="right", wrap_text=True)
header(St, 3, "Case", "K")
for i, h in enumerate(cols):
    x = cell(St, f"{L(3 + i)}3", h, WHITE)
    x.alignment = Alignment(horizontal="right", vertical="center", wrap_text=True)
St.row_dimensions[3].height = 30
blocks = {}
top = 4 + len(SCEN) + 2
for i, sc in enumerate(SCEN):
    t = top
    cell(St, f"A{t}", f"=Assumptions!$A${s0 + i}", Font(name=ARIAL, size=13, bold=True, color=GREEN))
    for c_ in ["A", "B"] + YC:
        St[f"{c_}{t}"].border = Border(bottom=Side(style="medium", color=LIME))
    St.row_dimensions[t].height = 22
    b = block(St, t, f"$A${t}")
    blocks[sc[1]] = b
    rr, O = b["rr"], b["O"]
    row = 4 + i
    cell(St, f"A{row}", f"=A{t}", BOLD).alignment = Alignment(horizontal="left", indent=1)
    links = [f"=E{rr['rev']}", f"=E{rr['ebitda']}", f"=E{rr['value']}", f"=E{rr['mark']}", f"=H{rr['value']}",
             f"=H{rr['mark']}", f"={O['lowest']}", f"={O['lowQ']}", f"={O['lasts']}"]
    fmts = [RM, RM, RM, MULT, RM, MULT, RM, None, None]
    for j, (fm_, nf) in enumerate(zip(links, fmts)):
        x = cell(St, f"{L(3 + j)}{row}", fm_, CALC, nf, OUTFILL if sc[1] == "plan" else None, bold=sc[1] == "plan")
        x.alignment = Alignment(horizontal="right")
    for c_ in "ABCDEFGHIJK":
        St[f"{c_}{row}"].border = RULE
        if sc[1] == "plan":
            St[f"{c_}{row}"].fill = OUTFILL
    St.row_dimensions[row].height = 18
    St.row_dimensions.group(t + 1, b["end"], outline_level=1, hidden=False)
    top = b["end"] + 3
St.freeze_panes = "C4"
for c_ in "CDEFGHIJK":
    St.column_dimensions[c_].width = 13

# ================================================================== Checks (ties to scripts/model.py)
Ck = wb.create_sheet("Checks")
Ck.column_dimensions["A"].width = 52
Ck.column_dimensions["B"].width = 26
for c_ in "CDEF":
    Ck.column_dimensions[c_].width = 16
cell(Ck, "A1", "Checks: the workbook against scripts/model.py", TITLE)
cell(Ck, "A2", "Python values are scripts/model.py's own results for the inputs shown on Assumptions. Change an input and the "
     "checks turn FALSE: that's expected.", NOTE)
cell(Ck, "A4", "Everything ties", BOLD)
header(Ck, 6, "Case", "F")
for i, h in enumerate(["Case", "Measure", "Workbook", "scripts/model.py", "Difference", "Ties"]):
    x = cell(Ck, f"{L(1 + i)}6", h.upper() if i == 0 else h, WHITE)
    x.alignment = Alignment(horizontal="left" if i < 2 else "right", vertical="center", indent=1 if i == 0 else 0)
r = 7
runs = {c["key"]: M.run(c) for c in M.CASES + M.TERM_CASES}
for i, sc in enumerate(SCEN):
    key = sc[1]
    py, b = runs[key], blocks[key]
    rr, O = b["rr"], b["O"]
    sref = lambda ref: f"='Stress cases'!{ref}"
    checks = [(f"Revenue {y}", f"{c_}{rr['rev']}", py["rows"][y]["revenue"], RM) for c_, y in zip(YC, Y)]
    checks += [(f"EBITDA {y}", f"{c_}{rr['ebitda']}", py["rows"][y]["ebitda"], RM) for c_, y in zip(YC, Y)]
    checks += [(f"Cash, 31 Dec {y}", f"{c_}{rr['close']}", py["rows"][y]["closing"], RM) for c_, y in zip(YC, Y)]
    checks += [("Value 2029", f"E{rr['value']}", py["vals"][2029]["total"], RM),
               ("Lowest cash", O["lowest"].replace("$", ""), py["low"][1], RM),
               ("Lowest quarter", O["lowQ"].replace("$", ""), py["low"][0], None),
               ("Cash lasts to", O["lasts"].replace("$", ""), py["lasts_to"] or "Never runs short", None)]
    for measure, ref, v, nf in checks:
        cell(Ck, f"A{r}", f"=Assumptions!$A${s0 + i}")
        cell(Ck, f"B{r}", measure)
        cell(Ck, f"C{r}", sref(ref), LINK, nf)
        cell(Ck, f"D{r}", round(v) if isinstance(v, float) else v, INPUT, nf)
        if isinstance(v, str):
            cell(Ck, f"E{r}", "")
            cell(Ck, f"F{r}", f"=C{r}=D{r}")
        else:
            cell(Ck, f"E{r}", f"=C{r}-D{r}", CALC, DIFF)
            cell(Ck, f"F{r}", f"=ABS(E{r})<1000")
        r += 1
plan_uof = M.use_of_funds(runs["plan"])
pb = blocks["plan"]["rr"]
uof_wb = {"golfzon": f"=ROUND('Stress cases'!C{pb['gzDirect']}+GZ_Team_Share*'Stress cases'!C{pb['central']},-4)",
          "launch": f"=ROUND('Stress cases'!C{pb['launch']},-4)"}
uof_wb["reserve"] = f"=Round_ZAR-C{r}-C{r + 1}"
for it in plan_uof["items"]:
    cell(Ck, f"A{r}", "The plan")
    cell(Ck, f"B{r}", f"Use of funds: {it['label']}")
    cell(Ck, f"C{r}", uof_wb[it["key"]], LINK, R0)
    cell(Ck, f"D{r}", it["ZAR"], INPUT, R0)
    cell(Ck, f"E{r}", f"=C{r}-D{r}", CALC, DIFF)
    cell(Ck, f"F{r}", f"=ABS(E{r})<1000")
    r += 1
cell(Ck, "C4", f"=AND(F7:F{r - 1})", CALC, None, OUTFILL, bold=True).alignment = Alignment(horizontal="center")
Ck.row_dimensions[4].height = 22
for rw in range(7, r):
    for c_ in "ABCDEF":
        Ck[f"{c_}{rw}"].border = RULE
    for c_ in "CDEF":
        Ck[f"{c_}{rw}"].alignment = Alignment(horizontal="right")
    Ck[f"A{rw}"].alignment = Alignment(horizontal="left", indent=1)
ok_font, bad_fill = Font(name=ARIAL, size=10, bold=True, color=GREEN_LIGHT), PatternFill("solid", fgColor="F8D7D3")
Ck.conditional_formatting.add(f"F7:F{r - 1}", FormulaRule(formula=["F7=TRUE"], font=ok_font))
Ck.conditional_formatting.add(f"F7:F{r - 1}", FormulaRule(formula=["F7=FALSE"], fill=bad_fill, font=Font(name=ARIAL, size=10, bold=True, color="9C2A1E")))
Ck.conditional_formatting.add("C4", FormulaRule(formula=["C4=TRUE"], fill=KEY, font=Font(name=ARIAL, size=10, bold=True, color=GREEN)))
Ck.conditional_formatting.add("C4", FormulaRule(formula=["C4=FALSE"], fill=bad_fill, font=Font(name=ARIAL, size=10, bold=True, color="9C2A1E")))
Ck.freeze_panes = "A7"

# Use of funds, from the plan, on the Round sheet (the deck's numbers)
rr0 = Rs.max_row + 2
header(Rs, rr0, "WHAT THE R9.0m PAYS FOR (THE PLAN)"); rr0 += 1
for i, it in enumerate(plan_uof["items"]):
    cell(Rs, f"A{rr0 + i}", it["label"])
    ref = f"Checks!C{r - len(plan_uof['items']) + i}"
    cell(Rs, f"C{rr0 + i}", f"={ref}", LINK, R0)
    cell(Rs, f"D{rr0 + i}", f"=C{rr0 + i}/Round_ZAR", CALC, PCT)
    cell(Rs, f"E{rr0 + i}", it["note"], NOTE)
n_ = len(plan_uof["items"])
cell(Rs, f"A{rr0 + n_}", "Revenue already pays the rest of the team in 2027", NOTE)
cell(Rs, f"C{rr0 + n_}",
     f"=ROUND((1-GZ_Team_Share)*'Stress cases'!C{pb['central']}+'Stress cases'!C{pb['ocDirect']}+('Stress cases'!C{pb['brand']}-'Stress cases'!C{pb['launch']}),-4)",
     LINK, R0)
cell(Rs, f"D{rr0 + n_}", f"='Stress cases'!C{pb['rev']}", LINK, RM)
cell(Rs, f"E{rr0 + n_}", "Running cost in 2027 (C), against 2027 revenue (D)", NOTE)
ir = rr0 + n_ + 2
header(Rs, ir, "WHY AN INSURER CAN COVER A SIMULATOR ACE"); ir += 1
for label, fm_, nf in [("Insurer breaks even at one ace in (plan premium)", f"=Prize_Multiple/(Assumptions!$H${s0}*(1-Broker_Commission))", N0),
                       ("Golfzon measures one ace in", "=Ace_Measured", N0),
                       ("Headroom", f"=C{ir + 1}/C{ir}", '0.00"×"')]:
    cell(Rs, f"A{ir}", label)
    cell(Rs, f"C{ir}", fm_, CALC, nf)
    ir += 1

# ---- the finish: night title bands with a lime rule, no gridlines, tab colours, print setup
from openpyxl.worksheet.page import PageMargins
from openpyxl.worksheet.properties import PageSetupProperties
from openpyxl.utils import column_index_from_string as CI
TABS = {"Read me": NIGHT, "Model": LIME, "Round": LIME, "Stress cases": GREEN, "Assumptions": GOLD, "Checks": MUTED}
BAND_TO = {"Model": "Z", "Stress cases": "Z", "Assumptions": "I", "Round": "H", "Checks": "F"}
for ws in wb.worksheets:
    ws.sheet_view.showGridLines = False
    ws.sheet_view.zoomScale = 100
    ws.sheet_properties.tabColor = TABS[ws.title]
    ws.page_setup.orientation = "landscape"
    ws.page_setup.paperSize = ws.PAPERSIZE_A4
    wide = ws.title in ("Model", "Stress cases")
    ws.sheet_properties.pageSetUpPr = PageSetupProperties(fitToPage=not wide)
    ws.page_setup.fitToWidth, ws.page_setup.fitToHeight = 1, 0
    ws.page_margins = PageMargins(left=0.4, right=0.4, top=0.5, bottom=0.6)
    ws.oddFooter.left.text = "Get Lucky Golf  ·  Investor model  ·  Confidential  ·  Forecast, not a promise"
    ws.oddFooter.right.text = "&A  ·  page &P of &N"
    for part in (ws.oddFooter.left, ws.oddFooter.right):
        part.size, part.font, part.color = 8, "Arial", MUTED
    if ws.title == "Read me":
        ws.page_setup.fitToHeight = 1
        continue
    if wide:
        ws.print_title_cols = "A:B"
    notes = {"Assumptions": "I", "Round": "E"}.get(ws.title)
    if notes:
        for (c_,) in ws.iter_rows(min_col=CI(notes), max_col=CI(notes), min_row=3):
            if isinstance(c_.value, str) and c_.font.i:   # the italic notes only, not year heads
                c_.alignment = Alignment(horizontal="left", indent=1)
    for col in range(1, CI(BAND_TO[ws.title]) + 1):
        c_ = ws.cell(row=1, column=col)
        c_.fill = BAND
        c_.border = Border(bottom=Side(style="medium", color=LIME))
    ws["A1"].font = TITLE
    ws["A1"].alignment = Alignment(horizontal="left", vertical="center", indent=1)
    ws.row_dimensions[1].height = 36
wb.move_sheet("Assumptions", offset=3)   # Read me, Model, Round, Stress cases, Assumptions, Checks
OUT.parent.mkdir(exist_ok=True)
wb.save(OUT)
print(f"wrote {OUT.relative_to(ROOT)}: {', '.join(ws.title for ws in wb.worksheets)}")

# openpyxl stores formulas without results. Where LibreOffice is installed, re-save through it so the
# file carries calculated values (previews and phones show numbers), then check it ties.
if shutil.which("soffice"):
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run(["soffice", "--headless", "--calc", "--convert-to", "xlsx:Calc MS Excel 2007 XML",
                        "--outdir", tmp, str(OUT)], check=True, capture_output=True, timeout=180)
        shutil.move(str(pathlib.Path(tmp) / OUT.name), OUT)
    ties = load_workbook(OUT, data_only=True)["Checks"]["C4"].value
    if ties is not True:
        sys.exit(f"the workbook does not tie to scripts/model.py (Checks!C4 = {ties!r})")
    print("calculated with LibreOffice: every check ties to scripts/model.py")
else:
    print("LibreOffice not found: the values calculate when the file is opened in Excel")
