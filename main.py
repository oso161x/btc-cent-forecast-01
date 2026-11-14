# btc-cent-forecast-01 entry: shrinkage forecaster for BTC's price 4 hours ahead.
#
# Idea (validated on 211 real BTC 1-minute checkpoints, 2026-10-28..2026-11-14,
# Binance BTCUSDC, 4h horizon, MAE in cents vs the persistence baseline):
#
#   * The last 1-minute close is a noisy read of the current level: the Orca
#     pool price moves in cents, stalls for minutes, then ticks. Averaging the
#     recent past denoises the level.
#   * Two shrinkage estimators, averaged:
#       - EWMA of the last 24h with a 30-minute half-life, pulled 25% toward
#         the last close:  last + 0.25 * (ewma30 - last)
#       - mean of the last 60 closes, pulled 35% toward the last close:
#         last + 0.35 * (mean60 - last)
#   * Trend/momentum extrapolation was tested and REJECTED: every trend and
#     momentum variant scored worse than persistence on both the tuning and
#     validation halves. Only short-horizon shrinkage toward the recent level
#     beat persistence, on 111 of 211 checkpoints, MAE 47,355 cents vs
#     persistence 47,917 cents (-1.2%). On the kit's 6 practice cases (one
#     strongly trending day, 2026-11-10) it scores 46,900 cents vs the house
#     baseline's 44,522 -- the edge is small and regime-dependent, but
#     persistence itself can never beat the baseline (a tie takes no prize),
#     so a positive-expected-edge forecaster is the right entry.
#
# Pure standard library, deterministic, no network, no randomness, runs in
# well under a second per case.

import json
import os
from pathlib import Path

INPUT_DIR = os.environ.get("MAKEFUN_INPUT_DIR", "/input")
OUTPUT_DIR = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")

MIN_PRICE = 0.00001
MAX_PRICE = 9_999_999.99999


def price5(x):
    """Clamp to the scorer's price grid: 5 decimals, (0, 10_000_000)."""
    return round(min(MAX_PRICE, max(MIN_PRICE, x)) * 1e5) / 1e5


def ewma(prices, half_life_minutes, window=1440):
    """Exponentially weighted mean over the last `window` closes."""
    alpha = 1.0 - 0.5 ** (1.0 / half_life_minutes)
    e = prices[-window]
    for x in prices[-window + 1:]:
        e = alpha * x + (1.0 - alpha) * e
    return e


def forecast(prices):
    """Forecast the close 240 minutes after the checkpoint.

    Average of two shrinkage estimators of the current level.
    """
    if not prices:
        raise ValueError("no prices in case")
    last = prices[-1]
    if not isinstance(last, (int, float)) or last != last or last in (float("inf"), float("-inf")):
        raise ValueError("last price is not a finite number")

    # Estimator 1: 30-minute half-life EWMA over the last 24h, 25% pull.
    f1 = last + 0.25 * (ewma(prices, 30) - last)
    # Estimator 2: mean of the last 60 closes, 35% pull.
    mean60 = sum(prices[-60:]) / min(60, len(prices))
    f2 = last + 0.35 * (mean60 - last)
    return price5((f1 + f2) / 2.0)


def main():
    in_dir = Path(INPUT_DIR)
    out_dir = Path(OUTPUT_DIR)
    out_dir.mkdir(parents=True, exist_ok=True)
    inputs = sorted(p for p in in_dir.iterdir() if p.name.endswith(".in"))
    for path in inputs:
        case_id = path.name[: -len(".in")]
        with path.open("r", encoding="utf-8") as f:
            case = json.load(f)
        markets = case.get("markets")
        if not isinstance(markets, list) or len(markets) != 1:
            raise ValueError(f"{path.name} does not hold exactly one market")
        prices = markets[0].get("prices")
        if not isinstance(prices, list) or not prices:
            raise ValueError(f"{path.name} has no prices")
        guess = forecast([float(p) for p in prices])
        out = {"forecasts": [{"case": case_id, "price": guess}]}
        with (out_dir / f"{case_id}.out").open("w", encoding="utf-8") as f:
            f.write(json.dumps(out) + "\n")


if __name__ == "__main__":
    main()
