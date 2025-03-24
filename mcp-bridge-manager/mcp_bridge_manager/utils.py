"""
Utility functions for the MCP Bridge Manager.
"""
import logging
import time
from typing import Callable, Any, Dict

logger = logging.getLogger(__name__)

def sanitize_logs(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Remove sensitive information from log data.
    
    Args:
        data: Dictionary containing data to be logged
        
    Returns:
        Dictionary with sensitive values replaced by "***"
    """
    sensitive_keys = ["apiKey", "api-key", "password", "token", "secret", "key"]
    sanitized = {}
    
    for key, value in data.items():
        if isinstance(value, dict):
            sanitized[key] = sanitize_logs(value)
        elif any(sensitive in key.lower() for sensitive in sensitive_keys):
            sanitized[key] = "***" 
        else:
            sanitized[key] = value
            
    return sanitized

def retry_on_exception(
    func: Callable, 
    max_retries: int = 3, 
    delay: int = 2, 
    backoff: int = 2,
    allowed_exceptions: tuple = Exception
) -> Any:
    """
    Retry a function call when specific exceptions occur.
    
    Args:
        func: Function to retry
        max_retries: Maximum number of retry attempts
        delay: Initial delay between retries (in seconds)
        backoff: Backoff multiplier for increasing delay between retries
        allowed_exceptions: Tuple of exceptions that should trigger a retry
        
    Returns:
        Result of the function call
        
    Raises:
        Exception: The last exception encountered after max_retries
    """
    retries = 0
    while True:
        try:
            return func()
        except allowed_exceptions as e:
            retries += 1
            if retries >= max_retries:
                logger.error(f"Max retries ({max_retries}) exceeded: {str(e)}")
                raise
            
            sleep_time = delay * (backoff ** (retries - 1))
            logger.warning(f"Retry {retries}/{max_retries} after {sleep_time}s due to: {str(e)}")
            time.sleep(sleep_time)