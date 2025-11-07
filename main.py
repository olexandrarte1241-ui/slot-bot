import logging
import random
import os
import sqlite3
from datetime import date
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

logging.basicConfig(level=logging.INFO)
TOKEN = os.environ.get('TOKEN')  # Токен з Railway vars

DB_PATH = 'users.db'
conn = sqlite3.connect(DB_PATH, check_same_thread=False)
cursor = conn.cursor()
cursor.execute('CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, points INTEGER DEFAULT 0, last_daily TEXT)')
conn.commit()

SYMBOLS = ['🍒', '🍋', '🍊', '🔔', '⭐', '💎', '7️⃣']

def get_user(user_id):
    cursor.execute('SELECT points, last_daily FROM users WHERE user_id = ?', (user_id,))
    row = cursor.fetchone()
    if not row:
        cursor.execute('INSERT INTO users (user_id, points) VALUES (?, 0)', (user_id,))
        conn.commit()
        return 0, None
    return row[0], row[1]

def update_user(user_id, points, last_daily=None):
    if last_daily:
        cursor.execute('UPDATE users SET points = ?, last_daily = ? WHERE user_id = ?', (points, last_daily, user_id))
    else:
        cursor.execute('UPDATE users SET points = ? WHERE user_id = ?', (points, user_id))
    conn.commit()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    points, _ = get_user(user_id)
    await update.message.reply_text(f"🎰 Гра слоти! Баланс: {points} очок.\n/daily — +100 очок на день.\n/spin — спін за 10 очок (виграш 100 за комбо).")

async def daily(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    points, last = get_user(user_id)
    today = str(date.today())
    if last == today:
        await update.message.reply_text("Вже взяв сьогодні!")
        return
    points += 100
    update_user(user_id, points, today)
    await update.message.reply_text(f"+100! Баланс: {points}")

async def spin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    points, _ = get_user(user_id)
    if points < 10:
        await update.message.reply_text(f"Мало! {points}/10 очок.")
        return
    points -= 10
    update_user(user_id, points)
    res = [random.choice(SYMBOLS) for _ in range(3)]
    msg = f"🎰 | {' | '.join(res)} |\nБаланс: {points}"
    if len(set(res)) == 1:
        points += 100
        update_user(user_id, points)
        msg = f"🔥 Комбо! +100 очок!\n{msg.replace(str(points-100), str(points))}"
    await update.message.reply_text(msg)

if __name__ == '__main__':
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("daily", daily))
    app.add_handler(CommandHandler("spin", spin))
    print("Бот запущено! 💰")
    app.run_polling()
