from kivy.animation import Animation

def fade(widget, d=0.25):
    widget.opacity = 0
    Animation(opacity=1, duration=d).start(widget)

def press(widget):
    Animation(scale=0.96, duration=0.05) + Animation(scale=1, duration=0.05)
