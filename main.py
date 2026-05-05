import os
import subprocess
import threading
from flask import Flask, jsonify
from dotenv import load_dotenv

# 1. 환경 변수 로드
load_dotenv()

app = Flask(__name__)

# 환경 변수 가져오기 (Render 설정값)
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
SPREADSHEET_ID = os.environ.get("MY_SPREADSHEET_ID")
CLIENT_PASS_NUMBER = os.environ.get("Client_PassNumber") # 추가된 변수

def run_mcp_server():
    """
    Bun을 사용하여 MCP 구글 시트 서버(index.ts)를 실행합니다.
    Docker 환경에서는 bun이 /usr/local/bin/bun에 위치합니다.
    """
    print("🚀 MCP Google Sheets 서버를 실행하는 중...")
    
    # Dockerfile 설정에 따른 index.ts 경로
    script_path = os.path.join(os.getcwd(), "mcp-google-sheets", "index.ts")
    
    try:
        # subprocess 실행 시 env=os.environ을 통해 모든 환경 변수를 자식 프로세스에 전달
        process = subprocess.Popen(
            ["bun", "run", script_path],
            env=os.environ,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # 실시간 로그 출력
        for line in process.stdout:
            print(f"✅ [MCP 출력]: {line.strip()}")
        for line in process.stderr:
            print(f"❌ [MCP 에러]: {line.strip()}")
            
    except Exception as e:
        print(f"🚨 MCP 서버 실행 중 오류 발생: {e}")

@app.route('/')
def health_check():
    # Client_PassNumber 존재 여부를 간단히 확인 (보안상 값은 노출 안 함)
    status = "정상" if CLIENT_PASS_NUMBER else "누락(환경변수 확인 필요)"
    return jsonify({
        "message": "AI TOEIC Vocabulary Server is Running",
        "mcp_status": "Starting...",
        "auth_status": status
    })

if __name__ == "__main__":
    # 1. 필수 환경 변수 체크
    if not all([GEMINI_API_KEY, SPREADSHEET_ID, CLIENT_PASS_NUMBER]):
        print("⚠️ 경고: 필수 환경 변수가 누락되었습니다.")
        print(f"- GEMINI_API_KEY: {'설정됨' if GEMINI_API_KEY else '미설정'}")
        print(f"- SPREADSHEET_ID: {'설정됨' if SPREADSHEET_ID else '미설정'}")
        print(f"- Client_PassNumber: {'설정됨' if CLIENT_PASS_NUMBER else '미설정'}")

    # 2. MCP 서버를 별도 스레드에서 실행
    mcp_thread = threading.Thread(target=run_mcp_server, daemon=True)
    mcp_thread.start()

    # 3. Flask 서버 실행 (Render의 기본 포트는 10000)
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)