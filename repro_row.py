import flet as ft

class MyRow(ft.Row):
    def __init__(self):
        super().__init__()
        self.expand = True
        self.controls = [ft.Text("Row Item")]

def main(page: ft.Page):
    page.add(MyRow())

if __name__ == "__main__":
    ft.app(target=main)
