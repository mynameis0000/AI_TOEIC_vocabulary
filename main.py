import os, subprocess, threading, json, requests, re
from flask import Flask, request, jsonify

app = Flask(__name__)
mcp_process = None

# 환경 변수에서 API 키 가져오기
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# 🔗 가장 안정적인 주소 형식으로 수정
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
def run_mcp_server():
    global mcp_process
    mcp_process = subprocess.Popen(
        ["bun", "run", "index.ts"],
        env=os.environ, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1
    )
    for line in mcp_process.stdout:
        print(f"✅ [MCP 로그]: {line.strip()}", flush=True)

threading.Thread(target=run_mcp_server, daemon=True).start()

def call_mcp_tool(name, args={}):
    if not mcp_process: return {"error": "MCP 연결 안됨"}
    payload = {"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": name, "arguments": args}}
    mcp_process.stdin.write(json.dumps(payload) + "\n")
    mcp_process.stdin.flush()
    return {"status": "sent"}

@app.route('/webhook', methods=['POST'])
def handle_webhook():
    try:
        data = request.json
        word = data.get('word')
        print(f"🔍 단어 수신: {word}")

        # AI 호출
        prompt = f"단어 '{word}'의 뜻과 예문을 한국어로 알려줘. JSON으로만 답해: {{\"meaning\": \"뜻\", \"example\": \"예문\"}}"
        resp = requests.post(GEMINI_URL, json={"contents": [{"parts": [{"text": prompt}]}]})
        res_data = resp.json()

        # 응답 구조가 평소와 다를 경우를 대비한 안전 장치
        if 'candidates' not in res_data:
            print(f"🔥 Gemini 에러 응답: {res_data}")
            return jsonify(res_data), 500

        text = res_data['candidates'][0]['content']['parts'][0]['text']
        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        ai_res = json.loads(json_match.group())

        # MCP 업데이트
        call_mcp_tool("update_row", {"word": word, "meaning": ai_res['meaning'], "example": ai_res['example']})
        
        print(f"✅ '{word}' 업데이트 성공")
        return jsonify({"status": "success"})

    except Exception as e:
        print(f"🔥 에러 발생: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/')
def health(): return "Online", 200

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))