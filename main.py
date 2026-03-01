from flask import Flask, request, jsonify, send_from_directory
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import threading

BOT_TOKEN = "8300179743:AAFE_xM3qJn02PhgkN9lJHcCGAmoHs1DQiY"
START_COINS = 100
MINI_GAME_PATH = "/mini-game"

balances = {}  # баланс пользователей

# ================== Telegram Bot ==================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if user_id not in balances:
        balances[user_id] = START_COINS

    keyboard = [[InlineKeyboardButton("🎮 Играть в мини-рулетку", url=f"{MINI_GAME_PATH}")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"Привет, {update.effective_user.first_name}! Ты получил {balances[user_id]} коинов.\n"
        f"Нажми кнопку ниже, чтобы играть!",
        reply_markup=reply_markup
    )

async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    bal = balances.get(user_id, START_COINS)
    await update.message.reply_text(f"У тебя {bal} коинов.")

async def add_coins(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Админская команда: /add <user_id> <amount>"""
    if update.effective_user.id != 7869085121:  # твой ID админа
        await update.message.reply_text("❌ Только админ!")
        return
    try:
        args = context.args
        user_id, amount = args[0], int(args[1])
        balances[user_id] = balances.get(user_id, START_COINS) + amount
        await update.message.reply_text(f"Баланс пользователя {user_id} увеличен на {amount} коинов!")
    except:
        await update.message.reply_text("Использование: /add <user_id> <amount>")

# ================== Flask Server для мини-игры ==================
app = Flask(__name__)

@app.route(MINI_GAME_PATH)
def mini_game():
    return send_from_directory('templates', 'index.html')

@app.route("/api/balance/<user_id>")
def get_balance(user_id):
    return jsonify({"balance": balances.get(user_id, START_COINS)})

@app.route("/api/play", methods=["POST"])
def play():
    data = request.json
    user_id = str(data["user_id"])
    bet = int(data["bet"])
    if balances.get(user_id, START_COINS) < bet:
        return jsonify({"status": "error", "message": "Недостаточно коинов!"})
    import random
    balances[user_id] -= bet
    win = random.random() < 0.5
    if win:
        balances[user_id] += bet * 2
    return jsonify({"status": "ok", "win": win, "balance": balances[user_id]})

# ================== Запуск бота и сервера одновременно ==================
def run_bot():
    bot_app = ApplicationBuilder().token(BOT_TOKEN).build()
    bot_app.add_handler(CommandHandler("start", start))
    bot_app.add_handler(CommandHandler("balance", balance))
    bot_app.add_handler(CommandHandler("add", add_coins))
    bot_app.run_polling()

def run_server():
    app.run(host="0.0.0.0", port=8080)

threading.Thread(target=run_bot).start()
threading.Thread(target=run_server).start()
