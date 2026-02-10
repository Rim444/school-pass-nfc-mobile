from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDRaisedButton
from kivymd.uix.label import MDLabel
from src.ui.widgets import GlassCard
from src.nfc.nfc_manager import NFCManager
from src.utils import storage

class PassScreen(MDBoxLayout):
    def __init__(self, **kw):
        super().__init__(orientation="vertical", padding=20, spacing=20)

        self.nfc = NFCManager()

        self.card = GlassCard(size_hint_y=None, height=180)
        self.label = MDLabel(
            text="Приложите пропуск",
            halign="center",
            theme_text_color="Primary"
        )
        self.card.add_widget(self.label)

        self.add_widget(self.card)
        self.add_widget(MDRaisedButton(text="Сканировать", on_release=self.scan))
        self.add_widget(MDRaisedButton(text="Использовать", on_release=self.use))

    def scan(self, _):
        uid = self.nfc.scan()
        storage.save_pass(uid)
        self.label.text = f"Пропуск сохранён\n{uid}"
        storage.add_log("Пропуск отсканирован")

    def use(self, _):
        uid = storage.load_pass()
        if uid and self.nfc.emulate(uid):
            self.label.text = "Пропуск использован"
            storage.add_log("Пропуск применён")
