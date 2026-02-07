from dataclasses import dataclass, field
from typing import List, Dict, Any
from .player import Player

@dataclass
class Team:
    id: str
    name: str
    color: str
    roster: List[Player] = field(default_factory=list)
    draft_picks: List[Dict[str, Any]] = field(default_factory=list)
    wins: int = 0
    losses: int = 0
    
    strategy_settings: Dict[str, Any] = field(default_factory=lambda: {
        "tactics": "Balanced", 
        "scoring_options": [], 
        "rotation_settings": {}
    })

    # Derived property, but we might want to cache it or just calculate on fly
    @property
    def salary_total(self) -> int:
        return sum(p.salary for p in self.roster)

    @property
    def average_ovr(self) -> float:
        if not self.roster:
            return 0.0
        return sum(p.ovr for p in self.roster) / len(self.roster)

    @classmethod
    def from_dict(cls, data: Dict[str, Any], all_players: List[Player] = None):
        """
        Create a Team object from a dictionary.
        Note: `all_players` is a list of ALL players in the game, 
        used to filter and assign players to this team based on team_id.
        """
        team_id = data.get("id", "")
        team_players = []
        if all_players:
            team_players = [p for p in all_players if p.team_id == team_id]
        
        # Restore strategy or default
        saved_strategy = data.get("strategy_settings", {})
        default_strategy = {
            "tactics": "Balanced", 
            "scoring_options": [], 
            "rotation_settings": {}
        }
        # Merge saved with default to ensure all keys exist
        strategy = {**default_strategy, **saved_strategy}

        return cls(
            id=team_id,
            name=data.get("name", "Unknown Team"),
            color=data.get("color", "#FFFFFF"),
            roster=team_players,
            draft_picks=data.get("draft_picks", []),
            wins=data.get("wins", 0),
            losses=data.get("losses", 0),
            strategy_settings=strategy
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "color": self.color,
            "wins": self.wins,
            "losses": self.losses,
            "draft_picks": self.draft_picks,
            "strategy_settings": self.strategy_settings
        }
