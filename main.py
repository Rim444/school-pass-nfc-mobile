"""
School Pass NFC — Финальная версия с дизайном в стиле Сферум
- Главный экран: карточка профиля, календарь, кнопка "Включить пропуск" (холостая)
- Экран настроек: ввод ФИО, учебного заведения, выбор должности (ученик/сотрудник) через радио-кнопки, кнопка привязки пропуска
- Журнал посещений
- Тёмная тема, синие акценты, иконки как в референсах
"""

import json
import os
import threading
import time
import sys
import traceback
from datetime import datetime, date, timedelta
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.uix.screenmanager import Screen
from kivy.utils import platform
from kivymd.app import MDApp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDRaisedButton, MDIconButton
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.dialog import MDDialog
from kivymd.uix.list import MDList, TwoLineListItem
from kivy.uix.scrollview import ScrollView
from kivymd.uix.textfield import MDTextField
from kivymd.uix.selectioncontrol import MDSwitch
from kivymd.uix.radio import MDRadio                      # <-- ИСПРАВЛЕНО
from kivymd.uix.bottomnavigation import MDBottomNavigation, MDBottomNavigationItem
from kivymd.uix.toolbar import MDTopAppBar
from plyer import vibrator

# ================================================================
# ГЛОБАЛЬНЫЙ ПЕРЕХВАТЧИК НЕОБРАБОТАННЫХ ИСКЛЮЧЕНИЙ (ДЛЯ ANDROID)
# ================================================================
def global_excepthook(exctype, value, tb):
    try:
        if platform == 'android':
            from android.storage import app_storage_path
            log_dir = app_storage_path()
        else:
            log_dir = '.'
        log_path = os.path.join(log_dir, 'crash_log.txt')
        with open(log_path, 'a') as f:
            f.write('\n=== CRASH AT {} ===\n'.format(datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
            traceback.print_exception(exctype, value, tb, file=f)
            f.write('\n')
    except:
        pass
    sys.__excepthook__(exctype, value, tb)

if platform == 'android':
    sys.excepthook = global_excepthook
# ================================================================

if platform != 'android':
    Window.size = (400, 700)
Window.softinput_mode = 'pan'

# -------------------------------------------------------------------
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ДЛЯ КАЛЕНДАРЯ
# -------------------------------------------------------------------
def get_week_dates():
    today = date.today()
    start = today - timedelta(days=today.weekday())  # понедельник
    return [(start + timedelta(days=i)) for i in range(7)]

week_days_ru = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']

# -------------------------------------------------------------------
# ГЛАВНЫЙ ЭКРАН (вкладка "Главная")
# -------------------------------------------------------------------
class MainScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.dialog = None
        self.pass_enabled = False
        self.build_ui()
        self.load_profile()

    def build_ui(self):
        layout = MDBoxLayout(orientation='vertical', spacing=0, padding=0)

        content = MDBoxLayout(orientation='vertical', spacing=10, padding=15, adaptive_height=True)

        # --- Карточка профиля ---
        card = MDCard(
            orientation='vertical',
            padding=20,
            spacing=5,
            size_hint=(1, None),
            height=160,
            elevation=4,
            radius=15,
            md_bg_color=self.get_card_bg_color()
        )

        from kivymd.uix.label import MDIcon
        avatar = MDIcon(
            icon='account-circle',
            size_hint=(None, None),
            size=(70, 70),
            halign='center',
            valign='middle',
            theme_text_color='Custom',
            text_color=self.get_accent_color()
        )
        avatar.pos_hint = {'center_x': 0.5}
        card.add_widget(avatar)

        self.name_label = MDLabel(
            text='Питирим Батурин',
            halign='center',
            theme_text_color='Custom',
            text_color=self.get_text_color(),
            font_style='H6',
            size_hint_y=None,
            height=40
        )
        card.add_widget(self.name_label)

        self.role_label = MDLabel(
            text='Ученик',
            halign='center',
            theme_text_color='Custom',
            text_color=self.get_secondary_text_color(),
            font_style='Subtitle2',
            size_hint_y=None,
            height=30
        )
        card.add_widget(self.role_label)

        content.add_widget(card)

        # --- Календарная строка ---
        dates = get_week_dates()
        days_layout = MDBoxLayout(orientation='horizontal', spacing=5, size_hint_y=None, height=30)
        for day in week_days_ru:
            days_layout.add_widget(MDLabel(
                text=day,
                halign='center',
                theme_text_color='Custom',
                text_color=self.get_secondary_text_color(),
                font_style='Caption'
            ))
        content.add_widget(days_layout)

        nums_layout = MDBoxLayout(orientation='horizontal', spacing=5, size_hint_y=None, height=40)
        for d in dates:
            color = self.get_accent_color() if d == date.today() else self.get_text_color()
            nums_layout.add_widget(MDLabel(
                text=str(d.day),
                halign='center',
                theme_text_color='Custom',
                text_color=color,
                font_style='Body1'
            ))
        content.add_widget(nums_layout)

        # --- Библиотека ---
        library_layout = MDBoxLayout(orientation='horizontal', adaptive_height=True, spacing=10)
        library_layout.add_widget(MDLabel(
            text='БИБЛИОТЕКА ЭЛЕКТРОННЫХ МАТЕРИАЛОВ',
            halign='left',
            theme_text_color='Custom',
            text_color=self.get_secondary_text_color(),
            font_style='Caption',
            size_hint_x=0.7
        ))
        library_layout.add_widget(MDRaisedButton(
            text='ПОДРОБНЕЕ',
            size_hint_x=0.3,
            height=30,
            md_bg_color=self.get_accent_color(),
            on_release=lambda x: self.show_dialog('Подробнее', 'Раздел в разработке')
        ))
        content.add_widget(library_layout)

        # --- Кнопка включения пропуска ---
        self.pass_button = MDRaisedButton(
            text='Включить пропуск',
            size_hint=(1, None),
            height=48,
            md_bg_color=self.get_accent_color(),
            on_release=self.toggle_pass
        )
        content.add_widget(self.pass_button)

        # --- Сообщение об отсутствии уроков ---
        content.add_widget(MDLabel(
            text='Уроков и мероприятий нет',
            halign='center',
            theme_text_color='Custom',
            text_color=self.get_secondary_text_color(),
            font_style='Body1',
            size_hint_y=None,
            height=40
        ))
        content.add_widget(MDLabel(
            text='Уроков и мероприятий на этот день не найдено',
            halign='center',
            theme_text_color='Custom',
            text_color=self.get_hint_text_color(),
            font_style='Caption',
            size_hint_y=None,
            height=30
        ))

        scroll = ScrollView(do_scroll_x=False)
        scroll.add_widget(content)
        layout.add_widget(scroll)

        self.add_widget(layout)

    def get_card_bg_color(self):
        app = MDApp.get_running_app()
        if app.theme_cls.theme_style == 'Dark':
            return (0.15, 0.15, 0.15, 0.95)
        else:
            return (0.95, 0.95, 0.95, 1)

    def get_text_color(self):
        app = MDApp.get_running_app()
        return (1, 1, 1, 1) if app.theme_cls.theme_style == 'Dark' else (0, 0, 0, 1)

    def get_secondary_text_color(self):
        app = MDApp.get_running_app()
        return (0.7, 0.7, 0.7, 1) if app.theme_cls.theme_style == 'Dark' else (0.3, 0.3, 0.3, 1)

    def get_hint_text_color(self):
        app = MDApp.get_running_app()
        return (0.5, 0.5, 0.5, 1) if app.theme_cls.theme_style == 'Dark' else (0.5, 0.5, 0.5, 1)

    def get_accent_color(self):
        return (0.2, 0.6, 0.9, 1)

    def load_profile(self):
        try:
            if os.path.exists('settings.json'):
                with open('settings.json', 'r') as f:
                    data = json.load(f)
                    self.name_label.text = data.get('name', 'Питирим Батурин')
                    self.role_label.text = data.get('role', 'Ученик')
        except:
            pass

    def toggle_pass(self, instance):
        self.pass_enabled = not self.pass_enabled
        if self.pass_enabled:
            self.pass_button.text = 'Выключить пропуск'
            self.pass_button.md_bg_color = (0.9, 0.2, 0.2, 1)
        else:
            self.pass_button.text = 'Включить пропуск'
            self.pass_button.md_bg_color = self.get_accent_color()
        self.show_dialog('Пропуск', 'Включён' if self.pass_enabled else 'Выключен')

    def show_dialog(self, title, text):
        if not self.dialog:
            self.dialog = MDDialog(
                title=title,
                text=text,
                buttons=[MDRaisedButton(text='OK', on_release=lambda x: self.dialog.dismiss())]
            )
        else:
            self.dialog.title = title
            self.dialog.text = text
        self.dialog.open()


# -------------------------------------------------------------------
# ЭКРАН ЖУРНАЛА
# -------------------------------------------------------------------
class LogScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.build_ui()
        self.load_log()

    def build_ui(self):
        layout = MDBoxLayout(orientation='vertical')
        self.toolbar = MDTopAppBar(title='Журнал посещений')
        layout.add_widget(self.toolbar)
        self.scroll = ScrollView()
        self.list_view = MDList()
        self.scroll.add_widget(self.list_view)
        layout.add_widget(self.scroll)
        self.add_widget(layout)

    def load_log(self):
        try:
            if os.path.exists('log.json'):
                with open('log.json', 'r') as f:
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
        self.add_list_item(event_type, time_str)
        try:
            log_file = 'log.json'
            entries = []
            if os.path.exists(log_file):
                with open(log_file, 'r') as f:
                    entries = json.load(f)
            entries.append({'type': event_type, 'time': time_str})
            with open(log_file, 'w') as f:
                json.dump(entries, f)
        except Exception as e:
            if platform == 'android':
                try:
                    from android.storage import app_storage_path
                    log_dir = app_storage_path()
                    log_path = os.path.join(log_dir, 'crash_log.txt')
                    with open(log_path, 'a') as f:
                        f.write(f'\n--- Ошибка записи журнала: {e}\n')
                except:
                    pass


# -------------------------------------------------------------------
# ЭКРАН НАСТРОЕК
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

        content = MDBoxLayout(orientation='vertical', spacing=15, padding=20, adaptive_height=True)

        self.name_field = MDTextField(
            hint_text='ФИО',
            size_hint_x=1
        )
        content.add_widget(self.name_field)

        self.school_field = MDTextField(
            hint_text='Учебное заведение',
            size_hint_x=1
        )
        content.add_widget(self.school_field)

        # Выбор должности
        role_label = MDLabel(
            text='Должность:',
            theme_text_color='Custom',
            text_color=self.get_text_color(),
            size_hint_y=None,
            height=30
        )
        content.add_widget(role_label)

        role_box = MDBoxLayout(orientation='horizontal', adaptive_height=True, spacing=10)
        self.student_radio = MDRadio(group='role')
        student_label = MDLabel(text='Ученик', size_hint_x=0.3)
        self.teacher_radio = MDRadio(group='role')
        teacher_label = MDLabel(text='Сотрудник', size_hint_x=0.3)

        role_box.add_widget(self.student_radio)
        role_box.add_widget(student_label)
        role_box.add_widget(self.teacher_radio)
        role_box.add_widget(teacher_label)
        content.add_widget(role_box)

        # Кнопка привязки пропуска
        btn_bind = MDRaisedButton(
            text='Считать пропуск',
            size_hint=(1, None),
            height=48,
            md_bg_color=self.get_accent_color(),
            on_release=self.bind_pass
        )
        content.add_widget(btn_bind)

        self.pass_status = MDLabel(
            text='Пропуск: не привязан',
            halign='left',
            theme_text_color='Custom',
            text_color=self.get_secondary_text_color(),
            font_style='Caption',
            size_hint_y=None,
            height=30
        )
        content.add_widget(self.pass_status)

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

    def get_text_color(self):
        app = MDApp.get_running_app()
        return (1, 1, 1, 1) if app.theme_cls.theme_style == 'Dark' else (0, 0, 0, 1)

    def get_secondary_text_color(self):
        app = MDApp.get_running_app()
        return (0.7, 0.7, 0.7, 1) if app.theme_cls.theme_style == 'Dark' else (0.3, 0.3, 0.3, 1)

    def get_accent_color(self):
        return (0.2, 0.6, 0.9, 1)

    def load_settings(self):
        try:
            if os.path.exists('settings.json'):
                with open('settings.json', 'r') as f:
                    data = json.load(f)
                    self.name_field.text = data.get('name', 'Питирим Батурин')
                    self.school_field.text = data.get('school', '')
                    role = data.get('role', 'Ученик')
                    if role == 'Ученик':
                        self.student_radio.active = True
                        self.teacher_radio.active = False
                    else:
                        self.student_radio.active = False
                        self.teacher_radio.active = True
                    if 'card_uid' in data:
                        self.pass_status.text = f"Пропуск: привязан ({data['card_uid']})"
                    else:
                        self.pass_status.text = 'Пропуск: не привязан'
        except:
            self.name_field.text = 'Питирим Батурин'
            self.school_field.text = ''
            self.student_radio.active = True

    def save_settings(self, *args):
        try:
            data = {}
            if os.path.exists('settings.json'):
                with open('settings.json', 'r') as f:
                    data = json.load(f)

            data['name'] = self.name_field.text
            data['school'] = self.school_field.text
            data['role'] = 'Ученик' if self.student_radio.active else 'Сотрудник'

            with open('settings.json', 'w') as f:
                json.dump(data, f)

            app = MDApp.get_running_app()
            if app.main_screen:
                app.main_screen.name_label.text = self.name_field.text
                app.main_screen.role_label.text = data['role']

            self.show_dialog('Настройки сохранены')
        except Exception as e:
            self.show_dialog(f'Ошибка: {e}')

    def bind_pass(self, *args):
        def simulate():
            time.sleep(2)
            uid = '04:5A:6B:7C:8D:9E'
            try:
                with open('settings.json', 'r') as f:
                    data = json.load(f)
            except:
                data = {}
            data['card_uid'] = uid
            with open('settings.json', 'w') as f:
                json.dump(data, f)

            Clock.schedule_once(lambda dt: self.update_pass_status(uid))
            if platform == 'android':
                try:
                    vibrator.vibrate(0.1)
                except:
                    pass

        self.show_dialog('Сканирование', 'Поднесите карту к NFC...')
        threading.Thread(target=simulate).start()

    def update_pass_status(self, uid):
        self.pass_status.text = f"Пропуск: привязан ({uid})"
        self.show_dialog('Успех', 'Пропуск успешно привязан!')

    def delete_pass(self, *args):
        try:
            if os.path.exists('settings.json'):
                with open('settings.json', 'r') as f:
                    data = json.load(f)
                if 'card_uid' in data:
                    del data['card_uid']
                    with open('settings.json', 'w') as f:
                        json.dump(data, f)
            self.pass_status.text = 'Пропуск: не привязан'
            self.show_dialog('Пропуск удалён')
        except Exception as e:
            self.show_dialog(f'Ошибка: {e}')

    def on_theme_switch(self, switch, active):
        app = MDApp.get_running_app()
        app.theme_cls.theme_style = 'Dark' if active else 'Light'

    def show_dialog(self, title, text):
        if not self.dialog:
            self.dialog = MDDialog(
                title=title,
                text=text,
                buttons=[MDRaisedButton(text='OK', on_release=lambda x: self.dialog.dismiss())]
            )
        else:
            self.dialog.title = title
            self.dialog.text = text
        self.dialog.open()


# -------------------------------------------------------------------
# КОРНЕВОЕ ПРИЛОЖЕНИЕ
# -------------------------------------------------------------------
class SchoolPassApp(MDApp):
    def build(self):
        self.title = 'School Pass'
        self.theme_cls.theme_style = 'Dark'
        self.theme_cls.primary_palette = 'Blue'
        self.theme_cls.accent_palette = 'LightBlue'
        Window.clearcolor = (0.12, 0.12, 0.12, 1)

        self.main_screen = MainScreen(name='main')
        self.log_screen = LogScreen(name='log')
        self.settings_screen = SettingsScreen(name='settings')

        self.bottom_nav = MDBottomNavigation(
            panel_color=self.theme_cls.primary_color,
            selected_color_background=self.theme_cls.primary_light,
            text_color_active=(1, 1, 1, 1),
        )

        main_item = MDBottomNavigationItem(
            name='main',
            text='Главная',
            icon='home'
        )
        main_item.add_widget(self.main_screen)
        self.bottom_nav.add_widget(main_item)

        log_item = MDBottomNavigationItem(
            name='log',
            text='Журнал',
            icon='clipboard-list'
        )
        log_item.add_widget(self.log_screen)
        self.bottom_nav.add_widget(log_item)

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