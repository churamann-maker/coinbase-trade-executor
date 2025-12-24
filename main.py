#!/usr/bin/env python3
"""
Coinbase Trading Bot - Main Entry Point

This script provides a command-line interface to:
- Run diagnostics to verify API setup
- Fetch current market data
- Execute test trades (in dry run or live mode)

Usage:
    python main.py                    # Interactive menu
    python main.py --diagnose         # Run diagnostics only
    python main.py --price            # Get current price
    python main.py --buy 10           # Buy $10 of BTC
    python main.py --dry-run --buy 10 # Force dry run mode
"""

import argparse
import sys

from config import load_config, print_config_summary
from trading_bot import TradingBot


def print_banner():
    """Print a welcome banner."""
    print("""
    ╔═══════════════════════════════════════════════════════════╗
    ║       COINBASE ADVANCED TRADE BOT                         ║
    ║       A simple bot for learning the API                   ║
    ╚═══════════════════════════════════════════════════════════╝
    """)


def interactive_menu(bot: TradingBot):
    """
    Run an interactive menu for the trading bot.

    Args:
        bot: Initialized TradingBot instance
    """
    while True:
        print("\n" + "=" * 40)
        print("MAIN MENU")
        print("=" * 40)
        print("1. Run diagnostics")
        print("2. Get current BTC price")
        print("3. View order book")
        print("4. Check account balances")
        print("5. Place test buy order ($10)")
        print("6. Place custom buy order")
        print("0. Exit")
        print("=" * 40)

        choice = input("\nEnter your choice: ").strip()

        if choice == '0':
            print("\nGoodbye!")
            break

        elif choice == '1':
            print("\nRunning diagnostics...")
            bot.run_diagnostics()

        elif choice == '2':
            price = bot.get_current_price()
            if price:
                print(f"\nCurrent BTC-USD price: ${price:,.2f}")

        elif choice == '3':
            print("\nFetching order book...")
            order_book = bot.get_order_book(limit=10)
            if order_book:
                print("\n--- TOP 10 BIDS (Buy Orders) ---")
                for i, bid in enumerate(order_book['bids'], 1):
                    print(f"  {i}. ${bid['price']:,.2f} - {bid['size']:.8f} BTC")

                print("\n--- TOP 10 ASKS (Sell Orders) ---")
                for i, ask in enumerate(order_book['asks'], 1):
                    print(f"  {i}. ${ask['price']:,.2f} - {ask['size']:.8f} BTC")

        elif choice == '4':
            print("\nFetching balances...")
            usd = bot.get_account_balance('USD')
            btc = bot.get_account_balance('BTC')
            print(f"\n  USD: ${usd:.2f}" if usd else "\n  USD: Not available")
            print(f"  BTC: {btc:.8f}" if btc else "  BTC: Not available")

        elif choice == '5':
            # Fixed $10 test order
            confirm = input(
                f"\nPlace a $10 buy order? "
                f"({'DRY RUN' if bot.config.is_dry_run else 'LIVE'})\n"
                f"Type 'yes' to confirm: "
            ).strip().lower()

            if confirm == 'yes':
                result = bot.place_market_buy(10.0)
                if result:
                    print("\nOrder completed successfully!")
            else:
                print("\nOrder cancelled.")

        elif choice == '6':
            # Custom order amount
            try:
                amount = float(input("\nEnter USD amount: $").strip())

                if amount > bot.config.max_order_usd:
                    print(f"\nAmount exceeds maximum (${bot.config.max_order_usd})")
                    print("Edit MAX_ORDER_USD in .env to increase limit")
                    continue

                confirm = input(
                    f"\nPlace a ${amount:.2f} buy order? "
                    f"({'DRY RUN' if bot.config.is_dry_run else 'LIVE'})\n"
                    f"Type 'yes' to confirm: "
                ).strip().lower()

                if confirm == 'yes':
                    result = bot.place_market_buy(amount)
                    if result:
                        print("\nOrder completed successfully!")
                else:
                    print("\nOrder cancelled.")

            except ValueError:
                print("\nInvalid amount. Please enter a number.")

        else:
            print("\nInvalid choice. Please try again.")


def main():
    """Main entry point for the trading bot."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description='Coinbase Advanced Trade Bot',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                    Interactive menu
  python main.py --diagnose         Run diagnostics
  python main.py --price            Show current BTC price
  python main.py --buy 10           Buy $10 of BTC
  python main.py --dry-run --buy 10 Force dry run mode
        """
    )

    parser.add_argument(
        '--diagnose', '-d',
        action='store_true',
        help='Run diagnostics and exit'
    )

    parser.add_argument(
        '--price', '-p',
        action='store_true',
        help='Get current BTC price and exit'
    )

    parser.add_argument(
        '--orderbook', '-o',
        action='store_true',
        help='Show order book and exit'
    )

    parser.add_argument(
        '--buy', '-b',
        type=float,
        metavar='AMOUNT',
        help='Place a market buy order for specified USD amount'
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Force dry run mode (override .env setting)'
    )

    parser.add_argument(
        '--live',
        action='store_true',
        help='Force live mode (override .env setting) - USE WITH CAUTION!'
    )

    args = parser.parse_args()

    # Print banner
    print_banner()

    # Load configuration
    try:
        config = load_config()
    except SystemExit:
        print("\nConfiguration error. Please check your .env file.")
        sys.exit(1)

    # Override trading mode if specified
    if args.dry_run:
        config.trading_mode = 'dry_run'
        print("[OVERRIDE] Forcing DRY RUN mode")
    elif args.live:
        config.trading_mode = 'live'
        print("[OVERRIDE] Forcing LIVE mode - Real trades will execute!")

    # Print configuration summary
    print_config_summary(config)

    # Initialize bot
    try:
        bot = TradingBot(config)
    except Exception as e:
        print(f"\nFailed to initialize bot: {e}")
        sys.exit(1)

    # Handle command line arguments
    if args.diagnose:
        success = bot.run_diagnostics()
        sys.exit(0 if success else 1)

    if args.price:
        price = bot.get_current_price()
        sys.exit(0 if price else 1)

    if args.orderbook:
        book = bot.get_order_book()
        if book:
            print("\n--- BIDS ---")
            for bid in book['bids']:
                print(f"  ${bid['price']:,.2f} - {bid['size']:.8f} BTC")
            print("\n--- ASKS ---")
            for ask in book['asks']:
                print(f"  ${ask['price']:,.2f} - {ask['size']:.8f} BTC")
        sys.exit(0 if book else 1)

    if args.buy is not None:
        # Require confirmation for buy orders
        mode_str = "DRY RUN" if config.is_dry_run else "LIVE"
        print(f"\nYou are about to place a ${args.buy:.2f} buy order ({mode_str})")

        if not config.is_dry_run:
            print("\nWARNING: This is a LIVE order with REAL money!")

        confirm = input("Type 'yes' to confirm: ").strip().lower()

        if confirm == 'yes':
            result = bot.place_market_buy(args.buy)
            sys.exit(0 if result else 1)
        else:
            print("Order cancelled.")
            sys.exit(0)

    # No specific command - run interactive menu
    interactive_menu(bot)


if __name__ == '__main__':
    main()
