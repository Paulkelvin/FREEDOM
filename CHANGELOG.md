# CHANGELOG - Arbitrage Monitor Updates

## December 28, 2025 - Adviser Recommendations Implemented

### 1. Peak Hours "Sniper Window" Strategy ✅
**Problem**: 60s polling 24/7 = 43,200 requests/month (exceeds 500 free tier by 86x)

**Solution**:
- Added `src/utils/peak_scheduler.py` - Smart scheduler that only polls during high-volume hours
- **Peak Hours (Fast)**: 60s polling during NBA evenings (6-11 PM) and EPL weekends
- **Off-Peak (Maintenance)**: 30-min polling outside active hours
- **Configuration**: `PEAK_HOURS_SCHEDULE` in `config/settings.py`

**Result**: User can customize schedule to fit 500 credits/month (e.g., Sat EPL only = ~720 req/month)

---

### 2. Smart Stake Rounding (Anti-Detection) ✅
**Problem**: All stakes rounded to nearest $5 looks robotic

**Solution**:
- Implemented `_smart_round()` in `src/calculators/arbitrage.py`
- **>$1000**: Round to nearest $100 (e.g., $1,247 → $1,200)
- **>$100**: Round to nearest $50 (e.g., $485 → $500)
- **<$100**: Round to nearest $5 (e.g., $73 → $75)
- **Toggle**: `ENABLE_SMART_ROUNDING = True` in config

**Result**: Stakes look like human betting patterns

---

### 3. Enhanced RiskReporter with 🔴 RED HEADER Alerts ✅
**Problem**: Rule mismatches (Overtime/90-min) not prominently flagged

**Solution**:
- Added `risk_check()` method to `RiskReporter` class
- **Basketball**: Detects if one bookie includes OT, other doesn't (e.g., Kwiff vs DraftKings)
- **Soccer**: Flags if bookies don't match 90-min vs "To Advance" rules
- **Discord Alert**: Shows `🔴 RULE MISMATCH: CHECK TERMS BEFORE BETTING!` header
- **High-Risk Bookies**: `Kwiff`, `InternationalBookieX` auto-flagged

**Result**: Users get critical warnings BEFORE betting on trap arbitrages

---

### 4. Updated Bookmaker Rules Database ✅
**Changes**:
- Expanded `BOOKMAKER_OVERTIME_RULES` with comprehensive coverage
- Added `HIGH_RISK_BOOKMAKERS` list (Kwiff, InternationalBookieX)
- Removed static `HIGH_RISK_COMBINATIONS` (now dynamically detected)

**Master Rules** (hardcoded as recommended):
- **Basketball**: Almost all include Overtime (except Kwiff - RED FLAG)
- **Soccer**: Almost all settle at 90 min + injury time (NO extra time)

---

### 5. Paper Trading Mode Enhanced ✅
**Existing**: `--dry-run` flag already implemented

**Improved Documentation**:
- Added "Paper Trading Protocol" section in README
- 10-bet validation workflow before going live
- Tracking template for logging results

---

### 6. Main Application Loop Updates ✅
**Changes**:
- Integrated peak hours scheduler into `main.py`
- Shows active sports during peak windows
- Skips sports outside their peak hours
- Displays schedule on startup
- Enhanced risk logging (🔴 CRITICAL, ⚠️ WARNING, ✅ SAFE)

**Output Example**:
```
🔄 PEAK HOURS - Starting scan at 19:32:15
   Active: Peak hours for: basketball_nba
⏸️ Off-peak hours. Next windows: soccer_epl: Sat at 07:00
```

---

## Configuration Examples

### Conservative (500 Credits/Month)
```python
PEAK_HOURS_SCHEDULE = {
    'soccer_epl': [
        {'days': [5], 'start_hour': 11, 'end_hour': 14},  # Sat 11 AM-2 PM
    ],
}
```

### Aggressive (Exceeds Free Tier - Requires Paid)
```python
PEAK_HOURS_SCHEDULE = {
    'basketball_nba': [
        {'days': [0,1,2,3,4,5,6], 'start_hour': 18, 'end_hour': 23},
    ],
    'soccer_epl': [
        {'days': [5,6], 'start_hour': 7, 'end_hour': 13},
        {'days': [1,2,3], 'start_hour': 19, 'end_hour': 22},
    ],
}
```

---

## Files Modified

1. `config/settings.py` - Peak hours schedule, smart rounding, high-risk bookies
2. `src/calculators/arbitrage.py` - Smart stake rounding, enhanced safety filters
3. `src/utils/advanced_monitors.py` - risk_check() method in RiskReporter
4. `src/notifiers/discord_webhook.py` - RED HEADER for rule mismatches
5. `src/utils/peak_scheduler.py` - NEW: Peak hours scheduling logic
6. `main.py` - Integrated scheduler, enhanced logging
7. `README.md` - Updated with all new features and warnings

---

## Next Steps for User

1. **Adjust Peak Hours**: Edit `config/settings.py` to fit 500 req/month budget
2. **Paper Trade**: Run `python main.py --dry-run` for 10-bet validation
3. **Monitor Quota**: Check logs for `x-requests-used` to track API usage
4. **Go Live**: Once paper trades succeed, run `python main.py` in production
