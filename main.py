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

# 필수 설정값 확인
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
SPREADSHEET_ID = os.environ.get("MY_SPREADSHEET_ID")

# Render 설정(Environment Variables)에서 추가한 BUN_PATH를 가져옵니다.
# 설정하지 않았다면 Render의 기본 설치 경로를 시도합니다.
BUN_EXECUTABLE = os.environ.get("BUN_PATH", "/opt/render/.bun/bin/bun")

if not GEMINI_API_KEY or not SPREADSHEET_ID:
    print("❌ 에러: GEMINI_API_KEY 또는 MY_SPREADSHEET_ID 환경 변수가 없습니다.")
    sys.exit(1)

# Gemini AI 설정
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-pro')

# 2. 핵심 로직: 시트 감시 및 단어 처리 (Infinite Loop)
def monitor_sheets():
    print(f"🚀 [Monitor] 시트 감시 시작. 대상: {SPREADSHEET_ID}")
    # index.ts 파일이 mcp-google-sheets 폴더 안에 있는지 확인하세요.
    script_path = "mcp-google-sheets/index.ts"

    while True:
        try:
            print(f"📡 [MCP] {time.strftime('%H:%M:%S')} - 단어 데이터 체크 중...")
            
            # Bun을 사용하여 TypeScript 로직 실행
            # capture_output을 사용하여 로그를 파이썬 콘솔에 출력합니다.
            result = subprocess.run(
                [BUN_EXECUTABLE, "run", script_path],
                check=True,
                capture_output=True,
                text=True
            )
            
            if result.stdout:
                print(f"✅ [MCP 결과]: {result.stdout.strip()}")
            
            # 1분마다 한 번씩 확인
            time.sleep(60) 
        except subprocess.CalledProcessError as e:
            print(f"❌ [MCP 실행 에러]: {e.stderr}")
            time.sleep(20)
        except Exception as e:
            print(f"❌ [시스템 에러]: {e}")
            # 경로가 잘못되었는지 다시 한번 출력
            if not os.path.exists(BUN_EXECUTABLE):
                print(f"⚠️ 경고: '{BUN_EXECUTABLE}' 경로에 bun 파일이 없습니다. Render 설정을 확인하세요.")
            time.sleep(20)

# 3. Render 생존 확인용 엔드포인트
@app.route('/')
def health_check():
    # Render가 이 경로로 접속하여 200 OK를 받으면 'Live' 상태를 유지합니다.
    return "TOEIC AI Vocabulary Server is Live and Running!", 200

# 4. 서버 실행
if __name__ == "__main__":
    # 시트 감시 로직을 별도 스레드에서 실행 (서버 중단 방지)
    monitor_thread = threading.Thread(target=monitor_sheets, daemon=True)
    monitor_thread.start()

    # Render에서 지정한 포트(기본 10000)로 실행
    port = int(os.environ.get("PORT", 10000))
    print(f"✅ [Render] 서버가 포트 {port}에서 대기 중입니다.")
    
    # host='0.0.0.0'은 외부 접속 허용을 위해 필수입니다.
    app.run(host='0.0.0.0', port=port)