import os
import sys

# Ensure we can import from current directory
sys.path.append(os.getcwd())

from controllers.data_loader import DataLoader
from models.match_engine import MatchEngine
from models.team import Team
from models.player import Player, PlayerAttributes

def test_masking():
    print("--- Testing Masking Algorithm ---")
    
    test_cases = [
        ("LeBron James", "L. James"),
        ("Jeremy Lin", "J. Lin"),
        ("Nene", "Nene"),  # Short name
        ("Giannis Antetokounmpo", "G. Antetokounmpo"),
        ("Luc Mbah a Moute", "L. Mbah a Moute"), # Depending on split logic
    ]

    for input_name, expected in test_cases:
        result = DataLoader.apply_masking(input_name)
        status = "PASS" if result == expected else f"FAIL (Got {result})"
        print(f"'{input_name}' -> '{result}' : {status}")

def test_simulation():
    print("\n--- Testing Simulation Engine ---")
    
    # Create Dummy Teams
    p1 = Player("p1", "Player A", "T1", "PG", 100, 20, PlayerAttributes(), "", 90)
    p2 = Player("p2", "Player B", "T1", "SG", 100, 20, PlayerAttributes(), "", 85)
    team_strong = Team("T1", "Strong", "#000", roster=[p1, p2]) # Sum OVR = 175 -> Base = 87.5

    p3 = Player("p3", "Player C", "T2", "PG", 100, 20, PlayerAttributes(), "", 60)
    p4 = Player("p4", "Player D", "T2", "SG", 100, 20, PlayerAttributes(), "", 65)
    team_weak = Team("T2", "Weak", "#FFF", roster=[p3, p4]) # Sum OVR = 125 -> Base = 62.5

    # Run 10 games
    strong_wins = 0
    weak_wins = 0
    
    for i in range(10):
        res = MatchEngine.simulate_game(team_strong, team_weak)
        print(f"Game {i+1}: {res['winner']} ({res['home_score']}-{res['away_score']}) MVP: {res['mvp']}")
        if res['winner'] == "Strong":
            strong_wins += 1
        else:
            weak_wins += 1

    print(f"Strong Wins: {strong_wins}, Weak Wins: {weak_wins}")
    if strong_wins > weak_wins:
        print("Simulation Logic looks reasonable (Strong team won more).")
    else:
        print("Simulation Logic result unexpected (Weak team won more/equal). Check variance.")

if __name__ == "__main__":
    test_masking()
    test_simulation()
