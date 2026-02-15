"""
School Pass NFC — абсолютно стабильная версия с журналом и настройками
"""

import json
import os
import threading
import time
from datetime import datetime

from kivy.core.window import Window
from kivy.uix.screenmanager import Screen
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
# Вспомогательные функции для работы с файлами
# -------------------------------------------------------------------
def load_settings():
    """Загружает настройки из settings.json, возвращает словарь."""
    default = {'name': 'Иванов Иван', 'class': '11А'}
    if not os.path.exists('settings.json'):
        return default
    try:
        with open('settings.json', 'r') as f:
            data = json.load(f)
            return {**default, **data}
    except:
        return default


def save_settings(data):
    """Сохраняет настройки в settings.json."""
    try:
        with open('settings.json', 'w') as f:
            json.dump(data, f)
    except:
        pass


def load_log():
    """Загружает записи журнала из log.json, возвращает список."""
    if not os.path.exists('log.json'):
        return []
    try:
        with open('log.json', 'r') as f:
            return json.load(f)
    except:
        return []


def save_log_entry(entry):
    """Добавляет одну запись в журнал и сохраняет."""
    entries = load_log()
    entries.append(entry)
    try:
        with open('log.json', 'w') as f:
            json.dump(entries, f)
    except:
        pass


# -------------------------------------------------------------------
# Главный экран (вкладка "Главная")
# -------------------------------------------------------------------
class MainScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.dialog = None
        self.nfc_data = None
        self.last_event_time = None  # None, 'entry' или 'exit'
        self.build_ui()
        self.update_profile()

    def build_ui(self):
        layout = MDBoxLayout(orientation='vertical', spacing=0, padding=0)

        # Верхний toolbar
        self.toolbar = MDTopAppBar(title='School Pass')
        layout.add_widget(self.toolbar)

        # Основной контент
        content = MDBoxLayout(orientation='vertical', spacing=20, padding=20, adaptive_height=True)

        # Карточка профиля
        self.card = MDCard(
            orientation='vertical',
            padding=20,
            spacing=10,
            size_hint=(1, None),
            height=200,
            elevation=6,
            radius=15,
            md_bg_color=self.get_card_bg_color()
        )
        self.update_card_colors()

        from kivymd.uix.label import MDIcon
        self.avatar = MDIcon(
            icon='account-circle',
            size_hint=(None, None),
            size=(80, 80),
            halign='center',
            valign='middle'
        )
        self.avatar.pos_hint = {'center_x': 0.5}
        self.card.add_widget(self.avatar)

        self.name_label = MDLabel(
            text='',
            halign='center',
            font_style='H5',
            size_hint_y=None,
            height=40
        )
        self.card.add_widget(self.name_label)

        self.class_label = MDLabel(
            text='',
            halign='center',
            font_style='Subtitle1',
            size_hint_y=None,
            height=30
        )
        self.card.add_widget(self.class_label)

        self.card_id_label = MDLabel(
            text='',
            halign='center',
            font_style='Caption',
            size_hint_y=None,
            height=30
        )
        self.card.add_widget(self.card_id_label)

        content.add_widget(self.card)

        # Кнопка NFC
        self.nfc_button = MDRaisedButton(
            text='СЧИТАТЬ ПРОПУСК',
            size_hint=(1, None),
            height=50,
            on_release=self.read_nfc
        )
        content.add_widget(self.nfc_button)

        # Статус
        self.status_label = MDLabel(
            text='Нажмите кнопку и поднесите карту к NFC',
            halign='center',
            font_style='Body1',
            size_hint_y=None,
            height=40
        )
        content.add_widget(self.status_label)

        scroll = ScrollView(do_scroll_x=False)
        scroll.add_widget(content)
        layout.add_widget(scroll)

        self.add_widget(layout)

    def get_card_bg_color(self):
        app = MDApp.get_running_app()
        if app.theme_cls.theme_style == 'Dark':
            return (0.2, 0.2, 0.2, 0.9)
        else:
            return (0.95, 0.95, 0.95, 1)

    def update_card_colors(self):
        """Обновляет цвета виджетов в соответствии с текущей темой."""
        app = MDApp.get_running_app()
        is_dark = app.theme_cls.theme_style == 'Dark'
        self.card.md_bg_color = self.get_card_bg_color()
        self.avatar.text_color = app.theme_cls.primary_color
        self.name_label.theme_text_color = 'Custom'
        self.name_label.text_color = (1, 1, 1, 1) if is_dark else (0, 0, 0, 1)
        self.class_label.theme_text_color = 'Custom'
        self.class_label.text_color = (0.8, 0.8, 0.8, 1) if is_dark else (0.3, 0.3, 0.3, 1)
        self.card_id_label.theme_text_color = 'Custom'
        self.card_id_label.text_color = (0.6, 0.6, 0.6, 1) if is_dark else (0.5, 0.5, 0.5, 1)
        self.status_label.theme_text_color = 'Custom'
        self.status_label.text_color = (0.8, 0.8, 0.8, 1) if is_dark else (0.3, 0.3, 0.3, 1)
        self.nfc_button.md_bg_color = app.theme_cls.primary_color

    def update_profile(self):
        """Обновляет текст из настроек."""
        settings = load_settings()
        self.name_label.text = settings.get('name', 'Иванов Иван')
        self.class_label.text = settings.get('class', '11А')
        self.card_id_label.text = settings.get('card_uid', 'ID карты: не привязана')

    def on_enter(self, *args):
        """Вызывается при входе на экран — обновляем цвета и профиль."""
        self.update_card_colors()
        self.update_profile()

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

            # Сохраняем запись в журнал
            save_log_entry({'type': event_type, 'time': time_str})

            self.status_label.text = f'{event_type} зафиксирован в {time_str}'
            if platform == 'android':
                try:
                    vibrator.vibrate(0.1)
                except:
                    pass

        threading.Thread(target=simulate).start()

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
# Экран журнала (вкладка "Журнал")
# -------------------------------------------------------------------
class LogScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.build_ui()

    def build_ui(self):
        layout = MDBoxLayout(orientation='vertical')
        self.toolbar = MDTopAppBar(title='Журнал посещений')
        layout.add_widget(self.toolbar)

        self.scroll = ScrollView()
        self.list_view = MDList()
        self.scroll.add_widget(self.list_view)
        layout.add_widget(self.scroll)

        self.add_widget(layout)

    def on_enter(self, *args):
        """При входе на экран перестраиваем список из файла."""
        self.refresh()

    def refresh(self):
        """Очищает список и загружает записи из файла."""
        self.list_view.clear_widgets()
        entries = load_log()
        app = MDApp.get_running_app()
        is_dark = app.theme_cls.theme_style == 'Dark'
        for entry in reversed(entries):
            item = TwoLineListItem(
                text=entry['type'],
                secondary_text=entry['time'],
                divider='Full',
                theme_text_color='Custom',
                text_color=(1, 1, 1, 1) if is_dark else (0, 0, 0, 1),
                secondary_text_color=(0.8, 0.8, 0.8, 1) if is_dark else (0.3, 0.3, 0.3, 1)
            )
            self.list_view.add_widget(item)


