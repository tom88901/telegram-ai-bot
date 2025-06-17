import logging
import json
import os
import requests
from datetime import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
import matplotlib.pyplot as plt

# --- LẤY TỪ BIẾN MÔI TRƯỜNG ---
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENROUTER_API_KEYS = os.getenv("OPENROUTER_API_KEYS", "").split(",")
DEEPINFRA_API_KEYS = os.getenv("DEEPINFRA_API_KEYS", "").split(",")
ADMIN_IDS = list(map(int, os.getenv("ADMIN_IDS", "").split(",")))
BOT_NAME = "mygpt_albot"

# --- CẤU HÌNH ---
VERSION = "v2.4"
USAGE_LIMIT = 10
USAGE_TRACK_FILE = "usage.json"
KEY_FILE = "apikeys.json"
ERROR_LOG_FILE = "error.log"
MEMORY_FILE_TEMPLATE = "memory_{}.json"
conversation_memory = {}
usage_counter = {}
error_keys = {"openrouter": [], "deepinfra": []}
api_stats = {}

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

def load_keys():
    if os.path.exists(KEY_FILE):
        with open(KEY_FILE, "r") as f:
            data = json.load(f)
            OPENROUTER_API_KEYS.extend(k for k in data.get("openrouter", []) if k not in OPENROUTER_API_KEYS)
            DEEPINFRA_API_KEYS.extend(k for k in data.get("deepinfra", []) if k not in DEEPINFRA_API_KEYS)

def save_keys():
    with open(KEY_FILE, "w") as f:
        json.dump({"openrouter": OPENROUTER_API_KEYS, "deepinfra": DEEPINFRA_API_KEYS}, f)

def log_error(msg):
    with open(ERROR_LOG_FILE, "a") as f:
        f.write(f"[{datetime.now()}] {msg}\n")

def is_admin(user_id):
    return user_id in ADMIN_IDS

# --- COMMANDS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"🤖 Xin chào! Mình là bot AI `{BOT_NAME}` phiên bản {VERSION}.\nGửi mình câu hỏi bất kỳ nhé!")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "/start - Khởi động lại bot\n/help - Xem hướng dẫn\n/reset - Xoá bộ nhớ\n/see - Xem tình trạng key\n/addkey - Thêm API Key mới (admin)\n/delete - Xoá key lỗi (admin)\n/error - Danh sách key đã lỗi (admin)\n/stats - Biểu đồ thống kê API (admin)\n/dashboard - Giao diện quản trị (admin)"
    )

async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    save_memory(chat_id)
    conversation_memory[chat_id] = []
    usage_counter[chat_id] = 0
    save_usage()
    await update.message.reply_text("✅ Bộ nhớ hội thoại đã được xoá.")

async def addkey(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        return await update.message.reply_text("🚫 Bạn không có quyền sử dụng lệnh này.")
    if len(context.args) < 2:
        return await update.message.reply_text("❗ Cú pháp đúng: /addkey [nguồn] [api_key]")
    source, key = context.args[0], context.args[1]
    if source not in ["openrouter", "deepinfra"]:
        return await update.message.reply_text("❗ Nguồn không hợp lệ. Dùng: openrouter hoặc deepinfra")
    if key in (OPENROUTER_API_KEYS + DEEPINFRA_API_KEYS):
        return await update.message.reply_text("⚠️ Key đã tồn tại.")
    if source == "openrouter":
        OPENROUTER_API_KEYS.append(key)
    else:
        DEEPINFRA_API_KEYS.append(key)
    save_keys()
    await update.message.reply_text("✅ Đã thêm API key thành công.")

async def error_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        return await update.message.reply_text("🚫 Bạn không có quyền sử dụng lệnh này.")
    msg = "🚨 Danh sách key lỗi:\n"
    for src, keys in error_keys.items():
        msg += f"\n🔹 {src}: {len(keys)} key\n" + "\n".join(keys) + "\n"
    await update.message.reply_text(msg)

async def delete_key(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        return await update.message.reply_text("🚫 Bạn không có quyền sử dụng lệnh này.")
    if len(context.args) < 2:
        return await update.message.reply_text("❗ Cú pháp đúng: /delete [nguồn] [api_key]")
    source, key = context.args[0], context.args[1]
    if source == "openrouter" and key in error_keys["openrouter"]:
        error_keys["openrouter"].remove(key)
        if key in OPENROUTER_API_KEYS:
            OPENROUTER_API_KEYS.remove(key)
    elif source == "deepinfra" and key in error_keys["deepinfra"]:
        error_keys["deepinfra"].remove(key)
        if key in DEEPINFRA_API_KEYS:
            DEEPINFRA_API_KEYS.remove(key)
    else:
        return await update.message.reply_text("⚠️ Không tìm thấy key cần xóa.")
    save_keys()
    await update.message.reply_text("✅ Đã xóa key khỏi danh sách.")

async def see(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = "📊 Tình trạng key:\n"
    msg += f"🔹 OpenRouter: {len(OPENROUTER_API_KEYS)} key\n"
    msg += f"🔹 DeepInfra: {len(DEEPINFRA_API_KEYS)} key\n"
    await update.message.reply_text(msg)

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        return await update.message.reply_text("🚫 Bạn không có quyền sử dụng lệnh này.")
    labels = list(api_stats.keys())
    values = list(api_stats.values())
    if not labels:
        return await update.message.reply_text("❗ Chưa có dữ liệu thống kê.")
    plt.clf()
    plt.bar(labels, values)
    plt.title("Thống kê số lượt sử dụng API")
    plt.xlabel("Key")
    plt.ylabel("Lượt dùng")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.savefig("api_stats.png")
    with open("api_stats.png", "rb") as photo:
        await update.message.reply_photo(photo=photo)

async def dashboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        return await update.message.reply_text("🚫 Bạn không có quyền sử dụng lệnh này.")
    await update.message.reply_text("📊 Giao diện quản trị đang được phát triển... (v2.5)")

# --- KHỞI CHẠY ---
if __name__ == '__main__':
    load_usage()
    load_keys()
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("reset", reset))
    app.add_handler(CommandHandler("addkey", addkey))
    app.add_handler(CommandHandler("error", error_command))
    app.add_handler(CommandHandler("delete", delete_key))
    app.add_handler(CommandHandler("see", see))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("dashboard", dashboard))
    print(f"🤖 {VERSION} - Bot {BOT_NAME} đang chạy...")
    app.run_polling()
