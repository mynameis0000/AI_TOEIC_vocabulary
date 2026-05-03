import asyncio
import os
import json
import random
import traceback
from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import core # core.py 모듈 임포트

# 환경 설정
load_dotenv()
MY_SPREADSHEET_ID = os.getenv("MY_SPREADSHEET_ID")
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

async def run_mcp_server():
    credentials_path = os.path.join(BASE_DIR, "credentials.json")
    server_script_path = os.path.join(BASE_DIR, "mcp-google-sheets", "index.ts")

    with open(credentials_path, "r", encoding="utf-8") as f:
        creds_json = f.read()

    server_params = StdioServerParameters(
        command="bun", 
        args=["run", "--silent", server_script_path],
        env={"GOOGLE_SHEETS_CREDENTIALS": creds_json, **os.environ}
    )

    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                
                # 1. 시트 초기화 및 헤더 작성
                await session.call_tool("update_sheet", arguments={
                    "spreadsheetId": MY_SPREADSHEET_ID,
                    "range": "시트1!A1:G1",
                    "values": [["단어", "뜻", "품사", "예문", "", "입력창(F2)", "출력창(G2)"]]
                })
                print("🚀 [서버 가동] 시트 감시를 시작합니다...")

                last_processed_input = ""

                while True:
                    # 2. 사용자 입력 감시 (F2 셀)
                    ui_data = await session.call_tool("read_sheet", arguments={
                        "spreadsheetId": MY_SPREADSHEET_ID, "range": "시트1!F2:F2"
                    })
                    raw_ui = json.loads(ui_data.content[0].text)
                    
                    try:
                        values = raw_ui if isinstance(raw_ui, list) else raw_ui.get("values", [])
                        current_input = values[0][0].strip() if values else ""
                    except: current_input = ""

                    # 3. 새로운 입력이 있을 경우 처리
                    if current_input and current_input != last_processed_input:
                        print(f"📩 새 입력 감지: {current_input}")
                        result_msg = ""

                        # [모드 1: 단어 추가] - 영문만 입력 시
                        if core.is_valid_input(current_input):
                            word_data = await core.get_gemini_word_data(current_input)
                            if word_data:
                                # 행 개수 확인
                                sheet_info = await session.call_tool("read_sheet", arguments={
                                    "spreadsheetId": MY_SPREADSHEET_ID, "range": "시트1!A:A"
                                })
                                rows_info = json.loads(sheet_info.content[0].text)
                                rows = rows_info if isinstance(rows_info, list) else rows_info.get("values", [])
                                next_row = len(rows) + 1
                                
                                # DB 저장
                                await session.call_tool("update_sheet", arguments={
                                    "spreadsheetId": MY_SPREADSHEET_ID,
                                    "range": f"시트1!A{next_row}:D{next_row}",
                                    "values": [[current_input] + word_data]
                                })
                                result_msg = f"✅ {next_row}행 저장 완료: {current_input}"
                            else:
                                result_msg = f"❌ '{current_input}'은 유효하지 않습니다."

                        # [모드 2: 퀴즈 분석] - 한글 포함 시(해석 답안)
                        else:
                            # DB에서 랜덤 추출
                            db_data = await session.call_tool("read_sheet", arguments={
                                "spreadsheetId": MY_SPREADSHEET_ID, "range": "시트1!A2:D"
                            })
                            db_json = json.loads(db_data.content[0].text)
                            rows = db_json if isinstance(db_json, list) else db_json.get("values", [])
                            valid_rows = [r for r in rows if len(r) >= 4]
                            
                            if valid_rows:
                                q = random.choice(valid_rows)
                                result_msg = await core.get_quiz_feedback(q[3], q[0], q[1], current_input)
                            else:
                                result_msg = "❌ DB에 퀴즈 데이터가 없습니다."

                        # 4. 결과 출력 (G2 셀)
                        await session.call_tool("update_sheet", arguments={
                            "spreadsheetId": MY_SPREADSHEET_ID, "range": "시트1!G2:G2",
                            "values": [[result_msg]]
                        })
                        last_processed_input = current_input

                    await asyncio.sleep(5) # 5초 대기 (API 할당량 관리)

    except Exception:
        print(f"🔥 서버 에러 발생:\n{traceback.format_exc()}")

if __name__ == "__main__":
    asyncio.run(run_mcp_server())