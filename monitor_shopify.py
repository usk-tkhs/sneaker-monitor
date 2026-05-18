import json
import os
from datetime import datetime, timezone, timedelta

import requests

WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

STATE_FILE = "stock_state.json"

JST = timezone(timedelta(hours=9))

HEADERS = {"User-Agent": "Mozilla/5.0"}

PRODUCTS = {
    "upthere_95": {
        "name": "UPTHERE(AU)_AIR MAX 95 neon (men's)",
        "url": "https://uptherestore.com/products/air-max-95-og-black-neon-yellow-cool-grey",
        "api_url": "https://uptherestore.com/products/air-max-95-og-black-neon-yellow-cool-grey.js",
        "target_sizes": [
            "10",
            "10.5",
            "11",
            "11.5",
            "12",
            "12.5",
            "13",
        ],
        "color": 16776960,
    },
    "kith": {
        "name": "KITH(CA)_New Balance Made in USA 992 - Argon",
        "url": "https://ca.kith.com/collections/mens-footwear/products/nbu992ki",
        "api_url": "https://ca.kith.com/products/nbu992ki.js",
        "target_sizes": [
            "9",
            "9.5",
            "10",
            "10.5",
            "11",
            "11.5",
            "12",
            "12.5",
            "13",
        ],
        "color": 10181046,
    },
    "kith_usa_990v3": {
        "name": "KITH(US)_New Balance Made in USA 990v3 - Hallow",
        "url": "https://kith.com/products/nbu990kt3",
        "api_url": "https://kith.com/products/nbu990kt3.js",
        "target_sizes": [
            "9",
            "9.5",
            "10",
            "10.5",
            "11",
            "11.5",
            "12",
            "12.5",
            "13",
        ],
        "color": 10181046,
    },
    "kith_usa_992": {
        "name": "KITH(US)_New Balance Made in USA 992 - Argon",
        "url": "https://kith.com/products/nbu992ki",
        "api_url": "https://kith.com/products/nbu992ki.js",
        "target_sizes": [
            "9",
            "9.5",
            "10",
            "10.5",
            "11",
            "11.5",
            "12",
            "12.5",
            "13",
        ],
        "color": 10181046,
    },
    "livestock_95": {
        "name": "Livestock(CA)_AIR MAX 95 neon (men's)",
        "url": "https://deadstock.ca/products/nike-air-max-95-og-black-neon-yellow-cool-grey",
        "api_url": "https://deadstock.ca/products/nike-air-max-95-og-black-neon-yellow-cool-grey.js",
        "target_sizes": [
            "10",
            "10.5",
            "11",
            "11.5",
            "12",
            "12.5",
            "13",
        ],
        "color": 3447003,
    },
    "sneakerbox_95": {
        "name": "Sneakerbox(CA)_AIR MAX 95 neon (men's)",
        "url": "https://sneakerboxshop.ca/products/nike-air-max-95-og-big-bubble-hm4740-001-neon-yellow",
        "api_url": "https://sneakerboxshop.ca/products/nike-air-max-95-og-big-bubble-hm4740-001-neon-yellow.js",
        "target_sizes": [
            "10",
            "10.5",
            "11",
            "11.5",
            "12",
            "12.5",
            "13",
        ],
        "color": 10181046,
    },
    "undefeated_95": {
        "name": "UNDEFEATED(US)_AIR MAX 95 neon (men's)",
        "url": "https://undefeated.com/products/nike-air-max-95-og-black-neonyellow",
        "api_url": "https://undefeated.com/products/nike-air-max-95-og-black-neonyellow.js",
        "target_sizes": [
            "10",
            "10.5",
            "11",
            "11.5",
            "12",
            "12.5",
            "13",
        ],
        "color": 16711680,
    },
    "supply_95": {
        "name": "Supply(AU)_AIR MAX 95 neon (men's)",
        "url": "https://supplystore.com.au/products/nike-air-max-95-og-black-neon-yellow",
        "api_url": "https://supplystore.com.au/products/nike-air-max-95-og-black-neon-yellow.js",
        "target_sizes": [
            "9",
            "10.5",
            "11",
            "11.5",
            "12",
            "12.5",
            "13",
        ],
        "color": 16753920,
    },
    "loaded_95": {
        "name": "LOADED(NZ)_AIR MAX 95 neon (men's)",
        "url": "https://loadednz.com/products/air-max-95-big-bubble-neon-1",
        "api_url": "https://loadednz.com/products/air-max-95-big-bubble-neon-1.js",
        "target_sizes": [
            "10",
            "10.5",
            "11",
            "11.5",
            "12",
            "12.5",
            "13",
        ],
        "color": 65280,
    },
}


