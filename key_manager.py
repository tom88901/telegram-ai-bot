import json
import os

KEY_FILES = {
    "openrouter": "data/openrouter_keys.json",
    "deepinfra": "data/deepinfra_keys.json"
}

api_keys = {}
api_status = {}

def load_keys():
    for src in KEY_FILES:
        if os.path.exists(KEY_FILES[src]):
            with open(KEY_FILES[src], "r") as f:
                api_keys[src] = json.load(f)
        else:
            api_keys[src] = []
        api_status[src] = {k: True for k in api_keys[src]}

def save_keys():
    for src in KEY_FILES:
        with open(KEY_FILES[src], "w") as f:
            json.dump(api_keys[src], f)

def add_key(src, key):
    src = src.lower()
    if src not in api_keys:
        return False, "❌ Nguồn không hợp lệ."
    if key not in api_keys[src]:
        api_keys[src].append(key)
        api_status[src][key] = True
        save_keys()
        return True, "✅ Đã thêm key thành công."
    else:
        return False, "⚠️ Key đã tồn tại."

def delete_key(src, key):
    src = src.lower()
    if src not in api_keys:
        return False, "❌ Nguồn không hợp lệ."
    if key in api_keys[src]:
        api_keys[src].remove(key)
        api_status[src].pop(key, None)
        save_keys()
        return True, "🗑️ Đã xoá key thành công."
    return False, "❌ Không tìm thấy key."

def get_working_key(src):
    for key in api_keys[src]:
        if api_status[src].get(key, False):
            return key
    return None

def mark_key_invalid(src, key):
    if src in api_status and key in api_status[src]:
        api_status[src][key] = False

def get_error_keys():
    msg = []
    for src in api_keys:
        err = [k for k in api_keys[src] if not api_status[src].get(k, True)]
        if err:
            msg.append(f"🔑 {src.upper()}: {', '.join(err)}")
    return msg if msg else ["✅ Không có key lỗi."]

def get_key_status():
    msg = []
    for src in api_keys:
        active = len([k for k in api_keys[src] if api_status[src][k]])
        total = len(api_keys[src])
        msg.append(f"🔍 {src.upper()}: {active} hoạt động / {total} tổng")
    return msg
