import os
import requests
import subprocess
from flask import Flask, request, jsonify

app = Flask(__name__)

# --- [환경 변수 설정] ---
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
# 모델 경로를 가장 확실한 v1 표준으로 설정합니다.
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"

# --- [MCP 서버 실행] ---
# package.json이 있는 위치에서 bun으로 index.ts를 실행합니다.
mcp_process = subprocess.Popen(
    ["bun", "run", "index.ts"],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True
)

def call_mcp_tool(word, meaning, example):
    """
    MCP 서버에 표준 입력을 통해 데이터를 전달하여 시트를 업데이트합니다.
    """
    import json
    # MCP 프로토콜에 맞춘 요청 메시지 (ID는 랜덤하게 부여)
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": "update_row",
            "arguments": {
                "word": word,
                "meaning": meaning,
                "example": example
            }
        }
    }
    
    # MCP 서버에 명령 전달
    input_str = json.dumps(payload) + "\n"
    mcp_process.stdin.write(input_str)
    mcp_process.stdin.flush()
    
    # 응답 읽기
    response = mcp_process.stdout.readline()
    print(f"📦 [MCP 응답]: {response}")
    return response

@app.route("/webhook", methods=["POST"])
def handle_webhook():
    data = request.json
    word = data.get("word")
    
    if not word:
        return jsonify({"error": "No word provided"}), 400

    print(f"🔍 [1단계] 단어 수신: {word}")

    # --- [2단계: Gemini AI 호출] ---
    prompt = f"단어 '{word}'의 뜻과 예문을 '뜻|예문' 형식으로 짧게 답해줘. 예문엔 해석 포함."
    headers = {"Content-Type": "application/json"}
    
    try:
        ai_resp = requests.post(
            GEMINI_URL, 
            json={"contents": [{"parts": [{"text": prompt}]}]},
            headers=headers
        )
        ai_data = ai_resp.json()
        
        # 상세 에러 디버깅을 위해 로그 출력
        if ai_resp.status_code != 200:
            print(f"🔥 [AI 에러 상세]: {ai_data}")
            return jsonify({"error": "AI failure", "raw": ai_data}), 500

        # 결과 추출
        ai_text = ai_data['candidates'][0]['content']['parts'][0]['text'].strip()
        meaning, example = ai_text.split('|')

        # --- [3단계: MCP 도구 호출 (시트 업데이트)] ---
        mcp_resp = call_mcp_tool(word.strip(), meaning.strip(), example.strip())
        
        print(f"✅ [최종 성공]: {word}")
        return jsonify({"status": "success", "data": ai_text})

    except Exception as e:
        print(f"🔥 [서버 내부 에러]: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    # Render는 PORT 환경변수를 사용합니다.
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)