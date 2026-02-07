from typing import List, Tuple, Optional
from models.player import Player
from models.team import Team
from .game_manager import GameManager

class TradeManager:
    def __init__(self):
        self.gm = GameManager()

    def calculate_loyalty(self, player: Player) -> int:
        """
        Calculates a Loyalty Score (0-200+) based on Performance vs Expectation and Tenure.
        Formula:
        1. Expected Efficiency per game = (OVR - 50) roughly.
        2. Actual Efficiency per game.
        3. Ratio = Actual / Expected. High Ratio (>1.2) = Happy/Loyal. Low (<0.8) = Unhappy.
        4. Tenure Bonus: Heavy weight per year.
        """
        # 1. Expected Efficiency
        # OVR 90 -> Exp 40. OVR 70 -> Exp 20. OVR 50 -> Exp 0.
        expected = max(5.0, float(player.ovr - 50))
        
        # 2. Actual Efficiency
        s = player.stats
        games = s.get("games", 0)
        
        # Fallback to last season if current season is young/empty (Offseason)
        if games < 5 and getattr(player, "history", []):
             last_season = player.history[-1]
             if last_season.get("games", 0) > 10: # Reasonable sample
                 s = last_season
                 games = s.get("games", 0)
        
        if games < 5:
            # Not enough sample size (Rookie or early season)
            # Assume Neutral Happiness (Base 50)
            perf_happiness = 50.0
        else:
            # Formula: Pts + Ast*1.5 + Reb*1.2 + Stl*2 + Blk*2 - TO*1.5
            total_eff = s.get("pts", 0) + \
                        (s.get("ast", 0) * 1.5) + \
                        (s.get("reb", 0) * 1.2) + \
                        (s.get("stl", 0) * 2.0) + \
                        (s.get("block", 0) * 2.0) - \
                        (s.get("to", 0) * 1.5)
            avg_eff = total_eff / games
            
            ratio = avg_eff / expected
            
            # Map Ratio to 0-100 Score
            # Ratio 1.2+ -> 100
            # Ratio 0.8- -> 0
            # 0.8 to 1.2 -> Linear
            if ratio >= 1.2:
                perf_happiness = 100.0
            elif ratio <= 0.6: # Relaxed floor
                perf_happiness = 0.0
            else:
                perf_happiness = ((ratio - 0.6) / 0.6) * 100.0
                
        # 3. Tenure Bonus (Heavy limit)
        # User: "Heavy weight on tenure".
        # 15 pts per year? Max 100?
        tenure_bonus = player.years_on_team * 15
        
        total_loyalty = int(perf_happiness + tenure_bonus)
        return total_loyalty

    def _calculate_pick_value(self, pick) -> int:
        """
        Calculates the value of a draft pick based on the original owner's strength.
        """
        owner_id = pick.get("original_owner_id")
        team = self.gm.get_team(owner_id)
        
        # Team Strength (Inverse Relationship)
        # Weak Team (70 OVR) -> High Pick Value
        # Strong Team (90 OVR) -> Low Pick Value
        
        team_strength = team.average_ovr if team else 75
        
        # 1. Base Value Calculation (Non-Linear)
        # 70 OVR -> Gap 30 -> 30^1.7 ~= 320 (High Lottery)
        # 80 OVR -> Gap 20 -> 20^1.7 ~= 160 (Mid 1st)
        # 90 OVR -> Gap 10 -> 10^1.7 ~= 50  (Late 1st)
        gap = max(100 - team_strength, 5)
        base_val = (gap ** 1.7) * 0.8
        
        # 2. Round Modifier
        if pick["round"] == 2:
            base_val *= 0.15 # 2nd Rounders are significantly less valuable
        
        # 3. Time Discount (Future Uncertainty)
        try:
            current_year = int(self.gm.season_year)
            diff = pick["year"] - current_year
            if diff == 2: base_val *= 0.85
            elif diff >= 3: base_val *= 0.70
        except:
            pass
            
        return int(max(1, base_val))

    def calculate_asset_value(self, asset) -> int:
        """
        Calculates trade value for Player OR Pick.
        """
        if isinstance(asset, dict):
            return self._calculate_pick_value(asset)
            
        # Player Logic
        player = asset
        # --- Standard Value Calculation ---
        # Base: 50 OVR = 0.
        # 75 OVR -> 25^1.6 ~= 172
        # 80 OVR -> 30^1.6 ~= 230
        # 90 OVR -> 40^1.6 ~= 365
        # 95 OVR -> 45^1.6 ~= 441
        # Two 75s (344) < One 90 (365). This solves the 2-for-1 generic issue.
        if player.ovr < 50:
            base_val = 1
        else:
             base_val = pow(player.ovr - 50, 1.6) * 1.2
        
        # Potential Bonus (Reduced for Fairness)
        pot_bonus = 0
        if player.age < 26:
            diff = max(0, player.potential - player.ovr)
            pot_bonus = diff * 1.5 # 10 Pot gap = 15 pts
        
        # Age Penalty
        age_penalty = 0
        if player.age > 33: # Tuned to 33
            age_penalty = (player.age - 33) * 15 # Heavier dropoff
            
        raw_value = base_val + pot_bonus - age_penalty
        raw_value = max(1, raw_value)
        
        # --- Loyalty Modifier ---
        loyalty = self.calculate_loyalty(player)
        
        # Multipliers
        # Loyalty > 100: 1.5x (Core/Untouchable)
        # Loyalty > 80: 1.2x (Reluctant)
        # Loyalty 40-80: 1.0x (Neutral)
        # Loyalty < 40: 0.8x (Unhappy/Trade Bait)
        
        mult = 1.0
        if loyalty >= 100:
            mult = 1.5
        elif loyalty >= 80:
            mult = 1.2
        elif loyalty < 40:
            mult = 0.8
            
        final_value = int(raw_value * mult)
        return final_value

    def validate_trade(self, team_a: Team, assets_a: List[Player], team_b: Team, assets_b: List[Player]) -> Tuple[bool, str]:
        """
        Validates if a trade is legal based on Salary Cap and Roster Rules.
        """
        # 1. Salary Matching
        # 1. Salary Matching
        salary_a = sum(p.salary for p in assets_a if isinstance(p, Player))
        salary_b = sum(p.salary for p in assets_b if isinstance(p, Player))
        
        diff_pct = 0.25
        
        # Check Team A Constraints
        team_a_new_salary = team_a.salary_total - salary_a + salary_b
        if team_a_new_salary > self.gm.salary_cap:
            if salary_b > salary_a * (1 + diff_pct) + 1: # +1 buffer
                return False, f"{team_a.name} Over Cap."

        # Check Team B Constraints
        team_b_new_salary = team_b.salary_total - salary_b + salary_a
        if team_b_new_salary > self.gm.salary_cap:
             if salary_a > salary_b * (1 + diff_pct) + 1:
                return False, f"{team_b.name} Over Cap."

        return True, "Valid."

    def evaluate_fairness(self, team_a_assets: List[Player], team_b_assets: List[Player], team_b_roster: List[Player] = None) -> Tuple[bool, str]:
        """
        Checks if the AI (Team B) accepts the value exchange.
        team_a = User (Offering)
        team_b = AI (Receiving)
        """
        # 1. Calculate Base Values
        val_offer = sum(self.calculate_asset_value(a) for a in team_a_assets)
        val_ask = sum(self.calculate_asset_value(a) for a in team_b_assets)
        
        # 2. Star Quality Check (The "Penny for a Dollar" Rule)
        # 2. Star Quality Check (The "Penny for a Dollar" Rule)
        # If AI is giving up the best player in the deal, the User must provide a player of comparable tier.
        # Only applies if players are involved.
        players_offer = [a for a in team_a_assets if isinstance(a, Player)]
        players_ask = [a for a in team_b_assets if isinstance(a, Player)]

        if players_ask and players_offer:
            best_offer = max(players_offer, key=lambda p: p.ovr)
            best_ask = max(players_ask, key=lambda p: p.ovr)
            
            ovr_diff = best_ask.ovr - best_offer.ovr
            
            # If User is downgrading significantly (e.g. trading for a 90 with a 78)
            # Penalty: The total offer value is discounted.
            if ovr_diff > 4: # Tier Gap
                 penalty_factor = 1.0
                 if ovr_diff <= 7: penalty_factor = 0.9  # Mild downgrade (e.g. 85 for 90)
                 elif ovr_diff <= 10: penalty_factor = 0.7 # Major downgrade (e.g. 80 for 90)
                 else: penalty_factor = 0.5 # Scrub for Star (e.g. 75 for 90) -> Massive penalty
                 
                 val_offer = val_offer * penalty_factor
                 # print(f"DEBUG: Quality Penalty applied. Diff: {ovr_diff}, Factor: {penalty_factor}")

        # 3. Threshold: AI wants to win the trade value-wise
        # Start at 1.0 (Fair).
        threshold = 1.0 
        
        if val_offer >= val_ask * threshold:
            return True, "AI accepts."
        else:
            return False, "AI refuses (Value too low or Quality mismatch)."

    def find_potential_trades(self, user_team: Team, user_assets: List[Player]) -> List[dict]:
        """
        Scans for trades.
        """
        potential_trades = []
        if not user_assets:
            return []

        user_value = sum(self.calculate_asset_value(p) for p in user_assets)
        
        for team in self.gm.teams:
            if team.id == user_team.id or team.id == "T00":
                continue
                
            # Combined Trade Candidates
            # 1. Single Asset Deals (Player OR Pick)
            # Limit picks to first 2 to keep search fast
            available_picks = team.draft_picks[:2]
            all_single_assets = team.roster + available_picks
            
            for asset in all_single_assets:
                target_assets = [asset]
                
                valid, _ = self.validate_trade(user_team, user_assets, team, target_assets)
                if not valid: continue
                
                # Check Fairness
                fair, reason = self.evaluate_fairness(user_assets, target_assets, team.roster)
                
                if fair:
                    val_out = self.calculate_asset_value(asset)
                    potential_trades.append({
                        'team': team,
                        'assets': target_assets,
                        'reason': f"AI Val: {val_out} vs Offer: {user_value}"
                    })
            
            # 2-Player Deals (Limit to top pairs to save time)
            if len(team.roster) >= 2:
                import itertools
                # Sort roster by value ascending (Cheaper/Unhappy players first)
                sorted_roster = sorted(team.roster, key=lambda x: self.calculate_asset_value(x))
                # Check pairs of "movable" assets (e.g. bottom half of value list?)
                # Or just check first 30 pairs
                check_cnt = 0
                for p1, p2 in itertools.combinations(sorted_roster, 2):
                    check_cnt += 1
                    if check_cnt > 30: break
                    
                    target_assets = [p1, p2]
                    valid, _ = self.validate_trade(user_team, user_assets, team, target_assets)
                    if not valid: continue
                        
                    fair, _ = self.evaluate_fairness(user_assets, target_assets, team.roster)
                    if fair:
                         val_out = self.calculate_asset_value(p1) + self.calculate_asset_value(p2)
                         potential_trades.append({
                            'team': team,
                            'assets': target_assets,
                            'reason': f"AI Val: {val_out} vs Offer: {user_value}"
                        })

        # Sort by value
        potential_trades.sort(key=lambda x: sum(self.calculate_asset_value(p) for p in x['assets']), reverse=True)
        return potential_trades[:5]

    def execute_trade(self, team_a: Team, assets_a: List[Player], team_b: Team, assets_b: List[Player]):
        """
        Moves the players and resets tenure/loyalty data.
        """
        # Move A -> B
        for asset in assets_a:
            if isinstance(asset, Player):
                if asset in team_a.roster:
                    team_a.roster.remove(asset)
                    team_b.roster.append(asset)
                    asset.team_id = team_b.id
                    asset.years_on_team = 0 # Reset Tenure
            elif isinstance(asset, dict): # Pick
                if asset in team_a.draft_picks:
                    team_a.draft_picks.remove(asset)
                    team_b.draft_picks.append(asset)
        
        # Move B -> A
        for asset in assets_b:
            if isinstance(asset, Player):
                if asset in team_b.roster:
                    team_b.roster.remove(asset)
                    team_a.roster.append(asset)
                    asset.team_id = team_a.id
                    asset.years_on_team = 0 # Reset Tenure
            elif isinstance(asset, dict): # Pick
                if asset in team_b.draft_picks:
                    team_b.draft_picks.remove(asset)
                    team_a.draft_picks.append(asset)

        # Persistence Logic (Save Game)
        from controllers.game_manager import GameManager
        gm = GameManager()
        gm.save_game(1)

    def identify_team_needs(self, team: Team) -> dict:
        """
        Analyzes roster to determine Status (Buyer/Seller) and Positional Needs.
        Returns: {'status': str, 'needs': [str], 'surplus': [str]}
        """
        # 1. Determine Status
        status = "Neutral"
        games_played = len(team.schedule_results) if hasattr(team, 'schedule_results') else 0
        total_games = max(1, games_played)
        wins = sum(1 for r in team.schedule_results if r['win']) if hasattr(team, 'schedule_results') else 0
        win_pct = wins / total_games
        
        if games_played >= 10:
            if win_pct >= 0.55: status = "Buyer"
            elif win_pct <= 0.40: status = "Seller"
            
        # 2. Analyze Needs based on Depth Chart
        roster_by_pos = {'G': [], 'F': [], 'C': []}
        for p in team.roster:
            if p.pos in ['PG', 'SG']: roster_by_pos['G'].append(p)
            elif p.pos in ['SF', 'PF']: roster_by_pos['F'].append(p)
            elif p.pos == 'C': roster_by_pos['C'].append(p)
            
        needs = []
        surplus = []
        
        # Logic: Need if < 2 players at position group. Surplus if > 4 (G/F) or > 3 (C).
        # Actually, simpler:
        # G: Need < 3, Surplus > 5
        # F: Need < 3, Surplus > 5
        # C: Need < 2, Surplus > 3
        
        if len(roster_by_pos['G']) < 3: needs.append('G')
        if len(roster_by_pos['F']) < 3: needs.append('F')
        if len(roster_by_pos['C']) < 2: needs.append('C') # Critical need
        
        if len(roster_by_pos['G']) > 5: surplus.append('G')
        if len(roster_by_pos['F']) > 5: surplus.append('F')
        if len(roster_by_pos['C']) > 3: surplus.append('C')
        
        return {'status': status, 'needs': needs, 'surplus': surplus}

    def attempt_ai_trade(self, day_progress: float) -> Optional[str]:
        """
        Simulates AI-to-AI trade activity using multiple strategies.
        """
        # 1. Trade Chance
        chance = 0.05
        if 0.6 <= day_progress <= 0.85: chance = 0.15
        
        import random
        if random.random() > chance: return None
        
        teams_data = {t.id: self.identify_team_needs(t) for t in self.gm.teams if t.id != self.gm.user_team_id}
        buyers = [self.gm.get_team(tid) for tid, data in teams_data.items() if data['status'] == "Buyer"]
        sellers = [self.gm.get_team(tid) for tid, data in teams_data.items() if data['status'] == "Seller"]
        
        if not buyers or not sellers: return None
        
        # --- Strategy Selection ---
        modes = ['DUMP', 'FILL', 'UPGRADE']
        # Weights: Dump (30%), Fill (40%), Upgrade (30%)
        mode = random.choices(modes, weights=[30, 40, 30])[0]
        
        if mode == 'DUMP':
            # Seller initiates logic (Previous Logic)
            seller = random.choice(sellers)
            trade_bait = None
            candidates = [p for p in seller.roster if (p.age >= 30 and p.ovr > 75) or self.calculate_loyalty(p) < 40]
            if not candidates: candidates = [p for p in seller.roster if getattr(p, 'years_left', 1) == 1]
            if not candidates: return None
            
            trade_bait = random.choice(candidates)
            buyer = random.choice(buyers)
            
            # Buyer offers Pick
            offer_assets = []
            if trade_bait.ovr >= 80:
                 pick = next((p for p in buyer.draft_picks if p['round'] == 1), None)
                 if pick: offer_assets.append(pick)
            if not offer_assets:
                 pick = next((p for p in buyer.draft_picks if p['round'] == 2), None)
                 if pick: offer_assets.append(pick)
            if not offer_assets: return None
            
            # Execute Check
            valid, _ = self.validate_trade(buyer, offer_assets, seller, [trade_bait])
            if valid:
                fair, _ = self.evaluate_fairness(offer_assets, [trade_bait], seller.roster)
                if fair:
                    self.execute_trade(buyer, offer_assets, seller, [trade_bait])
                    asset_name = f"{offer_assets[0]['year']} R{offer_assets[0]['round']}"
                    return f"TRADE: {seller.name} 送出老將 {trade_bait.name} 至 {buyer.name} 換取 {asset_name} (Dump)"

        elif mode == 'FILL':
            # Buyer looks for positional need
            # Filter buyers with needs
            needy_buyers = [b for b in buyers if teams_data[b.id]['needs']]
            if not needy_buyers: return None
            
            buyer = random.choice(needy_buyers)
            needed_pos_group = random.choice(teams_data[buyer.id]['needs']) # 'C', 'G', or 'F'
            
            # Find Seller with surplus in this group
            matching_sellers = [s for s in sellers if needed_pos_group in teams_data[s.id]['surplus']]
            if not matching_sellers: matching_sellers = sellers # Fallback to any seller
            
            seller = random.choice(matching_sellers)
            
            # ID Target: Decent player at that pos
            # If group is 'G', look for PG/SG. 'F' -> SF/PF. 'C' -> C
            valid_pos = ['PG', 'SG'] if needed_pos_group == 'G' else ['SF', 'PF'] if needed_pos_group == 'F' else ['C']
            targets = [p for p in seller.roster if p.pos in valid_pos and p.ovr >= 70]
            if not targets: return None
            
            target = max(targets, key=lambda x: x.ovr) # Best available
            
            # Offer: Pick + Salary Match (Low OVR player)
            offer_assets = []
            # Pick logic
            pick_round = 1 if target.ovr >= 80 else 2
            pick = next((p for p in buyer.draft_picks if p['round'] == pick_round), None)
            if not pick:
                 # Try downgrade pick
                 pick = next((p for p in buyer.draft_picks if p['round'] == 2), None)
            
            if pick: offer_assets.append(pick)
            
            # Salary Filler (Lowest OVR player)
            filler = min(buyer.roster, key=lambda x: x.ovr)
            offer_assets.append(filler)
            
            # Execute Check
            valid, _ = self.validate_trade(buyer, offer_assets, seller, [target])
            if valid:
                fair, _ = self.evaluate_fairness(offer_assets, [target], seller.roster)
                if fair:
                    self.execute_trade(buyer, offer_assets, seller, [target])
                    return f"TRADE: {buyer.name} 補強了 {target.pos} {target.name} (來自 {seller.name})"

        elif mode == 'UPGRADE':
            # Buyer looks to upgrade a starter
            buyer = random.choice(buyers)
            
            # Find weakest starter
            sorted_roster = sorted(buyer.roster, key=lambda x: x.ovr, reverse=True)
            if len(sorted_roster) < 5: return None
            starters = sorted_roster[:5]
            weakest_starter = min(starters, key=lambda x: x.ovr)
            
            # Target Seller with a better player at same pos
            seller = random.choice(sellers)
            upgrades = [p for p in seller.roster if p.pos == weakest_starter.pos and p.ovr > weakest_starter.ovr + 5]
            if not upgrades: return None
            
            target = max(upgrades, key=lambda x: x.ovr) # Get the best
            
            # Package: Weak Starter + 1st Round + Prospect
            offer_assets = [weakest_starter]
            
            r1_pick = next((p for p in buyer.draft_picks if p['round'] == 1), None)
            if r1_pick: offer_assets.append(r1_pick)
            else: return None # Can't upgrade without 1st rounder usually
            
            prospect = next((p for p in buyer.roster if p.age < 24 and p.ovr < 75 and p != weakest_starter), None)
            if prospect: offer_assets.append(prospect)
            
            # Execute Check
            valid, _ = self.validate_trade(buyer, offer_assets, seller, [target])
            if valid:
                fair, _ = self.evaluate_fairness(offer_assets, [target], seller.roster)
                if fair:
                    self.execute_trade(buyer, offer_assets, seller, [target])
                    return f"BLOCKBUSTER: {buyer.name} 打包選秀權，向 {seller.name} 換來了球星 {target.name}!"
                    
        return None
