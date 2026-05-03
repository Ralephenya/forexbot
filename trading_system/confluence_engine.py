"""
Confluence Engine - Hedge Fund Grade Trade Scoring System

Philosophy (30 years of market wisdom):
  - The market gives you 1-2 A+ setups per week, not 20.
  - Never trade in the middle of nowhere. Only trade at key levels.
  - Never fight the higher timeframe. It always wins.
  - Quality over quantity. Every. Single. Time.
  - A trade that scores less than 7/10 is not a trade — it's a gamble.

Scoring layers (10 points total):
  Layer 1: Higher Timeframe Trend Alignment     (2 pts) — HTF always wins
  Layer 2: RSI Extreme Reading                  (2 pts) — extremes mean exhaustion
  Layer 3: Price at Key S/R Level               (2 pts) — only trade at a reason
  Layer 4: VWAP Position                        (1 pt)  — institutional fair value
  Layer 5: Prime Session Hour                   (1 pt)  — liquidity = clean moves
  Layer 6: MACD Momentum Confirmation           (1 pt)  — momentum must agree
  Layer 7: Volatility Regime                    (1 pt)  — need range to profit

Grades:
  A+  (9-10):  Take it. Max confidence. Full size.
  A   (7-8):   Take it. High confidence. Normal size.
  B   (5-6):   Skip. Not enough confluence. Wait for better.
  C   (<5):    Never touch. This is noise.
"""

import pandas as pd
import numpy as np
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Session hours where institutional money is most active
PRIME_HOURS = [8, 9, 10, 13, 14]   # London open + NY open (UTC)
DEAD_HOURS  = [0, 1, 2, 3, 4, 5, 22, 23]  # Asian thin market

# How close price must be to an S/R level to count (as fraction of ATR)
SR_PROXIMITY_ATR_MULTIPLIER = 0.5

# Minimum score to take a trade
MIN_SCORE_TO_TRADE = 7


def detect_sr_levels(df: pd.DataFrame, lookback: int = 50) -> list:
    """
    Find key support and resistance levels from swing highs and lows.

    A 30-year pro does not draw random lines. They look for:
    - Swing highs: a high that is higher than N candles on both sides
    - Swing lows:  a low that is lower than N candles on both sides

    Args:
        df: OHLCV DataFrame
        lookback: How many candles back to scan

    Returns:
        List of price levels that are meaningful S/R
    """
    levels = []
    data = df.tail(lookback).copy().reset_index(drop=True)
    n = len(data)

    # Need at least 10 candles to detect a proper swing
    wing = 3  # candles on each side must be lower/higher

    for i in range(wing, n - wing):
        high_i = data['high'].iloc[i]
        low_i  = data['low'].iloc[i]

        # Swing high: this candle's high is the highest in wing*2+1 window
        is_swing_high = all(
            high_i >= data['high'].iloc[i - j] and
            high_i >= data['high'].iloc[i + j]
            for j in range(1, wing + 1)
        )

        # Swing low: this candle's low is the lowest in wing*2+1 window
        is_swing_low = all(
            low_i <= data['low'].iloc[i - j] and
            low_i <= data['low'].iloc[i + j]
            for j in range(1, wing + 1)
        )

        if is_swing_high:
            levels.append(high_i)
        if is_swing_low:
            levels.append(low_i)

    # Deduplicate levels that are very close to each other (cluster them)
    if not levels:
        return []

    levels = sorted(levels)
    clustered = [levels[0]]
    price_cluster_tolerance = data['close'].iloc[-1] * 0.0003  # 0.03% tolerance

    for level in levels[1:]:
        if abs(level - clustered[-1]) > price_cluster_tolerance:
            clustered.append(level)

    return clustered


