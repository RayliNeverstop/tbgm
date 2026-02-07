
# Localization Utility
# Stores translations and manages language state.

class LocalizationManager:
    def __init__(self):
        self.lang = "zh" # Default to Chinese as requested
        
        self.translations = {
            # --- Navigation ---
            "Dashboard": "儀表板",
            "Roster": "陣容管理",
            "Strategy": "戰術設定",
            "Market": "自由市場",
            "League": "聯盟資訊",
            "Standings": "戰績排行",
            "Scouting": "選秀預覽", # Updated from "新秀球探" to "選秀預覽"
            "Trades": "球員交易",
            "Progression": "球員成長",
            "Matches": "比賽日程",
            "Playoffs": "季後賽",
            "Simulate": "模擬",
            "Next Day": "下一天",
            "Save Game": "儲存進度",
            "Exit": "退出",

            # --- Common Actions ---
            "Save": "儲存",
            "Cancel": "取消",
            "Confirm": "確認",
            "Close": "關閉",
            "View": "檢視",
            "Back": "返回",
            "Release": "釋出",
            "Sign": "簽約",
            "Trade": "交易",
            "Simulate Game": "模擬比賽",
            "Simulate Week": "模擬一週",
            "Simulate Month": "模擬一月",
            
            # --- Roster View & Stats ---
            "Select Team": "請選擇球隊",
            "Stats": "數據",
            "Attributes": "能力",
            "Pos": "位置", # Short for Position
            "Name": "姓名",
            "In": "內", # Inside
            "Out": "外", # Outside
            "Pas": "傳", # Passing
            "Reb": "板", # Rebound
            "Def": "防", # Defense
            "Stl": "抄", # Steal - Short
            "Blk": "阻", # Block - Short
            "I.Q.": "智", # Game IQ / Consistency
            
            "Inside Scoring": "內線得分",
            "Outside Scoring": "外線得分",
            "Passing": "傳球能力",
            "Rebound": "籃板能力",
            "Defense": "防守能力",
            "Steal": "抄截能力",
            "Block": "阻攻能力",
            "Consistency": "穩定/球商",
            
            "Player Roster": "球員名單",
            "Cap Space": "薪資空間",
            "Luxury Tax": "豪華稅線",
            "Status": "狀態",
            "History": "歷史數據",
            "No History": "無歷史數據",
            "Age": "年齡",
            "OVR": "總評",
            "Salary": "薪資",
            "Contract": "合約",
            "Yrs": "年",
            
            # --- Strategy View ---
            "Team Strategy": "球隊戰術",
            "Strategy & Gameplan": "球隊策略與計畫",
            "Tactics": "進攻戰術",
            "Team Tactics": "團隊戰術",
            "Scoring Options": "進攻重心",
            "Rotation": "輪替設定",
            
            "Balanced (Default)": "平衡戰術 (預設)",
            "Pound the Paint (Inside Focus)": "強攻內線 (禁區主攻)",
            "Let it Fly (Outside Focus)": "外線跑轟 (外線主攻)",
            "7 Seconds or Less (Pace)": "七秒進攻 (跑轟)",
            
            "Offensive Hierarchy": "進攻階層 (重心)",
            "1st Option (Go-to Guy)": "第一進攻點 (王牌)",
            "2nd Option": "第二進攻點",
            "3rd Option": "第三進攻點",
            "None": "無",
            
            "Rotation Management": "輪替管理",
            "Adjust playing time and role for each player.": "調整每位球員的上場時間與角色定位。",
            "Save Strategy & Gameplan": "儲存策略設定",
            
            "Player": "球員",
            "Role/Minutes": "角色/時間",
            "++ Star": "++ 核心",
            "+ More": "+ 增加",
            "Normal": "正常",
            "- Less": "- 減少",
            "-- Bench": "-- 替補",
            
            "Balanced": "平衡戰術",
            "Pace": "跑轟戰術",
            "Inside": "內線主攻",
            "Outside": "外線投射",
            "Option 1": "第一進攻點",
            "Option 2": "第二進攻點",
            "Option 3": "第三進攻點",
            
            # --- Standings/League ---
            "League Standings": "聯盟戰績",
            "Conference": "分區",
            "Wins": "勝",
            "Losses": "敗",
            "W": "勝",
            "L": "敗",
            "Pct": "勝率",
            "Rank": "排名",
            "Strk": "近況",
            "Streak": "連勝敗",
            "Games Back": "勝差",
            "* Top 4 teams qualify for Playoffs": "* 前四名球隊晉級季後賽",
            
            "Player Details": "球員詳情",
            "General Info": "基本資料",
            "Season Stats": "賽季數據",
            "Career Stats": "生涯數據",
            "Real Name": "真名",
            
            "Close": "關閉",
            "Height": "身高",
            "Year": "賽季",
            "Team": "球隊",
            "GP": "出賽",
            
            # --- Market/Scouting ---
            "Free Agency Market": "自由球員市場",
            "Free Agents": "自由球員",
            "Draft Class": "待選新秀",
            "Draft Scouting": "新秀球探",
            "Scouting Points Available": "可用球探點數",
            "No active draft class. Wait for next season.": "目前無待選新秀，請等待下一季。",
            "Scout": "偵查",
            "Scouted": "已偵查",
            "Points Left": "剩餘點數",
            "Draft & Sign": "選秀並簽約",
            "Scout (-10)": "偵查 (-10點)",
            "Drafted": "已選中",
            "Draft Complete! Season Schedule Generated.": "選秀完成！新賽季賽程已生成。",
            "Finish Draft & Start Season": "完成選秀並開始賽季",
            "POT": "潛力", # Potential
            
            # --- Attributes (Player Detail) ---
            "Inside": "內線",
            "Outside": "外線",
            "IQ": "球商",
            "Passing": "傳球",
            "Rebound": "籃板",
            "Defense": "防守",
            "Consistency": "穩定度",
            "Steal_Attr": "抄截",
            "Block_Attr": "阻攻",
            "Season Stats": "賽季數據",
            "Year": "年份",
            
            
            # --- Trade ---
            "Select Team": "選擇球隊",
            "Select Trading Partner": "選擇交易對象",
            "Trade Center": "交易中心",
            "Your Team": "您的球隊",
            "Load Roster": "讀取名單",
            "Evaluate & Execute Trade": "評估並執行交易",
            "Find Deals (AI)": "尋找交易方案 (AI)",
            
            "Trade Proposal": "交易提案",
            "Execute Trade": "執行交易",
            "Salary Match": "薪資匹配",
            "Success": "成功",
            "Fail": "失敗",
            "Selected: Out": "選擇: 送出",
            
            "Trade Rejected": "交易被拒絕",
            "Rule Violation": "違反規則",
            "Offer from": "來自",
            "Receiving": "獲得球員",
            "Searching for trades...": "搜尋交易中...",
            "Trade Offers": "交易報價",
            "Accept Offer": "接受報價",
            "Found": "找到",
            "Offers": "個報價",
            "Trade Accepted! Transaction Complete.": "交易成功！祝合作愉快。",
            "Match Center": "比賽中心",
            
            # --- Stats ---
            "League Leaders": "聯盟數據王",
            "Points Per Game": "場均得分",
            "Rebounds Per Game": "場均籃板",
            "Assists Per Game": "場均助攻",
            "Steals Per Game": "場均抄截",
            "Blocks Per Game": "場均阻攻",
            "2PT Made": "兩分球命中數",
            "3PT Made": "三分球命中數",
            "No stats available yet. Simulate games first.": "尚無數據，請先模擬比賽。",
            
            "Day": "第", 
            "Playoffs: Semi-Finals": "季後賽：準決賽",
            "Playoffs: Finals": "季後賽：總決賽",
            "Season Finished": "賽季結束",
            "Simulate Next Game": "模擬下一場",
            "View Season Summary": "查看賽季總結",
            "Game Log": "比賽日誌",
            "Results": "賽果",
            "Simulation Complete": "模擬完成",
            "Game Summary": "比賽數據",
            "Home": "主隊",
            "Away": "客隊",
            "TO": "失誤", # Turnover
            "Record": "戰績",
            "Salary Cap": "團隊薪資",
            "No stats available": "無數據",
            "Today's Matches": "今日賽程",
            "No games scheduled for today.": "今日無賽程",
            
            # --- Market ---
            "No Free Agents available.": "目前無自由球員。",
            "Age": "年齡",
            "Sign": "簽約",
            
            # --- Progression ---
            "Season Progression Report": "賽季成長報告",
            "No progression data available yet. Finish a season first.": "尚無成長數據，請先完成一個賽季。",
            "Progression": "成長幅度",
            
            # --- Offseason ---
            "League Champion (Playoffs)": "年度總冠軍",
            "Regular Season Leader": "例行賽龍頭",
            "Retirements": "退休球員",
            "No retirements this year.": "本季無球員退休。",
            "Start Next Season": "開始下一季",
            "Season Finished": "賽季結束",
            
            # --- Dashboard ---
            "Season started. Good luck!": "賽季已開始，祝好運！",
            "Recent News": "最新消息",
            "Game Saved Successfully!": "進度儲存成功！",
            "Failed to Save Game.": "儲存失敗。",
            
            # --- Negotiation ---
            "Contract Status": "合約狀態",
            "Current Salary": "目前薪資",
            "Years Left": "合約年限",
            "Years on Team": "在隊年份",
            "Estimated Value": "預估身價",
            "Negotiation Table": "談判桌",
            "Offer Amount (Per Year)": "提供報價 (年薪)",
            "Contract Length": "合約長度",
            "Make Offer": "提出報價",
            "Mood": "心情",
            "ACCEPTED": "成交",
            "SIGNED": "已簽約",
            "ERROR": "錯誤",
            "COUNTER": "反報價",
            "REJECTED": "拒絕",
            "WALKED AWAY": "談判破裂",
            "Negotiate": "談判",
            "Player is on another team": "該球員隸屬其他球隊",
            "Contract valid for": "合約尚餘",

            "years": "年",
            "Draft Class Preview": "待選新秀預覽",
        }

    def tr(self, key: str) -> str:
        """Returns the translation for the given key in the current language."""
        if self.lang == "zh":
            return self.translations.get(key, key) # Return key if translation missing
        return key # Return English key if lang is not zh

# Singleton Instance
_loc_manager = LocalizationManager()

def tr(key: str) -> str:
    return _loc_manager.tr(key)

def set_language(lang: str):
    _loc_manager.lang = lang

def get_language() -> str:
    return _loc_manager.lang
