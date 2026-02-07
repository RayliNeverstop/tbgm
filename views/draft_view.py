import flet as ft
from controllers.game_manager import GameManager
from utils.localization import tr

class DraftView(ft.Container):
    def __init__(self, page: ft.Page, on_draft_end=None):
        super().__init__()
        self.expand = True
        self.gm = GameManager()
        self.main_page = page
        self.on_draft_end = on_draft_end
        
        # --- REPAIR LOGIC ---
        # If Draft Active but Data Missing (e.g. Broken Save), Repair it.
        if self.gm.is_draft_active:
             if not self.gm.draft_order or not self.gm.draft_class:
                 print("DEBUG: Draft Active but Data Missing. Repairing...")
                 self.gm.init_draft() # Re-run initialization
        # --------------------

        self.current_pick_text = ft.Text("Round 1 Pick 1", size=24, weight=ft.FontWeight.BOLD)
        
        # Log List
        self.log_list = ft.ListView(expand=True, spacing=5, auto_scroll=True)
        self.upcoming_list = ft.ListView(expand=True, spacing=5)
        
        # Rookie Header
        self.rookie_header = ft.Container(
             content=ft.Row([
                 ft.Text("球員", width=110, weight=ft.FontWeight.BOLD),
                 ft.Text("位置", width=40, weight=ft.FontWeight.BOLD), # Pos
                 ft.Text("年齡", width=40, weight=ft.FontWeight.BOLD), # Age
                 ft.Text("OVR", width=40, weight=ft.FontWeight.BOLD),
                 ft.Text("潛力", width=40, weight=ft.FontWeight.BOLD), # Pot
                 ft.Text("操作", width=70, weight=ft.FontWeight.BOLD), # Action
             ]),
             padding=5,
             bgcolor="#1E2740", # Dark Navy
             border=ft.border.all(1, "#3E4760")
        )
        self.rookie_list_view = ft.ListView(expand=True, spacing=2)

        # Build Layout
        
        # Build Layout
        try:
            print("DEBUG: Building DraftView Layout...")
            
            # --- DEBUG TEXT START ---
            self.debug_text = ft.Text("Initializing Draft View...", color=ft.Colors.RED, size=20)
            # --- DEBUG TEXT END ---
            
            # Define Buttons First
            self.btn_next = ft.ElevatedButton("下一順位 (Next Pick)", on_click=self._on_next_pick, icon="play_arrow")
            self.btn_sim = ft.ElevatedButton("模擬至玩家 (Sim to User)", on_click=self._on_sim_to_user, icon="fast_forward")
            
            # Manual Tab Buttons (Replacing ft.Tabs due to API issues)
            self.tab_live_btn = ft.ElevatedButton("實況 (Live)", on_click=lambda e: self._switch_tab("live"))
            self.tab_pool_btn = ft.ElevatedButton("待選 (Pool)", on_click=lambda e: self._switch_tab("pool"))
            
            # Initial Style (Live Selected)
            self.tab_live_btn.bgcolor = ft.Colors.PRIMARY
            self.tab_live_btn.color = ft.Colors.ON_PRIMARY
            self.tab_pool_btn.bgcolor = "#3E4760"
            self.tab_pool_btn.color = "#E0E0E0"
            
            self.tab_content_area = ft.Container(content=self._build_live_view(), expand=True)

            self.content = ft.Column([
                self.debug_text,
                # Header Container
                ft.Container(
                    content=ft.Column([
                        ft.Text("選秀大會 (Offseason Draft)", size=24, weight=ft.FontWeight.BOLD),
                        self.current_pick_text,
                        ft.Row([
                            self.btn_next,
                            self.btn_sim
                        ], alignment=ft.MainAxisAlignment.START, spacing=10, scroll=ft.ScrollMode.HIDDEN) 
                    ]),
                    padding=10,
                    bgcolor="#1E2740",
                    border_radius=10
                ),
                
                # Tab Control Row
                ft.Row([self.tab_live_btn, self.tab_pool_btn], alignment=ft.MainAxisAlignment.CENTER, spacing=20),
                
                # Content Area
                self.tab_content_area
            ], expand=True)
            
            # Initial View Update
            self._update_view(initial_setup=True)
            
        except Exception as e:
            print(f"ERROR Building DraftView: {e}")
            import traceback
            traceback.print_exc()
            self.content = ft.Text(f"Error Loading Draft View: {e}", color=ft.Colors.RED, size=20)

    def _force_reset(self, e):
        """Manually resets the draft data."""
        self.gm.draft_class = [] # Clear Class
        self.gm.init_draft() # Re-init (will generate class and order)
        self.page.snack_bar = ft.SnackBar(ft.Text("選秀已重置！"))
        self.page.snack_bar.open = True
        self._update_view()
        self.page.update()

    def _update_view(self, initial_setup=False):
        # Refresh GM instance to ensure data Freshness
        self.gm = GameManager()
        
        print(f"DEBUG: Entering _update_view. Draft Active: {self.gm.is_draft_active}")
        
        # DEBUG UPDATE
        count_class = len(self.gm.draft_class)
        count_order = len(self.gm.draft_order)
        self.debug_text.value = f"Draft Active: {self.gm.is_draft_active} | Class: {count_class} | Order: {count_order}"
        
        if not initial_setup:
            self.debug_text.update()
        
        # 1. Update Header Info
        if not self.gm.is_draft_active:
             self.current_pick_text.value = "選秀已結束 (Draft Complete)"
             if not initial_setup and self.main_page:
                 self.main_page.update()
             return
             
        # Check integrity again
        if not self.gm.draft_order:
             self.current_pick_text.value = "資料錯誤：無選秀順位，請點擊重置"
             self.upcoming_list.controls.clear()
             self.upcoming_list.controls.append(ft.Text("No Draft Order Data"))
             if not initial_setup and self.main_page: self.main_page.update()
             return
             
        idx = self.gm.current_draft_pick_index
        total = len(self.gm.draft_order)
        
        if idx < total:
            team_id = self.gm.draft_order[idx]
            team = self.gm.get_team(team_id)
            # Safe check team
            t_name = team.name if team else f"Unknown({team_id})"
            
            # Round/Pick Calc
            num_teams = total // 2
            if num_teams == 0: num_teams = 1
            round_num = 1 if idx < num_teams else 2
            pick_num = (idx % num_teams) + 1
            
            self.current_pick_text.value = f"第 {round_num} 輪 第 {pick_num} 順位: {t_name}"
        else:
            self.current_pick_text.value = "選秀結束"
        
        # 2a. Update Upcoming Picks
        self.upcoming_list.controls.clear()
        
        # Show specific next 5 picks
        shown_count = 0
        current_idx = self.gm.current_draft_pick_index
        total_picks = len(self.gm.draft_order)
        
        if not self.gm.draft_order:
             self.upcoming_list.controls.append(ft.Text("Order Error"))
             return # Logic integrity

        for i in range(current_idx, min(current_idx + 8, total_picks)):
            try:
                team_id = self.gm.draft_order[i]
                team = self.gm.get_team(team_id)
                
                # Check team existence
                if not team:
                    team_name = f"Unknown ({team_id})"
                else:
                    team_name = team.name
                
                # Calc pick number
                num_teams = total_picks // 2
                if num_teams == 0: num_teams = 1
                round_num = 1 if i < num_teams else 2
                pick_num = (i % num_teams) + 1
                
                is_current = (i == current_idx)
                # Theme: Gold for Current, Dark Navy for others
                bg_color = "#CFB28B" if is_current else "#1E2740" 
                text_color = "#000000" if is_current else "#FFFFFF"
                
                self.upcoming_list.controls.append(
                    ft.Container(
                        content=ft.Row([
                            ft.Text(f"R{round_num} P{pick_num}", weight=ft.FontWeight.BOLD, width=80, color=text_color),
                            ft.Text(f"{team_name}", weight=ft.FontWeight.BOLD if is_current else ft.FontWeight.NORMAL, color=text_color)
                        ]),
                        padding=5,
                        bgcolor=bg_color,
                        border=ft.border.all(2, "#CFB28B") if is_current else None,
                        border_radius=5
                    )
                )
            except Exception as ex:
                self.upcoming_list.controls.append(ft.Text(f"Error: {ex}", color=ft.Colors.RED))

        # 2b. Update History Log
        self.log_list.controls.clear()
        for pick in reversed(self.gm.draft_picks): 
            self.log_list.controls.append(
                ft.Container(
                    content=ft.Text(f"R{pick['round']} P{pick['pick']} {pick['team']}: {pick['player']}"),
                    padding=5,
                    bgcolor="#1E2740", # Dark Card BG
                    border_radius=5,
                    border=ft.border.all(1, "#3E4760") # Subtle outline
                )
            )
        
        # 3. Update Rookie List
        active_team_id = self.gm.draft_order[self.gm.current_draft_pick_index] if self.gm.current_draft_pick_index < len(self.gm.draft_order) else None
        user_team = self.gm.get_user_team()
        is_user_turn = (active_team_id == user_team.id) if active_team_id and user_team else False
        
        # Update Button States
        if is_user_turn:
            self.btn_next.disabled = True
            self.btn_sim.disabled = True
        else:
            self.btn_next.disabled = False
            self.btn_sim.disabled = False
        
        if not initial_setup:
            self.btn_next.update()
            self.btn_sim.update()
        
        self.rookie_list_view.controls.clear()
        
        # Filter: Only show undrafted
        available = [p for p in self.gm.draft_class if p.team_id == "DRAFT"]
        available.sort(key=lambda p: p.ovr, reverse=True)
        
        print(f"DEBUG: DraftView Update. Class Size: {len(self.gm.draft_class)}, Available: {len(available)}")
        
        for p in available:
            # Action Button
            action_control = ft.Container(width=70) # Width 70
            if is_user_turn:
                 action_control = ft.ElevatedButton("選中", on_click=lambda e, pid=p.id: self._on_user_pick(pid), width=70, style=ft.ButtonStyle(padding=2)) # Reduced padding
            
            row = ft.Container(
                content=ft.Row([
                     ft.Text(p.mask_name, width=110, size=12), # Smaller text, 110 width
                     ft.Text(p.pos, width=40, size=12),
                     ft.Text(str(p.age), width=40, size=12),
                     ft.Text(str(p.ovr), width=40, size=12, weight=ft.FontWeight.BOLD),
                     ft.Text(str(p.potential), width=40, size=12), 
                     action_control
                ]),
                padding=2,
                # bgcolor=ft.colors.BACKGROUND # Optional
            )
            self.rookie_list_view.controls.append(row)
            
        if not initial_setup and self.main_page:
            self.main_page.update()

    def _on_next_pick(self, e):
        if not self.gm.is_draft_active: return
        self.gm.resolve_draft_pick()
        self._update_view()

    def _on_user_pick(self, player_id):
        self.gm.resolve_draft_pick(player_id)
        self._update_view()
        
    def _build_live_view(self):
        return ft.Container(
            content=ft.Column([
                ft.Text("當前順位 (On The Clock)", weight=ft.FontWeight.BOLD),
                ft.Container(
                     content=self.upcoming_list, 
                     height=200, 
                     border=ft.border.all(1, "#3E4760"),
                     border_radius=5,
                     padding=5
                ),
                ft.Text("選秀紀錄 (History)", weight=ft.FontWeight.BOLD),
                ft.Container(
                     content=self.log_list, 
                     expand=True, 
                     border=ft.border.all(1, "#3E4760"),
                     border_radius=5,
                     padding=5
                ),
            ]),
            padding=10
        )

    def _build_pool_view(self):
        # Allow horizontal scrolling by enforcing a minimum width
        min_table_width = 400 
        
        # The Table Column (Header + List)
        table_content = ft.Column([
             self.rookie_header, 
             ft.Container(
                  content=self.rookie_list_view, 
                  expand=True, 
                  border=ft.border.all(1, "#3E4760"),
                  border_radius=5
             )
        ], expand=True)

        return ft.Container(
            content=ft.Column([
                 ft.Text("待選名單 (Green Room)", weight=ft.FontWeight.BOLD),
                 # Horizontal Scroll Wrapper
                 # We wrap the fixed-width table in a scrollable Row
                 ft.Row(
                     controls=[
                        ft.Container(
                            content=table_content, 
                            width=min_table_width
                        )
                     ],
                     scroll=ft.ScrollMode.AUTO, 
                     expand=True,
                     vertical_alignment=ft.CrossAxisAlignment.START # Top align
                 )
            ]),
            padding=5
        )

    def _switch_tab(self, mode):
        is_live = (mode == "live")
        # Update Styles
        self.tab_live_btn.bgcolor = ft.Colors.PRIMARY if is_live else "#3E4760"
        self.tab_live_btn.color = ft.Colors.ON_PRIMARY if is_live else "#E0E0E0"
        self.tab_pool_btn.bgcolor = ft.Colors.PRIMARY if not is_live else "#3E4760"
        self.tab_pool_btn.color = ft.Colors.ON_PRIMARY if not is_live else "#E0E0E0"
        
        # Update Content
        self.tab_content_area.content = self._build_live_view() if is_live else self._build_pool_view()
        
        # Safe Update
        try:
            self.tab_live_btn.update()
            self.tab_pool_btn.update()
            self.tab_content_area.update()
        except: pass

    def _on_sim_to_user(self, e):
        user_team = self.gm.get_user_team()
        max_picks = len(self.gm.draft_order)
        
        while self.gm.is_draft_active and self.gm.current_draft_pick_index < max_picks:
             active_team_id = self.gm.draft_order[self.gm.current_draft_pick_index]
             if active_team_id == user_team.id:
                 break # Stop at User Pick
             self.gm.resolve_draft_pick()
             
        self._update_view()

    def _on_finish_draft(self, e):
        # 1. End Draft & Schedule (Redundant safety)
        if self.gm.is_draft_active:
             self.gm.is_draft_active = False
             self.gm.schedule_post_draft()
             self.gm.save_game(0) # Logic Update: Save on finish
        
        # 2. Trigger Callback to Parent (ScoutingView)
        if self.on_draft_end:
            self.on_draft_end()


