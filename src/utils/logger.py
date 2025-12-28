"""
Structured logging utility for arbitrage monitoring
"""
import logging
import sys
from datetime import datetime
from config.settings import LOG_LEVEL, LOG_FILE


def setup_logger(name: str = 'arbitrage_monitor') -> logging.Logger:
    """
    Configure and return a logger with both file and console handlers
    
    Args:
        name: Logger name
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, LOG_LEVEL))
    
    # Avoid duplicate handlers if logger already configured
    if logger.handlers:
        return logger
    
    # Format: [2025-12-28 14:30:00] INFO - Message
    formatter = logging.Formatter(
        '[%(asctime)s] %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # File handler
    file_handler = logging.FileHandler(LOG_FILE)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    return logger


def log_api_request(logger: logging.Logger, sport: str, requests_made: int, quota_remaining: int):
    """Log API request with quota tracking"""
    logger.info(f"API Request: {sport} | Total Requests: {requests_made} | Quota Remaining: {quota_remaining}")


def log_arbitrage_opportunity(logger: logging.Logger, event: str, roi: float, bookmakers: list):
    """Log detected arbitrage opportunity"""
    logger.warning(f"🚨 ARB FOUND: {event} | ROI: {roi:.2f}% | Bookmakers: {', '.join(bookmakers)}")


def log_filtered_opportunity(logger: logging.Logger, reason: str, event: str, roi: float):
    """Log filtered/rejected arbitrage"""
    logger.info(f"FILTERED ({reason}): {event} | ROI: {roi:.2f}%")
