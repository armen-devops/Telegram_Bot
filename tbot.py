import logging, math, os, time
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import scraper as rates
from dotenv import load_dotenv
from telebot import TeleBot, types

load_dotenv()
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

TOKEN = os.getenv("TOKEN")
if not TOKEN:
    raise SystemExit("TOKEN is missing in .env")
bot = TeleBot(TOKEN)

PHOTO = Path(__file__).parent / "exchange-rate.jpg"
TZ = ZoneInfo("Asia/Yerevan")
STATE_TTL = 300
ERROR_TEXT = "⚠️ Couldn't load rates, try again in a minute."

COMMANDS = [
    ("start", "Starts a chat"),
    ("rates", "Shows current USD, EUR and RUR rates"),
    ("convert", "Converts rate from one to another"),
    ("help", "Shows all commands"),
]

CURRENCIES = {
    "USD": ("🇺🇸", 0, 1),
    "EUR": ("🇪🇺", 2, 3),
    "RUR": ("🇷🇺", 4, 5),
}

SYMBOLS = {"USD": "$", "EUR": "€", "RUR": "₽", "AMD": "֏"}
ALL_CUR = ["USD", "EUR", "RUR", "AMD"]


def current_row():
    return rates.get_rows()[0]


def stamp():
    t = datetime.fromtimestamp(rates.updated_at(), TZ)
    return t.strftime("🕒 Updated %H:%M")


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


_photo_id = None


@bot.message_handler(commands=["start"])
def start(message):
    global _photo_id
    if _photo_id:
        bot.send_photo(message.chat.id, _photo_id)
    else:
        with open(PHOTO, "rb") as f:
            _photo_id = bot.send_photo(message.chat.id, f).photo[-1].file_id
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
        row = current_row()
        text = "\n\n".join(format_rows(cur, row) for cur in CURRENCIES)
    except Exception:
        log.exception("/rates failed")
        bot.send_message(message.chat.id, ERROR_TEXT)
        return
    bot.send_message(message.chat.id, f"{text}\n\n{stamp()}")


@bot.callback_query_handler(func=lambda c: c.data.startswith("cur:"))
def on_currency(call):
    cur = call.data.split(":")[1]
    bot.answer_callback_query(call.id)
    try:
        text = format_rows(cur, current_row())
    except Exception:
        log.exception("currency button failed")
        bot.send_message(call.message.chat.id, ERROR_TEXT)
        return
    bot.send_message(call.message.chat.id, f"{text}\n\n{stamp()}")


convert_state = {}


def get_state(chat_id):
    s = convert_state.get(chat_id)
    if s and time.time() - s["ts"] > STATE_TTL:
        convert_state.pop(chat_id, None)
        return None
    return s


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


def parse_amount(text):
    t = text.strip().replace(" ", "")
    if "," in t and "." in t:
        t = t.replace(",", "")
    elif t.count(",") == 1 and len(t.split(",")[1]) <= 2:
        t = t.replace(",", ".")
    else:
        t = t.replace(",", "")
    v = float(t)
    if not math.isfinite(v) or not 0 < v < 1e12:
        raise ValueError("amount out of range")
    return v


def fmt_rate(src, dest, amount, result):
    if not result:
        return ""
    r = result / amount
    if r < 1:
        return f"1 {dest} = {1 / r:,.2f} {src}"
    return f"1 {src} = {r:,.2f} {dest}"


@bot.message_handler(commands=["convert"])
def convert_cmd(message):
    convert_state.pop(message.chat.id, None)
    bot.send_message(message.chat.id, "Convert from which currency?",
                     reply_markup=cur_kb("from"))


@bot.callback_query_handler(func=lambda c: c.data.startswith("from:"))
def on_from(call):
    src = call.data.split(":")[1]
    convert_state[call.message.chat.id] = {"src": src, "ts": time.time()}
    bot.answer_callback_query(call.id)
    bot.edit_message_text(f"{SYMBOLS[src]} ➜ ?\nConvert to which currency?",
                          call.message.chat.id, call.message.message_id,
                          reply_markup=cur_kb("to", exclude=src))


@bot.callback_query_handler(func=lambda c: c.data.startswith("to:"))
def on_to(call):
    chat_id = call.message.chat.id
    state = get_state(chat_id)
    bot.answer_callback_query(call.id)
    if not state:
        bot.send_message(chat_id, "Session expired, send /convert again.")
        return
    state["dest"] = call.data.split(":")[1]
    state["ts"] = time.time()
    bot.edit_message_text(
        f"{SYMBOLS[state['src']]} ➜ {SYMBOLS[state['dest']]}\nHow much do you want to convert?",
        chat_id, call.message.message_id)


def waiting_for_amount(message):
    state = get_state(message.chat.id)
    return bool(state and "dest" in state and message.text and not message.text.startswith("/"))


@bot.message_handler(func=waiting_for_amount)
def on_amount(message):
    chat_id = message.chat.id
    state = get_state(chat_id)
    if not state:
        bot.send_message(chat_id, "Session expired, send /convert again.")
        return

    try:
        amount = parse_amount(message.text)
    except ValueError:
        bot.send_message(chat_id, "Please send a positive number, e.g. 100")
        return

    src, dest = state["src"], state["dest"]
    try:
        row = current_row()
        result = from_amd(to_amd(amount, src, row), dest, row)
    except Exception:
        log.exception("convert failed")
        bot.send_message(chat_id, ERROR_TEXT)
        return

    convert_state.pop(chat_id, None)
    bot.send_message(
        chat_id,
        f"{SYMBOLS[src]} {src} ➜ {SYMBOLS[dest]} {dest}\n\n"
        f"{amount:,.2f} {src} = {result:,.2f} {dest}\n"
        f"{fmt_rate(src, dest, amount, result)}\n\n"
        f"{stamp()}",
    )


if __name__ == "__main__":
    bot.set_my_commands([types.BotCommand(n, d) for n, d in COMMANDS])
    try:
        bot.infinity_polling(skip_pending=True)
    finally:
        rates.close()