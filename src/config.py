from kivy.storage.jsonstore import JsonStore

store = JsonStore("config.json")

class Config:
    theme = store.get("theme")["value"] if store.exists("theme") else "Dark"
    account = store.get("account")["value"] if store.exists("account") else "User"
    pin = store.get("pin")["value"] if store.exists("pin") else None

    @staticmethod
    def set_theme(v):
        Config.theme = v
        store.put("theme", value=v)

    @staticmethod
    def set_account(v):
        Config.account = v
        store.put("account", value=v)

    @staticmethod
    def set_pin(v):
        Config.pin = v
        store.put("pin", value=v)
