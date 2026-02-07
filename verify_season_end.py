from controllers.game_manager import GameManager
from models.player import Player

def verify_season_end():
    print("--- Verifying Season End Logic ---")
    gm = GameManager()
    gm.initialize("data/gamedata.json")
    
    # 1. Force Finals State
    gm.current_day = 12
    print(f"Current Day set to: {gm.current_day}")
    
    # Generate Finals if not exists (usually happens in advance_day(11->12))
    # We can manually trigger it or mock schedule
    # Let's ensure schedule has a Day 12 game
    gm._generate_playoffs_finals()
    print(f"Schedule Day 12 games: {len([g for g in gm.schedule if g.day == 12])}")
    
    # 2. Simulate Finals (Advance Day 12 -> 13)
    gm.advance_day()
    print(f"Day after Finals: {gm.current_day}")
    
    if gm.current_day == 13:
        print("PASS: Day advanced to 13 (Season Finished State).")
    else:
        print("FAIL: Day did not advance correctly.")
        
    # 3. Test New Season Start
    current_year = gm.season_year
    print(f"Current Year: {current_year}")
    
    # Mock some stats
    gm.players[0].stats['pts'] = 100
    
    print("Starting New Season...")
    gm.start_new_season()
    
    # 4. Checks
    print(f"New Year: {gm.season_year}")
    if gm.season_year == current_year + 1:
         print("PASS: Season Year incremented.")
    else:
         print("FAIL: Year not incremented.")
         
    if gm.players[0].stats['pts'] == 0:
         print("PASS: Stats reset.")
    else:
         print("FAIL: Stats not reset.")
         
    if gm.current_day == 1:
         print("PASS: Day reset to 1.")
    else:
         print("FAIL: Day not reset.")
         
    # Check Rookies
    fa_team = gm.get_team("T00")
    rookies = [p for p in fa_team.roster if p.id.startswith(f"R{gm.season_year}")]
    print(f"Generated Rookies: {len(rookies)}")
    
    if len(rookies) >= 5:
        print("PASS: Rookies generated.")
    else:
        print("FAIL: Rookies not found.")

if __name__ == "__main__":
    verify_season_end()
