import flet as ft
from controllers.game_manager import GameManager
from models.player import Player
from utils.localization import tr
from views.draft_view import DraftView

class ScoutingView(ft.Container):
    def __init__(self, page: ft.Page):
        super().__init__()
        self.gm = GameManager()
        self.page_ref = page # Store page reference for DraftView
        self.padding = 20
        self.expand = True
        self.rookie_list = ft.Column(scroll=ft.ScrollMode.AUTO, expand=True)
        self.header_text = ft.Text(tr("Draft Class Preview"), size=30, weight=ft.FontWeight.BOLD)
        self.points_text = ft.Text("", size=16, color=ft.Colors.GREEN)
        
        self.build_content()

    def refresh(self):
        # Refresh GM instance to ensure data Freshness
        self.gm = GameManager() 
        self.build_content()

    def build_content(self):
        # MODE CHECK: If Draft is Active, Show DraftView!
        if self.gm.is_draft_active:
            self.content = DraftView(self.page_ref, on_draft_end=self.refresh)
            return

        # --- NORMAL SCOUTING VIEW (Draft Preview) ---
        self.rookie_list.controls.clear()
        
        # User Request: No Scouting Points, Show All
        # self.points_text.value = ... (Removed)
        
        if not self.gm.draft_class:
            self.rookie_list.controls.append(
                ft.Text(tr("No active draft class. Wait for next season."), size=16, italic=True)
            )
        else:
            for p in self.gm.draft_class:
                self.rookie_list.controls.append(self._build_rookie_card(p))
                
        actions = []

        self.content = ft.Column([
            ft.Row([self.header_text, ft.Container(expand=True)], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ft.Divider(),
            ft.Container(content=self.rookie_list, expand=True), 
            ft.Divider(),
            ft.Row(actions, alignment=ft.MainAxisAlignment.END)
        ])

    def _build_rookie_card(self, p: Player):
        # Always fully scouted
        ovr_display = str(p.ovr)
        pot_display = str(p.potential)
        
        ovr_color = ft.Colors.BLACK
        if p.ovr >= 80: ovr_color = ft.Colors.RED
        elif p.ovr >= 70: ovr_color = ft.Colors.ORANGE
        
        # Draft/Sign Button
        # Check if DRAFT active
        sign_btn = None
        if not self.gm.is_draft_active:
             # Regular season preview
             pass
        else:
             # During Draft
             sign_btn = ft.ElevatedButton(
                 tr("Available"),
                 disabled=True,
                 icon=ft.Icons.LOCK
             )
        
        card = ft.Container(
            padding=10,
            border=ft.border.all(1, ft.Colors.AMBER_500), # Gold Border
            border_radius=8,
            bgcolor="#1A1A1A", # Dark Black Background (User Request)
            content=ft.Row([
                ft.Column([
                    ft.Text(p.mask_name, weight=ft.FontWeight.BOLD, size=16, color=ft.Colors.AMBER_500), # Gold Name
                    ft.Text(f"{p.pos} | {tr('Age')}: {p.age} | {p.id}", size=12, color=ft.Colors.GREY_400),
                ], width=150),
                
                ft.Column([
                    ft.Text(f"{tr('Salary')}: ${p.salary}M", color=ft.Colors.GREEN_400),
                ], width=100),
                
                ft.Column([
                    ft.Text(f"{tr('OVR')}: {ovr_display}", weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE, size=18 if p.ovr >= 80 else 14),
                    ft.Text(f"{tr('POT')}: {pot_display}", color=ft.Colors.CYAN_200),
                ], width=100),
                
                ft.Row([sign_btn] if sign_btn else [])
                
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, scroll=ft.ScrollMode.AUTO)
        )
        return card

    def _get_grade(self, value: int, fuzz: bool = False) -> str:
        # Deprecated but kept for safety if needed elsewhere
        return str(value)

    def _on_scout_click(self, e, player: Player):
        success, msg = self.gm.scout_player(player.id)
        if success:
             self.build_content()
             self.update()
        else:
             e.control.text = msg 
             e.control.update()

    def _on_sign_click(self, e, player: Player):
        user_team = self.gm.get_user_team()
        if not user_team: return
        
        # Logic to sign:
        # Move from draft_class to users team
        if player in self.gm.draft_class:
             self.gm.draft_class.remove(player)
             player.team_id = user_team.id
             user_team.roster.append(player)
             self.gm.players.append(player) # Now active
             
             snack = ft.SnackBar(ft.Text(f"{tr('Drafted')} {player.mask_name}!"))
             self.page.overlay.append(snack)
             snack.open = True
             
             self.build_content()
             self.update()
        
    def _on_finish_draft_click(self, e):
        self.gm.complete_draft()
        snack = ft.SnackBar(ft.Text(tr("Draft Complete! Season Schedule Generated.")))
        self.page.overlay.append(snack)
        snack.open = True
        
        self.build_content()
        self.update()
