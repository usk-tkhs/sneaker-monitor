import json
import os
import re
from datetime import datetime, timezone, timedelta

import requests

WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

STATE_FILE = "stock_state.json"

JST = timezone(timedelta(hours=9))

HEADERS = {"User-Agent": "Mozilla/5.0"}

PRODUCTS = {
    "nike": {
        "name": "Nike(API Signal)_AIR MAX 95 neon",
        "url": "https://www.nike.com/au/t/nike-air-max-95-big-bubble-og-mens-shoes-zhFhFmlx/HM4740-001",
        "style_color": "HM4740-001",
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
    "footlocker": {
        "name": "Footlocker(US)_AIR MAX 95 neon (men's)",
        "url": "https://www.footlocker.com/product/nike-air-max-95-mens/H4740001.html",
        "target_sizes": [
            "10",
            "10.5",
            "11",
            "11.5",
            "12",
            "12.5",
            "13",
        ],
        "color": 16753920,
    },
    "champs_95": {
        "name": "Champs(US)_AIR MAX 95 neon (men's)",
        "url": "https://www.champssports.com/product/nike-air-max-95-mens/HM4740001.html",
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
    "sws_mind001": {
        "name": "SWS(JP)_Nike Mind 001 Black Hyper Crimson",
        "url": "https://www.sports-ws.com/commodity/SKOB1347D/NI1757BU079698/",
        "target_sizes": [
            "10",
            "11",
            "12",
            "13",
        ],
        "color": 16753920,
    },
    "kishispo_mind001": {
        "name": "KISHISPO(JP)_Nike Mind 001",
        "url": "https://www.kishispo.net/products/list?category_id=20079&cond=t5",
        "target_sizes": [
            "10",
            "11",
            "12",
            "13",
        ],
        "color": 3447003,
    },
    "atmos_mind001": {
        "name": "ATMOS(JP)_Nike Mind 001",
        "url": "https://www.atmos-tokyo.com/search?q=HQ4307-001",
        "target_sizes": [
            "10",
            "11",
            "12",
            "13",
        ],
        "color": 10181046,
    },
    "uniontokyo_mind001": {
        "name": "UNION TOKYO(JP)_Nike Mind 001",
        "url": "https://www.uniontokyo.jp/search?q=HQ4307-001",
        "target_sizes": [
            "10",
            "11",
            "12",
            "13",
        ],
        "color": 15105570,
    },
    "uptown_mind001": {
        "name": "Uptown Deluxe(JP)_Nike Mind 001",
        "url": "https://uptowndeluxe.co.jp/?pid=191728360",
        "target_sizes": [
            "10",
            "11",
            "12",
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
    target_sizes = product["target_sizes"]
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
        if item.get("available", False) and size in target_sizes:
            found.append(size)

    return found


def filter_nike_cartable_sizes(product_key, candidate_sizes):
    product = PRODUCTS[product_key]

    html = requests.get(
        product["url"],
        headers=HEADERS,
        timeout=20,
    ).text

    cartable_sizes = []

    for size in candidate_sizes:
        patterns = [
            f'"nikeSize":"{size}"',
            f'"label":"US {size}"',
            f'US {size}',
        ]

        has_size = any(pattern in html for pattern in patterns)

        soldout_near_size = re.search(
            rf'(US {re.escape(size)}|nikeSize":"{re.escape(size)}").{{0,800}}?(soldOut|Sold Out|outOfStock|unavailable|disabled)',
            html,
            re.IGNORECASE,
        )

        if has_size and not soldout_near_size:
            cartable_sizes.append(size)

    return cartable_sizes


def check_nike_cartable(product_key):
    candidate_sizes = check_nike(product_key)

    if not candidate_sizes:
        return []

    cartable_sizes = filter_nike_cartable_sizes(
        product_key,
        candidate_sizes,
    )

    print(
        f"{product_key} cartable result: {cartable_sizes}",
        flush=True,
    )

    return cartable_sizes


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

    target_sizes = PRODUCTS["footlocker"]["target_sizes"]
    return [s for s in sizes if s in target_sizes]


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

    target_sizes = PRODUCTS["champs_95"]["target_sizes"]
    return [s for s in sizes if s in target_sizes]


JP_TARGET_KEYWORDS = [
    "HQ4307-001",
    "hq4307-001",
    "HQ4307 001",
    "hq4307 001",
    "マインド 001",
    "Mind 001",
    "MIND 001",
]

JP_SOLDOUT_KEYWORDS = [
    "SOLD OUT",
    "Sold Out",
    "sold out",
    "売り切れ",
    "品切れ",
    "在庫なし",
    "ただいま品切れ中",
    "完売",
    "抽選販売",
    "抽選受付",
]


def check_jp_page_signal(product_key):
    product = PRODUCTS[product_key]

    print(f"Checking {product_key}...", flush=True)

    html = requests.get(
        product["url"],
        headers=HEADERS,
        timeout=20,
    ).text

    print(
        f"{product_key} response received",
        len(html),
        flush=True,
    )

    has_target = any(keyword in html for keyword in JP_TARGET_KEYWORDS)
    has_soldout = any(keyword in html for keyword in JP_SOLDOUT_KEYWORDS)

    print(
        f"{product_key} has_target={has_target}, has_soldout={has_soldout}",
        flush=True,
    )

    if has_target and not has_soldout:
        return ["SIGNAL"]

    return []


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
        "nike": safe_check(
            "nike",
            lambda: check_nike_cartable("nike")
        ),
        "footlocker": safe_check(
            "footlocker",
            check_footlocker
        ),
        "champs_95": safe_check(
            "champs_95",
            check_champs
        ),
        "sws_mind001": safe_check(
            "sws_mind001",
            lambda: check_jp_page_signal("sws_mind001")
        ),
        "kishispo_mind001": safe_check(
            "kishispo_mind001",
            lambda: check_jp_page_signal("kishispo_mind001")
        ),
        "atmos_mind001": safe_check(
            "atmos_mind001",
            lambda: check_jp_page_signal("atmos_mind001")
        ),
        "uniontokyo_mind001": safe_check(
            "uniontokyo_mind001",
            lambda: check_jp_page_signal("uniontokyo_mind001")
        ),
        "uptown_mind001": safe_check(
            "uptown_mind001",
            lambda: check_jp_page_signal("uptown_mind001")
        ),
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
