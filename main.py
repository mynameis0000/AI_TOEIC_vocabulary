import os, subprocess, threading, json, requests, re
from flask import Flask, request, jsonify

app = Flask(__name__)
mcp_process = None

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# 🔗 모델명을 포함한 가장 표준적인 주소 (v1beta 유지)
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
        print(f"🔍 [1단계] 단어 수신: {word}")

        # AI 호출용 데이터 설정
        payload = {
            "contents": [{
                "parts": [{"text": f"단어 '{word}'의 뜻과 예문을 한국어로 알려줘. JSON으로만 답해: {{\"meaning\": \"...\", \"example\": \"...\"}}"}]
            }]
        }
        
        # 호출 및 응답 확인
        resp = requests.post(GEMINI_URL, json=payload)
        res_data = resp.json()

        # ⚠️ 에러 발생 시 로그를 아주 상세하게 출력 (범인 검거용)
        if 'candidates' not in res_data:
            print(f"🔥 [Gemini 상세 에러]: {json.dumps(res_data, indent=2, ensure_ascii=False)}")
            return jsonify({"error": "Gemini 응답 실패", "raw": res_data}), 500

        text = res_data['candidates'][0]['content']['parts'][0]['text']
        
        # JSON 데이터 추출
        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if not json_match:
            raise ValueError("AI가 JSON 형식이 아닌 답변을 보냈습니다.")
            
        ai_res = json.loads(json_match.group())

        # MCP 도구 호출 (시트에 쓰기)
        call_mcp_tool("update_row", {
            "word": word,
            "meaning": ai_res['meaning'],
            "example": ai_res['example']
        })
        
        print(f"✅ [처리 완료] 단어: {word}")
        return jsonify({"status": "success"})

    except Exception as e:
        print(f"🔥 [서버 에러]: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/')
def health(): return "AI Word Master Online", 200

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))