import os
import subprocess
import threading
import json
from flask import Flask, request, jsonify

app = Flask(__name__)

# MCP 프로세스를 전역 변수로 관리
mcp_process = None

def run_mcp_server():
    global mcp_process
    # 파일이 최상위에 있다고 가정 ("index.ts")
    script_path = "index.ts"
    
    mcp_process = subprocess.Popen(
        ["bun", "run", script_path],
        env=os.environ,
        stdin=subprocess.PIPE, # 명령을 보내기 위해 필요
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )

    for line in mcp_process.stdout:
        print(f"✅ [MCP 로그]: {line.strip()}", flush=True)

# 1. 백그라운드에서 MCP 서버 시작
threading.Thread(target=run_mcp_server, daemon=True).start()

# 2. MCP 서버에 명령(JSON-RPC)을 보내는 함수
def call_mcp_tool(name, arguments={}):
    if not mcp_process or mcp_process.poll() is not None:
        return {"error": "MCP 서버가 실행 중이 아닙니다."}

    # MCP 표준 프로토콜 양식
    request_data = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": name,
            "arguments": arguments
        }
    }
    
    # 서버에 명령 전달
    mcp_process.stdin.write(json.dumps(request_data) + "\n")
    mcp_process.stdin.flush()
    return {"status": "sent"}

@app.route('/')
def health_check():
    return "Word Master is Online!", 200

# 3. 헤더 초기화 버튼 (브라우저에서 이 주소를 입력하면 실행됨)
@app.route('/init-header')
def init_header():
    result = call_mcp_tool("initialize_headers")
    return jsonify({"message": "헤더 생성 명령을 보냈습니다. 시트를 확인하세요!", "result": result})

# 4. 단어 추가 테스트 (나중에 기능 붙일 때 사용)
@app.route('/add-test')
def add_test():
    result = call_mcp_tool("append_word", {
        "word": "Persistence",
        "meaning": "끈기, 고집",
        "example": "Success requires persistence."
    })
    return jsonify({"message": "단어 추가 명령을 보냈습니다.", "result": result})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)