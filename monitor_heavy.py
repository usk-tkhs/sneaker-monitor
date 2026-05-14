import json
import os
import re
from datetime import datetime, timezone, timedelta

import requests

WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

TARGET_SIZES = ["9", "9.5", "10", "10.5", "11", "11.5", "12", "12.5", "13"]
STATE_FILE = "stock_state.json"

JST = timezone(timedelta(hours=9))

HEADERS = {"User-Agent": "Mozilla/5.0"}

PRODUCTS = {
    "nike": {
        "name": "Nike(API Signal)_AIR MAX 95 neon",
        "url": "https://www.nike.com/au/t/nike-air-max-95-big-bubble-og-mens-shoes-zhFhFmlx/HM4740-001",
        "style_color": "HM4740-001",
        "color": 16711680,
    },
    "mind001_au": {
        "name": "Nike(API Signal)_Mind 001 Mule Black Hyper Crimson",
        "url": "https://www.nike.com/au/t/nike-mind-001-mens-pregame-mules-0gWQwzQC/HQ4307-001",
        "style_color": "HQ4307-001",
        "color": 16753920,
    },
    "footlocker": {
        "name": "Footlocker(US)_AIR MAX 95 neon (men's)",
        "url": "https://www.footlocker.com/product/nike-air-max-95-mens/H4740001.html",
        "color": 16753920,
    },
    "champs_95": {
        "name": "Champs(US)_AIR MAX 95 neon (men's)",
        "url": "https://www.champssports.com/product/nike-air-max-95-mens/HM4740001.html",
        "color": 16776960,
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
        "title": "✅ Heavy Monitor alive",
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


def check_nike(product_key: str) -> list[str]:
    product = PRODUCTS[product_key]
    style_color = product["style_color"]

    api_url = (
        "https://api.nike.com/product_feed/threads/v2"
        f"?filter=productInfo.merchProduct.styleColor({style_color})"
        "&filter=marketplace(US)"
        "&filter=language(en)"
        "&filter=channelId(d9a5bc42-4b9c-4976-858a-f159cf99c647)"
    )

    data = requests.get(api_url, headers=HEADERS, timeout=20).json()
    objects = data.get("objects", [])

    if not objects:
        print(f"{product_key}: no Nike API objects found", flush=True)
        return []

    product_info = objects[0]["productInfo"][0]
    skus = product_info.get("skus", [])
    available_skus = product_info.get("availableSkus", [])

    size_map = {
        sku["id"]: str(sku.get("nikeSize", "")).strip()
        for sku in skus
    }

    found = []
    for item in available_skus:
        size = size_map.get(item.get("skuId"))
        if item.get("available", False) and size in TARGET_SIZES:
            found.append(size)

    return found


def check_footlocker() -> list[str]:
    html = requests.get(
        PRODUCTS["footlocker"]["url"],
        headers=HEADERS,
        timeout=20,
    ).text

    sizes = re.findall(
        r'"size":"([^"]+)".{0,500}?"inventoryStatus":"Available"',
        html,
    )

    return [s for s in sizes if s in TARGET_SIZES]


def check_champs() -> list[str]:
    html = requests.get(
        PRODUCTS["champs_95"]["url"],
        headers=HEADERS,
        timeout=20,
    ).text

    sizes = re.findall(
        r'"size":"([^"]+)".{0,500}?"inventoryStatus":"Available"',
        html,
    )

    return [s for s in sizes if s in TARGET_SIZES]


def create_embed(product_key: str, sizes: list[str]) -> dict:
    product = PRODUCTS[product_key]
    size_text = " / ".join(f"US {s}" for s in sizes)

    return {
        "title": "🚨 STOCK SIGNAL DETECTED",
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


def safe_check(name: str, func) -> list[str]:
    try:
        print(f"Checking {name}...", flush=True)
        result = func()
        print(f"{name} result: {result}", flush=True)
        return result
    except Exception as e:
        print(f"{name} error: {e}", flush=True)
        return []


def main() -> None:
    state = load_state()

    results = {
        "nike": safe_check("nike", lambda: check_nike("nike")),
        "mind001_au": safe_check("mind001_au", lambda: check_nike("mind001_au")),
        "footlocker": safe_check("footlocker", check_footlocker),
        "champs_95": safe_check("champs_95", check_champs),
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
