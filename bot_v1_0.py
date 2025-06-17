import os
import json
import logging
import requests
import re
from datetime import datetime
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ContextTypes, filters
)

# --- CẤU HÌNH ---
BOT_NAME = "mygpt_albot"
VERSION = "v1.0"
USAGE_LIMIT = 10
USAGE_TRACK_FILE = "usage.json"
MEMORY_FILE_TEMPLATE = "memory_{}.json"
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

# --- CẤU HÌNH API KEY ---
api_keys = {
    "openrouter": [],
    "deepinfra": []
}
api_status = {
    "openrouter": {},
    "deepinfra": {}
}

# --- BỘ NHỚ & USAGE ---
conversation_memory = {}
usage_counter = {}

# --- LOGGING ---
logging.basicConfig(level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s')

# --- HÀM HỖ TRỢ ---
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

def get_working_key(source):
    for key in api_keys[source]:
        if api_status[source].get(key, False):
            return key
    return None

def mark_key_invalid(source, key):
    api_status[source][key] = False

# === 1. HÀM LẤY CHƯƠNG TRUYỆN FANQIENOVEL ===
def get_fanqie_chapter(chapter_url):
    headers = {
        "User-Agent": "Mozilla/5.0",
    }
    # Chấp nhận cả /chapter/ID và /reader/ID
    m = re.search(r'/(chapter|reader)/(\d+)', chapter_url)
    if not m:
        return None, "❌ Link chương không hợp lệ! Vui lòng gửi đúng link fanqienovel."
    chapter_id = m.group(2)
    api_url = f"https://api.api-fanqienovel.sunianyun.live/info?id={chapter_id}"
    try:
        r = requests.get(api_url, headers=headers, timeout=10)
        data = r.json()
        raw_text = data['data'].get('content', '')
        if not raw_text:
            return None, "❌ Không lấy được nội dung chương. Có thể chương này đã bị giới hạn."
        return raw_text, None
    except Exception as e:
        return None, f"❌ Lỗi khi lấy nội dung chương: {e}"

# === 2. HÀM DỊCH CHƯƠNG BẰNG AI BOT ===
def translate_with_bot_ai(raw_text):
    prompt = "Dịch đoạn văn sau từ tiếng Trung sang tiếng Việt. Giữ nguyên nghĩa, văn phong tự nhiên:\n\n" + raw_text
    for src in ["openrouter", "deepinfra"]:
        key = get_working_key(src)
        if not key:
            continue
        headers = {
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        }
        if src == "openrouter":
            headers["HTTP-Referer"] = "https://your-app-domain"
            url = "https://openrouter.ai/api/v1/chat/completions"
            model = "openai/gpt-3.5-turbo"
        elif src == "deepinfra":
            url = "https://api.deepinfra.com/v1/openai/chat/completions"
            model = "meta-llama/Meta-Llama-3-8B-Instruct"

        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": "Bạn là một dịch giả chuyên nghiệp."},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 2048,
            "temperature": 0.2
        }

        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=30)
            data = resp.json()
            if "choices" in data and data["choices"]:
                return data["choices"][0]["message"]["content"]
            else:
                mark_key_invalid(src, key)
        except Exception as e:
            mark_key_invalid(src, key)
    return "❌ Lỗi dịch. Tất cả key đã hết hoặc gặp sự cố."

# === 3. HANDLER NHẬN LINK CHƯƠNG & DỊCH TRẢ VỀ TELEGRAM ===
async def handle_fanqie_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message.text.strip()
    if "fanqienovel.com/chapter/" in msg:
        await update.message.reply_text("🔍 Đang lấy nội dung chương truyện...")
        raw_text, err = get_fanqie_chapter(msg)
        if err:
            await update.message.reply_text(err)
            return
        await update.message.reply_text("🤖 Đang dịch sang tiếng Việt, vui lòng chờ...")
        vi_text = translate_with_bot_ai(raw_text)
        max_len = 4000
        if len(vi_text) <= max_len:
            await update.message.reply_text("📖 Bản dịch:\n" + vi_text)
        else:
            for i in range(0, len(vi_text), max_len):
                await update.message.reply_text(vi_text[i:i+max_len])
        return
    else:
        return False

# --- LỆNH CƠ BẢN ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await update.message.reply_text(
        f"🤖 Xin chào {user.first_name or ''}! Mình là bot AI `{BOT_NAME}` phiên bản {VERSION}.\n"
        "Gửi mình câu hỏi để nhận phản hồi thông minh nhé!"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    count = usage_counter.get(chat_id, 0)
    await update.message.reply_text(
        f"📚 Bot phiên bản: {VERSION}\n"
        f"Bạn đã sử dụng: {count} lần\n\n"
        "/start - Khởi động lại bot\n"
        "/help - Xem hướng dẫn\n"
        "/reset - Xoá bộ nhớ hội thoại\n"
        "/see - Xem trạng thái key\n"
        "/error - Danh sách key lỗi (admin)\n"
        "/delete - Xoá key lỗi (admin)\n"
        "/addkey - Thêm key API mới (admin)\n"
    )

