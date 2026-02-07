import flet as ft
import inspect
import sys

with open("debug_out_utf8.txt", "w", encoding="utf-8") as f:
    try:
        f.write(f"Version: {ft.version}\n")
    except:
        f.write("Version unknown\n")

    try:
        sig = inspect.signature(ft.Tab.__init__)
        f.write(f"SIGNATURE: {sig}\n")
    except Exception as e:
        f.write(f"Sig Failed: {e}\n")

    try:
        t = ft.Tab()
        f.write("Empty Init: Success\n")
        f.write(f"DIR: {dir(t)}\n")
    except Exception as e:
        f.write(f"Empty Init Failed: {e}\n")
