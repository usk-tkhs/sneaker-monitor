import os
import re
import json
import requests

import hashlib
from datetime import datetime

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
    "upthere_95": {
        "name": "UPTHERE(AU)_AIR MAX 95 neon (men's)",
        "url": "https://uptherestore.com/products/air-max-95-og-black-neon-yellow-cool-grey",
        "api_url": "https://uptherestore.com/products/air-max-95-og-black-neon-yellow-cool-grey.js",
    },
    "champs_95": {
        "name": "Champs(US)_AIR MAX 95 neon (men's)",
        "url": "https://www.champssports.com/product/nike-air-max-95-mens/HM4740001.html",
    },
    "kith": {
        "name": "KITH(CA)_New Balance Made in USA 992 - Argon",
        "url": "https://ca.kith.com/collections/mens-footwear/products/nbu992ki",
        "api_url": "https://ca.kith.com/products/nbu992ki.js",
    },
    "kith_usa_990v3": {
        "name": "KITH(US)_New Balance Made in USA 990v3 - Hallow",
        "url": "https://kith.com/products/nbu990kt3",
        "api_url": "https://kith.com/products/nbu990kt3.js",
    },
    "kith_usa_992": {
        "name": "KITH(US)_New Balance Made in USA 992 - Argon",
        "url": "https://kith.com/products/nbu992ki",
        "api_url": "https://kith.com/products/nbu992ki.js",
    },
}

HEADERS = {"User-Agent": "Mozilla/5.0"}


def notify(message):
    r = requests.post(WEBHOOK_URL, json={"content": message})
    print("Discord status:", r.status_code)
    print("Discord response:", r.text)


# =========================
# STATE FILE
# =========================
STATE_FILE = "stock_state.json"


def load_state():

    if not os.path.exists(STATE_FILE):
        return {}

    try:
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    except:
        return {}


def save_state(state):

    with open(STATE_FILE, "w") as f:
        json.dump(state, f)


# =========================
# STOCK HASH
# =========================
def generate_stock_hash(results):

    normalized = json.dumps(results, sort_keys=True)

    return hashlib.md5(
        normalized.encode()
    ).hexdigest()


# =========================
# HEALTH CHECK
# =========================
def should_send_healthcheck(state):

    today = datetime.utcnow().strftime("%Y-%m-%d")

    last_healthcheck = state.get(
        "last_healthcheck"
    )

    return last_healthcheck != today


def send_healthcheck(state):

    notify(
        "✅ Sneaker monitor alive\n"
        f"UTC: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}"
    )

    state["last_healthcheck"] = (
        datetime.utcnow().strftime("%Y-%m-%d")
    )

    save_state(state)


def check_kith(product_key):

    api_url = PRODUCTS[product_key]["api_url"]
    
    data = requests.get(
        api_url,
        headers=HEADERS,
        timeout=20
    ).json()

    found = []
    
    for v in data.get("variants", []):

        size = (
            v.get("title", "")
            .replace("US ", "")
            .strip()
        )

        if (
            size in TARGET_SIZES
            and v.get("available")
        ):
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


def check_champs():

    url = PRODUCTS["champs_95"]["url"]

    html = requests.get(
        url,
        headers=HEADERS,
        timeout=20
    ).text

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


# =========================
# MAIN
# =========================
def main():

    state = load_state()

    results = {
        "kith": check_kith("kith"),
        "kith_usa_990v3": check_kith("kith_usa_990v3"),
        "kith_usa_992": check_kith("kith_usa_992"),
        "upthere_95": check_kith("upthere_95"),
    }

    print(results)

    # =========================
    # HEALTH CHECK
    # =========================
    if should_send_healthcheck(state):
        send_healthcheck(state)

    blocks = []

    for key, sizes in results.items():

        block = format_stock_block(
            key,
            sizes
        )

        if block:
            blocks.append(block)

    current_hash = generate_stock_hash(results)

    previous_hash = state.get(
        "last_stock_hash"
    )

    if blocks:

        if current_hash != previous_hash:

            message = (
                "🚨 **RESTOCK DETECTED - Shopify Fast Monitor** 🚨\n\n"
                "対象サイズ: **US 9〜US 13**\n\n"
                + "\n\n".join(blocks)
            )

            notify(message)

            state[
                "last_stock_hash"
            ] = current_hash

            save_state(state)

        else:
            print("Duplicate stock. Skip notification.")

    else:

        print("No stock found.")

        state[
            "last_stock_hash"
        ] = ""

        save_state(state)


if __name__ == "__main__":
    main()