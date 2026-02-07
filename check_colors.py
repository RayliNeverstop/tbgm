import flet as ft
try:
    print("Listing ft.Colors attributes:")
    attrs = dir(ft.Colors)
    print("Total:", len(attrs))
    print("SURFACE_VARIANT in Colors?", 'SURFACE_VARIANT' in attrs)
    print("SURFACE_VARIANT_CONTAINER in Colors?", 'SURFACE_VARIANT_CONTAINER' in attrs)
    print("SURFACE in Colors?", 'SURFACE' in attrs)
    
    # Print first 20 valid ones (uppercase)
    valid = [a for a in attrs if a.isupper()]
    print("First 20 UPPER:", valid[:20])
except Exception as e:
    print(e)
