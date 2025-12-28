# Sports Arbitrage Monitoring System

A production-ready Python application that continuously monitors NBA and EPL odds from The Odds API, detects profitable arbitrage opportunities using advanced safety filters, and sends mobile-optimized alerts to Discord.

## 🎯 Features

### Core Functionality
- **Real-time Odds Monitoring**: Tracks NBA (basketball_nba) and Tennis ATP (tennis_atp) - 2-way markets for cleaner arbitrage
- **Sharp vs Soft Classification**: Prioritizes opportunities between market leaders (Pinnacle, Betfair) and slow movers (1xBet, Unibet)
- **Peak Hours Scheduling**: "Sniper Window" strategy - only polls during high-volume hours to conserve API credits
- **Manual Scan Trigger**: `/scan_now` Discord command for on-demand 5-minute burst scanning (30 credits per scan)
- **Arbitrage Detection**: Implements standard formula `Implied% = (1/OddsA) + (1/OddsB)` with guaranteed profit calculation
- **Optimal Stake Distribution**: Calculates precise bet amounts with smart rounding (anti-detection)

### Safety Filters (Critical Risk Management)
1. **The "Palpable Error" Filter**: Automatically rejects ROI > 15% (likely bookmaker pricing errors that will void)
2. **The "Minimum Profit" Filter**: Only alerts for ROI > 1.5% (covers transfer fees and costs)
3. **The "Trap" Filter**: Validates bookmaker settlement rules (Overtime/90-min handling) with 🔴 RED HEADER alerts for mismatches

### Advanced Monitoring
- **Drift Tracker with Value Betting**: Detects when Sharp bookmakers (Pinnacle) drop but Soft stays high - catch profit before arb forms
- **Priority Alert Tags**: 
  - [⭐ HIGH CONFIDENCE] = Sharp vs Soft (highest probability)
  - [⚡ FAST MOVE] = Soft vs Soft (2-3 min window)
  - [🔹 SHARP ARB] = Sharp vs Sharp (rare, act fast)
- **Multi-Market Scanner**: Cross-checks Winner, Over/Under, and Spread markets
- **Risk Reporter**: Enhanced risk_check() with high-risk bookmaker flagging (e.g., Kwiff, non-standard rules)
- **Smart Stake Rounding**: >$1000→$100 increments, >$100→$50, <$100→$5 (looks human)

### Mobile-Optimized Discord Alerts
Formatted for phone screens with emoji indicators, smart-rounded stakes, priority tags, 🔴 RED HEADER for rule mismatches, and pro betting recommendations.

---

## 📁 Project Structure

```
FREEDOM/
├── config/
│   └── settings.py          # Configuration (API keys, thresholds, filters)
├── src/
│   ├── api/
│   │   └── odds_client.py   # The Odds API wrapper with rate limiting
│   ├── calculators/
│   │   └── arbitrage.py     # Arbitrage detection (2-way + 3-way markets)
│   ├── notifiers/
│   │   └── discord_webhook.py  # Alerts with priority tags & value bets
│   └── utils/
│       ├── logger.py        # Structured logging
│       ├── peak_scheduler.py # Peak hours "Sniper Window" scheduler
│       ├── discord_commands.py # NEW: Manual scan trigger (/scan_now)
│       ├── bookmaker_classifier.py # NEW: Sharp vs Soft classification
│       └── advanced_monitors.py  # Drift/Value Betting/Risk modules
├── main.py                  # Application entry point
├── README.md               # This file
├── CHANGELOG.md            # Peak hours & safety updates
└── ADVANCED_FEATURES.md    # NEW: Sharp/Soft strategy & value betting guiddependencies
├── .env.example            # Environment variable template
└── README.md               # This file
```

---

## 🚀 Quick Start

### 1. Install Dependencies
```powershell
# Create virtual environment (recommended)
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install packages
pip install -r requirements.txt
```

### 2. Configure API & Discord
```powershell
# Copy example environment file
Copy-Item .env.example .env

# Edit .env with your credentials
notepad .env
```

Add your credentials:
```env
ODDS_API_KEY=your_api_key_from_the-odds-api.com
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/your_webhook_url
```

