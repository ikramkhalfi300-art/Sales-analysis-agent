"""
Central configuration for the Analyse_Agent pipeline.
Loads .env if present, then provides typed constants.
"""
import os
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

def _env(key: str, default):
    return os.getenv(key, default)

# ── App environment ──
APP_ENV   = _env("APP_ENV", "development")   # development | production
LOG_LEVEL = _env("LOG_LEVEL", "INFO")

# ── Anthropic / LLM ──
ANTHROPIC_API_KEY = _env("ANTHROPIC_API_KEY", "")
PRIMARY_MODEL     = _env("PRIMARY_MODEL", "claude-sonnet-4-6")
FALLBACK_MODEL    = _env("FALLBACK_MODEL", "claude-3-haiku-20240307")
MAX_TOKENS        = int(_env("MAX_TOKENS", "4096"))
MAX_RETRIES       = int(_env("MAX_RETRIES", "3"))
RETRY_BASE_DELAY  = float(_env("RETRY_BASE_DELAY", "2.0"))

# ── CV thresholds for volatility classification ──
CV_LOW      = 20
CV_MODERATE = 40
CV_HIGH     = 70

# ── Decision engine thresholds ──
RANK_TOP        = 0.85
RANK_STRONG     = 0.60
RANK_AVERAGE    = 0.40
RANK_WEAK       = 0.20
RECENT_DECLINE_WARN  = -10
RECENT_DECLINE_CRIT  = -15

# ── Trend classification ──
TREND_GROWING   = 5.0
TREND_DECLINING = -5.0

# ── Forecasting ──
BEAR_MULT_MIN  = 0.50
BULL_MULT_MAX  = 2.00

# ── Quality ──
FC_GAP_ANOMALY = 200

# ── Caching ──
CACHE_DIR  = Path(_env("CACHE_DIR", ".cache"))
CACHE_TTL  = int(_env("CACHE_TTL", "3600"))   # seconds
