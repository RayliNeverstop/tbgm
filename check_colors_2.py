import flet as ft
try:
    attrs = dir(ft.Colors)
    print("OUTLINE in Colors?", 'OUTLINE' in attrs)
    print("ON_SURFACE_VARIANT in Colors?", 'ON_SURFACE_VARIANT' in attrs)
    print("ON_SURFACE in Colors?", 'ON_SURFACE' in attrs)
except Exception as e:
    print(e)
