import logging, json, os, requests
from datetime import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# --- CẤU HÌNH BIẾN MÔI TRƯỜNG ---
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENROUTER_API_KEYS = os.getenv("OPENROUTER_API_KEYS", "").split(",")
DEEPINFRA_API_KEYS = os.getenv("DEEPINFRA_API_KEYS", "").split(",")
ADMIN_IDS = list(map(int, os.getenv("ADMIN_IDS", "1202674202").split(",")))
BOT_NAME = "mygpt_albot"
VERSION = "v2.3"
USAGE_LIMIT = 10
USAGE_TRACK_FILE = "usage.json"
MEMORY_FILE_TEMPLATE = "memory_{}.json"
conversation_memory = {}
usage_counter = {}
error_keys = {"openrouter": [], "deepinfra": []}

# --- HÀM LƯU/TẢI ---
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

# --- CHỌN API KEY ---
def get_valid_key(source):
    keys = OPENROUTER_API_KEYS if source == "openrouter" else DEEPINFRA_API_KEYS
    for key in keys:
        if key not in error_keys[source]:
            return key
    return None

# --- GỬI YÊU CẦU ĐẾN API ---
def send_to_ai(source, messages):
    key = get_valid_key(source)
    if not key:
        raise Exception(f"Hết key khả dụng cho nguồn: {source.upper()}")

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {key}"
    }

    if source == "openrouter":
        headers["HTTP-Referer"] = "https://worker-production-c60d.up.railway.app"
        url = "https://openrouter.ai/api/v1/chat/completions"
        model = "openai/gpt-3.5-turbo"
    else:
        url = "https://api.deepinfra.com/v1/openai/chat/completions"
        model = "meta-llama/Meta-Llama-3-8B-Instruct"

    payload = {"model": model, "messages": messages}
    res = requests.post(url, headers=headers, json=payload)
    if res.status_code != 200:
        error_keys[source].append(key)
        raise Exception(f"Lỗi {source.upper()} - {res.status_code}: {res.text}")
    return res.json()["choices"][0]["message"]["content"]

# --- COMMANDS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    await update.message.reply_text(f"🤖 Xin chào! Mình là `{BOT_NAME}` phiên bản {VERSION}.\nID của bạn là: {user_id}\nGửi câu hỏi để mình trả lời nhé!")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    count = usage_counter.get(chat_id, 0)
    await update.message.reply_text(
        f"📚 Phiên bản: {VERSION}\nĐã dùng: {count}/{USAGE_LIMIT} lần\n\n"
        "/start - Bắt đầu lại bot\n/help - Xem hướng dẫn\n/reset - Xoá bộ nhớ\n"
        "/see - Xem trạng thái API\n"
        "/error - Xem key lỗi (Admin)\n/delete - Xoá key lỗi (Admin)\n"
        "/addkey [nguồn] [key] - Thêm key (Admin)"
    )

async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    save_memory(chat_id)
    conversation_memory[chat_id] = []
    usage_counter[chat_id] = 0
    save_usage()
    await update.message.reply_text("✅ Đã reset bộ nhớ và lượt sử dụng.")

async def see(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = ""
    for src, keys in [("openrouter", OPENROUTER_API_KEYS), ("deepinfra", DEEPINFRA_API_KEYS)]:
        active = len([k for k in keys if k not in error_keys[src]])
        text += f"🔍 {src.upper()}: {active}/{len(keys)} key còn dùng được\n"
    await update.message.reply_text(text)

async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("❌ Bạn không có quyền dùng lệnh này.")
        return
    msg = "❗ Key lỗi:\n"
    for src in error_keys:
        msg += f"🔻 {src}: {len(error_keys[src])} key lỗi\n"
    await update.message.reply_text(msg)

async def delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("❌ Bạn không có quyền.")
        return
    for src in error_keys:
        error_keys[src] = []
    await update.message.reply_text("✅ Đã xoá tất cả key lỗi.")

async def addkey(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("❌ Không có quyền.")
        return
    try:
        source, new_key = context.args[0], context.args[1]
        if source == "openrouter":
            OPENROUTER_API_KEYS.append(new_key)
        elif source == "deepinfra":
            DEEPINFRA_API_KEYS.append(new_key)
        else:
            raise Exception("Nguồn không hợp lệ.")
        await update.message.reply_text(f"✅ Đã thêm key mới vào {source}.")
    except:
        await update.message.reply_text("⚠️ Dùng: /addkey [openrouter|deepinfra] [API_KEY]")

# --- XỬ LÝ TIN NHẮN ---
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    user_message = update.message.text
    usage_counter[chat_id] = usage_counter.get(chat_id, 0) + 1
    if usage_counter[chat_id] > USAGE_LIMIT:
        await update.message.reply_text("⚠️ Hết lượt sử dụng hôm nay (10).")
        return
    save_usage()
    if chat_id not in conversation_memory:
        conversation_memory[chat_id] = []
    conversation_memory[chat_id].append({"role": "user", "content": user_message})
    reply = ""
    try:
        reply = send_to_ai("openrouter", conversation_memory[chat_id])
    except Exception as e1:
        try:
            reply = send_to_ai("deepinfra", conversation_memory[chat_id])
        except Exception as e2:
            reply = f"❌ Lỗi cả hai nguồn:\nOpenRouter: {e1}\nDeepInfra: {e2}"
    if reply:
        conversation_memory[chat_id].append({"role": "assistant", "content": reply})
    await update.message.reply_text(reply)

# --- KHỞI CHẠY ---
if __name__ == '__main__':
    load_usage()
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("reset", reset))
    app.add_handler(CommandHandler("see", see))
    app.add_handler(CommandHandler("error", error))
    app.add_handler(CommandHandler("delete", delete))
    app.add_handler(CommandHandler("addkey", addkey))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print(f"🤖 Bot {BOT_NAME} v{VERSION} đang chạy...")
    app.run_polling()
