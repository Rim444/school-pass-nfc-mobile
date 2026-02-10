import random

class NFCManager:
    def scan(self):
        return f"NFC-{random.randint(100000,999999)}"

    def emulate(self, uid):
        return True
