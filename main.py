import asyncio
import os
import json
import threading
from flask import Flask
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import google.generativeai as genai
from dotenv import load_dotenv

# 1. 환경 변수 로드
load_dotenv()

SPREADSHEET_ID = os.getenv("MY_SPREADSHEET_ID")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
SHEETS_CREDS_JSON = os.getenv("GOOGLE_SHEETS_CREDENTIALS")

# 2. Render 상태 확인용 Flask 웹 서버 설정
app = Flask(__name__)

@app.route('/')
def health_check():
    return "ALIVE", 200

def run_flask():
    # Render가 할당하는 PORT 환경 변수를 사용 (없으면 10000번)
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# 3. Gemini API 설정
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('models/gemini-flash-latest')

async def get_gemini_info(word):
    prompt = f"단어 '{word}'의 뜻, 품사, 예문을 '뜻|품사|예문' 형식으로만 출력해줘."
    try:
        response = model.generate_content(prompt)
        if not response or not response.text:
            return ["응답 없음", "없음", "Gemini 답변 생성 실패"]
        
        data = response.text.strip().split('|')
        if len(data) >= 3:
            return [data[0].strip(), data[1].strip(), data[2].strip()]
        else:
            return ["형식 오류", "오류", f"원본: {response.text[:20]}"]
    except Exception as e:
        print(f"❌ Gemini 에러: {e}")
        return ["연결 에러", "에러", str(e)[:20]]

async def run_mcp_server():
    if not SHEETS_CREDS_JSON:
        print("❌ 에러: GOOGLE_SHEETS_CREDENTIALS 환경 변수가 없습니다.")
        return

    # MCP 서버 경로 (사용자님의 폴더 구조에 맞게 수정됨)
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    server_script_path = os.path.join(BASE_DIR, "mcp-google-sheets", "index.ts")

    server_params = StdioServerParameters(
        command="bun",
        args=["run", "--silent", server_script_path],
        env={
            "GOOGLE_SHEETS_CREDENTIALS": SHEETS_CREDS_JSON, 
            **os.environ
        }
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            print(f"🚀 [Render] 시트 감시 시작 (ID: {SPREADSHEET_ID[:10]}...)")

            while True:
                try:
                    ui_data = await session.call_tool("read_sheet", arguments={
                        "spreadsheetId": SPREADSHEET_ID,
                        "range": "시트1!A2:G100"
                    })
                    
                    rows = json.loads(ui_data.content[0].text)

                    for i, row in enumerate(rows):
                        word = row[0] if len(row) > 0 else ""
                        meaning = row[1] if len(row) > 1 else ""

                        if word and not meaning:
                            actual_row = i + 2 
                            print(f"🔍 {actual_row}행 '{word}' 처리 중...")

                            ai_result = await get_gemini_info(word)

                            await session.call_tool("update_sheet", arguments={
                                "spreadsheetId": SPREADSHEET_ID,
                                "range": f"시트1!B{actual_row}:G{actual_row}",
                                "values": [[
                                    ai_result[0], 
                                    ai_result[1], 
                                    ai_result[2], 
                                    "", "", 
                                    f"✅ 완료"
                                ]]
                            })
                    
                    # 10초마다 시트 확인 (API 할당량 준수)
                    await asyncio.sleep(10)

                except Exception as e:
                    print(f"⚠️ 루프 에러: {e}")
                    await asyncio.sleep(20)

if __name__ == "__main__":
    # 1. Flask 서버를 백그라운드 쓰레드에서 실행
    threading.Thread(target=run_flask, daemon=True).start()
    
    # 2. 메인 비동기 루프 실행
    asyncio.run(run_mcp_server())