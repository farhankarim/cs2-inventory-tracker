#!/usr/bin/env python3
"""
CS2 Inventory Tracker - Fetch inventory items from Steam profile
This script uses BeautifulSoup4 to scrape CS2 inventory items from a Steam profile.
"""

import requests
from bs4 import BeautifulSoup
import json
import time
import sys


class CS2InventoryTracker:
    """Class to track and fetch CS2 inventory items from Steam."""
    
    def __init__(self, profile_url):
        """
        Initialize the inventory tracker.
        
        Args:
            profile_url: Full Steam profile URL or Steam ID
        """
        self.profile_url = profile_url
        self.steam_id = None
        self.session = requests.Session()
        
        # Steam requires proper headers to avoid being blocked
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        
        # CS2 App ID
        self.app_id = 730  # CS2 (Counter-Strike 2) uses the same app ID as CS:GO
        self.context_id = 2
        
    def extract_steam_id(self):
        """Extract Steam ID from profile URL."""
        try:
            # If it's already a 64-bit Steam ID
            if self.profile_url.isdigit() and len(self.profile_url) == 17:
                self.steam_id = self.profile_url
                return True
            
            # Try to get Steam ID from vanity URL
            response = self.session.get(self.profile_url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for Steam ID in various places
            # Method 1: Check for inventory link
            inventory_link = soup.find('a', {'class': 'inventory_link'})
            if inventory_link and 'href' in inventory_link.attrs:
                href = inventory_link['href']
                if '/profiles/' in href:
                    self.steam_id = href.split('/profiles/')[1].split('/')[0]
                    return True
            
            # Method 2: Check page source for steamid
            page_text = response.text
            if 'g_steamID = "' in page_text:
                start = page_text.find('g_steamID = "') + 13
                end = page_text.find('"', start)
                self.steam_id = page_text[start:end]
                return True
            
            # Method 3: Look in scripts for steamid
            scripts = soup.find_all('script', {'type': 'text/javascript'})
            for script in scripts:
                if script.string and 'steamid' in script.string.lower():
                    # Try to extract 17-digit Steam ID
                    import re
                    matches = re.findall(r'\b\d{17}\b', script.string)
                    if matches:
                        self.steam_id = matches[0]
                        return True
            
            print("Could not extract Steam ID from profile URL.")
            print("Please ensure the profile is public and the URL is correct.")
            return False
            
        except Exception as e:
            print(f"Error extracting Steam ID: {e}")
            return False
    
    def fetch_inventory(self, start_assetid=None, count=5000):
        """
        Fetch inventory items using Steam's inventory API.
        
        Args:
            start_assetid: Asset ID to start from (for pagination)
            count: Number of items to fetch per request
            
        Returns:
            Dictionary containing inventory data
        """
        if not self.steam_id:
            if not self.extract_steam_id():
                return None
        
        # Build the inventory API URL
        url = f"https://steamcommunity.com/inventory/{self.steam_id}/{self.app_id}/{self.context_id}"
        
        params = {
            'l': 'english',
            'count': count
        }
        
        if start_assetid:
            params['start_assetid'] = start_assetid
        
        try:
            print(f"Fetching inventory from Steam ID: {self.steam_id}")
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            return data
            
        except requests.exceptions.HTTPError as e:
            if response.status_code == 403:
                print("Error: Inventory is private. Please make your inventory public.")
            elif response.status_code == 500:
                print("Error: Steam returned an error. The inventory might be empty or private.")
            else:
                print(f"HTTP Error: {e}")
            return None
        except Exception as e:
            print(f"Error fetching inventory: {e}")
            return None
    
    def parse_inventory_html(self, html_content):
        """
        Parse inventory from HTML content (fallback method).
        
        Args:
            html_content: HTML content of the inventory page
            
        Returns:
            List of items parsed from HTML
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        items = []
        
        # Look for inventory items in the HTML
        inventory_items = soup.find_all('div', {'class': 'inventory_item_element'})
        
        for item in inventory_items:
            try:
                item_data = {
                    'name': item.get('data-name', 'Unknown'),
                    'asset_id': item.get('data-assetid', ''),
                    'class_id': item.get('data-classid', ''),
                    'instance_id': item.get('data-instanceid', '')
                }
                items.append(item_data)
            except Exception as e:
                print(f"Error parsing item: {e}")
                continue
        
        return items
    
    def get_all_items(self):
        """
        Fetch all inventory items, handling pagination.
        
        Returns:
            List of all inventory items with descriptions
        """
        all_items = []
        start_assetid = None
        has_more = True
        
        while has_more:
            data = self.fetch_inventory(start_assetid=start_assetid)
            
            if not data:
                break
            
            # Check if we have items
            if 'assets' not in data or 'descriptions' not in data:
                print("No items found or inventory is empty.")
                break
            
            # Create a mapping of classid_instanceid to descriptions
            descriptions_map = {}
            for desc in data.get('descriptions', []):
                key = f"{desc['classid']}_{desc['instanceid']}"
                descriptions_map[key] = desc
            
            # Process each asset
            for asset in data.get('assets', []):
                key = f"{asset['classid']}_{asset['instanceid']}"
                description = descriptions_map.get(key, {})
                
                item = {
                    'asset_id': asset.get('assetid'),
                    'class_id': asset.get('classid'),
                    'instance_id': asset.get('instanceid'),
                    'amount': asset.get('amount', '1'),
                    'name': description.get('name', 'Unknown'),
                    'market_name': description.get('market_name', ''),
                    'market_hash_name': description.get('market_hash_name', ''),
                    'type': description.get('type', ''),
                    'tradable': description.get('tradable', 0),
                    'marketable': description.get('marketable', 0),
                    'commodity': description.get('commodity', 0),
                    'icon_url': description.get('icon_url', ''),
                    'icon_url_large': description.get('icon_url_large', ''),
                    'name_color': description.get('name_color', ''),
                    'background_color': description.get('background_color', '')
                }
                
                # Add tags if available
                if 'tags' in description:
                    item['tags'] = description['tags']
                
                all_items.append(item)
            
            # Check for pagination
            if data.get('more_items', 0) == 1 and 'last_assetid' in data:
                start_assetid = data['last_assetid']
                print(f"Fetching more items... (Current count: {len(all_items)})")
                time.sleep(1)  # Be nice to Steam's servers
            else:
                has_more = False
        
        return all_items
    
    def display_items(self, items):
        """
        Display inventory items in a formatted way.
        
        Args:
            items: List of inventory items
        """
        if not items:
            print("No items to display.")
            return
        
        print(f"\n{'='*80}")
        print(f"CS2 INVENTORY - Total Items: {len(items)}")
        print(f"{'='*80}\n")
        
        # Group items by type
        items_by_type = {}
        for item in items:
            item_type = item.get('type', 'Unknown')
            if item_type not in items_by_type:
                items_by_type[item_type] = []
            items_by_type[item_type].append(item)
        
        # Display items grouped by type
        for item_type, type_items in sorted(items_by_type.items()):
            print(f"\n{item_type} ({len(type_items)} items):")
            print("-" * 80)
            for item in type_items:
                name = item.get('name', 'Unknown')
                market_name = item.get('market_name', '')
                tradable = "✓" if item.get('tradable', 0) == 1 else "✗"
                marketable = "✓" if item.get('marketable', 0) == 1 else "✗"
                
                print(f"  • {name}")
                if market_name and market_name != name:
                    print(f"    Market Name: {market_name}")
                print(f"    Tradable: {tradable} | Marketable: {marketable}")
                print()
    
    def save_to_json(self, items, filename='inventory.json'):
        """
        Save inventory items to a JSON file.
        
        Args:
            items: List of inventory items
            filename: Output filename
        """
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(items, f, indent=2, ensure_ascii=False)
            print(f"\nInventory saved to {filename}")
        except Exception as e:
            print(f"Error saving to JSON: {e}")


def main():
    """Main function to run the inventory tracker."""
    # Default profile URL
    profile_url = "https://steamcommunity.com/id/farhankarim/inventory"
    
    # Allow custom profile URL from command line
    if len(sys.argv) > 1:
        profile_url = sys.argv[1]
    
    print("CS2 Inventory Tracker")
    print("=" * 80)
    print(f"Profile URL: {profile_url}\n")
    
    # Create tracker instance
    tracker = CS2InventoryTracker(profile_url)
    
    # Fetch all items
    items = tracker.get_all_items()
    
    if items:
        # Display items
        tracker.display_items(items)
        
        # Save to JSON
        tracker.save_to_json(items)
        
        print(f"\n{'='*80}")
        print(f"Successfully fetched {len(items)} items from the inventory!")
        print(f"{'='*80}")
    else:
        print("\nFailed to fetch inventory items.")
        print("Please check:")
        print("  1. The profile URL is correct")
        print("  2. The inventory is set to public")
        print("  3. Your internet connection is working")
        sys.exit(1)


if __name__ == "__main__":
    main()
