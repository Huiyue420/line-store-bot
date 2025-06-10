from typing import List, Dict
import re
from .auth import login, logout, is_admin
from .menu import menu_manager
from .order import order_manager
from .user_state import user_state

def parse_order_command(command: str) -> List[Dict[str, int]]:
    """解析訂單命令
    格式：order 商品名稱1 數量1 商品名稱2 數量2 ...
    """
    parts = command.split()[1:]  # 移除 "order" 命令
    if len(parts) % 2 != 0:
        raise ValueError("訂單格式錯誤，請使用：order 商品名稱 數量 [商品名稱 數量 ...]")
    
    items = []
    for i in range(0, len(parts), 2):
        try:
            quantity = int(parts[i + 1])
            if quantity <= 0:
                raise ValueError
        except ValueError:
            raise ValueError(f"商品數量必須為正整數：{parts[i + 1]}")
        
        items.append({
            "name": parts[i],
            "quantity": quantity
        })
    
    return items

def parse_edit_menu_command(command: str) -> tuple[str, str, List[str]]:
    """解析編輯商品命令
    格式：
    - edit menu add 商品名稱 價格 庫存 [描述]
    - edit menu edit 商品名稱 [價格 庫存 描述]
    - edit menu delete 商品名稱
    """
    parts = command.split()
    if len(parts) < 4:
        raise ValueError("命令格式錯誤")
    
    action = parts[2]
    name = parts[3]
    
    if action == "add":
        if len(parts) < 6:
            raise ValueError("新增商品需要指定價格和庫存")
        try:
            price = int(parts[4])
            stock = int(parts[5])
            if price <= 0 or stock < 0:
                raise ValueError
        except ValueError:
            raise ValueError("價格必須為正整數，庫存必須為非負整數")
        
        description = " ".join(parts[6:]) if len(parts) > 6 else ""
        return action, name, [price, stock, description]
    
    elif action == "edit":
        if len(parts) < 5:
            raise ValueError("編輯商品需要至少一個參數")
        try:
            price = int(parts[4]) if len(parts) > 4 else None
            stock = int(parts[5]) if len(parts) > 5 else None
            if (price is not None and price <= 0) or (stock is not None and stock < 0):
                raise ValueError
        except ValueError:
            raise ValueError("價格必須為正整數，庫存必須為非負整數")
        
        description = " ".join(parts[6:]) if len(parts) > 6 else None
        return action, name, [price, stock, description]
    
    elif action == "delete":
        return action, name, []
    
    else:
        raise ValueError("無效的操作：" + action)

def handle_command(text: str, user_id: str) -> str:
    """處理使用者命令"""
    text = text.strip()
    
    # 處理管理員登入
    if text.startswith("!admin"):
        parts = text.split()
        if len(parts) == 1:
            return "請輸入管理員密碼"
        success, message = login(user_id, parts[1])
        return message
    
    # 處理登出
    if text == "logout":
        if not is_admin(user_id):
            return "您不是管理員"
        return logout(user_id)
    
    # 處理一般命令
    try:
        if text == "menu":
            return menu_manager.get_menu()
        
        elif text == "help":
            if not is_admin(user_id):
                help_text = (
                    "🤖 商品販售小幫手使用說明\n\n"
                    "一般指令：\n"
                    "- menu：查看商品目錄\n"
                    "- order 商品名稱 數量 [商品名稱 數量 ...]：下訂單\n"
                    "- myorders：查看我的訂單\n"
                    "- help：顯示此說明\n\n"
                    "如需協助，請聯繫管理員。"
                )
                return help_text
            else:
                help_text = (
                    "🤖 商品販售小幫手使用說明 (管理員模式)\n\n"
                    "一般指令：\n"
                    "- menu：查看商品目錄\n"
                    "- order 商品名稱 數量 [商品名稱 數量 ...]：下訂單\n"
                    "- myorders：查看我的訂單\n"
                    "- help：顯示此說明\n\n"
                    "管理員指令：\n"
                    "- !admin 密碼：登入管理員模式\n"
                    "- edit menu add 商品名稱 價格 庫存 [描述]：新增商品\n"
                    "- edit menu edit 商品名稱 [價格 庫存 描述]：編輯商品\n"
                    "- edit menu delete 商品名稱：刪除商品\n"
                    "- view orders [status]：查看訂單\n"
                    "- update order 訂單編號 狀態：更新訂單狀態\n"
                    "- logout：登出管理員模式"
                )
                return help_text
        
        elif text.startswith("order "):
            items = parse_order_command(text)
            return order_manager.create_order(user_id, items)
        
        elif text == "myorders":
            return order_manager.get_user_orders(user_id)
        
        elif text.startswith("edit menu "):
            if not is_admin(user_id):
                return "此功能需要管理員權限"
            
            action, name, params = parse_edit_menu_command(text)
            if action == "add":
                return menu_manager.add_item(user_id, name, params[0], params[1], params[2])
            elif action == "edit":
                return menu_manager.edit_item(user_id, name, params[0], params[1], params[2])
            else:  # delete
                return menu_manager.delete_item(user_id, name)
        
        elif text.startswith("view orders"):
            if not is_admin(user_id):
                return "此功能需要管理員權限"
            
            parts = text.split()
            status = parts[2] if len(parts) > 2 else None
            return order_manager.view_orders(user_id, status)
        
        elif text.startswith("update order "):
            if not is_admin(user_id):
                return "此功能需要管理員權限"
            
            parts = text.split()
            if len(parts) != 4:
                return "命令格式：update order 訂單編號 狀態"
            
            try:
                order_id = int(parts[2])
            except ValueError:
                return "訂單編號必須為數字"
            
            return order_manager.update_order_status(user_id, order_id, parts[3])
        
        else:
            return "無效的命令。輸入 help 查看使用說明。"
    
    except ValueError as e:
        return str(e)
    except Exception as e:
        return f"處理命令時發生錯誤：{str(e)}" 