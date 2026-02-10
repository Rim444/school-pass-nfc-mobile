from kivymd.app import MDApp
from src.ui.root import RootWidget
from src.config import Config

class SchoolPassApp(MDApp):
    def build(self):
        self.title = "School Pass"
        self.theme_cls.theme_style = Config.theme
        self.theme_cls.primary_palette = "Blue"
        return RootWidget()

if __name__ == "__main__":
    SchoolPassApp().run()
