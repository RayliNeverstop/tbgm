import flet as ft
from controllers.game_manager import GameManager
import math

class TeamSelectScreen(ft.Container):
    def __init__(self, page: ft.Page, on_team_selected=None):
        super().__init__()
        self.main_page = page
        self.on_team_selected = on_team_selected
        self.gm = GameManager()
        self.expand = True
        self.padding = 20
        self.bgcolor = "#0b1120" # Deep Navy Background
        
        # Filter Playable Teams (Exclude Free Agents T00)
        # Also maybe exclude Dummy teams if you don't want them playable? 
        # For now assuming all teams except T00 are playable.
        self.teams = [t for t in self.gm.teams if t.id != "T00"]
        
        # Title
        self.title = ft.Text("選擇您的球隊 (Choose Your Team)", size=28, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER)
        
        # Grid of Teams
        self.team_grid = ft.GridView(
            expand=True,
            runs_count=2, # 2 columns on mobile usually good
            max_extent=200, # Max width of each tile
            child_aspect_ratio=1.0,
            spacing=10,
            run_spacing=10,
        )
        
        for team in self.teams:
            self.team_grid.controls.append(self._create_team_card(team))

        self.content = ft.Column([
            ft.Container(height=20),
            self.title,
            ft.Container(height=20),
            self.team_grid
        ], expand=True, alignment=ft.MainAxisAlignment.START)

    def _create_team_card(self, team):
        return ft.Container(
            content=ft.Column([
                ft.Icon(ft.Icons.SHIELD, size=40, color=team.color), # Placeholder Logo
                ft.Text(team.name, size=16, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER, overflow=ft.TextOverflow.ELLIPSIS),
                ft.Text(f"OVR: {int(team.average_ovr)}", size=14, color=ft.Colors.GREY_400),
            ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            bgcolor="#1E2740", # Card BG
            border=ft.border.all(2, team.color),
            border_radius=10,
            padding=10,
            on_click=lambda e, t_id=team.id: self._on_select(t_id),
            ink=True, # Ripple effect
        )

    def _on_select(self, team_id):
        print(f"DEBUG: Team Selected: {team_id}")
        if self.on_team_selected:
            self.on_team_selected(team_id)
