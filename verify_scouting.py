from controllers.game_manager import GameManager
from models.player import Player

def verify_scouting():
    print("--- Verifying Scouting & Draft ---")
    gm = GameManager()
    # Initialize properly to ensure attributes exist
    gm.initialize("data/gamedata.json")
    
    # Force reset logic for test isolation
    gm.teams = []
    gm.players = []
    gm._generate_dummy_teams()
    gm.season_year = 2024
    
    # 1. Test Draft Class Generation
    print("Generating Rookies...")
    gm._generate_rookies()
    
    if not gm.draft_class:
        print("FAIL: Draft class is empty.")
        return
        
    print(f"PASS: Generated {len(gm.draft_class)} rookies.")
    
    rookie = gm.draft_class[0]
    print(f"Rookie: {rookie.mask_name}, OVR: {rookie.ovr}, Scouted: {rookie.is_scouted}")
    
    if rookie.is_scouted:
        print("FAIL: Rookie starts as scouted?")
        return
        
    # 2. Test Scouting
    print("Testing Scouting Action (Points: 50)...")
    success, msg = gm.scout_player(rookie.id)
    print(f"Scout Result: {success}, {msg}")
    
    if not success:
        print("FAIL: Scouting failed.")
        return
        
    if not rookie.is_scouted:
        print("FAIL: is_scouted flag not set.")
        return
        
    if gm.scouting_points != 40:
        print(f"FAIL: Logic error in points deduction. Points: {gm.scouting_points}")
        return
        
    print("PASS: Scouting logic works.")
    
    # 3. Test Draft Completion
    print("Testing Draft Completion...")
    # Add dummy scouting points logic? No need.
    
    gm.complete_draft()
    
    if gm.draft_class:
        print("FAIL: Draft class not cleared.")
        return
        
    if not gm.schedule:
        print("FAIL: Schedule not generated after draft.")
        return
        
    # Check if rookie is in global players
    if rookie not in gm.players:
        print("FAIL: Drafted rookie not in global player list.")
        return
        
    print(f"PASS: Draft completed. Rookie Team: {rookie.team_id}")
    
    print("--- Verification Complete ---")

if __name__ == "__main__":
    verify_scouting()
