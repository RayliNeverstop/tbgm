import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, List
from models.player import Player
from models.team import Team
from models.game import Game

class SaveManager:
    def __init__(self, save_dir: str = None):
        if save_dir:
            self.save_dir = save_dir
        else:
            self.save_dir = self._get_safe_save_dir()
            
        # Ensure directory exists
        if not os.path.exists(self.save_dir):
            try:
                os.makedirs(self.save_dir)
            except OSError as e:
                print(f"WARNING: Could not create access {self.save_dir}: {e}")
                # Fallback to User Home (Guaranteed Writable usually)
                self.save_dir = str(Path.home() / "tbgm_saves")
                os.makedirs(self.save_dir, exist_ok=True)
                print(f"DEBUG: Fallback Save Path: {self.save_dir}")
        
        print(f"DEBUG: SaveManager Final Path: {self.save_dir}")

    def _get_safe_save_dir(self):
        """Determines a platform-safe save directory."""
        # 1. Check for existing 'game_saves' in current directory (Legacy/Desktop)
        cwd = os.getcwd()
        local_saves = os.path.join(cwd, "game_saves")
        
        # If it already exists, use it (User intention)
        if os.path.exists(local_saves):
            return local_saves
            
        # 2. Detect Mobile (Android/iOS)
        # 'ANDROID_ARGUMENT' is standard in P4A
        is_android = "ANDROID_ARGUMENT" in os.environ
        is_ios = os.environ.get("KIVY_BUILD") == "ios" or sys.platform == "ios" 
        
        if is_android or is_ios:
            # On Mobile, we MUST use the app's internal storage
            # Path.home() returns the app's writable data directory
            return str(Path.home() / "tbgm_saves")
            
        # 3. Default Desktop: Use local 'game_saves' for portability
        return local_saves

    def generate_save_data(self, game_manager) -> Dict[str, Any]:
        """Generates the save data dictionary from GameManager state."""
        return {
            "version": "1.0",
            "current_date": game_manager.current_date,
            "current_day": game_manager.current_day,
            "salary_cap": game_manager.salary_cap,
            "user_team_id": game_manager.user_team_id,
            "players": [p.to_dict() for p in game_manager.players],
            "teams": [t.to_dict() for t in game_manager.teams],
            "schedule": [g.to_dict() for g in game_manager.schedule],
            "draft_class": [p.to_dict() for p in game_manager.draft_class],
            "scouting_points": game_manager.scouting_points,
            "progression_log": game_manager.season_progression_log,
            # Serialize Playoff Series (Convert Team objects to IDs)
            "playoff_series": [
                {
                    "id": s.get("id"),
                    "t1_id": s["t1"].id if hasattr(s.get("t1"), "id") else s.get("t1"),
                    "t2_id": s["t2"].id if hasattr(s.get("t2"), "id") else s.get("t2"),
                    "w1": s.get("w1", 0),
                    "w2": s.get("w2", 0),
                    "round": s.get("round", 1),
                    "winner_id": s["winner"].id if s.get("winner") and hasattr(s["winner"], "id") else None
                }
                for s in game_manager.playoff_series
            ],
            "league_history": game_manager.league_history,
            
            # --- Draft State Persistence ---
            "is_draft_active": game_manager.is_draft_active,
            "draft_order": game_manager.draft_order,
            "current_draft_pick_index": game_manager.current_draft_pick_index,
            "draft_picks": game_manager.draft_picks,
            "draft_picks": game_manager.draft_picks,
            # -------------------------------
            
            # --- Gamification ---
            "gm_score": game_manager.gm_score,
            "achievements": game_manager.achievements,
            "gm_score_log": getattr(game_manager, "gm_score_log", []),
            "hall_of_fame": getattr(game_manager, "hall_of_fame", []),
            "news_feed": getattr(game_manager, "news_feed", []),
            "league_records": getattr(game_manager, "league_records", {}),
        }

    def save_game(self, game_manager, slot_id: int):
        """Saves the current state of GameManager to an encrypted file."""
        from utils.crypto_utils import CryptoUtils

        data = self.generate_save_data(game_manager)
        json_str = json.dumps(data, indent=4, ensure_ascii=False)
        
        # Trigger External Callback (e.g. for Client Storage on Mobile)
        if hasattr(game_manager, 'save_callback') and game_manager.save_callback:
            try:
                # We save unencrypted JSON to client storage for now if it expects dict, 
                # OR we could send encrypted string. 
                # Assuming Flet ClientStorage handles strings/dicts. 
                # For safety, let's stick to standard behavior for callback unless specified.
                game_manager.save_callback(data)
            except Exception as cb_e:
                print(f"Callback Error: {cb_e}")

        filename = f"save_{slot_id}.enc" # Changed extension to .enc
        filepath = os.path.join(self.save_dir, filename)
        
        try:
            encrypted_data = CryptoUtils.encrypt(json_str)
            with open(filepath, 'wb') as f: # Write Binary
                f.write(encrypted_data)
            print(f"Game saved to {filepath}")
            return True, "Success"
        except Exception as e:
            print(f"Error saving game: {e}")
            return False, str(e)

    def load_game(self, game_manager, slot_id: int):
        """Loads a game state into GameManager. Supports both .enc (Encrypted) and .json (Legacy)."""
        from utils.crypto_utils import CryptoUtils

        filename_enc = f"save_{slot_id}.enc"
        filepath_enc = os.path.join(self.save_dir, filename_enc)

        filename_json = f"save_{slot_id}.json"
        filepath_json = os.path.join(self.save_dir, filename_json)
        
        data = None
        loaded_path = ""

        try:
            # 1. Try Encrypted Load
            if os.path.exists(filepath_enc):
                with open(filepath_enc, 'rb') as f:
                    encrypted_content = f.read()
                    json_str = CryptoUtils.decrypt(encrypted_content)
                    data = json.loads(json_str)
                loaded_path = filepath_enc
            
            # 2. Fallback to Legacy JSON
            elif os.path.exists(filepath_json):
                print(f"DEBUG: Found legacy save {filepath_json}, migrating to encryption on next save.")
                with open(filepath_json, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                loaded_path = filepath_json
            
            else:
                print(f"Save file not found (Slot {slot_id})")
                return False, "File Not Found"

            # Restore Global State
            game_manager.current_date = data.get("current_date", "2023-10-01")
            game_manager.current_day = data.get("current_day", 1)
            game_manager.salary_cap = data.get("salary_cap", 5000)
            game_manager.user_team_id = data.get("user_team_id", "")
            game_manager.scouting_points = data.get("scouting_points", 50)
            game_manager.season_progression_log = data.get("progression_log", {})
            game_manager.league_history = data.get("league_history", [])
            game_manager.league_history = data.get("league_history", [])
            
            # Restore Playoff Series
            game_manager.playoff_series = []
            for s_data in data.get("playoff_series", []):
                t1 = game_manager.get_team(s_data.get("t1_id"))
                t2 = game_manager.get_team(s_data.get("t2_id"))
                winner = game_manager.get_team(s_data.get("winner_id")) if s_data.get("winner_id") else None
                
                # Only restore if teams found (safety)
                if t1 and t2:
                    series = {
                        "id": s_data.get("id"),
                        "t1": t1,
                        "t2": t2,
                        "w1": s_data.get("w1", 0),
                        "w2": s_data.get("w2", 0),
                        "round": s_data.get("round", 1),
                        "winner": winner
                    }
                    game_manager.playoff_series.append(series)
            
            # Gamification
            game_manager.gm_score = data.get("gm_score", 0)
            game_manager.achievements = data.get("achievements", {})
            game_manager.gm_score_log = data.get("gm_score_log", [])
            game_manager.hall_of_fame = data.get("hall_of_fame", [])
            
            # --- Draft State Recovery ---
            game_manager.is_draft_active = data.get("is_draft_active", False)
            game_manager.draft_order = data.get("draft_order", [])
            game_manager.current_draft_pick_index = data.get("current_draft_pick_index", 0)
            game_manager.draft_picks = data.get("draft_picks", [])
            # ---------------------------
            
            # Restore Draft Class
            game_manager.draft_class = []
            for p_data in data.get("draft_class", []):
                player = Player.from_dict(p_data)
                game_manager.draft_class.append(player)

            # Restore Players
            game_manager.players = []
            for p_data in data.get("players", []):
                player = Player.from_dict(p_data)
                game_manager.players.append(player)

            # Restore Teams
            game_manager.teams = []
            for t_data in data.get("teams", []):
                # We need global players list to link roster
                team = Team.from_dict(t_data, game_manager.players)
                game_manager.teams.append(team)

            # Restore Schedule
            # Need to link Team objects to Game objects
            game_manager.schedule = []
            for g_data in data.get("schedule", []):
                home_id = g_data.get("home_team_id")
                away_id = g_data.get("away_team_id")
                
                home_team = game_manager.get_team(home_id)
                away_team = game_manager.get_team(away_id)
                
                if home_team and away_team:
                    game = Game(
                        id=g_data.get("id"),
                        day=g_data.get("day"),
                        home_team=home_team,
                        away_team=away_team,
                        played=g_data.get("played", False),
                        result=g_data.get("result", {})
                    )
                    game_manager.schedule.append(game)
            
            print(f"Game loaded from {loaded_path}")
            return True, "Success"

        except Exception as e:
            print(f"Error loading game: {e}")
            import traceback
            traceback.print_exc()
            return False, str(e)
