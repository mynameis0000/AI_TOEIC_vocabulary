import os
import subprocess
import threading
from flask import Flask, request, jsonify

app = Flask(__name__)

# 1. MCP 서버를 Bun으로 실행하는 함수
def run_mcp_server():
    script_path = os.path.join(os.getcwd(), "index.ts")
    
    # subprocess를 통해 bun 실행
    # stderr=subprocess.STDOUT을 사용하여 에러 메시지도 표준 출력으로 합침
    process = subprocess.Popen(
        ["bun", "run", script_path],
        env=os.environ,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )

    print("🚀 MCP Google Sheets 서버를 실행하는 중...", flush=True)

    # 실시간으로 로그를 읽어서 출력
    for line in process.stdout:
        print(f"✅ [MCP 로그]: {line.strip()}", flush=True)

    process.wait()

# 2. 백그라운드에서 MCP 서버 시작
mcp_thread = threading.Thread(target=run_mcp_server, daemon=True)
mcp_thread.start()

@app.route('/')
def health_check():
    return "Word Master Backend is Running!", 200

# 테스트용 엔드포인트 (필요시 사용)
@app.route('/test', methods=['GET'])
def test_connection():
    pass_number = request.args.get('pass')
    if pass_number != os.environ.get('Client_PassNumber'):
        return jsonify({"error": "Unauthorized"}), 401
    return jsonify({"status": "Success", "message": "Connection is healthy"}), 200

if __name__ == "__main__":
    # Render는 PORT 환경 변수를 주므로 이를 따름
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)