import flet as ft
from controllers.game_manager import GameManager
from models.player import Player
from views.components.player_detail_dialog import PlayerDetailDialog
from utils.localization import tr

class StatsView(ft.Container):
    def __init__(self):
        super().__init__()
        self.gm = GameManager()
        self.padding = 20
        self.expand = True
        self.content_area = ft.Row(scroll=ft.ScrollMode.AUTO, wrap=True)
        self.build_content()
        
    def build_content(self):
        self.content = ft.Column([
            ft.Text(tr("League Leaders"), size=30, weight=ft.FontWeight.BOLD),
            ft.Divider(),
            self.content_area
        ], scroll=ft.ScrollMode.AUTO)
        
        self.refresh_stats()

    def refresh_stats(self):
        self.content_area.controls.clear()
        
        # Get all players with at least 1 game played for accurate averages
        all_players = [p for p in self.gm.get_all_players() if p.stats.get('games', 0) > 0]
        
        if not all_players:
            self.content_area.controls.append(ft.Text(tr("No stats available yet. Simulate games first."), size=16, italic=True))
            return

        # Helper to build leader table
        def build_leader_table(title, key_stat=None, stat_func=None, format_str="{:.1f}"):
            
            def get_val(p):
                if stat_func: return stat_func(p)
                return p.stats.get(key_stat, 0) / p.stats.get('games', 1)

            # Sort by stat average desc
            sorted_players = sorted(
                all_players, 
                key=get_val, 
                reverse=True
            )[:10] # Top 10
            
            rows = []
            for i, p in enumerate(sorted_players):
                avg = get_val(p)
                team = self.gm.get_team(p.team_id)
                team_name = team.name if team else "FA"
                
                # Highlight User Team
                is_user = (team and team.id == self.gm.user_team_id)
                # Use a subtle Gold overlay for the user team row
                color = "#33CFB28B" if is_user else None 
                
                # Clickable Name
                name_cell = ft.DataCell(
                    ft.Text(f"{p.mask_name}", weight=ft.FontWeight.BOLD if is_user else ft.FontWeight.NORMAL, color=ft.Colors.PRIMARY), # Gold Text
                    on_tap=lambda e, player=p: self.show_player_detail(player)
                )

                rows.append(
                    ft.DataRow(
                        cells=[
                            ft.DataCell(ft.Text(f"{i+1}")),
                            name_cell,
                            ft.DataCell(ft.Text(team_name, size=12)),
                            ft.DataCell(ft.Text(format_str.format(avg), weight=ft.FontWeight.BOLD)),
                        ],
                        color=color
                    )
                )
            
            return ft.Container(
                content=ft.Column([
                    ft.Text(title, size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.PRIMARY),
                    ft.Row([
                        ft.DataTable(
                            columns=[
                                ft.DataColumn(ft.Text("#"), numeric=True),
                                ft.DataColumn(ft.Text(tr("Name"))),
                                ft.DataColumn(ft.Text(tr("Team"))),
                                ft.DataColumn(ft.Text("Avg"), numeric=True),
                            ],
                            rows=rows,
                            heading_row_height=40,
                            data_row_min_height=40,
                            column_spacing=20
                        )
                    ], scroll=ft.ScrollMode.AUTO)
                ], alignment=ft.MainAxisAlignment.START),
                width=350,
                padding=10,
                border=ft.border.all(1, ft.Colors.OUTLINE_VARIANT),
                border_radius=10,
                margin=5
            )

        # 1. PTS Leaders
        self.content_area.controls.append(build_leader_table(tr("Points Per Game"), key_stat="pts"))
        
        # 2. REB Leaders
        self.content_area.controls.append(build_leader_table(tr("Rebounds Per Game"), key_stat="reb"))
        
        # 3. AST Leaders
        self.content_area.controls.append(build_leader_table(tr("Assists Per Game"), key_stat="ast"))
        
        # 4. STL Leaders
        self.content_area.controls.append(build_leader_table(tr("Steals Per Game"), key_stat="stl"))
        
        # 5. BLK Leaders
        self.content_area.controls.append(build_leader_table(tr("Blocks Per Game"), key_stat="blk"))

        # 6. 2PT Made Leaders
        self.content_area.controls.append(build_leader_table(tr("2PT Made"), key_stat="2pm"))

        # 7. 3PT Made Leaders
        self.content_area.controls.append(build_leader_table(tr("3PT Made"), key_stat="3pm"))

    def show_player_detail(self, player):
        dlg = PlayerDetailDialog(player)
        self.page.overlay.append(dlg)
        dlg.open = True
        self.page.update()
