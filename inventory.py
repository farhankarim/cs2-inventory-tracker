import argparse
import csv
import json
import os
import sys
import time
from typing import Dict, Optional, Tuple, List
import requests
import re

#!/usr/bin/env python3
"""
Fetch all pages of Steam Market purchase/sale history JSON and append into one variable `data`.

Usage:
    python inventory.py --cookie 'sessionid=...; steamLoginSecure=...; ...'
    # or set env STEAM_COOKIE and run without --cookie

Notes:
- Uses the same headers as your curl.
- Paginates over all available pages.
- Accumulates each page's JSON response into `data` (a list of dicts).
- Writes the combined JSON to stdout; redirect to a file if desired.
"""

import urllib.parse



BASE_URL = "https://steamcommunity.com/market/myhistory"


HEADERS = {
        "Accept": "text/javascript, text/html, application/xml, text/xml, */*",
        "Accept-Language": "en-US,en;q=0.9",
        "Connection": "keep-alive",
        "Referer": "https://steamcommunity.com/market/",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36",
        "X-Prototype-Version": "1.7",
        "X-Requested-With": "XMLHttpRequest",
        "sec-ch-ua": '"Google Chrome";v="141", "Not?A_Brand";v="8", "Chromium";v="141"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
}


def parse_cookie_str(cookie_str: str) -> Dict[str, str]:
        cookies: Dict[str, str] = {}
        for part in cookie_str.split(";"):
                part = part.strip()
                if not part or "=" not in part:
                        continue
                k, v = part.split("=", 1)
                cookies[k.strip()] = urllib.parse.unquote(v.strip())
        return cookies


def parse_netscape_cookies(filepath: str) -> Dict[str, str]:
        """Parse Netscape cookie file format."""
        cookies: Dict[str, str] = {}
        try:
                with open(filepath, 'r', encoding='utf-8') as f:
                        for line in f:
                                line = line.strip()
                                # Skip comments and empty lines
                                if not line or line.startswith('#'):
                                        continue
                                
                                # Netscape format: domain, domain_specified, path, secure, expires, name, value
                                parts = line.split('\t')
                                if len(parts) >= 7:
                                        name = parts[5]
                                        value = parts[6]
                                        cookies[name] = value
                return cookies
        except (IOError, OSError) as e:
                print(f"Error reading Netscape cookie file '{filepath}': {e}", file=sys.stderr)
                sys.exit(2)


def read_cookie_from_file(filepath: str) -> str:
        """Read cookie string from a file, detecting format automatically."""
        try:
                with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read().strip()
                
                # Check if it's Netscape format (starts with comment about Netscape)
                if content.startswith('# Netscape HTTP Cookie File') or '\t' in content:
                        # Parse as Netscape format and convert to cookie string
                        cookies_dict = parse_netscape_cookies(filepath)
                        # Convert to cookie string format
                        cookie_parts = [f"{k}={v}" for k, v in cookies_dict.items()]
                        return "; ".join(cookie_parts)
                else:
                        # Assume it's already in cookie string format
                        return content
                        
        except (IOError, OSError) as e:
                print(f"Error reading cookie file '{filepath}': {e}", file=sys.stderr)
                sys.exit(2)


def try_fetch_json(session: requests.Session, params: Dict[str, int]) -> Optional[dict]:
        r = session.get(BASE_URL, headers=HEADERS, params=params, timeout=30)
        r.raise_for_status()
        
        # Check content type - Steam returns HTML when not authenticated
        content_type = r.headers.get('content-type', '').lower()
        if 'text/html' in content_type:
                print(f"Error: Received HTML instead of JSON. This usually means authentication failed.", file=sys.stderr)
                print(f"Response content preview: {r.text[:200]}...", file=sys.stderr)
                return None
        
        try:
                return r.json()
        except ValueError as e:
                print(f"Error: Failed to parse JSON response. Content type: {content_type}", file=sys.stderr)
                print(f"Response preview: {r.text[:500]}...", file=sys.stderr)
                return None


