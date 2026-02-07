import flet as ft
from controllers.game_manager import GameManager
from utils.localization import tr

class SeasonSummaryView(ft.Container):
    def __init__(self, on_continue=None):
        super().__init__()
        self.gm = GameManager()
        self.on_continue = on_continue
        self.padding = 20
        self.build_content()
        
    def build_content(self):
        if not self.gm.league_history:
            self.content = ft.Text("No Season History Available")
            return
            
        # Get latest season data
        data = self.gm.league_history[-1]
        
        # Extract Data
        year = data.get("year", "N/A")
        champion_name = data.get("champion", "N/A")
        mvp_text = data.get("mvp", "N/A")
        fmvp_text = data.get("fmvp", "N/A")
        
        # Helper to create Award Cards
        def award_card(title, name, icon, color):
            return ft.Container(
                content=ft.Column([
                    ft.Icon(icon, size=50, color=color),
                    ft.Text(title, size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_400),
                    ft.Text(name, size=22, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                padding=20,
                border=ft.border.all(1, ft.Colors.WHITE10),
                border_radius=10,
                bgcolor="#1E2740", # Dark Surface
                width=300,
                alignment=ft.Alignment(0, 0)
            )

        self.content = ft.Column([
            ft.Text(f"{tr('Season')} {year} {tr('Summary')}", size=40, weight=ft.FontWeight.BOLD),
            ft.Divider(),
            
            # Champion Section
            ft.Container(
                content=ft.Column([
                    ft.Icon(ft.Icons.EMOJI_EVENTS, size=100, color=ft.Colors.AMBER),
                    ft.Text(tr("CHAMPIONS"), size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.AMBER),
                    ft.Text(champion_name, size=50, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                padding=40,
                alignment=ft.Alignment(0, 0)
            ),
            
            ft.Divider(),
            
            # Individual Awards
            ft.Row([
                award_card(tr("Season MVP"), mvp_text, ft.Icons.STAR, ft.Colors.CYAN),
                award_card(tr("Finals MVP"), fmvp_text, ft.Icons.LOCAL_FIRE_DEPARTMENT, ft.Colors.DEEP_ORANGE)
            ], alignment=ft.MainAxisAlignment.CENTER),
            
            ft.Container(height=50),
            
            ft.ElevatedButton(
                tr("Continue to Offseason"), 
                icon=ft.Icons.ARROW_FORWARD,
                style=ft.ButtonStyle(bgcolor=ft.Colors.GREEN_700, color=ft.Colors.WHITE, padding=25),
                on_click=self.handle_continue
            )
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, scroll=ft.ScrollMode.AUTO)

    def handle_continue(self, e):
        if self.on_continue:
            self.on_continue()
