import flet as ft
from controllers.game_manager import GameManager
from controllers.ui_utils import get_ovr_color
from views.components.player_detail_dialog import PlayerDetailDialog

from utils.localization import tr

class RosterView(ft.Container):
    def __init__(self):
        super().__init__()
        self.gm = GameManager()
        self.padding = 20
        self.view_mode = "stats" # Default mode
        self.selected_team_id = self.gm.user_team_id # Default to user team
        self.build_content()

    def reset_view(self):
        self.selected_team_id = self.gm.user_team_id
        self.build_content()

    def build_content(self):
        # 1. Get Selected Team
        team = self.gm.get_team(self.selected_team_id)
        if not team:
            # Fallback
            team = self.gm.get_user_team()
            self.selected_team_id = team.id

        players = team.roster
        
        # Sort players by OVR descending
        players.sort(key=lambda x: x.ovr, reverse=True)

        # 2. Team Selector (Arrow Style)
        # Exclude Free Agents
        valid_teams = [t for t in self.gm.teams if t.id != "T00"]
        
        # Ensure we have a valid index
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
            new_idx = (curr_idx - 1) % len(valid_teams)
            self.selected_team_id = valid_teams[new_idx].id
            self.build_content()
            self.update()
            
        team_selector = ft.Row([
            ft.IconButton(ft.Icons.ARROW_BACK_IOS, on_click=prev_team, tooltip=tr("Previous Team")),
            ft.Container(
                content=ft.Text(team.name, size=20, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER),
                expand=True, 
                alignment=ft.Alignment(0, 0)
            ),
            ft.IconButton(ft.Icons.ARROW_FORWARD_IOS, on_click=next_team, tooltip=tr("Next Team")),
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)

        # Toggle Button
        toggle = ft.SegmentedButton(
            selected=[self.view_mode], 
            on_change=self.on_view_change,
            segments=[
                ft.Segment(value="stats", label=ft.Text(tr("Stats"))),
                ft.Segment(value="attrs", label=ft.Text(tr("Attributes"))),
            ]
        )


        columns = []
        if self.view_mode == "stats":
            columns = [
                ft.DataColumn(ft.Text(tr("Pos"))), # "POS" -> "Pos" to match key
                ft.DataColumn(ft.Text(tr("Name"))),
                ft.DataColumn(ft.Text(tr("OVR")), numeric=True),
                ft.DataColumn(ft.Text(tr("Age")), numeric=True),
                ft.DataColumn(ft.Text(tr("Salary")), numeric=True),
                ft.DataColumn(ft.Text(tr("Yrs")), numeric=True), # Added Contract Years
                ft.DataColumn(ft.Text("PPG"), numeric=True), 
                ft.DataColumn(ft.Text("RPG"), numeric=True),
                ft.DataColumn(ft.Text("APG"), numeric=True),
                ft.DataColumn(ft.Text("SPG"), numeric=True), 
                ft.DataColumn(ft.Text("BPG"), numeric=True), 
                ft.DataColumn(ft.Text("2P%"), numeric=True),
                ft.DataColumn(ft.Text("3P%"), numeric=True),
            ]
        else:
            columns = [
                ft.DataColumn(ft.Text(tr("Pos"))),
                ft.DataColumn(ft.Text(tr("Name"))),
                ft.DataColumn(ft.Text(tr("OVR")), numeric=True),
                ft.DataColumn(ft.Text(tr("Age")), numeric=True),
                ft.DataColumn(ft.Text(tr("In")), numeric=True, tooltip=tr("Inside Scoring")),
                ft.DataColumn(ft.Text(tr("Out")), numeric=True, tooltip=tr("Outside Scoring")),
                ft.DataColumn(ft.Text(tr("Pas")), numeric=True, tooltip=tr("Passing")),
                ft.DataColumn(ft.Text(tr("Reb")), numeric=True, tooltip=tr("Rebound")),
                ft.DataColumn(ft.Text(tr("Def")), numeric=True, tooltip=tr("Defense")),
                ft.DataColumn(ft.Text(tr("Stl")), numeric=True, tooltip=tr("Steal")),
                ft.DataColumn(ft.Text(tr("Blk")), numeric=True, tooltip=tr("Block")),
                ft.DataColumn(ft.Text(tr("I.Q.")), numeric=True, tooltip=tr("Consistency")),
            ]

        rows = []
        for p in players:
            ovr_color = get_ovr_color(p.ovr)
            
            # Make Name Clickable
            name_cell = ft.DataCell(
                ft.Text(p.mask_name, color=ft.Colors.BLUE, weight=ft.FontWeight.BOLD),
                on_tap=lambda e, player=p: self.show_player_detail(player)
            )
            
            common_cells = [
                ft.DataCell(ft.Text(p.pos)),
                name_cell,
                ft.DataCell(ft.Container(
                    content=ft.Text(str(p.ovr), weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                    bgcolor=ovr_color,
                    padding=5,
                    border_radius=5,
                    width=40,
                    alignment=ft.Alignment(0, 0)
                )),
                ft.DataCell(ft.Text(str(p.age))),
            ]

            if self.view_mode == "stats":
                # Calculate Averages
                games = p.stats.get("games", 0)
                ppg = f"{(p.stats.get('pts', 0) / games):.1f}" if games > 0 else "0.0"
                rpg = f"{(p.stats.get('reb', 0) / games):.1f}" if games > 0 else "0.0"
                apg = f"{(p.stats.get('ast', 0) / games):.1f}" if games > 0 else "0.0"
                spg = f"{(p.stats.get('stl', 0) / games):.1f}" if games > 0 else "0.0"
                bpg = f"{(p.stats.get('blk', 0) / games):.1f}" if games > 0 else "0.0"
                m2, a2 = p.stats.get("2pm", 0), p.stats.get("2pa", 0)
                pct2 = f"{(m2/a2)*100:.1f}%" if a2 > 0 else "0.0%"
                m3, a3 = p.stats.get("3pm", 0), p.stats.get("3pa", 0)
                pct3 = f"{(m3/a3)*100:.1f}%" if a3 > 0 else "0.0%"
                
                rows.append(ft.DataRow(cells=common_cells + [
                    ft.DataCell(ft.Text(f"${p.salary:.1f}M")), # Salary 
                    ft.DataCell(ft.Text(str(p.contract_length), color=ft.Colors.RED if p.contract_length == 1 else None, weight=ft.FontWeight.BOLD if p.contract_length == 1 else None)), # Years

                    ft.DataCell(ft.Text(ppg)),
                    ft.DataCell(ft.Text(rpg)),
                    ft.DataCell(ft.Text(apg)),
                    ft.DataCell(ft.Text(spg)),
                    ft.DataCell(ft.Text(bpg)),
                    ft.DataCell(ft.Text(pct2)),
                    ft.DataCell(ft.Text(pct3)),
                ]))
            else:
                # Attributes
                attr = p.attributes
                rows.append(ft.DataRow(cells=common_cells + [
                    ft.DataCell(ft.Text(str(attr.two_pt))),
                    ft.DataCell(ft.Text(str(attr.three_pt))),
                    ft.DataCell(ft.Text(str(attr.passing))),
                    ft.DataCell(ft.Text(str(attr.rebound))),
                    ft.DataCell(ft.Text(str(attr.defense))),
                    ft.DataCell(ft.Text(str(attr.steal))),
                    ft.DataCell(ft.Text(str(attr.block))),
                    ft.DataCell(ft.Text(str(attr.consistency))),
                ]))

        self.content = ft.Column([
            ft.Row([
                # ft.Text(f"{tr('Player Roster')}: {team.name}", size=25, weight=ft.FontWeight.BOLD),
                ft.Text(tr('Player Roster'), size=25, weight=ft.FontWeight.BOLD),
                team_selector, # Added Selector
                ft.Container(expand=True),
                toggle
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ft.Divider(),
            ft.Row([
                ft.DataTable(
                    columns=columns,
                    rows=rows,
                    border=ft.border.all(1, ft.Colors.OUTLINE),
                    border_radius=10,
                    vertical_lines=ft.border.BorderSide(1, ft.Colors.OUTLINE),
                    horizontal_lines=ft.border.BorderSide(1, ft.Colors.OUTLINE),
                    column_spacing=15
                )
            ], scroll=ft.ScrollMode.AUTO)
        ], scroll=ft.ScrollMode.AUTO)

    def on_view_change(self, e):
        self.view_mode = list(e.control.selected)[0]
        self.build_content()
        self.update()
        


    def show_player_detail(self, player):
        dlg = PlayerDetailDialog(player)
        self.page.overlay.append(dlg)
        dlg.open = True
        self.page.update()
