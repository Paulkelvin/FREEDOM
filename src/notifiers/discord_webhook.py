"""
Discord Webhook Notifier - Mobile-Optimized Alert System
"""
import requests
from typing import Dict, List
from datetime import datetime
from config.settings import DISCORD_WEBHOOK_URL, ALERT_COOLDOWN_MINUTES
from src.utils.logger import setup_logger


class DiscordNotifier:
    """
    Sends mobile-optimized arbitrage alerts to Discord via webhook
    """
    
    def __init__(self):
        self.webhook_url = DISCORD_WEBHOOK_URL
        self.logger = setup_logger()
        self.recent_alerts = {}  # Deduplication tracker
        
    def send_arbitrage_alert(self, opportunity: Dict) -> bool:
        """
        Send formatted arbitrage alert to Discord
        
        Args:
            opportunity: Arbitrage opportunity dict from calculator
            
        Returns:
            True if sent successfully, False otherwise
        """
        if not self.webhook_url:
            self.logger.warning("⚠️ Discord webhook URL not configured. Skipping alert.")
            return False
        
        # Deduplication: Check if we already alerted for this event recently
        event_id = opportunity.get('event_id')
        if self._is_duplicate_alert(event_id):
            self.logger.info(f"Skipping duplicate alert for {event_id}")
            return False
        
        # Build mobile-optimized message
        message = self._format_mobile_alert(opportunity)
        
        # Send to Discord
        try:
            response = requests.post(
                self.webhook_url,
                json={'content': message},
                timeout=10
            )
            response.raise_for_status()
            
            self.logger.info(f"✅ Discord alert sent for {opportunity['event_name']}")
            self._mark_alerted(event_id)
            return True
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"❌ Failed to send Discord alert: {e}")
            return False
    
    def _format_mobile_alert(self, opp: Dict) -> str:
        """
        Format arbitrage data into mobile-friendly Discord message
        
        Uses mobile-optimized template with RED HEADER for rule mismatches
        and priority tags (⭐ HIGH CONFIDENCE, ⚡ FAST MOVE)
        """
        from config.settings import HIGH_RISK_BOOKMAKERS
        from src.utils.advanced_monitors import risk_reporter
        from src.utils.bookmaker_classifier import bookmaker_classifier
        
        roi = opp['roi']
        event_name = opp['event_name']
        sport = opp['sport']
        bets = opp['bets']
        stakes = opp['stakes']
        
        # Sport emoji
        sport_emoji = '🏀' if 'basketball' in sport.lower() else '🎾' if 'tennis' in sport.lower() else '⚽'
        
        # Determine market type for risk check
        market_type = 'basketball_moneyline' if 'basketball' in sport.lower() else 'soccer_h2h'
        
        # Risk check for rule mismatches
        risk_status = risk_reporter.risk_check(
            market_type,
            bets[0]['bookmaker'],
            bets[1]['bookmaker']
        )
        
        # Get priority tag (Sharp vs Soft classification)
        tag_emoji, tag_text, tag_explanation = bookmaker_classifier.get_priority_tag(
            bets[0]['bookmaker'],
            bets[1]['bookmaker']
        )
        
        # Calculate profit
        total_investment = sum(stakes)
        guaranteed_profit = (stakes[0] * bets[0]['odds']) - total_investment
        
        # Build header with priority tag and risk warnings
        if '🔴' in risk_status:
            header = (
                f"🔴 **RULE MISMATCH: CHECK TERMS BEFORE BETTING!**\n"
                f"🚨 **ARB FOUND ({roi:.1f}% Profit) - HIGH RISK**"
            )
        else:
            header = f"{tag_emoji} **[{tag_text}] ARB FOUND ({roi:.1f}% Profit)**"
        
        # Build message
        lines = [
            header,
            f"{sport_emoji} **{event_name}**",
            "",
            f"🟩 **BET 1:** Back **{bets[0]['outcome']}** @ **{bets[0]['odds']:.2f}**",
            f"🏦 Bookie: **{self._format_bookmaker_name(bets[0]['bookmaker'])}**",
            f"💵 Stake: **${stakes[0]:.0f}**",
            "",
            f"🟦 **BET 2:** Back **{bets[1]['outcome']}** @ **{bets[1]['odds']:.2f}**",
            f"🏦 Bookie: **{self._format_bookmaker_name(bets[1]['bookmaker'])}**",
            f"💵 Stake: **${stakes[1]:.0f}**",
            "",
            f"⚠️ **Total Risk:** ${total_investment:.0f} | **Guaranteed Profit:** ${guaranteed_profit:.2f}",
        ]
        
        # Add priority explanation
        if tag_explanation and '🔴' not in risk_status:
            lines.append("")
            lines.append(f"**Why {tag_text}?** {tag_explanation}")
        
        # Add betting recommendation
        recommendation = bookmaker_classifier.get_betting_recommendation(
            bets[0]['bookmaker'],
            bets[1]['bookmaker']
        )
        if recommendation:
            lines.append("")
            lines.append(recommendation)
        
        # Add risk status
        lines.append("")
        lines.append(f"**Risk Check:** {risk_status}")
        
        # Add specific warnings
        warnings = self._generate_risk_warnings(opp)
        if warnings:
            lines.append("")
            lines.extend(warnings)
        
        # Add timestamp
        lines.append("")
        lines.append(f"_Alert generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}_")
        
        return "\n".join(lines)
    
    def _format_bookmaker_name(self, bookmaker_key: str) -> str:
        """
        Convert API bookmaker key to readable name
        
        Args:
            bookmaker_key: API key (e.g., 'williamhill_us')
            
        Returns:
            Formatted name (e.g., 'William Hill')
        """
        # Common mappings
        name_map = {
            'williamhill': 'William Hill',
            'draftkings': 'DraftKings',
            'fanduel': 'FanDuel',
            'betmgm': 'BetMGM',
            'pointsbet': 'PointsBet',
            'unibet': 'Unibet',
            'betfair': 'Betfair',
            'pinnacle': 'Pinnacle',
            '1xbet': '1xBet',
            'bet365': 'Bet365',
        }
        
        # Remove region suffix (_us, _eu)
        clean_key = bookmaker_key.split('_')[0].lower()
        return name_map.get(clean_key, bookmaker_key.title())
    
    def _generate_risk_warnings(self, opp: Dict) -> List[str]:
        """
        Generate risk warning messages for the alert
        
        Args:
            opp: Opportunity dict
            
        Returns:
            List of warning strings
        """
        warnings = []
        
        bookmaker_a = opp['bets'][0]['bookmaker']
        bookmaker_b = opp['bets'][1]['bookmaker']
        
        # Check for overtime rule mismatches (basketball)
        if 'basketball' in opp['sport'].lower():
            warnings.append("⚠️ **BASKETBALL NOTICE:** Verify both bookies settle on SAME rules (including Overtime)")
            warnings.append(f"   → Check {self._format_bookmaker_name(bookmaker_a)} terms")
            warnings.append(f"   → Check {self._format_bookmaker_name(bookmaker_b)} terms")
        
        # Check for 90-min vs full-time mismatches (soccer)
        if 'soccer' in opp['sport'].lower() or 'football' in opp['sport'].lower():
            warnings.append("⚠️ **SOCCER NOTICE:** Most bookies settle on 90 min + injury time (NO extra time)")
            warnings.append(f"   → Confirm both {self._format_bookmaker_name(bookmaker_a)} & {self._format_bookmaker_name(bookmaker_b)} use same settlement")
        
        return warnings
    
    def _is_duplicate_alert(self, event_id: str) -> bool:
        """
        Check if we've already alerted for this event recently
        
        Args:
            event_id: Event identifier
            
        Returns:
            True if duplicate, False if new
        """
        if event_id in self.recent_alerts:
            last_alert_time = self.recent_alerts[event_id]
            minutes_since = (datetime.now() - last_alert_time).total_seconds() / 60
            return minutes_since < ALERT_COOLDOWN_MINUTES
        
        return False
    
    def _mark_alerted(self, event_id: str):
        """Record that we've sent an alert for this event"""
        self.recent_alerts[event_id] = datetime.now()
        
        # Cleanup old entries (keep last 100)
        if len(self.recent_alerts) > 100:
            sorted_events = sorted(self.recent_alerts.items(), key=lambda x: x[1])
            self.recent_alerts = dict(sorted_events[-100:])
    
    def send_drift_alert(self, drift_data: Dict) -> bool:
        """
        Send alert for rapid odds movement (pre-arb indicator) or value betting
        
        Args:
            drift_data: Drift tracking data or value bet opportunity
            
        Returns:
            True if sent successfully
        """
        if not self.webhook_url:
            return False
        
        # Value Betting Alert (NEW)
        if drift_data.get('type') == 'value_bet':
            message = (
                f"💎 **VALUE BET DETECTED**\n\n"
                f"**Outcome:** {drift_data['outcome']}\n"
                f"**Event:** {drift_data['event_id']}\n\n"
                f"🟢 **Soft Bookie:** {drift_data['soft_bookmaker']} @ **{drift_data['soft_odds']:.2f}**\n"
                f"🔵 **Sharp Consensus:** {drift_data['sharp_bookmaker']} @ {drift_data['sharp_odds']:.2f}\n"
                f"📊 **Value Edge:** +{drift_data['value_gap']:.1f}%\n\n"
                f"💡 **Recommendation:**\n{drift_data['recommendation']}\n\n"
                f"_This is NOT arbitrage - you're betting on the Sharp bookmaker being right. "
                f"The Soft bookie will likely adjust their price down soon._"
            )
        
        # Standard Drift Alert (existing)
        else:
            message = (
                f"📉 **ODDS DRIFT DETECTED**\n"
                f"Event: {drift_data['event_id']}\n"
                f"Outcome: **{drift_data['outcome']}**\n"
                f"Previous: {drift_data['previous_odds']:.2f} → Current: {drift_data['current_odds']:.2f}\n"
                f"Change: **{drift_data['drift_percent']:.1f}%**\n\n"
                f"_This may signal an upcoming arbitrage opportunity. Monitor closely._"
            )
        
        try:
            requests.post(self.webhook_url, json={'content': message}, timeout=10)
            return True
        except:
            return False
