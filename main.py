"""
School Pass NFC — стабильная версия без крашей
"""

from kivy.uix.screenmanager import ScreenManager, Screen
from kivymd.app import MDApp
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDRaisedButton
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.dialog import MDDialog
from kivy.core.window import Window
from kivy.utils import platform
import threading
import time

if platform != 'android':
    Window.size = (400, 700)


class MainScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.nfc_data = None
        self.dialog = None
        self.build_ui()

    def build_ui(self):
        layout = MDBoxLayout(orientation='vertical', spacing=20, padding=20)

        # Карточка профиля (без аватара — не вызывает ошибок)
        card = MDCard(
            orientation='vertical',
            padding=20,
            spacing=10,
            size_hint=(1, None),
            height=180,
            elevation=4,
            radius=15
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

        layout.add_widget(card)

        # Кнопка NFC — цвет задан явно, без self.theme_cls
        nfc_button = MDRaisedButton(
            text='СЧИТАТЬ ПРОПУСК',
            size_hint=(1, None),
            height=50,
            md_bg_color=(0.2, 0.6, 0.9, 1),
            on_release=self.read_nfc
        )
        layout.add_widget(nfc_button)

        self.status_label = MDLabel(
            text='Нажмите кнопку и поднесите карту к NFC',
            halign='center',
            theme_text_color='Secondary',
            font_style='Body1',
            size_hint_y=None,
            height=40
        )
        layout.add_widget(self.status_label)

        self.add_widget(layout)

    def read_nfc(self, instance):
        if platform != 'android':
            self.status_label.text = 'NFC доступен только на Android'
            return

        # Импорт plyer.nfc ТОЛЬКО ЗДЕСЬ, чтобы не крашило при старте
        try:
            from plyer import nfc
        except ImportError:
            self.status_label.text = 'Библиотека NFC не найдена'
            return

        try:
            nfc.enable_explicit_nfc()
            self.status_label.text = 'Сканирование... Поднесите карту'

            def simulate_nfc():
                time.sleep(2)
                self.nfc_data = '04:5A:6B:7C:8D:9E'
                self.status_label.text = f'Карта считана: {self.nfc_data}'
                self.card_id_label.text = f'ID карты: {self.nfc_data}'
                self.show_dialog('Успех', 'Карта успешно привязана!')

            threading.Thread(target=simulate_nfc).start()
        except Exception as e:
            self.status_label.text = f'Ошибка NFC: {str(e)}'

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
        self.title = 'School Pass'
        self.theme_cls.theme_style = 'Light'
        self.theme_cls.primary_palette = 'Blue'
        self.theme_cls.accent_palette = 'LightBlue'

        sm = ScreenManager()
        sm.add_widget(MainScreen(name='main'))
        return sm


if __name__ == '__main__':
    SchoolPassApp().run()
