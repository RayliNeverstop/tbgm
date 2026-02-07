import flet as ft
import inspect

try:
    print("Version:", ft.version)
except:
    print("Version unknown")

try:
    sig = inspect.signature(ft.Tab.__init__)
    print(f"SIGNATURE: {sig}")
except Exception as e:
    print(f"Sig Failed: {e}")

try:
    t = ft.Tab()
    print("Empty Init: Success")
    print("DIR:", dir(t))
except Exception as e:
    print(f"Empty Init Failed: {e}")
