import logging
import json
import os
import requests
from datetime import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "dán_token_telegram_ở_đây_nếu_test")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "dán_api_key_openrouter")

VERSION = "v1.4"
USAGE_LIMIT = 10
USAGE_TRACK_FILE = "usage.json"
MEMORY_FILE_TEMPLATE = "memory_{}.json"

conversation_memory = {}
usage_counter = {}

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

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"🤖 Xin chào! Mình là bot AI `mygpt_albot` dùng OpenRouter API.\nGửi mình câu hỏi nhé!"
    )

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

async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    save_memory(chat_id)
    conversation_memory[chat_id] = []
    usage_counter[chat_id] = 0
    save_usage()
    await update.message.reply_text("✅ Bộ nhớ hội thoại đã được xoá và lưu lại.")

async def handle_message(update: Update,
