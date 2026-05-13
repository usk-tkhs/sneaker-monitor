import os
import re
import json
import requests

WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

TARGET_SIZES = ["9.5", "10", "10.5", "11", "12", "13"]

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

def notify(msg):
    r = requests.post(
        WEBHOOK_URL,
        json={"content": msg}
    )

    print("status:", r.status_code)

# =========================
# KITH
# =========================
def check_kith():

    url = "https://ca.kith.com/products/nbu992ki.js"

    data = requests.get(url).json()

    found = []

    for v in data["variants"]:

        size = v["title"].replace("US ", "")

        if size in TARGET_SIZES and v["available"]:
            found.append(size)

    return found

# =========================
# NIKE
# =========================
def check_nike():

    url = "https://www.nike.com/au/t/nike-air-max-95-big-bubble-og-mens-shoes-zhFhFmlx/HM4740-001"

    html = requests.get(url, headers=HEADERS).text

    match = re.search(
        r'INITIAL_REDUX_STATE=(.*?);</script>',
        html
    )

    if not match:
        return []

    js = json.loads(match.group(1))

    try:
        skus = js["Threads"]["products"]["HM4740-001"]["availableSkus"]
    except:
        return []

    found = []

    for s in skus:

        if (
            s["nikeSize"] in TARGET_SIZES
            and s["availability"]["inStock"]
        ):
            found.append(s["nikeSize"])

    return found

# =========================
# FOOTLOCKER
# =========================
def check_footlocker():

    url = "https://www.footlocker.com/product/nike-air-max-95-mens/H4740001.html"

    html = requests.get(url, headers=HEADERS).text

    sizes = re.findall(
        r'"size":"(.*?)".*?"inventoryStatus":"Available"',
        html
    )

    return [s for s in sizes if s in TARGET_SIZES]

# =========================
# MAIN
# =========================
def main():

    nike = check_nike()
    footlocker = check_footlocker()
    kith = check_kith()

    print("Nike:", nike)
    print("Footlocker:", footlocker)
    print("KITH:", kith)

    if nike or footlocker or kith:

        msg = (
            "🚨 RESTOCK DETECTED 🚨\n\n"
            f"Nike: {nike}\n"
            f"Footlocker: {footlocker}\n"
            f"KITH: {kith}"
        )

        notify(msg)

if __name__ == "__main__":
    main()