import flet as ft
from controllers.game_manager import GameManager
from controllers.ui_utils import get_ovr_color

from utils.localization import tr

class MarketView(ft.Container):
    def __init__(self):
        super().__init__()
        self.gm = GameManager()
        self.padding = 20
        self.expand = True
        
        # Filter & Sort State
        self.pos_options = ["All", "PG", "SG", "SF", "PF", "C"]
        self.current_pos_idx = 0
        self.sort_col_index = None
        self.sort_ascending = True
        
        self.build_content()
        
    def build_content(self):
        # 1. Header
        header = ft.Row([
            ft.Text(tr("Free Agency Market"), size=30, weight=ft.FontWeight.BOLD),
            self._build_filter_controls(), # Add Filter
            ft.Container(expand=True),
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)

        # 2. Get Data & Filter
        free_agents = [p for p in self.gm.players if p.team_id == "T00"]
        
        current_pos = self.pos_options[self.current_pos_idx]
        if current_pos != "All":
            free_agents = [p for p in free_agents if p.pos == current_pos]
            
        # 3. Sort Data
        if self.sort_col_index is not None:
             # Map Column Index to Attribute
             # 0: Pos, 1: Name, 2: Age, 3: OVR, 4: Salary, 5: 2P, 6: 3P, 7: Reb, 8: Pas, 9: Def
             key_map = {
                 0: lambda p: p.pos,
                 1: lambda p: p.mask_name,
                 2: lambda p: p.age,
                 3: lambda p: p.ovr,
                 4: lambda p: p.salary,
                 5: lambda p: p.attributes.two_pt,
                 6: lambda p: p.attributes.three_pt,
                 7: lambda p: p.attributes.rebound,
                 8: lambda p: p.attributes.passing,
                 9: lambda p: p.attributes.defense
             }
             if self.sort_col_index in key_map:
                 free_agents.sort(key=key_map[self.sort_col_index], reverse=not self.sort_ascending)

        # 4. Build Table
        columns = [
            ft.DataColumn(ft.Text(tr("Pos")), on_sort=self.on_sort),
            ft.DataColumn(ft.Text(tr("Name")), on_sort=self.on_sort),
            ft.DataColumn(ft.Text(tr("Age")), numeric=True, on_sort=self.on_sort),
            ft.DataColumn(ft.Text(tr("OVR")), numeric=True, on_sort=self.on_sort),
            ft.DataColumn(ft.Text(tr("Salary")), numeric=True, on_sort=self.on_sort),
            ft.DataColumn(ft.Text(tr("2pt")), numeric=True, on_sort=self.on_sort),
            ft.DataColumn(ft.Text(tr("3pt")), numeric=True, on_sort=self.on_sort),
            ft.DataColumn(ft.Text(tr("Reb")), numeric=True, on_sort=self.on_sort),
            ft.DataColumn(ft.Text(tr("Pas")), numeric=True, on_sort=self.on_sort),
            ft.DataColumn(ft.Text(tr("Def")), numeric=True, on_sort=self.on_sort),
            ft.DataColumn(ft.Text(tr("Action"))),
        ]
        
        rows = []
        for p in free_agents:
            ovr_color = get_ovr_color(p.ovr)
            
            rows.append(ft.DataRow(cells=[
                ft.DataCell(ft.Text(p.pos)),
                ft.DataCell(
                    ft.Text(p.mask_name, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE),
                    on_tap=lambda e, p=p: self._open_player_detail(p)
                ), # Name
                ft.DataCell(ft.Text(str(p.age))),
                ft.DataCell(ft.Container( # OVR
                    content=ft.Text(str(p.ovr), weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                    bgcolor=ovr_color, padding=5, border_radius=5, width=40, alignment=ft.Alignment(0,0)
                )),
                ft.DataCell(ft.Text(f"${p.salary:.2f}M")),
                ft.DataCell(ft.Text(str(p.attributes.two_pt))),
                ft.DataCell(ft.Text(str(p.attributes.three_pt))),
                ft.DataCell(ft.Text(str(p.attributes.rebound))),
                ft.DataCell(ft.Text(str(p.attributes.passing))),
                ft.DataCell(ft.Text(str(p.attributes.defense))),
                ft.DataCell(ft.ElevatedButton(tr("Negotiate"), on_click=lambda e, p=p: self._open_negotiation(p))),
            ]))
            
        table = ft.DataTable(
            columns=columns,
            rows=rows,
            sort_column_index=self.sort_col_index,
            sort_ascending=self.sort_ascending,
            border=ft.border.all(1, ft.Colors.OUTLINE),
            border_radius=10,
            vertical_lines=ft.border.BorderSide(1, ft.Colors.OUTLINE),
            horizontal_lines=ft.border.BorderSide(1, ft.Colors.OUTLINE),
            column_spacing=10,
            heading_row_color="#2B3345",
        )

        self.content = ft.Column([
            header,
            ft.Divider(),
            ft.Column([ft.Row([table], scroll=ft.ScrollMode.AUTO)], scroll=ft.ScrollMode.AUTO, expand=True) # Scrollable Table
        ], expand=True)

    def _build_filter_controls(self):
        return ft.Row([
            ft.IconButton(ft.Icons.ARROW_BACK_IOS, on_click=self.prev_pos, tooltip=tr("Previous")),
            ft.Container(
                content=ft.Text(self.pos_options[self.current_pos_idx], size=20, weight=ft.FontWeight.BOLD),
                width=100, 
                alignment=ft.Alignment(0, 0)
            ),
            ft.IconButton(ft.Icons.ARROW_FORWARD_IOS, on_click=self.next_pos, tooltip=tr("Next")),
        ])

    def next_pos(self, e):
        self.current_pos_idx = (self.current_pos_idx + 1) % len(self.pos_options)
        self.build_content()
        self.update()

    def prev_pos(self, e):
         self.current_pos_idx = (self.current_pos_idx - 1) % len(self.pos_options)
         self.build_content()
         self.update()

    def on_sort(self, e):
        # Toggle sort order if same column, else default to descending (True = Ascending in Flet, usually we want high stats first which is Descending)
        # In Flet sort_ascending=True means 0->9. 
        # For OVR, we want 99->0 (Descending) -> sort_ascending=False.
        
        if self.sort_col_index == e.column_index:
            self.sort_ascending = not self.sort_ascending
        else:
            self.sort_col_index = e.column_index
            self.sort_ascending = False # Default to high-to-low for stats
            
        self.build_content()
        self.update()

    def _open_player_detail(self, player):
        from views.components.player_detail_dialog import PlayerDetailDialog
        
        # Open in "status" tab by default
        dlg = PlayerDetailDialog(player, on_close=None, initial_tab="status")
        self.page.overlay.append(dlg)
        dlg.open = True
        self.page.update()

    def _open_negotiation(self, player):
        from views.components.player_detail_dialog import PlayerDetailDialog
        
        def on_signed():
            self.show_snack(f"Signed {player.mask_name}!", ft.Colors.GREEN)
            self.build_content()
            self.update()
            
        dlg = PlayerDetailDialog(player, on_close=None, initial_tab="contract", on_signed=on_signed)
        self.page.overlay.append(dlg)
        dlg.open = True
        self.page.update()

    def show_snack(self, message, color):
        snack = ft.SnackBar(content=ft.Text(message), bgcolor=color)
        self.page.overlay.append(snack)
        snack.open = True
        self.page.update()
