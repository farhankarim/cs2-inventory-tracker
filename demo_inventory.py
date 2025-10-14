import requests
import csv
import time

# 🎯 Your skins and purchase prices (USD)
skins = {
    "AWP | Exoskeleton (Minimal Wear)": 9.97,
    "AWP | Atheris (Battle-Scarred)": 3.70,
    "M4A1-S | Nitro (Minimal Wear)": 1.29,
    "AWP | Mortis (Field-Tested)": 2.60,
    "AK-47 | Midnight Laminate (Field-Tested)": 10.43,
    "USP-S | Torque (Factory New)": 3.60,
    "MP9 | Food Chain (Well-Worn)": 1.86,
    "AK-47 | The Outsiders (Battle-Scarred)": 7.36,
    "M4A1-S | Liquidation (Minimal Wear)": 11.64,
    "M4A1-S | Black Lotus (Field-Tested)": 9.40
}

# 🧮 Steam takes ~13% fee, CS.Money takes ~7%
STEAM_FEE = 0.13
CSMONEY_FEE = 0.07

# Base URLs
STEAM_URL = "https://steamcommunity.com/market/priceoverview/"
CSMONEY_URL = "https://cs.money/api/exchange/prices?search="


def get_steam_price(item_name):
    """Fetch lowest Steam price in USD"""
    params = {"appid": 730, "currency": 1, "market_hash_name": item_name}
    try:
        r = requests.get(STEAM_URL, params=params, timeout=10)
        data = r.json()
        if data.get("success") and data.get("lowest_price"):
            return float(data["lowest_price"].replace("$", "").strip())
    except Exception as e:
        print(f"[Steam Error] {item_name}: {e}")
    return None


def get_csmoney_price(item_name):
    """Fetch CSMoney market price"""
    url = f"{CSMONEY_URL}{item_name}"
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        data = r.json()
        if isinstance(data, list) and len(data) > 0:
            return float(data[0].get("price", 0)) / 100  # Convert cents to USD
    except Exception as e:
        print(f"[CSMoney Error] {item_name}: {e}")
    return None


def apply_fee(price, fee_rate):
    """Deduct platform fee"""
    if not price:
        return None
    return round(price * (1 - fee_rate), 2)


def main():
    results = []

    for skin, buy_price in skins.items():
        print(f"Fetching: {skin} ...")

        steam_price = get_steam_price(skin)
        steam_after_fee = apply_fee(steam_price, STEAM_FEE)

        csmoney_price = get_csmoney_price(skin)
        csmoney_after_fee = apply_fee(csmoney_price, CSMONEY_FEE)

        # Calculate profit/loss
        steam_diff = (
            round(steam_after_fee - buy_price, 2) if steam_after_fee else None
        )
        csmoney_diff = (
            round(csmoney_after_fee - buy_price, 2) if csmoney_after_fee else None
        )

        results.append(
            {
                "Skin": skin,
                "Bought For ($)": buy_price,
                "Steam Price ($)": steam_price,
                "Steam After Fee ($)": steam_after_fee,
                "Steam Profit/Loss ($)": steam_diff,
                "CS.Money Price ($)": csmoney_price,
                "CS.Money After Fee ($)": csmoney_after_fee,
                "CS.Money Profit/Loss ($)": csmoney_diff,
            }
        )

        time.sleep(2)  # avoid rate-limiting

    # Export to CSV
    with open("cs2_prices.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "Skin",
                "Bought For ($)",
                "Steam Price ($)",
                "Steam After Fee ($)",
                "Steam Profit/Loss ($)",
                "CS.Money Price ($)",
                "CS.Money After Fee ($)",
                "CS.Money Profit/Loss ($)",
            ],
        )
        writer.writeheader()
        writer.writerows(results)

    print("\n✅ Exported results to cs2_prices.csv\n")
    total_profit_steam = sum(
        r["Steam Profit/Loss ($)"] or 0 for r in results if r["Steam Profit/Loss ($)"]
    )
    total_profit_csmoney = sum(
        r["CS.Money Profit/Loss ($)"] or 0 for r in results if r["CS.Money Profit/Loss ($)"]
    )

    print(f"💰 Total Steam Profit/Loss (after fee): ${round(total_profit_steam, 2)}")
    print(f"💰 Total CS.Money Profit/Loss (after fee): ${round(total_profit_csmoney, 2)}")


if __name__ == "__main__":
    main()
