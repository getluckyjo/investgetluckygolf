# Get Lucky Golf — investor briefing (investgetluckygolf)

A static, password-gated pitch site in the current Get Lucky brand (the
getlucky-www system: night and forest panels, paper pages, lime for action,
Poster Gothic display, Inter body). Built fresh in October 2026; it does not
reuse the old investgetlucky site.

## How it is built

- `scripts/model.py` builds the forecast (Get Lucky: the plan, the founder's
  targets and every stress case) into `data/model.json`.
- `scripts/build_xlsx.py` writes the same plan as a live-formula workbook for
  review, `data/get-lucky-model.xlsx`. Its Checks sheet ties it to `scripts/model.py`, case by
  case; the build refuses a workbook that doesn't tie.
- `scripts/build_site.py` renders `index.html` from `data/model.json` and
  `data/facts.json`. **Never hand-edit numbers in index.html** — change the
  model or facts.json and rebuild:

      python3 scripts/model.py && python3 scripts/build_site.py && python3 scripts/build_xlsx.py

- The build refuses to write a page that carries anything on its banned list.

## The story (since 4 November 2026)

Willie Ross's review, agreed by the founders: **Get Lucky is the hole-in-one
app — on course, on simulators, and next on the driving range — presented by
Ernie Els.** The app is the one interface: it takes every entry, on course, on
simulators and on ranges. The round funds two opportunities through it (Willie, 5 Nov
2026): **the app worldwide** (every par 3, launched with Ernie in his markets from 2028;
a conservative worldwide line is in the numbers) and **simulator integration**, Golfzon
first, so the plan doesn't hang on one partner. Asset-light: no hardware, no debt. One round, R6.2m for exactly 10%
at R55.8m pre (R62m post), Q1 2027 (the founder, 5 Nov 2026). No interim raise.
To fit the smaller round, 2027 is trimmed by R2m: the launch budget R2m (not R3m)
and the central team R8m (not R9m, hires a little later).

## Rules

- **Pitch the plan as it is.** No backward references to earlier versions: no "no
  interim raise", "one round", "no debt", "no note" or "trimmed" (the founder, 5 Nov
  2026). The build bans them.
- **No convertible note.** The R1m note was withdrawn on 4 Nov 2026; opening
  cash on 1 Jan 2027 is R0. Never bring the note back onto the page.
- **No gyms, for now.** Planet Fitness, Virgin Active, gym bays and the bay
  company are out of the deck and the model completely (the founder, 4 Nov
  2026). The build bans any mention. The gym work lives in the
  simulatorstrategy repo; don't bring it back here unless the founder asks.
- **Golfzon reads "in talks" until it signs.** The founder (5 Nov 2026): the live site
  goes out with Golfzon "in talks on its own proposal". One switch, `GOLFZON_SIGNED` in
  `scripts/model.py`, drives every status line; turn it on and rebuild the day the
  agreement is signed, never before. While it's off the build bans any Golfzon signature.
  The integration is a demo (Golfzon's side simulated): never "integration built".
- **Live at https://invest.getluckygolf.co.za**, from the repo's default branch
  (`claude/relaxed-johnson-bmyhxn`, Vercel production). The `.vercel.app` addresses sit
  behind Vercel login; investors use the custom domain and `SITE_PASSWORD`.
- **The app is built, not launched.** It runs at golf days; the public launch
  follows an independent code audit (the founder, 4 Nov 2026). Never "live".
- **The driving range is "next"** and unnamed until a partner signs (inRange
  only after an NDA). Not in the numbers.
- **Golfzon's chain pricing is confidential.** It's no longer in this repo's
  files (it went with the gym model) and must never appear on the page.
- **Ernie Els:** 5% non-diluting equity as Founding Ambassador, topped up inside
  the pre-money (the founder, 27 October 2026); his agreement is signed (4 Nov
  2026). Normal shareholder rights: his 5% shares in any profit paid out and in
  any sale, like every other share (the founder, 29 October 2026). No separate
  profit share on top of his shares, no fee. The page may show the 5%.
- **No old material:** no games, no hole-in-one registry, no betting language,
  no Icons fan pick, no membership/club tab, no superseded rounds.
- Directors' ID numbers and home addresses never appear anywhere.
- The password is the Vercel env var `SITE_PASSWORD`; without it the site
  stays shut. Never commit it.
