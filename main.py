import os
import subprocess
import threading
import json
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)
mcp_process = None

# --- 1. 환경 변수 체크 ---
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"

def run_mcp_server():
    global mcp_process
    script_path = "index.ts"
    mcp_process = subprocess.Popen(
        ["bun", "run", script_path],
        env=os.environ,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )
    for line in mcp_process.stdout:
        print(f"✅ [MCP 로그]: {line.strip()}", flush=True)

threading.Thread(target=run_mcp_server, daemon=True).start()

def call_mcp_tool(name, arguments={}):
    if not mcp_process or mcp_process.poll() is not None:
        return {"error": "MCP 서버 실행 중 아님"}
    request_data = {"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": name, "arguments": arguments}}
    mcp_process.stdin.write(json.dumps(request_data) + "\n")
    mcp_process.stdin.flush()
    return {"status": "sent"}

# --- 2. 경로 설정 (중요!) ---

# [테스트용] 헤더 생성 경로
@app.route('/init-header')
def init_header():
    call_mcp_tool("initialize_headers")
    return "✅ 헤더 생성 명령을 보냈습니다. 시트를 확인하세요."

# [핵심] 구글 시트 자동 완성 경로
# main.py의 handle_webhook 부분을 아래로 교체하거나 전체를 업데이트하세요
@app.route('/webhook', methods=['POST'])
def handle_webhook():
    try:
        print("📢 Webhook 요청 수신됨!")
        data = request.json
        word = data.get('word')
        
        if not word:
            return jsonify({"error": "단어 없음"}), 400

        # Gemini 호출
        print(f"🤖 Gemini에게 '{word}' 물어보는 중...")
        prompt = f"단어 '{word}'의 뜻과 예문을 한국어로 알려줘. 반드시 아래 JSON 형식으로만 응답해. 다른 말은 하지마. 형식: {{\"meaning\": \"...\", \"example\": \"...\"}}"
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        response = requests.post(GEMINI_URL, json=payload)
        
        # API 응답 확인
        res_json = response.json()
        if 'candidates' not in res_json:
            print(f"❌ Gemini 응답 오류: {res_json}")
            return jsonify({"error": "Gemini 응답 실패"}), 500

        result_text = res_json['candidates'][0]['content']['parts'][0]['text']
        # JSON 추출 로직 강화
        clean_json = result_text.replace("```json", "").replace("```", "").strip()
        ai_res = json.loads(clean_json)
        
        print(f"✅ AI 해석 완료: {ai_res['meaning']}")

        # MCP 업데이트 명령
        call_mcp_tool("update_row", {
            "word": word,
            "meaning": ai_res['meaning'],
            "example": ai_res['example']
        })
        
        return jsonify({"status": "success", "word": word})

    except Exception as e:
        print(f"🔥 서버 내부 에러 발생: {str(e)}") # 어떤 에러인지 로그에 찍힙니다
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/')
def health():
    return "AI Word Master is Online!", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)