import os
import re
import json
import requests

from datetime import datetime, timezone, timedelta

WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

TARGET_SIZES = ["9", "9.5", "10", "10.5", "11", "11.5", "12", "12.5", "13"]

PRODUCTS = {
    "nike": {
        "name": "NIKE(AU)_AIR MAX 95 neon (men's)",
        "url": "https://www.nike.com/au/t/nike-air-max-95-big-bubble-og-mens-shoes-zhFhFmlx/HM4740-001",
        "color": 16711680,
    },
    "footlocker": {
        "name": "Footlocker(US)_AIR MAX 95 neon (men's)",
        "url": "https://www.footlocker.com/product/nike-air-max-95-mens/H4740001.html",
        "color": 16753920,
    },
    "upthere_95": {
        "name": "UPTHERE(AU)_AIR MAX 95 neon (men's)",
        "url": "https://uptherestore.com/products/air-max-95-og-black-neon-yellow-cool-grey",
        "api_url": "https://uptherestore.com/products/air-max-95-og-black-neon-yellow-cool-grey.js",
        "color": 3447003,
    },
    "champs_95": {
        "name": "Champs(US)_AIR MAX 95 neon (men's)",
        "url": "https://www.champssports.com/product/nike-air-max-95-mens/HM4740001.html",
        "color": 16776960,
    },
    "kith": {
        "name": "KITH(CA)_New Balance Made in USA 992 - Argon",
        "url": "https://ca.kith.com/collections/mens-footwear/products/nbu992ki",
        "api_url": "https://ca.kith.com/products/nbu992ki.js",
        "color": 10181046,
    },
    "kith_usa_990v3": {
        "name": "KITH(US)_New Balance Made in USA 990v3 - Hallow",
        "url": "https://kith.com/products/nbu990kt3",
        "api_url": "https://kith.com/products/nbu990kt3.js",
        "color": 10181046,
    },
    "kith_usa_992": {
        "name": "KITH(US)_New Balance Made in USA 992 - Argon",
        "url": "https://kith.com/products/nbu992ki",
        "api_url": "https://kith.com/products/nbu992ki.js",
        "color": 10181046,
    },
}

HEADERS = {"User-Agent": "Mozilla/5.0"}


# =========================
# STORE STATE MANAGEMENT
# =========================
def get_new_sizes(product_key, current_sizes, state):

    previous_sizes = state.get(
        product_key,
        []
    )

    new_sizes = []

    for size in current_sizes:

        if size not in previous_sizes:
            new_sizes.append(size)

    return new_sizes


def update_store_state(product_key, sizes, state):

    state[product_key] = sizes


# =========================
# DISCORD EMBED
# =========================
def notify_embeds(embeds):

    payload = {
        "embeds": embeds
    }

    r = requests.post(
        WEBHOOK_URL,
        json=payload
    )

    print("Discord status:", r.status_code)
    print("Discord response:", r.text)


# =========================
# STATE FILE
# =========================
STATE_FILE = "stock_state.json"

JST = timezone(timedelta(hours=9))


def get_jst_now():
    return datetime.now(JST).strftime("%Y-%m-%d %H:%M:%S JST")


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
# HEALTH CHECK
# =========================
def should_send_healthcheck(state):

    today = datetime.now(timezone.utc).strftime(
        "%Y-%m-%d"
    )

    last_healthcheck = state.get(
        "last_healthcheck"
    )

    return last_healthcheck != today


def send_healthcheck(state):
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

    state["last_healthcheck"] = datetime.now(timezone.utc).strftime("%Y-%m-%d")
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

    print("Checking Footlocker...", flush=True)

    url = PRODUCTS["footlocker"]["url"]

    html = requests.get(

        url,

        headers=HEADERS,

        timeout=20

    ).text

    print("Footlocker response received", len(html), flush=True)

    sizes = re.findall(

        r'"size":"([^"]+)".{0,500}?"inventoryStatus":"Available"',

        html,

    )

    print("Footlocker parsed", sizes, flush=True)

    return [s for s in sizes if s in TARGET_SIZES]


'''
def check_footlocker():
    html = requests.get(PRODUCTS["footlocker"]["url"], headers=HEADERS, timeout=20).text

    sizes = re.findall(
        r'"size":"(.*?)".*?"inventoryStatus":"Available"',
        html,
    )

    return [s for s in sizes if s in TARGET_SIZES]
'''


def check_champs():

    print("Checking Champs...", flush=True)

    url = PRODUCTS["champs_95"]["url"]

    html = requests.get(

        url,

        headers=HEADERS,

        timeout=20

    ).text

    print("Champs response received", len(html), flush=True)

    sizes = re.findall(

        r'"size":"([^"]+)".{0,500}?"inventoryStatus":"Available"',

        html,

    )

    print("Champs parsed", sizes, flush=True)

    return [s for s in sizes if s in TARGET_SIZES]


'''
def check_champs():

    url = PRODUCTS["champs_95"]["url"]

    html = requests.get(
        url,
        headers=HEADERS,
        timeout=20
    ).text

    sizes = re.findall(
        r'"size":"([^"]+)".{0,500}?"inventoryStatus":"Available"',
        html,
    )

    return [s for s in sizes if s in TARGET_SIZES]
'''


# =========================
# DISCORD EMBED FORMAT
# =========================
def create_embed(product_key, sizes):
    product = PRODUCTS[product_key]

    size_text = " / ".join(
        f"US {s}" for s in sizes
    )

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


def safe_check(name, func):

    try:

        print(f"Checking {name}...", flush=True)

        result = func()

        print(f"{name} result: {result}", flush=True)

        return result

    except Exception as e:

        print(f"{name} error: {e}", flush=True)

        return []


# =========================
# MAIN
# =========================
def main():

    state = load_state()

    results = {
        "nike": safe_check("nike", check_nike),
        "footlocker": safe_check("footlocker", check_footlocker),
        "champs_95": safe_check("champs", check_champs),
    }

    print(results)

    if should_send_healthcheck(state):
        send_healthcheck(state)

    embeds = []

    for product_key, current_sizes in results.items():

        new_sizes = get_new_sizes(
            product_key,
            current_sizes,
            state,
        )

        if new_sizes:

            embed = create_embed(
                product_key,
                new_sizes,
            )

            embeds.append(embed)

        update_store_state(
            product_key,
            current_sizes,
            state,
        )

    save_state(state)

    if embeds:
        notify_embeds(embeds)
    else:
        print("No new stock.")


if __name__ == "__main__":
    main()