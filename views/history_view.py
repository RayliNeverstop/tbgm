import flet as ft
from controllers.game_manager import GameManager
from utils.localization import tr

class HistoryView(ft.Container):
    def __init__(self, page: ft.Page):
        super().__init__()
        self.app_page = page
        self.gm = GameManager()
        self.expand = True
        self.padding = 20
        self.build_content()

    def build_content(self):
        # Header
        header = ft.Row(
            [
                ft.Icon(ft.Icons.HISTORY_EDU, size=30, color=ft.Colors.AMBER),
                ft.Text(tr("League History"), size=30, weight=ft.FontWeight.BOLD)
            ],
            alignment=ft.MainAxisAlignment.CENTER
        )

        # Tabs
        self.content_area = ft.Container(expand=True)
        
        def set_tab(tab_name):
            # Update Button Styles
            self.history_btn.bgcolor = "#CFB28B" if tab_name == "history" else "#1E2740"
            self.history_btn.color = "#0b1120" if tab_name == "history" else "#E0E0E0"
            
            self.achievements_btn.bgcolor = "#CFB28B" if tab_name == "achievements" else "#1E2740"
            self.achievements_btn.color = "#0b1120" if tab_name == "achievements" else "#E0E0E0"
            
            self.hof_btn.bgcolor = "#CFB28B" if tab_name == "hof" else "#1E2740"
            self.hof_btn.color = "#0b1120" if tab_name == "hof" else "#E0E0E0"
            
            self.records_btn.bgcolor = "#CFB28B" if tab_name == "records" else "#1E2740"
            self.records_btn.color = "#0b1120" if tab_name == "records" else "#E0E0E0"
            
            if tab_name == "history":
                self.content_area.content = self._build_history_tab()
            elif tab_name == "achievements":
                self.content_area.content = self._build_achievements_tab()
            elif tab_name == "hof":
                self.content_area.content = self._build_hof_tab()
            elif tab_name == "records":
                self.content_area.content = self._build_records_tab()
            
            self.content_area.update()
            self.history_btn.update()
            self.achievements_btn.update()
            self.hof_btn.update()
            self.records_btn.update()

        self.history_btn = ft.ElevatedButton(tr("History"), on_click=lambda e: set_tab("history"), bgcolor="#CFB28B", color="#0b1120")
        self.achievements_btn = ft.ElevatedButton(tr("Achievements"), on_click=lambda e: set_tab("achievements"), bgcolor="#1E2740", color="#E0E0E0")
        self.hof_btn = ft.ElevatedButton(tr("Hall of Fame"), on_click=lambda e: set_tab("hof"), bgcolor="#1E2740", color="#E0E0E0")
        self.records_btn = ft.ElevatedButton(tr("Records"), on_click=lambda e: set_tab("records"), bgcolor="#1E2740", color="#E0E0E0")
        
        # Initialize Default
        self.content_area.content = self._build_history_tab()

        self.content = ft.Column(
            [
                header,
                ft.Row([self.history_btn, self.achievements_btn, self.hof_btn, self.records_btn], alignment=ft.MainAxisAlignment.CENTER, scroll=ft.ScrollMode.AUTO),
                ft.Divider(),
                self.content_area
            ],
            expand=True,
            scroll=ft.ScrollMode.AUTO
        )

    def _build_history_tab(self):
        columns = [
            ft.DataColumn(ft.Text(tr("Year"))),
            ft.DataColumn(ft.Text(tr("Champion"))),
            ft.DataColumn(ft.Text(tr("MVP"))),
            ft.DataColumn(ft.Text(tr("Finals MVP"))),
        ]

        rows = []
        # Sort history by year descending
        history = sorted(self.gm.league_history, key=lambda x: x["year"], reverse=True)
        
        if not history:
             rows.append(ft.DataRow([
                 ft.DataCell(ft.Text(tr("No history available yet."))),
                 ft.DataCell(ft.Text("")),
                 ft.DataCell(ft.Text("")),
                 ft.DataCell(ft.Text("")),
             ]))
        else:
             for entry in history:
                 rows.append(
                     ft.DataRow(
                         cells=[
                             ft.DataCell(ft.Text(str(entry.get("year", "N/A")))),
                             ft.DataCell(ft.Container(
                                 content=ft.Text(entry.get("champion", "N/A"), weight=ft.FontWeight.BOLD, color=ft.Colors.AMBER),
                                 bgcolor="#003460",
                                 padding=5,
                                 border_radius=5
                             )),
                             ft.DataCell(ft.Text(entry.get("mvp", "N/A"))),
                             ft.DataCell(ft.Text(entry.get("fmvp", "N/A"))),
                         ],
                         on_select_change=lambda e, ent=entry: self._show_history_details(ent)
                     )
                 )

        history_table = ft.DataTable(
            columns=columns,
            rows=rows,
            border=ft.border.all(1, ft.Colors.OUTLINE),
            vertical_lines=ft.border.all(1, ft.Colors.OUTLINE),
            horizontal_lines=ft.border.all(1, ft.Colors.OUTLINE),
            heading_row_color="#232F3E",
        )
        
        return ft.Row([history_table], scroll=ft.ScrollMode.AUTO, alignment=ft.MainAxisAlignment.CENTER)

    def _show_history_details(self, entry):
        """Shows a dialog with full season history."""
        year = entry.get("year", "N/A")
        champion = entry.get("champion", "N/A")
        record = entry.get("champion_record", "N/A")
        mvp = entry.get("mvp", "N/A")
        fmvp = entry.get("fmvp", "N/A")
        all_league = entry.get("all_league", [])
        
        # Build All-League List
        all_league_controls = []
        if all_league:
            all_league_controls.append(ft.Text(tr("First Team All-League"), weight=ft.FontWeight.BOLD, size=16))
            for p in all_league:
                all_league_controls.append(
                    ft.Row([
                        ft.Text(p.get("pos", "?"), weight=ft.FontWeight.BOLD, color=ft.Colors.AMBER),
                        ft.Text(p.get("name", "N/A"))
                    ])
                )
        else:
            all_league_controls.append(ft.Text(tr("No All-League data available for this season."), italic=True, color=ft.Colors.GREY))

        content = ft.Column([
            ft.Row([
                ft.Icon(ft.Icons.EMOJI_EVENTS, color=ft.Colors.AMBER, size=40),
                ft.Text(f"Season {year} Review", size=24, weight=ft.FontWeight.BOLD)
            ], alignment=ft.MainAxisAlignment.CENTER),
            ft.Divider(),
            ft.Text(f"Champion: {champion}", size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.AMBER),
            ft.Text(f"Record: {record}", size=16),
            ft.Divider(),
            ft.Text(f"MVP: {mvp}", size=16),
            ft.Text(f"Finals MVP: {fmvp}", size=16),
            ft.Divider(),
            ft.Column(all_league_controls),
        ], scroll=ft.ScrollMode.AUTO)
        
        dlg = ft.AlertDialog(
            title=ft.Text(tr("Season History")),
            content=ft.Container(content=content, width=400, height=400),
            actions=[
                ft.TextButton(tr("Close"), on_click=lambda e: self.app_page.close_dialog())
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        
        self.app_page.dialog = dlg
        dlg.open = True
        self.app_page.update()

    def _build_achievements_tab(self):
        from controllers.game_manager import ACHIEVEMENT_DEFINITIONS
        
        user_achievements = getattr(self.gm, "achievements", {})
        
        items = []
        for key, def_data in ACHIEVEMENT_DEFINITIONS.items():
            is_unlocked = key in user_achievements
            unlock_data = user_achievements.get(key, {})
            
            # Styling
            bg_color = "#1E2740" if is_unlocked else "#0b1120"
            border_color = ft.Colors.AMBER if is_unlocked else ft.Colors.GREY_800
            icon_color = ft.Colors.AMBER if is_unlocked else ft.Colors.GREY_700
            text_color = ft.Colors.WHITE if is_unlocked else ft.Colors.GREY_600
            
            title = def_data["title"]
            desc = def_data["description"]
            date_str = f"Unlocked: {unlock_data.get('date', 'N/A')}" if is_unlocked else "Locked"
            
            icon_name = def_data.get("icon", "STAR")
            # Flet icon lookup
            icon_code = getattr(ft.Icons, icon_name, ft.Icons.STAR)

            items.append(
                ft.Container(
                    content=ft.Column([
                        ft.Icon(icon_code, color=icon_color, size=40),
                        ft.Text(tr(title), size=16, weight=ft.FontWeight.BOLD, color=text_color, text_align=ft.TextAlign.CENTER),
                        ft.Text(tr(desc), size=12, color=ft.Colors.GREY_500 if is_unlocked else ft.Colors.GREY_800, text_align=ft.TextAlign.CENTER),
                        ft.Text(date_str, size=10, italic=True, color=ft.Colors.GREY_400 if is_unlocked else ft.Colors.GREY_800)
                    ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    bgcolor=bg_color,
                    border_radius=10,
                    padding=20,
                    width=200,
                    height=200,
                    border=ft.border.all(1, border_color)
                )
            )

        return ft.GridView(
            controls=items,
            runs_count=5,
            max_extent=220,
            child_aspect_ratio=1.0,
            spacing=10,
            run_spacing=10
        )

    def _build_hof_tab(self):
        hof_list = getattr(self.gm, 'hall_of_fame', [])
        
        if not hof_list:
            return ft.Container(
                content=ft.Column([
                    ft.Icon(ft.Icons.BLOCK, size=50, color=ft.Colors.GREY),
                    ft.Text(tr("No Hall of Fame inductees yet."), size=20, color=ft.Colors.GREY)
                ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                alignment=ft.Alignment(0, 0),
                expand=True
            )
            
        items = []
        for entry in hof_list:
            card = ft.Container(
                content=ft.Column([
                    ft.Row([
                         ft.Icon(ft.Icons.MILITARY_TECH, color=ft.Colors.AMBER),
                         ft.Text(entry.get('name', 'Unknown'), size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.AMBER),
                    ], alignment=ft.MainAxisAlignment.CENTER),
                    ft.Text(f"Inducted: {entry.get('year', 'Unknown')}", size=12, italic=True),
                    ft.Text(entry.get('pos', '??'), size=14, weight=ft.FontWeight.BOLD),
                    ft.Divider(height=10, color=ft.Colors.WHITE24),
                    ft.Text(entry.get('stats', ''), size=12, text_align=ft.TextAlign.CENTER),
                    ft.Text(f"Score: {entry.get('score', 0)}", size=10, color=ft.Colors.GREY),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                bgcolor="#1E2740",
                padding=15,
                border_radius=10,
                border=ft.border.all(1, ft.Colors.AMBER),
                width=220,
                height=180,
            )
            items.append(card)
            
        return ft.Container(
            content=ft.Row(items, wrap=True, scroll=ft.ScrollMode.AUTO, alignment=ft.MainAxisAlignment.START),
            padding=20,
            expand=True
        )

    def _build_records_tab(self):
        records = getattr(self.gm, "league_records", {})
        
        # Convert to list for DataTable
        start_rows = []
        
        # Order: Points, Rebounds, Assists, Steals, Blocks, 3PM
        order = ["Points", "Rebounds", "Assists", "Steals", "Blocks", "3PM"]
        
        for key in order:
            rec = records.get(key)
            if not rec: continue
            
            # Record Row
            # Val | Type | Holder | Team | Date
            val = rec.get("val", 0)
            holder = rec.get("holder", "N/A")
            team = rec.get("team", "N/A")
            date = rec.get("date", "N/A")
            
            start_rows.append(
                ft.DataRow([
                    ft.DataCell(ft.Text(key, weight=ft.FontWeight.BOLD, size=16)),
                    ft.DataCell(ft.Container(
                        content=ft.Text(str(val), weight=ft.FontWeight.BOLD, size=18, color=ft.Colors.AMBER),
                        bgcolor="#003460", padding=5, border_radius=5
                    )),
                    ft.DataCell(ft.Text(holder, size=16)),
                    ft.DataCell(ft.Text(team)),
                    ft.DataCell(ft.Text(date)),
                ])
            )

        return ft.Container(
            content=ft.Column([
                ft.Text(tr("Single Game Records"), size=24, weight=ft.FontWeight.BOLD),
                ft.DataTable(
                    columns=[
                        ft.DataColumn(ft.Text(tr("Record"))),
                        ft.DataColumn(ft.Text(tr("Value")), numeric=True),
                        ft.DataColumn(ft.Text(tr("Holder"))),
                        ft.DataColumn(ft.Text(tr("Team"))),
                        ft.DataColumn(ft.Text(tr("Date"))),
                    ],
                    rows=start_rows,
                    border=ft.border.all(1, ft.Colors.OUTLINE),
                    vertical_lines=ft.border.BorderSide(1, ft.Colors.OUTLINE),
                    horizontal_lines=ft.border.BorderSide(1, ft.Colors.OUTLINE),
                    heading_row_color="#1E2740",
                )
            ]),
            padding=20
        )
