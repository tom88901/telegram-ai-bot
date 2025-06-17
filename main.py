import os
import logging
import datetime
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters
)

from user_profile import (
    load_profiles, save_profiles, get_profile, update_profile,
    top_users, top_models, user_profiles
)
from api_call import call_ai
from model_selection import get_model_keyboard
from api_logging import log_api
from key_manager import (
    load_keys, save_keys, add_key, delete_key,
    get_error_keys, get_key_status
)

BOT_NAME = "mygpt_albot"
VERSION = "v1.2"
USAGE_LIMIT = 10
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
USAGE_TRACK_FILE = "data/usage.json"
usage_counter = {}

def load_usage():
    global usage_counter
    if os.path.exists(USAGE_TRACK_FILE):
        import json
        with open(USAGE_TRACK_FILE, "r") as f:
            usage_counter = json.load(f)
    else:
        usage_counter = {}

def save_usage():
    import json
    with open(USAGE_TRACK_FILE, "w") as f:
        json.dump(usage_counter, f)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await update.message.reply_text(
        f"🤖 Chào {user.first_name or ''}! Bot {BOT_NAME} phiên bản {VERSION}.\n"
        "Gửi mình câu hỏi để nhận phản hồi thông minh nhé!\n"
        "Gợi ý: dùng /help để xem hướng dẫn."
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 **Hướng dẫn sử dụng**:\n"
        "- /start: Khởi động lại bot\n"
        "- /reset: Xoá bộ nhớ hội thoại & lượt dùng\n"
        "- /model: Chọn nguồn AI bạn muốn dùng (OpenRouter/DeepInfra)\n"
        "- /see: Xem trạng thái key hiện tại\n"
        "- /userprofile [@username|id] (admin): Xem hồ sơ user\n"
        "- /useredit [@username|id] [field] [value] (admin): Sửa hồ sơ user\n"
        "- /addkey [nguồn] [apikey] (admin): Thêm API key\n"
        "- /delete [nguồn] [apikey] (admin): Xoá key\n"
        "- /error (admin): Danh sách key lỗi\n"
        "- /help: Xem lại hướng dẫn\n"
        "⏱️ Mỗi user tối đa 10 lượt/ngày (admin có thể tăng/giảm)\n"
        "Liên hệ admin nếu cần thêm quyền!"
    )

async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    usage_counter[chat_id] = 0
    save_usage()
    profile = get_profile(chat_id, update.effective_user.username)
    update_profile(chat_id, usage_count=0)
    await update.message.reply_text("✅ Đã reset hội thoại và lượt sử dụng cho bạn.")

async def see_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = "\n".join(get_key_status())
    await update.message.reply_text(msg)

async def model_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Vui lòng chọn nguồn AI bạn muốn dùng:",
        reply_markup=get_model_keyboard()
    )

async def model_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    username = query.from_user.username
    model = query.data.replace("model_", "")
    update_profile(user_id, selected_model=model)
    await query.answer()
    if model == "openrouter":
        txt = "✅ Bạn đã chọn nguồn: **OpenRouter (GPT-3.5-turbo)**"
    elif model == "deepinfra":
        txt = "✅ Bạn đã chọn nguồn: **DeepInfra (Llama 3)**"
    else:
        txt = "❌ Lựa chọn không hợp lệ!"
    await query.edit_message_text(txt, parse_mode="Markdown")
    log_api(user_id, username, model, "model_changed", "ok")

async def userprofile_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("🚫 Không có quyền.")
        return
    if not context.args:
        await update.message.reply_text("Cú pháp: /userprofile [@username|id]")
        return
    key = context.args[0]
    if key.startswith("@"):
        profile = next((p for p in user_profiles.values() if p["username"] == key[1:]), None)
    else:
        profile = user_profiles.get(str(key))
    if not profile:
        await update.message.reply_text("❌ Không tìm thấy user.")
        return
    txt = (
        f"**User profile:**\n"
        f"- Username: {profile.get('username','')}\n"
        f"- Số lượt: {profile.get('usage_count',0)}\n"
        f"- Model: {profile.get('selected_model','openrouter')}\n"
        f"- Last active: {profile.get('last_active')}\n"
        f"- API gọi: {profile.get('api_count',0)}"
    )
    await update.message.reply_text(txt, parse_mode="Markdown")

