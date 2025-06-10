import os
import hashlib
import secrets
from datetime import datetime, timedelta
from dotenv import load_dotenv
from .user_state import user_state

# 載入環境變數
load_dotenv()

def hash_password(password: str) -> str:
    """使用 SHA-256 進行密碼雜湊"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password: str) -> bool:
    """驗證管理員密碼"""
    stored_hash = os.getenv('ADMIN_PASSWORD_HASH')
    if not stored_hash:
        # 如果還沒有雜湊值，使用預設密碼並儲存其雜湊值
        default_password = os.getenv('ADMIN_PASSWORD', '960130')
        stored_hash = hash_password(default_password)
        # 在實際應用中，這裡應該將雜湊值保存到環境變數或資料庫
    
    return hash_password(password) == stored_hash

def generate_session_token() -> str:
    """生成安全的 session token"""
    return secrets.token_hex(32)

def login(user_id: str, password: str) -> tuple[bool, str]:
    """
    處理使用者登入
    返回: (是否成功, 訊息)
    """
    # 檢查是否被暫時封鎖
    if user_state.is_blocked(user_id):
        block_end = user_state.get_block_end_time(user_id)
        if block_end and datetime.now() < block_end:
            remaining = (block_end - datetime.now()).seconds // 60
            return False, f"帳號已被暫時封鎖，請等待 {remaining} 分鐘後再試"
        else:
            user_state.unblock_user(user_id)
    
    # 檢查登入嘗試次數
    attempts = user_state.get_login_attempts(user_id)
    if attempts >= 3:
        # 超過嘗試次數，暫時封鎖帳號（15分鐘）
        block_end = datetime.now() + timedelta(minutes=15)
        user_state.block_user(user_id, block_end)
        return False, "登入嘗試次數過多，帳號已被暫時封鎖15分鐘"
    
    # 驗證密碼
    if not verify_password(password):
        user_state.increment_login_attempts(user_id)
        remaining_attempts = 3 - user_state.get_login_attempts(user_id)
        return False, f"密碼錯誤，還剩 {remaining_attempts} 次嘗試機會"
    
    # 登入成功
    session_token = generate_session_token()
    user_state.set_admin_status(user_id, True)
    user_state.set_login_status(user_id, True)
    user_state.set_session_token(user_id, session_token)
    user_state.reset_login_attempts(user_id)
    
    return True, "登入成功！您現在處於管理員模式"

def logout(user_id: str) -> str:
    """處理使用者登出"""
    user_state.set_login_status(user_id, False)
    user_state.clear_session_token(user_id)
    return "已登出管理員模式"

def is_admin(user_id: str) -> bool:
    """檢查使用者是否為管理員且已登入"""
    return (user_state.is_admin(user_id) and 
            user_state.is_logged_in(user_id) and 
            user_state.has_valid_session(user_id))

def require_admin(func):
    """管理員權限檢查裝飾器"""
    def wrapper(user_id: str, *args, **kwargs):
        if not is_admin(user_id):
            return "此功能需要管理員權限"
        return func(user_id, *args, **kwargs)
    return wrapper 