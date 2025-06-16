import requests, json
from datetime import datetime, date
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

TELEGRAM_TOKEN = "7692583121:AAH5anZKknZE_tPTqbpjh6hkt1H5likjDwQ"
OPENROUTER_API_KEY = "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"
BOT_VERSION = "v1.4.0"
ADMIN_ID = 523456789  # ← THAY bằng Telegram ID của bạn

conversation_memory = {}
usage_count = {}
model_selection = {}
total_usage_global = 0

def save_memory(chat_id):
    filename = f"memory_{chat_id}.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(conversation_memory.get(chat_id, []), f, ensure_ascii=False, indent=2)

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"🤖 Bot đang chạy phiên bản: {BOT_VERSION}\nGõ /help để xem các lệnh.")

async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"📚 Hướng dẫn sử dụng bot (v{BOT_VERSION}):\n\n"
        "/start - Bắt đầu lại bot\n/help - Hiển thị hướng dẫn\n"
        "/reset - Xoá bộ nhớ\n/model <gpt|mistral|llama>\n/time - Giờ hiện tại\n"
        "/stats - (Admin) Thống kê tổng lượt dùng"
    )

async def cmd_reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    save_memory(chat_id)
    conversation_memory.pop(chat_id, None)
    usage_count.pop(chat_id, None)
    await update.message.reply_text("✅ Bộ nhớ đã được xoá.")

async def cmd_model(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    args = context.args
    if not args:
        await update.message.reply_text("❗ Dùng như: /model gpt")
        return
    model_map = {
        "gpt": "openai/gpt-3.5-turbo",
        "mistral": "mistralai/mistral-7b-instruct",
        "llama": "meta-llama/llama-2-13b-chat"
    }
    model = model_map.get(args[0])
    if not model:
        await update.message.reply_text("❗ Model không hợp lệ. Dùng: gpt, mistral, llama")
        return
    model_selection[chat_id] = model
    await update.message.reply_text(f"✅ Đã chọn model: {args[0]}")

async def cmd_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    now = datetime.now().strftime("%H:%M:%S - %d/%m/%Y")
    await update.message.reply_text(f"🕒 Bây giờ là: {now}")

async def cmd_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != ADMIN_ID:
        await update.message.reply_text("⛔ Chỉ admin được dùng lệnh này.")
        return
    await update.message.reply_text(f"📊 Tổng số lượt hỏi toàn bot: {total_usage_global}")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global total_usage_global
    chat_id = update.effective_chat.id
    msg = update.message.text
    today = date.today().isoformat()

    user_usage = usage_count.setdefault(chat_id, {})
    if user_usage.get(today, 0) >= 10:
        await update.message.reply_text("⚠️ Bạn đã dùng hết 10 lượt hôm nay.")
        return

    conversation_memory.setdefault(chat_id, []).append({"role": "user", "content": msg})
    user_usage[today] = user_usage.get(today, 0) + 1
    total_usage_global += 1

    model = model_selection.get(chat_id, "openai/gpt-3.5-turbo")
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model,
        "messages": conversation_memory[chat_id],
        "temperature": 0.7
    }

    try:
        r = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload)
        data = r.json()
        reply = data["choices"][0]["message"]["content"]
        conversation_memory[chat_id].append({"role": "assistant", "content": reply})
    except Exception as e:
        reply = f"❌ Lỗi: {e}"
    await update.message.reply_text(reply)

if __name__ == "__main__":
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("reset", cmd_reset))
    app.add_handler(CommandHandler("model", cmd_model))
    app.add_handler(CommandHandler("time", cmd_time))
    app.add_handler(CommandHandler("stats", cmd_stats))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print(f"🤖 Bot đang chạy phiên bản {BOT_VERSION}...")
    app.run_polling()
