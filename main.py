"""
School Pass NFC Mobile Application
Полнофункциональный клиент для работы с NFC-пропусками
"""

from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen
from kivymd.app import MDApp
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDRaisedButton
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.dialog import MDDialog
from kivymd.uix.list import MDList, OneLineListItem
from kivy.uix.scrollview import ScrollView
from kivy.core.window import Window
from kivy.utils import platform
from plyer import nfc
import requests
import json

# Настройка окна для ПК (для тестирования)
if platform != 'android':
    Window.size = (400, 700)


class MainScreen(Screen):
    """Главный экран с профилем и NFC-кнопкой"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.build_ui()
        self.nfc_data = None
        self.dialog = None

    def build_ui(self):
        """Построение интерфейса"""
        layout = MDBoxLayout(orientation='vertical', spacing=20, padding=20)

        # --- Карточка профиля ---
        card = MDCard(
            orientation='vertical',
            padding=20,
            spacing=10,
            size_hint=(1, None),
            height=220,
            elevation=4,
            radius=15
        )

        # Аватар (иконка)
        from kivymd.uix.imagelist import MDSmartTile
        from kivymd.icon_definitions import md_icons

        avatar = MDSmartTile(
            source='data/avatar.png',
            size_hint=(None, None),
            size=(80, 80),
            radius=40,
            pos_hint={'center_x': 0.5}
        )
        # Если файла avatar.png нет, замените на MDIcon
        if not avatar.source:
            from kivymd.uix.label import MDIcon
            avatar = MDIcon(
                icon='account-circle',
                size_hint=(None, None),
                size=(80, 80),
                halign='center'
            )
        card.add_widget(avatar)

        # Имя пользователя
        self.name_label = MDLabel(
            text='Иванов Иван',
            halign='center',
            theme_text_color='Primary',
            font_style='H5',
            size_hint_y=None,
            height=40
        )
        card.add_widget(self.name_label)

        # Класс / роль
        self.class_label = MDLabel(
            text='Ученик 11А класса',
            halign='center',
            theme_text_color='Secondary',
            font_style='Subtitle1',
            size_hint_y=None,
            height=30
        )
        card.add_widget(self.class_label)

        # ID карты (если есть)
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

        # --- Кнопка NFC ---
        nfc_button = MDRaisedButton(
            text='СЧИТАТЬ ПРОПУСК',
            size_hint=(1, None),
            height=50,
            md_bg_color=(0.2, 0.6, 0.9, 1),
            on_release=self.read_nfc
        )
        layout.add_widget(nfc_button)

        # --- Статус NFC ---
        self.status_label = MDLabel(
            text='Нажмите кнопку и поднесите карту к NFC',
            halign='center',
            theme_text_color='Secondary',
            font_style='Body1',
            size_hint_y=None,
            height=40
        )
        layout.add_widget(self.status_label)

        # --- История посещений (заглушка) ---
        history_label = MDLabel(
            text='Последние события:',
            halign='left',
            theme_text_color='Primary',
            font_style='Subtitle2',
            size_hint_y=None,
            height=30
        )
        layout.add_widget(history_label)

        scroll = ScrollView(size_hint=(1, 0.3))
        list_view = MDList()
        for i in range(3):
            item = OneLineListItem(
                text=f'Вход в школу • 08:3{i}',
                divider='Full'
            )
            list_view.add_widget(item)
        scroll.add_widget(list_view)
        layout.add_widget(scroll)

        self.add_widget(layout)

    def read_nfc(self, instance):
        """Обработка нажатия кнопки NFC"""
        if platform == 'android':
            try:
                # Запрос включения NFC
                nfc.enable_explicit_nfc()
                self.status_label.text = 'Сканирование... Поднесите карту'

                # Здесь должен быть код для чтения метки через pyjnius
                # Для примера используем симуляцию
                from threading import Thread
                import time

                def simulate_nfc():
                    time.sleep(2)
                    self.nfc_data = '04:5A:6B:7C:8D:9E'  # Пример UID
                    self.status_label.text = f'Карта считана: {self.nfc_data}'
                    self.card_id_label.text = f'ID карты: {self.nfc_data}'
                    self.show_dialog('Успех', 'Карта успешно привязана!')

                Thread(target=simulate_nfc).start()

            except Exception as e:
                self.status_label.text = f'Ошибка NFC: {str(e)}'
        else:
            self.status_label.text = 'NFC доступен только на Android'

    def show_dialog(self, title, text):
        """Отображение диалогового окна"""
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
    """Основной класс приложения"""
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
