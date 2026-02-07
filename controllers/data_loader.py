import json
import os
from typing import Dict, Any, List
from models.player import Player
from models.team import Team

class DataLoader:
    def __init__(self, data_path: str):
        self.data_path = data_path

    def load_data(self) -> Dict[str, Any]:
        if not os.path.exists(self.data_path):
            return {}
        
        with open(self.data_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data

    @staticmethod
    def apply_masking(real_name: str) -> str:
        """
        Applies masking rules:
        Rule 1: Retain Last Name.
        Rule 2: First Name First Initial.
        Rule 3: If string too short, do nothing.
        Example: "LeBron James" -> "L. James"
        """
        if not real_name or len(real_name) < 3:
            return real_name

        parts = real_name.split()
        if len(parts) < 2:
            return real_name

        first_name = parts[0]
        last_name = " ".join(parts[1:]) # Handle multi-word last names roughly, or just take last part

        # Taking the first char of first name
        masked_name = f"{first_name[0]}. {last_name}"
        return masked_name

    def process_data_into_objects(self, raw_data: Dict[str, Any]) -> tuple[List[Team], List[Player]]:
        teams_data = raw_data.get("teams", [])
        # Support both 'players' (Save File) and 'roster' (Template) keys
        roster_data = raw_data.get("players") or raw_data.get("roster", [])

        all_players = []
        for p_data in roster_data:
            # Apply masking if mask_name is empty
            if not p_data.get("mask_name"):
                real_name = p_data.get("real_name", "")
                p_data["mask_name"] = self.apply_masking(real_name)
            
            player = Player.from_dict(p_data)
            all_players.append(player)

        all_teams = []
        for t_data in teams_data:
            team = Team.from_dict(t_data, all_players)
            all_teams.append(team)

        return all_teams, all_players
