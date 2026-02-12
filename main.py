"""
School Pass NFC — ПОЛНАЯ ВЕРСИЯ
- Карточка пользователя (MDCard) с аватаром-иконкой
- Кнопка "СЧИТАТЬ ПРОПУСК" с цветом из темы
- Реальное чтение NFC UID через pyjnius (без plyer)
- Диалог подтверждения
- Статусная строка
- Готово к отправке на сервер (requests)
- Совместимо с Android 14, KivyMD 2.0.1
"""

from kivy.core.window import Window
from kivy.utils import platform
from kivy.clock import Clock

from kivymd.app import MDApp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDRaisedButton
from kivymd.uix.dialog import MDDialog
from kivymd.uix.imagelist import MDSmartTile
from kivymd.icon_definitions import md_icons

import threading
import time
import requests  # для отправки на сервер

# Настройка окна для ПК
if platform != 'android':
    Window.size = (400, 700)


class MainScreen(MDBoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', spacing=20, padding=20, **kwargs)
        self.dialog = None
        self.nfc_data = None
        self.build_ui()

    def build_ui(self):
        # --- Карточка профиля (без внешнего файла, иконка из md_icons) ---
        card = MDCard(
            orientation='vertical',
            padding=20,
            spacing=10,
            size_hint=(1, None),
            height=200,
            elevation=4,
            radius=15,
            md_bg_color=(1, 1, 1, 1)
        )

        # Аватар — иконка (нет зависимости от avatar.png)
        from kivymd.uix.label import MDIcon
        avatar = MDIcon(
            icon='account-circle',
            size_hint=(None, None),
            size=(80, 80),
            halign='center',
            valign='middle',
            theme_text_color='Custom',
            text_color=self.theme_cls.primary_color
        )
        avatar.pos_hint = {'center_x': 0.5}
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

        # ID карты
        self.card_id_label = MDLabel(
            text='ID карты: не привязана',
            halign='center',
            theme_text_color='Hint',
            font_style='Caption',
            size_hint_y=None,
            height=30
        )
        card.add_widget(self.card_id_label)

        self.add_widget(card)

        # --- Кнопка NFC ---
        self.nfc_button = MDRaisedButton(
            text='СЧИТАТЬ ПРОПУСК',
            size_hint=(1, None),
            height=50,
            md_bg_color=self.theme_cls.primary_color,
            on_release=self.read_nfc
        )
        self.add_widget(self.nfc_button)

        # --- Статус NFC ---
        self.status_label = MDLabel(
            text='Нажмите кнопку и поднесите карту к NFC',
            halign='center',
            theme_text_color='Secondary',
            font_style='Body1',
            size_hint_y=None,
            height=40
        )
        self.add_widget(self.status_label)

        # --- История посещений (заглушка, можно заменить реальными данными) ---
        from kivymd.uix.list import MDList, OneLineListItem
        from kivy.uix.scrollview import ScrollView

        history_label = MDLabel(
            text='Последние события:',
            halign='left',
            theme_text_color='Primary',
            font_style='Subtitle2',
            size_hint_y=None,
            height=30
        )
        self.add_widget(history_label)

        scroll = ScrollView(size_hint=(1, 0.3))
        list_view = MDList()
        for i in range(3):
            item = OneLineListItem(
                text=f'Вход в школу • 08:3{i}',
                divider='Full'
            )
            list_view.add_widget(item)
        scroll.add_widget(list_view)
        self.add_widget(scroll)

    # ------------------------------------------------------------
    # РЕАЛЬНОЕ ЧТЕНИЕ NFC ЧЕРЕЗ PYJNIUS (БЕЗ PLYER)
    # ------------------------------------------------------------
    def read_nfc(self, instance):
        if platform != 'android':
            self.status_label.text = 'NFC доступен только на Android'
            return

        # Импортируем pyjnius ТОЛЬКО ЗДЕСЬ и на Android
        try:
            from jnius import autoclass
            from android import activity
            from android.runnable import run_on_ui_thread
        except ImportError:
            self.status_label.text = 'Библиотека NFC не найдена'
            return

        # Запускаем чтение в отдельном потоке, чтобы не блокировать UI
        def nfc_reader():
            try:
                # Получаем доступ к NFC-адаптеру
                NfcAdapter = autoclass('android.nfc.NfcAdapter')
                Intent = autoclass('android.content.Intent')
                PendingIntent = autoclass('android.app.PendingIntent')
                IntentFilter = autoclass('android.content.IntentFilter')
                Tag = autoclass('android.nfc.Tag')

                activity = MDApp.get_running_app().root_window._activity
                adapter = NfcAdapter.getDefaultAdapter(activity)

                if adapter is None:
                    self.status_label.text = 'NFC не поддерживается'
                    return

                if not adapter.isEnabled():
                    self.status_label.text = 'Включите NFC в настройках'
                    # Можно открыть настройки NFC:
                    # activity.startActivity(Intent(android.provider.Settings.ACTION_NFC_SETTINGS))
                    return

                # Создаём PendingIntent для получения уведомлений о метках
                intent = Intent(activity, activity.getClass())
                intent.addFlags(Intent.FLAG_ACTIVITY_SINGLE_TOP)
                pending_intent = PendingIntent.getActivity(
                    activity, 0, intent, 
                    PendingIntent.FLAG_IMMUTABLE | PendingIntent.FLAG_UPDATE_CURRENT
                )

                # Фильтры для всех типов NFC-меток
                filters = [IntentFilter(NfcAdapter.ACTION_TAG_DISCOVERED)]
                filters[0].addDataType('*/*')  # для MIME-типов, если нужно

                # Запускаем foreground dispatch
                run_on_ui_thread(adapter.enableForegroundDispatch)(
                    activity, pending_intent, filters, None
                )

                self.status_label.text = 'Сканирование... Поднесите карту'

                # Теперь нужно перехватить Intent в on_new_intent
                # Для этого сохраняем callback в классе приложения
                app = MDApp.get_running_app()
                app.nfc_callback = self.on_nfc_tag

            except Exception as e:
                self.status_label.text = f'Ошибка NFC: {str(e)}'

        threading.Thread(target=nfc_reader).start()

    def on_nfc_tag(self, intent):
        """Вызывается, когда найдена NFC-метка (из MainActivity)"""
        try:
            from jnius import autoclass, JavaException
            Tag = autoclass('android.nfc.Tag')
            tag = intent.getParcelableExtra('android.nfc.extra.TAG')
            if tag is not None:
                # Получаем UID в шестнадцатеричном виде
                uid_bytes = tag.getId()
                uid = ''.join(f'{b:02X}' for b in uid_bytes)
                uid_formatted = ':'.join(uid[i:i+2] for i in range(0, len(uid), 2))

                self.nfc_data = uid_formatted
                self.card_id_label.text = f'ID карты: {self.nfc_data}'
                self.status_label.text = 'Карта считана!'
                self.show_dialog('Успех', f'Карта привязана.\nUID: {self.nfc_data}')

                # Здесь можно отправить UID на сервер
                # self.send_to_server(self.nfc_data)
            else:
                self.status_label.text = 'Не удалось прочитать карту'
        except Exception as e:
            self.status_label.text = f'Ошибка: {str(e)}'

    def send_to_server(self, uid):
        """Отправка UID на ваш сервер (пример)"""
        try:
            # Замените URL на ваш эндпоинт
            url = 'https://your-server.com/api/nfc'
            payload = {'uid': uid, 'user': 'ivanov'}
            response = requests.post(url, json=payload, timeout=5)
            if response.status_code == 200:
                self.status_label.text = 'Данные отправлены'
            else:
                self.status_label.text = 'Ошибка сервера'
        except Exception as e:
            self.status_label.text = 'Нет соединения'

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

        # Для перехвата NFC-интентов на Android
        if platform == 'android':
            from android import activity
            activity.bind(on_new_intent=self.on_new_intent)

        return MainScreen()

    def on_new_intent(self, intent):
        """Перехватываем Intent с NFC-меткой"""
        if hasattr(self.root, 'on_nfc_tag'):
            self.root.on_nfc_tag(intent)


if __name__ == '__main__':
    SchoolPassApp().run()
