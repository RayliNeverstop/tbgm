from dataclasses import dataclass, field
from typing import Dict, Any, List

@dataclass
class PlayerAttributes:
    two_pt: int = 0
    three_pt: int = 0
    rebound: int = 0
    passing: int = 0
    consistency: int = 0
    block: int = 0
    steal: int = 0
    defense: int = 0

    @classmethod
    def from_dict(cls, data: Dict[str, int]):
        return cls(
            two_pt=data.get("2pt", 0),
            three_pt=data.get("3pt", 0),
            rebound=data.get("rebound", 0),
            passing=data.get("pass", 0),
            consistency=data.get("consistency", 0),
            block=data.get("block", 0),
            steal=data.get("steal", 0),
            defense=data.get("def", 0)
        )

@dataclass
class Player:
    id: str
    real_name: str
    team_id: str
    pos: str
    salary: float
    age: int
    attributes: PlayerAttributes
    mask_name: str = ""
    ovr: int = 0
    
    # Additional specific attributes from prompt
    number: int = 0 
    contract_length: int = 1
    stats: Dict[str, float] = field(default_factory=lambda: {"games": 0, "pts": 0, "reb": 0, "ast": 0})
    history: List[Dict[str, Any]] = field(default_factory=list)
    potential: int = 0
    is_scouted: bool = False
    offense_status: int = 0
    years_on_team: int = 0

    @staticmethod
    def calculate_ovr(attr: PlayerAttributes) -> int:
        # User Formula:
        # MAX(2pt, 3pt)*0.32 + MIN(2pt, 3pt)*0.08 
        # + MAX(Stl, Blk, Def)*0.4 
        # + ((Cons+Def)/2)*0.1 
        # + MAX(Reb, Pass)*0.1
        
        # 1. Scoring (40%)
        # Weighted towards best scoring attribute
        s_max = max(attr.two_pt, attr.three_pt)
        s_min = min(attr.two_pt, attr.three_pt)
        score_val = (s_max * 0.32) + (s_min * 0.08)
        
        # 2. Defense (40%)
        # Based on best defensive stat
        # Note: 'defense' attribute is 'def' key usually, assumed mapped correctly in PlayerAttributes
        def_val = max(attr.steal, attr.block, attr.defense) * 0.40
        
        # 3. Stability/Defense Mix (10%)
        mix_val = ((attr.consistency + attr.defense) / 2) * 0.10
        
        # 4. Utility (10%)
        util_val = max(attr.rebound, attr.passing) * 0.10
        
        total = score_val + def_val + mix_val + util_val
        return int(round(total))

    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        attr_data = data.get("attributes", {})
        attributes = PlayerAttributes.from_dict(attr_data)
        
        # Salary Normalization Logic
        # Input is usually huge (e.g. 25000000 or 850000)
        # We want to display in Millions (e.g. 25.0M or 0.85M)
        raw_salary = data.get("salary", 0)
        try:
            val = float(raw_salary)
            if val > 500: # If > 500, assume raw currency, convert to M
                 salary = round(val / 1000000, 2)
            else: # Already in M or very small
                 salary = round(val, 2)
        except:
            salary = 0.0
            
        # OVR Logic: Dynamic Calculation (Phase 35)
        # Override file OVR with formula OVR
        ovr = cls.calculate_ovr(attributes)
        
        # Potential logic
        potential = data.get("potential", 0)
        if potential == 0:
            import random
            age = data.get("age", 20)
            if age < 25:
                potential = ovr + random.randint(5, 15)
            elif age < 30:
                potential = ovr + random.randint(0, 5)
            else:
                potential = ovr # Old players peaked
            
            # Cap potential at 99
            potential = min(99, potential)
            
        return cls(
            id=str(data.get("id", "")),
            real_name=data.get("real_name", "Unknown"),
            mask_name=data.get("mask_name", ""),
            team_id=data.get("team_id", ""),
            pos=data.get("pos", "PG"),
            ovr=ovr,
            salary=salary,
            age=data.get("age", 20),
            attributes=attributes,
            number=data.get("number", 0),
            contract_length=data.get("contract_length", 1),
            stats=data.get("stats", {"games": 0, "pts": 0, "reb": 0, "ast": 0}),
            history=data.get("history", []),
            potential=potential,
            is_scouted=data.get("is_scouted", False),
            offense_status=data.get("offense_status", 0),
            years_on_team=data.get("years_on_team", 0)
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "real_name": self.real_name,
            "mask_name": self.mask_name,
            "team_id": self.team_id,
            "pos": self.pos,
            "ovr": self.ovr,
            "salary": self.salary,
            "age": self.age,
            "number": self.number,
            "contract_length": self.contract_length,
            "stats": self.stats,
            "history": self.history,
            "potential": self.potential,
            "is_scouted": self.is_scouted,
            "offense_status": self.offense_status,
            "years_on_team": self.years_on_team,
            "attributes": {
                "2pt": self.attributes.two_pt,
                "3pt": self.attributes.three_pt,
                "rebound": self.attributes.rebound,
                "pass": self.attributes.passing,
                "consistency": self.attributes.consistency,
                "block": self.attributes.block,
                "steal": self.attributes.steal,
                "def": self.attributes.defense
            }
        }

    def update_ovr(self):
        """Recalculates OVR based on current attributes."""
        self.ovr = Player.calculate_ovr(self.attributes)
