"""
Bookmaker Classification and Priority Tagging System
"""
from typing import Tuple, Optional
from config.settings import SHARP_BOOKMAKERS, SOFT_BOOKMAKERS


class BookmakerClassifier:
    """
    Classifies bookmaker pairs and assigns priority tags for Discord alerts
    
    Priority Logic:
    - Sharp vs Soft = [⭐ HIGH CONFIDENCE] - Most profitable, Sharp is always right
    - Soft vs Soft = [⚡ FAST MOVE] - Temporary pricing lag between slow movers
    - Sharp vs Sharp = Standard alert (rare arbitrage, both accurate)
    """
    
    def __init__(self):
        self.sharps = [b.lower() for b in SHARP_BOOKMAKERS]
        self.softs = [b.lower() for b in SOFT_BOOKMAKERS]
    
    def classify_bookmaker(self, bookmaker: str) -> str:
        """
        Classify a bookmaker as Sharp, Soft, or Unknown
        
        Args:
            bookmaker: Bookmaker key from API (e.g., 'pinnacle', 'unibet_us')
            
        Returns:
            'sharp', 'soft', or 'unknown'
        """
        # Clean bookmaker name (remove region suffix)
        clean_name = bookmaker.split('_')[0].lower()
        
        if clean_name in self.sharps:
            return 'sharp'
        elif clean_name in self.softs:
            return 'soft'
        else:
            return 'unknown'
    
    def get_priority_tag(self, bookmaker_a: str, bookmaker_b: str) -> Tuple[str, str, str]:
        """
        Determine priority tag for an arbitrage opportunity
        
        Args:
            bookmaker_a: First bookmaker
            bookmaker_b: Second bookmaker
            
        Returns:
            (tag_emoji, tag_text, explanation)
        """
        class_a = self.classify_bookmaker(bookmaker_a)
        class_b = self.classify_bookmaker(bookmaker_b)
        
        # Sharp vs Soft - Highest confidence
        if (class_a == 'sharp' and class_b == 'soft') or \
           (class_a == 'soft' and class_b == 'sharp'):
            return (
                '⭐',
                'HIGH CONFIDENCE',
                'Sharp bookmaker vs Soft bookmaker - High probability profit'
            )
        
        # Soft vs Soft - Fast move opportunity
        elif class_a == 'soft' and class_b == 'soft':
            return (
                '⚡',
                'FAST MOVE',
                'Both bookmakers are slow movers - Temporary pricing lag'
            )
        
        # Sharp vs Sharp - Rare but valid
        elif class_a == 'sharp' and class_b == 'sharp':
            return (
                '🔹',
                'SHARP ARB',
                'Rare arbitrage between market leaders - Act quickly'
            )
        
        # Unknown bookmakers
        else:
            return (
                '📊',
                'STANDARD',
                'Standard arbitrage opportunity'
            )
    
    def get_sharp_bookmaker(self, bookmaker_a: str, bookmaker_b: str) -> Optional[str]:
        """
        Identify which bookmaker is the Sharp (source of truth)
        
        Args:
            bookmaker_a, bookmaker_b: Bookmaker keys
            
        Returns:
            Sharp bookmaker name or None
        """
        class_a = self.classify_bookmaker(bookmaker_a)
        class_b = self.classify_bookmaker(bookmaker_b)
        
        if class_a == 'sharp':
            return bookmaker_a
        elif class_b == 'sharp':
            return bookmaker_b
        else:
            return None
    
    def get_betting_recommendation(self, bookmaker_a: str, bookmaker_b: str) -> str:
        """
        Generate betting recommendation based on bookmaker classification
        
        Returns:
            Recommendation text for Discord alert
        """
        sharp = self.get_sharp_bookmaker(bookmaker_a, bookmaker_b)
        
        if sharp:
            return (
                f"💡 **Pro Tip**: {sharp.split('_')[0].title()} is a Sharp bookmaker. "
                f"Their price is the market consensus. Bet the opposite side."
            )
        
        class_a = self.classify_bookmaker(bookmaker_a)
        class_b = self.classify_bookmaker(bookmaker_b)
        
        if class_a == 'soft' and class_b == 'soft':
            return (
                "⏱️ **Time Sensitive**: Both bookmakers are slow movers. "
                "This gap may close within 2-3 minutes."
            )
        
        return ""


# Singleton instance
bookmaker_classifier = BookmakerClassifier()
