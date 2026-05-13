import requests, re, json

# ===== 通知設定 =====
DISCORD_WEBHOOK = "https://discord.com/api/webhooks/1504122014040985793/wfITyGv3N6QH0dlrDaUkLQwnQjOw3hfI24CS4qnTHHjJ8eHGLPmNB7GWkv5x6o9VrxVZ"

TARGET_SIZES = ["9.5","10","10.5","11","12","13"]

def notify(msg):
    requests.post(DISCORD_WEBHOOK, json={"content": msg})

# ===== KITH =====
def check_kith():
    url = "https://ca.kith.com/products/nbu992ki.js"
    data = requests.get(url).json()
    found = []

    for v in data["variants"]:
        size = v["title"].replace("US ","")
        if size in TARGET_SIZES and v["available"]:
            found.append(size)

    return found

# ===== NIKE =====
def check_nike():
    url = "https://www.nike.com/au/t/nike-air-max-95-big-bubble-og-mens-shoes-zhFhFmlx/HM4740-001"
    html = requests.get(url, headers={"User-Agent":"Mozilla/5.0"}).text
    data = re.search(r'INITIAL_REDUX_STATE=(.*?);</script>', html)
    if not data:
        return []
    js = json.loads(data.group(1))
    skus = js["Threads"]["products"]["HM4740-001"]["availableSkus"]

    found = []
    for s in skus:
        if s["nikeSize"] in TARGET_SIZES and s["availability"]["inStock"]:
            found.append(s["nikeSize"])
    return found

# ===== FOOTLOCKER =====
def check_footlocker():
    url = "https://www.footlocker.com/product/nike-air-max-95-mens/H4740001.html"
    html = requests.get(url, headers={"User-Agent":"Mozilla/5.0"}).text
    sizes = re.findall(r'"size":"(.*?)".*?"inventoryStatus":"Available"', html)
    return [s for s in sizes if s in TARGET_SIZES]

# ===== MAIN =====
def main():
    nike = check_nike()
    footlocker = check_footlocker()
    kith = check_kith()

    if nike or footlocker or kith:
        msg = f"🚨 RESTOCK!\nNike:{nike}\nFootlocker:{footlocker}\nKITH:{kith}"
        notify(msg)

if __name__ == "__main__":
    main()
