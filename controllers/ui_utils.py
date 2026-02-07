import flet as ft

def get_ovr_color(ovr: int) -> str:
    """
    Returns the color code based on OVR value.
    OVR >= 90: ft.Colors.AMBER (Gold/Legend)
    OVR 80-89: ft.Colors.RED (Red/All-Star)
    OVR 70-79: ft.Colors.GREEN (Green/Starter)
    OVR < 70: ft.Colors.GREY (Grey/Bench)
    """
    if ovr >= 90:
        return ft.Colors.AMBER
    elif ovr >= 80:
        return ft.Colors.RED
    elif ovr >= 70:
        return ft.Colors.GREEN
    else:
        return ft.Colors.GREY
