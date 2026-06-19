import time
import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

from config import *

db = sqlite3.connect("data.db", check_same_thread=False)
cur = db.cursor()


# ---------- ساخت کاربر ----------
def create_user(user_id, invited_by=None):
    cur.execute("SELECT user_id FROM users WHERE user_id=?", (user_id,))
    if not cur.fetchone():
        cur.execute(
            "INSERT INTO users(user_id, diamonds, referrals, invited_by, last_daily, join_date) VALUES (?,0,0,?,0,?)",
            (user_id, invited_by, int(time.time()))
        )
        db.commit()

        if invited_by:
            cur.execute("UPDATE users SET referrals = referrals + 1 WHERE user_id=?", (invited_by,))
            db.commit()


# ---------- منو ----------
def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💎 موجودی", callback_data="balance")],
        [InlineKeyboardButton("🎁 جایزه روزانه", callback_data="daily")],
        [InlineKeyboardButton("👥 دعوت", callback_data="invite")],
        [InlineKeyboardButton("🆔 آیدی من", callback_data="myid")]
    ])


# ---------- /start ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    invited_by = None
    if context.args:
        try:
            invited_by = int(context.args[0])
        except:
            invited_by = None

    create_user(user.id, invited_by)

    await update.message.reply_text(
        "به ربات خوش آمدید 👇",
        reply_markup=main_menu()
    )


# ---------- callback ----------
async def handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    user_id = q.from_user.id

    cur.execute("SELECT diamonds, last_daily, referrals FROM users WHERE user_id=?", (user_id,))
    data = cur.fetchone()

    if not data:
        create_user(user_id)
        data = (0, 0, 0)

    diamonds, last_daily, refs = data

    # موجودی
    if q.data == "balance":
        await q.message.edit_text(f"💎 موجودی شما: {diamonds}")

    # آیدی
    elif q.data == "myid":
        await q.message.edit_text(f"🆔 آیدی شما: {user_id}")

    # جایزه روزانه
    elif q.data == "daily":
        now = int(time.time())

        if now - last_daily < 86400:
            await q.message.edit_text("⛔ هنوز جایزه امروز را گرفته‌ای")
            return

        cur.execute("UPDATE users SET diamonds = diamonds + ?, last_daily=? WHERE user_id=?",
                    (DAILY_REWARD, now, user_id))
        db.commit()

        await q.message.edit_text(f"🎁 دریافت شد +{DAILY_REWARD} 💎")

    # دعوت
    elif q.data == "invite":
        link = f"https://t.me/{context.bot.username}?start={user_id}"
        await q.message.edit_text(
            f"👥 لینک دعوت شما:\n{link}\n\n👥 زیرمجموعه: {refs}"
        )


# ---------- اجرا ----------
app = Application.builder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(handler))

app.run_polling()