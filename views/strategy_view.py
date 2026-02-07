import flet as ft
from controllers.game_manager import GameManager

from utils.localization import tr

class StrategyView(ft.Container):
    # __init__ moved below
    def __init__(self):
        super().__init__()
        self.gm = GameManager()
        self.expand = True
        self.padding = 20
        self.content = ft.Column()
        self.current_team = None
        self.settings = {}
        # self.build_content() # Moved to on-demand

    def build_content(self):
        # Refresh Data (Fixes Stale Reference Bug)
        self.current_team = self.gm.get_user_team()
        if self.current_team:
            self.settings = self.current_team.strategy_settings
        else:
            self.settings = {}

        if not self.current_team:
            self.content.controls = [ft.Text(tr("No user team found."))]
            return
            
        print(f"DEBUG: StrategyView Loading. Team: {self.current_team.name}")
        print(f"DEBUG: Loaded Settings: {self.settings}")

        # 1. Team Tactics
        tactics_card = self._build_tactics_card()
        
        # 2. Scoring Options
        options_card = self._build_options_card()
        
        # 3. Rotation Management
        rotation_card = self._build_rotation_card()

        self.content = ft.Column(
            controls=[
                ft.Text(tr("Strategy & Gameplan"), size=30, weight=ft.FontWeight.BOLD),
                ft.Divider(),
                ft.Row([tactics_card, options_card], alignment=ft.MainAxisAlignment.START, vertical_alignment=ft.CrossAxisAlignment.START, wrap=True),
                ft.Divider(),
                ft.Text(tr("Rotation Management"), size=20, weight=ft.FontWeight.BOLD),
                ft.Text(tr("Adjust playing time and role for each player."), size=12, italic=True),
                ft.Row([rotation_card], scroll=ft.ScrollMode.AUTO),
                ft.Divider(),
                ft.Row([
                    ft.ElevatedButton(
                        tr("Settings Saved Automatically"), 
                        icon=ft.Icons.CHECK_CIRCLE, 
                        disabled=True
                    )
                ], alignment=ft.MainAxisAlignment.END)
            ],
            scroll=ft.ScrollMode.AUTO,
            expand=True
        )

    def _build_tactics_card(self):
        current_tactic = self.settings.get("tactics", "Balanced")
        
        radio_group = ft.RadioGroup(
            content=ft.Column([
                ft.Radio(value="Balanced", label=tr("Balanced (Default)")),
                ft.Radio(value="Inside", label=tr("Pound the Paint (Inside Focus)")),
                ft.Radio(value="Outside", label=tr("Let it Fly (Outside Focus)")),
                ft.Radio(value="Pace", label=tr("7 Seconds or Less (Pace)")),
            ]),
            value=current_tactic,
            on_change=self._on_tactic_change
        )
        
        return ft.Container(
            width=300,
            padding=15,
            border=ft.border.all(1, ft.Colors.OUTLINE),
            border_radius=10,
            content=ft.Column([
                ft.Text(tr("Team Tactics"), size=18, weight=ft.FontWeight.BOLD),
                radio_group
            ])
        )

    def _build_options_card(self):
        self.option_dropdowns = [] # Store references
        
        col_controls = [ft.Text(tr("Offensive Hierarchy"), size=18, weight=ft.FontWeight.BOLD)]
        
        current_opts = self.settings.get("scoring_options", [])
        # Ensure list structure
        if not isinstance(current_opts, list): current_opts = []
        while len(current_opts) < 3: current_opts.append(None)
            
        labels = [tr("1st Option (Go-to Guy)"), tr("2nd Option"), tr("3rd Option")]
        
        for idx in range(3):
            roster_options = [ft.dropdown.Option(text=tr("None"), key="None")]
            # Note: Player ID is str
            for p in self.current_team.roster:
                roster_options.append(ft.dropdown.Option(text=p.mask_name, key=str(p.id)))

            val = current_opts[idx]
            if val is None or val == "None": val = "None"
            
            # Verify ID validity
            if val != "None" and not any(str(p.id) == val for p in self.current_team.roster):
                val = "None"
                
            dd = ft.Dropdown(
                label=labels[idx],
                options=roster_options,
                value=val,
                width=250,
                text_size=14,
            )
            # Assign handler after initialization
            dd.on_change = lambda e, idx=idx: self._on_option_change_and_save(e, idx)
            self.option_dropdowns.append(dd)
            col_controls.append(dd)

        return ft.Container(
            padding=15,
            border=ft.border.all(1, ft.Colors.OUTLINE),
            border_radius=10,
            content=ft.Column(col_controls)
        )

    def _on_option_change_and_save(self, e, current_idx):
        self._on_option_change(e, current_idx)
        self._auto_save_settings()

    def _on_option_change(self, e, current_idx):
        """
        Prevents duplicate value selection across scoring options.
        If Player A is selected in Slot 1, remove them from Slot 2/3.
        """
        selected_val = e.control.value
        
        if selected_val == "None": return
        
        for idx, dd in enumerate(self.option_dropdowns):
            if idx == current_idx: continue
            
            # If conflict found (and not resolving to None already)
            if dd.value == selected_val:
                # Reset the conflicting dropdown to "None"
                dd.value = "None"
                dd.update()
                
                # Notify User
                if self.page:
                     self.page.snack_bar = ft.SnackBar(
                         content=ft.Text(tr("Player cannot be selected for multiple options. Reset conflicting slot.")),
                         bgcolor=ft.Colors.ORANGE,
                     )
                     self.page.snack_bar.open = True
                     self.page.update()

    def _build_rotation_card(self):
        self.rotation_dropdowns = {} # Map ID -> Dropdown
        rows = []
        rotation_map = self.settings.get("rotation_settings", {})
        if not rotation_map: rotation_map = {}
        
        for p in sorted(self.current_team.roster, key=lambda x: x.ovr, reverse=True):
            current_role = rotation_map.get(str(p.id), " ")
            
            role_dd = ft.Dropdown(
                width=100,
                options=[
                    ft.dropdown.Option("++", tr("++ Star")),
                    ft.dropdown.Option("+", tr("+ More")),
                    ft.dropdown.Option(" ", tr("Normal")),
                    ft.dropdown.Option("-", tr("- Less")),
                    ft.dropdown.Option("--", tr("-- Bench")),
                ],
                value=current_role,
                dense=True,
                content_padding=5,
            )
            role_dd.on_change = lambda e: self._auto_save_settings()
            self.rotation_dropdowns[str(p.id)] = role_dd
            
            rows.append(
                ft.DataRow(cells=[
                    ft.DataCell(ft.Text(f"{p.mask_name} ({p.pos})")),
                    ft.DataCell(ft.Text(str(p.ovr))),
                    ft.DataCell(role_dd),
                    ft.DataCell(ft.Text(f"${p.salary}M")),
                ])
            )
            
        return ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text(tr("Player"))),
                ft.DataColumn(ft.Text(tr("OVR")), numeric=True),
                ft.DataColumn(ft.Text(tr("Role/Minutes"))),
                ft.DataColumn(ft.Text(tr("Salary"))),
            ],
            rows=rows,
            heading_row_height=40,
            data_row_min_height=50,
        )

    def _on_tactic_change(self, e):
        self.settings["tactics"] = e.control.value
        self._auto_save_settings()

    def _on_save_click(self, e):
        # Legacy manual save button (now disabled/informational)
        self._auto_save_settings()

    def _auto_save_settings(self):
        """Compiles settings from UI elements and saves via GameManager."""
        print("DEBUG: Auto-Saving Strategy...")
        try:
            if not self.current_team:
                print("ERROR: No current team to save settings to.")
                return

            # 1. Update Scoring Options
            new_opts = []
            seen_players = set()
            
            for i, dd in enumerate(self.option_dropdowns):
                val = dd.value
                # Handle Flet "None" vs Python None
                if val == "None" or val is None:
                    new_opts.append(None)
                else:
                    if val in seen_players:
                        new_opts.append(None)
                        dd.value = "None"
                        dd.update()
                    else:
                        new_opts.append(val)
                        seen_players.add(val)
                        
            # 2. Update Rotation Settings from Dropdowns
            new_rot = {}
            for pid, dd in self.rotation_dropdowns.items():
                if dd.value:
                    new_rot[pid] = dd.value
                else:
                    new_rot[pid] = " " # Default
            
            # 3. Explicitly Update Team Dictionary
            self.settings["scoring_options"] = new_opts
            self.settings["rotation_settings"] = new_rot
            self.current_team.strategy_settings = self.settings # Ensure reference is updated
            
            print(f"DEBUG: Saving Scoring: {new_opts}")
            print(f"DEBUG: Saving Rotation Keys: {len(new_rot)}")

            # 4. Save to Disk
            success, msg = self.gm.save_game(1)
            
            if success:
                print(f"DEBUG: Auto-Saved Strategy: {msg}")
            else:
                print(f"ERROR: Save Failed: {msg}")
                
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"ERROR Saving Strategy: {e}")
