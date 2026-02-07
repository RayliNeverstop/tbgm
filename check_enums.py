import flet as ft
try:
    print("Checking ft.Colors, etc...")
    print("Colors.RED:", getattr(ft.Colors, "RED", "Not Found"))
    print("colors.RED:", getattr(ft.colors, "RED", "Not Found"))
    
    print("FontWeight.BOLD:", getattr(ft.FontWeight, "BOLD", "Not Found"))
    
    print("MainAxisAlignment.CENTER:", getattr(ft.MainAxisAlignment, "CENTER", "Not Found"))
    
    # Check icons again just to be sure context
    print("Icons.PEOPLE:", getattr(ft.Icons, "PEOPLE", "Not Found"))

except Exception as e:
    print("Error:", e)
