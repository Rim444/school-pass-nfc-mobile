"""
School Pass NFC — СТАБИЛЬНАЯ ВЕРСИЯ
- Убраны все обращения к несуществующим id
- Явный цвет кнопки (без self.theme_cls)
- Фон только через Window.clearcolor
- Аватар — иконка (без загрузки файлов)
"""

import json
import os
import threading
import time

from kivy.core.window import Window
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition
from kivy.utils import platform
from kivymd.app import MDApp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDRaisedButton, MDIconButton
from kivymd.uix.card import MDCard
from kivymd.uix.dialog import MDDialog
from kivymd.uix.label import MDLabel
from kivymd.uix.list import MDList, OneLineListItem
from kivy.uix.scrollview import ScrollView
from kivymd.uix.textfield import MDTextField
from plyer import vibrator

if platform != 'android':
    Window.size = (400, 700)


# -------------------------------------------------------------------
# ГЛАВНЫЙ ЭКРАН
# -------------------------------------------------------------------
class MainScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.dialog = None
        self.nfc_data = None
        self.build_ui()
        self.load_profile()

    def build_ui(self):
        layout = MDBoxLayout(orientation='vertical', spacing=20, padding=20)

        # --- Карточка профиля ---
        card = MDCard(
            orientation='vertical',
            padding=20,
            spacing=10,
            size_hint=(1, None),
            height=200,
            elevation=6,
            radius=15,
            md_bg_color=(0.2, 0.2, 0.2, 0.9)
        )

        from kivymd.uix.label import MDIcon
        self.avatar = MDIcon(
            icon='account-circle',
            size_hint=(None, None),
            size=(80, 80),
            halign='center',
            valign='middle',
            theme_text_color='Custom',
            text_color=(0.2, 0.6, 0.9, 1)  # явный синий
        )
        self.avatar.pos_hint = {'center_x': 0.5}
        card.add_widget(self.avatar)

        self.name_label = MDLabel(
            text='Иванов Иван',
            halign='center',
            theme_text_color='Custom',
            text_color=(1, 1, 1, 1),
            font_style='H5',
            size_hint_y=None,
            height=40
        )
        card.add_widget(self.name_label)

        self.class_label = MDLabel(
            text='Ученик 11А класса',
            halign='center',
            theme_text_color='Custom',
            text_color=(0.8, 0.8, 0.8, 1),
            font_style='Subtitle1',
            size_hint_y=None,
            height=30
        )
        card.add_widget(self.class_label)

        self.card_id_label = MDLabel(
            text='ID карты: не привязана',
            halign='center',
            theme_text_color='Custom',
            text_color=(0.6, 0.6, 0.6, 1),
            font_style='Caption',
            size_hint_y=None,
            height=30
        )
        card.add_widget(self.card_id_label)

        layout.add_widget(card)

        # --- Кнопка NFC (явный цвет) ---
        self.nfc_button = MDRaisedButton(
            text='СЧИТАТЬ ПРОПУСК',
            size_hint=(1, None),
            height=50,
            md_bg_color=(0.2, 0.6, 0.9, 1),  # синий
            on_release=self.read_nfc
        )
        layout.add_widget(self.nfc_button)

        # --- Статус ---
        self.status_label = MDLabel(
            text='Нажмите кнопку и поднесите карту к NFC',
            halign='center',
            theme_text_color='Custom',
            text_color=(0.8, 0.8, 0.8, 1),
            font_style='Body1',
            size_hint_y=None,
            height=40
        )
        layout.add_widget(self.status_label)

        # --- Кнопка настроек ---
        settings_btn = MDIconButton(
            icon='cog',
            pos_hint={'center_x': 0.5},
            on_release=lambda x: setattr(self.manager, 'current', 'settings')
        )
        layout.add_widget(settings_btn)

        # --- История (заглушка) ---
        history_label = MDLabel(
            text='Последние события:',
            halign='left',
            theme_text_color='Custom',
            text_color=(1, 1, 1, 1),
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
                divider='Full',
                theme_text_color='Custom',
                text_color=(0.9, 0.9, 0.9, 1)
            )
            list_view.add_widget(item)
        scroll.add_widget(list_view)
        layout.add_widget(scroll)

        self.add_widget(layout)

    def load_profile(self):
        """Загружает имя, класс, UID из settings.json (без аватара и фона)"""
        settings_file = 'settings.json'
        if os.path.exists(settings_file):
            with open(settings_file, 'r') as f:
                data = json.load(f)
                self.name_label.text = data.get('name', 'Иванов Иван')
                self.class_label.text = data.get('class', '11А')
                self.card_id_label.text = data.get('card_uid', 'ID карты: не привязана')

    def read_nfc(self, instance):
        self.status_label.text = 'Сканирование... Поднесите карту'

        def simulate():
            time.sleep(2)
            self.nfc_data = '04:5A:6B:7C:8D:9E'
            self.card_id_label.text = f'ID карты: {self.nfc_data}'
            self.status_label.text = 'Карта считана!'
            self.show_dialog('Успех', 'Карта успешно привязана!')
            self.save_card_uid(self.nfc_data)
            if platform == 'android':
                try:
                    vibrator.vibrate(0.1)
                except:
                    pass

        threading.Thread(target=simulate).start()

    def save_card_uid(self, uid):
        settings_file = 'settings.json'
        data = {}
        if os.path.exists(settings_file):
            with open(settings_file, 'r') as f:
                data = json.load(f)
        data['card_uid'] = f'ID карты: {uid}'
        with open(settings_file, 'w') as f:
            json.dump(data, f)

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


