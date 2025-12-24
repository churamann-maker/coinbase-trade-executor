"""
Coinbase Advanced Trade API Trading Bot

This module provides a TradingBot class that:
- Connects to Coinbase Advanced Trade API
- Fetches market data (price, order book)
- Executes trades with safety checks
- Supports dry run mode for testing
"""

import logging
import os
import sys
import uuid
from datetime import datetime
from typing import Optional

from coinbase.rest import RESTClient

from config import TradingConfig


def setup_logging(log_to_file: bool = True) -> logging.Logger:
    """
    Set up logging to both console and file.

    Args:
        log_to_file: If True, also log to a file in the logs/ directory

    Returns:
        logging.Logger: Configured logger instance
    """
    # Create logger
    logger = logging.getLogger('trading_bot')
    logger.setLevel(logging.DEBUG)

    # Clear any existing handlers (prevents duplicate logs)
    logger.handlers.clear()

    # Create formatter with timestamp
    formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Console handler - shows DEBUG and above
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler - shows DEBUG and above (more detailed)
    if log_to_file:
        # Create logs directory if it doesn't exist
        os.makedirs('logs', exist_ok=True)

        # Create log file with timestamp
        log_filename = f"logs/trading_bot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        file_handler = logging.FileHandler(log_filename)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        logger.info(f"Logging to file: {log_filename}")

    return logger


