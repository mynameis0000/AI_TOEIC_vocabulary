import asyncio
import os
import json
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from dotenv import load_dotenv

load_dotenv()

async def test_connection():
    # credentials.json 위치 확인
    base_dir = os.path.dirname(os.path.abspath(__file__))
    creds_path = os.path.join(base_dir, "credentials.json")
    
    if not os.path.exists(creds_path):
        print("❌ 에러: credentials.json 파일이 없습니다. GCP에서 다운로드 후 배치해 주세요.")
        return

    with open(creds_path, "r", encoding="utf-8") as f:
        creds_json = f.read()

    # MCP 서버 매개변수 설정
    server_params = StdioServerParameters(
        command="bun", 
        args=["run", "--silent", os.path.join(base_dir, "mcp-google-sheets", "index.ts")],
        env={"GOOGLE_SHEETS_CREDENTIALS": creds_json, **os.environ}
    )

    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                # 시트 메타데이터 읽기 시도
                result = await session.call_tool("read_sheet", arguments={
                    "spreadsheetId": os.getenv("MY_SPREADSHEET_ID"),
                    "range": "시트1!A1:A1"
                })
                print("✅ 서버 연결 성공! 구글 시트 데이터를 성공적으로 읽어왔습니다.")
    except Exception as e:
        print(f"❌ 연결 실패: {e}")

if __name__ == "__main__":
    asyncio.run(test_connection())