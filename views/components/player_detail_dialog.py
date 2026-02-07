import flet as ft
from models.player import Player
from utils.localization import tr
from controllers.game_manager import GameManager

class PlayerDetailDialog(ft.AlertDialog):
    def __init__(self, player: Player, on_close=None, initial_tab="status", on_signed=None):
        super().__init__()
        self.player = player
        self.on_close_callback = on_close
        self.initial_tab = initial_tab
        self.on_signed_callback = on_signed
        
        self.title = ft.Text(f"{player.real_name} (#{player.pos})")
        self.modal = False
        self.on_dismiss = self.close_dialog
        self.actions = [
            ft.TextButton(tr("Close"), on_click=self.close_dialog)
        ]
        
        self.content = self.build_content()
        
    def build_content(self):
        p = self.player
        stats = p.stats
        attr = p.attributes
        
        # Helper to get color for attribute
        def attr_color(val):
            if val >= 85: return ft.Colors.PURPLE
            if val >= 75: return ft.Colors.BLUE
            if val >= 65: return ft.Colors.GREEN
            if val >= 50: return ft.Colors.ORANGE
            return ft.Colors.RED

        # Stats Processing
        games = stats.get("games", 0)
        ppg = f"{(stats.get('pts', 0) / games):.1f}" if games > 0 else "0.0"
        rpg = f"{(stats.get('reb', 0) / games):.1f}" if games > 0 else "0.0"
        apg = f"{(stats.get('ast', 0) / games):.1f}" if games > 0 else "0.0"
        fg_pct = f"{(stats.get('fgm', 0)/stats.get('fga', 1)*100):.1f}%" if stats.get('fga', 0) > 0 else "0.0%"
        three_pct = f"{(stats.get('3pm', 0)/stats.get('3pa', 1)*100):.1f}%" if stats.get('3pa', 0) > 0 else "0.0%"

        self.gm = GameManager() # Init GM for negotiation logic
        
        self.status_view = self._build_status_tab(p, attr, attr_color, ppg, rpg, apg, fg_pct, three_pct, games)
        self.history_view = self._build_history_tab(p)
        self.content_area = ft.Container(content=self.status_view, padding=10)

        # Define Close Button Early
        self.close_button = ft.TextButton(tr("Close"), on_click=self.close_dialog)

        self.contract_view = self._build_contract_tab(p)

        def on_tab_change(e):
             selection = e.control.selected
             if isinstance(selection, set):
                 sel_list = list(selection)
             else:
                 sel_list = list(selection)
                 
             is_contract = "contract" in sel_list
             
             if "history" in sel_list:
                 self.content_area.content = self.history_view
             elif is_contract:
                 self.content_area.content = self.contract_view
             else:
                 self.content_area.content = self.status_view
                 
             # Toggle Actions
             if is_contract:
                 self.actions = [self.close_button, self.offer_button]
             else:
                 self.actions = [self.close_button]
                 
             self.content_area.update()
             self.update() # Update Dialog to reflect action changes

        # Set initial content
        if self.initial_tab == "history":
            self.content_area.content = self.history_view
        elif self.initial_tab == "contract":
            self.content_area.content = self.contract_view
        else:
            self.content_area.content = self.status_view
            self.content_area.content = self.status_view

        return ft.Container(
            content=ft.Column([
                ft.Container(
                    content=ft.SegmentedButton(
                        selected=[self.initial_tab], 
                        on_change=on_tab_change,
                        segments=[
                            ft.Segment(value="status", label=ft.Text(tr("Status"))),
                            ft.Segment(value="history", label=ft.Text(tr("History"))),
                            ft.Segment(value="contract", label=ft.Text(tr("Contract")))
                        ]
                    ),
                    alignment=ft.Alignment(0,0)
                ),
                self.content_area
            ], scroll=ft.ScrollMode.AUTO),
            # removed fixed size for mobile responsiveness
            # width=500, height=600 
            expand=True 
        )

    def _update_projection(self, e=None):
        if not hasattr(self, "offer_amount_slider") or not self.offer_amount_slider: return
        
        p = self.player
        user_team_id = self.gm.user_team_id
        
        # Calculate Base Payroll
        current_payroll = self.gm.calculate_team_payroll(user_team_id)
        base_payroll = current_payroll
        if p.team_id == user_team_id:
             base_payroll -= p.salary

        offer = float(self.offer_amount_slider.value)
        new_payroll = base_payroll + offer
        space = self.gm.salary_cap - new_payroll
        
        # Count Roster Spots
        user_team_obj = self.gm.get_user_team()
        roster_count = len(user_team_obj.roster) if user_team_obj else 0
        
        # If signing a new FA, roster count increases. If renewing, it stays same.
        if p.team_id != user_team_id:
                roster_count += 1
        
        empty_slots = max(0, 10 - roster_count)
        reserve = empty_slots * 1.0 # 1M per empty slot
        
        # Update Text
        if space < 0:
            self.cap_projection_text.value = f"⚠️ {tr('DANGER')}: {tr('Space after signing')}: ${space:.1f}M ({tr('Over Cap')})"
            self.cap_projection_text.color = ft.Colors.RED
            self.cap_projection_text.weight = ft.FontWeight.BOLD
        elif space < reserve:
                self.cap_projection_text.value = f"⚠️ {tr('WARNING')}: {tr('Space after signing')}: ${space:.1f}M ({tr('Low Reserve')}: ${reserve}M needed)"
                self.cap_projection_text.color = ft.Colors.ORANGE
        else:
                self.cap_projection_text.value = f"✅ {tr('Projected Space')}: ${space:.1f}M"
                self.cap_projection_text.color = ft.Colors.GREEN
                
        # Determine Disabled State
        can_negotiate = True
        if p.team_id != "T00" and p.team_id != user_team_id: can_negotiate = False
        elif p.team_id == user_team_id and p.contract_length > 1: can_negotiate = False

        disabled_reason = ""
        is_disabled = False
        
        if not can_negotiate:
                is_disabled = True
                disabled_reason = "Cannot Negotiate"
        elif not getattr(p, "negotiation_allowed", True):
                is_disabled = True
                disabled_reason = "Refuses to Negotiate"
        elif space < 0:
                is_disabled = True
                disabled_reason = "Over Cap"
        
        # Apply State
        self.offer_button.disabled = is_disabled
        self.status_text.value = disabled_reason if is_disabled else "Ready to Offer"
        self.status_text.color = ft.Colors.RED if is_disabled else ft.Colors.GREEN
        
        if e is not None:
            self.cap_projection_text.update()
            self.offer_button.update()
            self.status_text.update()

    def _on_make_offer_click(self, e):
        try:
            p = self.player
            years = int(self.offer_years_slider.value)
            amount = float(self.offer_amount_slider.value)
            
            response = self.gm.negotiate_contract(p, amount, years)
            
            status = response["status"]
            msg = response["message"]
            
            # Update Patience
            current_patience = getattr(p, "negotiation_patience", 0)
            max_p_current = getattr(p, "negotiation_max_patience", 3)
            self.patience_text.value = f"{tr('Mood')}: " + ("❤️" * current_patience + "🖤" * (max_p_current - current_patience))
            
            if status == "accept":
                # Apply Contract Terms
                p.salary = amount
                p.contract_length = years
                
                # Execute Signing (If Free Agent)
                sign_success = True
                if p.team_id == "T00":
                    user_team = self.gm.get_user_team()
                    success, s_msg = self.gm.sign_player(p, user_team)
                    if not success:
                        sign_success = False
                        msg = f"已達成協議，但簽約失敗：{s_msg}"
                        status = "error" 
                
                if sign_success:
                    self.negotiation_result.value = f"✅ {tr('Agreed')}: {msg}"
                    self.negotiation_result.color = ft.Colors.GREEN
                    self.offer_button.disabled = True
                    self.offer_years_slider.disabled = True
                    self.offer_amount_slider.disabled = True
                    self.status_text.value = "報價已接受並完成簽約！"
                    
                    # Fire Callback
                    if self.on_signed_callback:
                        self.on_signed_callback()
                    
                    # Update Projection visually
                    self._update_projection(e)
                else:
                    self.negotiation_result.value = f"❌ {tr('ERROR')}: {msg}"
                    self.negotiation_result.color = ft.Colors.RED
                    self.status_text.value = "簽約失敗"
                
            elif status == "walk_away":
                    self.negotiation_result.value = f"❌ {tr('Refused')}: {msg}"
                    self.negotiation_result.color = ft.Colors.RED
                    self.offer_button.disabled = True
                    self.status_text.value = "談判破裂"
                    
            else:
                    self.negotiation_result.value = f"💬 {msg}"
                    self.negotiation_result.color = ft.Colors.AMBER
                    self.status_text.value = "請再提出新的報價..."
                    
            self.patience_text.update()
            self.negotiation_result.update()
            self.offer_button.update()
            self.status_text.update()
            self.offer_years_slider.update()
            self.offer_amount_slider.update()
            
        except Exception as ex:
            import traceback
            traceback.print_exc()
            self.negotiation_result.value = f"❌ ERROR: {str(ex)}"
            self.negotiation_result.color = ft.Colors.RED
            self.negotiation_result.update()

    def _build_contract_tab(self, p):
        # 1. Current Status
        fmv = self.gm.calculate_market_value(p)
        loyalty = min(20, p.years_on_team * 2)
        
        # --- VALIDATION (UI LOCK) ---
        user_team_id = self.gm.user_team_id
        can_negotiate = True
        lock_msg = ""
        
        if p.team_id != "T00" and p.team_id != user_team_id:
            can_negotiate = False
            lock_msg = f"🚫 {tr('Player is on another team')}"
        elif p.team_id == user_team_id and p.contract_length > 1:
            can_negotiate = False
            lock_msg = f"🔒 {tr('Contract valid for')} {p.contract_length} {tr('years')}"
        # ----------------------------

        # Init Patience for display
        patience = getattr(p, "negotiation_patience", 3)
        max_patience = getattr(p, "negotiation_max_patience", 3)
        # Fallback if max < patience (legacy/bug safe)
        max_patience = max(patience, max_patience) 
        
        patience_str = "❤️" * patience + "🖤" * (max_patience - patience)
        
        # UI Elements
        self.offer_years_slider = ft.Slider(min=1, max=5, divisions=4, value=1, label="{value} Yrs")
        
        # Dynamic Max: Max(15, FMV*1.5) to allow overpaying
        dynamic_max = max(15.0, fmv * 1.5)
        # 0.01 increments for "smooth" feel but discrete values for label stability
        steps = int(dynamic_max / 0.01) 
        
        self.offer_amount_text = ft.Text(f"${fmv:.1f}M", weight=ft.FontWeight.BOLD)

        # Dynamic Max: Max(15, FMV*1.5) to allow overpaying
        dynamic_max = max(15.0, fmv * 1.5)
        # 0.1 increments (Reduced updates)
        steps = int(dynamic_max / 0.1) 

        self.offer_amount_slider = ft.Slider(
            min=0.5, 
            max=dynamic_max, 
            divisions=steps, 
            value=fmv,
            expand=True # Allow slider to fill space
        )

        def modify_offer(delta):
            new_val = self.offer_amount_slider.value + delta
            new_val = max(0.5, min(dynamic_max, new_val))
            # Snap to 0.1
            new_val = round(new_val, 1)
            self.offer_amount_slider.value = new_val
            update_projection(None)
            self.offer_amount_slider.update()
            
        self.btn_minus = ft.IconButton(ft.Icons.REMOVE, on_click=lambda e: modify_offer(-0.1))
        self.btn_plus = ft.IconButton(ft.Icons.ADD, on_click=lambda e: modify_offer(0.1))
        self.negotiation_result = ft.Text("", size=16, weight=ft.FontWeight.BOLD)
        self.patience_text = ft.Text(f"{tr('Mood')}: {patience_str}", size=16)
        
        # Dynamic Cap Projection Logic
        current_payroll = self.gm.calculate_team_payroll(user_team_id)
        # If player is already on team, their current salary is in payroll. 
        # We need to subtract it to see the "Base" payroll before re-signing.
        base_payroll = current_payroll
        if p.team_id == user_team_id:
             base_payroll -= p.salary
             
        self.cap_projection_text = ft.Text("", size=14)

        def update_projection(e):
            offer = float(self.offer_amount_slider.value)
            new_payroll = base_payroll + offer
            space = self.gm.salary_cap - new_payroll
            
            # Count Roster Spots
            user_team_obj = self.gm.get_user_team()
            roster_count = len(user_team_obj.roster) if user_team_obj else 0
            
            # print(f"DEBUG: Negotiate - Space: {space}, Roster: {roster_count}, CanNeg: {can_negotiate}, Allowed: {getattr(p, 'negotiation_allowed', 'UNK')}")
            
            # Update Live Text (1 Decimal Place)
            self.offer_amount_text.value = f"${offer:.1f}M"
            
            # Count Roster Spots
            if p.team_id != user_team_id:
                 roster_count += 1
            
            empty_slots = max(0, 10 - roster_count)
            reserve = empty_slots * 1.0 # 1M per empty slot
            
            if space < 0:
                self.cap_projection_text.value = f"⚠️ {tr('DANGER')}: {tr('Space after signing')}: ${space:.2f}M ({tr('Over Cap')})"
                self.cap_projection_text.color = ft.Colors.RED
                self.cap_projection_text.weight = ft.FontWeight.BOLD
            elif space < reserve:
                 self.cap_projection_text.value = f"⚠️ {tr('WARNING')}: {tr('Space after signing')}: ${space:.2f}M ({tr('Low Reserve')}: ${reserve}M needed)"
                 self.cap_projection_text.color = ft.Colors.ORANGE
            else:
                 self.cap_projection_text.value = f"✅ {tr('Projected Space')}: ${space:.2f}M"
                 self.cap_projection_text.color = ft.Colors.GREEN
            # Determine Disabled State
            disabled_reason = ""
            is_disabled = False
            
            if not can_negotiate:
                 is_disabled = True
                 disabled_reason = "無法談判 (球隊/合約)"
            elif not getattr(p, "negotiation_allowed", True):
                 is_disabled = True
                 disabled_reason = "球員拒絕談判"
            elif space < 0:
                 is_disabled = True
                 disabled_reason = "薪資空間不足 (超過硬上限)"
            
            # Apply State
            self.offer_button.disabled = is_disabled
            self.status_text.value = disabled_reason if is_disabled else "準備報價"
            self.status_text.color = ft.Colors.RED if is_disabled else ft.Colors.GREEN
            
            # print(f"DEBUG: Negotiate - Reason: {disabled_reason}, Disabled: {is_disabled}")

            if e is not None:
                self.cap_projection_text.update()
                self.offer_amount_text.update()
                self.offer_button.update()
                self.status_text.update()

        self.offer_amount_slider.on_change = update_projection
        self.status_text = ft.Text("", size=12)
        
        def on_offer_click(e):
            print("DEBUG: BUTTON CLICKED")
            years = int(self.offer_years_slider.value)
            amount = float(self.offer_amount_slider.value)
            
            response = self.gm.negotiate_contract(p, amount, years)
            status = response["status"]
            msg = response["message"]
            
            # Update Patience Display
            current_patience = getattr(p, "negotiation_patience", 0)
            max_p_current = getattr(p, "negotiation_max_patience", 3)
            self.patience_text.value = f"{tr('Mood')}: " + ("❤️" * current_patience + "🖤" * (max_p_current - current_patience))
            
            if status == "accept":
                self.negotiation_result.value = f"✅ {tr('Agreed')}: {msg}"
                self.negotiation_result.color = ft.Colors.GREEN
                self.offer_button.disabled = True
                self.offer_years_slider.disabled = True
                self.offer_amount_slider.disabled = True
                
            elif status == "negotiate":
                self.negotiation_result.value = f"⚠️ {tr('REJECTED')}: {msg}"
                self.negotiation_result.color = ft.Colors.ORANGE
                
            elif status == "walk_away":
                 self.negotiation_result.value = f"🚫 {tr('WALKED AWAY')}: {msg}"
                 self.negotiation_result.color = ft.Colors.RED
                 # Lock everything
                 self.offer_years_slider.disabled = True
                 self.offer_amount_slider.disabled = True
                 e.control.disabled = True
        # Create Button
        self.offer_button = ft.ElevatedButton(
            tr("Make Offer"), 
            on_click=self._on_make_offer_click, 
            icon=ft.Icons.MONETIZATION_ON
        )
        
        
        
        # Add to Actions
        # self.close_button already defined in build_content
        self.actions = [
            self.close_button,
            self.offer_button
        ]
        
        # Initial Action State
        # If not starting on contract tab, hide offer button
        if self.initial_tab != "contract":
            self.actions = [self.close_button]
        
        # Trigger Initial Update
        self._update_projection(None)
        
        # Check Lockout Init
        if not getattr(p, "negotiation_allowed", True):
             self.offer_years_slider.disabled = True
             self.offer_amount_slider.disabled = True
             self.offer_button.disabled = True
             self.negotiation_result.value = "🚫 球員拒絕談判。"
             self.negotiation_result.color = ft.Colors.RED

        # Layout
        return ft.Container(
            content=ft.Column([
                ft.Text(tr("Contract Status"), size=20, weight=ft.FontWeight.BOLD),
                ft.Divider(),
                
                # Team Cap Info
                ft.Container(
                    content=ft.Row([
                        ft.Icon(ft.Icons.ACCOUNT_BALANCE_WALLET, color=ft.Colors.GREEN),
                        ft.Text(f"{tr('Team Cap')}: ", weight=ft.FontWeight.BOLD),
                        ft.Text(f"${self.gm.calculate_team_payroll(user_team_id):.1f}M / ${self.gm.salary_cap:.1f}M", 
                                color=ft.Colors.WHITE, size=16, weight=ft.FontWeight.BOLD),
                        ft.Text(f"({tr('Space')}: ${self.gm.salary_cap - self.gm.calculate_team_payroll(user_team_id):.1f}M)", 
                                color=ft.Colors.GREEN if (self.gm.salary_cap - self.gm.calculate_team_payroll(user_team_id)) > 0 else ft.Colors.RED)
                    ]),
                    bgcolor="#2B3345",
                    padding=10,
                    border_radius=5,
                    margin=ft.margin.only(bottom=10)
                ),

                ft.Row([
                    ft.Column([
                        ft.Text(f"{tr('Current Salary')}: ${p.salary:.2f}M"),
                        ft.Text(f"{tr('Years Left')}: {p.contract_length}"),
                        ft.Text(f"{tr('Years on Team')}: {p.years_on_team} ({loyalty}% Discount)"),
                    ]),
                    ft.Column([
                        ft.Text(f"{tr('Estimated Value')}: ${fmv:.2f}M", color=ft.Colors.AMBER),
                        self.patience_text
                    ])
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, wrap=True),
                
                ft.Divider(),
                ft.Text(tr("Negotiation Table"), size=18, weight=ft.FontWeight.BOLD),
                ft.Container(height=10),
                
                ft.Row([
                    ft.Text(tr("Offer Amount (Per Year)")),
                    self.offer_amount_text
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                
                ft.Row([
                    self.btn_minus,
                    self.offer_amount_slider,
                    self.btn_plus
                ], alignment=ft.MainAxisAlignment.CENTER),
                
                # Dynamic Cap Projection
                self.cap_projection_text,

                ft.Text(tr("Contract Length")),
                self.offer_years_slider,
                
                ft.Container(height=10),
                self.negotiation_result,
                self.status_text,
                
                ft.Container(height=20),
                
            ]),
            padding=10
        )

    def _build_status_tab(self, p, attr, attr_color, ppg, rpg, apg, fg_pct, three_pct, games):
        # Dynamic Defense Stat Logic
        def_stat_label = tr("Block_Attr")
        def_stat_val = attr.block
        if attr.steal > attr.block:
            def_stat_label = tr("Steal_Attr")
            def_stat_val = attr.steal

        return ft.Container(
            content=ft.Column([
            # Header Info
            ft.Row([
                ft.Container(
                    content=ft.Text(str(p.ovr), size=30, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                    bgcolor=self._get_ovr_color(p.ovr),
                    padding=10,
                    border_radius=8
                ),
                ft.Column([
                    ft.Text(f"{tr('Age')}: {p.age} | {tr('Height')}: -", size=14),
                    ft.Text(f"{tr('Salary')}: ${p.salary:.2f}M", size=14),
                ])
            ], spacing=20),
            
            ft.Divider(),
            
            # Attributes Grid
            ft.Text(tr("Attributes"), weight=ft.FontWeight.BOLD),
            ft.Row([
                self._build_attr_bar(tr("Inside"), attr.two_pt, attr_color(attr.two_pt)),
                self._build_attr_bar(tr("Outside"), attr.three_pt, attr_color(attr.three_pt)),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, wrap=True),
            ft.Row([
                self._build_attr_bar(tr("Rebound"), attr.rebound, attr_color(attr.rebound)),
                self._build_attr_bar(tr("Passing"), attr.passing, attr_color(attr.passing)),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, wrap=True),
            ft.Row([
                self._build_attr_bar(tr("Defense"), attr.defense, attr_color(attr.defense)),
                self._build_attr_bar(def_stat_label, def_stat_val, attr_color(def_stat_val)), 
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, wrap=True),
            
            ft.Divider(),
            
            # Season Stats
            ft.Text(f"{tr('Season Stats')} ({games} G)", weight=ft.FontWeight.BOLD),
            ft.Row([
                self._build_stat_box("PTS", ppg),
                self._build_stat_box("REB", rpg),
                self._build_stat_box("AST", apg),
            ], alignment=ft.MainAxisAlignment.SPACE_EVENLY, wrap=True),
            ft.Row([
                 self._build_stat_box("FG%", fg_pct),
                 self._build_stat_box("3P%", three_pct),
            ], alignment=ft.MainAxisAlignment.SPACE_EVENLY, margin=ft.margin.only(top=10), wrap=True)
            
            ]),
            padding=10
        )

    def _build_history_tab(self, p):
        # 1. Fetch History
        history_data = p.history.copy() if hasattr(p, "history") and p.history else []
        
        # 2. Add Current Season stats if played
        curr_games = p.stats.get("games", 0)
        # Even if games=0, we might want to show current season row?
        # User requested "Current Data", usually implies if available.
        if curr_games > 0:
            current_entry = p.stats.copy()
            current_entry["year"] = str(self.gm.season_year)
            current_entry["team_id"] = p.team_id
            history_data.append(current_entry)
            
        if not history_data:
             return ft.Container(content=ft.Text(tr("No history available.")), alignment=ft.Alignment(0, 0))

        columns = [
            ft.DataColumn(ft.Text(tr("Year"))),
            ft.DataColumn(ft.Text(tr("Team"))),
            ft.DataColumn(ft.Text(tr("GP")), numeric=True),
            ft.DataColumn(ft.Text("PTS"), numeric=True),
            ft.DataColumn(ft.Text("REB"), numeric=True),
            ft.DataColumn(ft.Text("AST"), numeric=True),
            ft.DataColumn(ft.Text("FG%"), numeric=True),
            ft.DataColumn(ft.Text("3P%"), numeric=True),
            ft.DataColumn(ft.Text("STL"), numeric=True),
            ft.DataColumn(ft.Text("BLK"), numeric=True),
        ]
        
        rows = []
        try:
            # Sort by Year (Descending)
            def parse_year(x):
                y = x.get("year", 0)
                if isinstance(y, str):
                    if y.isdigit(): return int(y)
                    # Handle text?
                    return 9999 
                return y

            sorted_hist = sorted(history_data, key=parse_year, reverse=True)
            
            for s in sorted_hist:
                g = s.get("games", 0)
                if g > 0:
                    ppg = f"{(s.get('pts', 0)/g):.1f}"
                    rpg = f"{(s.get('reb', 0)/g):.1f}"
                    apg = f"{(s.get('ast', 0)/g):.1f}"
                    stl = f"{(s.get('stl', 0)/g):.1f}"
                    blk = f"{(s.get('blk', 0)/g):.1f}"
                    
                    fga = s.get('fga', 0)
                    fgm = s.get('fgm', 0)
                    fg_pct = f"{(fgm/fga*100):.1f}%" if fga > 0 else "0.0%"
                    
                    tpa = s.get('3pa', 0)
                    tpm = s.get('3pm', 0)
                    tp_pct = f"{(tpm/tpa*100):.1f}%" if tpa > 0 else "0.0%"
                else:
                    ppg = rpg = apg = stl = blk = "0.0"
                    fg_pct = tp_pct = "0.0%"

                t_id = s.get("team_id", "N/A")
                team = self.gm.get_team(t_id)
                t_name = team.name if team else t_id
                
                # Check Current
                year_val = str(s.get("year", "N/A"))
                is_current = (year_val == str(self.gm.season_year))

                rows.append(ft.DataRow(cells=[
                    ft.DataCell(ft.Text(year_val, weight=ft.FontWeight.BOLD if is_current else ft.FontWeight.NORMAL)),
                    ft.DataCell(ft.Text(t_name)),
                    ft.DataCell(ft.Text(str(g))),
                    ft.DataCell(ft.Text(ppg)),
                    ft.DataCell(ft.Text(rpg)),
                    ft.DataCell(ft.Text(apg)),
                    ft.DataCell(ft.Text(fg_pct)),
                    ft.DataCell(ft.Text(tp_pct)),
                    ft.DataCell(ft.Text(stl)),
                    ft.DataCell(ft.Text(blk)),
                ]))
        except Exception as e:
            return ft.Container(content=ft.Text(f"Error loading history: {e}"), alignment=ft.Alignment(0, 0))

        return ft.Container(
            content=ft.Column([
                ft.Text("← 左右滑動查看數據 → (Scroll Horizontally)", size=12, color=ft.Colors.GREY_500, italic=True),
                ft.Row([
                    ft.DataTable(
                        columns=columns,
                        rows=rows,
                        border=ft.border.all(1, ft.Colors.OUTLINE),
                        vertical_lines=ft.border.BorderSide(1, ft.Colors.OUTLINE),
                        column_spacing=15,
                        data_row_min_height=40,
                    ) 
                ], scroll=ft.ScrollMode.AUTO)
            ]),
            padding=10
        )

    def _build_attr_bar(self, label, value, color):
        return ft.Column([
            ft.Row([ft.Text(label, size=12), ft.Text(str(value), size=12, weight=ft.FontWeight.BOLD)], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, width=125),
            ft.ProgressBar(value=value/100, color=color, bgcolor="#333333", width=125)
        ])

    def _build_stat_box(self, label, value):
        return ft.Container(
            content=ft.Column([
                ft.Text(label, size=12, color="#CCCCCC"),
                ft.Text(value, size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            padding=10,
            bgcolor="#1E2740",
            border_radius=5,
            width=80
        )

    def _get_ovr_color(self, ovr):
        if ovr >= 90: return ft.Colors.PURPLE
        if ovr >= 80: return ft.Colors.BLUE
        if ovr >= 70: return ft.Colors.GREEN
        if ovr >= 60: return ft.Colors.ORANGE
        return ft.Colors.RED
        
    def close_dialog(self, e):
        self.open = False
        if self.on_close_callback:
            self.on_close_callback()
        self.page.update()
