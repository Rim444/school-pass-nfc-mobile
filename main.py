"""
School Pass NFC — ПОЛНАЯ ВЕРСИЯ
- Тёмная тема, эффект жидкого стекла
- Экран настроек (ФИО, класс, аватар, фон, удаление пропуска)
- Сохранение/загрузка профиля
- Анимированные переходы между экранами
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
from kivy.uix.image import Image
from kivy.uix.scrollview import ScrollView
from kivymd.uix.textfield import MDTextField
from kivymd.uix.imagelist import MDSmartTile
from plyer import storagechooser, vibrator

# Настройка окна для ПК
if platform != 'android':
    Window.size = (400, 700)

# -------------------------------------------------------------------
# ГЛАВНЫЙ ЭКРАН (карточка, кнопка NFC, статус, история)
# -------------------------------------------------------------------
class MainScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.dialog = None
        self.nfc_data = None
        self.avatar_widget = None
        self.build_ui()
        self.load_profile()

    def build_ui(self):
        # Основной макет
        layout = MDBoxLayout(orientation='vertical', spacing=20, padding=20)

        # --- Карточка профиля (полупрозрачная, эффект стекла) ---
        card = MDCard(
            orientation='vertical',
            padding=20,
            spacing=10,
            size_hint=(1, None),
            height=220,
            elevation=6,
            shadow_softness=12,
            shadow_offset=(0, 4),
            radius=15,
            md_bg_color=(0.2, 0.2, 0.2, 0.9)  # тёмный полупрозрачный фон
        )

        # Аватар (по умолчанию иконка)
        from kivymd.uix.label import MDIcon
        self.avatar_widget = MDIcon(
            icon='account-circle',
            size_hint=(None, None),
            size=(80, 80),
            halign='center',
            valign='middle',
            theme_text_color='Custom',
            text_color=self.theme_cls.primary_color
        )
        self.avatar_widget.pos_hint = {'center_x': 0.5}
        card.add_widget(self.avatar_widget)

        # Имя
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

        # Класс
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

        # ID карты
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

        # --- Кнопка NFC ---
        self.nfc_button = MDRaisedButton(
            text='СЧИТАТЬ ПРОПУСК',
            size_hint=(1, None),
            height=50,
            md_bg_color=self.theme_cls.primary_color,
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

        # --- Кнопка настроек (шестерёнка) ---
        settings_btn = MDIconButton(
            icon='cog',
            pos_hint={'center_x': 0.5},
            on_release=lambda x: setattr(self.manager, 'current', 'settings')
        )
        layout.add_widget(settings_btn)

        # --- История посещений ---
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
        """Загружает профиль из settings.json"""
        settings_file = 'settings.json'
        if os.path.exists(settings_file):
            with open(settings_file, 'r') as f:
                data = json.load(f)
                self.name_label.text = data.get('name', 'Иванов Иван')
                self.class_label.text = data.get('class', '11А')
                self.card_id_label.text = data.get('card_uid', 'ID карты: не привязана')
                # Загрузка аватара
                if 'avatar_path' in data and os.path.exists(data['avatar_path']):
                    self.set_avatar(data['avatar_path'])
                # Загрузка фона приложения
                if 'background_path' in data and os.path.exists(data['background_path']):
                    app = MDApp.get_running_app()
                    if hasattr(app.root, 'ids') and 'background' in app.root.ids:
                        app.root.ids.background.source = data['background_path']

    def set_avatar(self, path):
        """Заменяет иконку на изображение"""
        from kivy.uix.image import Image
        # Удаляем старый виджет аватара из карточки
        card = self.avatar_widget.parent
        card.remove_widget(self.avatar_widget)
        # Создаём Image
        self.avatar_widget = Image(
            source=path,
            size_hint=(None, None),
            size=(80, 80),
            pos_hint={'center_x': 0.5}
        )
        card.add_widget(self.avatar_widget, index=1)  # индекс после возможных других детей

    def read_nfc(self, instance):
        """Симуляция NFC (будет заменена на реальную)"""
        self.status_label.text = 'Сканирование... Поднесите карту'

        def simulate():
            time.sleep(2)
            self.nfc_data = '04:5A:6B:7C:8D:9E'
            self.card_id_label.text = f'ID карты: {self.nfc_data}'
            self.status_label.text = 'Карта считана!'
            self.show_dialog('Успех', 'Карта успешно привязана!')
            # Сохраняем UID в настройки
            self.save_card_uid(self.nfc_data)
            # Вибрация
            if platform == 'android':
                try:
                    vibrator.vibrate(0.1)
                except:
                    pass

        threading.Thread(target=simulate).start()

    def save_card_uid(self, uid):
        """Сохраняет UID карты в settings.json"""
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
# ЭКРАН НАСТРОЕК
# -------------------------------------------------------------------
class SettingsScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.dialog = None
        self.build_ui()
        self.load_settings()

    def build_ui(self):
        layout = MDBoxLayout(orientation='vertical', spacing=20, padding=20)

        # Верхняя панель с кнопкой назад
        header = MDBoxLayout(adaptive_height=True)
        back_btn = MDIconButton(
            icon='arrow-left',
            on_release=lambda x: setattr(self.manager, 'current', 'main')
        )
        header.add_widget(back_btn)
        header.add_widget(MDLabel(text='Настройки', font_style='H5'))
        layout.add_widget(header)

        # Поля ввода ФИО и класса
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

        # Кнопки выбора изображений
        btn_avatar = MDRaisedButton(
            text='Выбрать фото профиля',
            on_release=self.choose_avatar,
            size_hint=(1, None),
            height=48
        )
        layout.add_widget(btn_avatar)

        btn_background = MDRaisedButton(
            text='Выбрать фон приложения',
            on_release=self.choose_background,
            size_hint=(1, None),
            height=48
        )
        layout.add_widget(btn_background)

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
        """Загружает настройки в поля"""
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
        """Сохраняет настройки и обновляет главный экран"""
        data = {}
        settings_file = 'settings.json'
        if os.path.exists(settings_file):
            with open(settings_file, 'r') as f:
                data = json.load(f)

        data['name'] = self.name_field.text
        data['class'] = self.class_field.text

        with open(settings_file, 'w') as f:
            json.dump(data, f)

        # Обновляем главный экран, если он существует
        main_screen = self.manager.get_screen('main')
        main_screen.name_label.text = self.name_field.text
        main_screen.class_label.text = self.class_field.text

        self.show_dialog('Настройки сохранены')

    def choose_avatar(self, *args):
        """Выбор фото профиля"""
        if platform == 'android':
            try:
                from android.permissions import request_permissions, Permission
                request_permissions([Permission.READ_EXTERNAL_STORAGE, Permission.READ_MEDIA_IMAGES])
            except:
                pass

        try:
            chooser = storagechooser.StorageChooser(title='Выберите фото', type='image')
            chooser.bind(on_selection=self.on_avatar_selected)
            chooser.open()
        except Exception as e:
            self.show_dialog(f'Ошибка: {str(e)}')

    def on_avatar_selected(self, instance):
        """Обработка выбранного аватара"""
        selected = instance.selection
        if selected:
            path = selected[0]
            # Сохраняем путь в настройках
            settings_file = 'settings.json'
            data = {}
            if os.path.exists(settings_file):
                with open(settings_file, 'r') as f:
                    data = json.load(f)
            data['avatar_path'] = path
            with open(settings_file, 'w') as f:
                json.dump(data, f)

            # Обновляем аватар на главном экране
            main_screen = self.manager.get_screen('main')
            main_screen.set_avatar(path)
            self.show_dialog('Аватар обновлён')

    def choose_background(self, *args):
        """Выбор фонового изображения"""
        # Аналогично аватару
        if platform == 'android':
            try:
                from android.permissions import request_permissions, Permission
                request_permissions([Permission.READ_EXTERNAL_STORAGE, Permission.READ_MEDIA_IMAGES])
            except:
                pass

        try:
            chooser = storagechooser.StorageChooser(title='Выберите фон', type='image')
            chooser.bind(on_selection=self.on_background_selected)
            chooser.open()
        except Exception as e:
            self.show_dialog(f'Ошибка: {str(e)}')

    def on_background_selected(self, instance):
        selected = instance.selection
        if selected:
            path = selected[0]
            settings_file = 'settings.json'
            data = {}
            if os.path.exists(settings_file):
                with open(settings_file, 'r') as f:
                    data = json.load(f)
            data['background_path'] = path
            with open(settings_file, 'w') as f:
                json.dump(data, f)

            # Применяем фон
            app = MDApp.get_running_app()
            if hasattr(app.root, 'ids') and 'background' in app.root.ids:
                app.root.ids.background.source = path
            self.show_dialog('Фон обновлён')

    def delete_pass(self, *args):
        """Удаляет привязку пропуска"""
        main_screen = self.manager.get_screen('main')
        main_screen.card_id_label.text = 'ID карты: не привязана'
        main_screen.nfc_data = None
        # Удаляем UID из настроек
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
        # Тёмная тема
        self.theme_cls.theme_style = 'Dark'
        self.theme_cls.primary_palette = 'Blue'
        self.theme_cls.accent_palette = 'LightBlue'
        # Цвет фона окна
        Window.clearcolor = (0.12, 0.12, 0.12, 1)  # #1E1E1E

        # Создаём менеджер экранов с анимацией
        sm = ScreenManager(transition=SlideTransition(duration=0.3))
        sm.add_widget(MainScreen(name='main'))
        sm.add_widget(SettingsScreen(name='settings'))
        return sm

    def on_start(self):
        """После запуска загружаем настройки"""
        # Загружаем фон, если есть
        settings_file = 'settings.json'
        if os.path.exists(settings_file):
            with open(settings_file, 'r') as f:
                data = json.load(f)
            # Применяем фон (предполагаем, что корневой виджет имеет id 'background')
            if 'background_path' in data and hasattr(self.root, 'ids') and 'background' in self.root.ids:
                self.root.ids.background.source = data['background_path']


if __name__ == '__main__':
    SchoolPassApp().run()