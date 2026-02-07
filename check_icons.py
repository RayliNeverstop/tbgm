import flet as ft
try:
    print("Checking ft.Icons...")
    print("PEOPLE:", getattr(ft.Icons, "PEOPLE", "Not Found"))
    print("GROUP:", getattr(ft.Icons, "GROUP", "Not Found"))
except Exception as e:
    print("Error:", e)
