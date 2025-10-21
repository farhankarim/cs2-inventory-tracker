# CS2 Inventory Tracker

A comprehensive Python toolkit for tracking Counter-Strike 2 (CS2) inventory items and Steam Market transactions.

## Features

### Inventory Tracker (`fetch_inventory.py`)
- Fetches all CS2 inventory items from public Steam profiles
- Uses Steam's official inventory API for reliable data
- Displays items grouped by type (weapons, cases, stickers, etc.)
- Shows tradable and marketable status for each item
- Saves inventory data to JSON format for further analysis

### Steam Market History Tracker (`inventory.py`)
- **NEW**: Fetches complete Steam Market purchase/sale history
- Tracks profit/loss for items bought and sold
- Detects items with stickers and includes sticker costs in calculations
- Groups transactions by type (bought only, sold only, bought & sold)
- Provides detailed financial summary with sticker cost analysis
- Exports data to CSV format for spreadsheet analysis
- Supports both Netscape cookie format and manual cookie strings

## Requirements

- Python 3.6 or higher
- Internet connection
- For inventory tracking: Public Steam inventory
- For market history: Valid Steam login cookies

## Installation

1. Clone this repository:
```bash
git clone https://github.com/farhankarim/cs2-inventory-tracker.git
cd cs2-inventory-tracker
```

2. Install the required dependencies:
```bash
pip install -r requirements.txt
```

### Quick Start (Linux/Mac)

For a quick automated setup, run:
```bash
chmod +x quickstart.sh
./quickstart.sh
```

## Usage

### Steam Market History Tracker

The market history tracker requires Steam authentication cookies to access your private transaction history.

#### Step 1: Extract Cookies

