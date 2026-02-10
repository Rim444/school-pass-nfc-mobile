from kivy.storage.jsonstore import JsonStore
from datetime import datetime

store = JsonStore("data.json")

def save_pass(uid):
    store.put("pass", uid=uid)

def load_pass():
    return store.get("pass")["uid"] if store.exists("pass") else None

def delete_pass():
    if store.exists("pass"):
        store.delete("pass")

def add_log(text):
    logs = store.get("journal")["items"] if store.exists("journal") else []
    logs.append(f"{datetime.now().strftime('%d.%m %H:%M')} — {text}")
    store.put("journal", items=logs)

def get_logs():
    return store.get("journal")["items"] if store.exists("journal") else []
