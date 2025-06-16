import logging
import json
import os
import requests
from datetime import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# --- Biến môi trường ---
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
BOT_NAME = "mygpt_albot"
VERSION = "v1.4"
USAGE_LIMIT = 10

# --- Tệp lưu trữ ---
USAGE_TRACK_FILE = "usage.json"
MEMORY_FILE_TEMPLATE = "memory_{}.json"

# --- Bộ nhớ ---
conversation_memory = {}
usage_counter = {}

# --- Hàm hỗ trợ ---
def load_usage():
    global usage_counter
    if os.path.exists(USAGE_TRACK_FILE):
        with open(USAGE_TRACK_FILE, "r") as f:
            usage_counter = json.load(f)

def save_usage():
    with open(USAGE_TRACK_FILE, "w") as f:
        json.dump(usage_counter, f)

def save_memory(chat_id):
    mem_file = MEMORY_FILE_TEMPLATE.format(chat_id)
    with open(mem_file, "w") as f:
        json.dump(conversation_memory.get(chat_id, []), f)

# --- /start ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"🤖 Xin chào! Mình là bot AI `{BOT_NAME}` dùng OpenRouter API.\nGửi mình câu hỏi nhé!"
    )

# --- /help ---
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    count = usage_counter.get(chat_id, 0)
    await update.message.reply_text(
        f"📚 Bot phiên bản: {VERSION}\nBạn đã sử dụng: {count} lần\n\n"
        "/start - Khởi động lại bot\n"
        "/help - Xem hướng dẫn và số lần sử dụng\n"
        "/reset - Xoá bộ nhớ và lưu lịch sử hội thoại\n"
        "\n💬 Gửi câu hỏi bất kỳ để bot trả lời theo ngữ cảnh."
    )

# --- /reset ---
async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    save_memory(chat_id)
    conversation_memory[chat_id] = []
    usage_counter[chat_id] = 0
    save_usage()
    await update.message.reply_text("✅ Bộ nhớ hội thoại đã được xoá và lưu lại.")

# --- Xử lý tin nhắn ---
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    user_message = update.message.text

    usage_counter[chat_id] = usage_counter.get(chat_id, 0) + 1
    if usage_counter[chat_id] > USAGE_LIMIT:
        await update.message.reply_text("⚠️ Bạn đã dùng hết lượt trong ngày (10).")
        return
    save_usage()

    if chat_id not in conversation_memory:
        conversation_memory[chat_id] = []

    conversation_memory[chat_id].append({"role": "user", "content": user_message})

    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "openai/gpt-3.5-turbo",
        "messages": conversation_memory[chat_id],
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        data = response.json()
        if "choices" in data:
            reply = data["choices"][0]["message"]["content"]
            conversation_memory[chat_id].append({"role": "assistant", "content": reply})
        else:
            error_msg = data.get("error", data)
            reply = f"❌ Lỗi OpenRouter: {error_msg}"
    except Exception as e:
        reply = f"❌ Lỗi: {str(e)}"

    await update.message.reply_text(reply)

# --- Chạy bot ---
if __name__ == '__main__':
    load_usage()
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("reset", reset))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print(f"🤖 {VERSION} - Bot {BOT_NAME} đang chạy...")
    app.run_polling()
