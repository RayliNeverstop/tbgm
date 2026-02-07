import flet as ft
from controllers.game_manager import GameManager

from utils.localization import tr

class StandingsView(ft.Container):
    def __init__(self):
        super().__init__()
        self.gm = GameManager()
        self.padding = 20
        self.expand = True
        self.build_content()
        
    def build_content(self):
        # Header
        header = ft.Text(tr("League Standings"), size=30, weight=ft.FontWeight.BOLD)
        
        # Get Sorted Teams (Exclude T00)
        sorted_teams = sorted(
            [t for t in self.gm.teams if t.id != "T00"], # Filter T00
            key=lambda t: (t.wins, t.wins / (t.wins + t.losses) if (t.wins + t.losses) > 0 else 0), 
            reverse=True
        )
        
        # Build Table
        columns = [
            ft.DataColumn(ft.Text(tr("Rank"))),
            ft.DataColumn(ft.Text(tr("Team"))),
            ft.DataColumn(ft.Text(tr("W")), numeric=True),
            ft.DataColumn(ft.Text(tr("L")), numeric=True),
            ft.DataColumn(ft.Text(tr("Pct")), numeric=True),
            ft.DataColumn(ft.Text(tr("Strk"))), # Optional: Streak (Mock for now)
        ]
        
        rows = []
        for i, team in enumerate(sorted_teams):
            rank = i + 1
            total_games = team.wins + team.losses
            pct = f"{(team.wins / total_games):.3f}" if total_games > 0 else ".000"
            
            # Highlight User Team
            is_user = (team.id == self.gm.user_team_id)
            row_color = "#33CFB28B" if is_user else None # Deep Gold Overlay

            # Highlight Playoff Zone (Top 4)
            rank_display = ft.Text(str(rank))
            if rank <= 4:
                rank_display = ft.Container(
                    content=ft.Text(str(rank), color=ft.Colors.BLACK, weight=ft.FontWeight.BOLD),
                    bgcolor=ft.Colors.AMBER,
                    padding=5,
                    border_radius=5,
                    alignment=ft.Alignment(0, 0)
                )
            
            rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(rank_display),
                        ft.DataCell(ft.Row([
                            ft.Container(width=10, height=10, bgcolor=team.color, border_radius=5),
                            ft.Text(team.name, weight=ft.FontWeight.BOLD if is_user else ft.FontWeight.NORMAL, 
                                    color=ft.Colors.PRIMARY if is_user else None) # Gold Text for user
                        ])),
                        ft.DataCell(ft.Text(str(team.wins))),
                        ft.DataCell(ft.Text(str(team.losses))),
                        ft.DataCell(ft.Text(pct)),
                        ft.DataCell(ft.Text("-")),
                    ],
                    color=row_color
                )
            )

        table = ft.DataTable(
            columns=columns,
            rows=rows,
            border=ft.border.all(1, ft.Colors.OUTLINE),
            border_radius=10,
            vertical_lines=ft.border.BorderSide(1, ft.Colors.OUTLINE),
            horizontal_lines=ft.border.BorderSide(1, ft.Colors.OUTLINE_VARIANT),
            heading_row_color=ft.Colors.SURFACE,
        )

        self.content = ft.Column([
            header,
            ft.Divider(),
            ft.Row([table], scroll=ft.ScrollMode.AUTO),
            ft.Container(height=20),
            ft.Text(tr("* Top 4 teams qualify for Playoffs"), italic=True, size=12, color=ft.Colors.GREY)
        ], expand=True, scroll=ft.ScrollMode.AUTO)