def page_strategy_from_response(js: dict) -> Tuple[str, int, int]:
        """
        Decide pagination scheme based on first JSON:
        - If it exposes total_count/pagesize/start: use start/count pagination.
        - Else if it exposes total_pages/current_page: use page pagination.
        - Else fallback to page pagination with unknown total.
        Returns (mode, start_or_page, pagesize_or_count)
        mode in {"start_count", "page"}
        """
        total_count = js.get("total_count")
        pagesize = js.get("pagesize") or js.get("page_size")
        start = js.get("start")
        current_page = js.get("page") or js.get("current_page")
        total_pages = js.get("total_pages")

        if total_count is not None and (pagesize or js.get("count") or start is not None):
                # Prefer a reasonably large count if not given
                count = int(pagesize or js.get("count") or 100)
                start_val = int(start or 0)
                return ("start_count", start_val, count)

        # Default to page-based
        page = int(current_page or 1)
        # pagesize unknown here; not needed for page mode
        return ("page", page, 0)


def has_more_pages(js: dict, mode: str, cursor: int, step: int) -> bool:
        # If server tells us totals, use them
        if mode == "start_count":
                total_count = js.get("total_count")
                pagesize = js.get("pagesize") or js.get("page_size") or step
                start = js.get("start", cursor)
                if total_count is not None and pagesize:
                        return (start + pagesize) < int(total_count)
        else:
                total_pages = js.get("total_pages")
                current_page = js.get("page") or js.get("current_page") or cursor
                if total_pages is not None:
                        return int(current_page) < int(total_pages)

        # Fallback: if results_html present and non-empty, assume more until empty
        results_html = js.get("results_html") or js.get("html") or ""
        return bool(str(results_html).strip())


def extract_sticker_info(assets_data: dict, asset_id: str) -> List[str]:
        """Extract sticker information from assets data."""
        stickers = []
        try:
                # Navigate through the assets structure: assets -> 730 -> 2 -> asset_id
                if "730" in assets_data and "2" in assets_data["730"]:
                        asset_info = assets_data["730"]["2"].get(asset_id, {})
                        descriptions = asset_info.get("descriptions", [])
                        
                        for desc in descriptions:
                                if desc.get("name") == "sticker_info" and desc.get("value"):
                                        # Parse sticker info from HTML
                                        sticker_html = desc["value"]
                                        # Extract sticker names using regex
                                        sticker_pattern = r'title="Sticker: ([^"]+)"'
                                        sticker_matches = re.findall(sticker_pattern, sticker_html)
                                        stickers.extend(sticker_matches)
        except Exception as e:
                print(f"Debug: Error extracting stickers for asset {asset_id}: {e}", file=sys.stderr)
        
        return stickers


