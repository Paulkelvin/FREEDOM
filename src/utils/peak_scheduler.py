"""
Peak Hours Scheduler - "Sniper Window" Strategy
Only polls during high-volume hours to conserve API credits
"""
from datetime import datetime
from typing import Optional
from config.settings import PEAK_HOURS_SCHEDULE


class PeakHoursScheduler:
    """
    Manages polling schedule based on peak arbitrage activity hours
    
    Saves 500 API credits by only polling when money is actually moving
    """
    
    def __init__(self):
        self.schedule = PEAK_HOURS_SCHEDULE
    
    def is_peak_hour(self, sport: str) -> bool:
        """
        Check if current time is within peak hours for a sport
        
        Args:
            sport: Sport key (e.g., 'basketball_nba')
            
        Returns:
            True if in peak hours, False otherwise
        """
        now = datetime.now()
        current_day = now.weekday()  # 0=Monday, 6=Sunday
        current_hour = now.hour
        
        if sport not in self.schedule:
            return True  # Default: poll if no schedule defined
        
        for window in self.schedule[sport]:
            # Check if current day is in allowed days
            if current_day in window['days']:
                # Check if current hour is in time range
                if window['start_hour'] <= current_hour < window['end_hour']:
                    return True
        
        return False
    
    def get_next_peak_time(self, sport: str) -> Optional[str]:
        """
        Calculate when the next peak window opens for a sport
        
        Args:
            sport: Sport key
            
        Returns:
            Human-readable next peak time
        """
        now = datetime.now()
        
        if sport not in self.schedule:
            return None
        
        # Find next window (simplified - just shows next scheduled day/time)
        for window in self.schedule[sport]:
            if now.weekday() in window['days']:
                return f"Today at {window['start_hour']:02d}:00"
            
        # Next scheduled day
        next_window = self.schedule[sport][0]
        days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        next_day = days[next_window['days'][0]]
        return f"{next_day} at {next_window['start_hour']:02d}:00"
    
    def should_poll_now(self) -> tuple[bool, str]:
        """
        Check if we should poll ANY sport right now
        
        Returns:
            (should_poll, reason)
        """
        from config.settings import SPORTS
        
        active_sports = []
        for sport in SPORTS:
            if self.is_peak_hour(sport):
                active_sports.append(sport)
        
        if active_sports:
            return True, f"Peak hours for: {', '.join(active_sports)}"
        else:
            # Calculate when next peak window opens
            next_times = []
            for sport in SPORTS:
                next_time = self.get_next_peak_time(sport)
                if next_time:
                    next_times.append(f"{sport}: {next_time}")
            
            reason = "Off-peak hours. Next windows: " + " | ".join(next_times) if next_times else "Off-peak"
            return False, reason


# Singleton instance
peak_scheduler = PeakHoursScheduler()
