"""
Sports Arbitrage Monitoring System - Main Application
Production-ready arbitrage scanner with peak hours scheduling, safety filters, and Discord alerts
"""
import time
import signal
import sys
import argparse
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from config.settings import POLL_INTERVAL_SECONDS, OFF_PEAK_POLL_INTERVAL, SPORTS, REQUEST_RETRY_DELAY
from src.api.odds_client import OddsAPIClient
from src.calculators.arbitrage import ArbitrageCalculator
from src.notifiers.discord_webhook import DiscordNotifier
from src.utils.advanced_monitors import drift_tracker, risk_reporter
from src.utils.peak_scheduler import peak_scheduler
from src.utils.logger import setup_logger


class ArbitrageMonitor:
    """
    Main application orchestrator for continuous arbitrage monitoring
    """
    
    def __init__(self, dry_run: bool = False, duration_minutes: Optional[int] = None, sport_filter: Optional[str] = None):
        """
        Initialize the arbitrage monitoring system
        
        Args:
            dry_run: If True, log opportunities but don't send Discord alerts
            duration_minutes: If set, run for this many minutes then exit (for GitHub Actions)
            sport_filter: If set, only scan this sport ('nba', 'tennis', or 'all')
        """
        self.logger = setup_logger()
        self.api_client = OddsAPIClient()
        self.calculator = ArbitrageCalculator()
        self.notifier = DiscordNotifier()
        self.dry_run = dry_run
        self.running = True
        self.duration_minutes = duration_minutes
        self.sport_filter = sport_filter
        self.start_time = datetime.now()
        
        # Graceful shutdown handler
        signal.signal(signal.SIGINT, self._shutdown_handler)
        signal.signal(signal.SIGTERM, self._shutdown_handler)
        
        
        # Filter sports if specified
        if self.sport_filter and self.sport_filter != 'all':
            sport_map = {'nba': 'basketball_nba', 'tennis': 'tennis_atp'}
            filtered_sport = sport_map.get(self.sport_filter, self.sport_filter)
            if filtered_sport in SPORTS:
                self.active_sports = [filtered_sport]
            else:
                self.active_sports = SPORTS
        else:
            self.active_sports = SPORTS
            
        self.logger.info(f"Sports: {', '.join(self.active_sports)}")
        self.logger.info(f"Peak Hours Polling: {POLL_INTERVAL_SECONDS}s")
        self.logger.info(f"Off-Peak Polling: {OFF_PEAK_POLL_INTERVAL}s")
        if duration_minutes:
            self.logger.info(f"⏱️ Timed Run: {duration_minutes} minute
        if dry_run:
            self.logger.info("📝 DRY RUN MODE: Alerts will be logged only (no Discord)")
        self.logger.info(f"Sports: {', '.join(SPORTS)}")
        self.logger.info(f"Peak Hours Polling: {POLL_INTERVAL_SECONDS}s")
        self.logger.info(f"Off-Peak Polling: {OFF_PEAK_POLL_INTERVAL}s")
        
        # Show peak hours schedule
        from config.settings import PEAK_HOURS_SCHEDULE
        self.logger.info("\n📅 PEAK HOURS SCHEDULE (Sniper Window Strategy):")
        for sport, windows in PEAK_HOURS_SCHEDULE.items():
            self.logger.info(f"  {sport}:")
            for window in windows:
                days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
                day_names = ', '.join([days[d] for d in window['days']])
                self.logger.info(f"    - {day_names}: {window['start_hour']:02d}:00 - {window['end_hour']:02d}:00")
        self.logger.info("")
    
    def run(self):
        """
        Main monitoring loop with peak hours scheduling (Sniper Window Strategy)
        
        Only polls during high-volume hours to conserve API credits
        Supports timed runs for GitHub Actions
        """
        while self.running:
            # Check if timed run has exceeded duration
            if self.duration_minutes:
                elapsed = (datetime.now() - self.start_time).total_seconds() / 60
                if elapsed >= self.duration_minutes:
                    self.logger.info(f"⏱️ Timed run complete ({self.duration_minutes} minutes)")
                    break
            
            cycle_start = time.time()
            
            try:
                # Check if we're in peak hours for any sport
                should_poll, reason = peak_scheduler.should_poll_now()
                
                if not should_poll:
                    self.logger.info(f"⏸️ {reason}")
                    self.logger.info(f"Sleeping {OFF_PEAK_POLL_INTERVAL}s (off-peak mode)...")
                    self._smart_sleep(OFF_PEAK_POLL_INTERVAL)
                    continue
                
                self.logger.info(f"🔄 PEAK HOURS - Starting scan at {datetime.now().strftime('%H:%M:%S')}")
                self.logger.info(f"   Active: {reason}")
                
                # Fetch odds from API for filtered sports
                all_odds = self.api_client.get_all_sports_odds(sports=self.active_sports)
                
                if not all_odds:
                    self.logger.warning("⚠️ No odds data received. Waiting before retry...")
                    time.sleep(REQUEST_RETRY_DELAY)
                    continue
                
                # Process each sport
                total_opportunities = 0
                for sport, events in all_odds.items():
                    # Only process if in peak hours for this specific sport
                    if not peak_scheduler.is_peak_hour(sport):
                        self.logger.info(f"⏭️ Skipping {sport} (off-peak)")
                        continue
                    
                    opportunities = self._scan_sport_events(sport, events)
                    total_opportunities += len(opportunities)
                    
                    # Send alerts for each opportunity
                    for opp in opportunities:
                        self._process_opportunity(opp)
                
                # Summary
                cycle_duration = time.time() - cycle_start
                self.logger.info(
                    f"✅ Cycle complete: {total_opportunities} opportunities found in {cycle_duration:.1f}s"
                )
                
                # Wait before next poll (fast during peak hours)
                self._smart_sleep(POLL_INTERVAL_SECONDS)
                
            except Exception as e:
                self.logger.error(f"❌ Error in main loop: {e}", exc_info=True)
                self.logger.info(f"Waiting {REQUEST_RETRY_DELAY}s before retry...")
                time.sleep(REQUEST_RETRY_DELAY)
    
    def _scan_sport_events(self, sport: str, events: List[Dict]) -> List[Dict]:
        """
        Scan all events for a sport and find arbitrage opportunities
        
        Args:
            sport: Sport name (e.g., 'basketball_nba')
            events: List of event dictionaries from API
            
        Returns:
            List of arbitrage opportunities
        """
        opportunities = []
        
        self.logger.info(f"📊 Scanning {len(events)} {sport} events...")
        
        for event in events:
            # Parse bookmaker odds
            parsed_odds = self.api_client.parse_bookmaker_odds(event)
            
            if len(parsed_odds) < 2:
                continue  # Need at least 2 bookmakers
            
            # Check for stale odds
            if parsed_odds and self.api_client.is_odds_stale(parsed_odds[0].get('last_update', '')):
                self.logger.debug(f"Skipping {event.get('id')} - stale odds")
                continue
            
            # Find arbitrage opportunities
            event_opps = self.calculator.find_arbitrage_opportunities(event, parsed_odds)
            
            # Drift tracking (pre-arb signal)
            if event_opps:
                event_id = event.get('id')
                current_odds_map = {
                    entry['outcome']: entry['odds'] 
                    for entry in parsed_odds
                }
                drift_alert = self.calculator.track_odds_drift(event_id, current_odds_map)
                if drift_alert:
                    self.notifier.send_drift_alert(drift_alert)
            
            opportunities.extend(event_opps)
        
        return opportunities
    
    def _process_opportunity(self, opportunity: Dict):
        """
        Process a detected arbitrage opportunity
        
        Args:
            opportunity: Arbitrage opportunity dictionary
        """
        event_name = opportunity['event_name']
        roi = opportunity['roi']
        bookmakers = [bet['bookmaker'] for bet in opportunity['bets']]
        
        self.logger.warning(
            f"🚨 ARB DETECTED: {event_name} | "
            f"ROI: {roi:.2f}% | "
            f"Bookmakers: {bookmakers[0]} vs {bookmakers[1]}"
        )
        
        # Risk validation using RiskReporter
        sport = opportunity['sport']
        market_type = 'basketball_moneyline' if 'basketball' in sport.lower() else 'soccer_h2h'
        
        risk_status = risk_reporter.risk_check(
            market_type,
            bookmakers[0], 
            bookmakers[1]
        )
        
        # Log risk status
        if '🔴' in risk_status:
            self.logger.error(f"🔴 CRITICAL RISK: {risk_status}")
        elif '⚠️' in risk_status:
            self.logger.warning(f"⚠️ {risk_status}")
        else:
            self.logger.info(f"✅ {risk_status}")
        
        # Legacy validation (kept for compatibility)
        validation = risk_reporter.validate_bookmaker_pair(
            bookmakers[0], 
            bookmakers[1], 
            sport
        )
        
        if not validation['compatible']:
            self.logger.warning(f"⚠️ RISK ALERT: {validation['warning']}")
            self.logger.info(f"   Recommendation: {validation['recommendation']}")
            # Could add this to Discord alert as well
        
        # Generate verification checklist
        checklist = risk_reporter.generate_checklist(
            bookmakers[0], 
            bookmakers[1], 
            sport
        )
        self.logger.info("📋 Pre-Bet Checklist:")
        for item in checklist:
            self.logger.info(f"   {item}")
        
        # Send Discord alert (unless dry run)
        if not self.dry_run:
            success = self.notifier.send_arbitrage_alert(opportunity)
            if success:
                self.logger.info(f"✅ Alert sent to Discord")
        else:
            self.logger.info("📝 DRY RUN: Alert would be sent to Discord")
    
    def _smart_sleep(self, seconds: int):
        """
        Sleep with periodic checks for shutdown signal
        
        Args:
            seconds: Total sleep duration
        """
        intervals = 10  # Check every second
        for _ in range(intervals):
            if not self.running:
                break
            time.sleep(seconds / intervals)
    
    def _shutdown_handler(self, signum, frame):
        """Handle graceful shutdown on SIGINT/SIGTERM"""
        self.logger.info("")
        self.logger.info("🛑 Shutdown signal received. Stopping monitor...")
        self.running = False
        sys.exit(0)


def main():
    """
    Application entry point
    """
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Sports Arbitrage Monitoring System',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Normal mode (sends Discord alerts)
  python main.py
  
  # Dry run mode (paper trading - logs only)
  python main.py --dry-run
  
Configuration:
  1. Copy .env.example to .env
  2. Add your Odds API key from https://the-odds-api.com
  3. Add your Discord webhook URL
  4. Adjust config/settings.py as needed
        """
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Paper trading mode: log opportunities without sending Discord alerts'
    )
    
    parser.add_argument(
        '--duration',
        type=int,
        metavar='MINUTES',
        help='Run for specified minutes then exit (for GitHub Actions)'
    )
    
    parser.add_argument(
        '--sport',
        type=str,
        choices=['all', 'nba', 'tennis'],
        default='all',
        help='Filter to specific sport (default: all)'
    )
    
    args = parser.parse_args()
    
    # Initialize and run
    monitor = ArbitrageMonitor(
        dry_run=args.dry_run,
        duration_minutes=args.duration,
        sport_filter=args.sport
    )
    monitor.run()


if __name__ == '__main__':
    main()
