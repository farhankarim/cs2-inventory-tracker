STEAM_FEE = 0.13
STEAM_URL = "https://steamcommunity.com/market/priceoverview/"

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
import requests
import csv
import time
import os
import json

# CSV input file (columns: Skin,Wear,Price (USD))
SKINS_CSV = "skins.csv"


def load_skins_from_csv(path=SKINS_CSV):
    """Return list of dicts with keys: name, wear, price (float)."""
    out = []
    if not os.path.exists(path):
        raise FileNotFoundError(f"{path} not found")
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = (row.get("Skin") or "").strip()
            wear = (row.get("Wear") or "").strip()
            price_raw = (row.get("Price (USD)") or row.get("Price") or "").strip()
            try:
                price = float(price_raw) if price_raw != "" else None
            except Exception:
                price = None
            out.append({"name": name, "wear": wear, "price": price})
    return out

    return None


def apply_fee(price, fee_rate):
    """Deduct platform fee"""
    if price is None:
        return None
    return round(price * (1 - fee_rate), 2)


def main():
    results = []
    skins_list = load_skins_from_csv()
    for entry in skins_list:
        base_name = entry["name"]
        wear = entry["wear"]
        buy_price = entry["price"]
        full_name = f"{base_name} ({wear})" if wear else base_name
        print(f"Fetching: {full_name} ...")

        steam_price = get_steam_price(full_name)
        steam_after_fee = apply_fee(steam_price, STEAM_FEE)

        # Calculate profit/loss — show zero/negative explicitly
        steam_diff = (
            round(steam_after_fee - buy_price, 2) if steam_after_fee is not None and buy_price is not None else None
        )

        results.append(
            {
                "Skin": full_name,
                "Bought For ($)": buy_price,
                "Steam Price ($)": steam_price,
                "Steam After Fee ($)": steam_after_fee,
                "Steam Profit/Loss ($)": steam_diff,
            }
        )

        time.sleep(2)  # avoid rate-limiting

    # Sort results by most loss first (lowest profit/loss)
    results_sorted = sorted(results, key=lambda x: x["Steam Profit/Loss ($)"] if x["Steam Profit/Loss ($)"] is not None else 0)

    # Export to CSV
    fieldnames = [
        "Skin",
        "Bought For ($)",
        "Steam Price ($)",
        "Steam After Fee ($)",
        "Steam Profit/Loss ($)",
    ]
    normalized = []
    for r in results_sorted:
        row = {}
        for fn in fieldnames:
            v = r.get(fn)
            if isinstance(v, (int, float)):
                row[fn] = f"{v:.2f}"
            elif v is None:
                row[fn] = ""
            else:
                row[fn] = v
        normalized.append(row)

    with open("cs2_prices.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(normalized)

    print("\n✅ Exported results to cs2_prices.csv\n")
    # Robust totals (treat None as 0)
    total_profit_steam = sum((float(r.get("Steam Profit/Loss ($)")) if r.get("Steam Profit/Loss ($)") is not None else 0) for r in results_sorted)

    print(f"💰 Total Steam Profit/Loss (after fee): ${round(total_profit_steam, 2)}")
    print(f"💸 Total profit if I sell everything on Steam (after fee): ${round(total_profit_steam, 2)}")

    # Echo sorted results
    print("\nSorted items by most loss first:")
    for r in results_sorted:
        print(f"{r['Skin']}: Profit/Loss = {r['Steam Profit/Loss ($)']}")


if __name__ == "__main__":
    main()
