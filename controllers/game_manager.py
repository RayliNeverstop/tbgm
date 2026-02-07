from typing import List, Optional
from models.player import Player, PlayerAttributes
from models.team import Team
from models.game import Game
from models.match_engine import MatchEngine
from .data_loader import DataLoader
from .save_manager import SaveManager
import random
import os
import glob

ACHIEVEMENT_DEFINITIONS = {
    "first_win": {
        "title": "First Blood",
        "description": "Win your first game.",
        "icon": "SPORTS_BASKETBALL"
    },
    "playoff_bound": {
        "title": "Playoff Competitor",
        "description": "Win a playoff series.",
        "icon": "WHATSHOT" 
    },
    "champion": {
        "title": "National Champion",
        "description": "Win the TPBL Title.",
        "icon": "EMOJI_EVENTS"
    },
    "mvp_finder": {
        "title": "MVP Mentor",
        "description": "Have a player win MVP.",
        "icon": "STAR"
    },
    "fmvp_finder": {
        "title": "Finals MVP Mentor",
        "description": "Have a player win Finals MVP.",
        "icon": "STAR_BORDER"
    },
    "dynasty": {
        "title": "Dynasty",
        "description": "Win 3 Championships in a row.",
        "icon": "AUTO_AWESOME"
    },
    "underdog": {
        "title": "Underdog",
        "description": "Win title as #4 seed.",
        "icon": "TRENDING_UP"
    },
    "perfect_season": {
        "title": "Perfect Season",
        "description": "Win title with < 5 losses.",
        "icon": "DIAMOND"
    },
    "sniper": {
        "title": "Sniper",
        "description": "Draft a player who reaches 90+ OVR.",
        "icon": "GPS_FIXED"
    }
}

class GameManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(GameManager, cls).__new__(cls)
            cls._instance.initialized = False
            cls._instance.save_callback = None # Callback for external storage (e.g. Flet Client Storage)
        return cls._instance

    def set_save_callback(self, callback):
        self.save_callback = callback

    def initialize(self, data_path: str, raw_data_override=None):
        print(f"DEBUG: GameManager.initialize called. Initialized={self.initialized}")
        if self.initialized:
            return
        
        self.data_loader = DataLoader(data_path)
        
        if raw_data_override:
             print("DEBUG: Loading from Client Storage Override")
             self.raw_data = raw_data_override
        else:
             self.raw_data = self.data_loader.load_data()
        
        self.salary_cap = self.raw_data.get("salary_cap", 70.0)
        self.user_team_id = self.raw_data.get("user_team_id", "")
        
        self.teams, self.players = self.data_loader.process_data_into_objects(self.raw_data)
        
        # Ensure enough teams for a season
        if len(self.teams) < 4:
            self._generate_dummy_teams()

        self.current_date = self.raw_data.get("current_date", "2025-10-01")
        self.current_day = self.raw_data.get("current_day", 1)
        self.season_year = 2025
        self.retired_players: List[Player] = []
        self.scouting_points = self.raw_data.get("scouting_points", 50)
        self.news_feed = self.raw_data.get("news_feed", []) # News Feed
        
        # Initialize TradeManager lazily to avoid circular import issues if possible, 
        # or just import at top if safe.
        # self.trade_manager = TradeManager() # Circular dep: TradeManager imports GameManager
        # We will instantiate locally when needed.
        
        # Load Schedule
        self.schedule: List[Game] = []
        raw_schedule = self.raw_data.get("schedule", [])
        
        if raw_schedule:
            print(f"DEBUG: Persistence - Loading {len(raw_schedule)} games from Save.")
            for g_data in raw_schedule:
                # Re-link Team Objects
                home_id = g_data.get("home_team_id")
                away_id = g_data.get("away_team_id")
                home = next((t for t in self.teams if t.id == home_id), None)
                away = next((t for t in self.teams if t.id == away_id), None)
                
                if home and away:
                    # Manually reconstruct if from_dict missing, or use Class method
                    # Assuming from_dict exists or constructing manually for safety
                    new_game = Game(
                        id=g_data.get("id"),
                        day=g_data.get("day"),
                        home_team=home,
                        away_team=away
                    )
                    new_game.home_score = g_data.get("home_score", 0)
                    new_game.away_score = g_data.get("away_score", 0)
                    new_game.played = g_data.get("played", False)
                    self.schedule.append(new_game)
            self._recalc_total_days()
        else:
            print("DEBUG: No Schedule in Save. Generating New Schedule.")
            self._generate_schedule()

        # Load Draft Class
        self.draft_class = []
        raw_draft = self.raw_data.get("draft_class", [])
        if raw_draft:
             for p_data in raw_draft:
                 self.draft_class.append(Player.from_dict(p_data))
        elif not raw_schedule: # Only if fresh start generate
             # Unless we want to regenerate draft class if missing? 
             pass # Draft class is generated in 'offseason' or 'start'.
             # If empty, it stays empty until generated.
        
        # --- Initialize Default Draft Picks (Phase 62) ---
        try:
            current_year = int(self.season_year)
            for team in self.teams:
                if not team.draft_picks:
                    new_picks = []
                    for offset in range(1, 4): # Next 3 years
                        year = current_year + offset
                        for r in [1, 2]: # Round 1 & 2
                             new_picks.append({
                                 "year": year,
                                 "round": r,
                                 "original_owner_id": team.id
                             })
                    team.draft_picks = new_picks
        except Exception as e:
            print(f"Error initializing draft picks: {e}")
        # -------------------------------------------------

        self.initialized = True
        # Preserve save directory config across resets (Fixes Save Path Mismatch bug)
        current_save_dir = "data/saves"
        if hasattr(self, 'save_manager') and hasattr(self.save_manager, 'save_dir'):
             current_save_dir = self.save_manager.save_dir
        
        self.save_manager = SaveManager(current_save_dir)
        self.season_progression_log = self.raw_data.get("season_progression_log", {})
        self.playoff_series = self.raw_data.get("playoff_series", [])
        self.progression_data = {} 
        
        # Draft State Persistence
        self.is_draft_active = self.raw_data.get("is_draft_active", False)
        self.draft_order = self.raw_data.get("draft_order", [])
        self.draft_picks = self.raw_data.get("draft_picks", [])
        self.draft_order = self.raw_data.get("draft_order", [])
        self.draft_picks = self.raw_data.get("draft_picks", [])
        self.current_draft_pick_index = self.raw_data.get("current_draft_pick_index", 0)

        # Gamification
        self.gm_score = self.raw_data.get("gm_score", 0)
        self.achievements = self.raw_data.get("achievements", {})
        self.gm_score_log = self.raw_data.get("gm_score_log", [])
        self.hall_of_fame = self.raw_data.get("hall_of_fame", [])
        self.league_history = self.raw_data.get("league_history", [])
        self.league_records = self.raw_data.get("league_records", {
            "Points": {"val": 0, "holder": "None", "date": "N/A", "team": "N/A"},
            "Rebounds": {"val": 0, "holder": "None", "date": "N/A", "team": "N/A"},
            "Assists": {"val": 0, "holder": "None", "date": "N/A", "team": "N/A"},
            "Steals": {"val": 0, "holder": "None", "date": "N/A", "team": "N/A"},
            "Blocks": {"val": 0, "holder": "None", "date": "N/A", "team": "N/A"},
            "3PM": {"val": 0, "holder": "None", "date": "N/A", "team": "N/A"},
        })
        
    def check_new_records(self, player, stats):
        """Checks if a player broke a single-game record."""
        # Key Map: (Record Key, Stats Key)
        checks = [
            ("Points", "pts"),
            ("Rebounds", "reb"),
            ("Assists", "ast"),
            ("Steals", "stl"),
            ("Blocks", "blk"),
            ("3PM", "3pm")
        ]
        
        for rec_key, stat_key in checks:
            val = stats.get(stat_key, 0)
            current_record = self.league_records.get(rec_key, {}).get("val", 0)
            
            if val > current_record:
                # NEW RECORD!
                team_name = self.get_team(player.team_id).name if self.get_team(player.team_id) else "N/A"
                
                self.league_records[rec_key] = {
                    "val": val,
                    "holder": player.mask_name,
                    "date": f"S{self.season_year} D{self.current_day}",
                    "team": team_name
                }
                
                print(f"DEBUG: NEW RECORD! {player.mask_name} - {val} {rec_key}")
                
                # News Feed
                self.news_feed = getattr(self, 'news_feed', [])
                self.news_feed.append(
                    f"HISTORY: {player.mask_name} ({team_name}) broke the {rec_key} record with {val}!"
                )
                
                # Achievement Hook if user player
                # Achievement Hook if user player
                if player.team_id == self.user_team_id:
                     self.add_gm_score(50, f"Team Record: {rec_key}")

    def _check_hall_of_fame(self, player):
        """Checks if a retiring player qualifies for Hall of Fame."""
        score = 0
        
        # Career Stats from History
        history = getattr(player, 'history', [])
        career_pts = sum(s.get("pts", 0) for s in history)
        career_reb = sum(s.get("reb", 0) for s in history)
        career_ast = sum(s.get("ast", 0) for s in history)
        
        # Weighting (adjust as needed)
        score += career_pts * 1.0
        score += career_reb * 1.5
        score += career_ast * 2.0
        
        # Peak OVR Bonus (Estimate using current OVR if retiring high, or usually low?)
        # Retiring players usually declined. 
        # Ideally we track 'peak_ovr'. 
        # For now, use OVR but it might be low (36yo).
        # Let's use Career Games as longevity bonus
        games = sum(s.get("games", 0) for s in history)
        score += games * 10
        
        # Threshold (TBD, set low fow testing)
        THRESHOLD = 3000 
        
        if score > THRESHOLD:
             entry = {
                 "name": player.mask_name,
                 "pos": player.pos,
                 "year": self.season_year,
                 "score": int(score),
                 "stats": f"{career_pts} Pts, {career_reb} Reb, {career_ast} Ast"
             }
             self.hall_of_fame.append(entry)
             print(f"DEBUG: {player.mask_name} inducted into Hall of Fame! (Score: {int(score)})")
             
             if player.team_id == self.user_team_id:
                 self.add_gm_score(500, "Hall of Fame Inductee")
                 self.unlock_achievement("legend_maker", "Legend Maker", "Have a player inducted into the Hall of Fame.")



    def save_game(self, slot_id: int):
        return self.save_manager.save_game(self, slot_id)

    def load_game(self, slot_id: int):
        return self.save_manager.load_game(self, slot_id)

    def sign_player(self, player: Player, team: Team) -> tuple[bool, str]:
        """
        Signs a player to a team.
        Returns (Success, Message).
        """
        if player.team_id == team.id:
            return False, "Player is already on this team."
        
        # Check Salary Cap
        if team.salary_total + player.salary > self.salary_cap:
            return False, f"Over Salary Cap! (Cap: ${self.salary_cap}M)"

        # Remove from old team
        old_team = self.get_team(player.team_id)
        if old_team and player in old_team.roster:
            old_team.roster.remove(player)
            
        # Add to new team
        team.roster.append(player)
        player.team_id = team.id
        
        self.save_game(1)
        return True, f"Successfully signed {player.mask_name}!"

    def reset_game(self, template_path):
        """Resets the game to initial state (Factory Reset)."""
        print("DEBUG: Resetting Game...")
        
        # 1. Delete Save Files
        if hasattr(self, 'save_manager') and self.save_manager and self.save_manager.save_dir:
             import glob
             files = glob.glob(os.path.join(self.save_manager.save_dir, "save_*.json"))
             for f in files:
                 try:
                     os.remove(f)
                     print(f"Deleted {f}")
                 except: pass
        
        # 2. Reset Flag
        self.initialized = False
        
        # 3. Re-Initialize with Template
        self.initialize(template_path)
        
        # 4. Save immediately to persist new state
        self.save_game(1)

    def add_gm_score(self, points, reason):
        """Adds to GM legacy score and saves."""
        self.gm_score = getattr(self, 'gm_score', 0) + points
        
        # Log entry
        log_entry = {
            "date": str(getattr(self, "current_date", "Unknown")),
            "points": points,
            "reason": reason
        }
        if not hasattr(self, 'gm_score_log'):
            self.gm_score_log = []
        self.gm_score_log.insert(0, log_entry) # Add to top
        
        print(f"DEBUG: GM Score +{points} ({reason}). Total: {self.gm_score}")
        self.save_game(1)

    def unlock_achievement(self, key, title, description=""):
        """Unlocks an achievement."""
        self.achievements = getattr(self, 'achievements', {})
        
        if key not in self.achievements:
            import datetime
            self.achievements[key] = {
                "title": title,
                "description": description,
                "date": str(datetime.date.today())
            }
            print(f"DEBUG: Achievement Unlocked: {title}")
            self.add_gm_score(100, f"Achievement: {title}") # Bonus for achievement
            self.save_game(1)

    def release_player(self, player: Player) -> tuple[bool, str]:
        """
        Releases a player to Free Agency (T00).
        """
        old_team = self.get_team(player.team_id)
        if old_team and player in old_team.roster:
            old_team.roster.remove(player)
            
        # Get or Create Free Agent Team
        fa_team = self.get_team("T00")
        if not fa_team:
            fa_team = Team("T00", "Free Agents", "#333333")
            self.teams.append(fa_team)
            
        fa_team.roster.append(player)
        player.team_id = "T00"
        
        # Reset State for Negotiation
        player.contract_length = 0
        player.salary = 0.5 # Minimum wage or reset to 0? Just keep current salary as reference? No, 0.5 min.
        player.years_on_team = 0
        player.negotiation_allowed = True
        player.negotiation_patience = 3 # Reset patience
        player.negotiation_max_patience = 3
        
        self.save_game(1)
        return True, f"Released {player.mask_name}."

    def _generate_dummy_teams(self):
        """Generates dummy teams to ensure at least 4 teams for league play."""
        dummy_teams_needed = 4 - len(self.teams)
        if dummy_teams_needed <= 0:
            return

        team_names = ["Kaohsiung Steelers", "Taoyuan Pilots", "Formosa Dreamers", "Hsinchu Lioneers"]
        
        for i in range(dummy_teams_needed):
            t_id = f"DT{i+1}"
            name = team_names[i] if i < len(team_names) else f"Team {i+1}"
            color = "#CCCCCC"
            
            # Generate dummy players
            roster = []
            for j in range(8): # Small roster for dummy
                p = Player(
                    id=f"{t_id}_P{j}",
                    real_name=f"Player {j}",
                    mask_name=f"P. {j}",
                    team_id=t_id,
                    pos="PG" if j < 2 else "SG" if j < 4 else "SF" if j < 6 else "C",
                    salary=100,
                    age=22,
                    attributes=PlayerAttributes(),
                    ovr=random.randint(60, 85)
                )
                roster.append(p)
                self.players.append(p)
                
            new_team = Team(id=t_id, name=name, color=color, roster=roster)
            self.teams.append(new_team)

    def _generate_schedule(self):
        """
        Generates advanced Regular Season schedule.
        Requirement: Each team plays every other team 6 times.
        Cycle: 6 Rounds.
        Total Games per Team = (N-1) * 6.
        """
        self.schedule = []
        # Exclude Free Agents (T00) from schedule
        teams = [t for t in self.teams if t.id != "T00"]
        n = len(teams)
        if n < 2: return

        # 1. Generate all matchups (TeamA vs TeamB) * 6
        all_matchups = []
        
        # Round Robin pairs
        base_pairs = []
        for i in range(n):
            for j in range(i + 1, n):
                base_pairs.append((teams[i], teams[j]))

        # Repeat 6 times (3 Home / 3 Away balance if possible)
        for _ in range(6):
            # Shuffle base pairs each cycle to distribute
            random.shuffle(base_pairs)
            for t1, t2 in base_pairs:
                # Randomize home/away for now to keep simple, 
                # or alternate? Simple shuffle is usually 'infinite' safe enough.
                if random.random() < 0.5:
                    all_matchups.append((t1, t2))
                else:
                    all_matchups.append((t2, t1))
        
        # 2. Assign to Days (Scheduler Algorithm)
        # We need to assign games to "Day 1, Day 2..." such that 
        # no team plays twice on the same day.
        
        schedule_map = {} # Day -> List of (Home, Away)
        day = 1
        
        # Helper: Try to fit game into 'day', if not, try 'day+1'
        for home, away in all_matchups:
            placed = False
            curr_check = 1
            
            while not placed:
                # Check if Day 'curr_check' is valid for both teams
                day_games = schedule_map.get(curr_check, [])
                teams_playing_today = set()
                for (h, a) in day_games:
                    teams_playing_today.add(h.id)
                    teams_playing_today.add(a.id)
                
                if home.id not in teams_playing_today and away.id not in teams_playing_today:
                    # Valid! Place it
                    if curr_check not in schedule_map: schedule_map[curr_check] = []
                    schedule_map[curr_check].append((home, away))
                    placed = True
                else:
                    # Busy, try next day
                    curr_check += 1
        
        # 3. Create Game Objects
        game_id_counter = 1
        max_day = max(schedule_map.keys())
        self.total_regular_season_days = max_day
        
        for d in range(1, max_day + 1):
             games = schedule_map.get(d, [])
             for home, away in games:
                 game = Game(
                     id=f"G{game_id_counter}",
                     day=d,
                     home_team=home,
                     away_team=away
                 )
                 self.schedule.append(game)
                 game_id_counter += 1
                 
        print(f"DEBUG: Generated Schedule. Total Days: {self.total_regular_season_days}. Total Games: {len(self.schedule)}")

    def _recalc_total_days(self):
        """Recalculates total_regular_season_days from schedule."""
        if not self.schedule: return
        # Filter out playoff games if any (assume playoff games have ID starting with 'P' or day > some generic threshold?)
        # Better: Filter games that are NOT playoff series games.
        # But Playoff games are added to schedule dynamically.
        # Regular games usually ID "GX". Playoff "P_SX_GY".
        reg_games = [g for g in self.schedule if not g.id.startswith("P")]
        if not reg_games: return
        
        self.total_regular_season_days = max(g.day for g in reg_games)
        print(f"DEBUG: Recalculated Total Regular Season Days: {self.total_regular_season_days}")

    def get_todays_games(self) -> List[Game]:
        return [g for g in self.schedule if g.day == self.current_day]

    def advance_day(self):
        self.current_day += 1
        
        # --- AI Autonomous Trades (Phase 63) ---
        if self.current_day > 10 and self.current_day < self.total_regular_season_days * 0.85: # Trade Deadline
            try:
                from controllers.trade_manager import TradeManager
                tm = TradeManager()
                progress = self.current_day / self.total_regular_season_days
                news = tm.attempt_ai_trade(progress)
                if news:
                    self.news_feed.append(news)
                    if len(self.news_feed) > 50: self.news_feed.pop(0)
            except Exception as e:
                print(f"Error in AI Trade: {e}")
        # ---------------------------------------
        
        # Check Regular Season End
        if self.current_day > self.total_regular_season_days:
            # Entering Playoffs
            if not self.playoff_series:
                 # Initialize Playoffs
                 self._init_playoffs_round1()
            else:
                 # Continue Playoffs
                 self._advance_playoffs()
        
        self.save_game(1)

    def _init_playoffs_round1(self):
        print("DEBUG: Init Playoffs Round 1")
        # Sort teams
        sorted_teams = sorted(
            self.teams, 
            key=lambda t: (t.wins, t.wins / (t.wins + t.losses) if (t.wins + t.losses) > 0 else 0), 
            reverse=True
        )
        if len(sorted_teams) < 4: return
            
        seed1, seed2, seed3, seed4 = sorted_teams[0], sorted_teams[1], sorted_teams[2], sorted_teams[3]
        
        # Define Series: Best of 7 (First to 4)
        # Structure: {id, t1, t2, w1, w2, round, winner}
        self.playoff_series = [
            {"id": "S1", "t1": seed1, "t2": seed4, "w1": 0, "w2": 0, "round": 1, "winner": None}, # 1 vs 4
            {"id": "S2", "t1": seed2, "t2": seed3, "w1": 0, "w2": 0, "round": 1, "winner": None}  # 2 vs 3
        ]
        
        # Schedule Game 1 for tomorrow (current_day)
        self._schedule_next_playoff_games()

    def _advance_playoffs(self):
        # 1. Check results of *yesterday's* games (which were simulated)
        todays_games = [g for g in self.schedule if g.day == self.current_day - 1] # Games just finished
        
        series_updated = False
        
        for g in todays_games:
            # Find which series this game belongs to
            # We can tag games? Or lookup by team.
            if g.id.startswith("P"): # Playoff Game
               winner_name = g.result.get('winner')
               if not winner_name: continue
               
               # Find Series
               for s in self.playoff_series:
                   if s['winner']: continue # Already done
                   
                   t1 = s['t1']
                   t2 = s['t2']
                   
                   if g.home_team.id in [t1.id, t2.id] and g.away_team.id in [t1.id, t2.id]:
                       # Found Series
                       if t1.name == winner_name:
                           s['w1'] += 1
                       else:
                           s['w2'] += 1
                       series_updated = True
                       
                       # Check Series End
                       if s['w1'] >= 4:
                           s['winner'] = t1
                           print(f"DEBUG: Series {s['id']} Winner: {t1.name}")
                       elif s['w2'] >= 4:
                           s['winner'] = t2
                           print(f"DEBUG: Series {s['id']} Winner: {t2.name}")
                            
                       # Gamification Hook: Series Win
                       if s['winner'] and s['winner'].id == self.user_team_id:
                            self.add_gm_score(50, "Playoff Series Win")
                            if s['round'] == 1:
                                self.unlock_achievement("playoff_bound", "Playoff Competitor", "Win a playoff series.")
                       break
        
        # 2. Check Round Completion
        round1_series = [s for s in self.playoff_series if s['round'] == 1]
        round2_series = [s for s in self.playoff_series if s['round'] == 2]
        
        if round1_series and all(s['winner'] is not None for s in round1_series) and not round2_series:
            # Round 1 Done -> Create Finals
            w1 = round1_series[0]['winner']
            w2 = round1_series[1]['winner']
            
            # Start Finals
            print("DEBUG: Starting Finals")
            final_series = {"id": "SF", "t1": w1, "t2": w2, "w1": 0, "w2": 0, "round": 2, "winner": None}
            self.playoff_series.append(final_series)
            self._schedule_next_playoff_games()
            
        elif round2_series and round2_series[0]['winner']:
            # Finals Done -> Season Over
            champion = round2_series[0]['winner']
            print(f"DEBUG: SEASON OVER! Champion: {champion.name}")
            
            # Gamification Hook: Championship
            if champion.id == self.user_team_id:
                self.add_gm_score(1000, "Championship Title")
                self.unlock_achievement("champion", "National Champion", "Win the TPBL Title.")
                self.celebration_pending = True # Flag for UI
                
            # Do nothing logic-wise, UI should show "Season Fin" or Offseason button
            pass
        else:
            # Continue scheduling games for active series
            self._schedule_next_playoff_games()

    def _schedule_next_playoff_games(self):
        # Determine next game number for active series
        game_scheduled = False
        
        for s in self.playoff_series:
            if s['winner']: continue # Series over
            
            # Create next game
            game_num = s['w1'] + s['w2'] + 1
            
            # Home Court Logic usually 2-2-1-1-1.
            # G1, G2: Higher Seed (t1) Home
            # G3, G4: Lower Seed (t2) Home
            # G5: t1
            # G6: t2
            # G7: t1
            is_t1_home = True
            if game_num in [3, 4, 6]:
                is_t1_home = False
                
            home = s['t1'] if is_t1_home else s['t2']
            away = s['t2'] if is_t1_home else s['t1']
            
            g = Game(
                id=f"P_{s['id']}_G{game_num}", # unique ID
                day=self.current_day,
                home_team=home,
                away_team=away
            )
            # Tag the series info in game object? 
            # Not strictly supported by Game class yet, but ID helps.
            
            self.schedule.append(g)
            game_scheduled = True
            
        if not game_scheduled:
            # Maybe Offseason or waiting?
            pass

        # Update AI Strategies (Legacy Support)
        self._update_ai_strategies()

    def get_team(self, team_id: str) -> Optional[Team]:
        for team in self.teams:
            if team.id == team_id:
                return team
        return None

    def get_user_team(self) -> Optional[Team]:
        return self.get_team(self.user_team_id)

    def get_all_players(self) -> List[Player]:
        return self.players

    def start_new_season(self):
        """Resets the state for a new season."""
        self.season_year += 1
        self.current_day = 1
        self.schedule = [] # Clear schedule
        # self.playoff_series = [] # Reset playoffs MOVED to finalize_offseason
        self.season_progression_log = {} # Clear logs
        self.retired_players = [] 
        
        # Draft State
        self.is_draft_active = False 
        self.draft_order = [] # List[TeamID]
        self.draft_picks = [] # List[Dict] {round, pick, team, player}
        self.current_draft_pick_index = 0
        self.draft_class = [] # List[Player]
        
        # 1. Age Increase & Stats Reset
        for p in self.players:
            p.age += 1
            p.years_on_team += 1 # Loyalty Metric
            
            # Archive Stats if they played
            if p.stats.get("games", 0) > 0:
                history_entry = p.stats.copy()
                history_entry["year"] = self.season_year - 1
                history_entry["team_id"] = p.team_id
                if not hasattr(p, "history"): p.history = []
                p.history.append(history_entry)
            
            # Reset Stats Moved to finalize_offseason()
            # p.stats = {"games": 0, "pts": 0, "reb": 0, "ast": 0}

        # 2. Retirements
        self._handle_retirements()

        # 3. Progression (Growth/Decline)
        self._handle_progression()
        
        # 3.5 AI Renewals (Before Expiry)
        self._ai_process_renewals()
        
        # 3.6 Reset Negotiation Patience (New Season = Fresh Start)
        print("DEBUG: Resetting Player Negotiation Patience/Status...")
        for p in self.players:
            # Unlock negotiation for everyone (except those signed internally logic handles elsewhere)
            # Actually, standard is: If walked away last year, try again this year.
            p.negotiation_allowed = True
            
            # Recover Patience
            current_p = getattr(p, "negotiation_patience", 3)
            # Logic: Recover +2 patience per season, up to max
            # If they were at 0 (Walk Away), now they are at 2 (Warning) or 3 (Neutral)
            p.negotiation_patience = min(getattr(p, "negotiation_max_patience", 3), current_p + 3) # Full reset effectively
            # Ensure at least 3
            if p.negotiation_patience < 3: p.negotiation_patience = 3

        # 4. Contracts (Expiry)
        self._handle_contracts()

        # 5. Rookie Generation (Fills draft_class)
        self._generate_rookies()
        self.scouting_points = 50 # Reset points
        
        # 6. Schedule is generated AFTER draft completion
        
        # 7. Reset Team Records MOVED to finalize_offseason
        # for t in self.teams:
        #     t.wins = 0
        #     t.losses = 0

    def _handle_progression(self):
        """
        Updates player OVR based on Age and Potential.
        Phase 41: Includes "User Favor" logic.
        """
        # 1. Identify User Team and Calculate Favor Scores
        # 1. League-Wide Performance Bonus (Previously User Favor)
        # Calculate Score for ALL players to determine League S/A Tiers
        s_tier_ids = [] # Global Top 5
        a_tier_ids = [] # Global Rank 6-15
        
        scored_players = []
        for p in self.players:
            # Skip if no stats (didn't play)
            if p.stats.get("games", 0) == 0: continue
            
            s = p.stats
            # Formula: (Games*5) + Pts + Ast*1.5 + Reb*1.2 + Stl*2 + Blk*2 - To*1.5
            score = (s.get("games", 0) * 5) + \
                    s.get("pts", 0) + \
                    (s.get("ast", 0) * 1.5) + \
                    (s.get("reb", 0) * 1.2) + \
                    (s.get("stl", 0) * 2.0) + \
                    (s.get("block", 0) * 2.0) - \
                    (s.get("to", 0) * 1.5)
            scored_players.append((p, score))
        
        # Sort by score descending
        scored_players.sort(key=lambda x: x[1], reverse=True)
        
        # Assign Global Tiers
        for idx, (p, score) in enumerate(scored_players):
            if idx < 5: # Top 5 (MVP Candidates)
                s_tier_ids.append(p.id)
                print(f"DEBUG: {p.mask_name} ({p.team_id}) is S-Tier Bonus (Score: {score:.1f})")
            elif idx < 15: # Rank 6-15 (All-League)
                a_tier_ids.append(p.id)
                print(f"DEBUG: {p.mask_name} ({p.team_id}) is A-Tier Bonus (Score: {score:.1f})")

        for p in self.players:
            # Skip if retired
            
            # --- 1. Determine Target Gain/Loss ---
            target_gain = 0
            
            # --- User Favor Tier Check ---
            is_s_tier = p.id in s_tier_ids
            is_a_tier = p.id in a_tier_ids
            
            # --- Age Logic (User Refined: Potential = Speed) ---
            # --- Age Logic (User Refined: Potential = Speed) ---
            if p.age <= 28:
                # Growth Phase (Potential determines Speed)
                # User Req: If OVR >= 88, Potential NO LONGER affects growth.
                # Treat them like Prime Phase (Standard random growth).
                if p.ovr >= 88:
                    rand = random.random()
                    if rand < 0.20: target_gain = 3
                    elif rand < 0.45: target_gain = 2
                    elif rand < 0.70: target_gain = 1
                    else: target_gain = 0
                    print(f"DEBUG: {p.mask_name} (OVR {p.ovr} >= 88) ignores Potential -> Standard Growth (+{target_gain})")
                else:
                    # Normal Potential Logic
                    pot = p.potential
                    
                    if pot >= 100:
                        target_gain = random.randint(5, 7)
                    elif pot >= 90:
                        target_gain = random.randint(3, 5)
                    elif pot >= 80:
                        target_gain = 3
                    elif pot >= 70:
                        target_gain = random.randint(1, 3)
                    else:
                        target_gain = random.randint(0, 1)
                    
                    # Double Growth Mechanic
                    if pot >= 80 and random.random() < 0.10:
                        print(f"DEBUG: {p.mask_name} triggered DOUBLE GROWTH! ({target_gain} -> {target_gain*2})")
                        target_gain *= 2

                # Favor Bonus (Apply to both paths)
                if is_s_tier: target_gain = max(target_gain + 1, 3) 
                elif is_a_tier: target_gain += 1
                
            elif p.age <= 32: # Extended Prime slightly? No, maintain manual logic. 
                # Let's say 29-32 is Prime now? Usually prime is late 20s.
                # User said "28之後潛力就不影響了". 
                # So > 28 is Prime/Decline.
                # Let's keep previous Prime logic for 29-32? Or just 29-30?
                # Previous manual said Prime 26-30. Now Growth is up to 28.
                # So Prime is 29-32? Or 29-30?
                # Let's assume Prime is 29-32 for now to give them some peak time.
                
                # Prime Phase (Updated Logic)
                # 20% chance: +3
                # 25% chance: +2
                # 25% chance: +1
                # 30% chance: +0
                rand = random.random()
                if rand < 0.20:
                    target_gain = 3
                elif rand < 0.45:
                    target_gain = 2
                elif rand < 0.70:
                    target_gain = 1
                else:
                    target_gain = 0
                
                if is_s_tier and target_gain == 0: target_gain = 1 
                
            else:
                # Decline Phase (> 32)
                # Base decay
                decline_chance = (p.age - 32) * 0.10 # Adjust start age to 32
                if random.random() < decline_chance:
                    target_gain = random.randint(-3, -1)
                
                # Favor Protection
                if is_s_tier:
                    # Rejuvenation: 50% chance to Flip negative to positive
                    if target_gain < 0:
                         target_gain = 0 # Prevent decay first
                         if random.random() < 0.5: target_gain = 1 # Growth
                    elif target_gain == 0:
                         if random.random() < 0.5: target_gain = 1
                
                elif is_a_tier:
                     # Frozen: Prevent decay
                     if target_gain < 0: target_gain = 0
                    
            # --- 2. Execute Attribute Growth ---
            if target_gain > 0:
                # User Req: High Capability (OVR >= 95) growth is harder.
                if p.ovr >= 95:
                    # Resistance Mechanism: 50% chance to HALVE growth (rounded down)
                    if random.random() < 0.50:
                         original_gain = target_gain
                         target_gain = target_gain // 2
                         print(f"DEBUG: {p.mask_name} (OVR {p.ovr}) hit RESISTANCE! ({original_gain} -> {target_gain})")

                # User Req: OVR Hard Cap at 99.
                if p.ovr >= 99:
                    target_gain = 0
                elif (p.ovr + target_gain) > 99:
                    target_gain = 99 - p.ovr

            # Capture initial diff calculated from target_gain (which might be 0)
            ovr_change = target_gain
            
            # Helper to get attr dict
            def get_attr_snapshot(pl):
                return {
                    "2pt": pl.attributes.two_pt,
                    "3pt": pl.attributes.three_pt,
                    "pass": pl.attributes.passing,
                    "reb": pl.attributes.rebound,
                    "def": pl.attributes.defense,
                    "stl": pl.attributes.steal,
                    "blk": pl.attributes.block
                    # omit consistency for UI cleanliness unless requested
                }

            old_attrs = get_attr_snapshot(p)

            if target_gain != 0:
                self._apply_attribute_changes(p, target_gain)
            
            new_attrs = get_attr_snapshot(p)
            attr_diffs = {k: new_attrs[k] - old_attrs[k] for k in old_attrs}

            # Store in Data Transfer Object (DTO) style
            if not hasattr(self, 'progression_data'): self.progression_data = {}
            self.progression_data[p.id] = {
                "name": p.mask_name,
                "age": p.age,
                "team_id": p.team_id,
                "old_ovr": p.ovr - ovr_change,
                "new_ovr": p.ovr,
                "diff": ovr_change,
                "attr_diffs": attr_diffs, # Detailed changes
                "new_attrs": new_attrs    # Current values
            }

    def _apply_attribute_changes(self, p: Player, target_gain: int):
        """
        Distributes OVR gain/loss into specific attributes based on the User's Curve.
        """
        start_ovr = p.ovr
        current_ovr = start_ovr
        changes_map = {} # Key: Attr, Val: Amount
        
        # Safety break
        attempts = 0
        max_attempts = 100 # Increased limit for +1 granularity
        
        # User Req: Alternating Offense / Defense
        # Define pools
        offense_pool = ["two_pt", "three_pt", "passing", "consistency"]
        defense_pool = ["defense", "steal", "block", "rebound"]
        
        # Random start
        is_offense_turn = random.choice([True, False])
        
        while attempts < max_attempts: 
            # Check if we met target
            if target_gain > 0:
                if current_ovr >= start_ovr + target_gain: break
            else:
                 if current_ovr <= start_ovr + target_gain: break
            
            attempts += 1
            
            # Select Pool
            if is_offense_turn:
                pool = offense_pool
            else:
                pool = defense_pool
            
            # Build valid keys from pool
            # Note: consistency is in attributes but key map needed
            key = random.choice(pool)
            
            # Toggle for next loop
            is_offense_turn = not is_offense_turn
            
            # Map key to attribute field name
            attr_name_map = {
                "two_pt": "two_pt", "three_pt": "three_pt", 
                "passing": "passing", "consistency": "consistency",
                "rebound": "rebound", "defense": "defense", 
                "steal": "steal", "block": "block"
            }
            field_name = attr_name_map[key]
            
            # --- Guard Block Restriction ---
            # User Req: Guards' block basically won't rise.
            if key == "block" and p.pos in ["PG", "SG", "控球後衛", "得分後衛"]:
                # 90% chance to skip this attribute and pick another one
                if random.random() < 0.90:
                    continue

            val = getattr(p.attributes, field_name)
            
            amount = 0
            
            # --- GROWTH LOGIC (User Refined: Loop by 1 + 10% Jackpot) ---
            if target_gain > 0:
                # Breakthrough Logic
                # User Req: If value is 50 (or <= 50), NO breakthrough.
                # Only attributes > 50 and < 70 can breakthrough.
                can_breakthrough = (val > 50 and val < 70)
                
                if can_breakthrough and random.random() < 0.10:
                     amount = 10
                     print(f"DEBUG: {p.mask_name} BREAKTHROUGH in {key}! (+10)")
                else:
                     amount = 1
                
                # Cap check
                if val >= 99: 
                    amount = 0
                elif val + amount > 99: 
                    amount = 99 - val
                
                if amount > 0:
                    setattr(p.attributes, field_name, val + amount)
                    changes_map[key] = changes_map.get(key, 0) + amount

            # --- DECLINE LOGIC ---
            else:
                 amount = random.randint(1, 3)
                 new_val = max(25, val - amount)
                 setattr(p.attributes, field_name, new_val)
                 changes_map[key] = changes_map.get(key, 0) - amount
            
            # Recalculate OVR to check progress
            p.update_ovr()
            current_ovr = p.ovr
            
        # Log Result
        if changes_map:
            diff_ovr = current_ovr - start_ovr
            sign = "+" if diff_ovr >= 0 else ""
            details = ", ".join([f"{k} {v:+}" for k, v in changes_map.items()])
            log_str = f"{p.mask_name} (OVR {start_ovr}->{current_ovr} {sign}{diff_ovr}): {details}"
            
            if p.team_id not in self.season_progression_log:
                self.season_progression_log[p.team_id] = []
            self.season_progression_log[p.team_id].append(log_str)

    def _handle_contracts(self):
        """
        Decrements contract length and releases expired players.
        """
        expired_players = []
        for p in self.players:
            # Decrement
            if p.contract_length > 0:
                p.contract_length -= 1
            
            # Check Expiry
            if p.contract_length == 0:
                expired_players.append(p)

        for p in expired_players:
            # If already FA, ignore
            if p.team_id == "T00":
                continue
                
            # Release to clean slate
            old_team = self.get_team(p.team_id)
            if old_team:
                self.release_player(p)
                # Maybe add a notification or log?
                # "Player X contract expired and is now a Free Agent."

    def _handle_retirements(self):
        to_retire = []
        for p in self.players:
            chance = 0
            # Phase 43: Exponential Retirement > 36
            # User Req: "Age > 36, exponential chance"
            if p.age >= 36:
                 # Formula: 10 * 2^(Age-36)
                 # 36: 10%
                 # 37: 20%
                 # 38: 40%
                 # 39: 80%
                 # 40: 160% (Force)
                 exponent = p.age - 36
                 chance = 10 * (2 ** exponent)
            
            # Ability-Based Retirement Delay (User Req)
            # High OVR reduces retirement desire
            if chance > 0:
                if p.ovr >= 90:
                    # Superstar: Drastically reduce chance (80% reduction)
                    print(f"DEBUG: {p.mask_name} (Age {p.age}, OVR {p.ovr}) slows retirement! (Chance {chance}% -> {chance*0.2}%)")
                    chance *= 0.2
                elif p.ovr >= 80:
                    # Starter: Reduce chance (50% reduction)
                    print(f"DEBUG: {p.mask_name} (Age {p.age}, OVR {p.ovr}) slows retirement! (Chance {chance}% -> {chance*0.5}%)")
                    chance *= 0.5
            
            # S-Tier Favor Protection: Reduce chance by half for "Legends"
            # (Optional, but fits "Simulate forever" if user loves a player)
            # Not implemented yet to respect strict request.
            
            if chance > 0 and random.randint(1, 100) <= chance:
                to_retire.append(p)
        
        for p in to_retire:
            self._check_hall_of_fame(p)
            self.release_player(p) # Move to FA first (or just remove completely)
            # Remove from global player list
            if p in self.players:
                self.players.remove(p)
            
            # Remove from FA if there
            fa_team = self.get_team("T00")
            if fa_team and p in fa_team.roster:
                fa_team.roster.remove(p)

            self.retired_players.append(p)

        self.draft_class: List[Player] = []
        self.scouting_points = 50

    def scout_player(self, player_id: str) -> tuple[bool, str]:
        if self.scouting_points < 10:
            return False, "Not enough scouting points!"
        
        p = next((p for p in self.draft_class if p.id == player_id), None)
        if not p:
            return False, "Player not found in draft class."
            
        if p.is_scouted:
            return False, "Player already scouted."
            
        p.is_scouted = True
        self.scouting_points -= 10
        self.save_game(1)
        return True, "Player scouted! Attributes revealed."

    def complete_draft(self):
        """
        Moves draft class to active players (simulates draft).
        Assigns best rookies to worst teams (reverse order).
        Remaining go to FA.
        Then generates schedule.
        """
        # Sort draft class by OVR (Best first)
        sorted_rookies = sorted(self.draft_class, key=lambda p: p.ovr, reverse=True)
        
        # Sort teams by last season record (Worst first gets best pick)
        # Using current wins/losses which were reset? 
        # Crap, start_new_season resets wins/losses.
        # We should have stored standings somewhere.
        # For now, just random order or alphabetical for AI. 
        # Ideally we'd store 'last_season_rank'.
        # Let's just iterate teams randomly for now.
        teams_to_pick = [t for t in self.teams if t.id != "T00"]
        
        # User manual pick? 
        # For Phase 11, let's assume User has already "signed"/picked from ScoutingView if implemented.
        # If ScoutingView allows "signing" rookies, they might already be in user team?
        # Let's assume ScoutingView acts as "Draft Board" where users can 'Sign' (Draft) them using Cap Space?
        # Actually standard draft uses picks.
        # Let's simplify: ScoutingView has "Sign Rookie" button (Market style).
        # Any rookies remaining in gm.draft_class at "complete_draft" are distributed to AI or FA.
        
        for p in list(sorted_rookies): # Copy list
            if p.team_id != "DRAFT": 
                # Already signed/picked by user
                if p not in self.players:
                    self.players.append(p)
                continue
                
            # Assign to random team or FA
            prospect_team = random.choice(teams_to_pick)
            # Check roster limit? (skip for now)
            
            p.team_id = prospect_team.id
            prospect_team.roster.append(p)
            self.players.append(p)
            
        self.draft_class = [] # Clear
        
        # NOW generate schedule
        self._generate_schedule()

    def _generate_chinese_name(self) -> str:
        """Generates a random Chinese Name."""
        last_names = ["王", "陳", "李", "張", "林", "劉", "黃", "吳", "蔡", "楊", "許", "鄭", "謝", "郭", "洪", "曾", "邱", "廖", "賴", "徐", "周", "葉", "蘇", "莊", "呂", "江", "何", "蕭", "羅", "高", "潘", "簡", "朱", "鍾", "彭", "游", "詹", "胡", "施", "沈"]
        first_names = ["志明", "志偉", "建國", "建華", "俊傑", "俊宏", "家豪", "家瑋", "冠宇", "冠廷", "宗翰", "柏翰", "彥廷", "彥宏", "承恩", "承翰", "宇軒", "宇欣", "品睿", "品宏", "浩宇", "浩然", "子軒", "子維", "偉哲", "偉豪", "智瑋", "智豪", "信宏", "信豪", "文傑", "文豪", "明哲", "明弘", "士豪", "士軒", "家榮", "家弘", "建宏", "建志"]
        return random.choice(last_names) + random.choice(first_names)

    def _generate_rookies(self):
        """Generates a draft class of young players with Chinese names."""
        self.draft_class = []
        
        # Determine number of rookies (Draft is 2 rounds of N teams)
        num_teams = len([t for t in self.teams if t.id != "T00"])
        num_rookies = max(20, num_teams * 4) # Ensure enough players for 2 rounds + undrafted
        
        for i in range(num_rookies):
            age = random.randint(18, 22)
            pos = random.choice(["PG", "SG", "SF", "PF", "C"])
            
            # Potential & OVR Distribution
            roll = random.random()
            if roll < 0.05: # Generational
               pot = random.randint(90, 99)
               start_ovr = random.randint(70, 80)
            elif roll < 0.20: # All-Star
               pot = random.randint(80, 89)
               start_ovr = random.randint(65, 75)
            elif roll < 0.60: # Role Player
               pot = random.randint(70, 79)
               start_ovr = random.randint(55, 65)
            else: # Bench
               pot = random.randint(50, 69)
               start_ovr = random.randint(40, 55)
               
            pid = f"R{self.season_year}{i+1:03d}"
            name = self._generate_chinese_name()
            
            # Base Attributes centered around start_ovr
            attrs = {
                "2pt": max(30, start_ovr + random.randint(-10, 10)),
                "3pt": max(30, start_ovr + random.randint(-15, 15)),
                "rebound": max(30, start_ovr + random.randint(-10, 10)),
                "pass": max(30, start_ovr + random.randint(-10, 10)),
                "consistency": random.randint(40, 80),
                "block": max(30, start_ovr + random.randint(-15, 15)),
                "steal": max(30, start_ovr + random.randint(-10, 10)),
                "defense": max(30, start_ovr + random.randint(-5, 5))
            }
            
            # Create Attributes object
            p_attrs = PlayerAttributes.from_dict(attrs)
            p_attrs.defense = attrs["defense"]
            
            # Create Player (Fixing Arguments)
            p = Player(
                id=pid,
                real_name=name,
                mask_name=name,
                team_id="DRAFT",
                pos=pos,
                salary=0.5,
                age=age,
                attributes=p_attrs,
                potential=pot,
                ovr=start_ovr, # Set initial OVR
                is_scouted=True # User Request: No scouting needed
            )
            # Recalculate OVR to be sure
            p.update_ovr()
            
            # Normalize OVR
            p.ovr = int((p.ovr + start_ovr)/2)
            
            self.draft_class.append(p)
            
        print(f"DEBUG: Generated {len(self.draft_class)} Rookies.")

    def init_draft(self):
        """Initializes Random Draft Order and Starts Draft."""
        self.is_draft_active = True
        self.current_draft_pick_index = 0
        self.draft_picks = []
        
        # Ensure Draft Class Exists
        if not self.draft_class:
            print("DEBUG: Draft Class Empty. Generating Rookies...")
            self._generate_rookies()
        
        # Determine Order based on Performance
        # Logic: 
        # 1. Identify Playoff Teams (Champion=Last, RunnerUp=2ndLast) -> Sorted by Elimination Round then Regular Season Wins?
        #    Currently Playoff logic determines 'Champion'.
        #    Let's simplify: 
        #    - Non-Playoff Teams: Sorted by Regular Season Wins (Ascending) -> Worse record = Early pick.
        #    - Playoff Teams: Placed after Non-Playoff. Sorted by Elimination? 
        #      Winner is last. Runner up second last.
        #    For now, simpler approach requested: "Reverse Standings" generally, maybe specific override for finalists.
        
        
        active_teams = [t for t in self.teams if t.id != "T00"]
        print(f"DEBUG: init_draft. Active Teams: {len(active_teams)}")
        
        # Sort by Wins (Ascending) = Worst record first
        # Tie-breaker: Lower Loss (Desc) or Random
        active_teams.sort(key=lambda t: (t.wins, t.losses)) 
        
        # Champion Logic Override:
        # If we know the champion, move them to the end.
        if hasattr(self, 'playoff_series') and self.playoff_series:
             # Find Winner of Round 2 (Finals)
             final = next((s for s in self.playoff_series if s['round'] == 2), None)
             if final and final.get('winner'):
                 champ = final['winner']
                 if champ in active_teams:
                     active_teams.remove(champ)
                     active_teams.append(champ) # Move to last
                     
             # Find Loser of finals? (Runner Up) -> 2nd Last
             if final and final.get('winner'):
                  winner = final['winner']
                  t1 = final['t1']
                  t2 = final['t2']
                  runner_up = t1 if t1 != winner else t2
                  if runner_up in active_teams:
                      active_teams.remove(runner_up)
                      active_teams.insert(len(active_teams)-1, runner_up) # Insert before champ
        
        # Round 1 & 2
        self.draft_order = [t.id for t in active_teams] * 2
        
        # Save State Immediately
        self.save_game(1)

    def resolve_draft_pick(self, player_id: str = None):
        """Resolves current pick. AI autos, or User specific."""
        if self.current_draft_pick_index >= len(self.draft_order):
            self.is_draft_active = False
            return

        team_id = self.draft_order[self.current_draft_pick_index]
        team = self.get_team(team_id)
        
        picked_player = None
        
        # AI Logic
        if not player_id:
            available = [p for p in self.draft_class if p.team_id == "DRAFT"]
            if not available:
                self.current_draft_pick_index += 1
                return

            # Score = OVR*0.4 + Pot*0.6
            candidates = sorted(available, key=lambda p: (p.ovr*0.4 + p.potential*0.6), reverse=True)
            top_3 = candidates[:3]
            
            # Gap Check
            score1 = top_3[0].ovr*0.4 + top_3[0].potential*0.6
            score2 = top_3[1].ovr*0.4 + top_3[1].potential*0.6 if len(top_3) > 1 else 0
            
            # Lowered threshold from 5 to 2 based on user feedback
            if score1 > score2 + 2:
                 picked_player = top_3[0]
            else:
                 picked_player = random.choice(top_3)
        else:
            # User Manual Pick
            picked_player = next((p for p in self.draft_class if p.id == player_id), None)
            
        if picked_player:
            picked_player.team_id = team_id
            picked_player.years_on_team = 0
            team.roster.append(picked_player)
            self.players.append(picked_player)
            
            # Log
            # Pick number in round
            num_teams = len(self.draft_order) // 2
            pick_in_round = (self.current_draft_pick_index % num_teams) + 1
            round_num = 1 if self.current_draft_pick_index < num_teams else 2
            
            self.draft_picks.append({
                "round": round_num,
                "pick": int(pick_in_round),
                "team": team.name, 
                "player": f"{picked_player.mask_name} ({picked_player.pos} {picked_player.ovr})"
            })
            
            self.current_draft_pick_index += 1
            
        if self.current_draft_pick_index >= len(self.draft_order):
            self.is_draft_active = False
            self.schedule_post_draft()
            
        self.save_game(1)

    def schedule_post_draft(self):
        # 1. Move Undrafted Rookies to Free Agency
        undrafted = [p for p in self.draft_class if p.team_id == "DRAFT"]
        fa_team = self.get_team("T00")
        
        if not fa_team:
            # Create if missing (Should exist)
            fa_team = Team("T00", "Free Agents", "#333333")
            self.teams.append(fa_team)
            
        for p in undrafted:
            p.team_id = "T00"
            fa_team.roster.append(p)
            self.players.append(p) # Ensure they are in main pool if not already?
            # Wait, draft_class items are not in self.players until picked usually.
            # If we add them to FA, we must add to self.players.
            if p not in self.players:
                self.players.append(p)
                
            # Reset Negotiation State for Undrafted Rookies
            p.contract_length = 0
            # p.salary = ... (Already set in generation)
            p.years_on_team = 0
            p.negotiation_allowed = True
            p.negotiation_patience = 3
            p.negotiation_max_patience = 3
                
        # Clear Draft Class? No, keep for reference or clear next year.
        
        # 2. Finalize Offseason (Reset Stats)
        self.finalize_offseason()
        
        # 3. Generate Schedule
        # 3. Generate Schedule
        self._generate_schedule()

        # RE-ENFORCE SALARY CAP (User Request Update)
        # If Cap is unrealistic (e.g. 5000M), reset to new standard 70M
        if self.salary_cap > 200:
            self.salary_cap = 70.0 # 70M Hard Cap
            print(f"DEBUG: Salary Cap reset to {self.salary_cap}M based on new scale.")

    def calculate_market_value(self, player) -> float:
        """
        Calculates Fair Market Value (FMV) for a player in Millions.
        Base Formula: Exponential OVR curve.
        """
        # 1. Base Value by OVR
        # Curve (New Scale): 
        # OVR 90+ -> 10.0M - 15.0M
        # OVR 80+ -> 5.0M - 9.0M
        # OVR 70+ -> 1.5M - 4.0M
        
        # Formula: 0.5 + (OVR - 60)^2 * 0.012
        # 60 -> 0.5
        # 70 -> 0.5 + 100*0.012 = 1.7
        # 80 -> 0.5 + 400*0.012 = 5.3
        # 90 -> 0.5 + 900*0.012 = 11.3 (Matches 10-15 range)
        # 99 -> 0.5 + 1521*0.012 = 18.7 (Clamp to 15)
        
        base_ovr = max(60, player.ovr)
        base_val = 0.5 + ((base_ovr - 60) ** 2) * 0.012
        
        # 2. Potential Premium (Only for young players < 26)
        pot_premium = 0
        if player.age < 26 and player.potential > player.ovr:
            gap = player.potential - player.ovr
            pot_premium = gap * 0.1 # e.g. Gap 10 -> +1M
        
        # 3. Age Discount (Old players > 34)
        age_discount = 1.0
        if player.age > 34:
            age_discount = 0.8 # 20% off
        
        final_val = (base_val + pot_premium) * age_discount
        
        # Clamp
        final_val = max(0.5, final_val) # Min 0.5M
        final_val = min(15.0, final_val) # Max 15M (Supermax - Reduced)
        
        return round(final_val, 2)

    def negotiate_contract(self, player, offer_amount: float, offer_years: int) -> dict:
        """
        Determines player response to a contract offer.
        Returns: { "status": "accept"|"negotiate"|"reject"|"walk_away", "message": "..." }
        """
        # --- VALIDATION CHECKS (User Request) ---
        # 1. Team Restriction: Can only negotiate with Own Players or Free Agents.
        if player.team_id != "T00" and player.team_id != self.user_team_id:
             return {"status": "reject", "message": "我已經和別的球隊簽約了。（違規接觸！）"}
        
        # 2. Extension Restriction: Can only extend if contract <= 1 year left.
        # (Only applies if player is already on user team)
        if player.team_id == self.user_team_id and player.contract_length > 1:
             return {"status": "reject", "message": f"我的合約還有 {player.contract_length} 年才到期，現在談續約還太早了。"}
        # ----------------------------------------

        # 3. Initialize Mood/Patience if not present
        # 1. Calculate Loyalty & Performance Factors (From History)
        # We use History because current stats are reset in Post-Draft.
        last_season = player.history[-1] if player.history else {}
        
        # Tenure Factor (3% per year)
        tenure_discount = player.years_on_team * 0.03
        
        # Performance Factor (Did they play well?)
        perf_discount = 0.0
        if last_season:
            # Simple efficiency metric
            g = last_season.get('games', 0)
            if g > 0:
                ppg = last_season.get('pts', 0) / g
                eff = (last_season.get('pts', 0) + last_season.get('reb', 0) + last_season.get('ast', 0)) / g
                
                # If Star Performance (PPG > 15 or Eff > 25)
                if ppg > 15 or eff > 25:
                    perf_discount = 0.05 # 5% Happy Bonus
                    # "I love playing here."
                
                # If they were a starter (usage check? or minutes? usually games > 0 is enough for now)
        
        # Franchise Icon Bonus (Tenure > 4 + Good Perf)
        icon_discount = 0.0
        if player.years_on_team >= 4 and perf_discount > 0:
            icon_discount = 0.10 # "This is my home."
            
        # Total Loyalty Discount (Max 40%)
        loyalty_factor = min(0.40, tenure_discount + perf_discount + icon_discount)
        
        # 2. Initialize Mood/Patience
        # Loyal players are more patient.
        base_patience = 3
        if loyalty_factor >= 0.15: base_patience = 4
        if loyalty_factor >= 0.30: base_patience = 5
        
        if not hasattr(player, "negotiation_patience"):
            player.negotiation_allowed = True
            player.negotiation_patience = base_patience
            player.negotiation_max_patience = base_patience # Store for UI
        
        # 3. Check if already walked away
        if not getattr(player, "negotiation_allowed", True) or player.negotiation_patience <= 0:
             return {"status": "walk_away", "message": "我說過我不談了，自由市場見。"}

        fmv = self.calculate_market_value(player)
        
        # 4. Determine Internal Ask (Greed)
        greed = 1.05
        if player.ovr >= 90: greed = 1.15
        elif player.ovr >= 80: greed = 1.10
        
        # Term Factor (User Request: Years affect amount)
        # 1 Year: +5% (Risk Premium)
        # 2-3 Years: 0% (Standard)
        # 4-5 Years: -5% (Security Discount) - OLDER players might love this.
        # But Young Stars might WANT short term to bet on themselves?
        # Let's simplify: 
        # 1 Year offer -> They ask for 1.05x
        # 5 Year offer -> They ask for 0.95x
        term_factor = 1.0
        if offer_years == 1: term_factor = 1.05
        elif offer_years >= 4: term_factor = 0.95
        
        # Apply Loyalty to ASK
        # Note: We removed the "Star Penalty" (0.5x). Truly loyal stars now give full discount.
        # Ask = FMV * Greed * Loyalty * Term
        internal_ask = (fmv * greed) * (1.0 - loyalty_factor) * term_factor
        internal_ask = round(internal_ask, 2)
        
        # 5. Evaluate Offer
        if offer_amount >= internal_ask * 0.98:
             msg = "成交！我愛這支球隊。" if loyalty_factor > 0.1 else "這報價很公道，我接受。"
             return {"status": "accept", "message": msg, "ask": internal_ask}
        else:
             # Reject & Patience Penalty
             player.negotiation_patience -= 1
             remaining = player.negotiation_patience
             
             if remaining <= 0:
                 player.negotiation_allowed = False
                 return {"status": "walk_away", "message": "這談不下去了。(憤而離席)"}
             
             # Hint
             reason = "太低了"
             if loyalty_factor > 0.2: reason = "就算我有打折，這也太低了"
             
             diff_pct = (internal_ask - offer_amount) / internal_ask
             hint = "再加一點" if diff_pct < 0.1 else "差得遠了"
             
             return {
                 "status": "negotiate", 
                 "message": f"{reason}，{hint}。我至少要 ${internal_ask}M。", 
                 "ask": internal_ask, 
                 "patience": remaining
             }

    def calculate_team_payroll(self, team_id: str) -> float:
        """Calculates total salary of a team."""
        team = self.get_team(team_id)
        if not team: return 0.0
        return sum(p.salary for p in team.roster)

    def _calculate_and_store_awards(self, champion_team: Team):
        """Calculates Season MVP and Finals MVP, then stores in league history."""
        # MVP: Player with highest Efficiency on a Top 4 team (Winning bias)
        # Efficiency = PTS + REB + AST + STL + BLK - TO (Simplified)
        candidates = []
        for p in self.players:
            stats = p.stats
            games = stats.get("games", 0)
            if games < 10: continue
            
            # Simple EFF calculation
            eff = stats.get("pts", 0) + stats.get("reb", 0) + stats.get("ast", 0) + stats.get("stl", 0) + stats.get("blk", 0)
            
            # Win Factor
            team = self.get_team(p.team_id)
            if not team: continue
            win_pct = team.wins / max(1, (team.wins + team.losses))
            
            score = (eff / games) * (1 + win_pct) # Good stats on winning team matters
            candidates.append((p, score))
            
        candidates.sort(key=lambda x: x[1], reverse=True)
        mvp_player = candidates[0][0] if candidates else None
        mvp_name = f"{mvp_player.mask_name} ({self.get_team(mvp_player.team_id).name})" if mvp_player else "N/A"
        
        # Gamification Hook: MVP
        if mvp_player and mvp_player.team_id == self.user_team_id:
             self.add_gm_score(200, "MVP Award")
             self.unlock_achievement("mvp_finder", "MVP Mentor", "Have a player win MVP.")

        # FMVP: Best player on Champion Team (Highest GameScore or OVR)
        champion_players = champion_team.roster
        if champion_players:
            # Sort by OVR for now as we don't track pure Finals stats yet
            # Or use total season stats?
            # Let's use Season Stats as proxy for "Star Player"
            fmvp_player = max(champion_players, key=lambda p: (p.stats.get('pts',0) + p.stats.get('reb',0)*1.5 + p.stats.get('ast',0)*2))
            fmvp_name = f"{fmvp_player.mask_name} ({champion_team.name})"
            
            # Gamification Hook: FMVP
            if fmvp_player and fmvp_player.team_id == self.user_team_id:
                 self.add_gm_score(200, "Finals MVP Award")
                 self.unlock_achievement("fmvp_finder", "Finals MVP Mentor", "Have a player win Finals MVP.")
        else:
            fmvp_name = "N/A"
            
        # All-League First Team Selection
        # Strategy: Best 2 Guards, 2 Forwards, 1 Center based on Efficiency adjusted by Team Wins
        # candidates list already has (player, score).
        
        all_league_team = []
        guards = []
        forwards = []
        centers = []
        
        for p, score in candidates:
             pos = p.pos
             if "G" in pos or "後衛" in pos: guards.append(p)
             elif "F" in pos or "前鋒" in pos: forwards.append(p)
             elif "C" in pos or "中鋒" in pos: centers.append(p)
        
        # Select Top 2 G, 2 F, 1 C
        # If not enough at pos, fill with next best overall
        
        # Helper to format string
        def fmt(p): return f"{p.mask_name} ({self.get_team(p.team_id).name})" if p else "N/A"
        
        # Guards
        g1 = guards[0] if len(guards) > 0 else None
        g2 = guards[1] if len(guards) > 1 else None
         # Forwards
        f1 = forwards[0] if len(forwards) > 0 else None
        f2 = forwards[1] if len(forwards) > 1 else None
        # Centers
        c1 = centers[0] if len(centers) > 0 else None
        
        # Fallback Logic (simplified, assuming enough players exist)
        
        all_league_team = [
            {"pos": "G", "name": fmt(g1)},
            {"pos": "G", "name": fmt(g2)},
            {"pos": "F", "name": fmt(f1)},
            {"pos": "F", "name": fmt(f2)},
            {"pos": "C", "name": fmt(c1)},
        ]
            
        entry = {
            "year": self.season_year,
            "champion": champion_team.name,
            "champion_record": f"{champion_team.wins}-{champion_team.losses}",
            "mvp": mvp_name,
            "fmvp": fmvp_name,
            "all_league": all_league_team
        }
        self.league_history.append(entry)
        print(f"DEBUG: Added History Entry: {entry}")

    def finalize_offseason(self):
        """Resets stats and team records for the new season."""
        print("DEBUG: Finalizing Offseason - Resetting Stats and Records.")
        
        # Reset Playoffs
        self.playoff_series = []
        
        # Reset Player Stats
        for p in self.players:
            p.stats = {"games": 0, "pts": 0, "reb": 0, "ast": 0}
            
        # Reset Team Records
        for t in self.teams:
            t.wins = 0
            t.losses = 0
        # But if we clear, ScoutingView might show empty.
        # User might want to see who went undrafted?
        # Usually checking "Free Market" is next.
        
    def _update_ai_strategies(self):
        """
        Updates strategy settings for all AI teams based on their roster strengths.
        Runs daily to account for trades/signings/injuries (future).
        """
        for team in self. teams:
            if team.id == self.user_team_id:
                continue
                
            # 1. Scoring Options (Top 3 Players by OVR)
            # Find best offensive players (using OVR for now, could be specific stats)
            sorted_roster = sorted(team.roster, key=lambda p: p.ovr, reverse=True)
            
            # Reset options
            # Option 1: Best Player
            opt1 = str(sorted_roster[0].id) if len(sorted_roster) > 0 else None
            # Option 2: 2nd Best
            opt2 = str(sorted_roster[1].id) if len(sorted_roster) > 1 else None
            # Option 3: 3rd Best
            opt3 = str(sorted_roster[2].id) if len(sorted_roster) > 2 else None
            
            team.strategy_settings["scoring_options"] = [opt1, opt2, opt3]
            
            # 2. Rotation Settings
            # ++: Top 2
            # +:  Next 3 (Starters)
            #  :  Next 3 (Rotation)
            # -:  Next 2 (Deep Bench)
            # --: Rest
            rotation_map = {}
            for i, p in enumerate(sorted_roster):
                if i < 2:
                    role = "++"
                elif i < 5:
                    role = "+"
                elif i < 8:
                    role = " "
                elif i < 10:
                    role = "-"
                else:
                    role = "--"
                rotation_map[str(p.id)] = role
            
            team.strategy_settings["rotation_settings"] = rotation_map
            
            # 3. Tactics Selection
            # Check Top 8 (Rotation) average attributes
            active_roster = sorted_roster[:8]
            if not active_roster: continue
            
            avg_3pt = sum(p.attributes.three_pt for p in active_roster) / len(active_roster)
            avg_2pt = sum(p.attributes.two_pt for p in active_roster) / len(active_roster)
            
            # Logic
            # If 3PT is elite (> 80) or significantly better than 2PT -> Outside
            # If 2PT is significantly better -> Inside
            # Else -> Balanced
            
            if avg_3pt >= 75:
                # Strong shooting team
                tactic = "Outside"
            elif avg_2pt > avg_3pt + 10:
                # Dominant inside, weak outside
                tactic = "Inside"
            else:
                tactic = "Balanced"
                
            team.strategy_settings["tactics"] = tactic
            
            # print(f"DEBUG: AI Strategy Updated for {team.name}: {tactic}, Options: {[p.mask_name for p in team.roster if str(p.id) in [opt1, opt2, opt3]]}")

    def advance_day(self):
        """Advances the simulation by one day."""
        if self.mode != "season":
             return
             
        # 0. AI Strategy Update (Refactored)
        self._update_ai_strategies()

        # 1. Simulate Games (if any)
        todays_games = [g for g in self.schedule if g.day == self.current_day]

        self._generate_schedule()
        
        # Phase 14: AI Free Agency
        # Run AFTER invalidation/draft so rosters are ready to be filled
        self._ai_process_free_agency()

    def play_day(self):
        """Simulates all games for the current day and advances."""
        games = self.get_todays_games()
        results = []
        
        for game in games:
            if game.played:
                continue
                
            # Simulate
            result = MatchEngine.simulate_game(game.home_team, game.away_team)
            
            # Phase 64: League Records Check
            if "box_score" in result:
                for pid, stats in result["box_score"].items():
                    # Verify Player Object exists in teams
                    p_obj = next((p for p in game.home_team.roster if p.id == pid), None)
                    if not p_obj:
                        p_obj = next((p for p in game.away_team.roster if p.id == pid), None)
                    
                    if p_obj:
                        self.check_new_records(p_obj, stats)

            # Update Game Object
            game.played = True
            game.result = result
            
            # --- Gamification Hook ---
            winner_team = game.home_team if result["home_score"] > result["away_score"] else game.away_team
            if winner_team.id == self.user_team_id:
                self.add_gm_score(10, "Season Win")
                self.unlock_achievement("first_win", "First Blood", "Win your first game.")
                
                # Check for Perfect Season (Example: if wins reaches specific count?)
                # user_team = self.get_team(self.user_team_id)
                # if user_team and user_team.wins + user_team.losses == 0: pass # Start of season
            # -------------------------
            
            results.append(result)
            
        # Update Playoff Series Status (If applicable)
        if self.playoff_series:
            self._update_playoff_progress(results)

        # AI Mid-Season Moves (Daily)
        self._ai_process_midseason_free_agency()
            
        self.advance_day()
        
        # Aggressive Auto-Save (Mobile Requirement)
        self.save_game(1)
        
        return results

    def advance_day(self):
        self.current_day += 1
        
        # Check for Regular Season End
        if self.current_day > self.total_regular_season_days:
            if not self.playoff_series:
                # Regular Season just ended. Start Playoffs.
                self._start_playoffs()
            else:
                 # Playoffs are ongoing. Schedule next games if needed.
                 self._schedule_next_playoff_games()

    def _start_playoffs(self):
        print("DEBUG: Starting Playoffs!")
        # 1. Rank Teams
        standings = sorted([t for t in self.teams if t.id != "T00"], 
                           key=lambda x: (x.wins, x.wins/(x.losses+x.wins) if x.losses+x.wins > 0 else 0), 
                           reverse=True)
                           
        # Top 4 make playoffs
        if len(standings) < 4:
            print("ERROR: Not enough teams for playoffs!")
            return
            
        seeds = standings[:4]
        self.playoff_series = []
        
        # 1 vs 4
        s1 = {
            "id": "S1", "round": 1, 
            "t1": seeds[0], "t2": seeds[3], 
            "w1": 0, "w2": 0, "winner": None
        }
        # 2 vs 3
        s2 = {
            "id": "S2", "round": 1, 
            "t1": seeds[1], "t2": seeds[2], 
            "w1": 0, "w2": 0, "winner": None
        }
        self.playoff_series.append(s1)
        self.playoff_series.append(s2)
        
        print(f"DEBUG: Playoff Semi-Finals Set: {seeds[0].name} vs {seeds[3].name}, {seeds[1].name} vs {seeds[2].name}")
        self._schedule_next_playoff_games()

    def _schedule_next_playoff_games(self):
        """Schedules the next daily game for each active series."""
        if not self.playoff_series: return
        
        games_added = 0
        for s in self.playoff_series:
            if s["winner"]: continue # Series finished
            
            # Check if a game for this series is already scheduled for tomorrow (current_day)?
            # Actually current_day has already advanced.
            # We schedule for 'current_day'.
            
            # Generate Game ID: P_{SeriesID}_G{GameNum}
            game_num = s["w1"] + s["w2"] + 1
            game_id = f"P_{s['id']}_G{game_num}"
            
            # Check if already exists (prevent duplicates if called multiple times)
            if any(g.id == game_id for g in self.schedule):
                continue
                
            g = Game(
                 id=game_id,
                 day=self.current_day,
                 home_team=s["t1"] if game_num % 2 != 0 else s["t2"], # Alternate Home/Away? Or 2-2-1-1-1? Let's do simple cleaning.
                 away_team=s["t2"] if game_num % 2 != 0 else s["t1"]
            )
            # Simple alternating home field for now
            self.schedule.append(g)
            games_added += 1
        
        if games_added > 0:
            print(f"DEBUG: Scheduled {games_added} Playoff Games for Day {self.current_day}")

    def _update_playoff_progress(self, results):
        """Updates series scores based on game results."""
        if not self.playoff_series: return
        
        series_updated = set()
        
        for res in results:
            # We assume results don't carry Game ID, but we can verify team names
            # Or better, iterate Today's Games that were played?
            # Matching by team names in series
            
            winner_name = res["winner"] # Name
            
            for s in self.playoff_series:
                if s.get("winner"): continue
                
                # Check if this result belongs to this series
                if (s["t1"].name in [res["home_team"], res["away_team"]] and 
                    s["t2"].name in [res["home_team"], res["away_team"]]):
                    
                    if winner_name == s["t1"].name:
                        s["w1"] += 1
                    else:
                        s["w2"] += 1
                    
                    print(f"DEBUG: Series {s['id']} Update: {s['t1'].name} {s['w1']} - {s['w2']} {s['t2'].name}")
                    series_updated.add(s["id"])
                    
                    # Check Victory (Best of 7 = 4 Wins)
                    if s["w1"] == 4:
                        s["winner"] = s["t1"]
                        print(f"DEBUG: {s['t1'].name} Wins Series {s['id']}!")
                    elif s["w2"] == 4:
                        s["winner"] = s["t2"]
                        print(f"DEBUG: {s['t2'].name} Wins Series {s['id']}!")
                        
                    # Trigger Next Round Logic if Series Ends
                    if s["winner"]:
                        self._check_round_completion()
                    break

    def _check_round_completion(self):
        """Checks if all series in the current round are finished, then starts next round."""
        active_round = max(s["round"] for s in self.playoff_series)
        current_round_series = [s for s in self.playoff_series if s["round"] == active_round]
        
        if all(s["winner"] for s in current_round_series):
            # Round Complete!
            print(f"DEBUG: Round {active_round} Complete!")
            
            if active_round == 1:
                # Semi-Finals Done -> Start Finals
                # Find the two winners
                winners = [s["winner"] for s in current_round_series]
                if len(winners) != 2:
                    print("ERROR: Weird number of winners for Finals.")
                    return
                    
                finals = {
                    "id": "F1", "round": 2,
                    "t1": winners[0], "t2": winners[1],
                    "w1": 0, "w2": 0, "winner": None
                }
                self.playoff_series.append(finals)
                print(f"DEBUG: Finals Set: {winners[0].name} vs {winners[1].name}")
                # Do NOT schedule here. advance_day will do it for the NEXT day.
                
            elif active_round == 2:
                # Finals Done -> Champion!
                finals_series = current_round_series[0] # Should be only 1
                champion = finals_series["winner"]
                print(f"DEBUG: SEASON CHAMPION: {champion.name}")
                
                # TRIGGER AWARDS
                self._calculate_and_store_awards(champion)

    def _ai_process_midseason_free_agency(self):
        """
        AI Teams occasionally check Free Agency during the season to fill roster spots.
        Triggered daily with a small probability.
        """
        ai_teams = [t for t in self.teams if t.id != "T00" and t.id != self.user_team_id]
        fa_team = self.get_team("T00")
        if not fa_team or not fa_team.roster: return

        # Sort FAs by OVR once
        available_fas = sorted(fa_team.roster, key=lambda p: p.ovr, reverse=True)
        
        for team in ai_teams:
            # 1. Check Roster Limit & Chance
            # AI usually only fills to 13. But for Stars (OVR>=80), will go to 15.
            limit = 13
            chance = 0.08
            
            # Star Hunting: If top FA is a Star, boost chance and limit
            best_fa = available_fas[0] if available_fas else None
            is_star_hunt = (best_fa and best_fa.ovr >= 80)
            
            if is_star_hunt:
                limit = 15
                chance = 0.80 # High aggression for stars
            
            if len(team.roster) >= limit: continue
            if random.random() > chance: continue
            
            # 3. Check Cap Space
            payroll = sum(p.salary for p in team.roster)
            cap_space = self.salary_cap - payroll
            
            if cap_space < 1.0: continue # Need at least 1M
            
            # 4. Find Target (Best Available that fits cap)
            target = None
            for fa in available_fas:
                # Star Priority: If searching for star, only take star
                if is_star_hunt and fa.ovr < 80: break 
                
                fmv = self.calculate_market_value(fa)
                if fmv <= cap_space:
                    target = fa
                    break # Take the best one that fits
            
            if target:
                # 5. Execute Signing
                fmv = self.calculate_market_value(target) # Recalc? (already done)
                target.salary = fmv
                target.contract_length = 1 
                if target.ovr >= 80: target.contract_length = random.randint(2, 4) # Lock stars
                
                success, msg = self.sign_player(target, team)
                if success:
                    tag = " (STAR STEAL!)" if target.ovr >= 80 else ""
                    print(f"DEBUG: AI {team.name} signed {target.mask_name} (OVR {target.ovr}) for ${fmv:.2f}M{tag}")

    def _ai_process_renewals(self):
        """AI attempts to renew key players before they hit Free Agency."""
        print("DEBUG: AI Processing Contract Renewals...")
        ai_teams = [t for t in self.teams if t.id != "T00" and t.id != self.user_team_id]
        
        for team in ai_teams:
            # Find expiring contracts (1 year left)
            expiring = [p for p in team.roster if p.contract_length <= 1]
            if not expiring: continue
            
            payroll = sum(p.salary for p in team.roster)
            cap_space = self.salary_cap - payroll
            
            # Sort by Value (OVR + Potential)
            expiring.sort(key=lambda p: p.ovr * 3 + p.potential * 2, reverse=True)
            
            for p in expiring:
                # Core Player Threshold
                is_core = p.ovr >= 80 or (p.ovr >= 75 and p.potential >= 80)
                
                if is_core:
                    fmv = self.calculate_market_value(p)
                    salary_diff = fmv - p.salary
                    
                    # SAFETY CHECK: Roster Reserve (Min 10 players)
                    roster_count = len(team.roster)
                    empty_slots = max(0, 10 - roster_count)
                    reserve_buffer = empty_slots * 1.0 
                    
                    if cap_space - reserve_buffer >= salary_diff:
                        # Renew!
                        import random
                        length = random.randint(3, 5)
                        
                        p.salary = fmv
                        p.contract_length = length 
                        p.years_on_team += length
                        
                        print(f"DEBUG: AI {team.name} RENEWED {p.mask_name} (OVR {p.ovr}) for ${fmv:.1f}M / {length} Yrs")
                        cap_space -= salary_diff
                    else:
                        print(f"DEBUG: AI {team.name} CANNOT AFFORD to renew {p.mask_name}")

    def _ai_process_free_agency(self):
        """AI signs players from Free Agency to fill roster holes."""
        # print("DEBUG: AI Processing Free Agency...") # Reduce spam
        ai_teams = [t for t in self.teams if t.id != "T00" and t.id != self.user_team_id]
        fa_team = self.get_team("T00")
        if not fa_team or not fa_team.roster: return

        # Sort Free Agents by OVR
        free_agents = sorted(fa_team.roster, key=lambda p: p.ovr, reverse=True)
        
        for team in ai_teams:
            roster_size = len(team.roster)
            payroll = sum(p.salary for p in team.roster)
            cap_space = self.salary_cap - payroll
            
            # Target Roster Size: 13
            needs = 13 - roster_size
            if needs <= 0: continue
            
            # Analyze Positional Needs
            pos_counts = {"G": 0, "F": 0, "C": 0}
            for p in team.roster:
                if "G" in p.pos or "後衛" in p.pos: pos_counts["G"] += 1
                elif "F" in p.pos or "前鋒" in p.pos: pos_counts["F"] += 1
                elif "C" in p.pos or "中鋒" in p.pos: pos_counts["C"] += 1
            
            target_pos = []
            if pos_counts["C"] < 2: target_pos.extend(["C", "中鋒"])
            if pos_counts["G"] < 4: target_pos.extend(["PG", "SG", "G", "控球後衛", "得分後衛", "後衛"])
            if pos_counts["F"] < 4: target_pos.extend(["SF", "PF", "F", "小前鋒", "大前鋒", "前鋒"])
            
            signed_count = 0
            
            for fa in free_agents:
                if fa.team_id != "T00": continue 
                if signed_count >= 2: break # Limit 2 signings per day to spread talent
                
                # Logic: Is this a Star? (OVR >= 80)
                is_star = fa.ovr >= 80
                
                # Logic: Is this a Fit?
                is_fit = False
                if target_pos and fa.pos in target_pos:
                    is_fit = True
                
                # Decision Tree:
                # 1. Star Player -> Sign immediately if affordable (Ignore fit)
                # 2. Fit Player -> Sign if affordable
                # 3. Best Available -> Only if panic mode (Roster < 10)
                
                should_sign = False
                if is_star: should_sign = True
                elif is_fit: should_sign = True
                elif len(team.roster) < 10: should_sign = True # Panic fill
                
                if not should_sign: continue
                    
                # Check Affordability
                ask = self.calculate_market_value(fa)
                if cap_space >= ask:
                     # Contract Negotiation Simulation
                     fa.salary = ask
                     fa.contract_length = random.randint(1, 2) 
                     if is_star: 
                         fa.contract_length = random.randint(3, 5) # Lock stars down longer

                     if self.sign_player(fa, team):
                         cap_space -= ask
                         signed_count += 1
                         
                         # Log
                         tag = " (STAR!)" if is_star else ""
                         # print(f"DEBUG: AI {team.name} SIGNED {fa.mask_name} (OVR {fa.ovr}) for ${ask:.1f}M{tag}")
                         
                         # News Feed for Major Signings
                         if is_star or fa.ovr >= 78:
                             self.news_feed.append(f"BREAKING: {team.name} has signed free agent {fa.mask_name} (OVR {fa.ovr})!")
                             
                         # Update counts for loop validity
                         if "G" in fa.pos: pos_counts["G"] += 1
                         elif "C" in fa.pos: pos_counts["C"] += 1
                         else: pos_counts["F"] += 1
            

