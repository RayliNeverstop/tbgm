import flet as ft
from controllers.game_manager import GameManager
from utils.localization import tr

class DashboardView(ft.Container):
    def __init__(self, on_history_click=None):
        super().__init__()
        self.gm = GameManager()
        self.on_history_click = on_history_click
        self.padding = 20
        self.build_content()
        # self.content = ft.Text("Test")

    def build_content(self):
        user_team = self.gm.get_user_team()
        
        team_name = user_team.name if user_team else tr("No Team Selected")
        wins = user_team.wins if user_team else 0
        losses = user_team.losses if user_team else 0
        
        # Calculate Rank
        sorted_teams = sorted(
            [t for t in self.gm.teams if t.id != "T00"], 
            key=lambda t: (t.wins, t.wins / (t.wins + t.losses) if (t.wins + t.losses) > 0 else 0), 
            reverse=True
        )
        try:
            rank = sorted_teams.index(user_team) + 1
            rank_suffix = "st" if rank == 1 else "nd" if rank == 2 else "rd" if rank == 3 else "th"
            rank_str = f" ({rank}{rank_suffix})"
        except:
            rank_str = ""

        salary_cap = self.gm.salary_cap
        
        # Calculate current payroll
        # Calculate current payroll
        # Ensure we use millions.
        # Player salaries are stored as floats representing millions (e.g. 15.0).
        current_payroll = sum(p.salary for p in user_team.roster) if user_team else 0
        cap_space = salary_cap - current_payroll

        # Get next game info
        todays_games = self.gm.get_todays_games()
        user_next_game = next((g for g in todays_games if g.home_team.id == user_team.id or g.away_team.id == user_team.id), None)
        
        next_opponent = tr("None")
        if user_next_game:
            opponent = user_next_game.away_team if user_next_game.home_team.id == user_team.id else user_next_game.home_team
            next_opponent = opponent.name

        self.content = ft.Column([
            ft.Row([
                ft.Text(tr("Dashboard"), size=30, weight=ft.FontWeight.BOLD),
                ft.Container(expand=True),
                
                # Action Button (Moved from body)
                self._build_action_button(),
                ft.Container(width=10),

                ft.Container(
                    content=ft.Row([
                        ft.Icon(ft.Icons.MILITARY_TECH, color=ft.Colors.AMBER),
                        ft.Text(f"{getattr(self.gm, 'gm_score', 0)}", size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.AMBER)
                    ]),
                    padding=10,
                    bgcolor="#1E2740",
                    border_radius=10,
                    tooltip=tr("View Score Details"),
                    margin=ft.margin.only(right=10),
                    on_click=self._show_gm_score_details,
                    ink=True
                ),
                ft.ElevatedButton(tr("History"), icon=ft.Icons.HISTORY_EDU, on_click=lambda e: self.on_history_click() if self.on_history_click else None),
                ft.ElevatedButton(tr("Save Game"), icon=ft.Icons.SAVE, on_click=self.save_game),
                ft.IconButton(ft.Icons.INFO_OUTLINE, on_click=self._show_debug_info, tooltip="System Info") 
            ]),
            ft.Divider(),
            ft.Row([
                self._build_stat_card(tr("Team"), team_name, ft.Icons.PEOPLE),
                self._build_stat_card(tr("Record"), f"{wins} - {losses}{rank_str}", ft.Icons.SPORTS_BASKETBALL),
                self._build_stat_card(tr("Team Salary"), f"${current_payroll:.1f}M / ${salary_cap:.1f}M", ft.Icons.MONETIZATION_ON),
                self._build_stat_card(tr("Cap Space"), f"${cap_space:.1f}M", ft.Icons.ACCOUNT_BALANCE_WALLET),
            ], scroll=ft.ScrollMode.AUTO),
            ft.Divider(),
            # Removed redundant 'Next Game' Card
            ft.Text(tr("Recent News"), size=20, weight=ft.FontWeight.BOLD),
            self._build_news_feed(),
        ], scroll=ft.ScrollMode.AUTO)

    def _build_news_feed(self):
        news_items = getattr(self.gm, 'news_feed', [])
        if not news_items:
            return ft.Text(tr("Season started. Good luck!"), italic=True)
            
        # Show last 5
        recent = list(reversed(news_items[-5:]))
        
        return ft.Column([
            ft.Container(
                content=ft.Text(item, size=14),
                padding=5,
                border=ft.border.only(bottom=ft.border.BorderSide(1, "#303030"))
            ) for item in recent
        ])

    def _show_debug_info(self, e):
        import os
        path = self.gm.data_loader.file_path if hasattr(self.gm, 'data_loader') else "N/A"
        exists = os.path.exists(path) if path != "N/A" else False
        save_dir = self.gm.save_manager.save_dir if hasattr(self.gm, 'save_manager') else "N/A"
        
        info = f"App Path: {os.getcwd()}\nData Path: {path}\nFile Exists: {exists}\nSave Dir: {save_dir}\nLoaded Players: {len(self.gm.players)}\nLoaded Teams: {len(self.gm.teams)}\nUser Team: {self.gm.user_team_id}"
        
        def close_dlg(e):
            dlg.open = False
            self.page.update()

        dlg = ft.AlertDialog(
            title=ft.Text("System Debug Info"),
            content=ft.Text(info, size=12, font_family="Consolas"),
            actions=[ft.TextButton("Close", on_click=close_dlg)]
        )
        self.page.dialog = dlg
        dlg.open = True
        self.page.update()

    def save_game(self, e):
        try:
            # 1. File Save (Desktop / Backup)
            result = self.gm.save_game(1)
            
            # 2. Client Storage REMOVED (Caused AttributeError on some devices)
            # Reliance on relative 'game_saves' path is sufficient.
            
            # Handle potential tuple return (success, message) or single bool
            if isinstance(result, tuple):
                success, server_msg = result
            else:
                success = result
                server_msg = "Unknown Error"

            if success:
                msg = tr("Game Saved Successfully!")
                color = ft.Colors.GREEN
            else:
                # If file save failed
                msg = f"{tr('Failed to Save Game')}: {server_msg}"
                color = ft.Colors.ERROR
                
        except Exception as ex:
             msg = f"Critical Save Error: {str(ex)}"
             color = ft.Colors.ERROR

        snack = ft.SnackBar(content=ft.Text(msg), bgcolor=color)
        self.page.overlay.append(snack)
        snack.open = True
        self.page.update()

    def simulate_day(self, e):
        # Placeholder for navigation or actual sim
        # ideally this would navigate to MatchView or run sim
        self.page.go("/match") 

    def _build_action_button(self):
        # Check Season Status
        is_season_over = self._check_season_over()
        
        if is_season_over:
             return ft.ElevatedButton(
                tr("Start Offseason (Draft)"), 
                on_click=self.start_offseason, 
                icon=ft.Icons.NEXT_PLAN,
                bgcolor=ft.Colors.AMBER_900,
                color=ft.Colors.WHITE
            )
        else:
             return ft.ElevatedButton(
                tr("Simulate Day") if not self.gm.is_draft_active else "Draft in Progress", 
                on_click=self.simulate_day, 
                icon=ft.Icons.PLAY_ARROW if not self.gm.is_draft_active else ft.Icons.LOCK,
                disabled=self.gm.is_draft_active
            )

    def _check_season_over(self):
        # Logic to check if finals are done
        # Usually check if rounds 2 is done
        round2 = [s for s in self.gm.playoff_series if s['round'] == 2]
        if round2 and round2[0].get('winner'):
             return True
        return False

    def start_offseason(self, e):
        # Trigger Offseason Flow
        print("Starting Offseason Sequence...")
        self.gm.init_draft()
        self.page.go("/draft")

    def _build_stat_card(self, title, value, icon):
        return ft.Container(
            padding=20,
            bgcolor="#1E2740", # Dark Surface (replacing broken SURFACE_VARIANT)
            border_radius=10,
            width=200,
            content=ft.Column([
                ft.Icon(icon, size=30, color=ft.Colors.PRIMARY), # Gold Icon
                ft.Text(title, size=14, color="#CCCCCC"), # Light Grey Text (replacing ON_SURFACE_VARIANT)
                ft.Text(str(value), size=20, weight=ft.FontWeight.BOLD, color="#FFFFFF") # White Text
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        )

    def _show_gm_score_details(self, e):
        log = getattr(self.gm, 'gm_score_log', [])
        
        if not log:
            content = ft.Text(tr("No score history recorded yet."), italic=True)
        else:
            rows = []
            for entry in log:
                rows.append(ft.DataRow(cells=[
                    ft.DataCell(ft.Text(str(entry.get('date', '-')))),
                    ft.DataCell(ft.Text(str(entry.get('reason', 'Unknown')))),
                    ft.DataCell(ft.Text(f"+{entry.get('points', 0)}", color=ft.Colors.GREEN))
                ]))
            
            content = ft.Column([
                ft.DataTable(
                    columns=[
                        ft.DataColumn(ft.Text(tr("Date"))),
                        ft.DataColumn(ft.Text(tr("Reason"))),
                        ft.DataColumn(ft.Text(tr("Points")), numeric=True),
                    ],
                    rows=rows,
                    heading_row_color=ft.Colors.BLACK12,
                )
            ], scroll=ft.ScrollMode.AUTO, height=400)

        def close_dlg(e):
            dlg.open = False
            e.page.update()

        dlg = ft.AlertDialog(
            title=ft.Text(tr("GM Score History")),
            content=ft.Container(content, width=400, padding=10),
            actions=[ft.TextButton(tr("Close"), on_click=close_dlg)],
            modal=True,
            bgcolor="#1E2740",
        )
        
        if e.page:
            e.page.overlay.append(dlg)
            dlg.open = True
            e.page.update()
