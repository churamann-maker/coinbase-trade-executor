# Coinbase Trading Bot

A Python trading bot for the Coinbase Advanced Trade API. Designed for learning the API mechanics before building more complex trading strategies.

## Features

- Authenticate with Coinbase Advanced Trade API
- Fetch real-time market data (price, order book)
- Execute market buy orders with safety checks
- Dry run mode for testing without real trades
- Comprehensive logging to console and file
- Maximum order limit to prevent accidental large trades

## Getting Coinbase API Keys

1. **Log in to Coinbase**: Go to [coinbase.com](https://www.coinbase.com) and sign in

2. **Navigate to API Settings**:
   - Click your profile icon (top right)
   - Go to **Settings** > **API**
   - Or go directly to: https://www.coinbase.com/settings/api

3. **Create a New API Key**:
   - Click **"New API Key"**
   - Give it a nickname (e.g., "Trading Bot")

4. **Set Permissions** (minimum required):
   - `wallet:accounts:read` - View account balances
   - `wallet:orders:read` - View orders
   - `wallet:orders:create` - Create orders (needed for trading)
   - `wallet:trades:read` - View trade history

5. **Complete 2FA Verification**

6. **Save Your Credentials**:
   - **API Key**: Displayed after creation
   - **API Secret**: Shown ONCE - copy it immediately!

   Store these securely. You cannot retrieve the secret later.

## Setup

### 1. Clone and Navigate

```bash
cd coinbase-trade-executor
```

### 2. Create Virtual Environment

```bash
python -m venv venv

# On Linux/Mac:
source venv/bin/activate

# On Windows:
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure API Credentials

```bash
# Copy the example config
cp .env.example .env

# Edit .env with your credentials
nano .env  # or use your preferred editor
```

Update `.env` with your actual API credentials:

```
COINBASE_API_KEY=your_actual_api_key
COINBASE_API_SECRET=your_actual_api_secret
TRADING_MODE=dry_run
MAX_ORDER_USD=50.0
TRADING_PAIR=BTC-USD
```

**Important**: Never commit `.env` to version control!

## Usage

### Interactive Mode

Run without arguments for an interactive menu:

```bash
python main.py
```

### Command Line Options

```bash
# Run diagnostics to verify setup
python main.py --diagnose

# Get current BTC price
python main.py --price

# View order book
python main.py --orderbook

# Place a $10 buy order (uses mode from .env)
python main.py --buy 10

# Force dry run mode
python main.py --dry-run --buy 10

# Force live mode (caution!)
python main.py --live --buy 10
```

### Trading Modes

- **Dry Run** (`TRADING_MODE=dry_run`): Simulates orders without real trades. Perfect for testing.
- **Live** (`TRADING_MODE=live`): Executes real orders with real money.

**Always start with dry run mode!**

## Project Structure

```
coinbase-trade-executor/
├── main.py           # Entry point with CLI and interactive menu
├── trading_bot.py    # Core bot logic (API calls, order execution)
├── config.py         # Configuration and credential management
├── requirements.txt  # Python dependencies
├── .env.example      # Template for credentials
├── .env              # Your credentials (gitignored)
├── .gitignore        # Files to exclude from git
├── logs/             # Log files (gitignored)
└── README.md         # This file
```

## Safety Features

1. **Maximum Order Limit**: Orders exceeding `MAX_ORDER_USD` are rejected
2. **Dry Run Mode**: Test without real money
3. **Confirmation Prompts**: All orders require explicit confirmation
4. **Balance Checks**: Verifies sufficient funds before live orders
5. **Credential Validation**: Tests API keys before allowing trades

## Logging

Logs are written to:
- **Console**: INFO level and above
- **File**: DEBUG level (more detailed) in `logs/` directory

Example log output:
```
2024-01-15 10:30:45 | INFO     | Fetching current price for BTC-USD
2024-01-15 10:30:46 | INFO     | Current BTC-USD price: $43,250.00
```

## Example Session

```bash
$ python main.py --diagnose

    ╔═══════════════════════════════════════════════════════════╗
    ║       COINBASE ADVANCED TRADE BOT                         ║
    ╚═══════════════════════════════════════════════════════════╝

==================================================
CONFIGURATION SUMMARY
==================================================
API Key:        abc1...xyz9
Trading Mode:   DRY_RUN
Trading Pair:   BTC-USD
Max Order:      $50.00

[DRY RUN MODE] No real trades will be executed
==================================================

==================================================
RUNNING DIAGNOSTICS
==================================================

[Test 1/4] Validating credentials...
PASSED: Credentials are valid

[Test 2/4] Fetching price data...
PASSED: Price fetched ($43,250.00)

[Test 3/4] Fetching order book...
PASSED: Order book fetched

[Test 4/4] Fetching account balance...
PASSED: USD balance is $100.00

==================================================
ALL DIAGNOSTICS PASSED
Your bot is ready to trade!
==================================================
```

## Troubleshooting

### "Credential validation failed"
- Verify API key and secret are correct
- Check that required permissions are enabled
- Ensure your IP isn't blocked (if using IP allowlist)

### "Insufficient USD balance"
- Deposit funds to your Coinbase account
- Check that you're looking at the right account (Advanced Trade vs regular)

### "Order amount exceeds maximum"
- Increase `MAX_ORDER_USD` in `.env`
- This is a safety feature to prevent large accidental orders

## Disclaimer

This bot is for educational purposes. Cryptocurrency trading involves significant risk. Only trade what you can afford to lose. Test thoroughly in dry run mode before using live trading.

## License

MIT
