import asyncio
import os
import json
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import google.generativeai as genai
from dotenv import load_dotenv

# 1. 환경 변수 로드 (.env 파일이 없어도 시스템 환경 변수를 읽어옵니다)
load_dotenv()

# Render 대시보드의 Environment Variables에 입력할 변수들입니다.
SPREADSHEET_ID = os.getenv("MY_SPREADSHEET_ID")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
# 파일 대신 환경 변수 문자열에서 JSON 데이터를 직접 가져옵니다.
SHEETS_CREDS_JSON = os.getenv("GOOGLE_SHEETS_CREDENTIALS")

# 2. Gemini 설정
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('models/gemini-flash-latest')

async def get_gemini_info(word):
    """Gemini API를 사용하여 단어 정보를 가져옵니다."""
    prompt = f"단어 '{word}'의 뜻, 품사, 예문을 '뜻|품사|예문' 형식으로만 출력해줘."
    try:
        response = model.generate_content(prompt)
        if not response or not response.text:
            return ["응답 없음", "없음", "Gemini가 답변을 생성하지 못했습니다."]
        
        data = response.text.strip().split('|')
        if len(data) >= 3:
            return [data[0].strip(), data[1].strip(), data[2].strip()]
        else:
            return ["형식 오류", "오류", f"원본 답변: {response.text[:20]}"]
    except Exception as e:
        print(f"❌ Gemini 호출 에러: {e}")
        return ["연결 에러", "에러", str(e)[:20]]

async def run_mcp_server():
    # 3. 보안 체크: 환경 변수가 비어있는지 확인
    if not SHEETS_CREDS_JSON:
        print("❌ 에러: GOOGLE_SHEETS_CREDENTIALS 환경 변수가 설정되지 않았습니다.")
        return

    # 서버 실행 경로 설정
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    server_script_path = os.path.join(BASE_DIR, "mcp-google-sheets", "index.ts")

    # MCP 서버 실행 파라미터
    # credentials.json 파일 대신 환경 변수에 저장된 JSON 문자열을 직접 넘깁니다.
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
            print(f"🚀 [Render 서버 가동] 시트 감시 중... (ID: {SPREADSHEET_ID[:10]}...)")

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
                            print(f"🔍 {actual_row}행 단어 '{word}' 처리 중...")

                            ai_result = await get_gemini_info(word)

                            await session.call_tool("update_sheet", arguments={
                                "spreadsheetId": SPREADSHEET_ID,
                                "range": f"시트1!B{actual_row}:G{actual_row}",
                                "values": [[
                                    ai_result[0], 
                                    ai_result[1], 
                                    ai_result[2], 
                                    "", "", 
                                    f"✅ {actual_row}행 완료"
                                ]]
                            })
                    
                    # 무료 티어 및 API 할당량을 고려하여 대기 시간을 넉넉히 둡니다.
                    await asyncio.sleep(10)

                except Exception as e:
                    print(f"⚠️ 루프 알림: {e}")
                    await asyncio.sleep(20)

if __name__ == "__main__":
    asyncio.run(run_mcp_server())