import sys
import os
sys.path.append(os.getcwd())

from controllers.game_manager import GameManager
from controllers.save_manager import SaveManager
from utils.crypto_utils import CryptoUtils
import shutil

def test_encryption():
    print("--- Testing Encryption ---")
    
    # 1. Setup
    gm = GameManager()
    # Dummy Data
    gm.salary_cap = 999
    gm.user_team_id = "TEST_TEAM"
    gm.initialized = True # Fake init
    
    # Missing attributes that caused error
    gm.current_date = "2025-10-01"
    gm.current_day = 1
    gm.scouting_points = 50
    gm.season_progression_log = []
    gm.is_draft_active = False
    gm.draft_order = []
    gm.current_draft_pick_index = 0
    gm.draft_picks = []
    gm.gm_score = 0
    gm.gm_score_log = []
    gm.hall_of_fame = []
    gm.league_records = {} # Added
    
    # Need dummy lists to avoid attribute errors during save generation if empty
    gm.players = []
    gm.teams = []
    gm.schedule = []
    gm.draft_class = []
    gm.league_history = []
    gm.playoff_series = []
    gm.achievements = {} 
    
    sm = SaveManager(save_dir="tests/test_saves")
    
    # 2. Save
    print("Saving to slot 99...")
    success, msg = sm.save_game(gm, 99)
    if not success:
        print(f"FAILED to save: {msg}")
        return False
        
    # 3. Verify File Exists
    enc_path = "tests/test_saves/save_99.enc"
    if not os.path.exists(enc_path):
        print(f"FAILED: {enc_path} does not exist.")
        return False
        
    print(f"Verified {enc_path} exists.")
    
    # 4. Verify Content is Not JSON (is binary/encrypted)
    with open(enc_path, "rb") as f:
        content = f.read()
        if content.startswith(b"{"):
            print("FAILED: File content looks like plain JSON!")
            return False
        print("Verified file content is not plain JSON.")
        
    # 5. Load Back
    print("Loading back...")
    gm2 = GameManager()
    success, msg = sm.load_game(gm2, 99)
    if not success:
         print(f"FAILED to load: {msg}")
         return False
         
    if gm2.user_team_id == "TEST_TEAM" and gm2.salary_cap == 999:
        print("SUCCESS: Data loaded correctly!")
    else:
        print(f"FAILED: Data mismatch. Got {gm2.user_team_id}, {gm2.salary_cap}")
        return False

    # Cleanup
    shutil.rmtree("tests/test_saves")
    return True

if __name__ == "__main__":
    try:
        if test_encryption():
            print("ALL TESTS PASSED")
            sys.exit(0)
        else:
            print("TESTS FAILED")
            sys.exit(1)
    except Exception as e:
        import traceback
        traceback.print_exc()
        sys.exit(1)
