import flet as ft
from controllers.game_manager import GameManager
from utils.localization import tr

class ProgressionView(ft.Container):
    def __init__(self, on_continue_click=None):
        super().__init__()
        self.gm = GameManager()
        self.on_continue_click = on_continue_click # Unused now but kept for compatibility
        self.padding = 20
        self.expand = True
        
        self.selected_team_id = self.gm.user_team_id
        
        self.build_content()
        
    def build_content(self):
        # Refresh Data
        self.prog_data = getattr(self.gm, 'progression_data', {})
        
        # 1. Team Selector (Arrow Style)
        team = self.gm.get_team(self.selected_team_id)
        if not team:
            # Fallback
            team = self.gm.get_user_team()
            self.selected_team_id = team.id

        valid_teams = [t for t in self.gm.teams if t.id != "T00"]
        
        try:
             curr_idx = next(i for i, t in enumerate(valid_teams) if t.id == self.selected_team_id)
        except StopIteration:
             curr_idx = 0
             self.selected_team_id = valid_teams[0].id
             
        def next_team(e):
            new_idx = (curr_idx + 1) % len(valid_teams)
            self.selected_team_id = valid_teams[new_idx].id
            self.build_content()
            self.update()
            
        def prev_team(e):
            new_idx = (curr_idx - 1 + len(valid_teams)) % len(valid_teams)
            self.selected_team_id = valid_teams[new_idx].id
            self.build_content()
            self.update()

        team_selector = ft.Row([
            ft.IconButton(ft.Icons.ARROW_BACK_IOS, on_click=prev_team),
            ft.Text(team.name, size=20, weight=ft.FontWeight.BOLD),
            ft.IconButton(ft.Icons.ARROW_FORWARD_IOS, on_click=next_team),
        ], alignment=ft.MainAxisAlignment.CENTER)

        # Header
        header = ft.Column([
            ft.Text(f"{tr('Season')} {self.gm.season_year-1}-{self.gm.season_year} {tr('Progression Report')}", size=24, weight=ft.FontWeight.BOLD),
            team_selector
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        
        
        # Data Table
        self.data_table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text(tr("Player Info"))), # Merged Name/Age + OVR
                # Stats columns (Right aligned)
                ft.DataColumn(ft.Text(tr("2PT")), numeric=True),
                ft.DataColumn(ft.Text(tr("3PT")), numeric=True),
                ft.DataColumn(ft.Text(tr("REB")), numeric=True),
                ft.DataColumn(ft.Text(tr("AST")), numeric=True),
                ft.DataColumn(ft.Text(tr("STL")), numeric=True),
                ft.DataColumn(ft.Text(tr("BLK")), numeric=True),
                ft.DataColumn(ft.Text(tr("DEF")), numeric=True),
            ],
            column_spacing=40, 
            heading_row_height=40,
            data_row_min_height=84, # Balanced height
            rows=[]
        )
        
        self._populate_rows()
        
        self.content = ft.Column([
            header,
            ft.Divider(),
            ft.Container(
                content=ft.Column([ft.Row([self.data_table], scroll=ft.ScrollMode.AUTO)], scroll=ft.ScrollMode.AUTO),
                expand=True,
                border=ft.border.all(1, ft.Colors.OUTLINE),
                border_radius=8
            )
        ])
        
    def _populate_rows(self):
        self.data_table.rows.clear()
        
        current_rows = []
        for pid, data in self.prog_data.items():
            if data['team_id'] == self.selected_team_id:
                current_rows.append(data)
                
        # Sort by New OVR desc
        current_rows.sort(key=lambda x: x['new_ovr'], reverse=True)
        
        # Helper for cell formatting
        def get_diff_cell(val, diff):
            if diff > 0:
                txt = f"{val} (+{diff})"
                col = ft.Colors.GREEN
            elif diff < 0:
                txt = f"{val} ({diff})"
                col = ft.Colors.RED
            else:
                txt = f"{val}"
                col = ft.Colors.GREY
            # Use Container for explicit alignment to match the Name column
            return ft.DataCell(
                ft.Container(
                    content=ft.Text(txt, color=col, weight=ft.FontWeight.BOLD),
                    alignment=ft.alignment.Alignment(1.0, 0.0), # Center Vertical, Right Horizontal (Manual)
                    padding=ft.padding.only(right=10)
                )
            )

        for p in current_rows:
            # Identity Column: 
            # Row([ Column(Name, Age), Spacer, OVR ])
            
            diff = p['diff']
            new_ovr = p['new_ovr']
            if diff > 0:
                ovr_txt = f"{new_ovr} (+{diff})"
                ovr_col = ft.Colors.GREEN
            elif diff < 0:
                ovr_txt = f"{new_ovr} ({diff})"
                ovr_col = ft.Colors.RED
            else:
                ovr_txt = f"{new_ovr}"
                ovr_col = ft.Colors.GREY
            
            # Left side: Name and Age
            name_age_col = ft.Column([
                ft.Text(p['name'], weight=ft.FontWeight.BOLD, size=18),
                ft.Text(f"Age: {p['age']}", size=12, color=ft.Colors.GREY)
            ], spacing=2, alignment=ft.MainAxisAlignment.CENTER)
            
            # Right side (of the cell): OVR
            ovr_content = ft.Text(ovr_txt, size=16, color=ovr_col, weight=ft.FontWeight.BOLD)
            
            # Combine into one container
            player_info_cell = ft.Container(
                content=ft.Row([
                    name_age_col,
                    ft.Container(width=20), # Spacer
                    ovr_content
                ], alignment=ft.MainAxisAlignment.START, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                alignment=ft.alignment.Alignment(-1.0, 0.0) # Center Vertical, Left Horizontal (Manual)
            )
            
            # Attributes
            attr_diffs = p.get('attr_diffs', {})
            new_attrs = p.get('new_attrs', {})
            
            def get_attr_data(key):
                val = new_attrs.get(key, 0)
                d = attr_diffs.get(key, 0)
                return val, d
                
            cells = [
                ft.DataCell(player_info_cell), 
                get_diff_cell(*get_attr_data("2pt")),
                get_diff_cell(*get_attr_data("3pt")),
                get_diff_cell(*get_attr_data("reb")),
                get_diff_cell(*get_attr_data("pass")),
                get_diff_cell(*get_attr_data("stl")),
                get_diff_cell(*get_attr_data("block")),
                get_diff_cell(*get_attr_data("def")),
            ]
            
            self.data_table.rows.append(ft.DataRow(cells=cells))
