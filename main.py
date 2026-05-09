#gemini-2.5-flash사용하고 있었음

import time # 속도 조절을 위한 추가

import os
import json
import logging
import requests
import gspread
import time

from flask import Flask, request, jsonify
from dotenv import load_dotenv
from google.oauth2.service_account import Credentials

# .env 파일 로드 (로컬 환경용)
load_dotenv()

# 로그 설정: 서버의 상태를 Render 로그에서 확인할 수 있게 함
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

def get_batch_ai_response(words):
    """Gemini API를 사용하여 여러 단어를 한꺼번에 분석 (토큰 및 비용 절약)"""
    try:
        api_key = os.getenv("GEMINI_API_KEY")
        # 모델명은 반드시 gemini-1.5-flash를 사용 (무료 티어 권장 모델)
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"

        word_list_str = ", ".join(words)
        
        # AI 지시문 (프롬프트): 한국어 뜻, 영어 예문, 대괄호 제거, 품사 형식 지정
        prompt = f"""
Input Words: {word_list_str}

각 단어에 대해 아래 규칙을 '절대적'으로 지켜서 [뜻 | 품사 | 예문]을 작성해:

1. **뜻 (Meaning)**: 반드시 **한국어(KOREAN)**로만 작성해. 영어를 섞지 마.
   - 뜻이 여러 개라면 가장 중요한 것 최대 2개만 요약해 (예: '달리다, 운영하다').
2. **품사 (POS)**: 한국어로 작성해 (예: '명사', '동사', '동사, 명사'). 
   - 뜻이 2개 이상이면 '동사(2개)' 처럼 표시해.
3. **예문 (Example)**: 반드시 **영어(ENGLISH)**로만 작성해. 한글 해석은 절대 넣지 마.
4. **형식**: '뜻 | 품사 | 예문' 형식을 유지하고, 각 단어는 줄바꿈으로 구분해.
5. **금지**: 대괄호 '[]', 따옴표, 또는 서론/결론 설명을 절대 포함하지 마.

출력 예시:
사과 | 명사 | I ate an apple.
"""

        data = {
            "contents": [{"parts": [{"text": prompt}]}]
        }

        # API 호출 (타임아웃 15초 설정)
        response = requests.post(url, json=data, timeout=15)
        
        if response.status_code != 200:
            logger.error(f"Gemini API 에러: {response.status_code} - {response.text}")
            return None

        result = response.json()
        
        if "candidates" not in result:
            logger.error(f"잘못된 API 응답 구조: {result}")
            return None
            
        full_text = result["candidates"][0]["content"]["parts"][0]["text"]
        
        # 1. 대괄호 및 불필요한 기호 강제 제거
        clean_text = full_text.replace("[", "").replace("]", "").replace("`", "")
        
        # 2. 줄 단위로 나누고 '|' 구분자가 포함된 유효한 행만 추출
        lines = [line.strip() for line in clean_text.strip().split('\n') if "|" in line]
        
        logger.info(f"AI 분석 완료: {len(lines)}개 단어 처리됨")
        return lines

    except Exception as e:
        logger.error(f"AI 처리 중 예외 발생: {str(e)}")
        return None

@app.route("/webhook", methods=["POST"])
def webhook():
    """Google Apps Script의 요청을 받는 엔드포인트"""
    try:
        data = request.get_json()
        words = data.get("words") 
        row_indices = data.get("rowIndices") 
        spreadsheet_id = data.get("spreadsheetId")

        if not words or not spreadsheet_id:
            return jsonify({"error": "데이터 누락"}), 400

        # 1. AI 분석 수행
        ai_results = get_batch_ai_response(words)
        
        if not ai_results:
            return jsonify({"error": "AI 분석 실패"}), 500

        # 2. 구글 시트 인증 및 연결
        creds_raw = os.getenv("GOOGLE_SHEETS_CREDENTIALS")
        creds_info = json.loads(creds_raw)
        creds = Credentials.from_service_account_info(
            creds_info, 
            scopes=["https://www.googleapis.com/auth/spreadsheets"]
        )
        gc = gspread.authorize(creds)
        sh = gc.open_by_key(spreadsheet_id)
        
        # 시트 이름이 "시트1"이 아닐 경우를 대비해 첫 번째 워크시트 가져오기
        try:
            worksheet = sh.get_worksheet(0)
        except Exception as e:
            logger.error(f"시트를 찾을 수 없음: {str(e)}")
            return jsonify({"error": "시트 연결 실패"}), 500

        # 3. 결과 업데이트 (각 단어의 원래 행 위치에 기록)
        for i in range(len(words)):
            if i < len(ai_results):
                parts = [p.strip() for p in ai_results[i].split("|")]
                if len(parts) >= 3:
                    # B, C, D열에 뜻, 품사, 예문을 한꺼번에 업데이트
                    range_label = f"B{row_indices[i]}:D{row_indices[i]}"
                    values = [[parts[0], parts[1], parts[2]]]
                    worksheet.update(values, range_label)
            
            # 구글 시트 API 할당량(Quota) 초과 방지를 위한 짧은 지연
            time.sleep(0.2)

        return jsonify({"status": "success", "processed_count": len(ai_results)}), 200

    except Exception as e:
        logger.error(f"서버 내부 에러: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    # Render 환경의 포트 설정 대응
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)