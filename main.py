import os
import sys
import subprocess
import threading
import time
from flask import Flask
import google.generativeai as genai
from dotenv import load_dotenv

# 1. 환경 변수 로드
load_dotenv()

app = Flask(__name__)

# 필수 환경 변수 체크
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
SPREADSHEET_ID = os.environ.get("MY_SPREADSHEET_ID")

if not GEMINI_API_KEY or not SPREADSHEET_ID:
    print("❌ 에러: GEMINI_API_KEY 또는 MY_SPREADSHEET_ID가 설정되지 않았습니다.")
    sys.exit(1)

# Gemini AI 설정
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-pro')

# 2. 핵심 로직: 시트 감시 및 단어 처리
def monitor_sheets():
    print(f"🚀 [Monitor] 시트 감시를 시작합니다. 대상: {SPREADSHEET_ID}")
    
    # Render 환경에서 Bun의 실제 설치 경로를 추적합니다.
    # /opt/render/.bun/bin/bun 대신 환경 변수를 활용한 경로로 수정
    home_path = os.environ.get("HOME", "/opt/render")
    bun_path = os.path.join(home_path, ".bun", "bin", "bun")
    
    script_path = "mcp-google-sheets/index.ts"

    while True:
        try:
            print(f"📡 [MCP] {time.strftime('%Y-%m-%d %H:%M:%S')} - 단어 데이터 체크 중...")
            
            # Bun이 존재하는지 먼저 확인 (디버깅용)
            if not os.path.exists(bun_path):
                # 만약 위 경로에도 없다면 PATH에서 직접 찾기 시도
                bun_command = "bun"
            else:
                bun_command = bun_path

            subprocess.run([bun_command, "run", script_path], check=True)
            time.sleep(60) 
        except Exception as e:
            print(f"❌ [Error] 감시 중 오류 발생: {e}")
            time.sleep(10)

# 3. Render 생존 확인용 엔드포인트
@app.route('/')
def health_check():
    return "TOEIC AI Vocabulary Server is Live!", 200

# 4. 메인 실행부
if __name__ == "__main__":
    monitor_thread = threading.Thread(target=monitor_sheets, daemon=True)
    monitor_thread.start()

    port = int(os.environ.get("PORT", 10000))
    print(f"✅ [Render] 서버가 포트 {port}에서 대기 중입니다.")
    
    app.run(host='0.0.0.0', port=port)