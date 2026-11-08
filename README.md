# Telegram Rate Bot

A Telegram bot that shows current Armenian dram (AMD) exchange rates and converts between currencies. Rates are scraped from [rate.am](https://www.rate.am/hy/armenian-dram-exchange-rates/banks) with Selenium (headless Chrome) and cached in the background, so replies are fast.

Works on **Windows, macOS and Linux**.

## Features

- Current **USD, EUR and RUR** buy/sell rates against AMD
- Guided **currency converter** (USD, EUR, RUR, AMD): pick the source currency, then the target, then type the amount
- Inline currency buttons on the welcome message
- **/clear** to wipe the chat
- Background scraper that refreshes rates every 60 seconds and recovers automatically if Chrome crashes
- "Updated HH:MM" timestamp on every answer

## Commands

| Command | Description |
|---|---|
| `/start` | Starts a chat, sends the welcome photo and currency buttons |
| `/rates` | Shows current USD, EUR and RUR rates |
| `/convert` | Converts an amount from one currency to another |
| `/clear` | Clears the chat and cancels any unfinished `/convert` |
| `/help` | Shows all commands |

The command list is defined once in `COMMANDS` in `tbot.py`. `/help` and the Telegram command menu are both built from it.

## Project structure

```
Telegram_Bot/
├── tbot.py             # Bot: commands, buttons, converter, /clear
├── scraper.py          # Selenium scraper with background refresh and cache
├── exchange-rate.jpg   # Welcome image sent on /start
├── requirements.txt
├── .env                # Your bot token
├── .gitignore
└── README.md
```

## Requirements

- **Python 3.9+** (the bot uses `zoneinfo`)
  - Windows: download from [python.org](https://www.python.org/downloads/) and tick **"Add python.exe to PATH"** in the installer
  - macOS: `brew install python` or download from [python.org](https://www.python.org/downloads/)
  - Linux: usually preinstalled; otherwise `sudo apt install python3 python3-venv`
- **Google Chrome** installed (Selenium downloads the matching driver automatically)
  - Windows / macOS: install from [google.com/chrome](https://www.google.com/chrome/)
  - Linux: install the `.deb` from the Chrome website (Ubuntu doesn't ship Chrome in `apt` by default)
- **Git** (only if you clone the repo)
- A bot token from [@BotFather](https://t.me/BotFather)

## Setup

### 1. Get the code

```bash
git clone <your-repo-url>
cd Telegram_Bot
```

### 2. Create a virtual environment

| OS | Command |
|---|---|
| Windows (PowerShell / CMD) | `py -m venv venv` |
| macOS / Linux | `python3 -m venv venv` |

### 3. Activate it

| OS | Command |
|---|---|
| Windows (PowerShell) | `venv\Scripts\Activate.ps1` |
| Windows (CMD) | `venv\Scripts\activate.bat` |
| macOS / Linux | `source venv/bin/activate` |

You should see `(venv)` at the start of your terminal line.

> **Windows PowerShell says "running scripts is disabled"?** Run this once, then activate again:
> ```powershell
> Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
> ```

### 4. Install dependencies

Same command on every OS (with the venv active):

```bash
pip install -r requirements.txt
```

If you are building `requirements.txt` yourself, it needs:

```
pyTelegramBotAPI
selenium
python-dotenv
tzdata
```

`tzdata` is required on **Windows** (it has no built-in time zone database, so `zoneinfo` fails without it). It's harmless on macOS and Linux.

Keep `pyTelegramBotAPI` up to date (`pip install -U pyTelegramBotAPI`), since `/clear` uses bulk message deletion.

### 5. Configure

Create a file named `.env` next to `tbot.py` with this content:

```
TOKEN=123456:your-telegram-bot-token
```

- **Windows:** make sure the file is really called `.env` and not `.env.txt` (enable "File name extensions" in File Explorer to check).
- The bot exits with an error if `TOKEN` is missing.

### 6. Run

| OS | Command |
|---|---|
| Windows | `python tbot.py` |
| macOS / Linux | `python3 tbot.py` |

Inside an activated venv, `python tbot.py` works on every OS. Stop the bot with `Ctrl+C`. The scraper and Chrome are shut down cleanly.

## Settings

Settings in `tbot.py`:

| Setting | Default | Description |
|---|---|---|
| `STATE_TTL` | `300` | Seconds before an unfinished `/convert` flow expires |
| `TZ` | `Asia/Yerevan` | Time zone used for the "Updated" line(Also u can change timezone into yours) |
| `PHOTO` | `exchange-rate.jpg` | Welcome image, looked up next to `tbot.py` |
| `ERROR_TEXT` | `⚠️ Couldn't load rates...` | Message shown when rates can't be loaded |
| `CLEAR_SWEEP` | `300` | How many recent message IDs `/clear` tries to delete |

Settings in `scraper.py`:

| Setting | Default | Description |
|---|---|---|
| `URL` | rate.am banks page | Page the rates are scraped from |
| `ROW_SELECTOR` | `div.group.flex.items-center.h-10` | CSS selector for the rate rows |
| `REFRESH_EVERY` | `60` | Seconds between background refreshes |
| `RETRY_AFTER` | `10` | Seconds to wait before retrying after a failed scrape |
| `FIRST_LOAD_TIMEOUT` | `25` | Seconds a request waits for the first load of rates |

The `CURRENCIES` dict maps each currency to its flag and the column indexes of its buy and sell values in a scraped row. `SYMBOLS` holds the currency symbols used in the converter ($, €, ₽, ֏).

## How it works

### Scraper

`scraper.py` starts a background thread that keeps one headless Chrome instance open and re-reads the rates page every `REFRESH_EVERY` seconds. The latest rows are kept in an in-memory cache. Bot handlers never open a browser themselves: they just read the cache through `get_rows()`.

If a scrape fails, the driver is restarted and the scraper retries after `RETRY_AFTER` seconds. If the very first load takes longer than `FIRST_LOAD_TIMEOUT`, the user gets the error message instead of hanging.

### Converter

`/convert` is a guided flow:

1. Pick the source currency (inline buttons)
2. Pick the target currency
3. Type the amount

Conversions go through AMD: the source amount is turned into AMD at the **buy** rate, then into the target currency at the **sell** rate. Amounts like `100`, `1,000.50`, `1 000` and `100,5` are all understood. The flow expires after `STATE_TTL` seconds of inactivity.

### /clear

Telegram bots can't read chat history, so `/clear` deletes the last `CLEAR_SWEEP` message IDs in batches of 100 (the IDs in a private chat are sequential). It also resets any unfinished `/convert`.

- Telegram only lets bots delete a user's messages that are less than 48 hours old. Older ones stay.
- In groups the bot needs admin rights with the "Delete messages" permission.
- If a chat has more than `CLEAR_SWEEP` recent messages, run `/clear` again or raise the value.
- If bulk deletion fails (for example an old library version), the bot falls back to deleting messages one by one, which is slower.

## Troubleshooting

| Problem | Fix |
|---|---|
| `TOKEN is missing in .env` | Create the `.env` file in the same folder you run the bot from (on Windows check it isn't `.env.txt`) |
| `ZoneInfoNotFoundError` (mostly Windows) | `pip install tzdata` |
| `python` / `python3: command not found` | Windows: use `py`. macOS / Linux: use `python3`. Or activate the venv first and use `python` |
| PowerShell blocks `Activate.ps1` | `Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned`, or use CMD and `activate.bat` |
| "Couldn't load rates, try again in a minute" | The scraper hasn't loaded rates yet or rate.am changed. Check the terminal for scrape errors and, if the layout changed, update `ROW_SELECTOR` |
| Chrome not found / driver errors | Install Google Chrome in its default location and make sure you have internet access (Selenium downloads the driver on first run) |
| A Chrome window appears | Make sure `--headless=new` is still in `_make_driver()` in `scraper.py` |
| macOS asks to allow Chrome / Terminal | Allow it in System Settings, then restart the bot |
| `/clear` is slow | Upgrade `pyTelegramBotAPI` so bulk deletion works |