Install the **Get cookies.txt LOCALLY** Chrome extension:
[https://chromewebstore.google.com/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc](https://chromewebstore.google.com/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc?pli=1)

1. **Install the extension** from the Chrome Web Store
2. **Log into Steam** in your browser and navigate to Steam Market
3. **Click the extension icon** in your browser toolbar
4. **Select "steamcommunity.com"** from the dropdown
5. **Save the cookies** to a file named `cookie.txt` in your project directory

#### Step 2: Run Market History Analysis

```bash
# Using cookie file (recommended)
python inventory.py --cookie-file cookie.txt

# Output to custom file
python inventory.py --cookie-file cookie.txt --output my_trades.csv

# Limit to first 5 pages for testing
python inventory.py --cookie-file cookie.txt --max-pages 5

# Get raw JSON data instead of CSV
python inventory.py --cookie-file cookie.txt --json > raw_data.json
```

#### Market History Features

- **Profit/Loss Calculation**: Automatically pairs bought and sold items using FIFO (First In, First Out)
- **Sticker Cost Tracking**: Identifies when you applied purchased stickers to items and adjusts profit calculations
- **Transaction Types**:
  - `Bought & Sold`: Complete transactions with profit/loss calculation
  - `Bought (Not Sold)`: Items you bought but haven't sold yet
  - `Sold (Not Bought)`: Items you sold but didn't originally purchase (e.g., drops, gifts)
  - `Sticker Bought/Sold`: Separate tracking for sticker transactions

#### Example Output

```
============================================================
TRANSACTION SUMMARY
============================================================

📈 BOUGHT & SOLD ITEMS: 5
   Total Profit/Loss (adjusted for sticker costs): $4.33
   Items:
   • AWP | Exoskeleton: $2.50 (Base: $4.03 - Stickers: $1.53) [Stickers: Spirit (Holo), donk]
   • AK-47 | Midnight Laminate: $0.00
   • M4A1-S | Nitro: $0.02

💰 BOUGHT ONLY (Not Sold): 8
   Total Investment: $23.45
   Items:
   • USP-S | Torque: $3.68 USD
   • AWP | Atheris: $3.70 USD

💸 SOLD ONLY (Not Previously Bought): 15
   Total Revenue: $45.67
   
🎯 STICKER TRANSACTIONS: 3
   Total Sticker Investment: $1.72

📊 OVERALL SUMMARY:
   Net Profit/Loss: $25.23
```

### Inventory Tracker (Original)

#### Basic Usage (Default Profile)

Run the script with the default profile URL:
```bash
python fetch_inventory.py
```

This will fetch inventory from: `https://steamcommunity.com/id/farhankarim/inventory`

#### Custom Profile URL

You can specify a different Steam profile URL as a command-line argument:
```bash
python fetch_inventory.py https://steamcommunity.com/id/your-steam-id/inventory
```

Or with a 64-bit Steam ID:
```bash
python fetch_inventory.py https://steamcommunity.com/profiles/76561198XXXXXXXXX/inventory
```

### Output

The script will:
1. Display all inventory items in the console, grouped by type
2. Show tradable and marketable status for each item
3. Save the complete inventory data to `inventory.json`

Example output:
```
================================================================================
CS2 INVENTORY - Total Items: 45
================================================================================

Base Grade Container (5 items):
--------------------------------------------------------------------------------
  • CS:GO Weapon Case
    Tradable: ✓ | Marketable: ✓

  • Chroma 3 Case
    Tradable: ✓ | Marketable: ✓
...
```

### JSON Output

The `inventory.json` file contains detailed information about each item:
```json
[
  {
    "asset_id": "123456789",
    "class_id": "987654321",
    "instance_id": "0",
    "amount": "1",
    "name": "AK-47 | Redline",
    "market_name": "AK-47 | Redline (Field-Tested)",
    "market_hash_name": "AK-47 | Redline (Field-Tested)",
    "type": "Rifle",
    "tradable": 1,
    "marketable": 1,
    "commodity": 0,
    "icon_url": "...",
    "name_color": "D2D2D2",
    "background_color": "",
    "tags": [...]
  }
]
```

## Advanced Usage

### Market History Options

```bash
# Custom delay between requests (default: 0.8 seconds)
python inventory.py --cookie-file cookie.txt --delay 1.5

# Using manual cookie string instead of file
python inventory.py --cookie "sessionid=abc123; steamLoginSecure=xyz789"

# Using environment variable
export STEAM_COOKIE="sessionid=abc123; steamLoginSecure=xyz789"
python inventory.py
```

### CSV Output Format

The market history CSV includes these columns:
- `name`: Item name
- `bought_price`: Purchase price (if applicable)
- `sold_price`: Sale price (if applicable)  
- `profit_loss`: Calculated profit/loss including sticker costs
- `transaction_type`: Type of transaction
- `stickers`: List of attached stickers
- `sticker_costs`: Individual sticker purchase costs

## Security Notes

### Cookie Safety
- **Never share your cookie file** - it contains sensitive authentication data
- **Add `cookie.txt` to `.gitignore`** to prevent accidental commits
- **Regenerate cookies periodically** by logging out and back into Steam
- **Use the browser extension method** rather than manual cookie extraction

### Rate Limiting
- The script includes automatic delays between requests
- Don't run multiple instances simultaneously
- Respect Steam's servers and terms of service

## Troubleshooting

### Market History Issues

**"Authentication failed" or receiving HTML instead of JSON:**
- Ensure your cookies are fresh (re-extract them)
- Make sure you're logged into Steam in the same browser
- Verify the cookie file format is correct

**"Debug: Using cookies: []":**
- Check that your cookie file is in the correct Netscape format
- Ensure the file path is correct
- Try re-extracting cookies with the browser extension

### Inventory Tracker Issues

**"Inventory is private":**
- Set your Steam inventory to public in Privacy Settings

**"Could not extract Steam ID":**
- Ensure the profile URL format is correct
- Profile should be accessible and public

## Technical Details

### Market History Tracker
- Uses Steam Community Market API endpoints
- Supports both start/count and page-based pagination
- Parses HTML responses for transaction details
- Extracts sticker information from asset metadata
- Handles Netscape cookie format automatically

### Inventory Tracker
- Uses Steam Inventory API (App ID: 730)
- BeautifulSoup4 for HTML parsing (fallback)
- Pagination support for large inventories

## License

MIT License - Feel free to use and modify this script.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Disclaimer

These tools are for personal use only. Be respectful of Steam's servers and don't abuse the APIs. The scripts include rate limiting to be nice to Steam's infrastructure.

**Important**: Always keep your authentication cookies secure and never share them with others.