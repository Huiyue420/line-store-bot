import json
import os
from typing import Dict, Optional, List, Any
from datetime import datetime
from .auth import require_admin

class MenuManager:
    def __init__(self):
        self.menu_file = "data/menu.json"
        self.menu: Dict[str, Dict[str, Any]] = {}
        self.stock_warning_threshold = 5  # 庫存警告閾值
        self.load_menu()
    
    def load_menu(self):
        """從檔案載入商品目錄"""
        try:
            if os.path.exists(self.menu_file):
                with open(self.menu_file, 'r', encoding='utf-8') as f:
                    self.menu = json.load(f)
        except Exception as e:
            print(f"載入商品目錄時發生錯誤：{e}")
            self.menu = {}
    
    def save_menu(self):
        """儲存商品目錄到檔案"""
        try:
            os.makedirs(os.path.dirname(self.menu_file), exist_ok=True)
            with open(self.menu_file, 'w', encoding='utf-8') as f:
                json.dump(self.menu, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"儲存商品目錄時發生錯誤：{e}")
    
    def get_menu(self) -> str:
        """取得商品目錄"""
        if not self.menu:
            return "目前沒有任何商品"
        
        message = "🛍️ 商品目錄：\n\n"
        for name, item in sorted(self.menu.items()):
            stock_status = self._get_stock_status_emoji(item["stock"])
            message += (
                f"📦 {name}\n"
                f"💰 價格：${item['price']}\n"
                f"📊 庫存：{stock_status} {item['stock']}\n"
            )
            if item.get("description"):
                message += f"📝 說明：{item['description']}\n"
            message += "\n"
        
        return message.strip()
    
    def get_item(self, name: str) -> Optional[Dict[str, Any]]:
        """取得商品資訊"""
        return self.menu.get(name)
    
    def add_item(self, admin_id: str, name: str, price: int, stock: int, description: str = "") -> str:
        """新增商品"""
        if name in self.menu:
            return f"商品 {name} 已存在"
        
        if price <= 0:
            return "商品價格必須大於 0"
        
        if stock < 0:
            return "商品庫存不能小於 0"
        
        self.menu[name] = {
            "price": price,
            "stock": stock,
            "description": description,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "created_by": admin_id
        }
        self.save_menu()
        
        return (
            f"✅ 商品已新增\n"
            f"📦 名稱：{name}\n"
            f"💰 價格：${price}\n"
            f"📊 庫存：{stock}\n"
            f"📝 說明：{description}"
        )
    
    def edit_item(self, admin_id: str, name: str, price: Optional[int] = None,
                 stock: Optional[int] = None, description: Optional[str] = None) -> str:
        """編輯商品"""
        if name not in self.menu:
            return f"找不到商品：{name}"
        
        item = self.menu[name]
        changes = []
        
        if price is not None:
            if price <= 0:
                return "商品價格必須大於 0"
            if price != item["price"]:
                changes.append(f"價格：${item['price']} → ${price}")
                item["price"] = price
        
        if stock is not None:
            if stock < 0:
                return "商品庫存不能小於 0"
            if stock != item["stock"]:
                changes.append(f"庫存：{item['stock']} → {stock}")
                item["stock"] = stock
        
        if description is not None and description != item["description"]:
            changes.append("說明已更新")
            item["description"] = description
        
        if not changes:
            return "沒有任何變更"
        
        item["updated_at"] = datetime.now().isoformat()
        self.save_menu()
        
        message = f"✅ 商品 {name} 已更新：\n"
        for change in changes:
            message += f"- {change}\n"
        
        # 檢查庫存是否低於警告閾值
        if stock is not None and stock <= self.stock_warning_threshold:
            message += f"\n⚠️ 警告：商品庫存低於 {self.stock_warning_threshold} 件"
        
        return message.strip()
    
    def delete_item(self, admin_id: str, name: str) -> str:
        """刪除商品"""
        if name not in self.menu:
            return f"找不到商品：{name}"
        
        item = self.menu.pop(name)
        self.save_menu()
        
        return (
            f"✅ 商品已刪除\n"
            f"📦 名稱：{name}\n"
            f"💰 價格：${item['price']}\n"
            f"📊 庫存：{item['stock']}"
        )
    
    def update_stock(self, name: str, quantity: int) -> None:
        """更新商品庫存"""
        if name not in self.menu:
            raise ValueError(f"找不到商品：{name}")
        
        item = self.menu[name]
        new_stock = item["stock"] + quantity
        
        if new_stock < 0:
            raise ValueError(f"商品 {name} 庫存不足")
        
        item["stock"] = new_stock
        item["updated_at"] = datetime.now().isoformat()
        self.save_menu()
        
        # 如果庫存低於警告閾值，返回警告訊息
        if new_stock <= self.stock_warning_threshold:
            print(f"⚠️ 警告：商品 {name} 庫存低於 {self.stock_warning_threshold} 件（剩餘：{new_stock}）")
    
    def _get_stock_status_emoji(self, stock: int) -> str:
        """取得庫存狀態表情符號"""
        if stock == 0:
            return "❌"  # 無庫存
        elif stock <= self.stock_warning_threshold:
            return "⚠️"  # 庫存警告
        else:
            return "✅"  # 庫存充足

# 建立全域實例
menu_manager = MenuManager() 