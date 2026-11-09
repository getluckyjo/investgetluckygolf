# Get Lucky Golf — investor briefing 2027

The pitch for the Q1 2027 round: exactly 10% at R55.8m pre-money (R62m post),
R3.4m in cash for 5.5% and 4.5% for an ongoing development partner.

The story: Get Lucky is the hole-in-one app — on course in South Africa, on
Golfzon's 15,029 simulator locations worldwide, and next on the driving range —
presented by Ernie Els, Founding Ambassador. One app takes every entry; the round
funds the app worldwide and simulator integration, Golfzon first.

```
python3 scripts/model.py          # forecast -> data/model.json (--dry to print only)
python3 scripts/build_site.py     # data -> index.html (refuses banned content)
python3 scripts/build_xlsx.py     # data -> data/get-lucky-model.xlsx, the model to review
python3 -m http.server 8000       # preview locally (the gate only runs on Vercel)
```

Live at https://invest.getluckygolf.co.za (production: the default branch). Golfzon
reads "in talks" until the agreement is signed; then set `GOLFZON_SIGNED` in
`scripts/model.py` and rebuild.

Deploy: Vercel, static, with `middleware.js` gating every path. Set
`SITE_PASSWORD` in the project's environment variables (Preview and
Production). `scripts/` and `data/` are never deployed.
