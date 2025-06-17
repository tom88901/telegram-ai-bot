from telegram import InlineKeyboardButton, InlineKeyboardMarkup

MODELS = [
    "openrouter",
    "deepinfra"
]

def get_model_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("OpenRouter (GPT-3.5)", callback_data="model_openrouter")],
        [InlineKeyboardButton("DeepInfra (Llama 3)", callback_data="model_deepinfra")]
    ])
