import logging
import json
import os
import requests
from datetime import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# --- LẤY TỪ BIẾN MÔI TRƯỜNG ---
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
admin_env = os.getenv("ADMIN_IDS")
ADMIN_IDS = list(map(int, admin_env.split(","))) if admin_env else []
BOT_NAME = "AL v2.5"

# --- CẤU HÌNH ---
VERSION = "v2.5"
USAGE_LIMIT = 10
USAGE_TRACK_FILE = "usage.json"
API_KEYS_FILE = "apikeys.json"
MEMORY_FILE_TEMPLATE = "memory_{}.json"
conversation_memory = {}
usage_counter = {}
api_keys = {"openrouter": [], "deepinfra": []}
error_keys = {"openrouter": [], "deepinfra": []}

# --- HÀM LƯU / TẢI ---
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

def load_api_keys():
    global api_keys
    if os.path.exists(API_KEYS_FILE):
        with open(API_KEYS_FILE, "r") as f:
            api_keys = json.load(f)

def save_api_keys():
    with open(API_KEYS_FILE, "w") as f:
        json.dump(api_keys, f)

# --- COMMANDS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_firstname = update.effective_user.first_name
    await update.message.reply_text(
        f"🤖 Xin chào, {user_firstname}! Mình là trợ lý AI `{BOT_NAME}`.\nMình có thể giúp gì cho bạn?"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "/start - Khởi động lại bot\n"
        "/help - Xem hướng dẫn\n"
        "/reset - Xoá bộ nhớ\n"
        "/error - Danh sách key đã lỗi (admin)\n"
        "/delete - Xoá key lỗi (admin)\n"
        "/see - Xem tình trạng key còn hoạt động\n"
        "/addkey - Thêm API Key mới (admin)\n"
        "/dashboard - Giao diện theo dõi key (admin)"
    )

async def addkey(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("🚫 Bạn không có quyền sử dụng lệnh này.")
        return
    try:
        text = update.message.text.split(" ", 1)[1]
        provider, key = text.split(":", 1)
        if provider in api_keys:
            api_keys[provider].append(key)
            save_api_keys()
            await update.message.reply_text(f"✅ Đã thêm key vào nguồn {provider}.")
        else:
            await update.message.reply_text("❌ Nguồn không hợp lệ. Hãy dùng openrouter hoặc deepinfra.")
    except:
        await update.message.reply_text("❗ Định dạng sai. Ví dụ: /addkey openrouter:key")

# --- KHỞI CHẠY ---
if __name__ == '__main__':
    load_usage()
    load_api_keys()
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("addkey", addkey))
    # (Thêm các handler khác tại đây...)
    print(f"🤖 {VERSION} - Bot {BOT_NAME} đang chạy...")
    app.run_polling()