# -------------------------------------------------------------------
# ЭКРАН НАСТРОЕК (УПРОЩЁННЫЙ, БЕЗ ВЫБОРА ИЗОБРАЖЕНИЙ)
# -------------------------------------------------------------------
class SettingsScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.dialog = None
        self.build_ui()
        self.load_settings()

    def build_ui(self):
        layout = MDBoxLayout(orientation='vertical', spacing=20, padding=20)

        header = MDBoxLayout(adaptive_height=True)
        back_btn = MDIconButton(
            icon='arrow-left',
            on_release=lambda x: setattr(self.manager, 'current', 'main')
        )
        header.add_widget(back_btn)
        header.add_widget(MDLabel(text='Настройки', font_style='H5'))
        layout.add_widget(header)

        self.name_field = MDTextField(
            hint_text='ФИО',
            size_hint_x=1
        )
        layout.add_widget(self.name_field)

        self.class_field = MDTextField(
            hint_text='Класс',
            size_hint_x=1
        )
        layout.add_widget(self.class_field)

        # Кнопка удаления пропуска
        btn_delete = MDRaisedButton(
            text='Удалить пропуск',
            md_bg_color=(0.8, 0.2, 0.2, 1),
            on_release=self.delete_pass,
            size_hint=(1, None),
            height=48
        )
        layout.add_widget(btn_delete)

        # Кнопка сохранения
        btn_save = MDRaisedButton(
            text='Сохранить',
            on_release=self.save_settings,
            size_hint=(1, None),
            height=48
        )
        layout.add_widget(btn_save)

        self.add_widget(layout)

    def load_settings(self):
        settings_file = 'settings.json'
        if os.path.exists(settings_file):
            with open(settings_file, 'r') as f:
                data = json.load(f)
                self.name_field.text = data.get('name', 'Иванов Иван')
                self.class_field.text = data.get('class', '11А')
        else:
            self.name_field.text = 'Иванов Иван'
            self.class_field.text = '11А'

    def save_settings(self, *args):
        data = {}
        settings_file = 'settings.json'
        if os.path.exists(settings_file):
            with open(settings_file, 'r') as f:
                data = json.load(f)

        data['name'] = self.name_field.text
        data['class'] = self.class_field.text

        with open(settings_file, 'w') as f:
            json.dump(data, f)

        main_screen = self.manager.get_screen('main')
        main_screen.name_label.text = self.name_field.text
        main_screen.class_label.text = self.class_field.text

        self.show_dialog('Настройки сохранены')

    def delete_pass(self, *args):
        main_screen = self.manager.get_screen('main')
        main_screen.card_id_label.text = 'ID карты: не привязана'
        main_screen.nfc_data = None
        settings_file = 'settings.json'
        if os.path.exists(settings_file):
            with open(settings_file, 'r') as f:
                data = json.load(f)
            if 'card_uid' in data:
                del data['card_uid']
                with open(settings_file, 'w') as f:
                    json.dump(data, f)
        self.show_dialog('Пропуск удалён')

    def show_dialog(self, text):
        if not self.dialog:
            self.dialog = MDDialog(
                text=text,
                buttons=[MDRaisedButton(text='OK', on_release=lambda x: self.dialog.dismiss())]
            )
        else:
            self.dialog.text = text
        self.dialog.open()


# -------------------------------------------------------------------
# ОСНОВНОЕ ПРИЛОЖЕНИЕ
# -------------------------------------------------------------------
class SchoolPassApp(MDApp):
    def build(self):
        self.title = 'School Pass'
        self.theme_cls.theme_style = 'Dark'
        self.theme_cls.primary_palette = 'Blue'
        self.theme_cls.accent_palette = 'LightBlue'
        Window.clearcolor = (0.12, 0.12, 0.12, 1)  # тёмно-серый фон

        sm = ScreenManager(transition=SlideTransition(duration=0.3))
        sm.add_widget(MainScreen(name='main'))
        sm.add_widget(SettingsScreen(name='settings'))
        return sm

    def on_start(self):
        # Фон уже задан через Window.clearcolor — никаких изображений
        pass


if __name__ == '__main__':
    SchoolPassApp().run()