from kivymd.uix.card import MDCard
from kivy.uix.effectwidget import EffectWidget, GaussianBlurEffect
from kivy.graphics import Color, RoundedRectangle

class GlassCard(MDCard):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.radius = [24]
        self.elevation = 0
        self.md_bg_color = (1, 1, 1, 0.10)

        with self.canvas.before:
            Color(1, 1, 1, 0.18)
            self.bg = RoundedRectangle(pos=self.pos, size=self.size, radius=self.radius)

        self.bind(pos=self.update_bg, size=self.update_bg)

    def update_bg(self, *_):
        self.bg.pos = self.pos
        self.bg.size = self.size

class BlurBackground(EffectWidget):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.effects = [GaussianBlurEffect(radius=12)]
