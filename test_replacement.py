import flet as ft
import sys

def main(page: ft.Page):
    print("In main function")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "run":
        print("Using ft.app(target=main)")
        try:
            ft.app(target=main)
        except Exception as e:
            print(e)
    else:
        print("Using ft.app(main)") # Typically typical new usage
        try:
            ft.app(main)
        except Exception as e:
            print(e)
