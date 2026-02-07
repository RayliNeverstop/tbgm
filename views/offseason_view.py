import flet as ft
from controllers.game_manager import GameManager
from controllers.ui_utils import get_ovr_color
from utils.localization import tr

class OffseasonView(ft.Container):
    def __init__(self, on_next_season_click):
        super().__init__()
        self.gm = GameManager()
        self.on_next_season_click = on_next_season_click
        self.padding = 20
        self.expand = True
        self.build_content()
        
    def _get_regular_season_leader(self):
        if not self.gm.teams: return "Unknown"
        # Sort by wins
        sorted_teams = sorted(self.gm.teams, key=lambda t: t.wins, reverse=True)
        leader = sorted_teams[0]
        return f"{leader.name} ({leader.wins}-{leader.losses})"

    def build_content(self):
        # 1. Season Summary
        # 1. Season Summary
        # Find Champion
        champion_name = "Unknown"
        champion_team = None
        
        if hasattr(self.gm, 'playoff_series') and self.gm.playoff_series:
            # Find Final Series
            final_series = next((s for s in self.gm.playoff_series if s['round'] == 2), None)
            if final_series and final_series.get('winner'):
                winner_obj = final_series['winner']
                champion_name = winner_obj.name
                champion_team = winner_obj
        
        # Fallback (Old logic, just in case)
        if champion_name == "Unknown":
            finals_game = next((g for g in self.gm.schedule if g.day == 12), None)
            if finals_game and finals_game.result:
                champion_name = finals_game.result.get("winner", "Unknown")
            
        champion_team = next((t for t in self.gm.teams if t.name == champion_name), None)
        # TPBL Gold
        tpbl_gold = "#CFB28B"
        tpbl_navy = "#003460"
        
        # Override with Gold as requested
        champ_color = tpbl_gold 
        text_color = tpbl_navy
        
        # 2. Retired Players
        retired_list = self.gm.retired_players
        retired_ui = []
        if not retired_list:
            retired_ui.append(ft.Text(tr("No retirements this year.")))
        else:
            for p in retired_list:
                retired_ui.append(
                    ft.ListTile(
                        leading=ft.Icon(ft.Icons.PERSON_OFF, color=ft.Colors.GREY),
                        title=ft.Text(p.mask_name),
                        subtitle=ft.Text(f"{tr('Age')}: {p.age} - {tr('OVR')}: {p.ovr} - {p.team_id}")
                    )
                )

        self.content = ft.Column([
            ft.Text(f"{tr('Season')} {self.gm.season_year} {tr('Season Finished')}", size=30, weight=ft.FontWeight.BOLD),
            ft.Divider(),
            
            # Champion Card
            ft.Container(
                padding=20,
                bgcolor=champ_color,
                border_radius=10,
                content=ft.Column([
                    ft.Text(tr("League Champion (Playoffs)"), size=16, color=text_color),
                    ft.Text(champion_name, size=40, weight=ft.FontWeight.BOLD, color=text_color),
                    ft.Container(height=10),
                    ft.Text(f"{tr('Regular Season Leader')}: {self._get_regular_season_leader()}", size=14, color=ft.Colors.BLACK54)
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                alignment=ft.Alignment(0, 0)
            ),
            
            ft.Divider(),
            ft.Text(tr("Retirements"), size=20, weight=ft.FontWeight.BOLD),
            ft.Container(
                content=ft.Column(retired_ui, scroll=ft.ScrollMode.AUTO),
                height=200,
                border=ft.border.all(1, ft.Colors.OUTLINE),
                border_radius=10,
                padding=10
            ),
            
            ft.Divider(),
            ft.ElevatedButton(
                tr("View Progression Report"), 
                icon=ft.Icons.TRENDING_UP,
                style=ft.ButtonStyle(bgcolor=ft.Colors.PRIMARY, color=ft.Colors.WHITE),
                on_click=self._on_start_click
            )
        ], scroll=ft.ScrollMode.AUTO)

    def _on_start_click(self, e):
        # 1. Start Season Logic (Retirements, Progression, Draft Class Gen)
        # Note: start_new_season now Initializes Draft instead of full reset
        if not self.gm.is_draft_active:
            self.gm.start_new_season() 
            self.gm.init_draft()

        # 2. Redirect to Progression
        if self.on_next_season_click:
            self.on_next_season_click()
