# Setup Instructions

## Prerequisites

1. **Python 3.8+** installed
2. **The Odds API Key** (free tier: https://the-odds-api.com)
3. **Discord Webhook URL** (optional for alerts)

---

## Quick Setup (5 Minutes)

### 1. Install Dependencies
```powershell
pip install -r requirements.txt
```

### 2. Configure Environment Variables
```powershell
# Copy the example file
Copy-Item .env.example .env

# Edit with your credentials
notepad .env
```

**Required in `.env`**:
```env
ODDS_API_KEY=your_api_key_here
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/your_webhook_url
```

**Get API Key**:
- Go to https://the-odds-api.com
- Sign up (free tier: 500 requests/month)
- Copy your API key from dashboard

**Get Discord Webhook** (optional but recommended):
- Open Discord server → Server Settings → Integrations → Webhooks
- Click "New Webhook"
- Copy webhook URL

### 3. Test Run (Dry Mode)
```powershell
python main.py --dry-run
```

This will:
- ✅ Validate API connection
- ✅ Show opportunities in console (no Discord alerts)
- ✅ Log to `arbitrage_monitor.log`

### 4. Go Live
```powershell
python main.py
```

---

## Configuration Tips

### For Testing (500 Free Credits)
Edit `config/settings.py`:

```python
# Option 1: Manual scans only (best for testing)
# Don't run main.py continuously, just trigger scans when needed

# Option 2: Minimal peak hours
PEAK_HOURS_SCHEDULE = {
    'basketball_nba': [
        {'days': [5], 'start_hour': 19, 'end_hour': 22},  # Saturday only
    ],
    'tennis_atp': [],  # Disable
}
```

### Sports Selection
```python
SPORTS = ['basketball_nba']  # Start with one sport
# SPORTS = ['tennis_atp']     # Or tennis
```

---

## Expected Output

### Console
```
🚀 SPORTS ARBITRAGE MONITOR STARTED
Sports: basketball_nba
Peak Hours Polling: 60s

🔄 PEAK HOURS - Starting scan at 19:32:15
📊 Fetched 12 events for basketball_nba
🚨 ARB DETECTED: Lakers vs Warriors | ROI: 3.42%
✅ Cycle complete: 1 opportunities found in 8.3s
```

### Discord (if webhook configured)
```
⭐ [HIGH CONFIDENCE] ARB FOUND (3.4% Profit)
🏀 Lakers vs Warriors
...
```

---

## Troubleshooting

### "Invalid API Key"
- Check `.env` has correct `ODDS_API_KEY`
- Verify at https://the-odds-api.com/account

### "No opportunities found"
- Normal! Arbitrage is rare (expect 0-5 per day)
- Try lowering `MIN_ROI_THRESHOLD = 0.5` in `config/settings.py`

### "Module not found"
```powershell
pip install --upgrade pip
pip install -r requirements.txt
```

---

## What to Expect

### First Run
- API will fetch current odds
- Most events will be filtered out (normal)
- You may see 0 opportunities (arbitrage is rare)

### During Peak Hours
- More events = higher chance of finding gaps
- Watch for [⭐ HIGH CONFIDENCE] tags

### Manual Scans
- Use `/scan_now` in Discord for on-demand bursts
- Costs 30 credits per 5-minute scan

---

## Next Steps

1. **Paper Trade**: Run `--dry-run` for 10 successful alerts
2. **Read Guides**: 
   - [QUICKSTART.md](QUICKSTART.md) - Betting strategy
   - [ADVANCED_FEATURES.md](ADVANCED_FEATURES.md) - Pro tips
3. **Adjust Settings**: Fine-tune peak hours and thresholds
4. **Go Live**: Start with small stakes ($10-20)

---

**Ready to find arbitrage opportunities! 🚀**
