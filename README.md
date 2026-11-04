# Get Lucky Golf — investor briefing 2027

The pitch for the R9.0m round (Q1 2027, about 14% at R56m pre-money, R65m
post). One round, no interim raise.

The story: Get Lucky is the hole-in-one app — on course in South Africa, on
Golfzon's 15,029 simulator locations worldwide, and next on the driving range —
presented by Ernie Els, Founding Ambassador. Asset-light: no hardware, no debt.
Golf bays in Planet Fitness and Virgin Active are an option we hold, not in the
plan or the numbers.

```
python3 scripts/model.py          # forecast -> data/model.json (--dry to print only)
python3 scripts/build_site.py     # data -> index.html (refuses banned content)
python3 -m http.server 8000       # preview locally (the gate only runs on Vercel)
```

The page shows Golfzon as signed (`GOLFZON_SIGNED` in `scripts/model.py`): send
it only once the agreement is signed.

Deploy: Vercel, static, with `middleware.js` gating every path. Set
`SITE_PASSWORD` in the project's environment variables (Preview and
Production). `scripts/` and `data/` are never deployed.
