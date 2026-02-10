from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.textfield import MDTextField
from kivymd.uix.button import MDFlatButton
from src.config import Config
from src.utils.storage import delete_pass

class SettingsScreen(MDBoxLayout):
    def __init__(self, **kw):
        super().__init__(orientation="vertical", padding=20, spacing=15)

        name = MDTextField(text=Config.account, hint_text="Имя")
        pin = MDTextField(hint_text="PIN", password=True)

        self.add_widget(name)
        self.add_widget(MDFlatButton(
            text="Сохранить имя",
            on_release=lambda _: Config.set_account(name.text)
        ))

        self.add_widget(pin)
        self.add_widget(MDFlatButton(
            text="Установить PIN",
            on_release=lambda _: Config.set_pin(pin.text)
        ))

        self.add_widget(MDFlatButton(
            text="Удалить пропуск",
            on_release=lambda _: delete_pass()
        ))
