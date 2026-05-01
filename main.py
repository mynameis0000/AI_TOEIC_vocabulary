import asyncio
import os
import random
import traceback
import json
import re
import google.generativeai as genai
from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from google.generativeai.types import HarmCategory, HarmBlockThreshold

# 1. 환경 변수 및 API 설정
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
MY_SPREADSHEET_ID = os.getenv("MY_SPREADSHEET_ID")

if not GEMINI_API_KEY or not MY_SPREADSHEET_ID:
    print("❌ .env 파일에 GEMINI_API_KEY와 MY_SPREADSHEET_ID를 설정해주세요.")
    exit()

genai.configure(api_key=GEMINI_API_KEY)

# 현재 파일(main.py)이 위치한 디렉토리를 기준으로 경로 설정 (서버 배포용)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

safety_settings = {
    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
}

# AI 인스트럭션: 단어 검증 로직 강화
instruction_save = """너는 영단어 DB 생성기야. 
입력된 단어가 실존하는 영단어인 경우에만 '뜻 | 품사 | 토익 빈출 예문' 형식으로 출력해.
만약 존재하지 않는 단어이거나 의미 없는 철자 조합이라면 무조건 'ERROR'라고만 출력해.
인사말 없이 결과만 출력해."""

model = genai.GenerativeModel('models/gemini-flash-latest')

def is_valid_input(word):
    """기본 문자열 검증 (한글 자음/모음 차단 및 길이 체크)"""
    if not word or len(word.strip()) < 2: return False
    if re.search("[ㄱ-ㅎㅏ-ㅣ가-힣]", word): return False
    return True

async def run_mcp_client():
    # 서버 환경에 대응하는 상대 경로 설정
    credentials_path = os.path.join(BASE_DIR, "credentials.json")
    server_script_path = os.path.join(BASE_DIR, "mcp-google-sheets", "index.ts")

    with open(credentials_path, "r", encoding="utf-8") as f:
        creds_json = f.read()

    # 서버에서는 'bun'이 환경 변수에 등록되어 있다고 가정합니다.
    server_params = StdioServerParameters(
        command="bun", 
        args=["run", "--silent", server_script_path],
        env={"GOOGLE_SHEETS_CREDENTIALS": creds_json, **os.environ}
    )

    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                
                print("\n✨ [영단어 마스터 v4.8 - 서버 통합 버전] ✨")

                # [초기화] 시트 헤더 작성 (A1:D1)
                await session.call_tool("update_sheet", arguments={
                    "spreadsheetId": MY_SPREADSHEET_ID,
                    "range": "시트1!A1:D1",
                    "values": [["단어", "뜻", "품사", "예문"]]
                })
                
                while True:
                    print("\n" + "="*45)
                    print("1. 단어 추가 (DB 누적 저장)")
                    print("2. 문장 해석 퀴즈 (AI 채점)")
                    print("0. 프로그램 종료")
                    choice = input("\n모드 선택: ")

                    if choice == "1":
                        while True:
                            word = input("\n🔍 추가할 영단어 (메뉴는 'q'): ").strip()
                            if word.lower() == 'q': break
                            if not is_valid_input(word):
                                print("⚠️ 유효한 영단어를 입력하세요 (2글자 이상, 영문 전용).")
                                continue

                            print(f"📡 AI 검증 중: {word}...")
                            save_model = genai.GenerativeModel('models/gemini-flash-latest', system_instruction=instruction_save)
                            response = save_model.generate_content(word)
                            raw_res = response.text.strip()
                            
                            if "ERROR" in raw_res or "|" not in raw_res:
                                print(f"❌ '{word}'은(는) 존재하지 않거나 유효하지 않은 단어입니다.")
                                continue

                            try:
                                parsed = [item.strip() for item in raw_res.split('|')]
                                meaning, pos, example = (parsed + ["-", "-", "-"])[:3]

                                # 현재 저장된 행 개수 확인하여 다음 행 번호 계산
                                sheet_info = await session.call_tool("read_sheet", arguments={
                                    "spreadsheetId": MY_SPREADSHEET_ID, "range": "시트1!A:A"
                                })
                                raw_data = json.loads(sheet_info.content[0].text)
                                current_rows = raw_data if isinstance(raw_data, list) else raw_data.get("values", [])
                                next_row_num = len(current_rows) + 1

                                # 데이터 저장
                                await session.call_tool("update_sheet", arguments={
                                    "spreadsheetId": MY_SPREADSHEET_ID,
                                    "range": f"시트1!A{next_row_num}:D{next_row_num}",
                                    "values": [[word, meaning, pos, example]]
                                })
                                print(f"✅ {next_row_num}행에 저장 완료: {word} ({meaning})")
                            except: 
                                print("⚠️ 데이터 처리 중 오류 발생")

                    elif choice == "2":
                        while True:
                            print("\n📚 DB 로드 중...")
                            sheet_data = await session.call_tool("read_sheet", arguments={
                                "spreadsheetId": MY_SPREADSHEET_ID, "range": "시트1!A2:D"
                            })
                            
                            try:
                                raw_content = sheet_data.content[0].text
                                data_json = json.loads(raw_content)
                                rows = data_json if isinstance(data_json, list) else data_json.get("values", [])
                                valid_rows = [r for r in rows if len(r) >= 4 and r[0].strip() and r[3].strip()]
                            except: valid_rows = []

                            if not valid_rows:
                                print("❌ 퀴즈 데이터가 부족합니다 (2행부터 확인)."); break
                                
                            quiz_row = random.choice(valid_rows)
                            q_word, q_mean, q_pos, q_ex = quiz_row[0], quiz_row[1], quiz_row[2], quiz_row[3]

                            print(f"\n" + "-"*40)
                            print(f"📝 해석해 보세요! (핵심: {q_word} [{q_pos}])")
                            print(f"👉 {q_ex}")
                            print("-" * 40)
                            
                            u_ans = input("내 해석 (메뉴는 'q'): ").strip()
                            if u_ans.lower() == 'q': break

                            prompt = f"영문: {q_ex}\n단어: {q_word}({q_mean})\n학생해석: {u_ans}\n\n[지침: 1.정확도(%), 2.본래뜻, 3.학습포인트(1문장)만 출력]"
                            
                            print("📢 AI 채점 중...")
                            score_res = model.generate_content(prompt, safety_settings=safety_settings)
                            print(f"\n🤖 AI 피드백:\n{score_res.text.strip()}")

                    elif choice == "0":
                        print("👋 프로그램을 종료합니다.")
                        return

    except Exception:
        print(f"\n🔥 에러 발생:\n{traceback.format_exc()}")

if __name__ == "__main__":
    asyncio.run(run_mcp_client())