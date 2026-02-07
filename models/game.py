from dataclasses import dataclass, field
from typing import Dict, Any, Optional
from models.team import Team

@dataclass
class Game:
    id: str
    day: int
    home_team: Team
    away_team: Team
    played: bool = False
    result: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "day": self.day,
            "home_team_id": self.home_team.id,
            "away_team_id": self.away_team.id,
            "played": self.played,
            "result": self.result
        }
