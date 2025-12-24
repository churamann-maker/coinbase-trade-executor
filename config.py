"""
Configuration Management for Coinbase Trading Bot

This module handles:
- Loading API credentials from environment variables
- Validating configuration settings
- Providing safe defaults for optional settings
"""

import os
import sys
from dataclasses import dataclass
from dotenv import load_dotenv


@dataclass
class TradingConfig:
    """
    Configuration container for the trading bot.

    Attributes:
        api_key: Coinbase Advanced Trade API key
        api_secret: Coinbase Advanced Trade API secret
        trading_mode: 'live' for real trades, 'dry_run' for simulation
        max_order_usd: Maximum allowed order size in USD (safety limit)
        trading_pair: The trading pair to use (e.g., 'BTC-USD')
    """
    api_key: str
    api_secret: str
    trading_mode: str
    max_order_usd: float
    trading_pair: str

    @property
    def is_dry_run(self) -> bool:
        """Returns True if running in dry run (simulation) mode."""
        return self.trading_mode.lower() != 'live'


def load_config() -> TradingConfig:
    """
    Load configuration from environment variables.

    This function:
    1. Loads variables from .env file (if it exists)
    2. Validates that required credentials are present
    3. Returns a TradingConfig object with all settings

    Returns:
        TradingConfig: Configuration object with all settings

    Raises:
        SystemExit: If required credentials are missing
    """
    # Load environment variables from .env file
    # This won't override existing environment variables
    load_dotenv()

    # Get API credentials (required)
    api_key = os.getenv('COINBASE_API_KEY', '')
    api_secret = os.getenv('COINBASE_API_SECRET', '')

    # Validate that credentials are provided
    if not api_key or api_key == 'your_api_key_here':
        print("ERROR: COINBASE_API_KEY not set or still has placeholder value")
        print("Please copy .env.example to .env and add your API credentials")
        sys.exit(1)

    if not api_secret or api_secret == 'your_api_secret_here':
        print("ERROR: COINBASE_API_SECRET not set or still has placeholder value")
        print("Please copy .env.example to .env and add your API credentials")
        sys.exit(1)

    # Get optional settings with safe defaults
    trading_mode = os.getenv('TRADING_MODE', 'dry_run')
    max_order_usd = float(os.getenv('MAX_ORDER_USD', '50.0'))
    trading_pair = os.getenv('TRADING_PAIR', 'BTC-USD')

    # Safety check: warn if max order is unusually high
    if max_order_usd > 100:
        print(f"WARNING: MAX_ORDER_USD is set to ${max_order_usd:.2f}")
        print("This is higher than recommended for testing. Are you sure?")

    return TradingConfig(
        api_key=api_key,
        api_secret=api_secret,
        trading_mode=trading_mode,
        max_order_usd=max_order_usd,
        trading_pair=trading_pair
    )


def print_config_summary(config: TradingConfig) -> None:
    """
    Print a summary of the current configuration (without exposing secrets).

    Args:
        config: The TradingConfig object to summarize
    """
    # Mask the API key for security (show only first/last 4 chars)
    masked_key = f"{config.api_key[:4]}...{config.api_key[-4:]}" if len(config.api_key) > 8 else "****"

    print("\n" + "=" * 50)
    print("CONFIGURATION SUMMARY")
    print("=" * 50)
    print(f"API Key:        {masked_key}")
    print(f"Trading Mode:   {config.trading_mode.upper()}")
    print(f"Trading Pair:   {config.trading_pair}")
    print(f"Max Order:      ${config.max_order_usd:.2f}")

    if config.is_dry_run:
        print("\n[DRY RUN MODE] No real trades will be executed")
    else:
        print("\n[LIVE MODE] Real trades WILL be executed!")
    print("=" * 50 + "\n")
