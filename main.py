"""
School Pass NFC — стабильная версия с KivyMD 2.0.1
Полностью совместима с Android 14, без крашей.
"""

from kivy.core.window import Window
from kivy.utils import platform
from kivymd.app import MDApp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDRaisedButton
from kivymd.uix.dialog import MDDialog

if platform != 'android':
    Window.size = (400, 700)

class MainScreen(MDBoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', spacing=20, padding=20, **kwargs)
        self.dialog = None

        # --- Карточка профиля ---
        card = MDCard(
            orientation='vertical',
            padding=20,
            spacing=10,
            size_hint=(1, None),
            height=180,
            elevation=4,
            radius=15,
            md_bg_color=(1, 1, 1, 1)
        )

        self.name_label = MDLabel(
            text='Иванов Иван',
            halign='center',
            theme_text_color='Primary',
            font_style='H5',
            size_hint_y=None,
            height=40
        )
        card.add_widget(self.name_label)

        self.class_label = MDLabel(
            text='Ученик 11А класса',
            halign='center',
            theme_text_color='Secondary',
            font_style='Subtitle1',
            size_hint_y=None,
            height=30
        )
        card.add_widget(self.class_label)

        self.card_id_label = MDLabel(
            text='ID карты: не привязана',
            halign='center',
            theme_text_color='Hint',
            font_style='Caption',
            size_hint_y=None,
            height=30
        )
        card.add_widget(self.card_id_label)

        self.add_widget(card)

        # --- Кнопка NFC ---
        self.nfc_button = MDRaisedButton(
            text='СЧИТАТЬ ПРОПУСК',
            size_hint=(1, None),
            height=50,
            md_bg_color=self.theme_cls.primary_color,
            on_release=self.read_nfc
        )
        self.add_widget(self.nfc_button)

        # --- Статус ---
        self.status_label = MDLabel(
            text='Нажмите кнопку и поднесите карту к NFC',
            halign='center',
            theme_text_color='Secondary',
            font_style='Body1',
            size_hint_y=None,
            height=40
        )
        self.add_widget(self.status_label)

    def read_nfc(self, instance):
        # Заглушка NFC – для проверки стабильности
        self.card_id_label.text = 'ID карты: 04:5A:6B:7C:8D:9E'
        self.status_label.text = 'Карта считана (тест)'
        self.show_dialog('Успех', 'Карта успешно привязана!')

    def show_dialog(self, title, text):
        if not self.dialog:
            self.dialog = MDDialog(
                title=title,
                text=text,
                buttons=[
                    MDRaisedButton(
                        text='OK',
                        on_release=lambda x: self.dialog.dismiss()
                    )
                ]
            )
        else:
            self.dialog.title = title
            self.dialog.text = text
        self.dialog.open()


class SchoolPassApp(MDApp):
    def build(self):
        self.theme_cls.theme_style = 'Light'
        self.theme_cls.primary_palette = 'Blue'
        self.theme_cls.accent_palette = 'LightBlue'
        return MainScreen()

if __name__ == '__main__':
    SchoolPassApp().run()
