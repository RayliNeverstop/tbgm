from controllers.game_manager import GameManager
from controllers.trade_manager import TradeManager
from models.player import Player, PlayerAttributes
from models.team import Team

def verify_trade():
    print("--- Verifying Trade Logic ---")
    gm = GameManager()
    tm = TradeManager()
    
    # Setup Mock Teams
    t1 = Team("T01", "Team A", "#000")
    t2 = Team("T02", "Team B", "#FFF")
    
    # Register teams in GM so find_potential_trades can see them
    gm.teams = [t1, t2]
    tm.gm.teams = gm.teams # Ensure TM sees them too (same instance check)
    
    # Set GM Cap for test
    gm.salary_cap = 5000
    tm.gm.salary_cap = 5000 # TradeManager has its own GM instance or reference? 
    # TradeManager inits new GM() which is Singleton, so same instance.
    print(f"Salary Cap: {gm.salary_cap}")
    
    # Valid Salary Trade
    # p1 ($100M) <-> p2 ($100M)
    p1 = Player(id="P1", real_name="P1", team_id="T01", pos="PG", salary=100, age=25, attributes=PlayerAttributes(), ovr=90, potential=90)
    p2 = Player(id="P2", real_name="P2", team_id="T02", pos="PG", salary=100, age=25, attributes=PlayerAttributes(), ovr=90, potential=90)
    
    t1.roster.append(p1)
    t2.roster.append(p2)
    
    print("\nTest 1: Even Trade")
    valid, msg = tm.validate_trade(t1, [p1], t2, [p2])
    print(f"Validation: {valid} - {msg}")
    
    fair, reason = tm.evaluate_fairness([p1], [p2])
    print(f"Fairness: {fair} - {reason}")
    
    if valid and fair:
        tm.execute_trade(t1, [p1], t2, [p2])
        if p1 in t2.roster and p2 in t1.roster:
            print("PASS: Execution successful.")
        else:
            print("FAIL: Execution failed.")
    else:
        print("FAIL: Even trade rejected.")

    # Invalid Salary Trade
    # p1 ($200M) -> p2 ($10M)
    # T2 absorbs $190M. If T2 close to cap, fail.
    p3 = Player(id="P3", real_name="P3", team_id="T01", pos="PG", salary=200, age=25, attributes=PlayerAttributes(), ovr=90)
    p4 = Player(id="P4", real_name="P4", team_id="T02", pos="PG", salary=10, age=25, attributes=PlayerAttributes(), ovr=90)
    
    t1.roster.append(p3)
    t2.roster.append(p4)
    # Fill T2 cap to near max (cap=5000. Current=110? Need way more)
    t2.roster.append(p4)
    # Fill T2 cap to near max (cap=5000) using filler player
    # salary_total is a property, so we must add players to increase it.
    
    # Player salary total is dynamic sum of roster.
    # Fill roster with dummy filler
    filler = Player(id="F1", real_name="Fill", team_id="T02", pos="C", salary=4800, age=30, attributes=PlayerAttributes())
    t2.roster.append(filler)
    
    print("\nTest 2: Salary Cap Violation")
    # T2 has 10+100+4800 = 4910. Cap 5000. Space 90.
    # Incoming 200. Outgoing 10. Net +190. New 5100. Fail.
    
    valid, msg = tm.validate_trade(t1, [p3], t2, [p4])
    print(f"Validation: {valid} - {msg}")
    
    if not valid:
        print("PASS: Cap violation caught.")
    else:
        print("FAIL: Cap violation ignored.")

    # Unfair Trade
    # P1 (90 OVR) -> P4 (10 OVR - wait P4 is 90 OVR but cheap. Make P5 bad)
    p5 = Player(id="P5", real_name="Low Value", team_id="T02", pos="PG", salary=10, age=35, attributes=PlayerAttributes(), ovr=50)
    t2.roster.append(p5)
    
    print("\nTest 3: Unfair Value (AI Rejection)")
    # Team A offers P5 (Trash) for P1 (God) - Wait, P1 is now on T2.
    # Team A offers P3 (God) for P5 (Trash) -> AI (T2) should ACCEPT (Robbery)
    # Team A offers P5 (Trash) for P3 (God) -> AI (T1) ?? Use validate function.
    
    # Use explicit args: evaluate_fairness(user_assets, target_assets)
    # User Offer: [p5] (Value ~5). Target: [p3] (Value ~100).
    # AI is the target side. AI is losing P3. AI is gaining P5.
    # val_a (incoming to AI) = 5. val_b (outgoing from AI) = 100.
    
    print(f"Fairness: {fair} - ({reason})")
    
    if not fair:
        print("PASS: Unfair trade rejected.")
    else:
        print("FAIL: Unfair trade accepted.")

    # Trade Finder Test
    print("\nTest 4: Trade Finder")
    # Setup T2 to have a good package for P3 ($200, Val ~100)
    # T2 Needs to offer ~110 Value.
    # User Offer (P3): OVR 90. Value ~100.
    # We need AI Asset (P6) such that 100 >= P6_Val * 1.1 => P6_Val <= 90.
    
    # Create P6 on T2 with moderate value (OVR 85)
    # Val: (85-50)*2.5 = 87.5. 87.5 * 1.1 = 96.25. 100 > 96.25. Deal.
    p6 = Player(id="P6", real_name="Fair Asset", team_id="T02", pos="C", salary=200, age=22, attributes=PlayerAttributes(), ovr=85, potential=88)
    t2.roster.append(p6)
    
    # User (T1) offers P3. AI (T2) should offer P6.
    offers = tm.find_potential_trades(t1, [p3])
    print(f"Offers found: {len(offers)}")
    
    matched = False
    for offer in offers:
        print(f"Offer from {offer['team'].name}: {[p.real_name for p in offer['assets']]} - {offer['reason']}")
        if p6 in offer['assets']:
            matched = True
            
    if matched:
        print("PASS: Trade Finder found the fair deal.")
    else:
        print("FAIL: Trade Finder found nothing or missed the deal.")

if __name__ == "__main__":
    verify_trade()
