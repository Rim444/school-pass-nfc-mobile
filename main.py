"""
School Pass NFC — Версия с выбором класса через выпадающие списки и тестовым расписанием
(исправлена ошибка вызова несуществующего метода update_scroll)
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
from kivymd.uix.list import MDList, TwoLineListItem, OneLineListItem
from kivy.uix.scrollview import ScrollView
from kivymd.uix.textfield import MDTextField
from kivymd.uix.selectioncontrol import MDSwitch, MDCheckbox
from kivymd.uix.bottomnavigation import MDBottomNavigation, MDBottomNavigationItem
from kivymd.uix.toolbar import MDTopAppBar
from kivymd.uix.menu import MDDropdownMenu
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
# ФУНКЦИИ ДЛЯ ГЕНЕРАЦИИ ТЕСТОВОГО РАСПИСАНИЯ
# -------------------------------------------------------------------
def generate_schedule_for_all_classes():
    """
    Генерирует тестовое расписание для всех классов.
    Каждый класс получает одинаковое расписание: каждый день 7 уроков "Информатика".
    """
    days = range(7)  # 0=пн, 6=вс
    lessons = ['Информатика'] * 7
    schedule = {}
    # Параллели 5-9 с буквами А-Д
    for grade in range(5, 10):
        for letter in ['А', 'Б', 'В', 'Г', 'Д']:
            class_name = f"{grade}{letter}"
            schedule[class_name] = {day: lessons.copy() for day in days}
    # Параллели 10-11 с буквами А-В
    for grade in range(10, 12):
        for letter in ['А', 'Б', 'В']:
            class_name = f"{grade}{letter}"
            schedule[class_name] = {day: lessons.copy() for day in days}
    return schedule

# Генерируем словарь расписания один раз при старте
SCHEDULE = generate_schedule_for_all_classes()

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
        self.last_event_time = None
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

        # --- Кнопка включения пропуска (записывает в журнал) ---
        self.pass_button = MDRaisedButton(
            text='Включить пропуск',
            size_hint=(1, None),
            height=48,
            md_bg_color=self.get_accent_color(),
            on_release=self.toggle_pass
        )
        content.add_widget(self.pass_button)

        # --- Расписание ---
        schedule_label = MDLabel(
            text='Расписание на сегодня:',
            halign='left',
            theme_text_color='Custom',
            text_color=self.get_secondary_text_color(),
            font_style='Subtitle2',
            size_hint_y=None,
            height=30
        )
        content.add_widget(schedule_label)

        # Список для уроков
        self.schedule_list = MDList()
        self.schedule_scroll = ScrollView(size_hint=(1, 0.5))
        self.schedule_scroll.add_widget(self.schedule_list)
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
                    # Обновляем расписание, если роль ученик и класс сохранён
                    if data.get('role') == 'Ученик' and 'class' in data and data['class']:
                        self.update_schedule(data['class'])
                    else:
                        self.clear_schedule()
        except Exception as e:
            print(f"Ошибка загрузки профиля: {e}")
            traceback.print_exc()

    def update_schedule(self, class_name):
        """Обновляет расписание для указанного класса на текущий день"""
        try:
            weekday = date.today().weekday()
            lessons = SCHEDULE.get(class_name, {}).get(weekday, [])
            self.clear_schedule()
            if lessons:
                for lesson in lessons:
                    item = OneLineListItem(
                        text=lesson,
                        divider='Full',
                        theme_text_color='Custom',
                        text_color=self.get_text_color()
                    )
                    self.schedule_list.add_widget(item)
            else:
                item = OneLineListItem(
                    text='Уроков нет',
                    divider='Full',
                    theme_text_color='Custom',
                    text_color=self.get_hint_text_color()
                )
                self.schedule_list.add_widget(item)

            # Принудительное обновление интерфейса
            Clock.schedule_once(lambda dt: self.schedule_list.do_layout(), 0)
        except Exception as e:
            print(f"Ошибка обновления расписания: {e}")
            traceback.print_exc()

    def clear_schedule(self):
        try:
            self.schedule_list.clear_widgets()
            Clock.schedule_once(lambda dt: self.schedule_list.do_layout(), 0)
        except Exception as e:
            print(f"Ошибка очистки расписания: {e}")

    def toggle_pass(self, instance):
        # Чередование Вход/Выход
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
            app.log_screen.add_entry(event_type, time_str)

        # Меняем состояние кнопки (просто для визуала)
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
        self.grade_menu = None
        self.letter_menu = None
        self.selected_grade = None  # выбранная параллель (число)
        self.selected_letter = None  # выбранная буква
        self.build_ui()
        self.load_settings()
        if platform == 'android':
            self.init_nfc()

    def init_nfc(self):
        """Инициализация NFC через pyjnius"""
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
        """Включаем приём NFC-интентов в foreground"""
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

        role_box = MDBoxLayout(orientation='horizontal', adaptive_height=True, spacing=20, padding=[0,0,0,0])
        self.student_radio = MDCheckbox(group='role', size_hint=(None, None), size=(48, 48))
        student_label = MDLabel(text='Ученик', size_hint_x=0.4, halign='left')
        self.teacher_radio = MDCheckbox(group='role', size_hint=(None, None), size=(48, 48))
        teacher_label = MDLabel(text='Сотрудник', size_hint_x=0.4, halign='left')

        role_box.add_widget(self.student_radio)
        role_box.add_widget(student_label)
        role_box.add_widget(self.teacher_radio)
        role_box.add_widget(teacher_label)
        content.add_widget(role_box)

        # --- Блок выбора класса (появляется только для учеников) ---
        self.class_selection_box = MDBoxLayout(orientation='vertical', spacing=10, size_hint_y=None, height=100)
        self.class_selection_box.opacity = 0
        self.class_selection_box.disabled = True

        # Кнопка для выбора параллели
        self.grade_button = MDRaisedButton(
            text='Параллель',
            size_hint=(1, None),
            height=48,
            md_bg_color=self.get_accent_color(),
            on_release=self.show_grade_menu
        )
        self.class_selection_box.add_widget(self.grade_button)

        # Кнопка для выбора буквы
        self.letter_button = MDRaisedButton(
            text='Буква',
            size_hint=(1, None),
            height=48,
            md_bg_color=self.get_accent_color(),
            on_release=self.show_letter_menu,
            disabled=True
        )
        self.class_selection_box.add_widget(self.letter_button)

        content.add_widget(self.class_selection_box)

        # Привяжем обработчики для радио-кнопок
        self.student_radio.bind(active=self.on_role_changed)
        self.teacher_radio.bind(active=self.on_role_changed)

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

    def on_role_changed(self, checkbox, value):
        """Показываем блок выбора класса, если выбрана роль 'Ученик'"""
        if checkbox == self.student_radio and value:
            self.class_selection_box.opacity = 1
            self.class_selection_box.disabled = False
        elif checkbox == self.teacher_radio and value:
            self.class_selection_box.opacity = 0
            self.class_selection_box.disabled = True

    def show_grade_menu(self, button):
        """Показывает выпадающее меню для выбора параллели (5-11)"""
        grade_items = [
            {"text": f"{i}", "viewclass": "OneLineListItem", "on_release": lambda x=f"{i}": self.set_grade(x)}
            for i in range(5, 12)
        ]
        self.grade_menu = MDDropdownMenu(
            caller=button,
            items=grade_items,
            width_mult=2,
        )
        self.grade_menu.open()

    def set_grade(self, grade_str):
        """Устанавливает выбранную параллель и обновляет кнопку"""
        self.selected_grade = grade_str
        self.grade_button.text = f"{grade_str} класс"
        self.grade_menu.dismiss()
        # Активируем кнопку выбора буквы и обновляем её меню
        self.letter_button.disabled = False
        self.update_letter_menu()
        # Сбрасываем выбор буквы
        self.selected_letter = None
        self.letter_button.text = 'Буква'

    def update_letter_menu(self):
        """Формирует список букв для выбранной параллели"""
        grade = int(self.selected_grade) if self.selected_grade else 0
        if 5 <= grade <= 9:
            letters = ['А', 'Б', 'В', 'Г', 'Д']
        elif grade in (10, 11):
            letters = ['А', 'Б', 'В']
        else:
            letters = []
        self.letter_items = [
            {"text": letter, "viewclass": "OneLineListItem", "on_release": lambda x=letter: self.set_letter(x)}
            for letter in letters
        ]

    def show_letter_menu(self, button):
        """Показывает выпадающее меню для выбора буквы"""
        if not hasattr(self, 'letter_items') or not self.letter_items:
            return
        self.letter_menu = MDDropdownMenu(
            caller=button,
            items=self.letter_items,
            width_mult=2,
        )
        self.letter_menu.open()

    def set_letter(self, letter):
        """Устанавливает выбранную букву и обновляет кнопку"""
        self.selected_letter = letter
        self.letter_button.text = letter
        self.letter_menu.dismiss()

    def get_selected_class(self):
        """Возвращает строку класса (например, '11А') или None"""
        if self.selected_grade and self.selected_letter:
            return f"{self.selected_grade}{self.selected_letter}"
        return None

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
                        self.class_selection_box.opacity = 1
                        self.class_selection_box.disabled = False
                        # Загружаем сохранённый класс
                        saved_class = data.get('class', '')
                        if saved_class and isinstance(saved_class, str) and len(saved_class) >= 2:
                            # Пытаемся разобрать
                            grade_str = saved_class[:-1]
                            letter = saved_class[-1]
                            if grade_str.isdigit() and 5 <= int(grade_str) <= 11:
                                self.selected_grade = grade_str
                                self.grade_button.text = f"{grade_str} класс"
                                self.update_letter_menu()
                                self.selected_letter = letter
                                self.letter_button.text = letter
                                self.letter_button.disabled = False
                    else:
                        self.student_radio.active = False
                        self.teacher_radio.active = True
                        self.class_selection_box.opacity = 0
                        self.class_selection_box.disabled = True

                    if 'card_uid' in data:
                        self.pass_status.text = f"Пропуск: привязан ({data['card_uid']})"
                    else:
                        self.pass_status.text = 'Пропуск: не привязан'
        except Exception as e:
            print(f"Ошибка загрузки настроек: {e}")
            traceback.print_exc()
            # Сброс к значениям по умолчанию
            self.name_field.text = 'Питирим Батурин'
            self.school_field.text = ''
            self.student_radio.active = True
            self.teacher_radio.active = False
            self.class_selection_box.opacity = 1
            self.class_selection_box.disabled = False
            self.selected_grade = None
            self.selected_letter = None
            self.grade_button.text = 'Параллель'
            self.letter_button.text = 'Буква'
            self.letter_button.disabled = True

    def save_settings(self, *args):
        try:
            data = {}
            if os.path.exists('settings.json'):
                with open('settings.json', 'r') as f:
                    data = json.load(f)

            data['name'] = self.name_field.text
            data['school'] = self.school_field.text
            data['role'] = 'Ученик' if self.student_radio.active else 'Сотрудник'
            # Сохраняем класс, если роль ученик и выбран
            if self.student_radio.active:
                selected_class = self.get_selected_class()
                if selected_class:
                    data['class'] = selected_class
                elif 'class' in data:
                    del data['class']
            else:
                if 'class' in data:
                    del data['class']

            with open('settings.json', 'w') as f:
                json.dump(data, f)

            app = MDApp.get_running_app()
            if app.main_screen:
                app.main_screen.name_label.text = self.name_field.text
                app.main_screen.role_label.text = data['role']
                # Обновляем расписание, если роль ученик и класс сохранён
                if data['role'] == 'Ученик' and 'class' in data and data['class']:
                    app.main_screen.update_schedule(data['class'])
                else:
                    app.main_screen.clear_schedule()

            self.show_dialog('Настройки сохранены', 'Данные обновлены')
        except Exception as e:
            print(f"Ошибка сохранения настроек: {e}")
            traceback.print_exc()
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