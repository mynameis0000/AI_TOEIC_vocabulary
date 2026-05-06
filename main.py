import os
import subprocess
import threading
import json
import requests  # Gemini API 호출용
from flask import Flask, request, jsonify

app = Flask(__name__)
mcp_process = None

# --- Gemini 설정 ---
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY") # Render 대시보드에 추가 필요
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

# --- 핵심 기능: AI에게 단어 정보 물어보기 ---
def ask_gemini(word):
    prompt = f"단어 '{word}'의 뜻과 예문을 한국어로 알려줘. JSON 형식으로만 응답해. 형식: {{\"meaning\": \"...\", \"example\": \"...\"}}"
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    response = requests.post(GEMINI_URL, json=payload)
    
    try:
        # Gemini 응답에서 JSON 텍스트만 추출
        result_text = response.json()['candidates'][0]['content']['parts'][0]['text']
        # 마크다운 코드 블록 제거 후 파싱
        clean_json = result_text.replace("```json", "").replace("```", "").strip()
        return json.loads(clean_json)
    except Exception as e:
        print(f"❌ Gemini 응답 파싱 실패: {e}")
        return None

# --- 구글 시트에서 신호를 받을 엔드포인트 ---
@app.route('/webhook', methods=['POST'])
def handle_webhook():
    data = request.json
    word = data.get('word')
    
    if not word:
        return jsonify({"error": "단어가 없습니다."}), 400

    print(f"🔍 새 단어 감지: {word}")

    # 1. Gemini에게 물어보기
    ai_res = ask_gemini(word)
    
    if ai_res:
        # 2. MCP를 통해 시트 업데이트 (update_row 도구 사용)
        call_mcp_tool("update_row", {
            "word": word,
            "meaning": ai_res['meaning'],
            "example": ai_res['example']
        })
        return jsonify({"status": "success", "word": word}), 200
    
    return jsonify({"status": "failed"}), 500

@app.route('/')
def health():
    return "AI Word Master is Online!", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)