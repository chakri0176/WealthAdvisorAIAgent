import sqlite3
import json
import os
from datetime import datetime
from typing import Optional

DB_PATH = os.path.join(os.path.dirname(__file__),"wealthadvisor.db")

def init_db():
    """Create database tables if they don't exist"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    #Client portfolio table
    cursor.execute("""
        CREATE TAVKE IF NOT EXISTS client_profiles(
            client_id TEXT PRIMARY KEY,
            client_name TEXT,
            risk_tolerance TEXT DEFAULT 'moderate',
            investment_goals TEXT DEFAULT '',
            time_horizon TEXT DEFAULT '',
            created_at TEXT,
            updated_at TEXT               
        )
    """)
    
    #Analysis sessions table
    cursor.execute("""
       CREATE TABLE IF NOT EXISTS analysis_sessions(
           session_id TEXT PRIMARY KEY,
           client_id TEXT,
           portfolio_data TEXT,
           risk_output TEXT,
           planning_output TEXT,
           client_summary TEXT,
           risk_score TEXT,
           created_at TEXT,
           FOREIGN KEY (client_id) REFEREMCES client_profiles(client_id)
       )            
    """)
    
    #Chat history table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chat_history(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id TEXT,
            session_id TEXT,
            role TEXT,
            content TEXT,
            created_at TEXT
        )
    """)
    
    conn.commit()
    conn.close()
    
#Initialize DB when module loads
init_db()

def save_client_profile(
    client_id: str,
    client_name: str,
    risk_tolerance: str = "moderate",
    investment_goals: str="",
    time_horizon: str=""
)->None:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    now = datetime.now().isoformat()
    
    cursor.execute("""
                   INSERT OR REPLACE INTO client_profiles(
                       client_id,
                       client_name,
                       risk_tolerance,
                       investment_goals,
                       time_horizon,
                       created_at,
                       updated_at = datetime.now.isoformat()
                   )
                   VALUES(?,?,?,?,?,?,?)
                   """,(client_id,client_name,risk_tolerance,investment_goals,time_horizon,now,now))
    
    conn.commit()
    conn.close()


def save_analysis_session(
    client_id: str,
    session_id: str,
    portfolio_data: str,
    risk_output: str = "",
    planning_output: str = "",
    client_summary: str = "",
    risk_score: str = ""
)->None:
    pass 


def load_client_history(client_id: str, limit: int=5)-> list:
    pass

def get_client_profile(client_id: str)-> Optional[dict]:
    pass