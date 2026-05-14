# Sneaker Restock Monitor

Discord notification based sneaker restock monitor using GitHub Actions.

Last updated: 2026-05-14 22:52:19 JST

---

## Features

- Discord notifications
- Shopify Fast Monitor
- Heavy Monitor
- Duplicate notification prevention
- Store-level state management
- Discord Embed notifications
- JST timestamp
- Store-specific embed colors

---

## Monitoring Frequency

| Monitor | Frequency |
|---|---|
| Shopify Fast Monitor | Every 1 minute |
| Heavy Monitor | Every 5 minutes |

---

## Target Sizes

US 9 - US 13 including half sizes.

---

## GitHub Actions

```text
.github/workflows/shopify.yml
.github/workflows/heavy.yml
.github/workflows/update-readme.yml
```

---

## Required Secret

```text
DISCORD_WEBHOOK_URL
```

---

## Notes

- Shopify stores use `.js` API endpoints
- Heavy monitor uses HTML parsing
- GitHub Actions uses UTC cron
- Discord notifications use Embed format
- Duplicate notifications are suppressed by store-level state

---

## Disclaimer

Personal use only.
