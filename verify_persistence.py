from controllers.game_manager import GameManager
import os
import shutil

def verify_persistence():
    print("--- Verifying Persistence (Draft & Scouting) ---")
    
    # 1. Setup Initial State
    gm = GameManager()
    gm.initialize("data/gamedata.json")
    
    # Force clean state
    gm.teams = []
    gm._generate_dummy_teams()
    gm.season_year = 2025
    
    # Generate Draft Class
    gm._generate_rookies()
    gm.scouting_points = 30 # Simulate spent points
    
    # Scout a player to flip boolean
    target_rookie = gm.draft_class[0]
    target_rookie.is_scouted = True
    
    print(f"Generated {len(gm.draft_class)} rookies.")
    print(f"Set Scouting Points to {gm.scouting_points}")
    print(f"Scouted Top Rookie: {target_rookie.mask_name}")
    
    # 2. Save Game
    print("Saving Game to slot 99...")
    gm.save_game(99)
    
    # 3. Clear State (Simulate restart)
    gm.draft_class = []
    gm.scouting_points = 50
    gm.players = []
    print("State cleared.")
    
    # 4. Load Game
    print("Loading Game from slot 99...")
    success = gm.load_game(99)
    if not success:
        print("FAIL: Load failed.")
        return
        
    # 5. Verify Data
    if len(gm.draft_class) == 0:
        print("FAIL: Draft class mismatch (Empty).")
        return
        
    if gm.scouting_points != 30:
        print(f"FAIL: Scouting points mismatch. Got {gm.scouting_points}, expected 30.")
        return
        
    loaded_rookie = gm.draft_class[0]
    if loaded_rookie.mask_name != target_rookie.mask_name:
         print(f"FAIL: Rookie order/name mismatch. Got {loaded_rookie.mask_name}")
         return
         
    if not loaded_rookie.is_scouted:
         print("FAIL: Rookie is_scouted flag not preserved.")
         return
         
    print("PASS: Persistence Verified Successfully!")
    print("--- Verification Complete ---")

if __name__ == "__main__":
    verify_persistence()
