import pytest
from app import app
from utils.menu import menu_manager
from utils.order import order_manager
from utils.user_state import user_state

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_callback_endpoint(client):
    """測試 callback 端點"""
    response = client.post('/callback')
    assert response.status_code in [200, 400]  # 400 是因為沒有有效的 LINE 簽章

def test_menu_manager():
    """測試商品管理功能"""
    # 測試新增商品
    result = menu_manager.add_item("test_admin", "測試商品", 100, 10, "測試描述")
    assert "商品已新增" in result
    
    # 測試取得商品
    item = menu_manager.get_item("測試商品")
    assert item is not None
    assert item["price"] == 100
    assert item["stock"] == 10
    
    # 測試編輯商品
    result = menu_manager.edit_item("test_admin", "測試商品", price=200)
    assert "已更新" in result
    
    # 測試刪除商品
    result = menu_manager.delete_item("test_admin", "測試商品")
    assert "商品已刪除" in result

def test_order_manager():
    """測試訂單管理功能"""
    # 準備測試商品
    menu_manager.add_item("test_admin", "測試商品", 100, 10)
    
    # 測試建立訂單
    items = [{"name": "測試商品", "quantity": 2}]
    result = order_manager.create_order("test_user", items)
    assert "訂單已建立" in result
    
    # 測試查看訂單
    result = order_manager.get_user_orders("test_user")
    assert "測試商品" in result
    
    # 清理測試數據
    menu_manager.delete_item("test_admin", "測試商品")

def test_user_state():
    """測試使用者狀態管理"""
    # 測試登入嘗試次數
    user_state.increment_login_attempts("test_user")
    assert user_state.get_login_attempts("test_user") == 1
    
    # 測試重置登入嘗試
    user_state.reset_login_attempts("test_user")
    assert user_state.get_login_attempts("test_user") == 0
    
    # 測試管理員狀態
    user_state.set_admin_status("test_user", True)
    assert user_state.is_admin("test_user") is True 