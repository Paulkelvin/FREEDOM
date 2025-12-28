"""
Configuration settings for Sports Arbitrage Monitoring System
"""
import os
from dotenv import load_dotenv

load_dotenv()

# ===========================
# API CONFIGURATION
# ===========================
ODDS_API_KEY = os.getenv('ODDS_API_KEY', 'YOUR_API_KEY_HERE')
ODDS_API_BASE_URL = 'https://api.the-odds-api.com/v4'

# API Request Parameters
REGIONS = ['eu', 'us']  # Global bookmakers (Unibet, William Hill, Betfair, 1xBet)
SPORTS = ['basketball_nba', 'tennis_atp']  # Focus on 2-way markets (no draws)
MARKETS = ['h2h']  # Head-to-head (moneyline/match winner)
ODDS_FORMAT = 'decimal'

# ===========================
# BOOKMAKER PRIORITIZATION (Sharp vs Soft)
# ===========================
# Group A: "The Sharps" - Market leaders with most accurate pricing
SHARP_BOOKMAKERS = [
    'pinnacle',      # The smartest - never bans arbitrageurs
    'betfair',       # Exchange - real human pricing
    'bet365',        # Market leader
]

# Group B: "The Softs" - Often slow to update, best arb targets
SOFT_BOOKMAKERS = [
    '1xbet',         # Slow mover, covers niche leagues
    'unibet',        # Pricing lags on minor markets
    'williamhill',   # Traditional bookie, slower updates
    'marathonbet',   # Good coverage, delayed adjustments
]

# Priority Logic:
# - Sharp vs Soft = [⭐ HIGH CONFIDENCE] tag
# - Soft vs Soft = [⚡ FAST MOVE] tag (temporary pricing lag)

# Rate Limiting (Free tier: 500 requests/month)
# Sniper Window Strategy: Only poll during high-volume hours to save API credits
POLL_INTERVAL_SECONDS = 60  # During peak hours (fast polling)
OFF_PEAK_POLL_INTERVAL = 1800  # 30 minutes during off-peak hours
MAX_MONTHLY_REQUESTS = 500
REQUEST_RETRY_DELAY = 300  # 5 minutes on API failure

# Peak Hours Schedule (when arbitrage opportunities are most common)
PEAK_HOURS_SCHEDULE = {
    'basketball_nba': [
        # NBA games typically 7 PM - 11 PM ET (convert to your timezone)
        {'days': [0, 1, 2, 3, 4, 5, 6], 'start_hour': 18, 'end_hour': 23},  # 6 PM - 11 PM daily
    ],
    'tennis_atp': [
        # Tennis: Global tournaments (adjust to major events)
        {'days': [0, 1, 2, 3, 4, 5, 6], 'start_hour': 9, 'end_hour': 20},  # 9 AM - 8 PM daily
    ],
}

# Manual Scan Configuration (Discord /scan_now command)
MANUAL_SCAN_DURATION = 300  # 5 minutes (300 seconds)
MANUAL_SCAN_INTERVAL = 10   # Poll every 10 seconds during manual burst
# Cost: 300s / 10s = 30 requests per manual scan

# ===========================
# ARBITRAGE FILTERS (SAFETY)
# ===========================
# The "Palpable Error" Filter: Reject suspiciously high ROI (likely pricing errors)
MAX_ROI_THRESHOLD = 15.0  # % - Discard arbs above this (e.g., 20% profit = void risk)

# The "Minimum Profit" Filter: Only alert if profitable after fees
MIN_ROI_THRESHOLD = 1.5  # % - Cover transfer fees and data costs

# The "Trap" Filter: Bookmaker rule mismatch warnings
BOOKMAKER_OVERTIME_RULES = {
    # Basketball - NBA (ALMOST ALL include overtime in moneyline)
    'PointsBet': 'includes_overtime',
    'DraftKings': 'includes_overtime',
    'FanDuel': 'includes_overtime',
    'BetMGM': 'includes_overtime',
    'Caesars': 'includes_overtime',
    'Unibet': 'includes_overtime',
    'William Hill': 'includes_overtime',
    '1xBet': 'includes_overtime',
    'Pinnacle': 'includes_overtime',
    'Kwiff': 'regulation_only',  # Known outlier - RED FLAG
    
    # Soccer - EPL (ALMOST ALL are 90 minutes + injury time, NO extra time)
    'Betfair': 'regulation_only',
    'Bet365': 'regulation_only',
    'Ladbrokes': 'regulation_only',
    'William Hill': 'regulation_only',
    'Unibet': 'regulation_only',
    '1xBet': 'regulation_only',
    'Pinnacle': 'regulation_only',
}

# Bookmakers with unusual/non-standard rules (ALWAYS FLAG)
HIGH_RISK_BOOKMAKERS = ['Kwiff', 'InternationalBookieX']

# Bookmaker combinations that may have rule conflicts (now dynamically detected)
HIGH_RISK_COMBINATIONS = []  # Deprecated - RiskReporter handles this

# ===========================
# BETTING PARAMETERS
# ===========================
DEFAULT_TOTAL_INVESTMENT = 1000  # $ - Total capital per arbitrage opportunity

# Smart Rounding (Anti-Detection): Stakes rounded to look human
# > $1000: Round to nearest $100
# > $100: Round to nearest $50
# < $100: Round to nearest $5
ENABLE_SMART_ROUNDING = True

# ===========================
# DISCORD NOTIFICATIONS
# ===========================
DISCORD_WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK_URL', '')
ALERT_COOLDOWN_MINUTES = 10  # Prevent duplicate alerts for same event

# ===========================
# LOGGING
# ===========================
LOG_LEVEL = 'INFO'
LOG_FILE = 'arbitrage_monitor.log'

# ===========================
# ADVANCED FEATURES
# ===========================
# Drift Tracker: Alert if odds change rapidly (pre-arb detection)
ENABLE_DRIFT_TRACKER = True
DRIFT_THRESHOLD_PERCENT = 5.0  # Alert if odds drop >5% in one poll

# Value Betting Mode: Track Sharp bookmaker movements
DRIFT_SHARP_BOOKMAKERS = ['pinnacle', 'betfair']  # "Source of truth" bookmakers
DRIFT_VALUE_THRESHOLD = 5.0  # Alert if Soft bookie is >5% higher than Sharp price

# Multi-Market Scanner: Check over/under in addition to h2h
ENABLE_MULTIMARKET_SCAN = False  # Set to True to scan totals/spreads
MULTIMARKET_MARKETS = ['h2h', 'totals']

# Risk Reporter: Deep check for rule mismatches
ENABLE_RISK_REPORTER = True
