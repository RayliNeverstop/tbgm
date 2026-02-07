import flet as ft
from main import main

if __name__ == "__main__":
    print("Starting Web Mode for Mobile Testing...")
    print("Ensure your phone is on the same Wi-Fi.")
    print("Please allow access in Windows Firewall if prompted.")
    
    # Run Flet in Web Server mode
    # Run Flet in Web Server mode
    # "web_browser" is the safe string constant if enums vary by version
    ft.app(target=main, view=ft.AppView.WEB_BROWSER, port=8080)
