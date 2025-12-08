"""
Logging utilities for AI Virtual Photographer.

Provides consistent logging configuration across all agents and services.
"""

import logging
import sys
from typing import Optional


def setup_logger(
    name: str,
    level: int = logging.INFO,
    format_string: Optional[str] = None
) -> logging.Logger:
    """
    Create and configure a logger with consistent formatting.
    
    Args:
        name: Logger name (typically __name__ of the calling module)
        level: Logging level (default: INFO)
        format_string: Custom format string (optional)
    
    Returns:
        Configured logger instance
    
    Example:
        >>> logger = setup_logger(__name__)
        >>> logger.info("Processing garment image...")
    """
    logger = logging.getLogger(name)
    
    # Avoid adding duplicate handlers
    if logger.handlers:
        return logger
    
    logger.setLevel(level)
    
    # Create console handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)
    
    # Set format
    if format_string is None:
        format_string = (
            "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
        )
    
    formatter = logging.Formatter(format_string, datefmt="%Y-%m-%d %H:%M:%S")
    handler.setFormatter(formatter)
    
    logger.addHandler(handler)
    
    return logger


# Pre-configured loggers for each component
def get_agent_logger(agent_name: str) -> logging.Logger:
    """
    Get a logger specifically for an agent.
    
    Args:
        agent_name: Name of the agent (e.g., "GarmentUnderstanding")
    
    Returns:
        Logger configured for agent use
    """
    return setup_logger(f"agent.{agent_name}")


def get_service_logger(service_name: str) -> logging.Logger:
    """
    Get a logger specifically for a service.
    
    Args:
        service_name: Name of the service (e.g., "GeminiClient")
    
    Returns:
        Logger configured for service use
    """
    return setup_logger(f"service.{service_name}")
