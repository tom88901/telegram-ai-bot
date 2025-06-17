import json
import os

PROFILE_FILE = "data/user_profile.json"
DEFAULT_MODEL = "openrouter"   # Mặc định là openrouter

user_profiles = {}

def load_profiles():
    global user_profiles
    try:
        if os.path.exists(PROFILE_FILE):
            with open(PROFILE_FILE, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content == "":
                    user_profiles = {}
                else:
                    user_profiles = json.loads(content)
        else:
            user_profiles = {}
    except Exception:
        user_profiles = {}

def save_profiles():
    with open(PROFILE_FILE, "w", encoding="utf-8") as f:
        json.dump(user_profiles, f, ensure_ascii=False, indent=2)

def get_profile(user_id, username=None):
    uid = str(user_id)
    if uid not in user_profiles:
        user_profiles[uid] = {
            "username": username or "",
            "usage_count": 0,
            "selected_model": DEFAULT_MODEL,
            "last_active": None,
            "api_count": 0
        }
    return user_profiles[uid]

def update_profile(user_id, **kwargs):
    profile = get_profile(user_id)
    for k, v in kwargs.items():
        profile[k] = v
    save_profiles()

def top_users(n=3):
    ranked = sorted(user_profiles.items(), key=lambda x: x[1].get('usage_count',0), reverse=True)
    return ranked[:n]

def top_models():
    count = {}
    for p in user_profiles.values():
        m = p.get('selected_model', DEFAULT_MODEL)
        count[m] = count.get(m, 0) + 1
    ranked = sorted(count.items(), key=lambda x: x[1], reverse=True)
    return ranked
