import flet as ft
from controllers.game_manager import GameManager

class MyView(ft.Container):
    def __init__(self):
        super().__init__()
        self.content = ft.Text("Hello")
        self.padding = 20
        self.gm = GameManager()

def main(page: ft.Page):
    page.add(MyView())

if __name__ == "__main__":
    ft.app(target=main)
