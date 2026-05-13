import os
import requests

WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

def notify(msg):
    r = requests.post(
        WEBHOOK_URL,
        json={"content": msg}
    )
    print("status:", r.status_code)
    print("response:", r.text)

def main():
    notify("TEST SUCCESS 🎉")

if __name__ == "__main__":
    main()