"""
Advanced Monitoring Modules:
- Drift Tracker: Pre-arb detection via rapid odds changes
- Multi-Market Scanner: Cross-market analysis (Winner + Over/Under)
- Risk Reporter: Bookmaker terms validation
"""
from typing import Dict, List, Optional
from datetime import datetime
from config.settings import (
    ENABLE_MULTIMARKET_SCAN, MULTIMARKET_MARKETS,
    BOOKMAKER_OVERTIME_RULES, ENABLE_DRIFT_TRACKER
)
from src.utils.logger import setup_logger


class DriftTracker:
    """
    Monitors global price movements to detect pre-arbitrage conditions
    
    TWO MODES:
    1. Pre-Arb Detection: If all bookies drop odds except one, that's a signal
    2. Value Betting: If Sharp (Pinnacle/Betfair) drops but Soft stays high, bet the Soft
    
    "Value Betting is often more profitable than arbitrage because you catch
    the move before the gap even officially opens."
    """
    
    def __init__(self):
        self.logger = setup_logger()
        self.historical_odds = {}  # {event_id: {bookmaker: {outcome: odds}}}
        self.sharp_prices = {}  # Track Sharp bookmaker prices separately
    
    def track_value_opportunity(self, event_id: str, bookmaker: str, outcome: str, 
                                current_odds: float) -> Optional[Dict]:
        """
        Value Betting Mode: Detect when Sharp bookmaker drops but Soft stays high
        
        Example:
        - Pinnacle Lakers odds: 1.90 → 1.80 → 1.70 (dropping)
        - 1xBet Lakers odds: 1.90 (still high)
        - Alert: Bet Lakers at 1.90 on 1xBet (value bet)
        
        Args:
            event_id: Unique event identifier
            bookmaker: Bookmaker name
            outcome: Outcome name (e.g., 'Lakers', 'Over')
            current_odds: Current odds value
            
        Returns:
            Value betting alert dict if opportunity detected
        """
        from config.settings import DRIFT_SHARP_BOOKMAKERS, DRIFT_VALUE_THRESHOLD
        from src.utils.bookmaker_classifier import bookmaker_classifier
        
        # Clean bookmaker name
        clean_bookie = bookmaker.split('_')[0].lower()
        bookie_class = bookmaker_classifier.classify_bookmaker(bookmaker)
        
        # Track Sharp bookmaker prices (source of truth)
        if clean_bookie in [s.lower() for s in DRIFT_SHARP_BOOKMAKERS]:
            event_outcome_key = f"{event_id}:{outcome}"
            
            # Store current Sharp price
            if event_outcome_key not in self.sharp_prices:
                self.sharp_prices[event_outcome_key] = {
                    'bookmaker': bookmaker,
                    'odds': current_odds,
                    'timestamp': datetime.now()
                }
            else:
                # Check if Sharp price dropped significantly
                prev_sharp = self.sharp_prices[event_outcome_key]['odds']
                
                if current_odds < prev_sharp:
                    drop_pct = ((prev_sharp - current_odds) / prev_sharp) * 100
                    
                    if drop_pct > 3:  # Sharp dropped >3%
                        self.logger.warning(
                            f"📉 SHARP DROP: {bookmaker} {outcome} "
                            f"{prev_sharp:.2f} → {current_odds:.2f} (-{drop_pct:.1f}%)"
                        )
                        
                        # Update stored Sharp price
                        self.sharp_prices[event_outcome_key] = {
                            'bookmaker': bookmaker,
                            'odds': current_odds,
                            'timestamp': datetime.now()
                        }
        
        # Check if Soft bookmaker has higher price than Sharp consensus
        elif bookie_class == 'soft':
            event_outcome_key = f"{event_id}:{outcome}"
            
            if event_outcome_key in self.sharp_prices:
                sharp_price = self.sharp_prices[event_outcome_key]['odds']
                sharp_bookie = self.sharp_prices[event_outcome_key]['bookmaker']
                
                # Calculate value gap
                value_gap_pct = ((current_odds - sharp_price) / sharp_price) * 100
                
                if value_gap_pct > DRIFT_VALUE_THRESHOLD:
                    self.logger.warning(
                        f"💎 VALUE BET: {bookmaker} @ {current_odds:.2f} "
                        f"vs {sharp_bookie} @ {sharp_price:.2f} "
                        f"(+{value_gap_pct:.1f}% value)"
                    )
                    
                    return {
                        'type': 'value_bet',
                        'event_id': event_id,
                        'outcome': outcome,
                        'soft_bookmaker': bookmaker,
                        'soft_odds': current_odds,
                        'sharp_bookmaker': sharp_bookie,
                        'sharp_odds': sharp_price,
                        'value_gap': value_gap_pct,
                        'recommendation': (
                            f"Bet {outcome} @ {current_odds:.2f} on {bookmaker}. "
                            f"Sharp consensus is {sharp_price:.2f}, giving you "
                            f"{value_gap_pct:.1f}% value edge."
                        )
                    }
        
        return None
    
    def track_movement(self, event_id: str, current_odds: Dict[str, Dict[str, float]]) -> Optional[Dict]:
        """
        Analyze if global consensus is moving while one bookie lags
        
        Args:
            event_id: Unique event identifier
            current_odds: {bookmaker: {outcome: odds}}
            
        Returns:
            Alert dict if divergence detected
        """
        if event_id not in self.historical_odds:
            self.historical_odds[event_id] = current_odds
            return None
        
        prev_odds = self.historical_odds[event_id]
        
        # For each outcome, check if most bookies moved but one stayed high
        for outcome in ['home', 'away', 'draw']:
            bookmakers_dropped = []
            bookmakers_stable = []
            
            for bookie in current_odds.keys():
                if bookie not in prev_odds or outcome not in prev_odds[bookie]:
                    continue
                
                prev_value = prev_odds[bookie].get(outcome)
                curr_value = current_odds[bookie].get(outcome)
                
                if prev_value and curr_value:
                    change_pct = ((curr_value - prev_value) / prev_value) * 100
                    
                    if change_pct < -3:  # Dropped >3%
                        bookmakers_dropped.append(bookie)
                    elif abs(change_pct) < 1:  # Stable
                        bookmakers_stable.append(bookie)
            
            # Alert if 3+ bookies dropped but 1+ stayed stable
            if len(bookmakers_dropped) >= 3 and len(bookmakers_stable) >= 1:
                self.logger.warning(
                    f"🎯 DRIFT SIGNAL: {event_id} - {outcome} - "
                    f"{len(bookmakers_dropped)} bookies dropped, {bookmakers_stable[0]} stayed high"
                )
                
                self.historical_odds[event_id] = current_odds
                return {
                    'event_id': event_id,
                    'outcome': outcome,
                    'lagging_bookies': bookmakers_stable,
                    'dropping_bookies': bookmakers_dropped
                }
        
        self.historical_odds[event_id] = current_odds
        return None


