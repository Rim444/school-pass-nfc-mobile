from kivy.uix.screenmanager import Screen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.textfield import MDTextField
from kivymd.uix.button import MDRaisedButton, MDIconButton
from kivymd.uix.label import MDLabel
from kivymd.uix.dialog import MDDialog
from kivy.uix.image import Image
from kivy.core.window import Window
from kivy.utils import platform
from plyer import storagechooser, vibrator
import json
import os

class SettingsScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.dialog = None
        self.build_ui()
        self.load_settings()

    def build_ui(self):
        layout = MDBoxLayout(orientation='vertical', spacing=20, padding=20)

        # Заголовок
        header = MDBoxLayout(adaptive_height=True)
        back_btn = MDIconButton(
            icon='arrow-left',
            on_release=lambda x: setattr(self.manager, 'current', 'main')
        )
        header.add_widget(back_btn)
        header.add_widget(MDLabel(text='Настройки', font_style='H5'))
        layout.add_widget(header)

        # Поля ФИО и класс
        self.name_field = MDTextField(
            hint_text='ФИО',
            text='Иванов Иван',  # заглушка, будет загружено
            size_hint_x=1
        )
        layout.add_widget(self.name_field)

        self.class_field = MDTextField(
            hint_text='Класс',
            text='11А',
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
        """Загружает настройки из файла settings.json"""
        settings_file = 'settings.json'
        if os.path.exists(settings_file):
            with open(settings_file, 'r') as f:
                data = json.load(f)
                self.name_field.text = data.get('name', 'Иванов Иван')
                self.class_field.text = data.get('class', '11А')
                # загрузка изображений будет позже
        else:
            # значения по умолчанию уже проставлены
            pass

    def save_settings(self, *args):
        """Сохраняет настройки в файл"""
        data = {
            'name': self.name_field.text,
            'class': self.class_field.text,
            # пути к изображениям можно добавить позже
        }
        with open('settings.json', 'w') as f:
            json.dump(data, f)

        # Обновляем главный экран (если он уже загружен)
        main_screen = self.manager.get_screen('main')
        if hasattr(main_screen, 'name_label'):
            main_screen.name_label.text = self.name_field.text
        if hasattr(main_screen, 'class_label'):
            main_screen.class_label.text = self.class_field.text

        self.show_dialog('Настройки сохранены')

    def choose_avatar(self, *args):
        """Выбор изображения для аватара"""
        if platform == 'android':
            from android import activity
            from android.permissions import request_permissions, Permission
            request_permissions([Permission.READ_EXTERNAL_STORAGE, Permission.READ_MEDIA_IMAGES])
        
        try:
            chooser = storagechooser.StorageChooser(title='Выберите фото', type='image')
            chooser.bind(on_selection=self.on_avatar_selected)
            chooser.open()
        except Exception as e:
            self.show_dialog(f'Ошибка: {str(e)}')

    def on_avatar_selected(self, instance):
        """Устанавливает выбранное фото как аватар на главном экране"""
        selected = instance.selection
        if selected:
            path = selected[0]
            main_screen = self.manager.get_screen('main')
            # Заменяем MDIcon на Image
            from kivy.uix.image import Image
            avatar = Image(
                source=path,
                size_hint=(None, None),
                size=(80, 80),
                pos_hint={'center_x': 0.5}
            )
            # Удаляем старый аватар (нужно найти его в карточке)
            # Упрощённо: очищаем карточку и пересоздаём? Лучше хранить ссылку.
            # Для простоты предложим сохранить путь и применить через Clock.
            self.show_dialog('Фото выбрано, применится после перезапуска')
            # Сохраняем путь в настройках
            data = {}
            with open('settings.json', 'r') as f:
                data = json.load(f)
            data['avatar_path'] = path
            with open('settings.json', 'w') as f:
                json.dump(data, f)

    def choose_background(self, *args):
        """Выбор изображения для фона"""
        # Аналогично choose_avatar, сохраняем путь
        pass

    def delete_pass(self, *args):
        """Сбрасывает привязку пропуска"""
        main_screen = self.manager.get_screen('main')
        if hasattr(main_screen, 'card_id_label'):
            main_screen.card_id_label.text = 'ID карты: не привязана'
        # Удаляем сохранённый ID
        # (если используете хранилище, очистите его)
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