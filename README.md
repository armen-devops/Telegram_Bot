# 💱 Telegram Exchange Rate Bot

A Telegram bot that shows up-to-date bank exchange rates in Armenia. It scrapes [rate.am] with Selenium (headless Chrome) and lets you check rates and convert currencies right from the chat.

## ✨ Features

- 📊 Live bank rates for **USD / EUR / RUR** against **AMD**
- 🔄 Guided currency converter (pick *from* → *to*, then type the amount)
- ⚡ Results cached for 120 seconds, so repeated requests are instant and rate.am isn't overloaded
- 🕶️ Headless Chrome, with no browser window popping up
- 📋 Command menu built into Telegram

## 🤖 Commands

| Command    | Description                                  |
|------------|----------------------------------------------|
| `/start`   | Start the bot and see the welcome message    |
| `/rates`   | Show current bank exchange rates             |
| `/convert` | Convert between currencies (e.g. `$ ➜ €`)    |
| `/help`    | List all available commands                  |

## 🗂️ Project Structure

```
Telegram_Bot/
├── Bot_folder/        # Bot source code (handlers, scraper)
├── Photo/             # Images used by the bot
├── .vscode/           # Editor settings
├── .env               # Secrets (bot token)
├── .gitignore
├── requirements.txt   # Python dependencies
└── README.md
```

## 🚀 Getting Started

### 1. Prerequisites

- Python 3.10+
- Google Chrome installed
- A bot token from [@BotFather](https://t.me/BotFather)

### 2. Clone and set up the environment

```bash
git clone <repo-url>
cd Telegram_Bot

python3 -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate

pip install -r requirements.txt
```

### 3. Configure the bot token

Create a `.env` file in the project root:

```env
BOT_TOKEN=your_telegram_bot_token_here
```

> ⚠️ Never commit `.env`. It is already listed in `.gitignore`.

### 4. Run

```bash
python Bot_folder/tbot.py
```

Then open your bot in Telegram and send `/start`.

## 🧰 Tech Stack

- [pyTelegramBotAPI (telebot)](https://github.com/eternnoir/pyTelegramBotAPI)
- [Selenium](https://www.selenium.dev/) + headless Chrome
- [python-dotenv](https://pypi.org/project/python-dotenv/)

## 🛠️ Troubleshooting

- **Chrome window appears / driver errors:** make sure Chrome is up to date and the bot is started with the headless options enabled.
- **Rates are empty:** rate.am may have changed its page layout, so the scraper selectors may need updating.
- **Bot doesn't respond:** check that `BOT_TOKEN` in `.env` is correct and the venv is activated.

## 📄 License

This project is for personal and educational use.
