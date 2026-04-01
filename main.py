"""
School Pass NFC — Версия с ручным добавлением расписания
"""

import json
import os
import threading
import time
import sys
import traceback
from datetime import datetime, date, timedelta
from functools import partial
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.uix.screenmanager import Screen
from kivy.utils import platform
from kivymd.app import MDApp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDRaisedButton, MDIconButton, MDFlatButton
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.dialog import MDDialog
from kivymd.uix.list import MDList, TwoLineListItem, OneLineListItem
from kivy.uix.scrollview import ScrollView
from kivymd.uix.textfield import MDTextField
from kivymd.uix.selectioncontrol import MDSwitch, MDCheckbox
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
# ФИКСИРОВАННОЕ РАСПИСАНИЕ УРОКОВ ПО НОМЕРАМ
# -------------------------------------------------------------------
LESSON_TIMES = {
    1: '8:30 – 9:15',
    2: '9:25 – 10:10',
    3: '10:20 – 11:05',
    4: '11:25 – 12:10',
    5: '12:30 – 13:15',
    6: '13:25 – 14:10',
    7: '14:30 – 15:15'
}

# -------------------------------------------------------------------
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ДЛЯ КАЛЕНДАРЯ
# -------------------------------------------------------------------
def get_week_dates():
    today = date.today()
    start = today - timedelta(days=today.weekday())
    return [(start + timedelta(days=i)) for i in range(7)]

week_days_ru = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']

