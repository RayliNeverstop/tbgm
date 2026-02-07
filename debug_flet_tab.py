import flet as ft
import inspect

print("Flet Version:", ft.version)
print("Tab Dir:", dir(ft.Tab))
print("Tab Init Args:", inspect.signature(ft.Tab.__init__))

try:
    t = ft.Tab(text="Test")
    print("Success with text")
except Exception as e:
    print("Failed with text:", e)

try:
    t = ft.Tab(tab_content=ft.Text("Test"))
    print("Success with tab_content")
except Exception as e:
    print("Failed with tab_content:", e)