class MultiMarketScanner:
    """
    Scans multiple markets (Winner + Over/Under + Spreads) for cross-market arbs
    
    Often a bookie fixes their moneyline but forgets totals/spreads
    """
    
    def __init__(self):
        self.logger = setup_logger()
    
    def scan_markets(self, event_data: Dict) -> List[Dict]:
        """
        Check all available markets for arbitrage opportunities
        
        Args:
            event_data: Full event data with multiple markets
            
        Returns:
            List of opportunities across all markets
        """
        if not ENABLE_MULTIMARKET_SCAN:
            return []
        
        opportunities = []
        
        for bookmaker in event_data.get('bookmakers', []):
            markets = bookmaker.get('markets', [])
            
            # Check each market type
            for market in markets:
                market_key = market.get('key')
                
                if market_key == 'totals':
                    # Over/Under arbitrage
                    opp = self._check_totals_arb(market, event_data)
                    if opp:
                        opportunities.append(opp)
                
                elif market_key == 'spreads':
                    # Point spread arbitrage
                    opp = self._check_spreads_arb(market, event_data)
                    if opp:
                        opportunities.append(opp)
        
        return opportunities
    
    def _check_totals_arb(self, market: Dict, event: Dict) -> Optional[Dict]:
        """Check Over/Under market for arbitrage"""
        # Implementation would follow same logic as h2h arbitrage
        # This is a placeholder for the concept
        self.logger.debug(f"Scanning totals market for {event.get('id')}")
        return None
    
    def _check_spreads_arb(self, market: Dict, event: Dict) -> Optional[Dict]:
        """Check point spread market for arbitrage"""
        self.logger.debug(f"Scanning spreads market for {event.get('id')}")
        return None


