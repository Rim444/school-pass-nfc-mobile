from kivymd.uix.bottomnavigation import MDBottomNavigation, MDBottomNavigationItem
from src.ui.screens.pass_screen import PassScreen
from src.ui.screens.journal_screen import JournalScreen
from src.ui.screens.settings_screen import SettingsScreen

class RootWidget(MDBottomNavigation):
    def __init__(self, **kw):
        super().__init__(**kw)

        self.add_widget(
            MDBottomNavigationItem(
                name="pass",
                text="Пропуск",
                icon="nfc",
                content=PassScreen()
            )
        )

        self.add_widget(
            MDBottomNavigationItem(
                name="journal",
                text="Журнал",
                icon="history",
                content=JournalScreen()
            )
        )

        self.add_widget(
            MDBottomNavigationItem(
                name="settings",
                text="Настройки",
                icon="cog",
                content=SettingsScreen()
            )
      )
