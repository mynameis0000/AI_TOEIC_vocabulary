#gemini-2.5-flash사용하고 있었음

import os
import json
import logging
import requests
import gspread

from flask import Flask, request, jsonify
from dotenv import load_dotenv
from google.oauth2.service_account import Credentials

import time # 속도 조절을 위한 추가

# 라이브러리 임포트 아래에 위치해야 합니다.
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__) # <-- logger 정의

app = Flask(__name__) # <-- app 정의


def get_batch_ai_response(words):
    try:
        api_key = os.getenv("GEMINI_API_KEY")
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"

        word_list_str = ", ".join(words)
        
        # 지시 사항을 더 구체적이고 엄격하게 수정
        prompt = f"""
Input Words: {word_list_str}

각 단어에 대해 아래 규칙을 엄격히 지켜서 [뜻 | 품사 | 예문]을 작성해:

1. 형식: 뜻 | 품사 | 영어 예문 (대괄호 '[]' 절대 사용 금지)
2. 예문: 반드시 '영어'로만 작성하고 한글 해석은 포함하지 마.
3. 중복 방지: 
   - 뜻이 여러 개라면 가장 중요한 것 최대 2개만 요약해서 적어.
   - 품사는 '동사', '명사', '형용사' 등 한국어로 적되, 뜻이 2개라면 '동사(2개)' 또는 '동사, 명사'와 같이 표시해.
4. 구분: 각 단어는 반드시 줄바꿈(Enter)으로 구분해.

출력 예시:
사과 | 명사 | I ate an apple.
달리다 | 동사 | I run fast.
"""

        data = {
            "contents": [{"parts": [{"text": prompt}]}]
        }

        response = requests.post(url, json=data, timeout=15)
        
        if response.status_code != 200:
            logger.error(f"API Error: {response.text}")
            return None

        result = response.json()
        full_text = result["candidates"][0]["content"]["parts"][0]["text"]
        
        # [ ] 대괄호가 혹시라도 포함되면 강제로 제거하는 안전장치
        clean_text = full_text.replace("[", "").replace("]", "")
        
        lines = [line.strip() for line in clean_text.strip().split('\n') if "|" in line]
        return lines

    except Exception as e:
        logger.error(f"AI Connection Exception: {str(e)}")
        return None


@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        data = request.get_json()
        words = data.get("words") # 단어 '리스트' 수신
        spreadsheet_id = data.get("spreadsheetId")
        row_indices = data.get("rowIndices") # 행 번호 '리스트' 수신

        if not words or not spreadsheet_id:
            return jsonify({"error": "Missing data"}), 400

        # 1. AI 분석 수행 (한 번의 호출로 여러 단어 처리)
        ai_results = get_batch_ai_response(words)
        
        if not ai_results or len(ai_results) == 0:
            return jsonify({"error": "AI 분석 실패"}), 500

        # 2. 구글 시트 인증 및 연결 (기존 로직 동일)
        creds_raw = os.getenv("GOOGLE_SHEETS_CREDENTIALS")
        creds_info = json.loads(creds_raw)
        creds = Credentials.from_service_account_info(creds_info, scopes=["https://www.googleapis.com/auth/spreadsheets"])
        gc = gspread.authorize(creds)
        sh = gc.open_by_key(spreadsheet_id)
        worksheet = sh.get_worksheet(0) # 첫 번째 시트 선택

        # 3. 결과 업데이트 (반복문을 돌며 각 행에 기록)
        for i in range(len(words)):
            if i < len(ai_results):
                parts = [p.strip() for p in ai_results[i].split("|")]
                if len(parts) >= 3:
                    # B, C, D열에 한꺼번에 업데이트
                    worksheet.update(f"B{row_indices[i]}:D{row_indices[i]}", [[parts[0], parts[1], parts[2]]])
            
            # API 할당량 초과 방지를 위한 미세한 지연 (선택 사항)
            time.sleep(0.2)

        return jsonify({"status": "success", "count": len(ai_results)}), 200

    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return jsonify({"error": str(e)}), 500