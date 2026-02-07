import flet as ft
from controllers.game_manager import GameManager
from models.match_engine import MatchEngine
import random
from utils.localization import tr

class MatchView(ft.Container):
    def __init__(self, on_season_end=None):
        super().__init__()
        self.gm = GameManager()
        self.on_season_end = on_season_end
        self.padding = 20
        self.result_text = ft.Text("", size=16)
        self.box_score = ft.Column(scroll=ft.ScrollMode.AUTO)
        self.build_content()
    
    def build_content(self):
        day_text = f"{tr('Day')} {self.gm.current_day}"
        is_season_end = False
        
        day_text = f"{tr('Day')} {self.gm.current_day}"
        is_season_end = False
        
        if self.gm.is_draft_active:
            self.content = ft.Container(
                alignment=ft.Alignment(0, 0),
                content=ft.Column([
                    ft.Icon(ft.Icons.LOCK, size=50, color=ft.Colors.GREY),
                    ft.Text(tr("Draft In Progress"), size=20, weight=ft.FontWeight.BOLD),
                    ft.Text(tr("Please complete the draft before starting the season."), size=16),
                    ft.ElevatedButton(tr("Go to Scouting Tab (Draft)"), disabled=True) 
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
            )
            return

        # Roster Validation Lock
        user_team = self.gm.get_user_team()
        if len(user_team.roster) < 8:
            self.content = ft.Container(
                alignment=ft.Alignment(0, 0),
                content=ft.Column([
                    ft.Icon(ft.Icons.LOCK, size=50, color=ft.Colors.RED),
                    ft.Text(tr("Roster Incomplete"), size=20, weight=ft.FontWeight.BOLD),
                    ft.Text(tr("You need at least 8 players to start the season."), size=16),
                    ft.Text(f"{tr('Current Roster')}: {len(user_team.roster)}", size=14, color=ft.Colors.GREY),
                    # Future: Button to Free Agency?
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
            )
            return

        if not hasattr(self.gm, 'total_regular_season_days') or self.gm.total_regular_season_days is None:
             self.gm._recalc_total_days()

        total_reg_days = getattr(self.gm, 'total_regular_season_days', 40) # Default to 40? 10 is too small for UI

        
        if self.gm.current_day <= total_reg_days:
            # Regular Season: Show Progress
            day_text = f"{tr('Day')} {self.gm.current_day} / {total_reg_days}"
        else:
            # Playoffs or Season End
            todays_games = self.gm.get_todays_games()
            
            if not todays_games:
                day_text = tr("Season Finished")
                is_season_end = True
            else:
                 # Check if Finals (Round 2)
                 is_finals = False
                 round_name = tr("Playoffs: Semi-Finals")
                 
                 if hasattr(self.gm, 'playoff_series') and self.gm.playoff_series:
                     if any(s['round'] == 2 for s in self.gm.playoff_series):
                         is_finals = True
                         round_name = tr("Playoffs: Finals")
                 
                 # Append Series Score info
                 series_info = []
                 if hasattr(self.gm, 'playoff_series'):
                     for s in self.gm.playoff_series:
                         if s['winner']: continue # Don't show finished
                         # Only show active series
                         if any(g.id.startswith(f"P_{s['id']}") for g in todays_games):
                             info = f"{s['t1'].name} {s['w1']}-{s['w2']} {s['t2'].name}"
                             series_info.append(info)
                 
                 if series_info:
                     day_text = f"{round_name}\n({', '.join(series_info)})"
                 else:
                     day_text = round_name

        action_button = ft.ElevatedButton(
            tr("Simulate Next Game"),
            icon=ft.Icons.PLAY_ARROW,
            on_click=self.sim_game,
            style=ft.ButtonStyle(
                color=ft.Colors.ON_PRIMARY,
                bgcolor=ft.Colors.PRIMARY,
                padding=20
            )
        )
        
        sim_playoffs_button = ft.ElevatedButton(
             tr("Simulate Season"),
             icon=ft.Icons.FAST_FORWARD,
             on_click=self.sim_to_playoffs,
             style=ft.ButtonStyle(bgcolor=ft.Colors.BLUE_GREY_900, color=ft.Colors.WHITE)
        )
        
        if is_season_end:
            action_button = ft.ElevatedButton(
                tr("View Season Summary"),
                icon=ft.Icons.CELEBRATION,
                on_click=self._on_summary_click,
                style=ft.ButtonStyle(
                    color=ft.Colors.WHITE,
                    bgcolor=ft.Colors.AMBER_700,
                    padding=20
                )
            )

        self.content = ft.Column([
            ft.Text(day_text, size=30, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER),
            ft.Divider(),
            ft.Text(self.result_text.value, size=16),
            ft.Container(height=20),
            ft.Row([action_button, sim_playoffs_button] if not is_season_end else [action_button], alignment=ft.MainAxisAlignment.CENTER),
            ft.Divider(),
            ft.Container(content=self.box_score, expand=True)
        ])
        
        # Check for Championship Celebration
        if getattr(self.gm, "celebration_pending", False):
            self.gm.celebration_pending = False # Consumed
            self._show_championship_dialog()

    def _show_championship_dialog(self):
        content = ft.Column([
            ft.Icon(ft.Icons.EMOJI_EVENTS, color=ft.Colors.AMBER, size=80),
            ft.Text("WE ARE THE CHAMPIONS!", size=28, weight=ft.FontWeight.BOLD, color=ft.Colors.AMBER, text_align=ft.TextAlign.CENTER),
            ft.Text(tr("Congratulations! You have won the TPBL Title!"), size=16, text_align=ft.TextAlign.CENTER),
            ft.Container(height=20),
            ft.Image(src="assets/confetti.png", width=200, height=100, fit=ft.ImageFit.CONTAIN, visible=False), # Placeholder
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        
        dlg = ft.AlertDialog(
            content=ft.Container(content=content, height=250),
            actions=[
                ft.TextButton(tr("Awesome!"), on_click=lambda e: self.app_page.close_dialog())
            ],
            actions_alignment=ft.MainAxisAlignment.CENTER,
            bgcolor="#0b1120",
            shape=ft.RoundedRectangleBorder(radius=20),
        )
        self.app_page.dialog = dlg
        dlg.open = True
        self.app_page.update()
    
    def _on_summary_click(self, e):
        if self.on_season_end:
            self.on_season_end()

    def sim_game(self, e):
        # Validation: Check Roster Size (Min 8)
        user_team = self.gm.get_user_team()
        if len(user_team.roster) < 8:
            if self.page:
                self.page.snack_bar = ft.SnackBar(content=ft.Text(tr("Roster must have at least 8 players to simulate games!")), bgcolor=ft.Colors.ERROR)
                self.page.snack_bar.open = True
                self.page.update()
            return

        games = self.gm.get_todays_games()
        
        if not games:
            self.result_text.value = tr("No games scheduled for today.")
            self.result_text.update()
            return
            
        # Use centralized logic
        results = self.gm.play_day()
        
        daily_summary = [f"=== {tr('Day')} {self.gm.current_day - 1} {tr('Results')} ==="]
        user_game_result = None
        
        for result in results:
             summary = f"{result['winner']} def. {result['loser']} ({result['home_score']}-{result['away_score']})"
             daily_summary.append(summary)
             
             # Check for user team
             h = result['home_team']
             a = result['away_team']
             if h == self.gm.user_team_id or a == self.gm.user_team_id: # Correction: result usually has names or IDs?
                 # MatchEngine returns Dict with names. We need ID check or assume names unique?
                 # Wait, MatchEngine.simulate_game returns:
                 # "home_team": home_team.name, "away_team": away_team.name
                 # We need the game object to know IDs easily, or look up by name.
                 # Actually gm.play_day iterates games.
                 pass

        # Since we lost the Game object reference in the loop inside gm.play_day (it returns results dicts),
        # we might need to find the user game separately or modify play_day to return Game objects.
        # But for now, let's just show summary.
        
        # To show user stats popup, we need to know if user played.
        # Let's hunt for user team name in results.
        user_team = self.gm.get_user_team()
        if user_team:
            for res in results:
                if res['home_team'] == user_team.name or res['away_team'] == user_team.name:
                    user_game_result = res
                    break

        self.result_text.value = f"{tr('Day')} {self.gm.current_day - 1} {tr('Simulation Complete')}."
        
        # Add to log
        self.box_score.controls.insert(0, ft.Text("\n".join(daily_summary)))
        self.box_score.controls.insert(0, ft.Divider())
        
        # Rebuild to update button if season finished
        self.build_content()
        self.update()
        
        # Show stats popup if user played
        if user_game_result:
            self._show_game_stats(user_game_result)

    def _show_game_stats(self, result):
        try:
            home_name = result["home_team"]
            away_name = result["away_team"]
            home_score = result["home_score"]
            away_score = result["away_score"]
            
            def create_table(box_list):
                if not box_list:
                    return ft.Text(tr("No stats available"))
                
                rows = []
                for p in sorted(box_list, key=lambda x: x["pts"], reverse=True):
                    fg_display = f"{p.get('fgm', 0)}-{p.get('fga', 0)}"
                    rows.append(
                        ft.DataRow(cells=[
                            ft.DataCell(ft.Text(str(p["name"]))),
                            ft.DataCell(ft.Text(str(p["pts"]))),
                            ft.DataCell(ft.Text(fg_display)),
                            ft.DataCell(ft.Text(str(p["reb"]))),
                            ft.DataCell(ft.Text(str(p["ast"]))),
                            ft.DataCell(ft.Text(str(p["stl"]))),
                            ft.DataCell(ft.Text(str(p["blk"]))),
                            ft.DataCell(ft.Text(str(p["to"]))),
                        ])
                    )
                
                return ft.DataTable(
                    columns=[
                        ft.DataColumn(ft.Text(tr("Player"))),
                        ft.DataColumn(ft.Text("PTS"), numeric=True),
                        ft.DataColumn(ft.Text("FG")),
                        ft.DataColumn(ft.Text("REB"), numeric=True),
                        ft.DataColumn(ft.Text("AST"), numeric=True),
                        ft.DataColumn(ft.Text("STL"), numeric=True),
                        ft.DataColumn(ft.Text("BLK"), numeric=True),
                        ft.DataColumn(ft.Text(tr("TO")), numeric=True),
                    ],
                    rows=rows,
                    heading_row_height=30,
                    data_row_min_height=30,
                    column_spacing=10, # Squeeze columns a bit
                )

            content = ft.Column([
                ft.Text(f"{home_name} ({home_score}) vs {away_name} ({away_score})", size=20, weight=ft.FontWeight.BOLD),
                ft.Divider(),
                ft.Text(f"{tr('Home')}: {home_name}"),
                ft.Row([create_table(result.get("home_box_score", []))], scroll=ft.ScrollMode.AUTO),
                ft.Divider(),
                ft.Text(f"{tr('Away')}: {away_name}"),
                ft.Row([create_table(result.get("away_box_score", []))], scroll=ft.ScrollMode.AUTO),
            ], scroll=ft.ScrollMode.AUTO, height=500, width=750)

            self.stat_dlg = ft.AlertDialog(
                title=ft.Text(tr("Game Summary")),
                content=content,
                modal=False,
                on_dismiss=lambda e: self.close_stat_dlg(),
                actions=[
                    ft.TextButton(tr("Close"), on_click=lambda e: self.close_stat_dlg())
                ]
            )
            
            # Use Overlay for reliability
            self.page.overlay.append(self.stat_dlg)
            self.stat_dlg.open = True
            
            # SnackBar as confirmation
            self.page.snack_bar = ft.SnackBar(ft.Text(f"{tr('Game Summary')}: {home_name} vs {away_name}"))
            self.page.snack_bar.open = True
            
            self.page.update()
            
        except Exception as e:
            print(f"ERROR in _show_game_stats: {e}")
            self.page.snack_bar = ft.SnackBar(ft.Text(f"Error showing stats: {e}"), bgcolor=ft.Colors.RED)
            self.page.snack_bar.open = True
            self.page.update()

    def close_stat_dlg(self):
        self.stat_dlg.open = False
        self.page.update()

    def sim_to_playoffs(self, e):
        limit = getattr(self.gm, 'total_regular_season_days', 60)
        
        # Show loading?
        self.result_text.value = tr("Simulating season...")
        self.update()
        
        # Safety break
        safety = 0
        import time
        
        while self.gm.current_day <= limit + 30 and safety < 100: # Limit + 30 for playoffs
             # Check if Season Ended (Champion determined or no games left)
             # Wait, sim_to_playoffs name implies stopping AT playoffs.
             # User probably wants "Simulate Season" to mean "Simulate EVERYTHING".
             # So let's allow it to run until no games are left.
             
             if not self.gm.get_todays_games() and self.gm.current_day > limit:
                 # No games and past regular season -> Finished?
                 # If Playoff Series exists but no winner yet, maybe games not scheduled yet?
                 # _schedule_next_playoff_games is called in advance_day.
                 # So if we are in playoffs, get_todays_games should return something.
                 # If not, it means season over.
                 break
                 
             self.gm.play_day()
             safety += 1
             
             # Optional: Update UI every few days to show progress
             if safety % 5 == 0:
                 self.result_text.value = f"Simulating... Day {self.gm.current_day} / {limit}"
                 self.update() # Update entire container to be safe
                 time.sleep(0.5) # Increased delay for visibility
             
        self.build_content()
        self.page.update() # Ensure page update
