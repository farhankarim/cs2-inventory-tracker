#!/usr/bin/env python3
"""
Demo script to show how the CS2 Inventory Tracker works with sample data.
This is useful for testing without requiring internet access or a real Steam profile.
"""

import json
from fetch_inventory import CS2InventoryTracker


def generate_sample_inventory():
    """Generate sample inventory data for demonstration."""
    sample_items = [
        {
            "asset_id": "123456789",
            "class_id": "310776884",
            "instance_id": "188530139",
            "amount": "1",
            "name": "AK-47 | Redline",
            "market_name": "AK-47 | Redline (Field-Tested)",
            "market_hash_name": "AK-47 | Redline (Field-Tested)",
            "type": "Rifle",
            "tradable": 1,
            "marketable": 1,
            "commodity": 0,
            "icon_url": "...",
            "icon_url_large": "...",
            "name_color": "D2D2D2",
            "background_color": "",
            "tags": [
                {"category": "Type", "internal_name": "CSGO_Type_Rifle", "localized_tag_name": "Rifle"},
                {"category": "Weapon", "internal_name": "weapon_ak47", "localized_tag_name": "AK-47"},
                {"category": "ItemSet", "internal_name": "set_community_2", "localized_tag_name": "The Phoenix Collection"},
                {"category": "Quality", "internal_name": "normal", "localized_tag_name": "Normal"},
                {"category": "Rarity", "internal_name": "Rarity_Legendary_Weapon", "localized_tag_name": "Classified"},
                {"category": "Exterior", "internal_name": "WearCategory1", "localized_tag_name": "Field-Tested"}
            ]
        },
        {
            "asset_id": "123456790",
            "class_id": "469448053",
            "instance_id": "0",
            "amount": "1",
            "name": "CS:GO Weapon Case",
            "market_name": "CS:GO Weapon Case",
            "market_hash_name": "CS:GO Weapon Case",
            "type": "Base Grade Container",
            "tradable": 1,
            "marketable": 1,
            "commodity": 1,
            "icon_url": "...",
            "icon_url_large": "...",
            "name_color": "D2D2D2",
            "background_color": "",
            "tags": [
                {"category": "Type", "internal_name": "CSGO_Type_WeaponCase", "localized_tag_name": "Container"},
                {"category": "ItemSet", "internal_name": "set_weapons_i", "localized_tag_name": "The Arms Deal Collection"},
                {"category": "Quality", "internal_name": "normal", "localized_tag_name": "Normal"},
                {"category": "Rarity", "internal_name": "Rarity_Common", "localized_tag_name": "Base Grade"}
            ]
        },
        {
            "asset_id": "123456791",
            "class_id": "1349278298",
            "instance_id": "0",
            "amount": "1",
            "name": "Chroma 3 Case",
            "market_name": "Chroma 3 Case",
            "market_hash_name": "Chroma 3 Case",
            "type": "Base Grade Container",
            "tradable": 1,
            "marketable": 1,
            "commodity": 1,
            "icon_url": "...",
            "icon_url_large": "...",
            "name_color": "D2D2D2",
            "background_color": "",
            "tags": [
                {"category": "Type", "internal_name": "CSGO_Type_WeaponCase", "localized_tag_name": "Container"},
                {"category": "ItemSet", "internal_name": "set_community_16", "localized_tag_name": "The Chroma 3 Collection"},
                {"category": "Quality", "internal_name": "normal", "localized_tag_name": "Normal"},
                {"category": "Rarity", "internal_name": "Rarity_Common", "localized_tag_name": "Base Grade"}
            ]
        },
        {
            "asset_id": "123456792",
            "class_id": "310777541",
            "instance_id": "480085569",
            "amount": "1",
            "name": "M4A4 | Asiimov",
            "market_name": "M4A4 | Asiimov (Battle-Scarred)",
            "market_hash_name": "M4A4 | Asiimov (Battle-Scarred)",
            "type": "Rifle",
            "tradable": 1,
            "marketable": 1,
            "commodity": 0,
            "icon_url": "...",
            "icon_url_large": "...",
            "name_color": "D2D2D2",
            "background_color": "",
            "tags": [
                {"category": "Type", "internal_name": "CSGO_Type_Rifle", "localized_tag_name": "Rifle"},
                {"category": "Weapon", "internal_name": "weapon_m4a1", "localized_tag_name": "M4A4"},
                {"category": "ItemSet", "internal_name": "set_community_2", "localized_tag_name": "The Phoenix Collection"},
                {"category": "Quality", "internal_name": "normal", "localized_tag_name": "Normal"},
                {"category": "Rarity", "internal_name": "Rarity_Legendary_Weapon", "localized_tag_name": "Covert"},
                {"category": "Exterior", "internal_name": "WearCategory4", "localized_tag_name": "Battle-Scarred"}
            ]
        },
        {
            "asset_id": "123456793",
            "class_id": "310776838",
            "instance_id": "302028390",
            "amount": "1",
            "name": "AWP | Asiimov",
            "market_name": "AWP | Asiimov (Well-Worn)",
            "market_hash_name": "AWP | Asiimov (Well-Worn)",
            "type": "Sniper Rifle",
            "tradable": 1,
            "marketable": 1,
            "commodity": 0,
            "icon_url": "...",
            "icon_url_large": "...",
            "name_color": "D2D2D2",
            "background_color": "",
            "tags": [
                {"category": "Type", "internal_name": "CSGO_Type_SniperRifle", "localized_tag_name": "Sniper Rifle"},
                {"category": "Weapon", "internal_name": "weapon_awp", "localized_tag_name": "AWP"},
                {"category": "ItemSet", "internal_name": "set_community_2", "localized_tag_name": "The Phoenix Collection"},
                {"category": "Quality", "internal_name": "normal", "localized_tag_name": "Normal"},
                {"category": "Rarity", "internal_name": "Rarity_Legendary_Weapon", "localized_tag_name": "Covert"},
                {"category": "Exterior", "internal_name": "WearCategory3", "localized_tag_name": "Well-Worn"}
            ]
        },
        {
            "asset_id": "123456794",
            "class_id": "310776838",
            "instance_id": "0",
            "amount": "3",
            "name": "Operation Phoenix Weapon Case",
            "market_name": "Operation Phoenix Weapon Case",
            "market_hash_name": "Operation Phoenix Weapon Case",
            "type": "Base Grade Container",
            "tradable": 1,
            "marketable": 1,
            "commodity": 1,
            "icon_url": "...",
            "icon_url_large": "...",
            "name_color": "D2D2D2",
            "background_color": "",
            "tags": [
                {"category": "Type", "internal_name": "CSGO_Type_WeaponCase", "localized_tag_name": "Container"},
                {"category": "ItemSet", "internal_name": "set_community_2", "localized_tag_name": "The Phoenix Collection"},
                {"category": "Quality", "internal_name": "normal", "localized_tag_name": "Normal"},
                {"category": "Rarity", "internal_name": "Rarity_Common", "localized_tag_name": "Base Grade"}
            ]
        }
    ]
    
    return sample_items


def main():
    """Main function to demonstrate the inventory tracker."""
    print("CS2 Inventory Tracker - Demo Mode")
    print("=" * 80)
    print("Generating sample inventory data...\n")
    
    # Generate sample data
    items = generate_sample_inventory()
    
    # Create a tracker instance (without needing a real profile)
    tracker = CS2InventoryTracker("https://steamcommunity.com/id/demo")
    
    # Display the sample items
    tracker.display_items(items)
    
    # Save to JSON
    tracker.save_to_json(items, 'sample_inventory.json')
    
    print(f"\n{'='*80}")
    print(f"Demo completed! Generated {len(items)} sample items.")
    print(f"{'='*80}")
    print("\nTo fetch real inventory data:")
    print("  python fetch_inventory.py https://steamcommunity.com/id/your-steam-id/inventory")


if __name__ == "__main__":
    main()
