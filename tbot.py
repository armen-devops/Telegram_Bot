import logging, os
import scraper as rates

from dotenv import load_dotenv
from telebot import TeleBot, types

load_dotenv()
logging.basicConfig(level=logging.INFO)
bot = TeleBot(os.getenv("TOKEN"))

COMMANDS = [
    ("start", "Starts a chat"),
    ("rates", "Shows current USD, EUR and RUR rates"),
    ("convert", "Converts rate from one to another"),
    ("clear", "Deletes recent messages in this chat"),
    ("help", "Shows all commands"),
]

ALIASES = {"RUB": "RUR", "ROUBLE": "RUR", "DOLLAR": "USD", "EURO": "EUR"}

CURRENCIES = {
    "USD": ("🇺🇸", 0, 1),
    "EUR": ("🇪🇺", 2, 3),
    "RUR": ("🇷🇺", 4, 5),
}
SUPPORTED = set(CURRENCIES) | {"AMD"}

def menu():
    kb = types.InlineKeyboardMarkup()
    kb.add(*[
        types.InlineKeyboardButton(f"{flag} {cur}", callback_data=f"cur:{cur}")
        for cur, (flag, _, _) in CURRENCIES.items()
    ])
    return kb


def format_rows(cur, row):
    flag, buy_i, sell_i = CURRENCIES[cur]
    return f"{flag} {cur}\nBuy: {row[buy_i]}\nSell: {row[sell_i]}"


@bot.message_handler(commands=["start"])
def start(message):
    with open("exchange-rate.jpeg", "rb") as photo:
        bot.send_photo(message.chat.id, photo)
    bot.send_message(message.chat.id, "Բարի գալուստ Rate բոտ", reply_markup=menu())

@bot.message_handler(commands=["help"])
def help_cmd(message):
    text = "Available commands:\n\n" + "\n".join(
        f"/{name} - {desc}" for name, desc in COMMANDS
    )
    bot.send_message(message.chat.id, text)

@bot.message_handler(commands=["rates"])
def rates_cmd(message):
    bot.send_chat_action(message.chat.id, "typing")
    try:
        row = rates.get_rows()[0]
        text = "\n\n".join(format_rows(cur, row) for cur in CURRENCIES)
        bot.send_message(message.chat.id, text)
    except Exception:
        bot.send_message(message.chat.id, "⚠️ Couldn't load rates, try again in a minute.")


@bot.callback_query_handler(func=lambda c: c.data.startswith("cur:"))
def on_currency(call):
    cur = call.data.split(":")[1]
    bot.answer_callback_query(call.id)
    try:
        row = rates.get_rows()[0]
        bot.send_message(call.message.chat.id, format_rows(cur, row))
    except Exception:
        bot.send_message(call.message.chat.id, "⚠️ Couldn't load rates, try again in a minute.")


def parse_convert(text):
    parts = text.split()[1:]
    if len(parts) not in (2, 3):
        raise ValueError
    amount = float(parts[0].replace(",", "."))
    if amount <= 0:
        raise ValueError
    names = [ALIASES.get(p.upper(), p.upper()) for p in parts[1:]]
    src = names[0]
    dest = names[1] if len(names) == 2 else "AMD"
    return amount, src, dest


def to_amd(amount, cur, row):
    if cur == "AMD":
        return amount
    _, buy_i, _ = CURRENCIES[cur]
    return amount * float(row[buy_i])


def from_amd(amd, cur, row):
    if cur == "AMD":
        return amd
    _, _, sell_i = CURRENCIES[cur]
    return amd / float(row[sell_i])


@bot.message_handler(commands=["convert"])
def convert_cmd(message):
    usage = ("Usage:\n"
             "/convert 100 usd → AMD\n"
             "/convert 40000 amd usd\n"
             "/convert 100 usd rub`")
    try:
        amount, src, dest = parse_convert(message.text)
    except ValueError:
        bot.send_message(message.chat.id, usage)
        return

    if src not in SUPPORTED or dest not in SUPPORTED or src == dest:
        bot.send_message(message.chat.id, usage)
        return

    try:
        row = rates.get_rows()[0]
        result = from_amd(to_amd(amount, src, row), dest, row)
    except Exception:
        bot.send_message(message.chat.id, "⚠️ Couldn't load rates, try again in a minute.")
        return

    bot.send_message(
        message.chat.id,
        f"{amount:,.2f} {src} = {result:,.2f} {dest}\n"
        f"Effective rate: 1 {src} = {result / amount:,.2f} {dest}",
    )

CLEAR_LIMIT = 500

@bot.message_handler(commands=["clear"])
def clear_cmd(message):
    chat_id = message.chat.id
    newest = message.message_id
    oldest = max(1, newest - CLEAR_LIMIT)

    for hi in range(newest, oldest - 1, -100):
        ids = list(range(max(oldest, hi - 99), hi + 1))
        try:
            bot.delete_messages(chat_id, ids)
        except Exception:
            for mid in ids:
                try:
                    bot.delete_messages(chat_id, mid)
                except Exception:
                    pass

    bot.send_message(chat_id, "🧹 hat cleared", reply_markup=menu())

if __name__ == "__main__":
    bot.set_my_commands([types.BotCommand(n, d) for n, d in COMMANDS])
    try:
        bot.infinity_polling(skip_pending=True)
    finally:
        rates.close()