class RiskReporter:
    """
    Validates bookmaker settlement rules to prevent "trap" arbitrages
    
    Checks:
    - Overtime handling (NBA/NHL)
    - Extra time rules (Soccer)
    - High-risk bookmakers with non-standard rules
    - Void conditions
    """
    
    def __init__(self):
        self.logger = setup_logger()
        self.rules_database = BOOKMAKER_OVERTIME_RULES
    
    def risk_check(self, market_type: str, bookie_a: str, bookie_b: str) -> str:
        """
        Enhanced risk check for high-risk rule mismatches
        
        Args:
            market_type: e.g., 'basketball_moneyline', 'soccer_h2h'
            bookie_a: First bookmaker
            bookie_b: Second bookmaker
            
        Returns:
            Risk status string with severity indicator
        """
        from config.settings import HIGH_RISK_BOOKMAKERS
        
        # Clean bookmaker names
        clean_a = bookie_a.split('_')[0]
        clean_b = bookie_b.split('_')[0]
        
        # Check for known high-risk bookmakers
        for risky in HIGH_RISK_BOOKMAKERS:
            if risky.lower() in clean_a.lower():
                return f"🔴 HIGH RISK: {risky} has non-standard {market_type} rules - VERIFY MANUALLY"
            if risky.lower() in clean_b.lower():
                return f"🔴 HIGH RISK: {risky} has non-standard {market_type} rules - VERIFY MANUALLY"
        
        # Basketball: Overtime rule check
        if 'basketball' in market_type.lower():
            rule_a = self._get_settlement_rule(bookie_a, 'basketball')
            rule_b = self._get_settlement_rule(bookie_b, 'basketball')
            
            if rule_a == 'unknown' or rule_b == 'unknown':
                return "⚠️ WARNING: Unknown Overtime rules - CHECK BOTH SITES"
            
            if rule_a != rule_b:
                return f"🔴 RULE MISMATCH: {bookie_a} ({rule_a}) vs {bookie_b} ({rule_b}) - REJECT ARB"
            
            return "✅ Rules Match: Both include Overtime"
        
        # Soccer: 90-min check
        if 'soccer' in market_type.lower() or 'football' in market_type.lower():
            return "ℹ️ Check: Ensure both settle at 90 Mins + Injury Time (NOT 'To Advance')"
        
        return "✅ Rules Match"
    
    def validate_bookmaker_pair(self, bookie_a: str, bookie_b: str, sport: str) -> Dict:
        """
        Check if two bookmakers have compatible settlement rules
        
        Args:
            bookie_a: First bookmaker key
            bookie_b: Second bookmaker key
            sport: Sport type (basketball_nba, soccer_epl)
            
        Returns:
            {
                'compatible': bool,
                'warning': str or None,
                'recommendation': str
            }
        """
        rule_a = self._get_settlement_rule(bookie_a, sport)
        rule_b = self._get_settlement_rule(bookie_b, sport)
        
        if rule_a == 'unknown' or rule_b == 'unknown':
            return {
                'compatible': False,
                'warning': f'Unknown settlement rules for {bookie_a} or {bookie_b}',
                'recommendation': 'MANUALLY VERIFY terms on both sites before betting'
            }
        
        if rule_a != rule_b:
            return {
                'compatible': False,
                'warning': f'RULE MISMATCH: {bookie_a} uses {rule_a}, {bookie_b} uses {rule_b}',
                'recommendation': 'REJECT THIS ARB - High void risk'
            }
        
        return {
            'compatible': True,
            'warning': None,
            'recommendation': f'Safe: Both settle on {rule_a}'
        }
    
    def _get_settlement_rule(self, bookmaker: str, sport: str) -> str:
        """
        Lookup settlement rule for a bookmaker
        
        Returns:
            'includes_overtime', 'regulation_only', or 'unknown'
        """
        # Clean bookmaker name (remove region suffix)
        clean_name = bookmaker.split('_')[0]
        
        # Try exact match
        for key, rule in self.rules_database.items():
            if key.lower() in clean_name.lower() or clean_name.lower() in key.lower():
                return rule
        
        return 'unknown'
    
    def generate_checklist(self, bookie_a: str, bookie_b: str, sport: str) -> List[str]:
        """
        Generate a pre-bet verification checklist
        
        Args:
            bookie_a, bookie_b: Bookmaker names
            sport: Sport type
            
        Returns:
            List of verification steps
        """
        checklist = [
            f"✓ Check {bookie_a} terms: Does bet include overtime/extra time?",
            f"✓ Check {bookie_b} terms: Does bet include overtime/extra time?",
            "✓ Verify both have SAME payout conditions",
        ]
        
        if 'basketball' in sport.lower():
            checklist.extend([
                "✓ Confirm overtime is included on BOTH sites",
                "✓ Check void conditions (player injury/scratch rules)",
            ])
        
        if 'soccer' in sport.lower() or 'football' in sport.lower():
            checklist.extend([
                "✓ Confirm bet settles at 90 min + injury time (NOT penalties/extra time)",
                "✓ Check if postponement voids the bet",
            ])
        
        checklist.append("✓ Paper trade first: Open both apps, verify odds match alert")
        
        return checklist


# Singleton instances for global use
drift_tracker = DriftTracker()
multimarket_scanner = MultiMarketScanner()
risk_reporter = RiskReporter()
