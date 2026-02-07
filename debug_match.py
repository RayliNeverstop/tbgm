from controllers.game_manager import GameManager
from models.match_engine import MatchEngine
from models.team import Team
from models.player import Player, PlayerAttributes

def debug_game():
    print("--- Debugging Match Logic ---")
    
    # Setup Mock Teams
    t1 = Team("T1", "Team Won", "#000")
    t2 = Team("T2", "Team Lost", "#FFF")
    
    # Mock Players
    for i in range(5):
        t1.roster.append(Player(f"P1_{i}", "P1", "T1", "PG", 100, 20, PlayerAttributes(), ovr=90))
        t2.roster.append(Player(f"P2_{i}", "P2", "T2", "PG", 100, 20, PlayerAttributes(), ovr=60))

    # Scenario 1: Home Wins (T1 Home, T2 Away) - Expected: T1 Win, T2 Loss
    print("\nScenario 1: Home (Strong) vs Away (Weak)")
    res = MatchEngine.simulate_game(t1, t2)
    print(f"Result: {res['winner']} def {res['loser']} ({res['home_score']}-{res['away_score']})")
    print(f"T1 Record: {t1.wins}-{t1.losses}")
    print(f"T2 Record: {t2.wins}-{t2.losses}")
    
    if t1.wins == 1 and t2.losses == 1:
        print("PASS: Home Win Logic Correct")
    else:
        print("FAIL: Record update wrong")

    # Scenario 2: Away Wins (T2 Home, T1 Away) - Expected: T1 Win, T2 Loss
    # Reset records
    t1.wins = 0; t1.losses = 0
    t2.wins = 0; t2.losses = 0
    
    print("\nScenario 2: Home (Weak) vs Away (Strong)")
    res = MatchEngine.simulate_game(t2, t1)
    print(f"Result: {res['winner']} def {res['loser']} ({res['home_score']}-{res['away_score']})")
    print(f"T2 (Home) Record: {t2.wins}-{t2.losses}")
    print(f"T1 (Away) Record: {t1.wins}-{t1.losses}")
    
    # T1 (Away) should win
    if t1.wins == 1 and t2.losses == 1:
        print("PASS: Away Win Logic Correct")
    else:
        print("FAIL: Record update wrong")

if __name__ == "__main__":
    debug_game()
