import os
import sys
import subprocess
import threading
import time
import shutil
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

# 2. 핵심 로직: 시트 감시 및 단어 처리 (무한 루프)
def monitor_sheets():
    print(f"🚀 [Monitor] 시트 감시 시작 (ID: {SPREADSHEET_ID[:4]}...)")
    script_path = "mcp-google-sheets/index.ts"

    while True:
        try:
            print(f"📡 [MCP] {time.strftime('%Y-%m-%d %H:%M:%S')} - 체크 중...")
            
            # 시스템 PATH에서 bun 실행 파일의 위치를 자동으로 찾습니다.
            # 찾지 못할 경우 기본값 'bun'을 사용합니다.
            bun_command = shutil.which("bun") or "bun"

            # TypeScript 로직 실행
            # env=os.environ을 통해 파이썬의 환경 변수를 자식 프로세스에도 전달합니다.
            result = subprocess.run(
                [bun_command, "run", script_path],
                env=os.environ,
                capture_output=True,
                text=True
            )
            
            # 실행 결과 출력 (디버깅용)
            if result.stderr:
                print(f"❌ [MCP 로그]: {result.stderr.strip()}")
            if result.stdout:
                print(f"✅ [MCP 출력]: {result.stdout.strip()}")
            
            # 1분(60초)마다 한 번씩 확인
            time.sleep(60) 
        except Exception as e:
            print(f"⚠️ 시스템 오류 발생: {e}")
            time.sleep(20) # 에러 시 대기 후 재시도

# 3. Render 생존 확인용 엔드포인트
@app.route('/')
def health_check():
    # Render가 이 경로로 접속하여 200 OK를 받으면 'Live' 상태를 유지합니다.
    return "TOEIC AI Vocabulary Server is Live and Running!", 200

# 4. 서버 실행
if __name__ == "__main__":
    # 시트 감시 로직을 별도 스레드에서 실행하여 Flask 서버와 병렬로 작동시킵니다.
    monitor_thread = threading.Thread(target=monitor_sheets, daemon=True)
    monitor_thread.start()

    # Render에서 할당한 포트(기본 10000)를 사용합니다.
    port = int(os.environ.get("PORT", 10000))
    print(f"✅ [Render] 서버가 포트 {port}에서 대기 중입니다.")
    
    # host='0.0.0.0'은 외부 접속 허용을 위해 필수입니다.
    app.run(host='0.0.0.0', port=port)