"""
Discord Command Handler for Manual Scan Trigger
Allows on-demand high-frequency scanning via /scan_now command
"""
import time
import threading
from datetime import datetime
from typing import Optional

from config.settings import (
    MANUAL_SCAN_DURATION, MANUAL_SCAN_INTERVAL, DISCORD_WEBHOOK_URL
)
from src.api.odds_client import OddsAPIClient
from src.calculators.arbitrage import ArbitrageCalculator
from src.notifiers.discord_webhook import DiscordNotifier
from src.utils.logger import setup_logger


class ManualScanHandler:
    """
    Handles manual scan requests triggered via Discord commands
    
    Usage: User sends /scan_now to Discord, bot responds with immediate scan
    """
    
    def __init__(self, api_client: OddsAPIClient, calculator: ArbitrageCalculator, 
                 notifier: DiscordNotifier):
        self.api_client = api_client
        self.calculator = calculator
        self.notifier = notifier
        self.logger = setup_logger()
        self.is_scanning = False
        self.scan_thread: Optional[threading.Thread] = None
        
    def trigger_manual_scan(self, sport: Optional[str] = None) -> dict:
        """
        Execute a high-frequency scan burst for 5 minutes
        
        Args:
            sport: Specific sport to scan, or None for all sports
            
        Returns:
            Scan summary with opportunities found and credits used
        """
        if self.is_scanning:
            return {
                'status': 'error',
                'message': 'A manual scan is already in progress. Please wait.'
            }
        
        # Start scan in background thread
        self.scan_thread = threading.Thread(
            target=self._execute_scan_burst,
            args=(sport,),
            daemon=True
        )
        self.scan_thread.start()
        
        return {
            'status': 'started',
            'message': f'🚀 Manual scan started! Running for {MANUAL_SCAN_DURATION}s...',
            'duration': MANUAL_SCAN_DURATION,
            'interval': MANUAL_SCAN_INTERVAL,
            'estimated_credits': MANUAL_SCAN_DURATION // MANUAL_SCAN_INTERVAL
        }
    
    def _execute_scan_burst(self, sport: Optional[str]):
        """
        Internal method to run the actual scan burst
        
        Args:
            sport: Sport to scan or None for all
        """
        self.is_scanning = True
        start_time = time.time()
        scan_count = 0
        opportunities_found = 0
        credits_used_before = self.api_client.requests_made
        
        self.logger.info("=" * 60)
        self.logger.info("🚀 MANUAL SCAN BURST STARTED")
        self.logger.info(f"Duration: {MANUAL_SCAN_DURATION}s | Interval: {MANUAL_SCAN_INTERVAL}s")
        self.logger.info("=" * 60)
        
        try:
            while (time.time() - start_time) < MANUAL_SCAN_DURATION:
                scan_count += 1
                self.logger.info(f"🔄 Manual Scan #{scan_count} at {datetime.now().strftime('%H:%M:%S')}")
                
                # Fetch odds
                if sport:
                    odds_data = {sport: self.api_client.get_sports_odds(sport)}
                else:
                    odds_data = self.api_client.get_all_sports_odds()
                
                # Process events
                for sport_key, events in odds_data.items():
                    if not events:
                        continue
                    
                    for event in events:
                        parsed_odds = self.api_client.parse_bookmaker_odds(event)
                        if len(parsed_odds) < 2:
                            continue
                        
                        # Find arbitrage
                        opps = self.calculator.find_arbitrage_opportunities(event, parsed_odds)
                        
                        if opps:
                            opportunities_found += len(opps)
                            for opp in opps:
                                self.notifier.send_arbitrage_alert(opp)
                                self.logger.warning(f"✅ Manual scan found arb: {opp['event_name']}")
                
                # Wait for next interval
                time.sleep(MANUAL_SCAN_INTERVAL)
            
        except Exception as e:
            self.logger.error(f"❌ Error during manual scan: {e}", exc_info=True)
        
        finally:
            # Calculate credits used
            credits_used = self.api_client.requests_made - credits_used_before
            elapsed = time.time() - start_time
            
            # Send completion report to Discord
            self._send_scan_report(scan_count, opportunities_found, credits_used, elapsed)
            
            self.is_scanning = False
            self.logger.info("=" * 60)
            self.logger.info(f"✅ Manual scan complete: {scan_count} scans, {opportunities_found} arbs, {credits_used} credits")
            self.logger.info("=" * 60)
    
    def _send_scan_report(self, scans: int, opportunities: int, credits: int, duration: float):
        """Send scan completion report to Discord"""
        if not DISCORD_WEBHOOK_URL:
            return
        
        import requests
        
        report = (
            f"📊 **MANUAL SCAN COMPLETE**\n\n"
            f"⏱️ Duration: {duration:.1f}s\n"
            f"🔄 Scans Performed: {scans}\n"
            f"🎯 Opportunities Found: {opportunities}\n"
            f"💳 API Credits Used: {credits}\n\n"
            f"_Scan finished at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}_"
        )
        
        try:
            requests.post(DISCORD_WEBHOOK_URL, json={'content': report}, timeout=10)
        except Exception as e:
            self.logger.error(f"Failed to send scan report: {e}")


class DiscordCommandListener:
    """
    Simple webhook-based Discord command listener
    
    For production, use discord.py library with slash commands
    This is a lightweight alternative for demo purposes
    """
    
    def __init__(self, scan_handler: ManualScanHandler):
        self.scan_handler = scan_handler
        self.logger = setup_logger()
    
    def parse_command(self, message: str) -> Optional[dict]:
        """
        Parse Discord message for commands
        
        Args:
            message: Raw message text
            
        Returns:
            Command dict or None
        """
        message = message.strip().lower()
        
        if message == '/scan_now' or message == '/scan':
            return {'command': 'scan', 'sport': None}
        
        if message.startswith('/scan_nba'):
            return {'command': 'scan', 'sport': 'basketball_nba'}
        
        if message.startswith('/scan_tennis'):
            return {'command': 'scan', 'sport': 'tennis_atp'}
        
        return None
    
    def handle_command(self, command: dict) -> str:
        """
        Execute command and return response
        
        Args:
            command: Parsed command dict
            
        Returns:
            Response message
        """
        if command['command'] == 'scan':
            result = self.scan_handler.trigger_manual_scan(command.get('sport'))
            
            if result['status'] == 'started':
                return (
                    f"{result['message']}\n"
                    f"Estimated credits: ~{result['estimated_credits']}\n"
                    f"You'll receive a summary when complete."
                )
            else:
                return result['message']
        
        return "Unknown command. Try /scan_now, /scan_nba, or /scan_tennis"


# Note: For full Discord bot integration, install discord.py and use:
# @bot.slash_command(name="scan_now", description="Trigger immediate arbitrage scan")
# async def scan_now(ctx):
#     result = scan_handler.trigger_manual_scan()
#     await ctx.respond(result['message'])
