import os, subprocess, threading, json, requests, re
from flask import Flask, request, jsonify

app = Flask(__name__)
mcp_process = None

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
# API URL 수정 (에러 방지를 위해 v1beta 사용)
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"

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
        print(f"🔍 [수신] 단어: {word}")

        # 1. Gemini AI 호출 (프롬프트 강화)
        prompt = f"단어 '{word}'의 뜻과 예문을 한국어로 알려줘. 다른 설명 없이 오직 JSON 데이터만 출력해. 형식: {{\"meaning\": \"뜻\", \"example\": \"예문\"}}"
        resp = requests.post(GEMINI_URL, json={"contents": [{"parts": [{"text": prompt}]}]})
        res_data = resp.json()

        # 에러 핸들링
        if 'candidates' not in res_data:
            print(f"🔥 AI 응답 실패: {res_data}")
            return jsonify({"error": "AI 응답 실패"}), 500

        raw_text = res_data['candidates'][0]['content']['parts'][0]['text']
        
        # 2. JSON 데이터만 정교하게 추출 (정규식 사용)
        json_match = re.search(r'\{.*\}', raw_text, re.DOTALL)
        if json_match:
            ai_res = json.loads(json_match.group())
        else:
            raise ValueError("AI 응답에서 JSON을 찾을 수 없음")

        print(f"✨ [해석 완료] 뜻: {ai_res['meaning']}")

        # 3. MCP를 통한 시트 업데이트
        call_mcp_tool("update_row", {
            "word": word,
            "meaning": ai_res['meaning'],
            "example": ai_res['example']
        })
        
        return jsonify({"status": "success", "word": word})

    except Exception as e:
        print(f"🔥 [최종 에러 상세]: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/init-header')
def init_header():
    call_mcp_tool("initialize_headers")
    return "✅ 헤더 생성 명령 전송 완료"

@app.route('/')
def health(): return "AI Word Master Online", 200

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))