# bot_v2_openrouter_deepinfra.py

import os
import json
import requests
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ContextTypes, filters
)

# --- CONFIG ---
BOT_NAME = "multi-ai-bot"
VERSION = "v2.3"
USAGE_LIMIT = 20
USAGE_TRACK_FILE = "usage.json"
conversation_memory = {}
bad_keys = set()

# --- ADMIN LIST ---
ADMIN_IDS = os.getenv("ADMIN_IDS", "").split(",")  # e.g., "123456789,987654321"

def is_admin(user_id):
    return str(user_id) in ADMIN_IDS

# --- API Key Lists ---
OPENROUTER_KEYS = os.getenv("OPENROUTER_API_KEYS", "").split(",")
DEEPINFRA_KEYS = os.getenv("DEEPINFRA_API_KEYS", "").split(",")

# --- Load/save usage ---
usage_counter = {}
if os.path.exists(USAGE_TRACK_FILE):
    with open(USAGE_TRACK_FILE, "r") as f:
        usage_counter = json.load(f)

def save_usage():
    with open(USAGE_TRACK_FILE, "w") as f:
        json.dump(usage_counter, f)

# --- AI CALLERS ---
def call_openrouter(prompt: str):
    url = "https://openrouter.ai/api/v1/chat/completions"
    messages = [{"role": "user", "content": prompt}]
    payload = {"model": "openai/gpt-3.5-turbo", "messages": messages}

    for key in OPENROUTER_KEYS:
        key = key.strip()
        if key in bad_keys:
            continue
        headers = {
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://worker-production-c60d.up.railway.app"
        }
        try:
            res = requests.post(url, headers=headers, json=payload, timeout=30)
            if res.status_code == 401:
                bad_keys.add(key)
                continue
            elif res.status_code != 200:
                continue
            data = res.json()
            if "choices" in data:
                return data["choices"][0]["message"]["content"]
        except:
            continue
    return None

def call_deepinfra(prompt: str):
    model = "meta-llama/Meta-Llama-3-8B-Instruct"
    url = f"https://api.deepinfra.com/v1/inference/{model}"
    payload = {"inputs": prompt, "parameters": {"temperature": 0.7, "max_new_tokens": 200}}

    for key in DEEPINFRA_KEYS:
        key = key.strip()
        if key in bad_keys:
            continue
        headers = {
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json"
        }
        try:
            res = requests.post(url, headers=headers, json=payload, timeout=30)
            if res.status_code == 401:
                bad_keys.add(key)
                continue
            elif res.status_code != 200:
                continue
            data = res.json()
            if isinstance(data, dict) and "generated_text" in data:
                return data["generated_text"]
            elif isinstance(data, list) and len(data) > 0 and "generated_text" in data[0]:
                return data[0]["generated_text"]
        except:
            continue
    return None

# --- Telegram Commands ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"🤖 Xin chào! Mình là `{BOT_NAME}` phiên bản {VERSION}.")

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

async def error_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("🚫 Chỉ quản trị viên mới có thể dùng lệnh này.")
        return
    if not bad_keys:
        await update.message.reply_text("✅ Tất cả API Key hiện đang hoạt động bình thường.")
    else:
        msg = "❌ Các API Key lỗi hoặc hết hạn:\n"
        for key in bad_keys:
            short_key = key[:6] + "..." + key[-4:]
            msg += f"- {short_key}\n"
        await update.message.reply_text(msg)

async def delete_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("🚫 Chỉ quản trị viên mới có thể dùng lệnh này.")
        return
    count = len(bad_keys)
    bad_keys.clear()
    await update.message.reply_text(f"🗑️ Đã xoá {count} API key bị lỗi khỏi danh sách.")

async def see_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = "📊 Tình trạng key hiện tại:\n"
    active_open = [k for k in OPENROUTER_KEYS if k.strip() not in bad_keys]
    active_deep = [k for k in DEEPINFRA_KEYS if k.strip() not in bad_keys]
    msg += f"\n🔹 OpenRouter: {len(active_open)}/{len(OPENROUTER_KEYS)} key hoạt động"
    msg += f"\n🔹 DeepInfra: {len(active_deep)}/{len(DEEPINFRA_KEYS)} key hoạt động"
    await update.message.reply_text(msg)

async def addkey(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("🚫 Chỉ quản trị viên mới có thể thêm API Key.")
        return
    if not context.args or len(context.args) < 2:
        await update.message.reply_text("❗ Cú pháp đúng: /addkey [nguồn] [api_key]")
        return

    source = context.args[0].lower()
    key = context.args[1].strip()

    if source == "openrouter":
        if key not in OPENROUTER_KEYS:
            OPENROUTER_KEYS.append(key)
            await update.message.reply_text("✅ Đã thêm key vào OpenRouter.")
    elif source == "deepinfra":
        if key not in DEEPINFRA_KEYS:
            DEEPINFRA_KEYS.append(key)
            await update.message.reply_text("✅ Đã thêm key vào DeepInfra.")
    else:
        await update.message.reply_text("❗ Nguồn không hợp lệ. Dùng: openrouter hoặc deepinfra")

async def dashboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("🚫 Chỉ quản trị viên được xem dashboard.")
        return
    msg = "📈 Dashboard AI Key\n"
    msg += f"🔑 OpenRouter: {len([k for k in OPENROUTER_KEYS if k.strip() not in bad_keys])}/{len(OPENROUTER_KEYS)} hoạt động\n"
    msg += f"🔑 DeepInfra: {len([k for k in DEEPINFRA_KEYS if k.strip() not in bad_keys])}/{len(DEEPINFRA_KEYS)} hoạt động\n"
    msg += f"🚫 Key lỗi: {len(bad_keys)}\n"
    await update.message.reply_text(msg)

async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    conversation_memory[chat_id] = []
    usage_counter[chat_id] = 0
    save_usage()
    await update.message.reply_text("✅ Đã reset bộ nhớ và số lượt sử dụng.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    user_msg = update.message.text

    usage_counter[chat_id] = usage_counter.get(chat_id, 0) + 1
    if usage_counter[chat_id] > USAGE_LIMIT:
        await update.message.reply_text("⚠️ Bạn đã dùng hết lượt hôm nay.")
        return
    save_usage()

    reply = call_openrouter(user_msg)
    if not reply:
        reply = call_deepinfra(user_msg)
    if not reply:
        reply = "❌ Tất cả các AI API hiện không phản hồi. Vui lòng thử lại sau."
        for admin_id in ADMIN_IDS:
            try:
                await context.bot.send_message(chat_id=int(admin_id.strip()),
                    text="🚨 Bot không còn API key khả dụng! Hãy kiểm tra và cập nhật key mới ngay.")
            except:
                pass

    await update.message.reply_text(reply)

# --- Main ---
if __name__ == '__main__':
    TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("reset", reset))
    app.add_handler(CommandHandler("error", error_command))
    app.add_handler(CommandHandler("delete", delete_command))
    app.add_handler(CommandHandler("see", see_command))
    app.add_handler(CommandHandler("addkey", addkey))
    app.add_handler(CommandHandler("dashboard", dashboard))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print(f"🤖 {VERSION} - Bot {BOT_NAME} is running...")
    app.run_polling()
