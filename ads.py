import os
import json
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv
import telebot
from telebot import types

# ================== CONFIG ==================
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
DATA_FILE = "data.json"

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")
scheduler = BackgroundScheduler()
scheduler.start()

logging.basicConfig(level=logging.INFO)

# ================== DATA ==================
def load_data():
    if not os.path.exists(DATA_FILE):
        return {
            "groups": [],
            "message": "📢 Reklama xabari",
            "interval": 10,
            "active": False
        }
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

data = load_data()

# ================== SCHEDULER ==================
def send_ads():
    if not data["active"]:
        return
    for gid in data["groups"]:
        try:
            bot.send_message(gid, data["message"])
        except Exception as e:
            logging.warning(f"Guruh {gid} ga yuborilmadi: {e}")

def restart_scheduler():
    scheduler.remove_all_jobs()
    scheduler.add_job(send_ads, "interval", minutes=data["interval"])
    logging.info(f"Reklama {data['interval']} daqiqada yuboriladi")

restart_scheduler()

# ================== GROUP AUTO ADD ==================
@bot.message_handler(content_types=["new_chat_members"])
def bot_added(message):
    gid = message.chat.id
    if gid not in data["groups"]:
        data["groups"].append(gid)
        save_data()
        bot.send_message(gid, "✅ Reklama bot ulandi")
        bot.send_message(ADMIN_ID, f"➕ Yangi guruh: {message.chat.title}")

# ================== ADMIN PANEL ==================
def admin_only(message):
    return message.from_user.id == ADMIN_ID

def main_menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("📄 Guruhlar", "✏️ Reklama matni")
    kb.add("⏱ Interval", "🚀 Boshlash", "🛑 To‘xtatish")
    return kb

@bot.message_handler(commands=["start"])
def start(message):
    if not admin_only(message):
        return
    bot.send_message(
        message.chat.id,
        "👋 <b>Admin panel</b>\nTanlang:",
        reply_markup=main_menu()
    )

# ================== GROUP LIST ==================
@bot.message_handler(func=lambda m: m.text == "📄 Guruhlar")
def show_groups(message):
    if not admin_only(message):
        return

    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("➕ Guruh qo‘shish", "❌ Guruhni uzish", "⬅️ Orqaga")

    if not data["groups"]:
        bot.send_message(
            message.chat.id,
            "📋 <b>Hech qaysi guruh ulanmagan</b>\n\n"
            "➕ Tugma orqali guruh qo‘shishingiz mumkin.",
            reply_markup=kb
        )
        return

    text = "📋 <b>Ulangan guruhlar:</b>\n\n"
    for i, g in enumerate(data["groups"], 1):
        text += f"{i}. <code>{g}</code>\n"

    bot.send_message(message.chat.id, text, reply_markup=kb)

# ================== ADD GROUP ==================
@bot.message_handler(func=lambda m: m.text == "➕ Guruh qo‘shish")
def ask_add_group(message):
    bot.send_message(message.chat.id, "➕ Guruh ID yuboring:")
    bot.register_next_step_handler(message, add_group)

def add_group(message):
    try:
        gid = int(message.text)
        if gid not in data["groups"]:
            data["groups"].append(gid)
            save_data()
            bot.send_message(message.chat.id, "✅ Guruh qo‘shildi")
        else:
            bot.send_message(message.chat.id, "⚠️ Bu guruh allaqachon bor")
    except:
        bot.send_message(message.chat.id, "❌ Noto‘g‘ri ID")

# ================== REMOVE GROUP ==================
@bot.message_handler(func=lambda m: m.text == "❌ Guruhni uzish")
def ask_remove_group(message):
    bot.send_message(message.chat.id, "❌ O‘chiriladigan guruh ID yuboring:")
    bot.register_next_step_handler(message, remove_group)

def remove_group(message):
    try:
        gid = int(message.text)
        if gid in data["groups"]:
            data["groups"].remove(gid)
            save_data()
            bot.send_message(message.chat.id, "🗑 Guruh o‘chirildi")
        else:
            bot.send_message(message.chat.id, "⚠️ Bunday guruh yo‘q")
    except:
        bot.send_message(message.chat.id, "❌ Noto‘g‘ri ID")

# ================== SET MESSAGE ==================
@bot.message_handler(func=lambda m: m.text == "✏️ Reklama matni")
def ask_text(message):
    bot.send_message(message.chat.id, "✏️ Yangi reklama matnini yuboring:")
    bot.register_next_step_handler(message, set_text)

def set_text(message):
    data["message"] = message.text
    save_data()
    bot.send_message(message.chat.id, "✅ Reklama matni yangilandi")

# ================== SET INTERVAL ==================
@bot.message_handler(func=lambda m: m.text == "⏱ Interval")
def ask_interval(message):
    bot.send_message(message.chat.id, "⏱ Daqiqani yuboring (masalan 10):")
    bot.register_next_step_handler(message, set_interval)

def set_interval(message):
    try:
        data["interval"] = int(message.text)
        save_data()
        restart_scheduler()
        bot.send_message(message.chat.id, f"✅ Interval {data['interval']} daqiqa")
    except:
        bot.send_message(message.chat.id, "❌ Faqat raqam")

# ================== START / STOP ==================
@bot.message_handler(func=lambda m: m.text == "🚀 Boshlash")
def start_ads(message):
    data["active"] = True
    save_data()
    bot.send_message(message.chat.id, "🚀 Reklama boshlandi")

@bot.message_handler(func=lambda m: m.text == "🛑 To‘xtatish")
def stop_ads(message):
    data["active"] = False
    save_data()
    bot.send_message(message.chat.id, "🛑 Reklama to‘xtadi")

@bot.message_handler(func=lambda m: m.text == "⬅️ Orqaga")
def back(message):
    start(message)

# ================== RUN ==================
logging.info("BOT ISHLAYAPTI 🚀")
bot.infinity_polling(skip_pending=True)
