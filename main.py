import os
import sys
import subprocess
import threading
import time
from flask import Flask, request, jsonify
from flask_cors import CORS
import google.generativeai as genai
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

app = Flask(__name__)
CORS(app)

# 환경 변수 설정 확인
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
SPREADSHEET_ID = os.environ.get("MY_SPREADSHEET_ID")

if not GEMINI_API_KEY or not SPREADSHEET_ID:
    print("❌ 에러: 환경 변수(GEMINI_API_KEY 또는 MY_SPREADSHEET_ID)가 설정되지 않았습니다.")
    sys.exit(1)

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-pro')

# MCP 서버 실행 함수 (별도 스레드에서 실행)
def run_mcp_server():
    print("📡 [MCP] Google Sheets MCP 서버를 시작합니다...")
    try:
        # Render 빌드 단계에서 설치된 bun 경로를 사용합니다.
        bun_path = os.path.expanduser("~/.bun/bin/bun")
        # index.ts 경로가 mcp-google-sheets 폴더 안에 있는지 확인하세요.
        subprocess.run([bun_path, "run", "mcp-google-sheets/index.ts"], check=True)
    except Exception as e:
        print(f"❌ [MCP] 서버 실행 중 에러 발생: {e}")

# 서버 시작 시 MCP 서버를 백그라운드에서 실행
mcp_thread = threading.Thread(target=run_mcp_server, daemon=True)
mcp_thread.start()

@app.route('/')
def health_check():
    return "시트 감시 서버가 정상 작동 중입니다!", 200

@app.route('/ask', methods=['POST'])
def ask_gemini():
    data = request.json
    user_input = data.get("prompt", "")
    
    if not user_input:
        return jsonify({"error": "Prompt is required"}), 400
    
    try:
        response = model.generate_content(user_input)
        return jsonify({"reply": response.text})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    # Render는 'PORT' 환경 변수를 통해 통신 포트를 지정합니다.
    # 포트가 없으면 기본값으로 10000을 사용합니다.
    port = int(os.environ.get("PORT", 10000))
    
    print(f"🚀 [Render] 서버가 포트 {port}에서 시작되었습니다.")
    print(f"📊 대상 시트 ID: {SPREADSHEET_ID}")
    
    # host='0.0.0.0' 설정은 Render 외부 연결을 위해 필수입니다.
    app.run(host='0.0.0.0', port=port)