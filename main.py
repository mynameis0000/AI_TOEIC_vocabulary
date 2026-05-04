import os
import sys
import subprocess
import threading
import time
from flask import Flask
import google.generativeai as genai
from dotenv import load_dotenv

# 1. 환경 변수 로드 (.env 파일 및 Render 설정값 읽기)
load_dotenv()

app = Flask(__name__)

# 필수 환경 변수 체크
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
SPREADSHEET_ID = os.environ.get("MY_SPREADSHEET_ID")

if not GEMINI_API_KEY or not SPREADSHEET_ID:
    print("❌ 에러: 환경 변수(GEMINI_API_KEY 또는 MY_SPREADSHEET_ID)가 설정되지 않았습니다.")
    sys.exit(1)

# Gemini AI 설정
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-pro')

# 2. 핵심 로직: 시트 감시 및 단어 처리 (Infinite Loop)
def monitor_sheets():
    print(f"🚀 [Monitor] 시트 감시를 시작합니다. 대상: {SPREADSHEET_ID}")
    
    # Render 빌드 단계에서 설치된 bun의 절대 경로
    bun_path = os.path.expanduser("~/.bun/bin/bun")
    # MCP 도구(TypeScript)가 위치한 경로
    script_path = "mcp-google-sheets/index.ts"

    while True:
        try:
            # MCP 서버를 실행하여 시트 데이터를 확인하고 AI 퀴즈를 생성합니다.
            # 이 부분은 사용자님이 이전에 개발하시던 TOEIC 단어 앱의 핵심 기능입니다.
            print(f"📡 [MCP] {time.strftime('%Y-%m-%d %H:%M:%S')} - 단어 데이터 체크 중...")
            
            # subprocess를 사용하여 TypeScript 로직을 주기적으로 실행
            subprocess.run([bun_path, "run", script_path], check=True)
            
            # 1분(60초)마다 한 번씩 시트의 변화를 확인합니다.
            time.sleep(60) 
        except Exception as e:
            print(f"❌ [Error] 감시 중 오류 발생: {e}")
            # 에러 발생 시 잠시 대기 후 다시 시도
            time.sleep(10)

# 3. Render 생존 확인용 엔드포인트 (Port Binding 해결)
@app.route('/')
def health_check():
    # Render 서버가 이 주소로 접속했을 때 200 OK를 응답해야 서버가 꺼지지 않습니다.
    return "TOEIC AI Vocabulary Server is Live!", 200

# 4. 메인 실행부
if __name__ == "__main__":
    # 시트 감시 로직을 메인 서버와 별개로(백그라운드) 실행합니다.
    monitor_thread = threading.Thread(target=monitor_sheets, daemon=True)
    monitor_thread.start()

    # Render에서 할당해주는 포트 번호를 읽어옵니다. (기본값 10000)
    port = int(os.environ.get("PORT", 10000))
    
    print(f"✅ [Render] 서버가 포트 {port}에서 대기 중입니다.")
    
    # host='0.0.0.0'으로 설정해야 Render의 외부 접속을 허용할 수 있습니다.
    app.run(host='0.0.0.0', port=port)