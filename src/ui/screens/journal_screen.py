from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from src.utils.storage import get_logs

class JournalScreen(MDBoxLayout):
    def __init__(self, **kw):
        super().__init__(orientation="vertical", padding=20, spacing=10)

        for log in get_logs():
            self.add_widget(MDLabel(text=log, theme_text_color="Secondary"))
