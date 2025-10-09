# CS2 Inventory Tracker

A Python script that fetches and tracks Counter-Strike 2 (CS2) inventory items from Steam profiles using BeautifulSoup4.

## Features

- Fetches all CS2 inventory items from public Steam profiles
- Uses Steam's official inventory API for reliable data
- Displays items grouped by type (weapons, cases, stickers, etc.)
- Shows tradable and marketable status for each item
- Saves inventory data to JSON format for further analysis
- Handles pagination for large inventories
- Includes proper error handling and user-friendly messages

## Requirements

- Python 3.6 or higher
- Internet connection
- Public Steam inventory (the profile must be set to public)

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

## Usage

### Basic Usage (Default Profile)

Run the script with the default profile URL:
```bash
python fetch_inventory.py
```

This will fetch inventory from: `https://steamcommunity.com/id/farhankarim/inventory`

### Custom Profile URL

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

## Troubleshooting

### "Inventory is private"
Make sure your Steam inventory is set to public:
1. Go to your Steam profile
2. Click "Edit Profile"
3. Go to "Privacy Settings"
4. Set "Inventory" to "Public"

### "Could not extract Steam ID"
- Ensure the profile URL is correct and accessible
- The profile should be in one of these formats:
  - `https://steamcommunity.com/id/vanity-url`
  - `https://steamcommunity.com/profiles/76561198XXXXXXXXX`

### "No items found"
- Verify that you have CS2 items in your inventory
- Make sure your inventory is public
- Check your internet connection

## Technical Details

The script uses:
- **BeautifulSoup4**: For HTML parsing (fallback method)
- **Requests**: For HTTP requests to Steam
- **Steam Inventory API**: Primary method for fetching inventory data
- **CS2 App ID**: 730 (same as CS:GO)

The script first attempts to extract the Steam ID from the profile URL, then uses Steam's official inventory API to fetch all items with pagination support.

## License

MIT License - Feel free to use and modify this script.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Disclaimer

This tool is for personal use only. Be respectful of Steam's servers and don't abuse the API. The script includes rate limiting to be nice to Steam's infrastructure.