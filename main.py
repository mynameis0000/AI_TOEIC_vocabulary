import os, json, requests, re, subprocess, threading
from flask import Flask, request, jsonify

app = Flask(__name__)
mcp_process = None

# 환경 변수 설정
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
# 가장 안정적인 v1beta 주소 체계
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"

def run_mcp_server():
    global mcp_process
    print("🚀 MCP 서버 기동 시작...")
    mcp_process = subprocess.Popen(
        ["bun", "run", "index.ts"],
        env=os.environ, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1
    )
    for line in mcp_process.stdout:
        print(f"📦 [MCP 로그]: {line.strip()}", flush=True)

threading.Thread(target=run_mcp_server, daemon=True).start()

def update_sheet(word, meaning, example):
    if not mcp_process: 
        print("❌ MCP 프로세스가 준비되지 않았습니다.")
        return
    payload = {
        "jsonrpc": "2.0", "id": 1, 
        "method": "tools/call", 
        "params": {"name": "update_row", "arguments": {"word": word, "meaning": meaning, "example": example}}
    }
    mcp_process.stdin.write(json.dumps(payload) + "\n")
    mcp_process.stdin.flush()

@app.route('/webhook', methods=['POST'])
def handle_webhook():
    try:
        data = request.json
        word = data.get('word')
        print(f"🔍 [1단계] 단어 수신: {word}")

        # AI 호출
        prompt = f"단어 '{word}'의 뜻과 예문을 한국어로 알려줘. JSON 형식으로만 답해: {{\"meaning\": \"...\", \"example\": \"...\"}}"
        ai_resp = requests.post(GEMINI_URL, json={"contents": [{"parts": [{"text": prompt}]}]})
        ai_data = ai_resp.json()

        # 🚨 AI 에러 집중 분석
        if 'candidates' not in ai_data:
            print(f"🔥 [AI 에러 상세]: {json.dumps(ai_data, indent=2, ensure_ascii=False)}")
            return jsonify({"error": "AI failure", "raw": ai_data}), 500

        # 결과 추출
        text = ai_data['candidates'][0]['content']['parts'][0]['text']
        match = re.search(r'\{.*\}', text, re.DOTALL)
        res = json.loads(match.group())

        # 시트 업데이트 호출
        update_sheet(word, res['meaning'], res['example'])
        
        print(f"✅ [최종 성공]: {word}")
        return jsonify({"status": "success"})

    except Exception as e:
        print(f"🔥 [서버 내부 에러]: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/')
def health(): return "AI Master Online", 200

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))