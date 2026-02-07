import pandas as pd
import json
import os
from typing import Dict, List, Any

# Column Mapping based on user request
COL_MAPPING = {
    "位置": "pos",
    "背號": "number",
    "球隊": "team_id",
    "兩分": "2pt",
    "三分": "3pt",
    "籃板": "rebound",
    "傳球": "pass",
    "穩定性": "consistency",
    "阻攻": "block",
    "抄截": "steal",
    "防守": "def",
    "合約長度": "contract_length",
    "薪水": "salary",
    "總評": "ovr",
    "年齡": "age",
    "姓名": "real_name",
    "名字": "real_name",
    "潛力": "potential",
    "進攻狀態": "offense_status"
}

def safe_int(val, default=0):
    try:
        if pd.isna(val) or val == "":
            return default
        return int(float(val))
    except:
        return default

def normalize_salary(val):
    """
    Converts raw salary (Yuan) to Millions (M).
    If value > 1,000,000, divide by 1M and round.
    If value is already small (presumably M), keep it.
    """
    try:
        if pd.isna(val) or val == "":
            return 0
        amount = float(val)
        if amount > 500: # Threshold: Assume values > 500 are raw dollars, not millions
            return round(amount / 1000000, 2)
        return round(amount, 2)
    except:
        return 0

def convert_excel_to_json(excel_path: str, output_path: str):
    if not os.path.exists(excel_path):
        print(f"Error: File not found at {excel_path}")
        return

    try:
        df = pd.read_excel(excel_path)
        # Strip whitespace from column names
        df.columns = df.columns.str.strip()
    except Exception as e:
        print(f"Error reading Excel file: {e}")
        return

    # Check for required columns
    print("Columns found:", df.columns.tolist())
    
    # Generate unique teams
    if "球隊" in df.columns:
        unique_teams = df["球隊"].dropna().unique()
        teams_data = []
        team_id_map = {}
        
        fa_keywords = ["自由", "自由球員", "Free Agents", "FA"]
        
        team_counter = 1
        for team_val in unique_teams:
            team_str = str(team_val).strip()
            
            # Map Free Agents to T00 and skip generic team creation
            if team_str in fa_keywords:
                team_id_map[team_val] = "T00"
                continue
            
            t_id = f"T{str(team_counter).zfill(2)}"
            team_counter += 1
            team_id_map[team_val] = t_id
            
            colors = ["#FF5733", "#33FF57", "#3357FF", "#F1C40F", "#8E44AD", "#E67E22", "#2ECC71", "#E74C3C"]
            color = colors[(team_counter - 2) % len(colors)]
            
            teams_data.append({
                "id": t_id,
                "name": str(team_val),
                "color": color
            })
            
        # Always ensure T00 exists
        teams_data.append({"id": "T00", "name": "Free Agents", "color": "#333333"})
            
    else:
        print("Warning: '球隊' column not found. Defaulting to one team.")
        teams_data = [{"id": "T00", "name": "Free Agents", "color": "#333333"}]
        team_id_map = {}

    players_data = []
    
    for index, row in df.iterrows():
        # Generate ID
        p_id = f"P{str(index+1).zfill(3)}"
        
        # Handle Name
        real_name = str(row.get("姓名", row.get("名字", f"Player {index+1}")))
        if pd.isna(real_name) or real_name == "nan":
             real_name = f"Player {index+1}"
        
        # Mask Name
        parts = real_name.split()
        if len(parts) > 1:
            mask_name = f"{parts[0][0]}. {parts[-1]}"
        else:
            mask_name = real_name 
            
        # Potentia Logic: Explicit import
        # If missing, it will be 0 and handled by Player.from_dict
        potential = safe_int(row.get("潛力"), 0)
        
        # Offense Status Logic
        off_status = safe_int(row.get("進攻狀態"), 0) 

        # Map Team
        raw_team = row.get("球隊")
        team_id = team_id_map.get(raw_team, "T00")

        # Map Attributes
        attr_dict = {}
        for chi_col, eng_key in COL_MAPPING.items():
            if eng_key in ["2pt", "3pt", "rebound", "pass", "consistency", "block", "steal", "def"]:
                val = row.get(chi_col, 0)
                attr_dict[eng_key] = safe_int(val)
        
        player = {
            "id": p_id,
            "real_name": real_name,
            "mask_name": mask_name,
            "team_id": team_id,
            "pos": str(row.get("位置", "PG")).upper(),
            "ovr": safe_int(row.get("總評"), 60),
            "salary": normalize_salary(row.get("薪水")),
            "age": safe_int(row.get("年齡"), 20),
            "number": safe_int(row.get("背號"), 0),
            "contract_length": safe_int(row.get("合約長度"), 1),
            "attributes": attr_dict,
            "potential": potential,
            "offense_status": off_status
        }
        players_data.append(player)

    # Construct Final JSON
    game_data = {
        "version": "1.0",
        "salary_cap": 70,
        "user_team_id": teams_data[0]["id"] if teams_data else "",
        "teams": teams_data,
        "roster": players_data
    }
    
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(game_data, f, indent=4, ensure_ascii=False)
        print(f"Successfully created {output_path}")
        print(f"Total Teams: {len(teams_data)}")
        print(f"Total Players: {len(players_data)}")
    except Exception as e:
        print(f"Error writing JSON: {e}")

if __name__ == "__main__":
    import sys
    # Usage: python excel_to_json.py [input.xlsx] [output.json]
    input_file = "players.xlsx" # Default
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # Default output to relative data folder if not specified
    output_file = os.path.join(current_dir, "..", "data", "gamedata.json")
    if len(sys.argv) > 2:
        output_file = sys.argv[2]
        
    print(f"Converting {input_file} to {output_file}...")
    convert_excel_to_json(input_file, output_file)
