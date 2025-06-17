
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
    top_users, top_models
)
from api_logging import log_api
from model_selection import get_model_keyboard, MODELS
from api_call import call_ai

BOT_NAME = "mygpt_albot"
VERSION = "v1.1"
USAGE_LIMIT = 10
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
usage_counter = {}

def load_usage():
    global usage_counter
    if os.path.exists("data/usage.json"):
        with open("data/usage.json", "r") as f:
            usage_counter = json.load(f)
    else:
        usage_counter = {}

def save_usage():
    with open("data/usage.json", "w") as f:
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
        "- /model: Chọn mô hình AI bạn muốn dùng\n"
        "- /userprofile [@username|id] (admin): Xem hồ sơ user\n"
        "- /useredit [@username|id] [field] [value] (admin): Sửa profile user\n"
        "- /see: Thống kê hệ thống\n"
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
    from user_profile import user_profiles
    total_users = len(user_profiles)
    topu = top_users()
    topm = top_models()
    txt = f"**Thống kê hệ thống:**\n"
    txt += f"- Tổng user: {total_users}\n"
    txt += "- Top user:\n"
    for i, (uid, p) in enumerate(topu):
        txt += f"  {i+1}. {p['username'] or uid}: {p.get('usage_count',0)} lượt\n"
    txt += "- Top model:\n"
    for m, cnt in topm:
        txt += f"  {m}: {cnt} user chọn\n"
    await update.message.reply_text(txt, parse_mode="Markdown")

async def model_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Vui lòng chọn mô hình AI bạn muốn dùng:",
        reply_markup=get_model_keyboard()
    )

async def model_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    username = query.from_user.username
    model = query.data.replace("model_", "")
    update_profile(user_id, selected_model=model)
    await query.answer()
    await query.edit_message_text(f"✅ Bạn đã chọn mô hình **{model}**!\nGửi câu hỏi bất kỳ để bắt đầu.")
    log_api(user_id, username, model, "model_changed", "ok")

async def userprofile_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from user_profile import user_profiles
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
        f"- Model: {profile.get('selected_model',MODELS[0])}\n"
        f"- Last active: {profile.get('last_active')}\n"
        f"- API gọi: {profile.get('api_count',0)}"
    )
    await update.message.reply_text(txt, parse_mode="Markdown")

async def useredit_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from user_profile import user_profiles
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

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from user_profile import user_profiles
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

    model = profile.get("selected_model", MODELS[0])
    messages = [{"role": "user", "content": text}]

    try:
        reply, usage = call_ai(model, messages)
        tokens = usage.get("total_tokens", 0)
        profile['api_count'] = profile.get('api_count', 0) + 1
        save_profiles()
        log_api(chat_id, username, model, text, "ok", tokens=tokens)
        await update.message.reply_text(reply)
    except Exception as e:
        log_api(chat_id, username, model, text, "error")
        await update.message.reply_text(f"❌ Lỗi gọi AI API: {e}")

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    os.makedirs("data", exist_ok=True)
    load_profiles()
    load_usage()

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
    app.add_handler(CallbackQueryHandler(model_callback, pattern="^model_"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print(f"🤖 {VERSION} - Bot {BOT_NAME} đã khởi động!")
    app.run_polling()
