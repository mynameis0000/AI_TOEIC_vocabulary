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
        # 모델은 안정적인 gemini-1.5-flash 권장
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
        
        # 여러 단어를 하나의 프롬프트로 묶음 (토큰 절약 핵심)
        word_list_str = ", ".join(words)
        prompt = f"""
다음 단어들의 [뜻 | 품사 | 예문]을 작성해줘.
각 단어는 반드시 줄바꿈(Enter)으로 구분하고, 설명 없이 형식만 맞춰서 답해줘.

단어 목록: {word_list_str}
"""

        data = {
            "contents": [{"parts": [{"text": prompt}]}]
        }

        response = requests.post(url, json=data)
        if response.status_code != 200:
            return None

        result = response.json()
        full_text = result["candidates"][0]["content"]["parts"][0]["text"]
        
        # AI 응답을 줄 단위로 쪼개서 리스트로 반환
        return [line.strip() for line in full_text.strip().split('\n') if "|" in line]

    except Exception as e:
        logger.error(f"AI Error: {str(e)}")
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