# -------------------------------------------------------------------
# ГЛАВНЫЙ ЭКРАН (вкладка "Главная")
# -------------------------------------------------------------------
class MainScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.dialog = None
        self.add_event_dialog = None
        self.lesson_spinner = None
        self.subject_field = None
        self.pass_enabled = False
        self.last_event_time = None
        self.schedule_events = []
        self.build_ui()
        self.load_schedule()

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

        # --- Кнопка включения пропуска ---
        self.pass_button = MDRaisedButton(
            text='Включить пропуск',
            size_hint=(1, None),
            height=48,
            md_bg_color=self.get_accent_color(),
            on_release=self.toggle_pass
        )
        content.add_widget(self.pass_button)

        # --- Кнопка добавления события ---
        add_event_btn = MDRaisedButton(
            text='Добавить событие',
            size_hint=(1, None),
            height=48,
            md_bg_color=self.get_accent_color(),
            on_release=self.show_add_event_dialog
        )
        content.add_widget(add_event_btn)

        # --- Расписание ---
        schedule_label = MDLabel(
            text='Моё расписание:',
            halign='left',
            theme_text_color='Custom',
            text_color=self.get_secondary_text_color(),
            font_style='Subtitle2',
            size_hint_y=None,
            height=30
        )
        content.add_widget(schedule_label)

        # Контейнер для событий
        self.schedule_container = MDBoxLayout(
            orientation='vertical',
            spacing=5,
            size_hint_y=None
        )
        self.schedule_container.bind(minimum_height=self.schedule_container.setter('height'))

        self.schedule_scroll = ScrollView(size_hint=(1, 0.5))
        self.schedule_scroll.add_widget(self.schedule_container)
        content.add_widget(self.schedule_scroll)

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
        except Exception as e:
            print(f"Ошибка загрузки профиля: {e}")

    def load_schedule(self):
        """Загружает расписание из schedule.json"""
        try:
            if os.path.exists('schedule.json'):
                with open('schedule.json', 'r') as f:
                    self.schedule_events = json.load(f)
            else:
                self.schedule_events = []
            self.update_schedule_display()
        except Exception as e:
            print(f"Ошибка загрузки расписания: {e}")
            self.schedule_events = []

    def save_schedule(self):
        """Сохраняет расписание в schedule.json"""
        try:
            with open('schedule.json', 'w') as f:
                json.dump(self.schedule_events, f)
        except Exception as e:
            print(f"Ошибка сохранения расписания: {e}")

    def update_schedule_display(self):
        """Обновляет отображение расписания на экране"""
        self.schedule_container.clear_widgets()
        if not self.schedule_events:
            item = OneLineListItem(
                text='Нет добавленных событий',
                divider='Full',
                theme_text_color='Custom',
                text_color=self.get_hint_text_color()
            )
            self.schedule_container.add_widget(item)
        else:
            # Сортируем по номеру урока
            sorted_events = sorted(self.schedule_events, key=lambda x: x['lesson_num'])
            for event in sorted_events:
                lesson_num = event['lesson_num']
                subject = event['subject']
                time_range = LESSON_TIMES.get(lesson_num, '')
                # Карточка события
                card = MDCard(
                    orientation='vertical',
                    padding=10,
                    spacing=5,
                    size_hint=(1, None),
                    height=80,
                    elevation=2,
                    radius=10,
                    md_bg_color=self.get_card_bg_color()
                )
                # Верхняя строка: номер урока и время
                header = MDBoxLayout(orientation='horizontal', adaptive_height=True)
                header.add_widget(MDLabel(
                    text=f'{lesson_num} урок',
                    font_style='Subtitle1',
                    theme_text_color='Custom',
                    text_color=self.get_text_color(),
                    size_hint_x=0.5
                ))
                header.add_widget(MDLabel(
                    text=time_range,
                    font_style='Caption',
                    theme_text_color='Custom',
                    text_color=self.get_secondary_text_color(),
                    halign='right',
                    size_hint_x=0.5
                ))
                card.add_widget(header)
                # Название предмета
                card.add_widget(MDLabel(
                    text=subject,
                    font_style='Body1',
                    theme_text_color='Custom',
                    text_color=self.get_accent_color()
                ))
                # Кнопка удаления
                delete_btn = MDIconButton(
                    icon='delete',
                    size_hint=(1, None),
                    height=30,
                    on_release=partial(self.delete_event, event)
                )
                card.add_widget(delete_btn)
                self.schedule_container.add_widget(card)

        Clock.schedule_once(lambda dt: self.schedule_container.do_layout(), 0)

    def delete_event(self, event, *args):
        """Удаляет событие из расписания"""
        if event in self.schedule_events:
            self.schedule_events.remove(event)
            self.save_schedule()
            self.update_schedule_display()
            self.show_dialog('Удалено', 'Событие удалено из расписания')

    def show_add_event_dialog(self, instance):
        """Показывает диалог добавления события"""
        if not self.add_event_dialog:
            # Создаём поля ввода
            self.lesson_spinner = MDTextField(
                hint_text='Номер урока (1-7)',
                input_filter='int',
                size_hint_x=1
            )
            self.subject_field = MDTextField(
                hint_text='Название предмета',
                size_hint_x=1
            )
            # Контейнер для полей
            content = MDBoxLayout(
                orientation='vertical',
                spacing=10,
                padding=10,
                size_hint_y=None,
                height=150
            )
            content.add_widget(self.lesson_spinner)
            content.add_widget(self.subject_field)

            self.add_event_dialog = MDDialog(
                title='Добавить событие',
                type='custom',
                content_cl=content,
                buttons=[
                    MDFlatButton(
                        text='ОТМЕНА',
                        on_release=lambda x: self.add_event_dialog.dismiss()
                    ),
                    MDRaisedButton(
                        text='ДОБАВИТЬ',
                        on_release=self.add_event
                    )
                ]
            )
        else:
            # Очищаем поля перед повторным открытием
            self.lesson_spinner.text = ''
            self.subject_field.text = ''
        self.add_event_dialog.open()

    def add_event(self, instance):
        """Добавляет новое событие"""
        try:
            lesson_num = int(self.lesson_spinner.text)
            if lesson_num < 1 or lesson_num > 7:
                self.show_dialog('Ошибка', 'Номер урока должен быть от 1 до 7')
                return
            subject = self.subject_field.text.strip()
            if not subject:
                self.show_dialog('Ошибка', 'Введите название предмета')
                return

            # Проверяем, нет ли уже такого урока
            for event in self.schedule_events:
                if event['lesson_num'] == lesson_num:
                    self.show_dialog('Ошибка', f'Урок №{lesson_num} уже добавлен')
                    return

            self.schedule_events.append({
                'lesson_num': lesson_num,
                'subject': subject
            })
            self.save_schedule()
            self.update_schedule_display()
            self.add_event_dialog.dismiss()
            self.show_dialog('Успех', f'Урок {lesson_num} добавлен')
        except ValueError:
            self.show_dialog('Ошибка', 'Введите корректный номер урока')

    def toggle_pass(self, instance):
        now = datetime.now()
        time_str = now.strftime('%d.%m.%Y %H:%M')
        if self.last_event_time is None or self.last_event_time == 'exit':
            event_type = 'Вход'
            self.last_event_time = 'entry'
        else:
            event_type = 'Выход'
            self.last_event_time = 'exit'

        app = MDApp.get_running_app()
        if app.log_screen:
            app.log_screen.add_entry(event_type, time_str)

        self.pass_enabled = not self.pass_enabled
        if self.pass_enabled:
            self.pass_button.text = 'Выключить пропуск'
            self.pass_button.md_bg_color = (0.9, 0.2, 0.2, 1)
        else:
            self.pass_button.text = 'Включить пропуск'
            self.pass_button.md_bg_color = self.get_accent_color()

        self.show_dialog('Пропуск', f'{event_type} зафиксирован в {time_str}')

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
        self.nfc_adapter = None
        self.nfc_pending_intent = None
        self.build_ui()
        self.load_settings()
        if platform == 'android':
            self.init_nfc()

    def init_nfc(self):
        try:
            from jnius import autoclass
            self.PythonActivity = autoclass('org.kivy.android.PythonActivity')
            self.NfcAdapter = autoclass('android.nfc.NfcAdapter')
            self.PendingIntent = autoclass('android.app.PendingIntent')
            self.Intent = autoclass('android.content.Intent')
            self.activity = self.PythonActivity.mActivity
            self.nfc_adapter = self.NfcAdapter.getDefaultAdapter(self.activity)
        except Exception as e:
            print(f'NFC init error: {e}')
            self.nfc_adapter = None

    def enable_nfc_foreground(self):
        if self.nfc_adapter is None:
            return
        try:
            intent = self.Intent(self.activity, self.activity.getClass())
            intent.addFlags(self.Intent.FLAG_ACTIVITY_SINGLE_TOP)
            self.nfc_pending_intent = self.PendingIntent.getActivity(
                self.activity, 0, intent,
                self.PendingIntent.FLAG_UPDATE_CURRENT | self.PendingIntent.FLAG_IMMUTABLE
            )
            self.nfc_adapter.enableForegroundDispatch(self.activity, self.nfc_pending_intent, None, None)
        except Exception as e:
            print(f'Enable foreground error: {e}')

    def disable_nfc_foreground(self):
        if self.nfc_adapter and hasattr(self, 'nfc_pending_intent'):
            try:
                self.nfc_adapter.disableForegroundDispatch(self.activity)
            except Exception as e:
                print(f'Disable foreground error: {e}')

    def build_ui(self):
        layout = MDBoxLayout(orientation='vertical')
        self.toolbar = MDTopAppBar(title='Настройки')
        layout.add_widget(self.toolbar)

        content = MDBoxLayout(orientation='vertical', spacing=15, padding=20, adaptive_height=True)

        self.name_field = MDTextField(hint_text='ФИО', size_hint_x=1)
        content.add_widget(self.name_field)

        self.school_field = MDTextField(hint_text='Учебное заведение', size_hint_x=1)
        content.add_widget(self.school_field)

        role_label = MDLabel(text='Должность:', theme_text_color='Custom', text_color=self.get_text_color())
        content.add_widget(role_label)

        role_box = MDBoxLayout(orientation='horizontal', adaptive_height=True, spacing=20)
        self.student_radio = MDCheckbox(group='role', size_hint=(None, None), size=(48, 48))
        student_label = MDLabel(text='Ученик', size_hint_x=0.4, halign='left')
        self.teacher_radio = MDCheckbox(group='role', size_hint=(None, None), size=(48, 48))
        teacher_label = MDLabel(text='Сотрудник', size_hint_x=0.4, halign='left')
        role_box.add_widget(self.student_radio)
        role_box.add_widget(student_label)
        role_box.add_widget(self.teacher_radio)
        role_box.add_widget(teacher_label)
        content.add_widget(role_box)

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

            self.show_dialog('Настройки сохранены', 'Данные обновлены')
        except Exception as e:
            self.show_dialog('Ошибка', f'Не удалось сохранить: {e}')

    def bind_pass(self, *args):
        if platform != 'android':
            self.show_dialog('NFC недоступен', 'Функция работает только на Android')
            return

        if self.nfc_adapter is None:
            self.show_dialog('Ошибка NFC', 'NFC не поддерживается на устройстве')
            return

        if not self.nfc_adapter.isEnabled():
            self.show_dialog('NFC выключен', 'Пожалуйста, включите NFC в настройках')
            return

        self.enable_nfc_foreground()
        self.show_dialog('Сканирование', 'Поднесите карту к NFC...')
        app = MDApp.get_running_app()
        app.waiting_for_card = True
        app.card_callback = self.on_nfc_tag

    def on_nfc_tag(self, tag):
        try:
            uid_bytes = tag.getId()
            uid = ''.join(f'{b:02X}' for b in uid_bytes)
            uid_formatted = ':'.join(uid[i:i+2] for i in range(0, len(uid), 2))

            try:
                with open('settings.json', 'r') as f:
                    data = json.load(f)
            except:
                data = {}
            data['card_uid'] = uid_formatted
            with open('settings.json', 'w') as f:
                json.dump(data, f)

            Clock.schedule_once(lambda dt: self.update_pass_status(uid_formatted))
            if platform == 'android':
                try:
                    vibrator.vibrate(0.1)
                except:
                    pass

            self.disable_nfc_foreground()
        except Exception as e:
            Clock.schedule_once(lambda dt: self.show_dialog('Ошибка', f'Не удалось считать карту: {e}'))

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
            self.show_dialog('Пропуск удалён', 'Карта отвязана')
        except Exception as e:
            self.show_dialog('Ошибка', f'Не удалось удалить: {e}')

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
        self.waiting_for_card = False
        self.card_callback = None

        if platform == 'android':
            from android import activity
            activity.bind(on_new_intent=self.on_new_intent)

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

    def on_new_intent(self, intent):
        if not self.waiting_for_card:
            return
        if platform != 'android':
            return
        try:
            from jnius import autoclass
            NfcAdapter = autoclass('android.nfc.NfcAdapter')
            Tag = autoclass('android.nfc.Tag')
            action = intent.getAction()
            if NfcAdapter.ACTION_TAG_DISCOVERED == action or \
               NfcAdapter.ACTION_TECH_DISCOVERED == action or \
               NfcAdapter.ACTION_NDEF_DISCOVERED == action:
                tag = intent.getParcelableExtra(NfcAdapter.EXTRA_TAG)
                if tag and self.card_callback:
                    self.card_callback(tag)
                    self.waiting_for_card = False
                    self.card_callback = None
        except Exception as e:
            print(f'NFC intent error: {e}')
            self.waiting_for_card = False
            self.card_callback = None


if __name__ == '__main__':
    SchoolPassApp().run()