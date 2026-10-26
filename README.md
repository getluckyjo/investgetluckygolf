# Get Lucky Golf — investor briefing 2027

The pitch for the R1.0m convertible note (November 2026; R36m cap or 20%
discount, whichever is better) and the R10.0m round (Q1 2027, about 15% at R56m
pre-money, R66m post).

The story: the app we built, Golfzon's 15,029-location network and the
integration we built for it, golf bays in Planet Fitness (signed) and Virgin
Active (in talks) funded in their own company, and Ernie Els as Founding
Ambassador.

```
python3 scripts/model.py          # forecast -> data/model.json (--dry to print only)
python3 scripts/build_site.py     # data -> index.html (refuses banned content)
python3 -m http.server 8000       # preview locally (the gate only runs on Vercel)
```

Deploy: Vercel, static, with `middleware.js` gating every path. Set
`SITE_PASSWORD` in the project's environment variables (Preview and
Production). `scripts/` and `data/` are never deployed.
