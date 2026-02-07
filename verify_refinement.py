from controllers.game_manager import GameManager
from models.match_engine import MatchEngine
import os

def verify():
    print("--- Verifying Refinements ---")
    
    # 1. Initialize GM (Loads Data)
    gm = GameManager()
    # Mock data path relative to script if needed, but GM uses hardcoded relative path inside usually
    # adjusting path logic if needed
    gm.initialize("data/gamedata.json")
    
    # 2. Check Salary Normalization
    print(f"\n[Salary Check]")
    high_salary_found = False
    for p in gm.players:
        if p.salary > 1000: # Assuming 50M cap for safety check, 1000 is way too high for normalized
            print(f"WARNING: High salary found: {p.real_name} - ${p.salary}")
            high_salary_found = True
            
    if not high_salary_found:
        print("PASS: All salaries appear normalized (<= 1000M/default).")
        
    # 3. Check Match Engine Balance
    print(f"\n[Match Engine Check]")
    team1 = gm.teams[0]
    team2 = gm.teams[1]
    
    result = MatchEngine.simulate_game(team1, team2)
    s1 = result['home_score']
    s2 = result['away_score']
    print(f"Simulated Score: {s1} - {s2}")
    
    if 60 <= s1 <= 150 and 60 <= s2 <= 150:
         print("PASS: Score is within realistic range.")
    else:
         print("WARNING: Score might be outlier.")

    # 4. Check Stats
    print(f"\n[Stats Check]")
    p1 = team1.roster[0]
    print(f"Player: {p1.mask_name}")
    print(f"Stats: {p1.stats}")
    
    if p1.stats['games'] > 0 and (p1.stats['pts'] > 0 or p1.stats['reb'] > 0 or p1.stats['ast'] > 0):
        print("PASS: Stats updated.")
    else:
        # It's possible to score 0, but games should be 1
        if p1.stats['games'] == 1:
             print("PASS: Games count updated (Player verified to have played).")
        else:
             print("FAIL: Stats not updated.")

if __name__ == "__main__":
    verify()