def is_near_sr_level(price: float, sr_levels: list, atr: float) -> tuple:
    """
    Check if current price is near any meaningful S/R level.

    A hedge fund manager only pulls the trigger when price is AT a level,
    not floating somewhere in the middle of a range.

    Args:
        price: Current close price
        sr_levels: List of S/R price levels
        atr: Current ATR for proximity calculation

    Returns:
        Tuple of (is_near: bool, nearest_level: float, distance_pips: float)
    """
    if not sr_levels or atr <= 0:
        return False, 0.0, 999.0

    proximity_threshold = atr * SR_PROXIMITY_ATR_MULTIPLIER
    nearest = min(sr_levels, key=lambda x: abs(x - price))
    distance = abs(nearest - price)

    return distance <= proximity_threshold, nearest, distance / 0.0001  # distance in pips


def score_trade(
    df: pd.DataFrame,
    direction: str,
    current_hour: int,
    vwap: Optional[float] = None
) -> dict:
    """
    Score a potential trade from 0-10 using institutional confluence logic.

    This is the core decision engine. It looks at every available piece
    of evidence and asks: "Would a 30-year veteran take this trade?"

    Args:
        df: DataFrame with OHLCV + all calculated indicators
        direction: 'BUY' or 'SELL'
        current_hour: Current UTC hour (0-23)
        vwap: Optional VWAP level (if available from indicator_calculator)

    Returns:
        dict with score, grade, reasons, take_trade flag, and all sub-scores
    """
    score = 0
    reasons = []
    warnings = []
    sub_scores = {}

    if df.empty or len(df) < 50:
        return {
            'score': 0, 'grade': 'F', 'take_trade': False,
            'reasons': ['Insufficient data'], 'warnings': [],
            'sub_scores': {}, 'direction': direction
        }

    latest = df.iloc[-1]
    direction = direction.upper()

    # ─────────────────────────────────────────────────────────────────
    # LAYER 1: HIGHER TIMEFRAME TREND (2 points)
    # Never fight the trend. The HTF always wins eventually.
    # We use EMA50 vs EMA200 as a proxy for the higher timeframe bias.
    # ─────────────────────────────────────────────────────────────────
    htf_score = 0
    htf_aligned = False

    if 'ema_50' in df.columns and 'ema_200' in df.columns:
        ema50  = latest.get('ema_50', None)
        ema200 = latest.get('ema_200', None)

        if ema50 is not None and ema200 is not None and not pd.isna(ema50) and not pd.isna(ema200):
            htf_trend = 'UP' if ema50 > ema200 else 'DOWN'
            htf_aligned = (
                (direction == 'BUY'  and htf_trend == 'UP') or
                (direction == 'SELL' and htf_trend == 'DOWN')
            )
            if htf_aligned:
                htf_score = 2
                reasons.append(f"HTF trend aligned: EMA50 {'>' if htf_trend=='UP' else '<'} EMA200 ({htf_trend})")
            else:
                warnings.append(f"COUNTER-TREND trade: EMA50/200 says {htf_trend}, you want {direction}")
    else:
        # Fallback: use EMA20 vs close as a simpler trend gauge
        if 'ema' in df.columns:
            ema20 = latest.get('ema', None)
            close = latest.get('close', None)
            if ema20 and close and not pd.isna(ema20):
                if (direction == 'BUY' and close > ema20) or (direction == 'SELL' and close < ema20):
                    htf_score = 1
                    reasons.append(f"Price {'above' if direction=='BUY' else 'below'} EMA20 — trend aligned")
                else:
                    warnings.append("Price going against EMA20")

    score += htf_score
    sub_scores['htf_trend'] = htf_score

    # ─────────────────────────────────────────────────────────────────
    # LAYER 2: RSI EXTREME READING (2 points)
    # RSI at extremes means the market is exhausted in one direction.
    # Perfect for mean reversion entries.
    # ─────────────────────────────────────────────────────────────────
    rsi_score = 0
    rsi_col = 'rsi' if 'rsi' in df.columns else 'rsi_14'

    if rsi_col in df.columns:
        rsi = latest.get(rsi_col, None)
        if rsi is not None and not pd.isna(rsi):
            if direction == 'BUY' and rsi <= 30:
                rsi_score = 2
                reasons.append(f"RSI deeply oversold at {rsi:.1f} — buyers exhausted")
            elif direction == 'BUY' and rsi <= 38:
                rsi_score = 1
                reasons.append(f"RSI approaching oversold at {rsi:.1f}")
            elif direction == 'SELL' and rsi >= 70:
                rsi_score = 2
                reasons.append(f"RSI deeply overbought at {rsi:.1f} — sellers exhausted")
            elif direction == 'SELL' and rsi >= 62:
                rsi_score = 1
                reasons.append(f"RSI approaching overbought at {rsi:.1f}")
            else:
                warnings.append(f"RSI neutral at {rsi:.1f} — no extreme reading")

    score += rsi_score
    sub_scores['rsi'] = rsi_score

    # ─────────────────────────────────────────────────────────────────
    # LAYER 3: PRICE AT KEY S/R LEVEL (2 points)
    # The single most important concept in technical analysis.
    # Only trade AT a reason. Never in the middle of nowhere.
    # ─────────────────────────────────────────────────────────────────
    sr_score = 0

    if 'atr' in df.columns:
        atr = latest.get('atr', None)
        close = latest.get('close', None)

        if atr is not None and close is not None and not pd.isna(atr) and not pd.isna(close):
            sr_levels = detect_sr_levels(df, lookback=80)
            is_near, nearest_level, dist_pips = is_near_sr_level(close, sr_levels, atr)

            if is_near:
                sr_score = 2
                reasons.append(f"Price at key S/R level {nearest_level:.5f} ({dist_pips:.1f} pips away)")
            elif dist_pips < 10:
                sr_score = 1
                reasons.append(f"Price near S/R level {nearest_level:.5f} ({dist_pips:.1f} pips)")
            else:
                warnings.append(f"Price floating {dist_pips:.1f} pips from nearest S/R — no clear level")

    score += sr_score
    sub_scores['sr_level'] = sr_score

    # ─────────────────────────────────────────────────────────────────
    # LAYER 4: VWAP POSITION (1 point)
    # VWAP is the institutional fair value. Banks buy below it, sell above.
    # Trading with VWAP bias means trading with the big money.
    # ─────────────────────────────────────────────────────────────────
    vwap_score = 0

    if vwap is not None and vwap > 0:
        close = latest.get('close', None)
        if close is not None:
            if direction == 'BUY' and close < vwap:
                vwap_score = 1
                reasons.append(f"Below VWAP at {vwap:.5f} — buying at discount")
            elif direction == 'SELL' and close > vwap:
                vwap_score = 1
                reasons.append(f"Above VWAP at {vwap:.5f} — selling at premium")
            else:
                warnings.append(f"Trading against VWAP position")
    elif 'vwap' in df.columns:
        vwap_val = latest.get('vwap', None)
        close = latest.get('close', None)
        if vwap_val is not None and close is not None and not pd.isna(vwap_val):
            if direction == 'BUY' and close < vwap_val:
                vwap_score = 1
                reasons.append(f"Below VWAP {vwap_val:.5f} — buying at discount")
            elif direction == 'SELL' and close > vwap_val:
                vwap_score = 1
                reasons.append(f"Above VWAP {vwap_val:.5f} — selling at premium")

    score += vwap_score
    sub_scores['vwap'] = vwap_score

    # ─────────────────────────────────────────────────────────────────
    # LAYER 5: PRIME SESSION HOUR (1 point)
    # London and NY open are where 80% of daily volume happens.
    # Moves in these sessions are clean, purposeful, and follow through.
    # Asian session moves are fake-outs and noise. Stay away.
    # ─────────────────────────────────────────────────────────────────
    session_score = 0

    if current_hour in PRIME_HOURS:
        session_score = 1
        session_name = (
            "London Open" if current_hour in [8, 9, 10] else "NY Open"
        )
        reasons.append(f"Prime session: {session_name} at {current_hour}:00 UTC")
    elif current_hour in DEAD_HOURS:
        warnings.append(f"Dead zone hour {current_hour}:00 UTC — thin liquidity, avoid")
    else:
        reasons.append(f"Acceptable session hour {current_hour}:00 UTC")

    score += session_score
    sub_scores['session'] = session_score

    # ─────────────────────────────────────────────────────────────────
    # LAYER 6: MACD MOMENTUM CONFIRMATION (1 point)
    # MACD tells you WHERE momentum is going, not where price has been.
    # You want momentum agreeing with your direction before entry.
    # ─────────────────────────────────────────────────────────────────
    macd_score = 0

    if 'macd' in df.columns and 'macd_signal' in df.columns:
        macd      = latest.get('macd', None)
        macd_sig  = latest.get('macd_signal', None)
        macd_hist = latest.get('macd_hist', None)

        if macd is not None and macd_sig is not None and not pd.isna(macd) and not pd.isna(macd_sig):
            macd_bullish = macd > macd_sig
            macd_bearish = macd < macd_sig

            if direction == 'BUY' and macd_bullish:
                macd_score = 1
                reasons.append(f"MACD bullish crossover — momentum confirming BUY")
            elif direction == 'SELL' and macd_bearish:
                macd_score = 1
                reasons.append(f"MACD bearish crossover — momentum confirming SELL")
            else:
                # Check histogram for divergence (early signal)
                if macd_hist is not None and not pd.isna(macd_hist):
                    warnings.append(
                        f"MACD diverging from direction (hist={macd_hist:.6f})"
                    )

    score += macd_score
    sub_scores['macd'] = macd_score

    # ─────────────────────────────────────────────────────────────────
    # LAYER 7: VOLATILITY REGIME (1 point)
    # Mean reversion strategies NEED volatility to work.
    # Trading RSI extremes in a flat, dead market = death by a thousand cuts.
    # ─────────────────────────────────────────────────────────────────
    vol_score = 0

    if 'is_high_volatility' in df.columns:
        is_high_vol = latest.get('is_high_volatility', False)
        if is_high_vol:
            vol_score = 1
            atr_val = latest.get('atr', 0)
            reasons.append(f"High volatility regime — ATR={atr_val:.5f}, range is wide enough")
        else:
            warnings.append("Low volatility regime — mean reversion may be sluggish")

    score += vol_score
    sub_scores['volatility'] = vol_score

    # ─────────────────────────────────────────────────────────────────
    # FINAL GRADE
    # ─────────────────────────────────────────────────────────────────
    if score >= 9:
        grade = 'A+'
        take_trade = True
        grade_msg = "EXCEPTIONAL setup — full conviction"
    elif score >= 7:
        grade = 'A'
        take_trade = True
        grade_msg = "HIGH QUALITY setup — take the trade"
    elif score >= 5:
        grade = 'B'
        take_trade = False
        grade_msg = "MEDIOCRE setup — not enough confluence, wait"
    else:
        grade = 'C'
        take_trade = False
        grade_msg = "WEAK setup — this is noise, stay out"

    result = {
        'score': score,
        'max_score': 10,
        'grade': grade,
        'grade_message': grade_msg,
        'take_trade': take_trade,
        'direction': direction,
        'reasons': reasons,
        'warnings': warnings,
        'sub_scores': sub_scores,
    }

    log_level = logging.INFO if take_trade else logging.DEBUG
    logger.log(
        log_level,
        f"Confluence Score: {score}/10 [{grade}] {direction} | "
        f"Take trade: {take_trade} | {grade_msg}"
    )
    if reasons:
        for r in reasons:
            logger.log(log_level, f"  ✓ {r}")
    if warnings:
        for w in warnings:
            logger.debug(f"  ✗ {w}")

    return result


def get_trade_size_multiplier(grade: str) -> float:
    """
    A hedge fund manager sizes up on A+ setups and sizes down on A setups.
    B and C don't exist in the trade blotter.

    Args:
        grade: Trade grade (A+, A, B, C)

    Returns:
        Position size multiplier (1.0 = normal size)
    """
    return {
        'A+': 1.5,   # Exceptional — 150% of normal size
        'A':  1.0,   # High quality — normal size
        'B':  0.0,   # Not taken
        'C':  0.0,   # Not taken
        'F':  0.0,   # Never taken
    }.get(grade, 0.0)
