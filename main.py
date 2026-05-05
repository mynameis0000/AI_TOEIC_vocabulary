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
            
            # [핵심 수정] Bun 경로를 찾는 3단계 전략
            # 1. 시스템 PATH에서 찾기 -> 2. Render 표준 경로 직접 지정 -> 3. 기본값 'bun'
            bun_command = shutil.which("bun")
            if not bun_command:
                render_bun_path = "/opt/render/.bun/bin/bun"
                if os.path.exists(render_bun_path):
                    bun_command = render_bun_path
                else:
                    bun_command = "bun"

            # TypeScript 로직 실행
            # env=os.environ을 통해 파이썬의 모든 환경 변수를 자식 프로세스에 전달합니다.
            result = subprocess.run(
                [bun_command, "run", script_path],
                env=os.environ,  # <--- 이 부분이 Render의 환경 변수를 Bun에게 넘겨주는 핵심입니다!
                capture_output=True,
                text=True
            )
            
            # 실행 결과 및 에러 출력 (디버깅 필수)
            if result.stderr:
                print(f"❌ [MCP 에러 로그]: {result.stderr.strip()}")
            if result.stdout:
                print(f"✅ [MCP 출력]: {result.stdout.strip()}")
            
            # 1분(60초)마다 한 번씩 확인
            time.sleep(60) 
        except Exception as e:
            print(f"⚠️ 시스템 오류 발생: {e}")
            print(f"🔍 현재 시도한 bun 경로: {bun_command if 'bun_command' in locals() else 'None'}")
            time.sleep(20)

# 3. Render 생존 확인용 엔드포인트
@app.route('/')
def health_check():
    # Render가 이 경로로 접속하여 200 OK를 받으면 'Live' 상태를 유지합니다.
    return "TOEIC AI Vocabulary Server is Live and Running!", 200

# 4. 서버 실행
if __name__ == "__main__":
    # 시트 감시 로직을 별도 스레드에서 실행
    monitor_thread = threading.Thread(target=monitor_sheets, daemon=True)
    monitor_thread.start()

    # Render 포트 설정 (기본값 10000)
    port = int(os.environ.get("PORT", 10000))
    print(f"✅ [Render] 서버가 포트 {port}에서 대기 중입니다.")
    
    # host='0.0.0.0'은 외부 접속 허용을 위해 필수입니다.
    app.run(host='0.0.0.0', port=port)