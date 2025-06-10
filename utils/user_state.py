import json
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

class UserState:
    def __init__(self):
        self.state_file = "data/user_state.json"
        self.states: Dict[str, Dict[str, Any]] = {}
        self.load_states()
    
    def load_states(self):
        """從檔案載入使用者狀態"""
        try:
            if os.path.exists(self.state_file):
                with open(self.state_file, 'r', encoding='utf-8') as f:
                    self.states = json.load(f)
        except Exception as e:
            print(f"載入使用者狀態時發生錯誤：{e}")
            self.states = {}
    
    def save_states(self):
        """儲存使用者狀態到檔案"""
        try:
            os.makedirs(os.path.dirname(self.state_file), exist_ok=True)
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(self.states, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"儲存使用者狀態時發生錯誤：{e}")
    
    def get_user_state(self, user_id: str) -> dict:
        """取得使用者狀態，如果不存在則初始化"""
        if user_id not in self.states:
            self.states[user_id] = {
                "is_admin": False,
                "is_logged_in": False,
                "login_attempts": 0,
                "last_attempt_time": None,
                "blocked_until": None,
                "session_token": None,
                "session_created": None
            }
            self.save_states()
        return self.states[user_id]
    
    def is_admin(self, user_id: str) -> bool:
        """檢查使用者是否為管理員"""
        return self.get_user_state(user_id).get("is_admin", False)
    
    def is_logged_in(self, user_id: str) -> bool:
        """檢查使用者是否已登入"""
        return self.get_user_state(user_id).get("is_logged_in", False)
    
    def set_admin_status(self, user_id: str, status: bool):
        """設定使用者的管理員狀態"""
        state = self.get_user_state(user_id)
        state["is_admin"] = status
        self.save_states()
    
    def set_login_status(self, user_id: str, status: bool):
        """設定使用者的登入狀態"""
        state = self.get_user_state(user_id)
        state["is_logged_in"] = status
        if not status:
            state["session_token"] = None
            state["session_created"] = None
        self.save_states()
    
    def get_login_attempts(self, user_id: str) -> int:
        """取得登入嘗試次數"""
        return self.get_user_state(user_id).get("login_attempts", 0)
    
    def increment_login_attempts(self, user_id: str):
        """增加登入嘗試次數"""
        state = self.get_user_state(user_id)
        state["login_attempts"] = state.get("login_attempts", 0) + 1
        state["last_attempt_time"] = datetime.now().isoformat()
        self.save_states()
    
    def reset_login_attempts(self, user_id: str):
        """重置登入嘗試次數"""
        state = self.get_user_state(user_id)
        state["login_attempts"] = 0
        state["last_attempt_time"] = None
        state["blocked_until"] = None
        self.save_states()
    
    def block_user(self, user_id: str, until: datetime):
        """暫時封鎖使用者"""
        state = self.get_user_state(user_id)
        state["blocked_until"] = until.isoformat()
        self.save_states()
    
    def unblock_user(self, user_id: str):
        """解除使用者封鎖"""
        state = self.get_user_state(user_id)
        state["blocked_until"] = None
        state["login_attempts"] = 0
        self.save_states()
    
    def is_blocked(self, user_id: str) -> bool:
        """檢查使用者是否被封鎖"""
        state = self.get_user_state(user_id)
        blocked_until = state.get("blocked_until")
        if not blocked_until:
            return False
        return datetime.now() < datetime.fromisoformat(blocked_until)
    
    def get_block_end_time(self, user_id: str) -> Optional[datetime]:
        """取得封鎖結束時間"""
        state = self.get_user_state(user_id)
        blocked_until = state.get("blocked_until")
        return datetime.fromisoformat(blocked_until) if blocked_until else None
    
    def set_session_token(self, user_id: str, token: str):
        """設定 session token"""
        state = self.get_user_state(user_id)
        state["session_token"] = token
        state["session_created"] = datetime.now().isoformat()
        self.save_states()
    
    def clear_session_token(self, user_id: str):
        """清除 session token"""
        state = self.get_user_state(user_id)
        state["session_token"] = None
        state["session_created"] = None
        self.save_states()
    
    def has_valid_session(self, user_id: str) -> bool:
        """檢查 session 是否有效"""
        state = self.get_user_state(user_id)
        token = state.get("session_token")
        created = state.get("session_created")
        
        if not token or not created:
            return False
        
        # session 有效期為 24 小時
        created_time = datetime.fromisoformat(created)
        return datetime.now() - created_time < timedelta(hours=24)

# 建立全域實例
user_state = UserState() 