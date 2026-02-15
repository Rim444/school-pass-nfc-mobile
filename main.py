"""
School Pass NFC — Стабильная версия без Screen
"""

import json
import os
import threading
import time
from datetime import datetime

from kivy.core.window import Window
from kivy.utils import platform
from kivymd.app import MDApp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDRaisedButton
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.dialog import MDDialog
from kivymd.uix.list import MDList, TwoLineListItem
from kivy.uix.scrollview import ScrollView
from kivymd.uix.textfield import MDTextField
from kivymd.uix.switch import MDSwitch
from kivymd.uix.bottomnavigation import MDBottomNavigation, MDBottomNavigationItem
from kivymd.uix.toolbar import MDTopAppBar
from plyer import vibrator

if platform != 'android':
    Window.size = (400, 700)

Window.softinput_mode = 'pan'


# -------------------------------------------------------------------
# Главный экран (вкладка "Главная")
# -------------------------------------------------------------------
class MainScreen(MDBoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', spacing=0, padding=0, **kwargs)
        self.dialog = None
        self.nfc_data = None
        self.last_event_time = None
        self.build_ui()
        self.load_profile()

    def build_ui(self):
        # Верхний toolbar
        self.toolbar = MDTopAppBar(title='School Pass')
        self.add_widget(self.toolbar)

        # Основной контент
        content = MDBoxLayout(orientation='vertical', spacing=20, padding=20, adaptive_height=True)

        # Карточка профиля
        card = MDCard(
            orientation='vertical',
            padding=20,
            spacing=10,
            size_hint=(1, None),
            height=200,
            elevation=6,
            radius=15,
            md_bg_color=self.get_card_bg_color()
        )

        from kivymd.uix.label import MDIcon
        self.avatar = MDIcon(
            icon='account-circle',
            size_hint=(None, None),
            size=(80, 80),
            halign='center',
            valign='middle',
            theme_text_color='Custom',
            text_color=self.get_accent_color()
        )
        self.avatar.pos_hint = {'center_x': 0.5}
        card.add_widget(self.avatar)

        self.name_label = MDLabel(
            text='Иванов Иван',
            halign='center',
            theme_text_color='Custom',
            text_color=self.get_text_color(),
            font_style='H5',
            size_hint_y=None,
            height=40
        )
        card.add_widget(self.name_label)

        self.class_label = MDLabel(
            text='Ученик 11А класса',
            halign='center',
            theme_text_color='Custom',
            text_color=self.get_secondary_text_color(),
            font_style='Subtitle1',
            size_hint_y=None,
            height=30
        )
        card.add_widget(self.class_label)

        self.card_id_label = MDLabel(
            text='ID карты: не привязана',
            halign='center',
            theme_text_color='Custom',
            text_color=self.get_hint_text_color(),
            font_style='Caption',
            size_hint_y=None,
            height=30
        )
        card.add_widget(self.card_id_label)

        content.add_widget(card)

        # Кнопка NFC
        self.nfc_button = MDRaisedButton(
            text='СЧИТАТЬ ПРОПУСК',
            size_hint=(1, None),
            height=50,
            md_bg_color=self.get_accent_color(),
            on_release=self.read_nfc
        )
        content.add_widget(self.nfc_button)

        # Статус
        self.status_label = MDLabel(
            text='Нажмите кнопку и поднесите карту к NFC',
            halign='center',
            theme_text_color='Custom',
            text_color=self.get_secondary_text_color(),
            font_style='Body1',
            size_hint_y=None,
            height=40
        )
        content.add_widget(self.status_label)

        scroll = ScrollView(do_scroll_x=False)
        scroll.add_widget(content)
        self.add_widget(scroll)

    def get_card_bg_color(self):
        app = MDApp.get_running_app()
        if app.theme_cls.theme_style == 'Dark':
            return (0.2, 0.2, 0.2, 0.9)
        else:
            return (0.95, 0.95, 0.95, 1)

    def get_text_color(self):
        app = MDApp.get_running_app()
        return (1, 1, 1, 1) if app.theme_cls.theme_style == 'Dark' else (0, 0, 0, 1)

    def get_secondary_text_color(self):
        app = MDApp.get_running_app()
        return (0.8, 0.8, 0.8, 1) if app.theme_cls.theme_style == 'Dark' else (0.3, 0.3, 0.3, 1)

    def get_hint_text_color(self):
        app = MDApp.get_running_app()
        return (0.6, 0.6, 0.6, 1) if app.theme_cls.theme_style == 'Dark' else (0.5, 0.5, 0.5, 1)

    def get_accent_color(self):
        return (0.2, 0.6, 0.9, 1)

    def load_profile(self):
        settings_file = 'settings.json'
        if os.path.exists(settings_file):
            try:
                with open(settings_file, 'r') as f:
                    data = json.load(f)
                    self.name_label.text = data.get('name', 'Иванов Иван')
                    self.class_label.text = data.get('class', '11А')
                    self.card_id_label.text = data.get('card_uid', 'ID карты: не привязана')
            except:
                pass

    def read_nfc(self, instance):
        self.status_label.text = 'Сканирование... Поднесите карту'

        def simulate():
            time.sleep(2)
            now = datetime.now()
            time_str = now.strftime('%d.%m.%Y %H:%M')
            if self.last_event_time is None or self.last_event_time == 'exit':
                event_type = 'Вход'
                self.last_event_time = 'entry'
            else:
                event_type = 'Выход'
                self.last_event_time = 'exit'

            # Добавляем запись в журнал
            app = MDApp.get_running_app()
            if app.log_screen:
                # Вызываем добавление в главном потоке
                from kivy.clock import Clock
                Clock.schedule_once(lambda dt: app.log_screen.add_entry(event_type, time_str))

            self.status_label.text = f'{event_type} зафиксирован в {time_str}'
            if platform == 'android':
                try:
                    vibrator.vibrate(0.1)
                except:
                    pass

        threading.Thread(target=simulate).start()


# -------------------------------------------------------------------
# Экран журнала (вкладка "Журнал")
# -------------------------------------------------------------------
class LogScreen(MDBoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', **kwargs)
        self.build_ui()
        self.load_log()

    def build_ui(self):
        self.toolbar = MDTopAppBar(title='Журнал посещений')
        self.add_widget(self.toolbar)

        self.scroll = ScrollView()
        self.list_view = MDList()
        self.scroll.add_widget(self.list_view)
        self.add_widget(self.scroll)

    def load_log(self):
        log_file = 'log.json'
        if os.path.exists(log_file):
            try:
                with open(log_file, 'r') as f:
                    entries = json.load(f)
                    for entry in reversed(entries):
                        self.add_list_item(entry['type'], entry['time'])
            except:
                pass

    def add_list_item(self, event_type, time_str):
        app = MDApp.get_running_app()
        text_color = (1,1,1,1) if app.theme_cls.theme_style == 'Dark' else (0,0,0,1)
        secondary_color = (0.8,0.8,0.8,1) if app.theme_cls.theme_style == 'Dark' else (0.3,0.3,0.3,1)
        item = TwoLineListItem(
            text=event_type,
            secondary_text=time_str,
            divider='Full',
            theme_text_color='Custom',
            text_color=text_color,
            secondary_text_color=secondary_color
        )
        self.list_view.add_widget(item, index=0)

    def add_entry(self, event_type, time_str):
        """Добавляет запись в список и сохраняет в файл"""
        self.add_list_item(event_type, time_str)
        # Сохраняем в файл
        log_file = 'log.json'
        entries = []
        if os.path.exists(log_file):
            try:
                with open(log_file, 'r') as f:
                    entries = json.load(f)
            except:
                entries = []
        entries.append({'type': event_type, 'time': time_str})
        try:
            with open(log_file, 'w') as f:
                json.dump(entries, f)
        except:
            pass


# -------------------------------------------------------------------
# Экран настроек (вкладка "Настройки")
# -------------------------------------------------------------------
class SettingsScreen(MDBoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', **kwargs)
        self.dialog = None
        self.build_ui()
        self.load_settings()

    def build_ui(self):
        self.toolbar = MDTopAppBar(title='Настройки')
        self.add_widget(self.toolbar)

        content = MDBoxLayout(orientation='vertical', spacing=20, padding=20, adaptive_height=True)

        self.name_field = MDTextField(
            hint_text='ФИО',
            size_hint_x=1
        )
        content.add_widget(self.name_field)

        self.class_field = MDTextField(
            hint_text='Класс',
            size_hint_x=1
        )
        content.add_widget(self.class_field)

        # Переключатель темы
        theme_box = MDBoxLayout(orientation='horizontal', adaptive_height=True, spacing=10)
        theme_box.add_widget(MDLabel(text='Тёмная тема', size_hint_x=0.7))
        self.theme_switch = MDSwitch(size_hint_x=0.3)
        app = MDApp.get_running_app()
        self.theme_switch.active = (app.theme_cls.theme_style == 'Dark')
        self.theme_switch.bind(active=self.on_theme_switch)
        theme_box.add_widget(self.theme_switch)
        content.add_widget(theme_box)

        btn_delete = MDRaisedButton(
            text='Удалить пропуск',
            md_bg_color=(0.8, 0.2, 0.2, 1),
            on_release=self.delete_pass,
            size_hint=(1, None),
            height=48
        )
        content.add_widget(btn_delete)

        btn_save = MDRaisedButton(
            text='Сохранить',
            on_release=self.save_settings,
            size_hint=(1, None),
            height=48
        )
        content.add_widget(btn_save)

        scroll = ScrollView(do_scroll_x=False)
        scroll.add_widget(content)
        self.add_widget(scroll)

    def load_settings(self):
        settings_file = 'settings.json'
        if os.path.exists(settings_file):
            try:
                with open(settings_file, 'r') as f:
                    data = json.load(f)
                    self.name_field.text = data.get('name', 'Иванов Иван')
                    self.class_field.text = data.get('class', '11А')
            except:
                self.name_field.text = 'Иванов Иван'
                self.class_field.text = '11А'
        else:
            self.name_field.text = 'Иванов Иван'
            self.class_field.text = '11А'

    def save_settings(self, *args):
        data = {}
        settings_file = 'settings.json'
        if os.path.exists(settings_file):
            try:
                with open(settings_file, 'r') as f:
                    data = json.load(f)
            except:
                data = {}

        data['name'] = self.name_field.text
        data['class'] = self.class_field.text

        try:
            with open(settings_file, 'w') as f:
                json.dump(data, f)
        except:
            pass

        # Обновляем главный экран
        app = MDApp.get_running_app()
        if app.main_screen:
            app.main_screen.name_label.text = self.name_field.text
            app.main_screen.class_label.text = self.class_field.text

        self.show_dialog('Настройки сохранены')

    def on_theme_switch(self, switch, active):
        app = MDApp.get_running_app()
        app.theme_cls.theme_style = 'Dark' if active else 'Light'

    def delete_pass(self, *args):
        app = MDApp.get_running_app()
        if app.main_screen:
            app.main_screen.card_id_label.text = 'ID карты: не привязана'
            app.main_screen.nfc_data = None
        settings_file = 'settings.json'
        if os.path.exists(settings_file):
            try:
                with open(settings_file, 'r') as f:
                    data = json.load(f)
                if 'card_uid' in data:
                    del data['card_uid']
                    with open(settings_file, 'w') as f:
                        json.dump(data, f)
            except:
                pass
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
# Корневое приложение с нижней навигацией
# -------------------------------------------------------------------
class SchoolPassApp(MDApp):
    def build(self):
        self.title = 'School Pass'
        self.theme_cls.theme_style = 'Dark'
        self.theme_cls.primary_palette = 'Blue'
        self.theme_cls.accent_palette = 'LightBlue'
        Window.clearcolor = (0.12, 0.12, 0.12, 1)

        # Создаём экраны и сохраняем ссылки
        self.main_screen = MainScreen()
        self.log_screen = LogScreen()
        self.settings_screen = SettingsScreen()

        # Нижняя навигация
        self.bottom_nav = MDBottomNavigation(
            panel_color=self.theme_cls.primary_color,
            selected_color_background=self.theme_cls.primary_light,
            text_color_active=(1, 1, 1, 1),
        )

        # Вкладка "Главная"
        main_item = MDBottomNavigationItem(
            name='main',
            text='Главная',
            icon='home'
        )
        main_item.add_widget(self.main_screen)
        self.bottom_nav.add_widget(main_item)

        # Вкладка "Журнал"
        log_item = MDBottomNavigationItem(
            name='log',
            text='Журнал',
            icon='clipboard-list'
        )
        log_item.add_widget(self.log_screen)
        self.bottom_nav.add_widget(log_item)

        # Вкладка "Настройки"
        settings_item = MDBottomNavigationItem(
            name='settings',
            text='Настройки',
            icon='cog'
        )
        settings_item.add_widget(self.settings_screen)
        self.bottom_nav.add_widget(settings_item)

        return self.bottom_nav


if __name__ == '__main__':
    SchoolPassApp().run()