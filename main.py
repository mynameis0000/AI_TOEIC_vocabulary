import os
import sys
import subprocess
import threading
import time
from flask import Flask
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)

# 환경 변수 확인 (로그에 시트 ID 앞 4자리만 출력)
BUN_EXECUTABLE = os.environ.get("BUN_PATH", "/opt/render/.bun/bin/bun")
SHEET_ID = os.environ.get("MY_SPREADSHEET_ID", "")

def monitor_sheets():
    print(f"🚀 [Monitor] 시트 감시 시작 (ID: {SHEET_ID[:4]}...)")
    script_path = "mcp-google-sheets/index.ts"

    while True:
        try:
            # shell=True를 사용해 환경 변수가 index.ts에 더 잘 전달되도록 함
            result = subprocess.run(
                [BUN_EXECUTABLE, "run", script_path],
                env=os.environ, # 파이썬의 모든 환경 변수를 Bun에게 전달
                capture_output=True,
                text=True
            )
            
            if result.stderr:
                print(f"❌ [MCP 에러 로그]: {result.stderr}")
            if result.stdout:
                print(f"✅ [MCP 출력]: {result.stdout}")
            
            time.sleep(60) 
        except Exception as e:
            print(f"⚠️ 시스템 오류: {e}")
            time.sleep(20)

@app.route('/')
def health_check():
    return "Server Live", 200

if __name__ == "__main__":
    threading.Thread(target=monitor_sheets, daemon=True).start()
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))