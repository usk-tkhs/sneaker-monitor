# Sneaker Restock Monitor

Discord notification based sneaker restock monitor using GitHub Actions.

This project monitors sneaker stock availability across multiple stores and sends Discord notifications when target sizes are restocked.

---

# Features

- Discord notifications
- GitHub Actions based automation
- Separate lightweight / heavyweight monitors
- Shopify API monitoring
- Multi-store support
- US size filtering
- Automatic scheduled execution

---

# Monitored Stores

## Lightweight (1 minute monitoring)

### KITH Canada
- New Balance 992 "Argon"

### KITH USA
- New Balance 990v3 "Hallow"
- New Balance 992 "Argon"

### UP THERE Australia
- AIR MAX 95 neon

---

## Heavyweight (5 minute monitoring)

### NIKE Australia
- AIR MAX 95 neon

### Footlocker US
- AIR MAX 95 neon

### Champs Sports US
- AIR MAX 95 neon

---

# Target Sizes

The following sizes are monitored:

```python
TARGET_SIZES = [
    "9",
    "9.5",
    "10",
    "10.5",
    "11",
    "11.5",
    "12",
    "12.5",
    "13"
]
```

---

# Project Structure

```text
.
├── monitor_shopify.py
├── monitor_heavy.py
├── requirements.txt
└── .github
    └── workflows
        ├── shopify.yml
        └── heavy.yml
```

---

# Requirements

- Python 3.9+
- GitHub account
- Discord server
- Discord Webhook URL

---

# Installation

## Clone repository

```bash
git clone https://github.com/YOUR_USERNAME/sneaker-monitor.git
cd sneaker-monitor
```

---

## Install dependencies

```bash
pip3 install -r requirements.txt
```

---

# Discord Webhook Setup

Create a Discord Webhook:

1. Open Discord
2. Server Settings
3. Integrations
4. Webhooks
5. New Webhook
6. Copy Webhook URL

---

# GitHub Secrets Setup

Go to:

```text
Repository
→ Settings
→ Secrets and variables
→ Actions
→ New repository secret
```

Create:

```text
Name:
DISCORD_WEBHOOK_URL
```

```text
Value:
YOUR_DISCORD_WEBHOOK
```

---

# GitHub Actions

## Shopify Fast Monitor

Runs every minute.

```yaml
.github/workflows/shopify.yml
```

Monitors:
- KITH
- UP THERE

---

## Heavy Monitor

Runs every 5 minutes.

```yaml
.github/workflows/heavy.yml
```

Monitors:
- Nike
- Footlocker
- Champs Sports

---

# Manual Execution

GitHub:

```text
Actions
→ Select workflow
→ Run workflow
```

---

# Example Notification

```text
🚨 RESTOCK DETECTED 🚨

━━━━━━━━━━━━━━━━━━━━
👟 NIKE(AU)_AIR MAX 95 neon (men's)
📏 Size: US 10, US 10.5
🔗 https://www.nike.com/au/t/...

━━━━━━━━━━━━━━━━━━━━
👟 KITH(CA)_New Balance Made in USA 992 - Argon
📏 Size: US 9.5, US 10
🔗 https://ca.kith.com/products/nbu992ki
```

---

# Notes

- Shopify stores are monitored via `.js` API endpoints
- Nike / Footlocker / Champs use HTML parsing
- GitHub Actions cron uses UTC timezone
- Nighttime monitoring is most effective for restocks

---

# Recommended Monitoring Times (JST)

Most restocks occur during:

```text
23:00 - 04:00 JST
```

---

# Future Improvements

- Duplicate notification suppression
- State persistence
- Discord embeds
- Multi-webhook support
- Region-specific monitoring
- Slack / LINE support
- Auto checkout support

---

# Disclaimer

This project is intended for personal monitoring purposes only.

Use responsibly and respect store Terms of Service.
