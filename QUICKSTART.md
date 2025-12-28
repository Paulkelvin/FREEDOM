# Quick Start: Professional Arbitrage & Value Betting

## 🎯 What's New in This Version?

You now have **3 ways to make money**:

### 1. Traditional Arbitrage (Risk-Free)
- Bet both sides on different bookies
- Guaranteed profit regardless of outcome
- Look for: **[⭐ HIGH CONFIDENCE]** tags (Sharp vs Soft)

### 2. Value Betting (Single-Side Bet)
- Bet ONE side when Soft bookie lags behind Sharp pricing
- Higher risk but bigger potential profit
- Look for: **💎 VALUE BET** alerts

### 3. Fast Move Arbs (Quick Action)
- Both bookies are slow, temporary pricing lag
- 2-3 minute window before gap closes
- Look for: **[⚡ FAST MOVE]** tags

---

## 🚀 5-Minute Setup

### 1. Install & Configure
```powershell
pip install -r requirements.txt
Copy-Item .env.example .env
notepad .env  # Add API key and Discord webhook
```

### 2. Choose Your Mode

**Option A: Manual Scans Only (Recommended for Free Tier)**
- No automatic polling (saves credits)
- Trigger scans during live games with `/scan_now`
- 15 scans/month = 450 credits

**Option B: Peak Hours Only**
Edit `config/settings.py`:
```python
PEAK_HOURS_SCHEDULE = {
    'basketball_nba': [
        {'days': [4, 5], 'start_hour': 19, 'end_hour': 23},  # Fri/Sat only
    ],
    'tennis_atp': [],  # Disable for now
}
```

### 3. Test Run
```powershell
python main.py --dry-run
```

Watch for alerts in terminal. When you see opportunities, verify in your betting apps.

---

## 📊 Understanding Alert Tags

### ⭐ HIGH CONFIDENCE (Best ROI)
- **What**: Pinnacle/Betfair (accurate) vs 1xBet/Unibet (slow)
- **Why It's Safe**: Sharp bookmaker is always right, Soft will follow
- **Action**: Bet immediately, gap lasts ~5-10 minutes
- **Example**: Pinnacle Lakers 1.75 vs 1xBet Lakers 2.05

### ⚡ FAST MOVE (Time-Sensitive)
- **What**: 1xBet vs Unibet (both slow movers)
- **Why It Happens**: Both lag behind market, temporary desync
- **Action**: Bet within 2-3 minutes or gap closes
- **Example**: Unibet 2.05 vs William Hill 2.10

### 💎 VALUE BET (Not Arbitrage)
- **What**: Sharp drops, Soft stays high
- **Risk**: You're betting the Sharp is right (not guaranteed)
- **Reward**: Higher profit than arbitrage (5-15%)
- **Example**: Pinnacle drops to 1.70, 1xBet still 1.90 → Bet 1xBet @ 1.90

---

## 🎯 Recommended Sports (2-Way Markets)

| Sport | Why Good | Best Markets |
|-------|----------|--------------|
| **Basketball (NBA)** | High scoring = frequent pricing gaps | Moneyline, Totals |
| **Tennis (ATP/WTA)** | No draws, 24/7 global coverage | Match Winner |

**Avoid Soccer for now**: 3-way markets (Win/Draw/Loss) split profit too thin.

---

## 💰 Manual Scan Strategy (Best for Free Tier)

### When to Trigger Scans

**Basketball**:
- 15 minutes before tip-off (lineup announcements)
- Live: Every 5 minutes during close games (last 5 minutes)

**Tennis**:
- Between sets (bookies adjust slowly)
- After momentum shifts (break of serve)

### Discord Commands
```
/scan_now       → All sports (30 credits)
/scan_nba       → NBA only (15 credits)
/scan_tennis    → Tennis only (15 credits)
```

### Monthly Budget
- **15 full scans** = 450 credits
- **Reserve 50 credits** for off-peak monitoring
- **Total**: Fits 500/month free tier ✅

---

## 📖 Paper Trading Protocol (Week 1)

**DO NOT BET REAL MONEY YET**

1. Run `python main.py --dry-run`
2. When alert arrives, open both betting apps
3. Check if odds still match
4. Log result:
   - ✓ **Win**: Odds matched, would have profited
   - ✗ **Loss**: Odds changed before you could bet

5. After **10 successful paper trades**, go live

### Paper Trade Tracker
```
Day 1: ✓✓✗ (2/3 would have won)
Day 2: ✓✓✓✓ (4/4 would have won)
Day 3: ✓✓✓ (3/3 would have won)
Total: 9/10 ✅ → READY FOR REAL BETS
```

---

## ⚠️ Critical Safety Rules

### Before EVERY Bet
1. ✓ Odds match the alert (open both apps to verify)
2. ✓ Both bookies settle same way (Overtime? 90 min?)
3. ✓ ROI between 1.5% and 15% (not palpable error)
4. ✓ You can place both bets simultaneously

### RED FLAGS (DO NOT BET)
- ❌ ROI > 15% (likely typo, will void)
- ❌ Odds changed significantly from alert
- ❌ 🔴 RED HEADER in Discord (rule mismatch)
- ❌ Can't verify both bookies' settlement terms

---

## 🧠 Pro Tips from Adviser

### On Sharp Bookmakers
> "Pinnacle never bans arbitrageurs. If you find a gap between Pinnacle and a local bookie, Pinnacle is always right. Bet on the other side."

### On Value Betting
> "Value Betting is often more profitable than arbitrage because you catch the move before the gap even officially opens."

### On Soft Bookmakers
> "1xBet and Unibet cover thousands of games (especially Tennis and niche Basketball leagues) and often forget to update their odds for 2-3 minutes after a major point or injury."

### On Speed
> "Soft vs Soft arbs close in 2-3 minutes. Sharp vs Soft arbs last longer because the Soft bookie doesn't track Sharps in real-time."

---

## 📞 Next Steps

1. **Read** [ADVANCED_FEATURES.md](ADVANCED_FEATURES.md) for full strategy guide
2. **Configure** your peak hours or manual-only mode
3. **Paper trade** for 10 successful bets
4. **Go live** with small stakes ($10-50 per arb)
5. **Scale up** once profitable for 1 month

---

**Built for winners. Stay sharp. 💎**
