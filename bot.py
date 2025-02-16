import os
import sys
import yt_dlp
import logging
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.enums import ChatMemberStatus

# Token va ID-lar
TOKEN = "8016243098:AAHvTSYUbcfPo1KlH1M_s57McDOOdfqKUz0"
CHANNEL_ID = -1002447570317  # Kanal ID
ADMIN_ID = 7156395320  # Admin ID

# Bot va Dispatcher obyektlarini yaratamiz
bot = Bot(token=TOKEN)
dp = Dispatcher()

# Loglarni sozlash
logging.basicConfig(level=logging.INFO)

# Global o'zgaruvchilar
users = set()
groups = set()
message_count = 0
banned_users = set()

async def check_subscription(user_id):
    """Foydalanuvchini kanalga a'zo ekanligini tekshiradi."""
    try:
        chat_member = await bot.get_chat_member(CHANNEL_ID, user_id)
        return chat_member.status in [ChatMemberStatus.MEMBER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.CREATOR]
    except:
        return False

@dp.message(Command("start"))
async def start_command(message: types.Message):
    """Foydalanuvchi /start buyrug‘ini yuborganda ishlaydi."""
    global users, groups
    user_id = message.from_user.id
    chat_id = message.chat.id

    if user_id in banned_users:
        await message.answer("⛔ Siz botdan foydalanish taqiqlangansiz!")
        return

    if chat_id > 0:  
        users.add(user_id)
    else:  
        groups.add(chat_id)

    if await check_subscription(user_id):
        await message.answer("✅ Xush kelibsiz! Video yoki musiqa yuklab olish uchun menga link yuboring.")
    else:
        markup = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📢 Kanalga obuna bo‘lish", url="https://t.me/PipStormX")],
            [InlineKeyboardButton(text="✅ Tekshirish", callback_data="check_subscription")]
        ])
        await message.answer("⛔ Botdan foydalanish uchun kanalga obuna bo‘lishingiz kerak!", reply_markup=markup)

@dp.callback_query(F.data == "check_subscription")
async def check_subscription_callback(callback_query: types.CallbackQuery):
    """Obunani tekshirish tugmasi bosilganda ishlaydi."""
    user_id = callback_query.from_user.id

    if await check_subscription(user_id):
        await bot.send_message(user_id, "✅ Rahmat! Endi botdan foydalanishingiz mumkin.")
    else:
        await bot.send_message(user_id, "⛔ Hali ham obuna bo‘lmagansiz. Iltimos, avval kanalga obuna bo‘ling.")

@dp.message(Command("admin"))
async def admin_command(message: types.Message):
    """Admin paneliga kirish."""
    if message.from_user.id == ADMIN_ID:
        markup = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📊 Statistika", callback_data="stats")],
            [InlineKeyboardButton(text="👤 Ban qilish", callback_data="ban_user")],
            [InlineKeyboardButton(text="🔓 Unban qilish", callback_data="unban_user")],
            [InlineKeyboardButton(text="📢 Xabar yuborish", callback_data="broadcast")],
            [InlineKeyboardButton(text="🔄 Qayta ishga tushirish", callback_data="restart")],
            [InlineKeyboardButton(text="🛑 To‘xtatish", callback_data="shutdown")]
        ])
        await message.answer("🔹 Admin paneliga xush kelibsiz!", reply_markup=markup)
    else:
        await message.answer("⛔ Siz admin emassiz!")

@dp.callback_query(F.data == "stats")
async def bot_stats(callback: types.CallbackQuery):
    """Statistika ko'rsatish."""
    if callback.from_user.id != ADMIN_ID:
        return

    stats_message = (
        f"📊 *Bot Statistikasi:*\n\n"
        f"👤 Foydalanuvchilar: {len(users)}\n"
        f"👥 Guruhlar: {len(groups)}\n"
        f"💬 Xabarlar soni: {message_count}\n"
        f"🚫 Banlangan foydalanuvchilar: {len(banned_users)}\n"
    )
    await callback.message.edit_text(stats_message, parse_mode="Markdown")

@dp.message(Command("broadcast"))
async def broadcast_command(message: types.Message):
    """Admin bot orqali umumiy xabar yuboradi."""
    if message.from_user.id != ADMIN_ID:
        return
    
    text = message.text.replace("/broadcast", "").strip()
    if not text:
        await message.answer("❌ Xabar matnini kiriting: \n`/broadcast Salom hammaga!`", parse_mode="Markdown")
        return
    
    success_count = 0
    for user_id in users:
        try:
            await bot.send_message(user_id, text)
            success_count += 1
        except:
            pass  # Foydalanuvchi botni bloklagan bo‘lishi mumkin
    
    await message.answer(f"📢 Xabar {success_count} ta foydalanuvchiga yuborildi!")

@dp.message()
async def download_video(message: types.Message):
    """Foydalanuvchi video yuklab olish uchun link yuborganda ishlaydi."""
    global message_count
    message_count += 1

    url = message.text.strip()

    # Faqat URL-larni qabul qilish
    if not (url.startswith("http://") or url.startswith("https://")):
        return  

    await message.answer("⏳ Yuklab olinmoqda, biroz kuting...")
    
    output_file = "downloads/video.mp4"
    ydl_opts = {'outtmpl': output_file, 'format': 'mp4/best'}
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        
        video_file = types.FSInputFile(output_file)
        await bot.send_video(chat_id=message.chat.id, video=video_file)
        os.remove(output_file)
    except Exception as e:
        await message.answer(f"❌ Xatolik yuz berdi: {e}")

async def main():
    """Botni ishga tushirish."""
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
