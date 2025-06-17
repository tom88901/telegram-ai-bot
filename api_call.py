import os
import requests

OPENROUTER_KEY = os.getenv("OPENROUTER_API")
DEEPINFRA_KEY = os.getenv("DEEPINFRA_API")

def call_openrouter(messages):
    headers = {
        "Authorization": f"Bearer {OPENROUTER_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://your-app-domain"
    }
    url = "https://openrouter.ai/api/v1/chat/completions"
    payload = {
        "model": "openai/gpt-3.5-turbo",
        "messages": messages
    }
    r = requests.post(url, headers=headers, json=payload, timeout=30)
    r.raise_for_status()
    data = r.json()
    reply = data["choices"][0]["message"]["content"]
    usage = data.get("usage", {})
    return reply, usage

def call_deepinfra(messages):
    headers = {
        "Authorization": f"Bearer {DEEPINFRA_KEY}",
        "Content-Type": "application/json"
    }
    url = "https://api.deepinfra.com/v1/openai/chat/completions"
    payload = {
        "model": "meta-llama/Meta-Llama-3-8B-Instruct",
        "messages": messages
    }
    r = requests.post(url, headers=headers, json=payload, timeout=30)
    r.raise_for_status()
    data = r.json()
    reply = data["choices"][0]["message"]["content"]
    usage = data.get("usage", {})
    return reply, usage

def call_ai(model, messages):
    if model == "openrouter":
        return call_openrouter(messages)
    elif model == "deepinfra":
        return call_deepinfra(messages)
    else:
        return "Model không hợp lệ!", {"total_tokens": 0}
