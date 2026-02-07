import flet as ft
from controllers.game_manager import GameManager
from controllers.trade_manager import TradeManager
from models.player import Player

from utils.localization import tr
from views.components.player_detail_dialog import PlayerDetailDialog

class TradeView(ft.Container):
    def __init__(self):
        super().__init__()
        self.gm = GameManager()
        self.tm = TradeManager()
        self.padding = 20
        self.expand = True
        
        # State
        self.target_team_id = None
        self.user_assets = []
        self.target_assets = []
        
        # Placeholder for controls (will be created in build_content)
        self.user_list = None
        self.target_list = None
        self.target_dropdown = None
        self.status_text = None
        
        self.build_content()
        
    def build_content(self):
        user_team = self.gm.get_user_team()
        if not user_team:
            self.content = ft.Text(tr("No User Team found!"))
            return

        # Initialize Controls Freshly
        self.status_text = ft.Text("", size=16)
        self.cap_space_text = ft.Text("", size=14, weight=ft.FontWeight.BOLD)
        self.user_list = ft.Column(scroll=ft.ScrollMode.AUTO, height=300)
        self.target_list = ft.Column(scroll=ft.ScrollMode.AUTO, height=300)
        
        self.target_dropdown = ft.Dropdown(
            label=tr("Select Trading Partner")
        )
        self.target_dropdown.on_change = self._on_target_team_change

        # Setup Team Dropdown Options
        options = []
        for t in self.gm.teams:
            if t.id != user_team.id and t.id != "T00": 
                options.append(ft.dropdown.Option(t.id, t.name))
        
        self.target_dropdown.options = options
        
        # Setup User Assets List
        self._refresh_user_list()
        
        self.offers_container = ft.Column() # Fallback for displaying offers

        self.content = ft.Column([
            ft.Text(tr("Trade Center"), size=30, weight=ft.FontWeight.BOLD),
            ft.Divider(),
            
            ft.Row([
                # Left Side: User Team
                ft.Column([
                    ft.Text(f"{tr('Your Team')}: {user_team.name}", size=20, weight=ft.FontWeight.BOLD),
                    ft.Container(
                        content=self.user_list,
                        border=ft.border.all(1, ft.Colors.OUTLINE),
                        border_radius=10,
                        padding=10,
                        width=400
                    )
                ]),
                
                # ft.VerticalDivider(width=20),
                
                # Right Side: Target Team
                ft.Column([
                    ft.Row([
                        self.target_dropdown,
                        ft.IconButton(icon=ft.Icons.REFRESH, tooltip=tr("Load Roster"), on_click=self._on_load_roster_click)
                    ]),
                    self.cap_space_text,
                    ft.Container(
                        content=self.target_list,
                        border=ft.border.all(1, ft.Colors.OUTLINE),
                        border_radius=10,
                        padding=10,
                        width=400
                    )
                ]),
            ], alignment=ft.MainAxisAlignment.CENTER, wrap=True),
            
            ft.Divider(),
            ft.Row([
                ft.ElevatedButton(
                    tr("Evaluate & Execute Trade"), 
                    icon=ft.Icons.SWAP_HORIZ,
                    style=ft.ButtonStyle(bgcolor=ft.Colors.GREEN_700, color=ft.Colors.WHITE),
                    on_click=self._on_trade_click
                ),
                ft.Container(width=20),
                ft.ElevatedButton(
                    tr("Find Deals (AI)"),
                    icon=ft.Icons.SEARCH,
                    style=ft.ButtonStyle(bgcolor=ft.Colors.BLUE_700, color=ft.Colors.WHITE),
                    on_click=self._on_find_deals_click
                )
            ], alignment=ft.MainAxisAlignment.CENTER),
            ft.Container(height=10),
            self.status_text,
            ft.Divider(),
            self.offers_container
        ], scroll=ft.ScrollMode.AUTO)

    def _on_load_roster_click(self, e):
        print("DEBUG: Manual Load Roster Clicked")
        if self.target_dropdown.value:
            self.target_team_id = self.target_dropdown.value
            self.target_assets = []
            try:
                self._refresh_target_list()
                self._update_status_preview()
                self.target_list.update()
                print("DEBUG: Target List Updated Manually")
            except Exception as ex:
                print(f"ERROR in manual load: {ex}")
        else:
             print("DEBUG: No team selected in dropdown")

    def _create_player_item(self, p, on_change_handler, is_checked):
        def on_name_click(e):
            if not self.page: return
            dlg = PlayerDetailDialog(p)
            self.page.overlay.append(dlg)
            dlg.open = True
            self.page.update()

        return ft.Container(
            content=ft.Row([
                ft.Checkbox(value=is_checked, data=p, on_change=on_change_handler),
                ft.TextButton(f"{p.mask_name} ({p.ovr})", on_click=on_name_click, style=ft.ButtonStyle(padding=0)),
                ft.Container(expand=True),
                ft.Text(f"${p.salary:.2f}M", size=12, color=ft.Colors.GREEN_200 if p.salary > 15 else ft.Colors.WHITE70),
                ft.Text(f"{p.pos}", size=12, color=ft.Colors.GREY)
            ], alignment=ft.MainAxisAlignment.START, spacing=5),
            padding=0,
            height=30
        )

    def _refresh_user_list(self):
        self.user_list.controls.clear()
        user_team = self.gm.get_user_team()
        if user_team:
            # 1. Players
            self.user_list.controls.append(ft.Text(tr("Players"), weight=ft.FontWeight.BOLD, size=14, color=ft.Colors.WHITE))
            for p in user_team.roster:
                self.user_list.controls.append(
                    self._create_player_item(p, self._on_user_asset_change, p in self.user_assets)
                )

            # 2. Draft Picks
            if user_team.draft_picks:
                self.user_list.controls.append(ft.Container(height=10))
                self.user_list.controls.append(ft.Text(tr("Draft Picks"), weight=ft.FontWeight.BOLD, size=14, color=ft.Colors.AMBER))
                
                # Sort picks: Year asc, Round asc
                sorted_picks = sorted(user_team.draft_picks, key=lambda x: (x['year'], x['round']))
                
                for pick in sorted_picks:
                     # Check if picked
                     is_picked = any(a == pick for a in self.user_assets) 
                     self.user_list.controls.append(
                         self._create_pick_item(pick, self._on_user_asset_change, is_picked)
                     )

    def _create_pick_item(self, pick, on_change_handler, is_checked):
         # Resolve original owner name if possible
         orig_team = self.gm.get_team(pick.get('original_owner_id', ''))
         orig_name = orig_team.name if orig_team else "Unknown"
         
         desc = f"{pick['year']} Round {pick['round']} ({orig_name})"
         return ft.Container(
             content=ft.Row([
                 ft.Checkbox(value=is_checked, data=pick, on_change=on_change_handler),
                 ft.Text(desc, size=13, color=ft.Colors.AMBER_100)
             ]),
             height=30,
             padding=ft.padding.only(left=5)
         )

    def _on_user_asset_change(self, e):
        asset = e.control.data
        if e.control.value:
            if asset not in self.user_assets:
                self.user_assets.append(asset)
        else:
            # Handles both Player object and Dict equality
            if asset in self.user_assets:
                self.user_assets.remove(asset)
        self._update_status_preview()

    def _on_target_team_change(self, e):
        print(f"DEBUG: Target Team Changed to {e.control.value}")
        self.target_team_id = e.control.value
        self.target_assets = [] # Clear selection
        try:
            self._refresh_target_list()
            self._update_status_preview()
            self.target_list.update()
        except Exception as ex:
            print(f"ERROR in target change: {ex}")

    def _refresh_target_list(self):
        self.target_list.controls.clear()
        if not self.target_team_id:
             self.target_list.controls.append(ft.Text(tr("Select a team."), italic=True))
             self.cap_space_text.value = ""
             return
            
        target_team = self.gm.get_team(self.target_team_id)
        if target_team:
             # Update Cap Space
             payroll = sum(p.salary for p in target_team.roster)
             cap_space = self.gm.salary_cap - payroll
             color = ft.Colors.GREEN if cap_space > 0 else ft.Colors.RED
             self.cap_space_text.value = f"{tr('Cap Space')}: ${cap_space:.2f}M"
             self.cap_space_text.color = color
             
             self.target_list.controls.append(ft.Text(tr("Players"), weight=ft.FontWeight.BOLD, size=14, color=ft.Colors.WHITE))
             
             for p in target_team.roster:
                self.target_list.controls.append(
                    self._create_player_item(p, self._on_target_asset_change, p in self.target_assets)
                )
             
             # Draft Picks
             if target_team.draft_picks:
                self.target_list.controls.append(ft.Container(height=10))
                self.target_list.controls.append(ft.Text(tr("Draft Picks"), weight=ft.FontWeight.BOLD, size=14, color=ft.Colors.AMBER))
                
                sorted_picks = sorted(target_team.draft_picks, key=lambda x: (x['year'], x['round']))
                for pick in sorted_picks:
                     is_picked = any(a == pick for a in self.target_assets)
                     self.target_list.controls.append(
                         self._create_pick_item(pick, self._on_target_asset_change, is_picked)
                     )
        else:
            self.target_list.controls.append(ft.Text(tr("Team not found."), color=ft.Colors.RED))

    def _on_target_asset_change(self, e):
        player = e.control.data
        if e.control.value:
            if player not in self.target_assets:
                self.target_assets.append(player)
        else:
            if player in self.target_assets:
                self.target_assets.remove(player)
        self._update_status_preview()
        
    def _update_status_preview(self):
        salary_out = sum(p.salary for p in self.user_assets if isinstance(p, Player))
        salary_in = sum(p.salary for p in self.target_assets if isinstance(p, Player))
        
        picks_out = sum(1 for p in self.user_assets if isinstance(p, dict))
        picks_in = sum(1 for p in self.target_assets if isinstance(p, dict))
        
        info = f"{tr('Selected: Out')} ${salary_out:.2f}M"
        if picks_out > 0: info += f" + {picks_out} Picks"
        
        info += f" | {tr('In')} ${salary_in:.2f}M"
        if picks_in > 0: info += f" + {picks_in} Picks"
        
        self.status_text.value = info
        self.status_text.color = ft.Colors.WHITE
        self.status_text.update()

    def _on_trade_click(self, e):
        print("DEBUG: Trade Clicked")
        user_team = self.gm.get_user_team()
        target_team = self.gm.get_team(self.target_team_id)
        
        if not user_team or not target_team:
            self.status_text.value = tr("Please select a target team.")
            self.status_text.color = ft.Colors.RED
            self.status_text.update()
            return

        if not self.user_assets and not self.target_assets:
            self.status_text.value = tr("Please select players to trade.")
            self.status_text.color = ft.Colors.RED
            self.status_text.update()
            return
            
        # 1. Validate Rules (Salary, Cap, Roster)
        try:
            valid, msg = self.tm.validate_trade(user_team, self.user_assets, target_team, self.target_assets)
            if not valid:
                self.status_text.value = f"{tr('Rule Violation')}: {msg}"
                self.status_text.color = ft.Colors.RED
                self.status_text.update()
                return
                
            # 2. Evaluate Fairness (AI)
            fair, reason = self.tm.evaluate_fairness(self.user_assets, self.target_assets, target_team.roster)
            if not fair:
                self.status_text.value = f"{tr('Trade Rejected')}: {reason}"
                self.status_text.color = ft.Colors.RED
                self.status_text.update()
                return
                
            # 3. Execute
            self.tm.execute_trade(user_team, self.user_assets, target_team, self.target_assets)
            self.status_text.value = tr("Trade Accepted! Transaction Complete.")
            self.status_text.color = ft.Colors.GREEN
            self.status_text.update()
            
            # Reset selection
            self.user_assets = []
            self.target_assets = []
            self.build_content() # Rebuild to refresh lists
            self.update()
        except Exception as ex:
             print(f"ERROR inside Trade Click: {ex}")
             self.status_text.value = f"Error: {ex}"
             self.status_text.update()

    def _on_find_deals_click(self, e):
        print("DEBUG: Find Deals Clicked")
        self.offers_container.controls.clear() # Clear old offers
        
        user_team = self.gm.get_user_team()
        if not self.user_assets:
            self.status_text.value = tr("Please select assets to trade first.")
            self.status_text.color = ft.Colors.RED
            self.status_text.update()
            return

        self.status_text.value = tr("Searching for trades...")
        self.status_text.color = ft.Colors.BLUE
        self.status_text.update()

        try:
            print("DEBUG: Calling find_potential_trades")
            offers = self.tm.find_potential_trades(user_team, self.user_assets)
            print(f"DEBUG: Offers found: {len(offers)}")
            
            if not offers:
                self.status_text.value = tr("No matching trades found (AI rejected or Salary mismatch).")
                self.status_text.color = ft.Colors.ORANGE
                self.status_text.update()
                return

            # Fallback Display in View
            self.offers_container.controls.append(ft.Text(f"{tr('Found')} {len(offers)} {tr('Offers')}:", size=20, weight=ft.FontWeight.BOLD))
            
            # Helper to generate accept callback
            def make_accept_func(off):
                return lambda e: self._accept_offer_action(off)

            for offer in offers:
                team = offer['team']
                assets = offer['assets']
                asset_names = ", ".join([f"{p.mask_name} ({p.ovr})" for p in assets])
                msg = offer.get('reason', '')
                total_salary = sum(p.salary for p in assets)
                
                self.offers_container.controls.append(
                    ft.Container(
                        content=ft.Row([
                            ft.Column([
                                ft.Text(f"{tr('Offer from')} {team.name}", weight=ft.FontWeight.BOLD),
                                ft.Text(f"{tr('Receiving')}: {asset_names} | {tr('Salary')}: ${total_salary:.2f}M"),
                                ft.Text(f"{msg}", size=12, italic=True)
                            ]),
                            ft.ElevatedButton(tr("Accept"), on_click=make_accept_func(offer))
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        padding=10,
                        border=ft.border.all(1, ft.Colors.OUTLINE),
                        border_radius=5
                    )
                )
            
            self.offers_container.update()

            # Still try to show Dialog as well
            self._show_offers_dialog(offers)
        except Exception as ex:
            print(f"ERROR inside Find Deals: {ex}")
            import traceback
            traceback.print_exc()
            self.status_text.value = f"Error: {ex}"
            self.status_text.color = ft.Colors.RED
            self.status_text.update()

    def _accept_offer_action(self, offer):
        team = offer['team']
        target_assets = offer['assets']
        user_team = self.gm.get_user_team()
        
        self.tm.execute_trade(user_team, self.user_assets, team, target_assets)
        self.status_text.value = tr("Trade Accepted! Transaction Complete.")
        self.status_text.color = ft.Colors.GREEN
        self.status_text.update()
        
        # Reset UI
        self.user_assets = []
        self.target_assets = []
        self.offers_container.controls.clear()
        
        if self.page.dialog:
            self.page.dialog.open = False
            
        self.build_content()
        self.update()

    def _show_offers_dialog(self, offers):
        # Create a list of offers vertically
        offer_controls = []
        
        def accept_offer(e):
            offer = e.control.data
            self._accept_offer_action(offer)

        def close_dlg(e):
            self.dlg.open = False
            self.page.update()

        for i, offer in enumerate(offers):
            team = offer['team']
            assets = offer['assets']
            asset_names = ", ".join([f"{p.mask_name} ({p.ovr})" for p in assets])
            msg = offer.get('reason', '')
            total_salary = sum(p.salary for p in assets)
            
            offer_controls.append(
                ft.Container(
                    content=ft.Column([
                        ft.Text(f"{tr('Offer from')} {team.name}", weight=ft.FontWeight.BOLD),
                        ft.Text(f"{tr('Receiving')}: {asset_names}"),
                        ft.Text(f"{tr('Salary')}: ${total_salary:.2f}M | {msg}", size=12, italic=True),
                        ft.ElevatedButton(tr("Accept Offer"), data=offer, on_click=accept_offer)
                    ]),
                    padding=10,
                    border=ft.border.all(1, ft.Colors.OUTLINE),
                    border_radius=5
                )
            )
            offer_controls.append(ft.Container(height=10))

        self.dlg = ft.AlertDialog(
            title=ft.Text(tr("Trade Offers")),
            content=ft.Container(
                content=ft.Column(offer_controls, scroll=ft.ScrollMode.AUTO),
                width=400,
                height=500
            ),
            actions=[
                ft.TextButton(tr("Cancel"), on_click=close_dlg)
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        
        # Use legacy dialog assignment for compatibility
        self.page.dialog = self.dlg
        self.dlg.open = True
        self.page.update()
