
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

MODELS = [
    "gpt-3.5-turbo",
    "gemini-pro",
    "deepinfra-llama3"
]

def get_model_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(model, callback_data=f"model_{model}")]
        for model in MODELS
    ])