def get_jst_now() -> str:
    return datetime.now(JST).strftime("%Y-%m-%d %H:%M:%S JST")


def get_utc_date() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def load_state() -> dict:
    if not os.path.exists(STATE_FILE):
        return {}

    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Failed to load state: {e}", flush=True)
        return {}


def save_state(state: dict) -> None:
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, sort_keys=True)


def get_new_sizes(product_key: str, current_sizes: list[str], state: dict) -> list[str]:
    previous_sizes = state.get(product_key, [])
    return [size for size in current_sizes if size not in previous_sizes]


def update_store_state(product_key: str, sizes: list[str], state: dict) -> None:
    state[product_key] = sizes


def notify_embeds(embeds: list[dict]) -> None:
    if not WEBHOOK_URL:
        print("DISCORD_WEBHOOK_URL is not set. Skip Discord notification.", flush=True)
        return

    r = requests.post(WEBHOOK_URL, json={"embeds": embeds}, timeout=20)
    print("Discord status:", r.status_code, flush=True)
    print("Discord response:", r.text, flush=True)


def should_send_healthcheck(state: dict) -> bool:
    return state.get("last_healthcheck") != get_utc_date()


def send_healthcheck(state: dict) -> None:
    embed = {
        "title": "✅ Shopify Fast Monitor alive",
        "color": 65280,
        "fields": [
            {
                "name": "Checked at",
                "value": get_jst_now(),
                "inline": False,
            }
        ],
    }

    notify_embeds([embed])
    state["last_healthcheck"] = get_utc_date()
    save_state(state)


def check_shopify_product(product_key: str) -> list[str]:
    product = PRODUCTS[product_key]
    target_sizes = product["target_sizes"]

    data = requests.get(
        product["api_url"],
        headers=HEADERS,
        timeout=20,
    ).json()

    found = []

    for variant in data.get("variants", []):
        size = (
            variant.get("title", "")
            .replace("US ", "")
            .strip()
        )

        if size in target_sizes and variant.get("available"):
            found.append(size)

    return found


def create_embed(product_key: str, sizes: list[str]) -> dict:
    product = PRODUCTS[product_key]
    size_text = " / ".join(f"US {s}" for s in sizes)

    return {
        "title": "🚨 RESTOCK DETECTED",
        "color": product.get("color", 16711680),
        "fields": [
            {
                "name": "Store / Product",
                "value": product["name"],
                "inline": False,
            },
            {
                "name": "Sizes",
                "value": size_text,
                "inline": False,
            },
            {
                "name": "Checked at",
                "value": get_jst_now(),
                "inline": False,
            },
            {
                "name": "URL",
                "value": product["url"],
                "inline": False,
            },
        ],
    }


def safe_check(product_key: str) -> list[str]:
    try:
        print(f"Checking {product_key}...", flush=True)
        result = check_shopify_product(product_key)
        print(f"{product_key} result: {result}", flush=True)
        return result
    except Exception as e:
        print(f"{product_key} error: {e}", flush=True)
        return []


def main() -> None:
    state = load_state()

    results = {
        product_key: safe_check(product_key)
        for product_key in PRODUCTS
    }

    print(results, flush=True)

    if should_send_healthcheck(state):
        send_healthcheck(state)

    embeds = []
    for product_key, current_sizes in results.items():
        new_sizes = get_new_sizes(product_key, current_sizes, state)

        if new_sizes:
            embeds.append(create_embed(product_key, new_sizes))

        update_store_state(product_key, current_sizes, state)

    save_state(state)

    if embeds:
        notify_embeds(embeds)
    else:
        print("No new stock.", flush=True)


if __name__ == "__main__":
    main()
