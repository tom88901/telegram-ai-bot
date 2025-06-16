import logging
import json
import os
import requests
from datetime import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# === CẤU HÌNH ===
VERSION = "v2.3"
BOT_NAME = "mygpt_albot"
ADMIN_IDS = ["1202674202"]

# === BIẾN TOÀN CỤC ===
conversation_memory = {}
usage_counter = {}
api_keys = {
    "openrouter": [],
    "deepinfra": []
}
api_index = {
    "openrouter": 0,
    "deepinfra": 0
}

# === HỖ TRỢ ===
def is_admin(user_id: int) -> bool:
    return str(user_id) in ADMIN_IDS

def load_keys():
    if os.path.exists("apikeys.json"):
        with open("apikeys.json", "r") as f:
            data = json.load(f)
            api_keys["openrouter"] = data.get("openrouter", [])
            api_keys["deepinfra"] = data.get("deepinfra", [])
            api_index["openrouter"] = 0
            api_index["deepinfra"] = 0

def save_keys():
    with open("apikeys.json", "w") as f:
        json.dump(api_keys, f)

def get_valid_key(source: str):
    keys = api_keys[source]
    index = api_index[source]
    for _ in range(len(keys)):
        if index >= len(keys): index = 0
        key = keys[index]
        index += 1
        api_index[source] = index
        return key
    return None

def load_usage():
    global usage_counter
    if os.path.exists("usage.json"):
        with open("usage.json", "r") as f:
            usage_counter = json.load(f)

def save_usage():
    with open("usage.json", "w") as f:
        json.dump(usage_counter, f)

# === COMMAND ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"🤖 Xin chào! Mình là bot AI `{BOT_NAME}` v{VERSION}.
Gửi mình câu hỏi nhé!")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "/start - Khởi động lại bot
"
        "/help - Xem hướng dẫn
"
        "/reset - Xoá bộ nhớ và đếm lượt
"
        "/see - Xem trạng thái API
"
        "/error - Kiểm tra key lỗi (Admin)
"
        "/delete - Xoá key lỗi (Admin)
"
    )

async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    conversation_memory[chat_id] = []
    usage_counter[chat_id] = 0
    save_usage()
    await update.message.reply_text("✅ Đã reset bộ nhớ.")

async def see(update: Update, context: ContextTypes.DEFAULT_TYPE):
    info = "📊 Trạng thái API:
"
    for source, keys in api_keys.items():
        info += f"- {source.upper()}: {len(keys)} key
"
    await update.message.reply_text(info)

async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return await update.message.reply_text("⛔ Không có quyền.")
    await update.message.reply_text("📛 Kiểm tra key lỗi chưa được tích hợp hoàn toàn.")

async def delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return await update.message.reply_text("⛔ Không có quyền.")
    await update.message.reply_text("🗑️ Tính năng xoá key lỗi sẽ cập nhật sau.")

# === CHAT ===
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    message = update.message.text
    usage_counter[chat_id] = usage_counter.get(chat_id, 0) + 1
    save_usage()

    # Lấy key xoay tua
    source = "openrouter"
    key = get_valid_key(source)
    if not key:
        await update.message.reply_text("❌ Hết API key. Vui lòng đợi admin cập nhật.")
        return

    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "openai/gpt-3.5-turbo",
        "messages": [{"role": "user", "content": message}]
    }

    try:
        res = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload)
        data = res.json()
        if "choices" in data:
            reply = data["choices"][0]["message"]["content"]
        else:
            reply = f"❌ Lỗi API: {data}"
    except Exception as e:
        reply = f"❌ Lỗi xử lý: {e}"

    await update.message.reply_text(reply)

# === MAIN ===
if __name__ == '__main__':
    load_keys()
    load_usage()
    app = ApplicationBuilder().token(os.getenv("TELEGRAM_TOKEN")).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("reset", reset))
    app.add_handler(CommandHandler("see", see))
    app.add_handler(CommandHandler("error", error))
    app.add_handler(CommandHandler("delete", delete))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print(f"🤖 Bot {BOT_NAME} v{VERSION} đang chạy polling...")
    app.run_polling()
