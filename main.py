import os, json, requests, re, subprocess, threading
from flask import Flask, request, jsonify

app = Flask(__name__)
mcp_process = None

# 환경 변수 및 API 설정
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"

# 1. MCP 서버(index.ts) 실행 함수
def run_mcp_server():
    global mcp_process
    print("🚀 MCP 서버 기동 시작...")
    mcp_process = subprocess.Popen(
        ["bun", "run", "index.ts"],
        env=os.environ, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1
    )
    for line in mcp_process.stdout:
        print(f"📦 [MCP]: {line.strip()}", flush=True)

# 백그라운드에서 MCP 실행
threading.Thread(target=run_mcp_server, daemon=True).start()

# 2. 시트 업데이트 도구 호출
def update_sheet(word, meaning, example):
    if not mcp_process: return
    payload = {
        "jsonrpc": "2.0", "id": 1, 
        "method": "tools/call", 
        "params": {"name": "update_row", "arguments": {"word": word, "meaning": meaning, "example": example}}
    }
    mcp_process.stdin.write(json.dumps(payload) + "\n")
    mcp_process.stdin.flush()

# 3. 핵심 웹훅 (Apps Script에서 신호를 받는 통로)
@app.route('/webhook', methods=['POST'])
def handle_webhook():
    try:
        data = request.json
        word = data.get('word')
        if not word: return jsonify({"error": "No word"}), 400
        
        print(f"🔍 단어 수신: {word}")

        # AI에게 뜻 요청
        prompt = f"단어 '{word}'의 뜻과 예문을 한국어로 알려줘. JSON 형식: {{\"meaning\": \"뜻\", \"example\": \"예문\"}}"
        ai_resp = requests.post(GEMINI_URL, json={"contents": [{"parts": [{"text": prompt}]}]})
        ai_data = ai_resp.json()

        # AI 응답 체크
        if 'candidates' not in ai_data:
            print(f"🔥 AI 에러: {ai_data}")
            return jsonify({"error": "AI failure", "details": ai_data}), 500

        # 결과 파싱 및 시트 전송
        text = ai_data['candidates'][0]['content']['parts'][0]['text']
        match = re.search(r'\{.*\}', text, re.DOTALL)
        res = json.loads(match.group())

        update_sheet(word, res['meaning'], res['example'])
        
        print(f"✅ 완료: {word}")
        return jsonify({"status": "success"})

    except Exception as e:
        print(f"🔥 에러: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/')
def health(): return "Server is running", 200

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))