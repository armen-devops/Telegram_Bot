# 🇦🇲 Rate Bot

A Telegram bot that shows current Armenian dram (AMD) exchange rates for USD, EUR and RUR, and converts amounts between currencies with a guided, button-based flow. Rates are scraped live from [rate.am](https://www.rate.am/hy/armenian-dram-exchange-rates/banks) using Selenium and headless Chrome.

## Features

- `/start` shows a welcome image and inline buttons for each currency
- `/rates` shows buy/sell rates for USD, EUR and RUR
- `/convert` is a step-by-step converter between AMD, USD, EUR and RUR
- `/help` shows all available commands
- Every rates and conversion message ends with an **"Updated HH:MM"** line (Yerevan time), so you can see how fresh the data is
- Results are cached for 2 minutes, so repeated requests don't re-scrape the site
- If a scrape fails, the bot restarts the browser and falls back to the last cached rates when available. The "Updated" time then shows how old they are
- Flexible amount input with validation (see below)
- Unfinished conversions expire after 5 minutes
- The welcome image is uploaded to Telegram once and reused afterwards
- Errors are logged with full tracebacks, and the bot refuses to start if the token is missing

## Usage

| Command | Description |
|---|---|
| `/start` | Welcome message and currency buttons |
| `/rates` | Buy/sell rates for all supported currencies |
| `/convert` | Guided currency converter (see below) |
| `/help` | Shows all available commands |

### Converting currencies

1. Send `/convert`
2. Tap the currency you want to convert **from**
3. Tap the currency you want to convert **to**
4. Type the amount

Example result:

```
$ USD ➜ € EUR

100.00 USD = 92.35 EUR
1 EUR = 1.08 USD

🕒 Updated 14:32
```

The rate line is always shown with the larger number first (for example `1 USD = 364.03 AMD` instead of `1 AMD = 0.00 USD`).

### Accepted amounts

| Input | Read as |
|---|---|
| `100` | 100 |
| `12,5` or `12.5` | 12.5 |
| `1,000` | 1000 |
| `1 000 000` | 1000000 |
| `1,234.56` | 1234.56 |

Zero, negative numbers, `inf`, `nan`, text, and values of 1,000,000,000,000 or more are rejected, and the bot asks for a positive number. If the session expires (5 minutes of inactivity), just send `/convert` again.

### How conversion works

The bot uses the first bank row on the rate.am list. Converting a foreign currency to AMD uses the **buy** rate, and converting from AMD uses the **sell** rate. For two foreign currencies, the amount goes through AMD first.

## Project structure

```
.
├── tbot.py             # Telegram bot: handlers, convert flow, formatting
├── scraper.py          # Selenium scraper with caching and driver recovery
├── exchange-rate.jpg   # Image sent with /start
├── .env                # Your bot token (not committed)
└── .gitignore
```

## Requirements

- Python 3.9+
- Google Chrome installed (Selenium 4.6+ downloads a matching driver automatically)
- A Telegram bot token from [@BotFather](https://t.me/BotFather)
- Python packages: `pyTelegramBotAPI`, `selenium`, `python-dotenv`
- On Windows only: `tzdata` (Python's `zoneinfo` needs it there)

## Setup

1. Clone the repository:

   ```bash
   git clone <your-repo-url>
   cd <your-repo-folder>
   ```

2. Install dependencies:

   ```bash
   pip install pyTelegramBotAPI selenium python-dotenv
   ```

   On Windows, also run `pip install tzdata`.

3. Create a `.env` file in the project root:

   ```
   TOKEN=your_telegram_bot_token
   ```

4. Make sure `exchange-rate.jpg` is in the project root.

5. Run the bot:

   ```bash
   python tbot.py
   ```

   If `TOKEN` is missing, the bot exits right away with `TOKEN is missing in .env`.

## Configuration

Settings in `scraper.py`:

| Setting | Default | Description |
|---|---|---|
| `URL` | rate.am banks page | Page to scrape |
| `ROW_SELECTOR` | `div.group.flex.items-center.h-10` | CSS selector for rate rows |
| `CACHE_TTL` | `120` | Seconds to cache scraped rates |

Settings in `tbot.py`:

| Setting | Default | Description |
|---|---|---|
| `STATE_TTL` | `300` | Seconds before an unfinished `/convert` flow expires |
| `TZ` | `Asia/Yerevan` | Time zone used for the "Updated" line |
| `PHOTO` | `exchange-rate.jpg` | Welcome image, looked up next to `tbot.py` |
| `ERROR_TEXT` | `⚠️ Couldn't load rates...` | Message shown when rates can't be loaded |

The `CURRENCIES` dict maps each currency to its flag and the column indexes of its buy/sell values, and `SYMBOLS` / `ALL_CUR` control what the converter shows. If rate.am changes its layout, `ROW_SELECTOR` is the first thing to update.

## Notes

- Chrome runs headless with `--no-sandbox` and `--disable-dev-shm-usage`, which makes it work in Docker and on small servers.
- The scraper uses a single shared browser instance guarded by a lock, so concurrent requests are handled safely. If the browser crashes or fails to close, it is discarded and started fresh on the next request.
- Converter progress is kept in memory per chat, so it resets when the bot restarts.
- Check the logs first when something breaks. Scrape and conversion failures are logged with the full error.
- Never commit your `.env` file. If a token leaks, revoke it in @BotFather and generate a new one.

## Disclaimer

Rates are scraped from a third-party site and are for information only. They may be delayed or inaccurate, so check with your bank before making any transaction.