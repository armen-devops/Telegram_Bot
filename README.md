# 🇦🇲 Rate Bot

A Telegram bot that shows current Armenian dram (AMD) exchange rates for USD, EUR and RUR, and converts amounts between currencies. Rates are scraped live from [rate.am](https://www.rate.am/hy/armenian-dram-exchange-rates/banks) using Selenium and headless Chrome.

## Features

- `/start` shows a welcome image and inline buttons for each currency
- `/rates` shows buy/sell rates for USD, EUR and RUR
- `/convert` converts between AMD, USD, EUR and RUR
- `/help` shows all available commands
- Results are cached for 2 minutes, so repeated requests don't re-scrape the site
- If a scrape fails, the bot restarts the browser and falls back to the last cached rates when available

## Usage

| Command | Description |
|---|---|
| `/start` | Welcome message and currency buttons |
| `/rates` | Buy/sell rates for all supported currencies |
| `/convert 100 usd` | Convert 100 USD to AMD |
| `/convert 40000 amd usd` | Convert 40,000 AMD to USD |
| `/convert 100 usd rub` | Convert 100 USD to RUR via AMD |
| `/help`| Shows all available commands |

Aliases are accepted: `rub` / `rouble` for RUR, `dollar` for USD, `euro` for EUR. Decimals can use `.` or `,`.

### How conversion works

The bot uses the first bank row on the rate.am list. Converting a foreign currency to AMD uses the **buy** rate, and converting from AMD uses the **sell** rate. For two foreign currencies, the amount goes through AMD first.

## Project structure

```
.
├── tbot.py             # Telegram bot: handlers, formatting, conversion logic
├── scraper.py          # Selenium scraper with caching and driver recovery
├── exchange-rate.jpeg  # Image sent with /start
├── .env                # Your bot token (not committed)
└── .gitignore
```

## Requirements

- Python 3.9+
- Google Chrome installed (Selenium 4.6+ downloads a matching driver automatically)
- A Telegram bot token from [@BotFather](https://t.me/BotFather)

## Setup

1. Clone the repository:

   ```bash
   git clone <your-repo-url>
   cd <your-repo-folder>
   ```

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Create a `.env` file in the project root:

   ```
   TOKEN=your_telegram_bot_token
   ```

4. Make sure `exchange-rate.jpeg` is in the project root.

5. Run the bot:

   ```bash
   python tbot.py
   ```

## Configuration

Settings live at the top of `scraper.py`:

| Setting | Default | Description |
|---|---|---|
| `URL` | rate.am banks page | Page to scrape |
| `ROW_SELECTOR` | `div.group.flex.items-center.h-10` | CSS selector for rate rows |
| `CACHE_TTL` | `120` | Seconds to cache scraped rates |

If rate.am changes its layout, `ROW_SELECTOR` is the first thing to update.

## Notes

- Chrome runs headless with `--no-sandbox` and `--disable-dev-shm-usage`, which makes it work in Docker and on small servers.
- The scraper uses a single shared browser instance guarded by a lock, so concurrent requests are handled safely.
- Never commit your `.env` file. If a token leaks, revoke it in @BotFather and generate a new one.

## Disclaimer

Rates are scraped from a third-party site and are for information only. They may be delayed or inaccurate, so check with your bank before making any transaction.