# -------------------------------------------------------------------
# Экран настроек (вкладка "Настройки")
# -------------------------------------------------------------------
class SettingsScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.dialog = None
        self.build_ui()
        self.load_settings()

    def build_ui(self):
        layout = MDBoxLayout(orientation='vertical')
        self.toolbar = MDTopAppBar(title='Настройки')
        layout.add_widget(self.toolbar)

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
        layout.add_widget(scroll)

        self.add_widget(layout)

    def load_settings(self):
        settings = load_settings()
        self.name_field.text = settings.get('name', 'Иванов Иван')
        self.class_field.text = settings.get('class', '11А')

    def save_settings(self, *args):
        settings = load_settings()
        settings['name'] = self.name_field.text
        settings['class'] = self.class_field.text
        save_settings(settings)
        self.show_dialog('Настройки сохранены')

    def on_theme_switch(self, switch, active):
        app = MDApp.get_running_app()
        app.theme_cls.theme_style = 'Dark' if active else 'Light'
        # Принудительно обновим цвета на главном экране и журнале при следующем входе
        # но они обновятся сами в on_enter

    def delete_pass(self, *args):
        settings = load_settings()
        if 'card_uid' in settings:
            del settings['card_uid']
            save_settings(settings)
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
        self.theme_cls.theme_style = 'Dark'  # начальная тема
        self.theme_cls.primary_palette = 'Blue'
        self.theme_cls.accent_palette = 'LightBlue'
        Window.clearcolor = (0.12, 0.12, 0.12, 1)

        # Нижняя навигация
        bottom_nav = MDBottomNavigation(
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
        main_item.add_widget(MainScreen(name='main'))
        bottom_nav.add_widget(main_item)

        # Вкладка "Журнал"
        log_item = MDBottomNavigationItem(
            name='log',
            text='Журнал',
            icon='clipboard-list'
        )
        log_item.add_widget(LogScreen(name='log'))
        bottom_nav.add_widget(log_item)

        # Вкладка "Настройки"
        settings_item = MDBottomNavigationItem(
            name='settings',
            text='Настройки',
            icon='cog'
        )
        settings_item.add_widget(SettingsScreen(name='settings'))
        bottom_nav.add_widget(settings_item)

        return bottom_nav


if __name__ == '__main__':
    SchoolPassApp().run()