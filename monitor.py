import os
import requests
from dotenv import load_dotenv

# .env 読み込み
load_dotenv()

WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL") or os.getenv("DISCORD_WEBHOOK")

def notify(message: str):
    if not WEBHOOK_URL:
        print("Webhook URL not found")
        return

    data = {
        "content": message
    }

    res = requests.post(WEBHOOK_URL, json=data)

    print("status:", res.status_code)
    print("response:", res.text)

# ===== MAIN =====
def main():
    notify("TEST SUCCESS 🎉")

if __name__ == "__main__":
    main()