async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    save_memory(chat_id)
    conversation_memory[chat_id] = []
    usage_counter[chat_id] = 0
    save_usage()
    await update.message.reply_text("✅ Đã reset hội thoại và lượt sử dụng.")

# --- ADMIN COMMANDS ---
async def error_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("🚫 Bạn không có quyền sử dụng lệnh này.")
        return
    msg = "\n".join([
        f"🔑 {src.upper()}: {', '.join([k for k, ok in api_status[src].items() if not ok]) or 'Không có key lỗi'}"
        for src in api_keys
    ])
    await update.message.reply_text(f"📛 Danh sách key lỗi:\n{msg}")

async def delete_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("🚫 Bạn không có quyền sử dụng lệnh này.")
        return
    for src in api_keys:
        api_keys[src] = [k for k in api_keys[src] if api_status[src].get(k, False)]
    await update.message.reply_text("🗑️ Đã xoá tất cả key lỗi.")

async def see_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = "\n".join([
        f"🔍 {src.upper()}: {len([k for k in api_status[src] if api_status[src][k]])} hoạt động / {len(api_status[src])} tổng"
        for src in api_keys
    ])
    await update.message.reply_text(f"🔐 Trạng thái API Key:\n{msg}")

async def addkey_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("🚫 Bạn không có quyền sử dụng lệnh này.")
        return
    try:
        src, newkey = context.args[0], context.args[1]
        src = src.lower()
        if src not in api_keys:
            await update.message.reply_text("❌ Nguồn không hợp lệ (openrouter/deepinfra)")
            return
        if newkey not in api_keys[src]:
            api_keys[src].append(newkey)
            api_status[src][newkey] = True
            await update.message.reply_text("✅ Đã thêm key thành công.")
        else:
            await update.message.reply_text("⚠️ Key đã tồn tại.")
    except Exception as e:
        await update.message.reply_text("❌ Sai cú pháp. Dùng: /addkey [nguồn] [apikey]")
        logging.exception(e)

# --- TRẢ LỜI AI ---
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    user_message = update.message.text

    usage_counter[chat_id] = usage_counter.get(chat_id, 0) + 1
    if usage_counter[chat_id] > USAGE_LIMIT:
        await update.message.reply_text(f"⚠️ Bạn đã dùng hết lượt trong ngày ({USAGE_LIMIT}).")
        return
    save_usage()

    if chat_id not in conversation_memory:
        conversation_memory[chat_id] = []
    conversation_memory[chat_id].append({"role": "user", "content": user_message})

    for source in ["openrouter", "deepinfra"]:
        key = get_working_key(source)
        if not key:
            continue

        headers = {
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        }
        if source == "openrouter":
            headers["HTTP-Referer"] = "https://your-app-domain"
            url = "https://openrouter.ai/api/v1/chat/completions"
            model = "openai/gpt-3.5-turbo"
        elif source == "deepinfra":
            url = "https://api.deepinfra.com/v1/openai/chat/completions"
            model = "meta-llama/Meta-Llama-3-8B-Instruct"

        payload = {"model": model, "messages": conversation_memory[chat_id]}

        try:
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            data = response.json()
            if "choices" in data and data["choices"]:
                reply = data["choices"][0]["message"]["content"]
                conversation_memory[chat_id].append({"role": "assistant", "content": reply})
                await update.message.reply_text(reply)
                return
            else:
                mark_key_invalid(source, key)
        except Exception as e:
            mark_key_invalid(source, key)
            logging.exception(f"Lỗi khi gọi API {source} với key {key}")

    await update.message.reply_text("❌ Tất cả API key đã hết hạn. Vui lòng liên hệ admin cập nhật.")

# --- MAIN ---
if __name__ == '__main__':
    load_usage()

    # Đọc API key từ biến môi trường (mỗi ENV 1 key)
    openrouter_key = os.getenv("OPENROUTER_API_KEY")
    deepinfra_key = os.getenv("DEEPINFRA_API_KEY")

    if openrouter_key:
        api_keys["openrouter"] = [openrouter_key]
        api_status["openrouter"][openrouter_key] = True
    if deepinfra_key:
        api_keys["deepinfra"] = [deepinfra_key]
        api_status["deepinfra"][deepinfra_key] = True

    # Đọc token Telegram
    telegram_token = os.getenv("TELEGRAM_TOKEN")
    if not telegram_token:
        logging.error("Bạn chưa cấu hình TELEGRAM_TOKEN trong biến môi trường!")
        exit(1)

    app = ApplicationBuilder().token(telegram_token).build()

    # --- ĐĂNG KÝ HANDLER FANQIE DỊCH TRUYỆN (ưu tiên trước AI chat) ---
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_fanqie_link))

    # --- ĐĂNG KÝ HANDLER CÁC COMMAND ---
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("reset", reset))
    app.add_handler(CommandHandler("see", see_command))
    app.add_handler(CommandHandler("error", error_command))
    app.add_handler(CommandHandler("delete", delete_command))
    app.add_handler(CommandHandler("addkey", addkey_command))

    # --- HANDLER CHAT AI CHUNG (xử lý mọi text khác) ---
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print(f"🤖 {VERSION} - Bot {BOT_NAME} đã khởi động!")
    app.run_polling()
