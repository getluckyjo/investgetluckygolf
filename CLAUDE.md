# Get Lucky Golf — investor briefing (investgetluckygolf)

A static, password-gated pitch site in the current Get Lucky brand (the
getlucky-www system: night and forest panels, paper pages, lime for action,
Poster Gothic display, Inter body). Built fresh in October 2026; it does not
reuse the old investgetlucky site.

## How it is built

- `scripts/model.py` builds the forecast (Get Lucky and the bay company, the
  plan, the founder's targets and every stress case) into `data/model.json`.
- `scripts/build_site.py` renders `index.html` from `data/model.json` and
  `data/facts.json`. **Never hand-edit numbers in index.html** — change the
  model or facts.json and rebuild:

      python3 scripts/model.py && python3 scripts/build_site.py

- The build refuses to write a page that carries anything on its banned list.

## Rules

- **Golfzon's chain pricing is confidential.** It lives in `scripts/model.py`
  only (excluded from the deploy by `.vercelignore`). Never on the page.
- **Never publish Ernie Els's percentage.** "Equity and a share of profit".
- **No old material:** no games, no hole-in-one registry, no betting language,
  no Icons fan pick, no membership/club tab, no superseded rounds.
- Statuses as the founder set them: Golfzon "in" on its October 2026 proposal,
  Ernie onboard as Founding Ambassador, Planet Fitness signed (first installs
  Q1 2027), Virgin Active in talks (modelled from mid-2027).
- The bay company's terms (6% fee, 15% preferred return, 50/50 split, R3m
  reserve, 1.25× lock-up) are proposals and the page says so.
- Directors' ID numbers and home addresses never appear anywhere.
- The password is the Vercel env var `SITE_PASSWORD`; without it the site
  stays shut. Never commit it.
