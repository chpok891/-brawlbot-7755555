import telebot
from telebot import types
import sqlite3

TOKEN = '7314156880:AAFkiUyDKce4QzNm12DKG4i9Id6acMg9MDU'
CHANNEL_USERNAME = '@housebrawlnews'
ADMIN_ID = 7803143441

bot = telebot.TeleBot(TOKEN)
conn = sqlite3.connect('brawlbot.db', check_same_thread=False)
cursor = conn.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    gems REAL DEFAULT 0,
    clicks INTEGER DEFAULT 0,
    invited INTEGER DEFAULT 0,
    referral_id INTEGER
)
''')
conn.commit()

def check_subscription(user_id):
    try:
        status = bot.get_chat_member(CHANNEL_USERNAME, user_id).status
        return status in ['member', 'administrator', 'creator']
    except:
        return False

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    args = message.text.split()
    ref_id = int(args[1]) if len(args) > 1 and args[1].isdigit() else None

    cursor.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    if cursor.fetchone() is None:
        cursor.execute("INSERT INTO users (user_id, referral_id) VALUES (?, ?)", (user_id, ref_id))
        if ref_id and ref_id != user_id:
            cursor.execute("UPDATE users SET invited = invited + 1 WHERE user_id=?", (ref_id,))
        conn.commit()

    if not check_subscription(user_id):
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔗 Подписаться", url=f"https://t.me/{CHANNEL_USERNAME[1:]}"))
        markup.add(types.InlineKeyboardButton("✅ Я подписался", callback_data="check_sub"))
        bot.send_message(user_id, "🔒 Подпишись на канал, чтобы пользоваться ботом:", reply_markup=markup)
    else:
        show_menu(user_id)

@bot.callback_query_handler(func=lambda call: call.data == "check_sub")
def check_sub(call):
    if check_subscription(call.from_user.id):
        show_menu(call.from_user.id)
    else:
        bot.answer_callback_query(call.id, "❌ Вы ещё не подписались!")

def show_menu(user_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("👤 Профиль", "💎 Получить 0.01 гем")
    markup.add("💰 Вывести")
    if user_id == ADMIN_ID:
        markup.add("🛠 Админ-панель")
    bot.send_message(user_id, "Меню:", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == "👤 Профиль")
def profile(message):
    user_id = message.from_user.id
    cursor.execute("SELECT gems, clicks, invited FROM users WHERE user_id=?", (user_id,))
    gems, clicks, invited = cursor.fetchone()
    ref_link = f"https://t.me/{bot.get_me().username}?start={user_id}"
    bot.send_message(user_id, f"👤 Профиль:
💎 Гемы: {gems:.2f}
🖱 Клики: {clicks}/50
👥 Приглашено: {invited}
🔗 Реф-ссылка: {ref_link}")

@bot.message_handler(func=lambda m: m.text == "💎 Получить 0.01 гем")
def get_gem(message):
    user_id = message.from_user.id
    cursor.execute("SELECT clicks, invited FROM users WHERE user_id=?", (user_id,))
    clicks, invited = cursor.fetchone()

    if clicks >= 50 and invited < 1:
        bot.send_message(user_id, "❌ Лимит 50 кликов. Пригласи друга по реф-ссылке, чтобы продолжить!")
        return

    cursor.execute("UPDATE users SET gems = gems + 0.01, clicks = clicks + 1 WHERE user_id=?", (user_id,))
    conn.commit()
    bot.send_message(user_id, "✅ Вы получили 0.01 гем!")

@bot.message_handler(func=lambda m: m.text == "💰 Вывести")
def withdraw(message):
    user_id = message.from_user.id
    cursor.execute("SELECT gems FROM users WHERE user_id=?", (user_id,))
    gems = cursor.fetchone()[0]

    if gems < 3:
        bot.send_message(user_id, "❌ Вывод доступен от 3 гемов.")
        return

    if not check_subscription(user_id):
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("📨 Подписаться и отправить заявку", url="https://t.me/YOUR_APPLICATION_CHANNEL"))
        bot.send_message(user_id, "Для вывода подпишись и отправь заявку:", reply_markup=markup)
        return

    bot.send_message(user_id, f"💬 Заявка на вывод {gems:.2f} гемов отправлена. Ожидайте ответа.")

@bot.message_handler(func=lambda m: m.text == "🛠 Админ-панель")
def admin_panel(message):
    if message.from_user.id != ADMIN_ID:
        return
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("➕ Добавить канал", url="https://t.me/YOUR_ADMIN_PANEL"))
    bot.send_message(message.chat.id, "🛠 Админ-панель", reply_markup=markup)

bot.infinity_polling()