import logging, os
import scraper as rates
import threading

from dotenv import load_dotenv
from telebot import TeleBot, types

load_dotenv()
logging.basicConfig(level=logging.INFO)
bot = TeleBot(os.getenv("TOKEN"))

COMMANDS = [
    ("start", "Starts a chat"),
    ("rates", "Shows current USD, EUR and RUR rates"),
    ("convert", "Converts rate from one to another"),
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
    with open("exchange-rate.jpg", "rb") as photo:
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

SYMBOLS = {"USD": "$", "EUR": "€", "RUR": "₽", "AMD": "֏"}
ALL_CUR = ["USD", "EUR", "RUR", "AMD"]

convert_state = {}

def cur_kb(prefix, exclude=None):
    kb = types.InlineKeyboardMarkup(row_width=4)
    kb.add(*[
        types.InlineKeyboardButton(f"{SYMBOLS[c]} {c}", callback_data=f"{prefix}:{c}")
        for c in ALL_CUR if c != exclude
    ])
    return kb


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
    convert_state.pop(message.chat.id, None)
    bot.send_message(message.chat.id, "Convert from which currency?",
                     reply_markup=cur_kb("from"))


@bot.callback_query_handler(func=lambda c: c.data.startswith("from:"))
def on_from(call):
    src = call.data.split(":")[1]
    convert_state[call.message.chat.id] = {"src": src}
    bot.answer_callback_query(call.id)
    bot.edit_message_text(f"{SYMBOLS[src]} ➜ ?\nConvert to which currency?",
                          call.message.chat.id, call.message.message_id,
                          reply_markup=cur_kb("to", exclude=src))


@bot.callback_query_handler(func=lambda c: c.data.startswith("to:"))
def on_to(call):
    chat_id = call.message.chat.id
    state = convert_state.get(chat_id)
    bot.answer_callback_query(call.id)
    if not state:
        bot.send_message(chat_id, "Session expired, send /convert again.")
        return
    state["dest"] = call.data.split(":")[1]
    bot.edit_message_text(
        f"{SYMBOLS[state['src']]} ➜ {SYMBOLS[state['dest']]}\nHow much do you want to convert?",
        chat_id, call.message.message_id)


def waiting_for_amount(message):
    state = convert_state.get(message.chat.id)
    return bool(state and "dest" in state and message.text and not message.text.startswith("/"))


@bot.message_handler(func=waiting_for_amount)
def on_amount(message):
    chat_id = message.chat.id
    state = convert_state[chat_id]
    try:
        amount = float(message.text.replace(",", ".").replace(" ", ""))
        if amount <= 0:
            raise ValueError
    except ValueError:
        bot.send_message(chat_id, "Please send a positive number, e.g. 100")
        return

    src, dest = state["src"], state["dest"]
    try:
        row = rates.get_rows()[0]
        result = from_amd(to_amd(amount, src, row), dest, row)
    except Exception:
        bot.send_message(chat_id, "⚠️ Couldn't load rates, try again in a minute.")
        return

    convert_state.pop(chat_id, None)
    bot.send_message(
        chat_id,
        f"{SYMBOLS[src]} {src} ➜ {SYMBOLS[dest]} {dest}\n\n"
        f"{amount:,.2f} {src} = {result:,.2f} {dest}\n"
        f"{fmt_rate(src, dest, amount, result)}",
    )

def fmt_rate(src, dest, amount, result):
    if not result:
        return ""
    r = result / amount
    if r < 1:
        return f"1 {dest} = {1 / r:,.2f} {src}"
    return f"1 {src} = {r:,.2f} {dest}"

if __name__ == "__main__":
    bot.set_my_commands([types.BotCommand(n, d) for n, d in COMMANDS])
    try:
        bot.infinity_polling(skip_pending=True)
    finally:
        rates.close()