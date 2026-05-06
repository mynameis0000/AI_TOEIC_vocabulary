import os, subprocess, threading, json, requests, re
from flask import Flask, request, jsonify

app = Flask(__name__)
mcp_process = None

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
# API URL 수정 (에러 방지를 위해 v1beta 사용)
GEMINI_URL = f"[https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key=](https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key=){GEMINI_API_KEY}"
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
    if not mcp_process: return {"error": "MCP 서버 연결 안됨"}
    payload = {"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": name, "arguments": args}}
    mcp_process.stdin.write(json.dumps(payload) + "\n")
    mcp_process.stdin.flush()
    return {"status": "sent"}

@app.route('/webhook', methods=['POST'])
def handle_webhook():
    try:
        data = request.json
        word = data.get('word')
        print(f"🔍 [1단계] 단어 수신: {word}")

        # Gemini 호출
        resp = requests.post(GEMINI_URL, json={"contents": [{"parts": [{"text": f"단어 '{word}'의 뜻과 예문을 한국어로 알려줘. JSON으로만 답해: {{\"meaning\": \"...\", \"example\": \"...\"}}"}]}]})
        res_data = resp.json()
        
        # ⚠️ 여기가 핵심: AI의 전체 응답을 로그에 찍습니다.
        print(f"📦 [2단계] AI 응답 전체: {json.dumps(res_data, ensure_ascii=False)}")

        if 'candidates' not in res_data:
            print("🔥 Gemini API 키 문제 혹은 할당량 초과입니다.")
            return jsonify(res_data), 500

        text = res_data['candidates'][0]['content']['parts'][0]['text']
        print(f"📝 [3단계] 추출된 텍스트: {text}")

        # JSON 추출
        clean_json = re.search(r'\{.*\}', text, re.DOTALL).group()
        ai_res = json.loads(clean_json)

        # MCP 호출
        call_mcp_tool("update_row", {"word": word, "meaning": ai_res['meaning'], "example": ai_res['example']})
        
        print(f"✅ [4단계] 처리 완료")
        return jsonify({"status": "ok"})

    except Exception as e:
        print(f"🔥 [최종 에러 발생]: {str(e)}")
        # 에러가 나면 AI가 준 생데이터를 다시 한번 찍습니다.
        return jsonify({"error": str(e)}), 500

@app.route('/init-header')
def init_header():
    call_mcp_tool("initialize_headers")
    return "✅ 헤더 생성 명령 전송 완료"

@app.route('/')
def health(): return "AI Word Master Online", 200

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))