def extract_items_from_data(data: List[dict]) -> List[Dict[str, str]]:
        """Extract item name and price from the API response data."""
        items = []
        
        for page_data in data:
                # Check for results_html which contains the HTML with item data
                results_html = page_data.get("results_html", "")
                assets_data = page_data.get("assets", {})
                
                if not results_html:
                        continue
                
                # Parse HTML to extract item names and prices
                import re
                from html import unescape
                
                # Pattern to match each market listing row with row ID
                row_pattern = r'<div class="market_listing_row[^"]*"[^>]*id="([^"]*)"[^>]*>(.*?)</div>\s*<div style="clear: both"></div>'
                rows = re.findall(row_pattern, results_html, re.DOTALL)
                
                for row_id, row_content in rows:
                        # Extract asset ID from row ID (e.g., "history_row_123_456_789" -> extract asset reference)
                        asset_id_match = re.search(r'history_row_\d+_\d+', row_id)
                        asset_id = None
                        
                        # Try to find asset ID in the row content
                        asset_pattern = r'CreateItemHoverFromContainer[^,]*,\s*\'730\',\s*\'2\',\s*\'(\d+)\''
                        asset_match = re.search(asset_pattern, row_content)
                        if asset_match:
                                asset_id = asset_match.group(1)
                        
                        # Extract transaction type from market_listing_gainorloss
                        transaction_pattern = r'<div class="market_listing_left_cell market_listing_gainorloss"[^>]*>\s*([+-])\s*</div>'
                        transaction_match = re.search(transaction_pattern, row_content)
                        
                        # Extract item name from the market_listing_item_name span
                        name_pattern = r'<span[^>]*class="market_listing_item_name"[^>]*>([^<]+)</span>'
                        name_match = re.search(name_pattern, row_content)
                        
                        # Extract price from the market_listing_price span
                        price_pattern = r'<span class="market_listing_price"[^>]*>\s*(.*?)\s*</span>'
                        price_match = re.search(price_pattern, row_content)
                        
                        if name_match and price_match:
                                name = unescape(name_match.group(1).strip())
                                price_raw = unescape(price_match.group(1).strip())
                                # Clean price - remove extra whitespace and tabs, extract only the price
                                price_clean = re.sub(r'\s+', ' ', price_raw).strip()
                                # Extract numeric price (e.g., "$14.00 USD" -> "14.00")
                                price_numeric_match = re.search(r'\$?(\d+\.?\d*)', price_clean)
                                price_value = float(price_numeric_match.group(1)) if price_numeric_match else 0.0
                                
                                # Determine transaction type
                                transaction_type = "Unknown"
                                if transaction_match:
                                        symbol = transaction_match.group(1).strip()
                                        transaction_type = "Bought" if symbol == "+" else "Sold"
                                
                                # Extract sticker information
                                stickers = []
                                if asset_id:
                                        stickers = extract_sticker_info(assets_data, asset_id)
                                
                                items.append({
                                        "name": name, 
                                        "price": price_clean,
                                        "price_value": price_value,
                                        "transaction_type": transaction_type,
                                        "stickers": stickers,
                                        "has_stickers": len(stickers) > 0
                                })
        
        return items


