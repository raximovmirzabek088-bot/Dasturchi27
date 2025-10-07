import telebot, sqlite3, datetime, schedule, time, threading, os
from flask import Flask

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
ADMIN_ID = int(os.getenv("ADMIN_ID"))
EXPIRATION_MINUTES = int(os.getenv("EXPIRATION_MINUTES"))

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

def get_db_connection():
    conn = sqlite3.connect('users.db', check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

@bot.chat_member_handler()
def handle_member_update(update):
    user = update.new_chat_member.user
    status = update.new_chat_member.status
    user_id = user.id

    with get_db_connection() as conn:
        cursor = conn.cursor()
        if status == 'member':
            join_date = datetime.datetime.now().isoformat()
            cursor.execute('INSERT OR IGNORE INTO users (user_id, join_date) VALUES (?, ?)', (user_id, join_date))
            bot.send_message(ADMIN_ID, f"✅ Foydalanuvchi qo‘shildi: {user.first_name} (ID: {user_id})")
        elif status == 'left':
            cursor.execute('DELETE FROM users WHERE user_id = ?', (user_id,))
            bot.send_message(ADMIN_ID, f"❌ Foydalanuvchi chiqib ketdi: {user.first_name} (ID: {user_id})")
        conn.commit()

def check_expired_users():
    now = datetime.datetime.now()
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT user_id, join_date FROM users')
        for user_id, join_date_str in cursor.fetchall():
            join_date = datetime.datetime.fromisoformat(join_date_str)
            elapsed_minutes = (now - join_date).total_seconds() / 60
            if elapsed_minutes >= EXPIRATION_MINUTES:
                try:
                    bot.kick_chat_member(CHANNEL_ID, user_id, revoke_messages=False)
                    cursor.execute('DELETE FROM users WHERE user_id = ?', (user_id,))
                    bot.send_message(ADMIN_ID, f"⏳ {int(elapsed_minutes)} minut o‘tdi — {user_id} chiqarildi.")
                except Exception as e:
                    bot.send_message(ADMIN_ID, f"⚠️ {user_id} ni chiqarishda xatolik: {e}")
        conn.commit()

def run_scheduler():
    schedule.every(1).minutes.do(check_expired_users)
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    with get_db_connection() as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                join_date TEXT NOT NULL
            )
        ''')
        conn.commit()

    threading.Thread(target=run_scheduler, daemon=True).start()
    threading.Thread(target=lambda: bot.infinity_polling(allowed_updates=['chat_member']), daemon=True).start()
    app.run(host="0.0.0.0", port=8080)