class TradingBot:
    """
    Trading bot for Coinbase Advanced Trade API.

    This class handles:
    - API authentication and connection
    - Market data retrieval
    - Order execution with safety checks
    - Dry run simulation mode

    Example usage:
        config = load_config()
        bot = TradingBot(config)
        if bot.validate_credentials():
            price = bot.get_current_price()
            order_book = bot.get_order_book()
            bot.place_market_buy(10.0)  # Buy $10 of BTC
    """

    def __init__(self, config: TradingConfig):
        """
        Initialize the trading bot.

        Args:
            config: TradingConfig object with API credentials and settings
        """
        self.config = config
        self.logger = setup_logging()
        self.client: Optional[RESTClient] = None

        self.logger.info("Initializing Coinbase Trading Bot")
        self.logger.info(f"Trading pair: {config.trading_pair}")
        self.logger.info(f"Mode: {'DRY RUN' if config.is_dry_run else 'LIVE'}")

        # Initialize the Coinbase client
        self._init_client()

    def _init_client(self) -> None:
        """
        Initialize the Coinbase REST client with API credentials.

        The client handles:
        - JWT authentication (automatically)
        - Request signing
        - Rate limiting
        """
        try:
            self.client = RESTClient(
                api_key=self.config.api_key,
                api_secret=self.config.api_secret
            )
            self.logger.debug("Coinbase REST client initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize client: {e}")
            raise

    def validate_credentials(self) -> bool:
        """
        Validate that API credentials are working by making a test API call.

        This fetches account information to verify:
        - API key is valid
        - API secret is correct
        - Required permissions are granted

        Returns:
            bool: True if credentials are valid, False otherwise
        """
        self.logger.info("Validating API credentials...")

        try:
            # Try to get accounts - this requires valid credentials
            accounts = self.client.get_accounts()

            # Check if we got a valid response
            if accounts and hasattr(accounts, 'accounts'):
                account_count = len(accounts.accounts) if accounts.accounts else 0
                self.logger.info(f"Credentials valid! Found {account_count} account(s)")

                # Log account summaries (without sensitive data)
                for account in accounts.accounts[:5]:  # Show first 5
                    self.logger.debug(
                        f"  Account: {account.currency} - "
                        f"Available: {account.available_balance.value}"
                    )

                return True
            else:
                self.logger.error("Unexpected response format from API")
                return False

        except Exception as e:
            self.logger.error(f"Credential validation failed: {e}")
            self.logger.error("Please check your API key and secret")
            return False

    def get_current_price(self) -> Optional[float]:
        """
        Get the current market price for the configured trading pair.

        Uses the product ticker endpoint to get the latest trade price.

        Returns:
            float: Current price, or None if request fails
        """
        self.logger.info(f"Fetching current price for {self.config.trading_pair}")

        try:
            # Get product information which includes current price
            product = self.client.get_product(self.config.trading_pair)

            if product:
                price = float(product.price)
                self.logger.info(f"Current {self.config.trading_pair} price: ${price:,.2f}")
                return price
            else:
                self.logger.error("No product data received")
                return None

        except Exception as e:
            self.logger.error(f"Failed to get price: {e}")
            return None

    def get_order_book(self, limit: int = 10) -> Optional[dict]:
        """
        Get the current order book (bids and asks) for the trading pair.

        The order book shows:
        - Bids: Buy orders waiting to be filled (sorted high to low)
        - Asks: Sell orders waiting to be filled (sorted low to high)

        Args:
            limit: Number of price levels to retrieve (default: 10)

        Returns:
            dict: Order book with 'bids' and 'asks' lists, or None if fails
        """
        self.logger.info(f"Fetching order book for {self.config.trading_pair}")

        try:
            # Get order book from API
            order_book = self.client.get_product_book(
                product_id=self.config.trading_pair,
                limit=limit
            )

            if order_book and hasattr(order_book, 'pricebook'):
                pricebook = order_book.pricebook

                # Parse bids and asks
                bids = []
                asks = []

                if hasattr(pricebook, 'bids') and pricebook.bids:
                    for bid in pricebook.bids[:limit]:
                        bids.append({
                            'price': float(bid.price),
                            'size': float(bid.size)
                        })

                if hasattr(pricebook, 'asks') and pricebook.asks:
                    for ask in pricebook.asks[:limit]:
                        asks.append({
                            'price': float(ask.price),
                            'size': float(ask.size)
                        })

                # Log summary
                if bids:
                    self.logger.info(f"Best bid: ${bids[0]['price']:,.2f}")
                if asks:
                    self.logger.info(f"Best ask: ${asks[0]['price']:,.2f}")
                if bids and asks:
                    spread = asks[0]['price'] - bids[0]['price']
                    spread_pct = (spread / asks[0]['price']) * 100
                    self.logger.info(f"Spread: ${spread:.2f} ({spread_pct:.4f}%)")

                return {'bids': bids, 'asks': asks}

            self.logger.warning("Empty order book received")
            return None

        except Exception as e:
            self.logger.error(f"Failed to get order book: {e}")
            return None

    def get_account_balance(self, currency: str = 'USD') -> Optional[float]:
        """
        Get the available balance for a specific currency.

        Args:
            currency: Currency code (e.g., 'USD', 'BTC')

        Returns:
            float: Available balance, or None if not found
        """
        self.logger.debug(f"Fetching {currency} balance")

        try:
            accounts = self.client.get_accounts()

            if accounts and accounts.accounts:
                for account in accounts.accounts:
                    if account.currency == currency:
                        balance = float(account.available_balance.value)
                        self.logger.info(f"{currency} balance: {balance}")
                        return balance

            self.logger.warning(f"No {currency} account found")
            return None

        except Exception as e:
            self.logger.error(f"Failed to get balance: {e}")
            return None

    def place_market_buy(self, usd_amount: float) -> Optional[dict]:
        """
        Place a market buy order for the configured trading pair.

        This method includes multiple safety checks:
        1. Validates amount is positive
        2. Checks against maximum order limit
        3. Verifies sufficient USD balance (in live mode)
        4. Simulates order in dry run mode

        Args:
            usd_amount: Amount in USD to spend on buying

        Returns:
            dict: Order details if successful, None if failed
        """
        self.logger.info(f"Preparing market buy order: ${usd_amount:.2f}")

        # ===== SAFETY CHECK 1: Positive amount =====
        if usd_amount <= 0:
            self.logger.error("Order amount must be positive")
            return None

        # ===== SAFETY CHECK 2: Maximum order limit =====
        if usd_amount > self.config.max_order_usd:
            self.logger.error(
                f"Order amount ${usd_amount:.2f} exceeds maximum "
                f"allowed ${self.config.max_order_usd:.2f}"
            )
            self.logger.error("Increase MAX_ORDER_USD in .env if this was intentional")
            return None

        # ===== SAFETY CHECK 3: Minimum order size =====
        # Coinbase has minimum order sizes (usually ~$1 for BTC-USD)
        if usd_amount < 1.0:
            self.logger.error("Order amount must be at least $1.00")
            return None

        # ===== DRY RUN MODE: Simulate the order =====
        if self.config.is_dry_run:
            return self._simulate_market_buy(usd_amount)

        # ===== LIVE MODE: Execute real order =====
        return self._execute_market_buy(usd_amount)

    def _simulate_market_buy(self, usd_amount: float) -> dict:
        """
        Simulate a market buy order (dry run mode).

        This fetches real market data to provide realistic simulation.

        Args:
            usd_amount: Amount in USD to spend

        Returns:
            dict: Simulated order details
        """
        self.logger.info("[DRY RUN] Simulating market buy order...")

        # Get current price for realistic simulation
        current_price = self.get_current_price()
        if not current_price:
            current_price = 0.0

        # Calculate simulated fill
        estimated_quantity = usd_amount / current_price if current_price > 0 else 0
        base_currency = self.config.trading_pair.split('-')[0]

        # Generate simulated order details
        simulated_order = {
            'order_id': f"DRY-RUN-{uuid.uuid4().hex[:8].upper()}",
            'product_id': self.config.trading_pair,
            'side': 'BUY',
            'type': 'MARKET',
            'status': 'SIMULATED',
            'quote_size': f"{usd_amount:.2f}",
            'estimated_fill_price': f"{current_price:.2f}",
            'estimated_quantity': f"{estimated_quantity:.8f}",
            'timestamp': datetime.now().isoformat()
        }

        self.logger.info("=" * 50)
        self.logger.info("[DRY RUN] SIMULATED ORDER DETAILS")
        self.logger.info("=" * 50)
        self.logger.info(f"Order ID:       {simulated_order['order_id']}")
        self.logger.info(f"Product:        {simulated_order['product_id']}")
        self.logger.info(f"Side:           {simulated_order['side']}")
        self.logger.info(f"Amount:         ${usd_amount:.2f} USD")
        self.logger.info(f"Est. Price:     ${current_price:,.2f}")
        self.logger.info(f"Est. Quantity:  {estimated_quantity:.8f} {base_currency}")
        self.logger.info("=" * 50)
        self.logger.info("[DRY RUN] No real order was placed")

        return simulated_order

    def _execute_market_buy(self, usd_amount: float) -> Optional[dict]:
        """
        Execute a real market buy order.

        WARNING: This places a REAL order with REAL money!

        Args:
            usd_amount: Amount in USD to spend

        Returns:
            dict: Order details if successful, None if failed
        """
        self.logger.warning("=" * 50)
        self.logger.warning("EXECUTING LIVE MARKET ORDER")
        self.logger.warning("=" * 50)

        # Check USD balance before ordering
        usd_balance = self.get_account_balance('USD')
        if usd_balance is not None and usd_balance < usd_amount:
            self.logger.error(
                f"Insufficient USD balance: ${usd_balance:.2f} < ${usd_amount:.2f}"
            )
            return None

        try:
            # Generate a unique client order ID for idempotency
            client_order_id = str(uuid.uuid4())

            self.logger.info(f"Placing market buy order for ${usd_amount:.2f}...")

            # Place the market order
            # quote_size specifies the amount in quote currency (USD)
            order = self.client.market_order_buy(
                client_order_id=client_order_id,
                product_id=self.config.trading_pair,
                quote_size=str(usd_amount)
            )

            if order:
                self.logger.info("=" * 50)
                self.logger.info("ORDER PLACED SUCCESSFULLY")
                self.logger.info("=" * 50)

                order_details = {
                    'order_id': order.order_id if hasattr(order, 'order_id') else 'N/A',
                    'client_order_id': client_order_id,
                    'product_id': self.config.trading_pair,
                    'side': 'BUY',
                    'type': 'MARKET',
                    'quote_size': str(usd_amount),
                    'status': 'PLACED',
                    'timestamp': datetime.now().isoformat()
                }

                self.logger.info(f"Order ID:     {order_details['order_id']}")
                self.logger.info(f"Product:      {order_details['product_id']}")
                self.logger.info(f"Amount:       ${usd_amount:.2f} USD")
                self.logger.info("=" * 50)

                return order_details

            else:
                self.logger.error("Order returned empty response")
                return None

        except Exception as e:
            self.logger.error(f"Order execution failed: {e}")
            self.logger.error("Check your account balance and API permissions")
            return None

    def run_diagnostics(self) -> bool:
        """
        Run a full diagnostic check of the bot.

        This verifies:
        1. API credentials are valid
        2. Can fetch market data
        3. Can fetch order book
        4. Can check account balances

        Returns:
            bool: True if all checks pass, False otherwise
        """
        self.logger.info("=" * 50)
        self.logger.info("RUNNING DIAGNOSTICS")
        self.logger.info("=" * 50)

        all_passed = True

        # Test 1: Credentials
        self.logger.info("\n[Test 1/4] Validating credentials...")
        if not self.validate_credentials():
            self.logger.error("FAILED: Credential validation")
            all_passed = False
        else:
            self.logger.info("PASSED: Credentials are valid")

        # Test 2: Price data
        self.logger.info("\n[Test 2/4] Fetching price data...")
        price = self.get_current_price()
        if price is None:
            self.logger.error("FAILED: Could not fetch price")
            all_passed = False
        else:
            self.logger.info(f"PASSED: Price fetched (${price:,.2f})")

        # Test 3: Order book
        self.logger.info("\n[Test 3/4] Fetching order book...")
        order_book = self.get_order_book(limit=5)
        if order_book is None:
            self.logger.error("FAILED: Could not fetch order book")
            all_passed = False
        else:
            self.logger.info("PASSED: Order book fetched")

        # Test 4: Account balance
        self.logger.info("\n[Test 4/4] Fetching account balance...")
        balance = self.get_account_balance('USD')
        if balance is None:
            self.logger.warning("WARNING: Could not fetch USD balance (may not have USD account)")
        else:
            self.logger.info(f"PASSED: USD balance is ${balance:.2f}")

        # Summary
        self.logger.info("\n" + "=" * 50)
        if all_passed:
            self.logger.info("ALL DIAGNOSTICS PASSED")
            self.logger.info("Your bot is ready to trade!")
        else:
            self.logger.error("SOME DIAGNOSTICS FAILED")
            self.logger.error("Please fix the issues above before trading")
        self.logger.info("=" * 50)

        return all_passed
