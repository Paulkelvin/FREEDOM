"""
Arbitrage Detection and Calculation Engine with Safety Filters
"""
from typing import Dict, List, Optional, Tuple
from itertools import combinations
from config.settings import (
    MAX_ROI_THRESHOLD, MIN_ROI_THRESHOLD, DEFAULT_TOTAL_INVESTMENT,
    ENABLE_SMART_ROUNDING, BOOKMAKER_OVERTIME_RULES, HIGH_RISK_COMBINATIONS,
    ENABLE_DRIFT_TRACKER, DRIFT_THRESHOLD_PERCENT, ENABLE_RISK_REPORTER
)
from src.utils.logger import setup_logger


class ArbitrageCalculator:
    """
    Detects and calculates arbitrage opportunities with risk management filters
    """
    
    def __init__(self):
        self.logger = setup_logger()
        self.previous_odds = {}  # For drift tracking
        
    def calculate_implied_probability(self, odds: float) -> float:
        """
        Calculate implied probability from decimal odds
        
        Args:
            odds: Decimal odds (e.g., 2.10)
            
        Returns:
            Implied probability as percentage (e.g., 47.62)
        """
        return (1 / odds) * 100
    
    def detect_two_way_arbitrage(self, odds_a: float, odds_b: float) -> Tuple[bool, float]:
        """
        Detect arbitrage opportunity for two-way markets (e.g., NBA moneyline, EPL double chance)
        
        Args:
            odds_a: Odds for outcome A
            odds_b: Odds for outcome B
            
        Returns:
            (is_arb, roi_percentage)
        """
        # Edge case: Protect against invalid odds (division by zero)
        if odds_a <= 0 or odds_b <= 0:
            self.logger.warning(f"⚠️ Invalid odds detected: {odds_a}, {odds_b} - skipping")
            return False, 0.0
        
        implied_total = (1 / odds_a) + (1 / odds_b)
        
        # Edge case: Check for zero implied total
        if implied_total == 0:
            self.logger.warning(f"⚠️ Zero implied total for odds: {odds_a}, {odds_b}")
            return False, 0.0
        
        if implied_total < 1.0:
            roi = ((1 / implied_total) - 1) * 100
            return True, roi
        
        return False, 0.0
    
    def detect_three_way_arbitrage(self, odds_1: float, odds_x: float, odds_2: float) -> Tuple[bool, float]:
        """
        Detect arbitrage for three-way markets (e.g., EPL 1X2)
        
        Args:
            odds_1: Home win odds
            odds_x: Draw odds
            odds_2: Away win odds
            
        Returns:
            (is_arb, roi_percentage)
        """
        # Edge case: Protect against invalid odds
        if odds_1 <= 0 or odds_x <= 0 or odds_2 <= 0:
            self.logger.warning(f"⚠️ Invalid 3-way odds: {odds_1}, {odds_x}, {odds_2}")
            return False, 0.0
        
        implied_total = (1 / odds_1) + (1 / odds_x) + (1 / odds_2)
        
        if implied_total == 0:
            return False, 0.0
        
        if implied_total < 1.0:
            roi = ((1 / implied_total) - 1) * 100
            return True, roi
        
        return False, 0.0
    
    def calculate_stakes(self, total_investment: float, odds_list: List[float]) -> List[float]:
        """
        Calculate optimal stake distribution for arbitrage with smart rounding
        
        Args:
            total_investment: Total capital to allocate (e.g., $1000)
            odds_list: List of odds for each outcome
            
        Returns:
            List of stake amounts for each outcome (intelligently rounded)
        """
        from config.settings import ENABLE_SMART_ROUNDING
        
        # Formula: Stake_i = (Total × (1/Odds_i)) / Σ(1/Odds_all)
        inverse_odds_sum = sum(1 / odds for odds in odds_list)
        
        stakes = []
        for odds in odds_list:
            stake = (total_investment * (1 / odds)) / inverse_odds_sum
            
            # Smart rounding for anti-detection (looks human)
            if ENABLE_SMART_ROUNDING:
                rounded_stake = self._smart_round(stake)
            else:
                # Legacy: Round to nearest $5
                rounded_stake = round(stake / 5) * 5
            
            stakes.append(rounded_stake)
        
        return stakes
    
    def _smart_round(self, amount: float) -> float:
        """
        Smart rounding to look like a human bettor (Anti-Detection)
        
        Large amounts rounded to $100, medium to $50, small to $5
        
        Args:
            amount: Raw stake amount
            
        Returns:
            Intelligently rounded stake
        """
        if amount > 1000:
            return round(amount / 100) * 100  # Round to nearest $100
        elif amount > 100:
            return round(amount / 50) * 50    # Round to nearest $50
        else:
            return round(amount / 5) * 5      # Round to nearest $5
    
    def apply_safety_filters(self, roi: float, bookmaker_a: str, bookmaker_b: str, sport: str) -> Tuple[bool, Optional[str]]:
        """
        Apply the three critical safety filters
        
        Args:
            roi: Calculated ROI percentage
            bookmaker_a: First bookmaker name
            bookmaker_b: Second bookmaker name
            sport: Sport type (for OT rule check)
            
        Returns:
            (passes_filters, rejection_reason)
        """
        from config.settings import HIGH_RISK_BOOKMAKERS
        
        # FILTER 1: The "Palpable Error" Filter
        if roi > MAX_ROI_THRESHOLD:
            return False, f"PALPABLE_ERROR (ROI {roi:.1f}% > {MAX_ROI_THRESHOLD}% threshold - likely void)"
        
        # FILTER 2: The "Minimum Profit" Filter
        if roi < MIN_ROI_THRESHOLD:
            return False, f"LOW_PROFIT (ROI {roi:.2f}% < {MIN_ROI_THRESHOLD}% minimum)"
        
        # FILTER 3: The "Trap" Filter - Rule Mismatch Check
        if ENABLE_RISK_REPORTER:
            # Check for high-risk bookmakers (non-standard rules)
            clean_a = bookmaker_a.split('_')[0]
            clean_b = bookmaker_b.split('_')[0]
            
            for risky_bookie in HIGH_RISK_BOOKMAKERS:
                if risky_bookie.lower() in clean_a.lower() or risky_bookie.lower() in clean_b.lower():
                    self.logger.warning(f"🔴 HIGH RISK BOOKIE: {risky_bookie} has non-standard rules!")
                    # Don't auto-reject, but flag heavily
            
            # Basketball: Check overtime handling
            if 'basketball' in sport.lower():
                rule_a = BOOKMAKER_OVERTIME_RULES.get(bookmaker_a, 'unknown')
                rule_b = BOOKMAKER_OVERTIME_RULES.get(bookmaker_b, 'unknown')
                
                if rule_a != rule_b and rule_a != 'unknown' and rule_b != 'unknown':
                    return False, f"RULE_MISMATCH ({bookmaker_a}:{rule_a} vs {bookmaker_b}:{rule_b})"
            
            # Soccer: Generally safe (all 90-min), but flag if unknown
            if 'soccer' in sport.lower() or 'football' in sport.lower():
                rule_a = BOOKMAKER_OVERTIME_RULES.get(bookmaker_a, 'unknown')
                rule_b = BOOKMAKER_OVERTIME_RULES.get(bookmaker_b, 'unknown')
                
                if rule_a == 'unknown' or rule_b == 'unknown':
                    self.logger.warning(f"⚠️ Unknown settlement rule for soccer market")
        
        return True, None
    
    def find_arbitrage_opportunities(self, event: Dict, parsed_odds: List[Dict]) -> List[Dict]:
        """
        Scan all bookmaker combinations for arbitrage in a single event
        
        MODULAR DESIGN: Supports 2-way (NBA/Tennis) and 3-way (Soccer) markets
        
        Args:
            event: Event data from API
            parsed_odds: List of {bookmaker, outcome, odds} dicts
            
        Returns:
            List of arbitrage opportunities
        """
        from src.utils.advanced_monitors import drift_tracker
        
        opportunities = []
        
        # Group odds by outcome
        outcomes_map = {}
        for entry in parsed_odds:
            outcome = entry['outcome']
            if outcome not in outcomes_map:
                outcomes_map[outcome] = []
            outcomes_map[outcome].append(entry)
        
        # Get unique outcomes
        outcomes = list(outcomes_map.keys())
        num_outcomes = len(outcomes)
        
        # VALUE BETTING: Track Sharp bookmaker prices for drift detection
        for outcome, odds_entries in outcomes_map.items():
            for entry in odds_entries:
                value_opp = drift_tracker.track_value_opportunity(
                    event.get('id'),
                    entry['bookmaker'],
                    outcome,
                    entry['odds']
                )
                # Value bets will be sent via drift alert, not standard arb alert
        
        # Two-way arbitrage (NBA, Tennis: Team A vs Team B)
        if num_outcomes == 2:
            outcome_a, outcome_b = outcomes
            
            # Try all bookmaker combinations
            for odds_a_entry in outcomes_map[outcome_a]:
                for odds_b_entry in outcomes_map[outcome_b]:
                    # Skip if same bookmaker
                    if odds_a_entry['bookmaker'] == odds_b_entry['bookmaker']:
                        continue
                    
                    is_arb, roi = self.detect_two_way_arbitrage(
                        odds_a_entry['odds'],
                        odds_b_entry['odds']
                    )
                    
                    if is_arb:
                        # Apply safety filters
                        passes, reason = self.apply_safety_filters(
                            roi,
                            odds_a_entry['bookmaker'],
                            odds_b_entry['bookmaker'],
                            event.get('sport_key', '')
                        )
                        
                        if passes:
                            opportunities.append({
                                'event_id': event.get('id'),
                                'sport': event.get('sport_title', 'Unknown'),
                                'event_name': f"{event.get('home_team')} vs {event.get('away_team')}",
                                'commence_time': event.get('commence_time'),
                                'roi': roi,
                                'bets': [
                                    {
                                        'outcome': outcome_a,
                                        'odds': odds_a_entry['odds'],
                                        'bookmaker': odds_a_entry['bookmaker']
                                    },
                                    {
                                        'outcome': outcome_b,
                                        'odds': odds_b_entry['odds'],
                                        'bookmaker': odds_b_entry['bookmaker']
                                    }
                                ],
                                'stakes': self.calculate_stakes(
                                    DEFAULT_TOTAL_INVESTMENT,
                                    [odds_a_entry['odds'], odds_b_entry['odds']]
                                )
                            })
                        else:
                            self.logger.info(f"FILTERED: {event.get('home_team')} vs {event.get('away_team')} - {reason}")
        
        # Three-way arbitrage (Soccer 1X2: Home/Draw/Away)
        elif num_outcomes == 3:
            # Try all 3-way combinations
            for odds_1 in outcomes_map[outcomes[0]]:
                for odds_x in outcomes_map[outcomes[1]]:
                    for odds_2 in outcomes_map[outcomes[2]]:
                        # Skip if same bookmaker
                        bookies = {odds_1['bookmaker'], odds_x['bookmaker'], odds_2['bookmaker']}
                        if len(bookies) < 2:  # Need at least 2 different bookmakers
                            continue
                        
                        is_arb, roi = self.detect_three_way_arbitrage(
                            odds_1['odds'],
                            odds_x['odds'],
                            odds_2['odds']
                        )
                        
                        if is_arb:
                            # Apply safety filters (first two bookmakers for simplicity)
                            passes, reason = self.apply_safety_filters(
                                roi,
                                odds_1['bookmaker'],
                                odds_2['bookmaker'],
                                event.get('sport_key', '')
                            )
                            
                            if passes:
                                opportunities.append({
                                    'event_id': event.get('id'),
                                    'sport': event.get('sport_title', 'Unknown'),
                                    'event_name': f"{event.get('home_team')} vs {event.get('away_team')}",
                                    'commence_time': event.get('commence_time'),
                                    'roi': roi,
                                    'bets': [
                                        {
                                            'outcome': outcomes[0],
                                            'odds': odds_1['odds'],
                                            'bookmaker': odds_1['bookmaker']
                                        },
                                        {
                                            'outcome': outcomes[1],
                                            'odds': odds_x['odds'],
                                            'bookmaker': odds_x['bookmaker']
                                        },
                                        {
                                            'outcome': outcomes[2],
                                            'odds': odds_2['odds'],
                                            'bookmaker': odds_2['bookmaker']
                                        }
                                    ],
                                    'stakes': self.calculate_stakes(
                                        DEFAULT_TOTAL_INVESTMENT,
                                        [odds_1['odds'], odds_x['odds'], odds_2['odds']]
                                    )
                                })
        
        return opportunities
    
    def track_odds_drift(self, event_id: str, current_odds: Dict) -> Optional[Dict]:
        """
        Drift Tracker: Monitor rapid odds movements (pre-arb indicator)
        
        Args:
            event_id: Unique event identifier
            current_odds: Current odds data
            
        Returns:
            Drift alert dict if significant movement detected
        """
        if not ENABLE_DRIFT_TRACKER:
            return None
        
        if event_id in self.previous_odds:
            prev = self.previous_odds[event_id]
            
            for outcome, current_value in current_odds.items():
                if outcome in prev:
                    prev_value = prev[outcome]
                    change_pct = abs((current_value - prev_value) / prev_value) * 100
                    
                    if change_pct > DRIFT_THRESHOLD_PERCENT:
                        self.logger.warning(f"📉 DRIFT ALERT: {event_id} - {outcome} moved {change_pct:.1f}% ({prev_value} → {current_value})")
                        return {
                            'event_id': event_id,
                            'outcome': outcome,
                            'previous_odds': prev_value,
                            'current_odds': current_value,
                            'drift_percent': change_pct
                        }
        
        # Store for next comparison
        self.previous_odds[event_id] = current_odds.copy()
        return None
