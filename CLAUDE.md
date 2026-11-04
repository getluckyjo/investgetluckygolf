# Get Lucky Golf — investor briefing (investgetluckygolf)

A static, password-gated pitch site in the current Get Lucky brand (the
getlucky-www system: night and forest panels, paper pages, lime for action,
Poster Gothic display, Inter body). Built fresh in October 2026; it does not
reuse the old investgetlucky site.

## How it is built

- `scripts/model.py` builds the forecast (Get Lucky: the plan, the founder's
  targets and every stress case) into `data/model.json`. The gym bay engine is
  still in the file but runs only as the internal `WITH_GYMS` case, printed in
  the build log and never written for the page.
- `scripts/build_site.py` renders `index.html` from `data/model.json` and
  `data/facts.json`. **Never hand-edit numbers in index.html** — change the
  model or facts.json and rebuild:

      python3 scripts/model.py && python3 scripts/build_site.py

- The build refuses to write a page that carries anything on its banned list.

## The story (since 4 November 2026)

Willie Ross's review, agreed by the founders: **Get Lucky is the hole-in-one
app — on course, on simulators, and next on the driving range — presented by
Ernie Els.** Asset-light: no hardware, no debt. One round, R9.0m for about 14%
at R56m pre (R65m post), Q1 2027. No interim raise.

## Rules

- **No convertible note.** The R1m note was withdrawn on 4 Nov 2026; opening
  cash on 1 Jan 2027 is R0. Never bring the note back onto the page.
- **The gyms are an option, not the plan.** Planet Fitness and Virgin Active
  appear only as "in discussion": no bay counts, capex, paybacks, unit
  economics, RMB, bay company or its terms, and nothing in the numbers. If it
  goes ahead, the bays are funded in their own company, never by this round.
  Never say Planet Fitness or Virgin Active has signed.
- **Golfzon is shown as signed.** The founder (4 Nov 2026): build the deck as if
  Golfzon has signed; the agreement is signed before we raise. One switch,
  `GOLFZON_SIGNED` in `scripts/model.py`, drives every status line; off, the
  page reads "in talks" and the build bans any Golfzon signature. **Don't send
  the page while the switch is on and the agreement isn't signed.** The
  integration is a demo (Golfzon's side simulated): never "integration built".
- **The app is built, not launched.** It runs at golf days; the public launch
  follows an independent code audit (the founder, 4 Nov 2026). Never "live".
- **The driving range is "next"** and unnamed until a partner signs (inRange
  only after an NDA). Not in the numbers.
- **Golfzon's chain pricing is confidential.** It lives in `scripts/model.py`
  only (excluded from the deploy by `.vercelignore`). Never on the page.
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
