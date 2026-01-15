"""Logging utilities for per-call log files."""
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict
import config


# Global registry of active call loggers
_loggers: Dict[str, 'CallLogger'] = {}


def get_or_create_logger(call_control_id: str, phone_number: str = None) -> 'CallLogger':
    """
    Get existing logger for a call or create a new one.
    Implements singleton pattern per call_control_id.
    
    Args:
        call_control_id: The call control ID
        phone_number: Caller's phone number (required for new loggers)
        
    Returns:
        CallLogger instance for this call
    """
    if call_control_id not in _loggers:
        if phone_number is None:
            raise ValueError(f"phone_number required to create new logger for {call_control_id}")
        _loggers[call_control_id] = CallLogger(call_control_id, phone_number)
    return _loggers[call_control_id]


def cleanup_logger(call_control_id: str) -> None:
    """
    Close and remove logger for a completed call.
    
    Args:
        call_control_id: The call control ID
    """
    if call_control_id in _loggers:
        _loggers[call_control_id].close()
        del _loggers[call_control_id]
        print(f"[Logger Registry] Cleaned up logger for call {call_control_id}")


class CallLogger:
    """Creates and manages per-call log files."""
    
    def __init__(self, call_control_id: str, phone_number: str):
        """
        Initialize a logger for a specific call.
        
        Args:
            call_control_id: The call control ID
            phone_number: Caller's phone number
        """
        self.call_control_id = call_control_id
        self.phone_number = phone_number
        
        # Create logs directory
        self.logs_dir = config.BASE_DIR / "logs"
        self.logs_dir.mkdir(exist_ok=True)
        
        # Generate log filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_number = phone_number.replace("+", "").replace(" ", "")
        filename = f"{timestamp}_{safe_number}_{call_control_id[:12]}.log"
        self.log_file = self.logs_dir / filename
        
        # Create logger
        self.logger = logging.getLogger(f"call_{call_control_id}")
        self.logger.setLevel(logging.DEBUG)  # Capture all levels, filter on output
        
        # Clear any existing handlers
        self.logger.handlers.clear()
        
        # File handler
        file_handler = logging.FileHandler(self.log_file)
        file_handler.setLevel(logging.INFO)
        
        # Format
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        
        self.logger.addHandler(file_handler)
        
        # Log call start
        self.logger.info("="*60)
        self.logger.info(f"CALL STARTED: {phone_number}")
        self.logger.info(f"Call Control ID: {call_control_id}")
        self.logger.info("="*60)
    
    def debug(self, message: str):
        """Log debug message."""
        self.logger.debug(message)
        if config.LOG_LEVEL == "DEBUG":
            print(f"[Call Log DEBUG] {message}")
    
    def info(self, message: str):
        """Log info message."""
        self.logger.info(message)
        # Also print to console
        print(f"[Call Log] {message}")
    
    def error(self, message: str):
        """Log error message."""
        self.logger.error(message)
        print(f"[Call Log ERROR] {message}")
    
    def success(self, message: str):
        """Log success message."""
        self.logger.info(f"✅ {message}")
        print(f"[Call Log] ✅ {message}")
    
    def close(self):
        """Close the logger."""
        self.logger.info("="*60)
        self.logger.info("CALL PROCESSING COMPLETED")
        self.logger.info("="*60)
        
        # Remove handlers
        for handler in self.logger.handlers:
            handler.close()
            self.logger.removeHandler(handler)
