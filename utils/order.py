import json
import os
from datetime import datetime
from typing import List, Dict, Optional, Any
from .menu import menu_manager
from .auth import require_admin

class OrderManager:
    def __init__(self):
        self.orders_file = "data/orders.json"
        self.orders: Dict[str, List[Dict[str, Any]]] = {}
        self.load_orders()
    
    def load_orders(self):
        """從檔案載入訂單資料"""
        try:
            if os.path.exists(self.orders_file):
                with open(self.orders_file, 'r', encoding='utf-8') as f:
                    self.orders = json.load(f)
        except Exception as e:
            print(f"載入訂單資料時發生錯誤：{e}")
            self.orders = {}
    
    def save_orders(self):
        """儲存訂單資料到檔案"""
        try:
            os.makedirs(os.path.dirname(self.orders_file), exist_ok=True)
            with open(self.orders_file, 'w', encoding='utf-8') as f:
                json.dump(self.orders, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"儲存訂單資料時發生錯誤：{e}")
    
    def create_order(self, user_id: str, items: List[Dict[str, int]]) -> str:
        """建立新訂單"""
        try:
            # 檢查商品是否存在且庫存足夠
            for item in items:
                product = menu_manager.get_item(item["name"])
                if not product:
                    return f"商品 {item['name']} 不存在"
                if product["stock"] < item["quantity"]:
                    return f"商品 {item['name']} 庫存不足（剩餘：{product['stock']}）"
            
            # 計算訂單總金額
            total = 0
            order_items = []
            for item in items:
                product = menu_manager.get_item(item["name"])
                subtotal = product["price"] * item["quantity"]
                order_items.append({
                    "name": item["name"],
                    "quantity": item["quantity"],
                    "price": product["price"],
                    "subtotal": subtotal
                })
                total += subtotal
            
            # 建立訂單
            order = {
                "id": len(self.get_all_orders()) + 1,
                "user_id": user_id,
                "items": order_items,
                "total": total,
                "status": "pending",  # pending, confirmed, cancelled, completed
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            
            # 更新庫存
            for item in items:
                menu_manager.update_stock(item["name"], -item["quantity"])
            
            # 儲存訂單
            if user_id not in self.orders:
                self.orders[user_id] = []
            self.orders[user_id].append(order)
            self.save_orders()
            
            # 產生訂單確認訊息
            message = (
                "✅ 訂單已建立！\n\n"
                f"📦 訂單編號：{order['id']}\n"
                "🛍️ 訂購商品：\n"
            )
            for item in order_items:
                message += f"  - {item['name']} x {item['quantity']} = ${item['subtotal']}\n"
            message += f"\n💰 總金額：${total}"
            
            return message
        
        except Exception as e:
            # 發生錯誤時回復庫存
            for item in items:
                try:
                    menu_manager.update_stock(item["name"], item["quantity"])
                except:
                    pass
            return f"建立訂單時發生錯誤：{str(e)}"
    
    def get_user_orders(self, user_id: str) -> str:
        """取得使用者的訂單"""
        if user_id not in self.orders or not self.orders[user_id]:
            return "您目前沒有任何訂單"
        
        message = "📋 您的訂單記錄：\n\n"
        for order in reversed(self.orders[user_id]):
            message += (
                f"📦 訂單 #{order['id']}\n"
                f"📅 建立時間：{datetime.fromisoformat(order['created_at']).strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"🔄 狀態：{self._get_status_emoji(order['status'])} {order['status']}\n"
                "🛍️ 商品：\n"
            )
            for item in order["items"]:
                message += f"  - {item['name']} x {item['quantity']} = ${item['subtotal']}\n"
            message += f"💰 總金額：${order['total']}\n\n"
        
        return message.strip()
    
    def get_all_orders(self) -> List[Dict[str, Any]]:
        """取得所有訂單"""
        all_orders = []
        for user_orders in self.orders.values():
            all_orders.extend(user_orders)
        return sorted(all_orders, key=lambda x: x["id"])
    
    def view_orders(self, admin_id: str, status: Optional[str] = None) -> str:
        """查看所有訂單（管理員功能）"""
        all_orders = self.get_all_orders()
        if not all_orders:
            return "目前沒有任何訂單"
        
        if status:
            all_orders = [o for o in all_orders if o["status"] == status]
            if not all_orders:
                return f"目前沒有狀態為 {status} 的訂單"
        
        message = "📋 所有訂單：\n\n"
        for order in reversed(all_orders):
            message += (
                f"📦 訂單 #{order['id']}\n"
                f"👤 用戶 ID：{order['user_id']}\n"
                f"📅 建立時間：{datetime.fromisoformat(order['created_at']).strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"🔄 狀態：{self._get_status_emoji(order['status'])} {order['status']}\n"
                "🛍️ 商品：\n"
            )
            for item in order["items"]:
                message += f"  - {item['name']} x {item['quantity']} = ${item['subtotal']}\n"
            message += f"💰 總金額：${order['total']}\n\n"
        
        return message.strip()
    
    def update_order_status(self, admin_id: str, order_id: int, new_status: str) -> str:
        """更新訂單狀態（管理員功能）"""
        # 驗證狀態
        valid_statuses = ["pending", "confirmed", "cancelled", "completed"]
        if new_status not in valid_statuses:
            return f"無效的狀態。有效狀態：{', '.join(valid_statuses)}"
        
        # 尋找訂單
        order = None
        user_id = None
        for uid, orders in self.orders.items():
            for o in orders:
                if o["id"] == order_id:
                    order = o
                    user_id = uid
                    break
            if order:
                break
        
        if not order:
            return f"找不到訂單 #{order_id}"
        
        # 檢查狀態變更的合法性
        if not self._is_valid_status_transition(order["status"], new_status):
            return f"無法將訂單從 {order['status']} 狀態變更為 {new_status}"
        
        # 更新狀態
        old_status = order["status"]
        order["status"] = new_status
        order["updated_at"] = datetime.now().isoformat()
        
        # 特殊處理：如果取消訂單，恢復庫存
        if new_status == "cancelled" and old_status != "cancelled":
            for item in order["items"]:
                menu_manager.update_stock(item["name"], item["quantity"])
        # 如果從取消狀態恢復，扣除庫存
        elif old_status == "cancelled" and new_status != "cancelled":
            for item in order["items"]:
                if menu_manager.get_item(item["name"])["stock"] < item["quantity"]:
                    order["status"] = old_status  # 回復原狀態
                    return f"無法恢復訂單：商品 {item['name']} 庫存不足"
                menu_manager.update_stock(item["name"], -item["quantity"])
        
        self.save_orders()
        
        return (
            f"✅ 訂單 #{order_id} 狀態已更新\n"
            f"原狀態：{self._get_status_emoji(old_status)} {old_status}\n"
            f"新狀態：{self._get_status_emoji(new_status)} {new_status}"
        )
    
    def _is_valid_status_transition(self, old_status: str, new_status: str) -> bool:
        """檢查狀態變更是否合法"""
        # 定義合法的狀態變更
        transitions = {
            "pending": ["confirmed", "cancelled"],
            "confirmed": ["completed", "cancelled"],
            "cancelled": ["pending"],  # 允許恢復被取消的訂單
            "completed": []  # 完成的訂單不能變更狀態
        }
        return new_status in transitions.get(old_status, [])
    
    def _get_status_emoji(self, status: str) -> str:
        """取得狀態對應的表情符號"""
        return {
            "pending": "⏳",
            "confirmed": "✅",
            "cancelled": "❌",
            "completed": "🎉"
        }.get(status, "❓")

# 建立全域實例
order_manager = OrderManager() 