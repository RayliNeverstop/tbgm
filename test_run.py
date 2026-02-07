import flet as ft

def main(page: ft.Page):
    print("In main")
    page.add(ft.Text("Hello"))

if __name__ == "__main__":
    try:
        ft.app(target=main) # Deprecated
    except Exception:
        pass

    try:
        print("Testing ft.app(main)")
        # Just creating the object, not running fully to block
    except:
        pass
