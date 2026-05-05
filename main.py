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

# Render Settings에서 설정한 BUN_PATH를 가져옵니다. 없을 경우 기본 경로 시도.
BUN_EXECUTABLE = os.environ.get("BUN_PATH", "/opt/render/.bun/bin/bun")

if not GEMINI_API_KEY or not SPREADSHEET_ID:
    print("❌ 에러: GEMINI_API_KEY 또는 MY_SPREADSHEET_ID가 설정되지 않았습니다.")
    sys.exit(1)

# Gemini AI 설정
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-pro')

# 2. 핵심 로직: 시트 감시 및 단어 처리 (무한 루프)
def monitor_sheets():
    print(f"🚀 [Monitor] 시트 감시를 시작합니다. 대상: {SPREADSHEET_ID}")
    script_path = "mcp-google-sheets/index.ts"

    while True:
        try:
            print(f"📡 [MCP] {time.strftime('%Y-%m-%d %H:%M:%S')} - 단어 데이터 체크 중...")
            
            # Bun 실행 파일이 존재하는지 확인 후 실행
            if os.path.exists(BUN_EXECUTABLE):
                cmd = BUN_EXECUTABLE
            else:
                # 경로에 없다면 시스템 PATH에서 'bun'을 찾도록 시도
                cmd = "bun"

            # TypeScript 로직 실행
            result = subprocess.run(
                [cmd, "run", script_path], 
                check=True, 
                capture_output=True, 
                text=True
            )
            
            if result.stdout:
                print(f"✅ [MCP 결과]: {result.stdout.strip()}")
            
            # 1분(60초)마다 한 번씩 시트의 변화를 확인
            time.sleep(60) 
        except Exception as e:
            print(f"❌ [Error] 감시 중 오류 발생: {e}")
            time.sleep(15) # 에러 발생 시 조금 더 대기 후 재시도

# 3. Render 생존 확인용 엔드포인트
@app.route('/')
def health_check():
    return "TOEIC AI Vocabulary Server is Live!", 200

# 4. 메인 실행부
if __name__ == "__main__":
    # 시트 감시 로직을 백그라운드 스레드에서 실행
    monitor_thread = threading.Thread(target=monitor_sheets, daemon=True)
    monitor_thread.start()

    # Render 포트 설정 (기본값 10000)
    port = int(os.environ.get("PORT", 10000))
    
    print(f"✅ [Render] 서버가 포트 {port}에서 대기 중입니다.")

    # host='0.0.0.0' 설정은 외부 접속 및 Render 서비스 유지를 위해 필수입니다.
    app.run(host='0.0.0.0', port=port)