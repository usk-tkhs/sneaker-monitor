import os
import re
import json
import requests

WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

TARGET_SIZES = ["9", "9.5", "10", "10.5", "11", "11.5", "12", "12.5", "13"]

PRODUCTS = {
    "nike": {
        "name": "NIKE(AU)_AIR MAX 95 neon (men's)",
        "url": "https://www.nike.com/au/t/nike-air-max-95-big-bubble-og-mens-shoes-zhFhFmlx/HM4740-001",
    },
    "footlocker": {
        "name": "Footlocker(US)_AIR MAX 95 neon (men's)",
        "url": "https://www.footlocker.com/product/nike-air-max-95-mens/H4740001.html",
    },
    "kith": {
        "name": "KITH(CA)_New Balance Made in USA 992 - Argon",
        "url": "https://ca.kith.com/collections/mens-footwear/products/nbu992ki",
        "api_url": "https://ca.kith.com/products/nbu992ki.js",
    },
}

HEADERS = {"User-Agent": "Mozilla/5.0"}


def notify(message):
    r = requests.post(WEBHOOK_URL, json={"content": message})
    print("Discord status:", r.status_code)
    print("Discord response:", r.text)


def check_kith():
    data = requests.get(PRODUCTS["kith"]["api_url"], headers=HEADERS, timeout=20).json()
    found = []

    for v in data.get("variants", []):
        size = v.get("title", "").replace("US ", "").strip()
        if size in TARGET_SIZES and v.get("available"):
            found.append(size)

    return found


def check_nike():
    html = requests.get(PRODUCTS["nike"]["url"], headers=HEADERS, timeout=20).text

    match = re.search(r"INITIAL_REDUX_STATE=(.*?);</script>", html)
    if not match:
        return []

    try:
        js = json.loads(match.group(1))
        skus = js["Threads"]["products"]["HM4740-001"]["availableSkus"]
    except Exception as e:
        print("Nike parse error:", e)
        return []

    found = []

    for s in skus:
        size = str(s.get("nikeSize", "")).strip()
        in_stock = s.get("availability", {}).get("inStock", False)

        if size in TARGET_SIZES and in_stock:
            found.append(size)

    return found


def check_footlocker():
    html = requests.get(PRODUCTS["footlocker"]["url"], headers=HEADERS, timeout=20).text

    sizes = re.findall(
        r'"size":"(.*?)".*?"inventoryStatus":"Available"',
        html,
    )

    return [s for s in sizes if s in TARGET_SIZES]


def format_stock_block(product_key, sizes):
    product = PRODUCTS[product_key]

    if not sizes:
        return None

    size_text = ", ".join(f"US {s}" for s in sizes)

    return (
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"👟 **{product['name']}**\n"
        f"📏 Size: **{size_text}**\n"
        f"🔗 {product['url']}"
    )


def main():
    results = {
        "nike": check_nike(),
        "footlocker": check_footlocker(),
        "kith": check_kith(),
    }

    print(results)

    blocks = []

    for key, sizes in results.items():
        block = format_stock_block(key, sizes)
        if block:
            blocks.append(block)

    if blocks:
        message = (
            "🚨 **RESTOCK DETECTED** 🚨\n\n"
            "対象サイズ: **US 9〜US 13**\n\n"
            + "\n\n".join(blocks)
        )
        notify(message)
    else:
        print("No stock found.")


if __name__ == "__main__":
    main()