async def useredit_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("🚫 Không có quyền.")
        return
    if len(context.args) < 3:
        await update.message.reply_text("Cú pháp: /useredit [@username|id] [field] [value]")
        return
    key, field, value = context.args[0], context.args[1], context.args[2]
    if key.startswith("@"):
        uid = next((uid for uid, p in user_profiles.items() if p["username"] == key[1:]), None)
    else:
        uid = str(key)
    if not uid or uid not in user_profiles:
        await update.message.reply_text("❌ Không tìm thấy user.")
        return
    if field not in ["usage_count", "selected_model", "api_count"]:
        await update.message.reply_text("❌ Field không hợp lệ.")
        return
    if field in ["usage_count", "api_count"]:
        try:
            value = int(value)
        except:
            await update.message.reply_text("❌ Giá trị phải là số nguyên.")
            return
    update_profile(uid, **{field: value})
    await update.message.reply_text(f"✅ Đã cập nhật user {uid} ({field}={value})")

async def addkey_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("🚫 Bạn không có quyền sử dụng lệnh này.")
        return
    if len(context.args) < 2:
        await update.message.reply_text("Cú pháp: /addkey [nguồn] [apikey]")
        return
    src, key = context.args[0].lower(), context.args[1]
    ok, msg = add_key(src, key)
    await update.message.reply_text(msg)

async def delete_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("🚫 Bạn không có quyền sử dụng lệnh này.")
        return
    if len(context.args) < 2:
        await update.message.reply_text("Cú pháp: /delete [nguồn] [apikey]")
        return
    src, key = context.args[0].lower(), context.args[1]
    ok, msg = delete_key(src, key)
    await update.message.reply_text(msg)

async def error_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("🚫 Bạn không có quyền sử dụng lệnh này.")
        return
    msg = "\n".join(get_error_keys())
    await update.message.reply_text(msg)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat_id = str(user.id)
    username = user.username
    text = update.message.text

    profile = get_profile(chat_id, username)
    usage_counter[chat_id] = usage_counter.get(chat_id, 0) + 1
    profile['usage_count'] = usage_counter[chat_id]
    profile['last_active'] = datetime.datetime.now().isoformat()
    save_usage()
    save_profiles()

    if usage_counter[chat_id] > USAGE_LIMIT:
        await update.message.reply_text(
            f"⚠️ Bạn đã dùng hết lượt ({USAGE_LIMIT}/ngày). Liên hệ admin để tăng giới hạn."
        )
        log_api(chat_id, username, profile['selected_model'], text, "limit")
        return

    model = profile.get("selected_model", "openrouter")
    messages = [{"role": "user", "content": text}]

    # Luân phiên gọi từng nguồn
    sources = ["openrouter", "deepinfra"] if model == "openrouter" else ["deepinfra", "openrouter"]
    for src in sources:
        try:
            reply, usage = call_ai(src, messages)
            tokens = usage.get("total_tokens", 0)
            profile['api_count'] = profile.get('api_count', 0) + 1
            save_profiles()
            log_api(chat_id, username, src, text, "ok", tokens=tokens)
            await update.message.reply_text(reply)
            return
        except Exception as e:
            log_api(chat_id, username, src, text, "error")
            continue

    await update.message.reply_text("❌ Tất cả API key đã hết hạn hoặc lỗi. Vui lòng liên hệ admin!")

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    os.makedirs("data", exist_ok=True)
    load_profiles()
    load_usage()
    load_keys()

    token = os.getenv("TELEGRAM_TOKEN")
    if not token:
        logging.error("Chưa cấu hình TELEGRAM_TOKEN trong biến môi trường!")
        exit(1)

    app = ApplicationBuilder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("reset", reset))
    app.add_handler(CommandHandler("see", see_command))
    app.add_handler(CommandHandler("model", model_command))
    app.add_handler(CommandHandler("userprofile", userprofile_command))
    app.add_handler(CommandHandler("useredit", useredit_command))
    app.add_handler(CommandHandler("addkey", addkey_command))
    app.add_handler(CommandHandler("delete", delete_command))
    app.add_handler(CommandHandler("error", error_command))
    app.add_handler(CallbackQueryHandler(model_callback, pattern="^model_"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print(f"🤖 {VERSION} - Bot {BOT_NAME} đã khởi động!")
    app.run_polling()
