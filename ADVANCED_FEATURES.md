# Advanced Features Update - December 28, 2025

## 🎯 Professional Betting Strategy Implementation

This update transforms the arbitrage monitor from a basic scanner into a professional-grade betting tool with Sharp vs Soft bookmaker intelligence and value betting capabilities.

---

## 1. BOOKMAKER PRIORITIZATION (Sharp vs Soft)

### Concept
Professional bettors know that not all bookmakers are equal:
- **Sharp Bookmakers**: Market leaders with the most accurate pricing (Pinnacle, Betfair, Bet365)
- **Soft Bookmakers**: Often slow to update prices (1xBet, Unibet, William Hill, MarathonBet)

### Implementation
**File**: [config/settings.py](config/settings.py#L22-L42)

```python
SHARP_BOOKMAKERS = ['pinnacle', 'betfair', 'bet365']
SOFT_BOOKMAKERS = ['1xbet', 'unibet', 'williamhill', 'marathonbet']
```

### Priority Logic
- **Sharp vs Soft** = [⭐ HIGH CONFIDENCE] tag
  - "Pinnacle (1.75) vs 1xBet (2.10)" = Bet on 1xBet side, Pinnacle is always right
- **Soft vs Soft** = [⚡ FAST MOVE] tag  
  - "Unibet (2.05) vs William Hill (2.10)" = Temporary pricing lag, act fast
- **Sharp vs Sharp** = [🔹 SHARP ARB] tag
  - Rare but valid, both accurate so move quickly

---

## 2. DISCORD ALERT PRIORITY TAGGING

### Alert Examples

#### High Confidence (Sharp vs Soft)
```
⭐ [HIGH CONFIDENCE] ARB FOUND (3.8% Profit)
🏀 Lakers vs Warriors

🟩 BET 1: Back Lakers @ 2.10
🏦 Bookie: 1xBet
💵 Stake: $520

🟦 BET 2: Back Warriors @ 2.05
🏦 Bookie: Pinnacle
💵 Stake: $480

⚠️ Total Risk: $1,000 | Guaranteed Profit: $38

Why HIGH CONFIDENCE? Sharp bookmaker vs Soft bookmaker - High probability profit

💡 Pro Tip: Pinnacle is a Sharp bookmaker. Their price is the market consensus. Bet the opposite side.
```

#### Fast Move (Soft vs Soft)
```
⚡ [FAST MOVE] ARB FOUND (2.4% Profit)
🎾 Djokovic vs Nadal

Why FAST MOVE? Both bookmakers are slow movers - Temporary pricing lag

⏱️ Time Sensitive: Both bookmakers are slow movers. This gap may close within 2-3 minutes.
```

**Implementation**: [src/utils/bookmaker_classifier.py](src/utils/bookmaker_classifier.py)

---

## 3. MANUAL SCAN TRIGGER (/scan_now)

### Problem
24/7 polling burns through API credits. You need on-demand scanning for live events.

### Solution: Discord Command Handler
**File**: [src/utils/discord_commands.py](src/utils/discord_commands.py)

### Commands
- `/scan_now` or `/scan` - Scan all sports
- `/scan_nba` - NBA only
- `/scan_tennis` - Tennis only

### How It Works
1. User sends `/scan_now` in Discord
2. Bot runs **30 polls** (10-second intervals) for 5 minutes
3. Sends completion report with credits used

### Cost
- **Duration**: 5 minutes (300 seconds)
- **Interval**: 10 seconds
- **Credits Used**: 30 requests per scan
- **Monthly Budget**: 15 manual scans/month on free tier

### Integration Notes
For full Discord bot integration, install `discord.py`:
```python
@bot.slash_command(name="scan_now", description="Trigger immediate arbitrage scan")
async def scan_now(ctx):
    result = scan_handler.trigger_manual_scan()
    await ctx.respond(result['message'])
```

Current implementation uses webhook-based message parsing (lightweight demo).

---

## 4. VALUE BETTING MODE (Enhanced Drift Tracker)

### Concept
**"Value Betting is often more profitable than arbitrage because you catch the move before the gap even officially opens."**

### How It Works
1. **Track Sharp bookmakers** (Pinnacle, Betfair) as "source of truth"
2. **Detect when Sharp drops** (e.g., Lakers 1.90 → 1.80 → 1.70)
3. **Alert if Soft stays high** (e.g., 1xBet still at 1.90)
4. **Recommendation**: Bet Lakers @ 1.90 on 1xBet (the Sharp is right, Soft will follow)

### Example Alert
```
💎 VALUE BET DETECTED

Outcome: Lakers
Event: lakers_vs_warriors_2025

🟢 Soft Bookie: 1xbet @ 1.90
🔵 Sharp Consensus: pinnacle @ 1.70
📊 Value Edge: +11.8%

💡 Recommendation:
Bet Lakers @ 1.90 on 1xbet. Sharp consensus is 1.70, 
giving you 11.8% value edge.

This is NOT arbitrage - you're betting on the Sharp bookmaker 
being right. The Soft bookie will likely adjust their price down soon.
```

### Configuration
[config/settings.py](config/settings.py#L139-L141):
```python
DRIFT_SHARP_BOOKMAKERS = ['pinnacle', 'betfair']
DRIFT_VALUE_THRESHOLD = 5.0  # Alert if Soft is >5% higher
```

### Implementation
[src/utils/advanced_monitors.py](src/utils/advanced_monitors.py) - `track_value_opportunity()` method

---

## 5. MULTI-OUTCOME FLEXIBILITY (3-Way Markets)

### Design Philosophy
While focusing on **2-way markets** (NBA/Tennis - no draws), the code is modular for future 3-way support (Soccer).

### Current Support
- ✅ **2-Way Markets**: Basketball (NBA), Tennis (ATP/WTA)
- 🔧 **3-Way Markets**: Soccer (EPL) - Full implementation in `detect_three_way_arbitrage()`

### Code Structure
[src/calculators/arbitrage.py](src/calculators/arbitrage.py#L143-L243):
```python
if num_outcomes == 2:
    # Two-way arbitrage (NBA, Tennis)
    opportunities.append(...)

elif num_outcomes == 3:
    # Three-way arbitrage (Soccer 1X2)
    opportunities.append(...)
```

No full rewrite needed to add Soccer later - just enable the 3-way branch.

---

## 6. RECOMMENDED SPORTS (2-Way Markets)

### Top 3 Sports for Your App

| Sport | Why Great | The Profit Gap |
|-------|-----------|----------------|
| **Basketball (NBA)** | High scoring causes bookie lag | Over/Under, Point Spreads |
| **Tennis (ATP/WTA)** | No draws, 24/7 global matches | Match Winner (Moneyline) |
| **Baseball (MLB)** | Data-heavy, different models | Run Lines, Totals |

### Configuration Update
[config/settings.py](config/settings.py#L16):
```python
SPORTS = ['basketball_nba', 'tennis_atp']  # Focus on 2-way markets
```

**Changed from**: `['basketball_nba', 'soccer_epl']`

### Why Avoid Soccer for Now?
- **3 outcomes** (Win/Draw/Loss) split profit three ways
- **Harder to find gaps** with triple coverage
- **Start simple with 2-way markets**, add Soccer later when profitable

---

## 7. "SWAPPED ODDS" SAFETY

### The Goldmine Risk
If Bookie A has Team 1 as favorite, but Bookie B has Team 2 as favorite = potential goldmine **OR** palpable error.

### Safety Rule
- ✅ **2-10% profit**: Likely real pricing difference (SAFE)
- ❌ **30% profit**: Palpable error (typo) - WILL BE VOIDED

### How App Handles It
**Palpable Error Filter** (already implemented):
[config/settings.py](config/settings.py#L60):
```python
MAX_ROI_THRESHOLD = 15.0  # Discard arbs above this
```

**Discord Alert**:
```
🔴 RULE MISMATCH: CHECK TERMS BEFORE BETTING!
🚨 ARB FOUND (18.2% Profit) - HIGH RISK
```

### Manual Verification Steps
1. Open both bookmaker apps
2. Verify odds are real (not typos)
3. Check recent news (injuries, lineup changes)
4. If profit > 15%, **do not bet unless verified 3 times**

---

## Files Modified

1. **config/settings.py** - Bookmaker categorization, manual scan config, value betting thresholds
2. **src/utils/bookmaker_classifier.py** - NEW: Sharp vs Soft classification logic
3. **src/utils/discord_commands.py** - NEW: Manual scan trigger handler
4. **src/notifiers/discord_webhook.py** - Priority tags in alerts, value bet alerts
5. **src/calculators/arbitrage.py** - 3-way market support, value betting integration
6. **src/utils/advanced_monitors.py** - Enhanced drift tracker with value betting mode

---

## Quick Start Guide

### 1. Update Configuration
Edit [config/settings.py](config/settings.py):
```python
SPORTS = ['basketball_nba', 'tennis_atp']  # 2-way markets
```

### 2. Enable Value Betting
Already enabled by default:
```python
DRIFT_SHARP_BOOKMAKERS = ['pinnacle', 'betfair']
DRIFT_VALUE_THRESHOLD = 5.0
```

### 3. Test Manual Scan
Run the app and trigger a scan:
```python
# In your code or Discord
/scan_now
```

Expected output:
```
🚀 Manual scan started! Running for 300s...
Estimated credits: ~30
You'll receive a summary when complete.
```

---

## Cost Analysis

### Monthly API Budget (500 Credits)

| Activity | Credits/Event | Frequency | Monthly Cost |
|----------|---------------|-----------|--------------|
| **Peak Hours** | 60/hour | 3 hrs/week | ~720/month ❌ |
| **Manual Scans** | 30/scan | 15 scans | 450/month ✅ |
| **Off-Peak** | 2/hour | 24/7 minus peaks | ~100/month |

### Recommended Strategy
- **Disable 24/7 polling** (use manual scans only)
- **15 manual scans/month** = 450 credits
- **Reserve 50 credits** for off-peak monitoring
- **Total**: ~500 credits ✅

---

## What's Next?

### For Immediate Use
1. ✅ Start with **Basketball NBA** and **Tennis ATP**
2. ✅ Use **manual scans** during live games
3. ✅ Watch for **⭐ HIGH CONFIDENCE** alerts (Sharp vs Soft)
4. ✅ Paper trade **💎 VALUE BET** alerts for 10 bets

### For Future Enhancement
1. Full Discord bot with slash commands (`discord.py` integration)
2. Add **Baseball (MLB)** for more 2-way markets
3. Implement Soccer (EPL) 3-way arbitrage when profitable
4. Web dashboard for historical tracking

---

## Professional Betting Wisdom

> "Pinnacle never bans arbitrageurs. If you find a gap between Pinnacle and a local bookie, Pinnacle is always right. Bet on the other side."

> "Value Betting catches the move before the gap even officially opens. Watch when Pinnacle drops but 1xBet stays high - that's free money."

> "Soft vs Soft arbs close in 2-3 minutes. Sharp vs Soft arbs last longer because the Soft bookie doesn't track Sharps in real-time."

---

**Built for professional betting. Stay sharp. 💎**