**Get The Odds API Key**: 
1. Go to https://the-odds-api.com
2. Sign up for free tier (500 requests/month)
3. Copy your API key

**Get Discord Webhook**:
1. Open your Discord server
2. Server Settings → Integrations → Webhooks
3. Create "New Webhook" for your alerts channel
4. Copy webhook URL

### 3. Run the Application

**Paper Trading Mode (Recommended First)**:
```powershell
# Test without sending real alerts (10-bet validation phase)
python main.py --dry-run
```

**Production Mode**:
```powershell
# Live monitoring with Discord alerts
python main.py
```

---

## ⚠️ CRITICAL: API Rate Management

**Your adviser is correct**: 60s polling 24/7 kills free tier credits in hours.

**The app now uses "Sniper Window" strategy**:
- ✅ **Peak Hours**: 60s polling only during high-volume times (6-11 PM NBA, Sat mornings EPL)
- ✅ **Off-Peak**: 30-min polling (maintenance mode)
- ⚠️ **Current default schedule still exceeds 500/month**

**Action Required**: Edit [config/settings.py](config/settings.py#L18-L27) to limit peak hours:

```python
# RECOMMENDED: Only monitor 1 sport on weekends (fits free tier)
PEAK_HOURS_SCHEDULE = {
    'basketball_nba': [
        {'days': [4, 5], 'start_hour': 19, 'end_hour': 23},  # Fri/Sat 7-11 PM
    ],
    'soccer_epl': [
        {'days': [5], 'start_hour': 10, 'end_hour': 14},  # Sat 10 AM-2 PM
    ],
}
# This = ~20 hours/week × 60 req/hr = 1,200/week ❌ STILL HIGH

# BEST PRACTICE for 500 credits/month:
PEAK_HOURS_SCHEDULE = {
    'soccer_epl': [
        {'days': [5], 'start_hour': 11, 'end_hour': 14},  # Sat 11 AM-2 PM = 3 hrs
    ],
}
# 3 hrs × 60 req/hr × 4 weeks = 720/month ✅ (with buffer)
```

---

## ⚙️ Configuration

### Key Settings in `config/settings.py`

```python- Sniper Window Strategy
POLL_INTERVAL_SECONDS = 60  # Fast polling during peak hours
OFF_PEAK_POLL_INTERVAL = 1800  # 30 min during off-peak (saves credits)

# Peak Hours Schedule (only poll when money moves)
PEAK_HOURS_SCHEDULE = {
    'basketball_nba': [
        {'days': [0,1,2,3,4,5,6], 'start_hour': 18, 'end_hour': 23},  # 6-11 PM daily
    ],
    'soccer_epl': [
        {'days': [5,6], 'start_hour': 7, 'end_hour': 13},  # Sat/Sun 7 AM-1 PM
        {'days': [1,2,3], 'start_hour': 19, 'end_hour': 22},  # Tue/Wed/Thu 7-10 PM
    ],
}

# Safety Filters
MAX_ROI_THRESHOLD = 15.0    # Reject suspiciously high ROI (void risk)
MIN_ROI_THRESHOLD = 1.5     # Minimum profit to cover fees

**Sniper Window Strategy**: The app now uses peak hours scheduling to conserve API credits.

| Mode | Frequency | API Usage | Coverage |
|------|-----------|-----------|----------|
| **Peak Hours** | 60s polling | ~300 req/day during windows | High (when arbs actually happen) |
| **Off-Peak** | 30 min polling | ~48 req/day | Low (maintenance mode) |
| **Total** | Combined | ~350 req/day = **~10,500/month** | ❌ **Still exceeds free tier** |

**Solution**: Adjust peak hours in `config/settings.py` to limit total daily windows:
```python
### Safe Arbitrage (Normal)
```
🚨 SAFE ARB FOUND (3.4% Profit)
⚽ Chelsea vs. Man Utd

🟩 BET 1: Back Chelsea @ 2.10
🏦 Bookie: William Hill
💵 Stake: $485

🟦 BET 2: Back Man Utd @ 2.05
🏦 Bookie: Unibet
💵 Stake: $515

⚠️ Total Risk: $1,000 | Guaranteed Profit: $34

Risk Check: ✅ Rules Match: Both settle at 90 Mins + Injury Time
```

### High-Risk Rule Mismatch
```
🔴 RULE MISMATCH: CHECK TERMS BEFORE BETTING!
🚨 ARB FOUND (4.2% Profit) - HIGH RISK
🏀 Lakers vs Warriors

🟩 BET 1: Back Lakers @ 1.95
🏦 Bookie: Kwiff
💵 Stake: $550

🟦 BET 2: Back Warriors @ 2.15
🏦 Bookie: DraftKings
💵 Stake: $450

⚠️ Total Risk: $1,000 | Guaranteed Profit: $42

Risk Check: 🔴 HIGH RISK: Kwiff has non-standard basketball_moneyline rules - VERIFY MANUALLY

⚠️ BASKETBALL NOTICE: Verify both bookies settle on SAME rules (including Overtime)
## 📱 Discord Alert Format

```
🚨 SAFE ARB FOUND (3.4% Profit)
⚽ Chelsea vs. Man Utd

🟩 BET 1: Back Chelsea @ 2.10
🏦 Bookie: William Hill
💵 Stake: $485 (Round to nearest 5)

🟦 BET 2: Back Man Utd/Draw @ 2.05
🏦 Bookie: Unibet
💵 Stake: $515 (Round to nearest 5)

⚠️ Total Risk: $1,000 | Guaranteed Profit: $34

⚠️ SOCCER NOTICE: Most bookies settle on 90 min + injury time (NO extra time)
   → Confirm both William Hill & Unibet use same settlement

✓ Check William Hill terms: Does bet include overtime/extra time?
✓ Check Unibet terms: Does bet include overtime/extra time?
✓ Paper trade first: Open both apps, verify odds match alert
```

---

## 🧪 Paper Trading Protocol

**CRITICAL**: Do NOT place real bets until you've validated 10 successful paper trades.

1. **Run in dry-run mode**: `python main.py --dry-run`
2. **When alert arrives**: Open both betting apps
3. **Verify odds match**: Check if the odds in the alert are still available
4. **Log the result**: Record if you would have won/lost
5. **Repeat 10 times**: If 10/10 would have been profitable, system is ready

### Paper Trade Tracking Template
```
Trade #1: ✓ Odds matched, would have won $X
Trade #2: ✗ Odds changed before I could bet
Trade #3: ✓ Odds matched, would have won $X
...
```

---

## 🛡️ Safety Protocol

### Before Each Bet
1. **Verify odds are current**: Open both bookmaker apps, confirm odds match alert
2. **Check settlement rules**: 
   - Basketball: Do both include Overtime?
   - Soccer: Do both settle at 90 min + injury time?
3. **Confirm account limits**: Ensure both accounts can handle the stake
4. **Place bets simultaneously**: Minimize odds movement risk

### Red Flags (DO NOT BET)
- ❌ ROI > 15% (palpable error - will likely void)
- ❌ Odds changed significantly from alert
- ❌ Can't verify both bookmakers use same rules
- ❌ One bookmaker is unresponsive/app crashing

---

## 📊 Monitoring & Logs

Logs are written to:
- **Console**: Real-time monitoring output
- **arbitrage_monitor.log**: Detailed file log for review

Key log patterns:
```
✅ Cycle complete: 2 opportunities found in 8.3s
🚨 ARB DETECTED: Lakers vs Warriors | ROI: 3.42% | Bookmakers: Unibet vs DraftKings
⚠️ RISK ALERT: RULE_MISMATCH (includes_overtime vs regulation_only)
📊 API Quota: 156 used | 344 remaining
```

---

## 🔧 Troubleshooting

### "Invalid API Key"
- Check `.env` file has correct `ODDS_API_KEY`
- Verify key is active at https://the-odds-api.com/account

### "Discord webhook failed"
- Confirm `DISCORD_WEBHOOK_URL` in `.env` is correct
- Test webhook: `curl -X POST <your_url> -d "content=Test"`

### "No opportunities found"
- This is **normal with peak hours scheduling** - arbitrage is rare
- During off-peak, you'll see: `⏸️ Off-peak hours. Sleeping...`
- During peak, expect 1-5 opportunities per week (not per day)
- Try lowering `MIN_ROI_THRESHOLD` to 0.5% for testing
- Check logs for filtered opportunities (PALPABLE_ERROR, LOW_PROFIT, RULE_MISMATCH)

### "API quota exceeded"
- **Root Cause**: Peak hours schedule still exceeds 500 req/month
- **Fix**: Reduce peak hours windows in [config/settings.py](config/settings.py)
  ```python
  # Example: Only Fri/Sat = ~240 req/week = 960/month (still high)
  # Better: Only Saturdays 4 hours = ~60 req/week = 240/month ✅
  PEAK_HOURS_SCHEDULE = {
      'basketball_nba': [],  # Disable if not main focus
      'soccer_epl': [
          {'days': [5], 'start_hour': 10, 'end_hour': 14},  # Sat 10AM-2PM only
      ],
  }
  ```
- Check `x-requests-used` in logs to monitor quota

---

## 🎓 How It Works

### Arbitrage Formula
```python
Implied Probability = (1 / Odds_A) + (1 / Odds_B)

If Implied < 1.0:
    ROI = ((1 / Implied) - 1) × 100%
    
Example:
    Odds_A = 2.10 (William Hill, Chelsea)
    Odds_B = 2.05 (Unibet, Man Utd)
    
    Implied = (1/2.10) + (1/2.05) = 0.9646
    ROI = (1/0.9646 - 1) × 100 = 3.67%
```

### Stake Distribution
```python
Stake_A = (Total × (1/Odds_A)) / ((1/Odds_A) + (1/Odds_B))
Stake_B = Total - Stake_A

Example ($1000 total):
    Stake_A = ($1000 × 0.476) / 0.965 = $493
    Stake_B = $1000 - $493 = $507
    
Payout (either outcome):
    Win A: $493 × 2.10 = $1035
    Win B: $507 × 2.05 = $1039
    Profit: ~$35-39 guaranteed
```

---

## 🌍 Regional Considerations

### Bookmaker Availability
This app scans **EU + US** regions. Adjust `config/settings.py` for your location:

```python
# For African markets (add 'africa' if API supports)
REGIONS = ['eu', 'us']  # 1xBet, Pinnacle often available

# For Asian markets
REGIONS = ['eu', 'asia']
```

### Currency
The app displays USD ($). For other currencies:
- Alerts show **ratios/percentages** (universal)
- Adjust `DEFAULT_TOTAL_INVESTMENT` to your currency (e.g., ₦500,000)

---

## 🤝 Support & Extensions

### Extending the System

**Add more sports**:
```python
# config/settings.py
SPORTS = ['basketball_nba', 'soccer_epl', 'tennis_atp', 'icehockey_nhl']
```

**Add more markets**:
```python
ENABLE_MULTIMARKET_SCAN = True
MULTIMARKET_MARKETS = ['h2h', 'totals', 'spreads']
```

**Custom bookmaker rules**:
```python
BOOKMAKER_OVERTIME_RULES = {
    'YourBookie': 'includes_overtime',  # or 'regulation_only'
}
```

### Community
- **Issues**: Report bugs or feature requests on GitHub
- **Contributions**: Pull requests welcome for new features

---

## ⚖️ Legal & Disclaimer

**This software is for educational purposes only.**

- **Not financial advice**: Always do your own research
- **Regional laws**: Ensure sports betting is legal in your jurisdiction
- **Bookmaker terms**: Read and comply with all bookmaker policies
- **Risk**: No guarantee of profit - markets can change instantly
- **Responsibility**: Use at your own risk

The developers are not responsible for any financial losses.

---

## 📜 License

MIT License - See LICENSE file for details

---

## 🙏 Credits

- **The Odds API**: https://the-odds-api.com
- **Discord**: https://discord.com
- **Python Community**: For excellent libraries

---

**Built with 💚 by a Senior Quantitative Developer**

*"In arbitrage, the devil is in the details - verify everything twice, bet once."*
