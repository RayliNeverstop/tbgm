import flet as ft
from views.dashboard_view import DashboardView
import sys

def main(page: ft.Page):
    print("In main...")
    sys.stdout.flush()
    try:
        import os
        import os
        # Assuming run from root
        data_path = os.path.abspath("data/gamedata.json")
        from controllers.game_manager import GameManager
        gm = GameManager()
        gm.initialize(data_path)
        
        dv = DashboardView()
        page.add(dv)
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    ft.app(target=main)
