from controllers.game_manager import GameManager
from models.player import Player, PlayerAttributes

def verify_dynasty():
    print("--- Verifying Dynasty Features ---")
    gm = GameManager()
    gm.initialize("data/gamedata.json")
    
    # Setup Mock Player for Progression
    # Young Player (Growth)
    p_young = Player("Y1", "Young Gun", "YG", "T01", "PG", 100, 20, PlayerAttributes(), ovr=70, potential=85)
    gm.players.append(p_young)
    
    # Old Player (Decline)
    p_old = Player("O1", "Old Vet", "OV", "T01", "PG", 100, 36, PlayerAttributes(), ovr=80, potential=80)
    gm.players.append(p_old)
    
    # Contract Player (Expiry)
    p_contract = Player("C1", "Contract Expiring", "CE", "T01", "PG", 100, 25, PlayerAttributes(), ovr=75, contract_length=1)
    gm.players.append(p_contract)
    
    # Ensure team exists for release logic
    team = gm.get_team("T01")
    if not team:
        from models.team import Team
        team = Team("T01", "Test Team", "#000")
        gm.teams.append(team)
    
    # Add to roster for correct release logic
    team.roster.append(p_contract)
    
    print(f"Young Player OVR: {p_young.ovr}, Age: {p_young.age}")
    print(f"Old Player OVR: {p_old.ovr}, Age: {p_old.age}")
    print(f"Contract Player Years: {p_contract.contract_length}")
    
    print("\n--- Simulating Season Reset ---")
    # Manually trigger new season
    gm.start_new_season()
    
    print("\n--- Results ---")
    print(f"Young Player OVR: {p_young.ovr} (Expected Increase/Same), Age: {p_young.age}")
    # Note: Growth is probabilistic, but potential logic should hold
    if p_young.ovr >= 70:
        print("PASS: Young player did not regress.")
        
    print(f"Old Player OVR: {p_old.ovr} (Expected Decrease/Same), Age: {p_old.age}")
    # Note: Decline is probabilistic
    
    print(f"Contract Player Years: {p_contract.contract_length}")
    print(f"Contract Player Team: {p_contract.team_id}")
    
    if p_contract.contract_length == 0:
        print("PASS: Contract expired.")
    else:
        print("FAIL: Contract did not decrement to 0.")
        
    if p_contract.team_id == "T00":
         print("PASS: Player released to FA.")
    else:
         print("FAIL: Player not released. Team is " + p_contract.team_id)

if __name__ == "__main__":
    verify_dynasty()
