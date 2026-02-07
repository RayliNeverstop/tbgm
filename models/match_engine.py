import random
import json
import os
from typing import Tuple, Dict, Any
from .team import Team
from .player import Player

class MatchEngine:
    @staticmethod
    def _load_config() -> Dict[str, Any]:
        """Loads simulation parameters from data/game_config.json. Supports // comments."""
        config_path = "data/game_config.json"
        try:
            if os.path.exists(config_path):
                with open(config_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    # Simple comment stripping: Remove lines starting with // or part of line after //
                    # This is a basic implementation for this specific use case
                    clean_lines = []
                    for line in content.splitlines():
                        if "//" in line:
                            line = line.split("//")[0]
                        clean_lines.append(line)
                    clean_content = "\n".join(clean_lines)
                    return json.loads(clean_content)
        except Exception as e:
            print(f"Error loading config: {e}")
        return {} # Fallback to defaults via .get()

    @staticmethod
    def simulate_game(home_team: Team, away_team: Team) -> Dict[str, Any]:
        """
        Simulates a game between home_team and away_team.
        Returns a dictionary with result details.
        """
        if not home_team.roster or not away_team.roster:
            return {"home_score": 0, "away_score": 0, "winner": "None", "loser": "None"}

        # --- 0. Load Configuration ---
        cfg = MatchEngine._load_config()
        
        # Helper to get config value safely
        def c(section, key, default):
            return cfg.get(section, {}).get(key, default)

        # --- 1. Preparation ---
        # Sort rosters by position for matchups: PG, SG, SF, PF, C
        pos_order = {"PG": 1, "SG": 2, "SF": 3, "PF": 4, "C": 5}
        
        def get_sorted_lineup(team):
            # Sort by Position Order, then OVR descending
            return sorted(team.roster, key=lambda p: (pos_order.get(p.pos, 6), -p.ovr))

        home_lineup = get_sorted_lineup(home_team)
        away_lineup = get_sorted_lineup(away_team)
        
        # Initialize Game Stats
        stats = {}
        for p in home_team.roster + away_team.roster:
            stats[p.id] = {
                "name": p.mask_name, 
                "pts": 0, "reb": 0, "ast": 0, 
                "fgm": 0, "fga": 0,
                "3pm": 0, "3pa": 0,
                "2pm": 0, "2pa": 0,
                "stl": 0, "blk": 0, "to": 0,
                "oreb": 0, "dreb": 0,
                "games": 1 # Track locally
            }

        # Hot Hand Tracking
        streak_map = {p.id: 0 for p in home_team.roster + away_team.roster}

        # Strategy Helpers
        def get_strategy(team):
            return getattr(team, "strategy_settings", {})

        home_strat = get_strategy(home_team)
        away_strat = get_strategy(away_team)
        
        # --- Rotation Logic ---
        def calculate_rotation_plan(team, strategy):
            # 1. Bucket Players & Calculate Adjusted OVR
            roster_buckets = {"Guards": [], "Forwards": [], "Centers": []}
            rotation_settings = strategy.get("rotation_settings", {})
            
            for p in team.roster:
                # Calculate Adjusted OVR
                adj_ovr = p.ovr
                role = rotation_settings.get(p.id, " ")
                
                if role == "++": adj_ovr += 20
                elif role == "+": adj_ovr += 5
                elif role == "-": adj_ovr -= 5
                elif role == "--": adj_ovr -= 50
                
                # Store adjusted ovr on the object temporarily (or just use tuple)
                p_entry = (p, adj_ovr) 
                
                # Normalize Position to Buckets
                pos = p.pos
                if pos in ["PG", "SG", "G", "後衛"]:
                    roster_buckets["Guards"].append(p_entry)
                elif pos in ["SF", "PF", "F", "前鋒"]:
                    roster_buckets["Forwards"].append(p_entry)
                elif pos in ["C", "中鋒"]:
                    roster_buckets["Centers"].append(p_entry)
                else: 
                    # Default fallback
                    roster_buckets["Forwards"].append(p_entry)

            # 2. Sort Buckets by Adjusted OVR
            for k in roster_buckets:
                roster_buckets[k].sort(key=lambda x: x[1], reverse=True)
                
            # 3. Select Starters (2G, 2F, 1C) and Bench (2G, 2F, 1C)
            starters = {} # Map 'PG', 'SG'... to Player
            bench = {}
            
            # Helper to pop or fallback
            def get_best(bucket_name, count):
                selected = []
                bucket = roster_buckets[bucket_name]
                for _ in range(count):
                    if bucket:
                        selected.append(bucket.pop(0)[0])
                return selected

            # Starters
            s_guards = get_best("Guards", 2)
            s_forwards = get_best("Forwards", 2)
            s_centers = get_best("Centers", 1)
            
            # Fill Starter Slots (Best effort mapping)
            starter_list = s_guards + s_forwards + s_centers
            # Safety: If not enough players, fill from any remaining
            while len(starter_list) < 5:
                # Find any remaining player from any bucket
                found = False
                for b in ["Guards", "Forwards", "Centers"]:
                    if roster_buckets[b]:
                        starter_list.append(roster_buckets[b].pop(0)[0])
                        found = True
                        break
                if not found: break # Roster too small (<5)

            # Bench (Next 5) -> Aiming for 10 man rotation
            b_guards = get_best("Guards", 2)
            b_forwards = get_best("Forwards", 2)
            b_centers = get_best("Centers", 1)
            bench_list = b_guards + b_forwards + b_centers
            
            # Safety fill for bench
            while len(bench_list) < 5:
                found = False
                for b in ["Guards", "Forwards", "Centers"]:
                    if roster_buckets[b]:
                        bench_list.append(roster_buckets[b].pop(0)[0])
                        found = True
                        break
                if not found: break 
            
            # If bench is still empty (e.g. only 6 players total), reuse starters
            if not bench_list:
                bench_list = [p for p in starter_list] # Copy starters
            
            # 4. Create 100-tick Plan
            # Starters: 0-35, 76-100 (Total 60 ticks)
            # Bench: 36-75 (Total 40 ticks)
            
            plan = []
            for tick in range(100):
                # Determine active unit
                if 35 <= tick < 75:
                    if len(bench_list) >= 5:
                        plan.append(bench_list[:5])
                    else:
                        # Hybrid if short bench
                        plan.append(bench_list + starter_list[:5-len(bench_list)])
                else:
                    plan.append(starter_list[:5]) # Should be size 5
                    
            return plan

        home_plan = calculate_rotation_plan(home_team, home_strat)
        away_plan = calculate_rotation_plan(away_team, away_strat)

        # --- Phase 32: Coach's Favorite Boost Calculation ---
        boost_map = {} # player_id -> boost_float

        def calc_boost(team, settings):
            if not settings: return
            rot_set = settings.get("rotation_settings", {})
            if not rot_set: return

            # 1. Raw Rank (Sort by OVR desc)
            raw_sorted = sorted(team.roster, key=lambda p: p.ovr, reverse=True)
            raw_rank_map = {p.id: i for i, p in enumerate(raw_sorted)}
            
            # 2. Adj Rank (Sort by Adj OVR)
            def get_mod_val(val):
                if val == "++": return 2
                if val == "+": return 1
                if val == "-": return -1
                if val == "--": return -2
                return 0

            def get_adj_ovr(p):
                val = rot_set.get(p.id, 0)
                mod = get_mod_val(val)
                bonus = 0
                if mod == 2: bonus = 6
                elif mod == 1: bonus = 3
                return p.ovr + bonus

            adj_sorted = sorted(team.roster, key=get_adj_ovr, reverse=True)
            adj_rank_map = {p.id: i for i, p in enumerate(adj_sorted)}
            
            # 3. Calculate Rise & Boost
            for p in team.roster:
                val = rot_set.get(p.id, 0)
                mod = get_mod_val(val)
                
                if mod > 0: # Only boost favorites (++ or +)
                    raw_r = raw_rank_map.get(p.id, 99)
                    adj_r = adj_rank_map.get(p.id, 99)
                    
                    # Case A: Rank Rise (Moving up the ladder)
                    rise = raw_r - adj_r
                    boost = 0.0
                    
                    if rise > 0:
                        boost = min(rise * 0.01, 0.08) # Max 8%
                    
                    # Case B: Already Top Rank (Starters getting love)
                    # If they are in the top 5 after adjustment, they get a significant boost
                    # Phase 35: Increased to 10% max as requested
                    # Rank 0 (1st) -> 10%, Rank 1 (2nd) -> 8% ... Rank 4 (5th) -> 2%
                    if adj_r < 5:
                        top_boost = (5 - adj_r) * 0.02
                        # Take the higher of the two boosts (Rise vs Top Status)
                        boost = max(boost, top_boost)
                    
                    if boost > 0:
                        boost_map[p.id] = boost

        calc_boost(home_team, home_strat)
        calc_boost(away_team, away_strat)
        # --- End Phase 32 ---

        def get_usage_weights(team, lineup):
            weights = []
            settings = get_strategy(team)
            opts = settings.get("scoring_options", [])
            rot = settings.get("rotation_settings", {})
            tactics = settings.get("tactics", "Balanced")
            
            # Config Values
            usage_exp = c("usage", "attribute_exponent", 3.0)
            att_weights = cfg.get("usage", {}).get("attribute_weights", {"2pt": 1.5, "3pt": 1.2, "consistency": 0.5})
            opt_mults = c("usage", "option_multipliers", [3.5, 2.2, 1.5])
            rot_mults = cfg.get("usage", {}).get("rotation_multipliers", {"++": 1.5, "--": 0.3})
            tact_bonus = c("usage", "tactics_bonus", 1.3)

            for p in lineup:
                # Base: Offensive Attributes
                w = (p.attributes.two_pt * att_weights.get("2pt", 1.5)) + \
                    (p.attributes.three_pt * att_weights.get("3pt", 1.2)) + \
                    (p.attributes.consistency * att_weights.get("consistency", 0.5))
                w = w ** usage_exp
                
                # Modifiers
                if p.id in opts:
                    idx = opts.index(p.id)
                    w *= opt_mults[idx] if idx < len(opt_mults) else 1.0
                
                role = rot.get(p.id, " ")
                w *= rot_mults.get(role, 1.0)
                
                if tactics == "Inside" and p.pos in ["C", "PF"]: w *= tact_bonus
                if tactics == "Outside" and p.pos in ["PG", "SG", "SF"]: w *= tact_bonus
                
                # --- Fatigue / High Volume Penalty ---
                # Prevent unrealistic usage (Hero Ball Fix)
                p_stats = stats.get(p.id, {})
                curr_fga = p_stats.get("fga", 0)
                
                # Progressive Penalty
                if curr_fga >= 40: w *= 0.05   # Stop shooting
                elif curr_fga >= 30: w *= 0.20 # Severe reduction
                elif curr_fga >= 22: w *= 0.50 # Moderate reduction (Kobe Zone)
                
                weights.append(w)
            return weights

        # Prepare Bottom 4 Ids (Phase 49)
        def get_bottom_4_ids(team):
             # Sort by OVR ascending (Low to High)
             sorted_r = sorted(team.roster, key=lambda p: p.ovr)
             # Take IDs of first 4 if roster large enough, else all?
             # User said "Bottom 4", implying specific slots.
             return {p.id for p in sorted_r[:4]}

        bottoms_map = get_bottom_4_ids(home_team).union(get_bottom_4_ids(away_team))

        # --- 2. Simulation Loop ---
        # Pace
        pace_min = c("pace", "min", 95)
        pace_max = c("pace", "max", 105)
        possessions = random.randint(pace_min, pace_max)
        if home_strat.get("tactics") == "Pace" or away_strat.get("tactics") == "Pace":
            possessions += c("pace", "tactic_bonus", 8)

        def simulate_possession(off_team, def_team, off_lineup, def_lineup, comeback_bonus=False) -> int:
            # Phase 36: OVR Global Factor Helper
            def get_ovr_factor(p):
                # Baseline 85 (User Request). Each point diff = 0.5% impact.
                # Configurable via game_config.json
                baseline = c("ovr_mechanics", "baseline", 85)
                factor = c("ovr_mechanics", "factor_per_point", 0.005)
                
                return 1.0 + (p.ovr - baseline) * factor

            # 1. Determine Attacker
            weights = get_usage_weights(off_team, off_lineup)
            attacker = random.choices(off_lineup, weights=weights, k=1)[0]
            
            # 2. Determine Defender (Matchup)
            try:
                idx = off_lineup.index(attacker)
                defender = def_lineup[idx] if idx < len(def_lineup) else random.choice(def_lineup)
            except:
                defender = random.choice(def_lineup)
            
            # 3. Event: Turnover Check
            to_chance = c("defense", "base_to_chance", 0.10)
            to_div = c("defense", "to_divisor", 1000)
            steal_div = c("defense", "steal_divisor", 800)
            
            # Apply OVR Factors
            off_f = get_ovr_factor(attacker)
            def_f = get_ovr_factor(defender)
            
            # Attacker ability reduced by factor (or boosted)
            to_chance -= (attacker.attributes.passing * off_f + attacker.attributes.consistency * off_f) / to_div
            # Defender ability boosted by factor
            to_chance += (defender.attributes.steal * def_f + defender.attributes.defense * def_f) / steal_div
            
            if random.random() < to_chance:
                stats[attacker.id]["to"] += 1
                # Credit Steal?
                if random.random() < c("defense", "steal_ratio_of_to", 0.7): 
                    stats[defender.id]["stl"] += 1
                return 0 # End Possession
            
            # 4. Event: Shot Attempt
            stats[attacker.id]["fga"] += 1
            
            # 5. Event: Block Check
            blk_base = c("defense", "base_block_chance", 0.02)
            blk_div = c("defense", "block_divisor", 700) # Reverted slightly from 600
            
            # Positional Multiplier (Phase 33/34 Tuned)
            pos_mult = 1.0
            if defender.pos in ["C", "PF", "中鋒", "大前鋒"]: 
                pos_mult = 1.8 # Tuned down from 3.0 (User reported too many blocks)
            elif "F" in defender.pos: 
                pos_mult = 1.2
            elif "G" in defender.pos: 
                pos_mult = 0.3 
            
            # Use BLOCK attribute if available, else DEFENSE
            blk_stat = getattr(defender.attributes, 'block', defender.attributes.defense)
            blk_stat *= def_f # Phase 36: Apply OVR factor
            
            blk_chance = blk_base + (blk_stat / blk_div) * pos_mult
            
            if attacker.pos in ["PG", "SG"] and defender.pos in ["C", "PF"]:
                blk_chance += c("defense", "big_block_small_bonus", 0.05)
                
            if random.random() < blk_chance:
                stats[defender.id]["blk"] += 1
                return 0 # Missed shot due to block
            
            # 6. Event: Make/Miss
            # Decide Shot Type (Smart Logic)
            is_3pt = False
            
            # Base Tendency from Config
            shot_tendency = c("shooting", "three_pt_freq_pg_sg_sf", 0.4)
            
            # 1. Attribute Modifier (Dynamic Tendency)
            # If 3PT > 80: significantly more likely to shoot 3s
            # If 3PT < 60: significantly less likely
            rat_3pt = attacker.attributes.three_pt
            if rat_3pt >= 85:
                shot_tendency += 0.30 # Super Green Light
            elif rat_3pt >= 75:
                shot_tendency += 0.15
            elif rat_3pt < 60:
                shot_tendency -= 0.20
            elif rat_3pt < 40:
                shot_tendency = 0.0 # Don't shoot
            
            # 2. Position Filtering (Stretch Bigs)
            perimeter_positions = ["PG", "SG", "SF", "G", "F", "後衛", "前鋒"]
            
            if attacker.pos in perimeter_positions:
                pass # Use calculated tendency
            else:
                # C/PF/中鋒... normally don't shoot unless they are good
                if rat_3pt > 75: # Stretch Big
                    shot_tendency = 0.25 # Lower volume than guards but will shoot
                else:
                    shot_tendency = 0.01 # Rare heave
            
            # 3. Strategy / Tactics Influence
            strategy = getattr(off_team, "strategy_settings", {})
            tactics = strategy.get("tactics", "Balanced")
            
            if tactics == "Outside":
                shot_tendency += 0.15 # Push for more 3s
            elif tactics == "Inside":
                shot_tendency -= 0.15 # Focus on paint
            elif tactics == "Pace":
                shot_tendency += 0.05 # Fast pace often implies quick 3s
                    
            if random.random() < shot_tendency: 
                is_3pt = True
            
            # Select Attribute
            # Phase 36: Apply OVR Factor to Shooting Attributes
            shot_raw = attacker.attributes.three_pt if is_3pt else attacker.attributes.two_pt
            def_raw = defender.attributes.defense
            
            # Phase 49: Superstar Defense Reduction (User Req)
            # If Attacker OVR >= 90: Def impact -50%
            # If Attacker OVR 80-89: Def impact -20%
            def_penalty = 1.0
            if attacker.ovr >= 90:
                def_penalty = 0.5
            elif 80 <= attacker.ovr <= 89:
                def_penalty = 0.8
                
            shot_val = shot_raw * off_f
            def_val = def_raw * def_f * def_penalty
            
            # Phase 38: Microwave Mechanic (Offense Status)
            # If streak >= 2, apply bonus based on offense_status
            current_streak = streak_map.get(attacker.id, 0)
            
            mw_req = c("microwave", "streak_req", 2)
            if current_streak >= mw_req:
                # Bonus = (Status / 100) * 5
                # Status 100 -> +5, Status 0 -> +0
                max_bonus = c("microwave", "max_bonus", 5.0)
                mw_bonus = (attacker.offense_status / 100.0) * max_bonus
                shot_val += mw_bonus

            # --- Fatigue Efficiency Penalty ---
            # If taking too many shots, efficiency drops (tired legs)
            p_stats = stats.get(attacker.id, {})
            curr_fga = p_stats.get("fga", 0)
            
            if curr_fga > 25:
                # Penalty: -3 attribute score per shot over 25
                shot_val -= (curr_fga - 25) * 3.0
            
            base_pct = c("shooting", "base_pct", 0.45)
            # +/- based on diff
            attr_impact_div = c("shooting", "attribute_impact_divisor", 350)
            
            # Phase 34: Decoupled Defense Logic
            # If Def > Off, reduce the penalty by factor (e.g. 0.8)
            # If Off > Def, full bonus (maintaining offensive stars' dominance)
            diff = shot_val - def_val
            if diff < 0:
                def_factor = c("defense", "defense_impact_factor", 0.8)
                diff *= def_factor
                
            base_pct += diff / attr_impact_div 
            
            # Variance
            # Phase 37: Consistency Logic
            # Higher consistency raises the 'floor' (v_low), reducing bad rolls
            v_low = c("shooting", "variance_low", 0.85)
            v_high = c("shooting", "variance_high", 1.15)
            
            cons_val = attacker.attributes.consistency
            # Example: 90 Cons -> +0.135 floor -> v_low becomes 0.985
            # Example: 40 Cons -> +0.060 floor -> v_low becomes 0.910
            c_bonus = c("consistency", "floor_bonus", 0.15)
            floor_boost = (cons_val / 100.0) * c_bonus
            v_low += floor_boost
            
            # Ensure v_low doesn't exceed v_high
            v_low = min(v_low, v_high - 0.01)
            
            make_pct = base_pct * random.uniform(v_low, v_high)
            
            # Hot Hand Bonus
            current_streak = streak_map.get(attacker.id, 0)
            if current_streak > 0:
                bonus_per = c("shooting", "hot_hand_bonus_per_streak", 0.05)
                cap = c("shooting", "hot_hand_cap", 0.15)
                bonus = min(current_streak * bonus_per, cap)
                make_pct += bonus

            # 3PT Penalty (Generic lower % for 3s)
            # Tuned: 0.85 -> 0.72 to match User's request (90->40%, 80->35%)
            if is_3pt: 
                penalty = c("shooting", "three_pt_penalty", 0.72)
                make_pct *= penalty
            
            # --- Phase 32: Apply Coach's Favorite Boost ---
            boost = boost_map.get(attacker.id, 0.0)
            if boost > 0:
                make_pct += boost

            # --- Phase 49: Scrub Boost (Bottom 4 bonus) ---
            # "排在上場表(12人上到下分配的那個)後面4位" -> Assuming lowest 4 OVR in roster
            if attacker.id in bottoms_map:
                if is_3pt:
                    make_pct += 0.10
                else:
                    make_pct += 0.20
            
            # --- Phase 50: Comeback Mechanic (Rubber Banding) ---
            if comeback_bonus:
                make_pct += 0.15

            # Record Attempt
            if is_3pt:
                stats[attacker.id]["3pa"] += 1
            else:
                stats[attacker.id]["2pa"] += 1
            
            is_made = random.random() < make_pct
            
            points_scored = 0
            
            if is_made:
                streak_map[attacker.id] += 1
                stats[attacker.id]["fgm"] += 1
                
                if is_3pt:
                    stats[attacker.id]["3pm"] += 1
                    stats[attacker.id]["pts"] += 3
                    points_scored = 3
                else:
                    stats[attacker.id]["2pm"] += 1
                    stats[attacker.id]["pts"] += 2
                    points_scored = 2
                
                # FT Logic (And-1 or fouled)
                if random.random() < 0.2:
                    stats[attacker.id]["pts"] += 1
                    points_scored += 1
                
                # Assist Check
                teammates = [p for p in off_lineup if p.id != attacker.id]
                if teammates:
                    # Phase 33 Revised: Position-Agnostic Playmaking
                    # Use Cubic Weighting to heavily favor high-attribute passers regardless of position
                    # 90^3 = 729k, 60^3 = 216k (3.3x more likely to be selected)
                    def get_pass_weight(p):
                        return p.attributes.passing ** 3

                    pass_weights = [get_pass_weight(p) for p in teammates]
                    
                    # Fix Crash: Ensure weights > 0
                    if sum(pass_weights) <= 0:
                        passer = random.choice(teammates)
                    else:
                        passer = random.choices(teammates, weights=pass_weights, k=1)[0]
                    
                    # Assist chance based on passer skill
                    # Target: 90 Passing -> ~10 APG, 80 Passing -> ~5 APG
                    # Math: 90 Passing selected ~45% of time. Needs ~55% conversion to get ~10 assists (on 40 team FGM).
                    # Formula: (Passing^2) / 15000
                    # 90^2 / 15000 = 0.54 (54%)
                    # 80^2 / 15000 = 0.42 (42%)
                    
                    # Phase 36: Apply OVR Factor (Small boost for OVR)
                    ovr_boost = get_ovr_factor(passer)
                    
                    pass_sq = passer.attributes.passing ** 2
                    ast_div = c("playmaking", "assist_divisor", 15000)
                    
                    ast_chance = (pass_sq / ast_div) * ovr_boost
                        
                    if random.random() < ast_chance:
                        stats[passer.id]["ast"] += 1
            else:
                # Miss -> Reset Streak
                streak_map[attacker.id] = 0
                
                # Miss -> Rebound
                def get_reb_weight(p, is_defense):
                    mult = 1.0
                    if p.pos == "C" or p.pos == "中鋒": mult = 2.5
                    elif p.pos == "PF" or p.pos == "大前鋒": mult = 2.0
                    elif "F" in p.pos or "前鋒" in p.pos: mult = 1.5
                    elif "G" in p.pos or "後衛" in p.pos: mult = 0.6 # Reduce guard rebounds
                    
                    # Phase 36: Apply OVR Factor
                    reb_val = p.attributes.rebound * get_ovr_factor(p)
                    
                    if is_defense:
                        return reb_val * 3.0 * mult
                    else:
                        return reb_val * mult

                off_reb_w = [get_reb_weight(p, False) for p in off_lineup]
                def_reb_w = [get_reb_weight(p, True) for p in def_lineup] 
                
                all_reb_candidates = off_lineup + def_lineup
                all_weights = off_reb_w + def_reb_w
                
                rebounder = random.choices(all_reb_candidates, weights=all_weights, k=1)[0]
                stats[rebounder.id]["reb"] += 1
                
                if rebounder in off_lineup:
                    stats[rebounder.id]["oreb"] += 1
                else:
                    stats[rebounder.id]["dreb"] += 1
            
            return points_scored

        # Run Loop (100 Possessions)
        # Phase 50: Running Score & Comeback Mode
        running_h = 0
        running_a = 0
        
        comeback_h = False
        comeback_a = False
        
        for tick in range(100):
            # Check Comeback State
            diff = running_h - running_a
            
            # Home Comeback Logic: Trailing > 20 (-21) -> Active. Stop if <= 10 (-10).
            if diff < -20: comeback_h = True
            elif diff >= -10: comeback_h = False
            
            # Away Comeback Logic: Trailing > 20 (+21) -> Active. Stop if <= 10 (+10).
            if diff > 20: comeback_a = True
            elif diff <= 10: comeback_a = False
            
            # Get Active 5 for this tick
            home_active = home_plan[tick] if tick < len(home_plan) else home_plan[-1]
            away_active = away_plan[tick] if tick < len(away_plan) else away_plan[-1]
            
            p_h = simulate_possession(home_team, away_team, home_active, away_active, comeback_bonus=comeback_h)
            running_h += p_h
            
            p_a = simulate_possession(away_team, home_team, away_active, home_active, comeback_bonus=comeback_a)
            running_a += p_a

        # --- 2b. Overtime Logic (Phase 48) ---
        # Calculate initial score
        current_home_points = sum(stats[p.id]["pts"] for p in home_team.roster)
        current_away_points = sum(stats[p.id]["pts"] for p in away_team.roster)
        
        ot_round = 0
        
        while current_home_points == current_away_points:
            ot_round += 1
            # Use Closing Lineup (last active unit in plan)
            h_lineup = home_plan[-1]
            a_lineup = away_plan[-1]
            
            # Single Possession Each (User Req: "兩邊各增加一回合")
            simulate_possession(home_team, away_team, h_lineup, a_lineup)
            simulate_possession(away_team, home_team, a_lineup, h_lineup)
            
            # Update Scores
            current_home_points = sum(stats[p.id]["pts"] for p in home_team.roster)
            current_away_points = sum(stats[p.id]["pts"] for p in away_team.roster)
            
            # If still tied, loop continues ("如果還是相同 就繼續")

        # --- 3. Finalize & Sync ---
        home_score = 0
        away_score = 0
        
        home_box = []
        away_box = []
        
        # Sync Logic
        for pid, s in stats.items():
            # Find player object
            player = next((p for p in home_team.roster + away_team.roster if p.id == pid), None)
            
            if player:
                # Accumulate Season Stats
                for k in s:
                    if k == "name": continue
                    player.stats[k] = player.stats.get(k, 0) + s[k]
                    
            if pid in [p.id for p in home_team.roster]:
                home_score += s["pts"]
                home_box.append(s)
            else:
                away_score += s["pts"]
                away_box.append(s)

        # Winner Logic
        if home_score > away_score:
            winner, loser = home_team, away_team
            home_team.wins += 1; away_team.losses += 1
        else:
            winner, loser = away_team, home_team
            away_team.wins += 1; home_team.losses += 1

        # MVP
        mvp_player = None
        best_eff = -999
        for p in winner.roster:
            s = stats[p.id]
            eff = s["pts"] + s["reb"] + s["ast"] + s["stl"] + s["blk"] - s["to"] - (s["fga"] - s["fgm"])
            if eff > best_eff:
                best_eff = eff
                mvp_player = p

        return {
            "home_team": home_team.name, "away_team": away_team.name,
            "home_score": home_score, "away_score": away_score,
            "winner": winner.name, "loser": loser.name,
            "mvp": mvp_player.mask_name if mvp_player else "None",
            "home_box_score": home_box, "away_box_score": away_box,
            "box_score": stats
        }
