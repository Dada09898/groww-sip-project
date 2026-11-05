"""Central config. Every value can be overridden in .env."""
import os, re
from dotenv import load_dotenv
load_dotenv()

# Which AI to use: "gemini" (free tier) or "anthropic" (paid). Default: whichever key you have.
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
_ak = os.getenv("ANTHROPIC_API_KEY", "")
_has_claude = _ak.startswith("sk-ant-") and "xxxx" not in _ak
LLM_PROVIDER = (os.getenv("LLM_PROVIDER") or ("anthropic" if _has_claude else "gemini")).lower()
# Gemini model IDs: "-latest" aliases point to Google's current models. If one errors,
# copy a model ID from aistudio.google.com and put it in .env.
GEMINI_TAG_MODEL = os.getenv("GEMINI_TAG_MODEL", "gemini-flash-lite-latest")
GEMINI_SYNTH_MODEL = os.getenv("GEMINI_SYNTH_MODEL", "gemini-flash-latest")
GEMINI_RPM = int(os.getenv("GEMINI_RPM", "10"))        # requests/minute to stay under free limits
# Items tagged per LLM call. Batching = far fewer calls (important on the free tier).
TAG_BATCH_SIZE = int(os.getenv("TAG_BATCH_SIZE", "15" if LLM_PROVIDER == "gemini" else "1"))

# Claude models (only used when LLM_PROVIDER=anthropic)
TAG_MODEL = os.getenv("TAG_MODEL", "claude-haiku-5-5")
SYNTH_MODEL = os.getenv("SYNTH_MODEL", "claude-sonnet-5-5")
ANTHROPIC_MODEL = SYNTH_MODEL  # kept for older imports

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY", "")
REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID", "")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET", "")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")

PLAY_APP_ID = "com.nextbillion.groww"   # verified
APPSTORE_APP_ID = "1404871703"          # verified: Groww Stocks, Mutual Fund, IPO
# Put your downloaded Play Store export here (columns: reviewId, content, score, at, ...)
PLAY_LOCAL_CSV = os.path.join(DATA_DIR, "groww_reviews_last5y.csv")

SUBREDDITS = ["IndiaInvestments", "mutualfunds", "MutualfundsIndia", "personalfinanceindia",
              "IndianStreetBets", "FIRE_Ind"]
REDDIT_QUERIES = ["stop SIP", "pause SIP", "SIP negative", "skip SIP", "first SIP",
                  "SIP not performing", "cancel SIP", "SIP red", "continue SIP", "groww SIP"]

# Leave empty to auto-search YouTube with YOUTUBE_SEARCH_QUERIES (uses API quota).
YOUTUBE_VIDEO_IDS = []
YOUTUBE_SEARCH_QUERIES = ["should I stop my SIP", "SIP negative returns", "SIP band karu ya nahi",
                          "first SIP mistakes", "SIP loss kya kare", "SIP pause or stop"]
YOUTUBE_VIDEOS_PER_QUERY = 3

TRADINGQNA_QUERIES = ["SIP stop", "SIP pause", "SIP negative returns", "first SIP",
                      "groww SIP", "SIP mandate", "skip SIP"]

# Keyword pre-filter (word boundaries, so "gossip" or "navigation" don't match).
# STRONG terms are SIP/MF specific. WEAK terms only count if a STRONG term is also present.
STRONG_RX = re.compile(r"\b(?:sips?|mutual ?funds?|mf|auto ?pay|e-?mandates?|mandates?|"
                       r"instal+ments?|xirr|elss|index ?funds?)\b", re.I)
WEAK_RX = re.compile(r"\b(?:nav|skip+ed|skip|pause[d]?|redeem|redemption|stop+ed|stop|"
                     r"cancel+ed|cancel|band|returns?)\b", re.I)
MIN_WORDS = 6   # drop "good sip app" style one-liners
