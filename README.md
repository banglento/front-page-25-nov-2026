# Front Page — 25 November 2026

[![make.fun](https://make.fun/badge/news-image-20261125.svg)](https://make.fun/c/news-image-20261125)
[![rank](https://make.fun/badge/news-image-20261125/banglento/front-page-25-nov-2026/rank.svg)](https://make.fun/c/news-image-20261125)
[![reward](https://make.fun/badge/news-image-20261125/banglento/front-page-25-nov-2026/reward.svg)](https://make.fun/c/news-image-20261125)

A one-page newspaper front page summing up the world's news of
**Wednesday 25 November 2026**, drawn entirely by `main.py`
(Python 3.13, standard library only — its own 5×7 bitmap font,
procedural illustrations and a hand-rolled PNG encoder, no network,
fully deterministic).

Stories on the page:

- **Ukraine hits two Russian ships** — a drone strike on a Russian
  cargo ship in the Gulf of Finland, and a Russian warship sunk in
  Benghazi, Libya.
- **COP31 collapses** — the Antalya climate summit ends with no final
  deal as oil and gas producers block fossil-fuel phaseout language.
- **Houthis hit Riyadh tower** — Kingdom Centre struck, 11 hurt.
- **47,000 women killed in a year** — by partners or family, about
  5 every hour, per the UN.
- **Trump pardons the turkeys** — Freedom and Feathers spared at the
  White House; Medal of Freedom for Rudy Giuliani.
- **Also:** NATO jets to Poland; US base Sigonella shut after drone
  sightings.

Run it:

```sh
mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py
```

It writes `out/entry.png` (1024×1024, under 1 MiB). Run it twice and
the bytes are identical.

Entry for the [make.fun](https://make.fun) competition
[news-image-20261125](https://make.fun/c/news-image-20261125).