def calculate_profit_loss(items: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Calculate profit/loss for items that were bought and then sold."""
        # Group transactions by item name
        item_transactions = {}
        sticker_purchases = {}  # Track sticker purchases separately
        
        for item in items:
                name = item["name"]
                
                # Track sticker purchases separately
                if "Sticker |" in name:
                        sticker_purchases[name] = item
                        continue
                
                if name not in item_transactions:
                        item_transactions[name] = {"bought": [], "sold": []}
                
                if item["transaction_type"] == "Bought":
                        item_transactions[name]["bought"].append(item)
                elif item["transaction_type"] == "Sold":
                        item_transactions[name]["sold"].append(item)
        
        # Calculate profit/loss for paired transactions
        result_items = []
        
        for name, transactions in item_transactions.items():
                bought_items = transactions["bought"]
                sold_items = transactions["sold"]
                
                # Pair bought and sold items (FIFO - first bought, first sold)
                pairs = min(len(bought_items), len(sold_items))
                
                for i in range(pairs):
                        bought_item = bought_items[i]
                        sold_item = sold_items[i]
                        
                        # Calculate base profit/loss
                        base_profit_loss = sold_item["price_value"] - bought_item["price_value"]
                        
                        # Combine sticker information
                        all_stickers = list(set(bought_item.get("stickers", []) + sold_item.get("stickers", [])))
                        stickers_str = ", ".join(all_stickers) if all_stickers else ""
                        
                        # Calculate sticker costs if item was sold with stickers
                        sticker_cost = 0.0
                        sticker_cost_details = []
                        
                        if sold_item.get("has_stickers", False):
                                for sticker_name in sold_item.get("stickers", []):
                                        # Look for matching sticker purchase
                                        sticker_key = f"Sticker | {sticker_name}"
                                        if sticker_key in sticker_purchases:
                                                sticker_price = sticker_purchases[sticker_key]["price_value"]
                                                sticker_cost += sticker_price
                                                sticker_cost_details.append(f"{sticker_name}: ${sticker_price:.2f}")
                        
                        # Adjust profit/loss by sticker costs
                        adjusted_profit_loss = base_profit_loss - sticker_cost
                        
                        # Format profit/loss display
                        if sticker_cost > 0:
                                profit_loss_str = f"${adjusted_profit_loss:.2f} (Base: ${base_profit_loss:.2f} - Stickers: ${sticker_cost:.2f})"
                        else:
                                profit_loss_str = f"${adjusted_profit_loss:.2f}"
                        
                        result_items.append({
                                "name": name,
                                "bought_price": bought_item["price"],
                                "sold_price": sold_item["price"],
                                "profit_loss": profit_loss_str,
                                "transaction_type": "Bought & Sold",
                                "stickers": stickers_str,
                                "sticker_costs": "; ".join(sticker_cost_details) if sticker_cost_details else "",
                                "has_stickers": len(all_stickers) > 0,
                                "adjusted_profit_value": adjusted_profit_loss  # For summary calculations
                        })
                
                # Add remaining unpaired transactions
                for i in range(pairs, len(bought_items)):
                        stickers_str = ", ".join(bought_items[i].get("stickers", []))
                        result_items.append({
                                "name": name,
                                "bought_price": bought_items[i]["price"],
                                "sold_price": "",
                                "profit_loss": "",
                                "transaction_type": "Bought (Not Sold)",
                                "stickers": stickers_str,
                                "sticker_costs": "",
                                "has_stickers": len(bought_items[i].get("stickers", [])) > 0,
                                "adjusted_profit_value": 0
                        })
                
                for i in range(pairs, len(sold_items)):
                        stickers_str = ", ".join(sold_items[i].get("stickers", []))
                        result_items.append({
                                "name": name,
                                "bought_price": "",
                                "sold_price": sold_items[i]["price"],
                                "profit_loss": "",
                                "transaction_type": "Sold (Not Bought)",
                                "stickers": stickers_str,
                                "sticker_costs": "",
                                "has_stickers": len(sold_items[i].get("stickers", [])) > 0,
                                "adjusted_profit_value": 0
                        })
        
        # Add sticker-only transactions to the results
        for sticker_name, sticker_item in sticker_purchases.items():
                result_items.append({
                        "name": sticker_name,
                        "bought_price": sticker_item["price"] if sticker_item["transaction_type"] == "Bought" else "",
                        "sold_price": sticker_item["price"] if sticker_item["transaction_type"] == "Sold" else "",
                        "profit_loss": "",
                        "transaction_type": f"Sticker {sticker_item['transaction_type']}",
                        "stickers": "",
                        "sticker_costs": "",
                        "has_stickers": False,
                        "adjusted_profit_value": 0
                })
        
        return result_items


def write_csv(items: List[Dict[str, str]], filename: str = "market_history.csv"):
        """Write items to CSV file."""
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                if items and "profit_loss" in items[0]:
                        # Profit/loss format with sticker costs
                        writer = csv.DictWriter(csvfile, fieldnames=['name', 'bought_price', 'sold_price', 'profit_loss', 'transaction_type', 'stickers', 'sticker_costs'])
                else:
                        # Original format
                        writer = csv.DictWriter(csvfile, fieldnames=['name', 'price', 'transaction_type', 'stickers'])
                writer.writeheader()
                # Remove internal fields for CSV output
                csv_items = []
                for item in items:
                        csv_item = {k: v for k, v in item.items() if k not in ['has_stickers', 'adjusted_profit_value']}
                        csv_items.append(csv_item)
                writer.writerows(csv_items)


def print_summary(items: List[Dict[str, str]]):
        """Print a summary of transaction statistics."""
        bought_only = []
        sold_only = []
        bought_and_sold = []
        items_with_stickers = []
        sticker_transactions = []
        
        total_bought_value = 0
        total_sold_value = 0
        total_profit_loss = 0
        total_sticker_investment = 0
        
        for item in items:
                if item.get("has_stickers", False):
                        items_with_stickers.append(item)
                
                if "Sticker" in item["transaction_type"]:
                        sticker_transactions.append(item)
                        if item["transaction_type"] == "Sticker Bought":
                                price_match = re.search(r'\$?(\d+\.?\d*)', item["bought_price"])
                                if price_match:
                                        total_sticker_investment += float(price_match.group(1))
                
                elif item["transaction_type"] == "Bought (Not Sold)":
                        bought_only.append(item)
                        # Extract price value
                        price_match = re.search(r'\$?(\d+\.?\d*)', item["bought_price"])
                        if price_match:
                                total_bought_value += float(price_match.group(1))
                                
                elif item["transaction_type"] == "Sold (Not Bought)":
                        sold_only.append(item)
                        # Extract price value
                        price_match = re.search(r'\$?(\d+\.?\d*)', item["sold_price"])
                        if price_match:
                                total_sold_value += float(price_match.group(1))
                                
                elif item["transaction_type"] == "Bought & Sold":
                        bought_and_sold.append(item)
                        if item.get("adjusted_profit_value") is not None:
                                total_profit_loss += item["adjusted_profit_value"]
        
        print("\n" + "="*60, file=sys.stderr)
        print("TRANSACTION SUMMARY", file=sys.stderr)
        print("="*60, file=sys.stderr)
        
        print(f"\n📈 BOUGHT & SOLD ITEMS: {len(bought_and_sold)}", file=sys.stderr)
        print(f"   Total Profit/Loss (adjusted for sticker costs): ${total_profit_loss:.2f}", file=sys.stderr)
        if bought_and_sold:
                print("   Items:", file=sys.stderr)
                for item in bought_and_sold:
                        sticker_info = f" [Stickers: {item['stickers']}]" if item.get('stickers') else ""
                        sticker_costs = f" [Sticker costs: {item['sticker_costs']}]" if item.get('sticker_costs') else ""
                        print(f"   • {item['name']}: {item['profit_loss']}{sticker_info}{sticker_costs}", file=sys.stderr)
        
        print(f"\n💰 BOUGHT ONLY (Not Sold): {len(bought_only)}", file=sys.stderr)
        print(f"   Total Investment: ${total_bought_value:.2f}", file=sys.stderr)
        if bought_only:
                print("   Items:", file=sys.stderr)
                for item in bought_only:
                        sticker_info = f" [Stickers: {item['stickers']}]" if item.get('stickers') else ""
                        print(f"   • {item['name']}: {item['bought_price']}{sticker_info}", file=sys.stderr)
        
        print(f"\n💸 SOLD ONLY (Not Previously Bought): {len(sold_only)}", file=sys.stderr)
        print(f"   Total Revenue: ${total_sold_value:.2f}", file=sys.stderr)
        if sold_only:
                print("   Items:", file=sys.stderr)
                for item in sold_only:
                        sticker_info = f" [Stickers: {item['stickers']}]" if item.get('stickers') else ""
                        print(f"   • {item['name']}: {item['sold_price']}{sticker_info}", file=sys.stderr)
        
        # Sticker summary
        if sticker_transactions:
                print(f"\n🎯 STICKER TRANSACTIONS: {len(sticker_transactions)}", file=sys.stderr)
                print(f"   Total Sticker Investment: ${total_sticker_investment:.2f}", file=sys.stderr)
                for item in sticker_transactions:
                        price = item['bought_price'] if item['bought_price'] else item['sold_price']
                        print(f"   • {item['name']} ({item['transaction_type']}): {price}", file=sys.stderr)
        
        if items_with_stickers:
                print(f"\n🏷️ ITEMS WITH STICKERS: {len(items_with_stickers)}", file=sys.stderr)
                for item in items_with_stickers:
                        print(f"   • {item['name']} ({item['transaction_type']}): {item['stickers']}", file=sys.stderr)
        
        # Overall summary
        net_total = total_profit_loss + total_sold_value - total_bought_value - total_sticker_investment
        print(f"\n📊 OVERALL SUMMARY:", file=sys.stderr)
        print(f"   Net Profit/Loss: ${net_total:.2f}", file=sys.stderr)
        print(f"   (Completed trades: ${total_profit_loss:.2f} + Sold only: ${total_sold_value:.2f} - Bought only: ${total_bought_value:.2f} - Sticker investment: ${total_sticker_investment:.2f})", file=sys.stderr)
        print("="*60 + "\n", file=sys.stderr)


def main():
        ap = argparse.ArgumentParser()
        ap.add_argument("--cookie", help="Full Cookie header value (e.g., 'sessionid=...; steamLoginSecure=...; ...'). If omitted, uses env STEAM_COOKIE.")
        ap.add_argument("--cookie-file", help="Path to file containing cookie string (e.g., 'cookie.txt'). Takes precedence over --cookie and STEAM_COOKIE.")
        ap.add_argument("--delay", type=float, default=0.8, help="Delay between requests in seconds.")
        ap.add_argument("--max-pages", type=int, default=0, help="Optional hard limit on number of pages to fetch (0 = no limit).")
        ap.add_argument("--output", "-o", default="market_history.csv", help="Output CSV filename (default: market_history.csv)")
        ap.add_argument("--json", action="store_true", help="Output raw JSON instead of CSV")
        args = ap.parse_args()

        # Priority: cookie-file > cookie arg > env variable
        cookie_str = ""
        if args.cookie_file:
                cookie_str = read_cookie_from_file(args.cookie_file)
        else:
                cookie_str = args.cookie or os.getenv("STEAM_COOKIE", "")
        
        if not cookie_str.strip():
                print("Error: Missing cookie. Provide --cookie-file, --cookie, or set STEAM_COOKIE.", file=sys.stderr)
                sys.exit(2)

        session = requests.Session()
        session.headers.update(HEADERS)
        cookies_dict = parse_cookie_str(cookie_str)
        session.cookies.update(cookies_dict)
        
        # Debug: print cookie info (without values for security)
        print(f"Debug: Using cookies: {list(cookies_dict.keys())}", file=sys.stderr)
        print(f"Debug: Parsed cookies: {cookies_dict}", file=sys.stderr)

        data = []  # This will contain all JSON responses across pages

        # Start from page 1 as requested
        page = 1
        # First attempt: try page-based params
        first = try_fetch_json(session, params={"page": page})
        if not first:
                # Fallback: some deployments use start/count; try start=0,count=100
                print("Debug: Page-based request failed, trying start/count method", file=sys.stderr)
                first = try_fetch_json(session, params={"start": 0, "count": 100})

        if not first:
                print("Error: Could not get valid JSON from Steam. Check your cookies and session.", file=sys.stderr)
                print("Tip: Try copying cookies directly from browser dev tools while logged into Steam Market.", file=sys.stderr)
                sys.exit(1)

        data.append(first)

        mode, cursor, step = page_strategy_from_response(first)
        if mode == "page":
                page = int(first.get("page") or first.get("current_page") or 1)
        else:
                # start_count mode
                page = 1  # only used for display; actual cursor is 'start'
                if step <= 0:
                        step = 100

        fetched_pages = 1
        while True:
                if args.max_pages and fetched_pages >= args.max_pages:
                        break
                if not has_more_pages(data[-1], mode, cursor, step):
                        break

                time.sleep(args.delay)

                if mode == "page":
                        page += 1
                        js = try_fetch_json(session, params={"page": page})
                else:
                        cursor += step
                        js = try_fetch_json(session, params={"start": cursor, "count": step})

                if not js:
                        break

                # Stop if results empty (common signaling)
                results_html = js.get("results_html") or js.get("html") or ""
                if isinstance(results_html, str) and not results_html.strip():
                        break

                data.append(js)
                fetched_pages += 1

        # Output the data
        if args.json:
                # Output the combined JSON list
                json.dump(data, sys.stdout)
                sys.stdout.write("\n")
        else:
                # Extract items and calculate profit/loss
                items = extract_items_from_data(data)
                profit_loss_items = calculate_profit_loss(items)
                write_csv(profit_loss_items, args.output)
                print(f"Exported {len(profit_loss_items)} transaction records to {args.output}", file=sys.stderr)
                
                # Print summary
                print_summary(profit_loss_items)


if __name__ == "__main__":
        main()