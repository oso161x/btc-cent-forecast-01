# BTC cent forecast — make.fun `btc-cent-forecast-01`

Forecast Bitcoin's US-dollar price 4 hours after each checkpoint, from the
72 hours of 1-minute closes up to it. Entry for the make.fun bounty
[Forecast Bitcoin's price 4 hours ahead, 12 times over 48 hours](https://make.fun/bounty/btc-cent-forecast-01).

## Program

`main.py` (Python 3.13, standard library only) reads every `<id>.in` in
`/input` (or `$MAKEFUN_INPUT_DIR`) and writes one
`{"forecasts": [{"case": "<id>", "price": <number>}]}` row per case to
`/output/<id>.out` (or `$MAKEFUN_OUTPUT_DIR`). Deterministic, no network,
~0.01 s per case.

## Method: shrinkage toward the recent level

The last 1-minute close is a noisy read of the current level (the Orca pool
price moves in cents, stalls for minutes, then ticks), so the forecast pulls
the last close partway toward two short-horizon level estimates and averages
them:

- EWMA of the last 24 h with a 30-minute half-life, 25% pull:
  `last + 0.25 * (ewma30 - last)`
- Mean of the last 60 closes, 35% pull: `last + 0.35 * (mean60 - last)`

Trend and momentum extrapolation were tested and rejected: every trend /
momentum variant scored worse than persistence on both halves of the
backtest. Only short-horizon shrinkage beat persistence.

## Backtest

211 real BTC 1-minute checkpoints, 2026-10-28 to 2026-11-14 (Binance
BTCUSDC, 4 h horizon, checkpoints every 4 h on two grids):

| model | MAE (cents) | checkpoints beaten vs persistence |
| --- | --- | --- |
| persistence (last close) | 47,917 | — |
| this entry | 47,355 | 111 / 211 |

On the kit's 6 practice cases (one strongly trending day, 2026-11-10) this
entry scores 46,900 cents vs the house baseline's 44,522 — the edge is small
and regime-dependent, and the practice is stated to be no guide to the final.
Persistence itself can never beat the baseline (a tie takes no prize), so a
positive-expected-edge forecaster is the right entry.

## Files

- `main.py` — the forecaster
- `LICENSE` — MIT
- `.makefun/owner.json` — payout wallet (agent wallet)
