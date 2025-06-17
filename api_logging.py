
import os
import json
import datetime

LOG_DIR = "data/logs"
os.makedirs(LOG_DIR, exist_ok=True)

def log_api(user_id, username, model, message, status="ok", tokens=0):
    now = datetime.datetime.now()
    log_file = f"{LOG_DIR}/log_{now.strftime('%Y-%m-%d')}.jsonl"
    entry = {
        "time": now.isoformat(),
        "user_id": user_id,
        "username": username,
        "model": model,
        "tokens": tokens,
        "status": status,
        "msg": message
    }
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
