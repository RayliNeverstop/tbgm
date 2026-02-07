import flet as ft
from views.dashboard_view import DashboardView
from controllers.game_manager import GameManager
from views.roster_view import RosterView
from views.match_view import MatchView
from views.market_view import MarketView
from views.standings_view import StandingsView
from views.offseason_view import OffseasonView
from views.trade_view import TradeView
from views.scouting_view import ScoutingView
from views.strategy_view import StrategyView
from views.stats_view import StatsView
from views.history_view import HistoryView
from views.season_summary_view import SeasonSummaryView
# from views.draft_view import DraftView # Consolidated

from views.progression_view import ProgressionView

from utils.localization import tr

from controllers.ad_manager import AdManager

class MainLayout(ft.Row):
    def __init__(self, page: ft.Page):
        super().__init__()
        self.page_ref = page
        self.gm = GameManager()
        self.ad_manager = AdManager() # Init AdManager
        
        # Mobile Persistence: Now handled by relative file path 'game_saves'.
        # Client Storage callback removed due to compatibility issues.
        
        self.expand = True
        
        # Initialize Views
        self.dashboard_view = DashboardView(on_history_click=self.show_history)
        self.roster_view = RosterView() 
        self.match_view = MatchView(on_season_end=self.show_season_end_summary)
        self.market_view = MarketView()
        self.trade_view = TradeView()
        self.standings_view = StandingsView()
        self.stats_view = StatsView()
        self.scouting_view = ScoutingView(page)
        self.strategy_view = StrategyView()
        self.progression_view = ProgressionView(on_continue_click=lambda: self.reset_to_dashboard(start_draft=True))
        self.history_view = HistoryView(page)
        self.season_summary_view = SeasonSummaryView(on_continue=self.show_offseason)
        self.offseason_view = OffseasonView(on_next_season_click=self.show_progression)
        
        self.body_container = ft.Container(content=self.dashboard_view, expand=True)

        # Ad Banner Setup
        self.ad_banner = self.ad_manager.get_banner_widget()
        self.content_with_ad = ft.Column([
            self.body_container,
            ft.Divider(height=1, thickness=1), # Separator
            ft.Container(content=self.ad_banner, alignment=ft.Alignment(0,0), bgcolor="#111111") # Ad Container
        ], expand=True, spacing=0)

        # 1. Define Destinations (Shared by Rail and Drawer)
        self.destinations_list = [
            (ft.Icons.DASHBOARD_OUTLINED, ft.Icons.DASHBOARD, tr("Dashboard")),
            (ft.Icons.FORMAT_LIST_NUMBERED_OUTLINED, ft.Icons.FORMAT_LIST_NUMBERED, tr("Standings")),
            (ft.Icons.BAR_CHART_OUTLINED, ft.Icons.BAR_CHART, tr("Stats")),
            (ft.Icons.PEOPLE_OUTLINE, ft.Icons.PEOPLE, tr("Roster")),
            (ft.Icons.SPORTS_BASKETBALL_OUTLINED, ft.Icons.SPORTS_BASKETBALL, tr("Matches")),
            (ft.Icons.STOREFRONT_OUTLINED, ft.Icons.STOREFRONT, tr("Market")),
            (ft.Icons.SWAP_HORIZ_OUTLINED, ft.Icons.SWAP_HORIZ, tr("Trades")),
            (ft.Icons.VISIBILITY_OUTLINED, ft.Icons.VISIBILITY, tr("Scouting")),
            (ft.Icons.SETTINGS_INPUT_COMPONENT_OUTLINED, ft.Icons.SETTINGS_INPUT_COMPONENT, tr("Strategy")),
            (ft.Icons.TRENDING_UP, ft.Icons.TRENDING_UP, tr("Progression")),
            (ft.Icons.HISTORY_EDU, ft.Icons.HISTORY_EDU, tr("History")),
        ]
        
        # 2. Desktop: Navigation Rail
        self.rail = ft.NavigationRail(
            selected_index=0,
            label_type=ft.NavigationRailLabelType.ALL,
            min_width=100,
            min_extended_width=400,
            group_alignment=-0.9,
            indicator_color=ft.Colors.PRIMARY_CONTAINER, 
            selected_label_text_style=ft.TextStyle(color=ft.Colors.PRIMARY_CONTAINER, weight=ft.FontWeight.BOLD),
            unselected_label_text_style=ft.TextStyle(color=ft.Colors.ON_SURFACE),
            destinations=[
                ft.NavigationRailDestination(icon=x[0], selected_icon=x[1], label=x[2]) 
                for x in self.destinations_list
            ],
            on_change=self._on_nav_change,
        )

        # 3. Mobile: Navigation Drawer
        self.drawer = ft.NavigationDrawer(
            on_change=self._on_nav_change,
            controls=[
                ft.Container(height=12),
                ft.Text(tr("Menu"), size=20, weight="bold", text_align="center"),
                ft.Divider(thickness=2),
                *[
                    ft.NavigationDrawerDestination(icon=x[0], selected_icon=x[1], label=x[2])
                    for x in self.destinations_list
                ]
            ],
        )

        # 4. Mobile: AppBar
        # improved: Remove manual leading to let Flet use native Drawer handle
        self.appbar = ft.AppBar(
            title=ft.Text("TBGM"),
            center_title=True,
            bgcolor="#202A3C", # Dark Blue-Grey Surface Variant
            toolbar_height=50,
        )

        # Initial Controls logic will be handled by resize
        self.controls = [] 
        
        # Bind Resize Event
        self.page_ref.on_resized = self._handle_resize
        
        # Bind Back Button (Android)
        self.page_ref.on_back_button = self._handle_back_button
        
        # Track current view for "On Leave" logic
        self.current_idx = 0
        
        # Initial check
        self._handle_resize(None)

    def _handle_resize(self, e):
        """Switches between Desktop/Mobile layouts based on width."""
        width = self.page_ref.width
        if width is None: return # Wait for initialization
        
        if width < 800:
            # Mobile Mode
            self.rail.visible = False
            self.page_ref.appbar = self.appbar
            self.page_ref.drawer = self.drawer
            self.controls = [self.content_with_ad]
        else:
            # Desktop Mode
            self.rail.visible = True
            self.page_ref.appbar = None
            self.page_ref.drawer = None
            self.controls = [self.rail, ft.VerticalDivider(width=1), self.content_with_ad]
            
        try:
            if self.page:
                self.page_ref.update()
                self.update()
        except Exception:
            pass

    def _open_drawer(self, e):
        self.drawer.open = True
        try:
            self.drawer.update()
            self.page_ref.update()
        except:
             pass

    def _handle_back_button(self, view):
        # 1. Close Drawer if Open
        if self.drawer.open:
            self.drawer.open = False
            try:
                self.drawer.update()
            except:
                pass
            return

        # 2. Return to Dashboard if elsewhere
        if self.rail.selected_index != 0:
            self.rail.selected_index = 0
            self.drawer.selected_index = 0
            self.reset_to_dashboard()
            try:
                self.rail.update()
                self.drawer.update()
            except:
                pass
            return

        # 3. If on Dashboard, Allow Exit (or maybe show confirmation dialog in future)
        # Flet default behavior will exit app here if we don't return True?
        # Actually page.on_back_button explanation: "Event handler is a function... If handler returns True, it prevents the default behavior (navigation pop or app exit)."
        # But Flet Python runs async-ish.
        # Wait, if we did action, we should probably return nothing or stop.
        # Flet docs says: "Back button event. On Android, it is triggered when Back button is pressed."
        pass

    def show_season_end_summary(self):
        """Displays the Season Summary (Awards) View."""
        self.season_summary_view.build_content() # Refresh data
        self.body_container.content = self.season_summary_view
        self.rail.selected_index = None # Deselect on Rail
        self.drawer.selected_index = None  # Deselect on Drawer
        self.update()

    def show_offseason(self):
        self.offseason_view.build_content()
        self.body_container.content = self.offseason_view
        self.rail.selected_index = None 
        self.drawer.selected_index = None
        self.update()

    def show_progression(self, start_draft=False): 
        self.progression_view.build_content()
        self.body_container.content = self.progression_view
        self.rail.selected_index = 9 
        self.drawer.selected_index = 9
        self.update()

    def reset_to_dashboard(self, start_draft=False):
        """Called when Season Ends or Draft Starts."""
        if start_draft:
             idx = 7 # Scouting / Draft Tab
             self.scouting_view.refresh() # Trigger View Update
             self.body_container.content = self.scouting_view
        else:
             idx = 0
             self.dashboard_view.build_content()
             self.body_container.content = self.dashboard_view
        
        # Save Strategy if leaving it
        if self.rail.selected_index == 8:
            print("DEBUG: Leaving Strategy View -> Auto-Saving.")
            self.strategy_view._auto_save_settings()

        self.rail.selected_index = idx
        self.drawer.selected_index = idx
        self.current_idx = idx
        self.update()
        self.page_ref.update()

    def show_history(self):
        idx = 10 # History Index
        self.rail.selected_index = idx
        self.drawer.selected_index = idx
        
        self.history_view.build_content() 
        self.body_container.content = self.history_view
        self.update()

    def _on_nav_change(self, e):
        index = e.control.selected_index
        
        # Save Strategy if leaving it
        if self.current_idx == 8 and index != 8:
            print("DEBUG: Navigating away from Strategy View -> Auto-Saving.")
            self.strategy_view._auto_save_settings()

        self.current_idx = index
        
        # Sync Selection
        self.rail.selected_index = index
        self.drawer.selected_index = index
        
        # Close drawer if mobile
        if self.page_ref.width < 800:
             try:
                 self.drawer.open = False
                 self.drawer.update()
             except Exception:
                 pass
        
        if index == 0:
            self.dashboard_view.build_content() 
            self.body_container.content = self.dashboard_view
        elif index == 1:
            self.standings_view.build_content()
            self.body_container.content = self.standings_view
        elif index == 2:
            self.stats_view.refresh_stats()
            self.body_container.content = self.stats_view
        elif index == 3:
            self.roster_view.reset_view() 
            self.body_container.content = self.roster_view
        elif index == 4:
            self.match_view.build_content() 
            self.body_container.content = self.match_view
        elif index == 5:
            self.market_view.build_content()
            self.body_container.content = self.market_view
        elif index == 6:
            self.trade_view.build_content()
            self.body_container.content = self.trade_view
        elif index == 7:
            self.scouting_view.refresh()
            self.body_container.content = self.scouting_view
        elif index == 8:
            self.strategy_view.build_content()
            self.body_container.content = self.strategy_view
        elif index == 9:
            self.progression_view.build_content()
            self.body_container.content = self.progression_view
        elif index == 10:
            self.history_view.build_content()
            self.body_container.content = self.history_view
            
        self.update()
