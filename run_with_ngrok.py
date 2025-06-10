import os
from pyngrok import ngrok
from dotenv import load_dotenv
from app import app

# 載入環境變數
load_dotenv()

def run_with_ngrok():
    try:
        # 設定 ngrok authtoken
        ngrok_token = os.getenv('NGROK_AUTH_TOKEN')
        if not ngrok_token:
            raise ValueError("未設定 NGROK_AUTH_TOKEN 環境變數")
        
        ngrok.set_auth_token(ngrok_token)
        
        # 建立 HTTPS 通道
        http_tunnel = ngrok.connect(5000)
        public_url = http_tunnel.public_url
        print("\n=== 開發伺服器已啟動 ===")
        print(f"本地網址：http://127.0.0.1:5000")
        print(f"公開網址：{public_url}")
        print(f"\n請在 LINE Developers Console 設定以下 Webhook URL：")
        print(f"{public_url}/callback")
        print("\n提醒：")
        print("1. 每次重新啟動 ngrok，網址都會改變")
        print("2. 請確保已在 LINE Developers Console 中：")
        print("   - 更新 Webhook URL")
        print("   - 啟用 Webhook")
        print("   - 關閉自動回覆訊息")
        print("   - 關閉歡迎訊息")
        print("\n按 Ctrl+C 停止伺服器")
        
        # 啟動 Flask 應用
        app.run()
        
    except Exception as e:
        print(f"\n錯誤：{str(e)}")
        print("\n請檢查：")
        print("1. .env 檔案是否存在")
        print("2. NGROK_AUTH_TOKEN 是否正確設定")
        print("3. 是否已啟動虛擬環境")
    
    finally:
        # 清理 ngrok 通道
        try:
            ngrok.kill()
        except:
            pass

if __name__ == '__main__':
    run_with_ngrok() 