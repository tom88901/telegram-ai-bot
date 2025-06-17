from key_manager import get_working_key, mark_key_invalid
import requests

def call_openrouter(messages):
    key = get_working_key("openrouter")
    if not key:
        raise Exception("❌ Tất cả key OpenRouter đã hết hạn hoặc lỗi!")
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://your-app-domain"
    }
    url = "https://openrouter.ai/api/v1/chat/completions"
    payload = {
        "model": "openai/gpt-3.5-turbo",
        "messages": messages
    }
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=30)
        if r.status_code == 401:
            mark_key_invalid("openrouter", key)
            raise Exception("401 Unauthorized")
        r.raise_for_status()
        data = r.json()
        reply = data["choices"][0]["message"]["content"]
        usage = data.get("usage", {})
        return reply, usage
    except Exception as e:
        mark_key_invalid("openrouter", key)
        raise e

def call_deepinfra(messages):
    key = get_working_key("deepinfra")
    if not key:
        raise Exception("❌ Tất cả key DeepInfra đã hết hạn hoặc lỗi!")
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json"
    }
    url = "https://api.deepinfra.com/v1/openai/chat/completions"
    payload = {
        "model": "meta-llama/Meta-Llama-3-8B-Instruct",
        "messages": messages
    }
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=30)
        if r.status_code == 401:
            mark_key_invalid("deepinfra", key)
            raise Exception("401 Unauthorized")
        r.raise_for_status()
        data = r.json()
        reply = data["choices"][0]["message"]["content"]
        usage = data.get("usage", {})
        return reply, usage
    except Exception as e:
        mark_key_invalid("deepinfra", key)
        raise e

def call_ai(model, messages):
    if model == "openrouter":
        return call_openrouter(messages)
    elif model == "deepinfra":
        return call_deepinfra(messages)
    else:
        return "Model không hợp lệ!", {"total_tokens": 0}
