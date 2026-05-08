import os
import json
import logging
import requests

from flask import Flask, request, jsonify
import gspread
from google.oauth2.service_account import Credentials

# 로그 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Gemini API 호출 함수
def get_ai_response(word):
    try:
        api_key = os.environ.get("GEMINI_API_KEY")

        if not api_key:
            logger.error("GEMINI_API_KEY missing")
            return "API KEY 오류"

        url = (
            f"https://generativelanguage.googleapis.com/v1/models/"
            f"gemini-1.5-flash:generateContent?key={api_key}"
        )

        headers = {
            "Content-Type": "application/json"
        }

        prompt = f"""
영단어: {word}

다음을 출력해줘.

1. 한국어 뜻
2. 영어 예문
3. 예문 해석

형식:
뜻:
예문:
해석:
"""

        data = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": prompt
                        }
                    ]
                }
            ]
        }

        response = requests.post(
            url,
            headers=headers,
            json=data,
            timeout=30
        )

        logger.info(f"Gemini Status: {response.status_code}")
        logger.info(response.text)

        if response.status_code != 200:
            return f"API 오류: {response.text}"

        result = response.json()

        # 응답 구조 검증
        if "candidates" not in result:
            logger.error(f"Invalid response: {result}")
            return "응답 형식 오류"

        return result["candidates"][0]["content"]["parts"][0]["text"]

    except Exception as e:
        logger.error(f"Gemini Error: {str(e)}")
        return "AI 분석 오류"


@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        # 데이터 수신
        data = request.get_json()

        if not data:
            return jsonify({"error": "No JSON data"}), 400

        word = data.get('word')
        spreadsheet_id = data.get('spreadsheetId')
        row_index = data.get('rowIndex')

        logger.info(
            f"데이터 수신: {word}, "
            f"ID: {spreadsheet_id}, "
            f"Row: {row_index}"
        )

        # 필수값 검증
        if not all([word, spreadsheet_id, row_index]):
            return jsonify({"error": "Missing data"}), 400

        # row_index 숫자 변환
        row_index = int(row_index)

        # 구글 인증 정보 가져오기
        creds_raw = os.environ.get('GOOGLE_SHEETS_CREDENTIALS')

        if not creds_raw:
            logger.error("GOOGLE_SHEETS_CREDENTIALS missing")
            return jsonify({"error": "Auth config missing"}), 500

        creds_info = json.loads(creds_raw)

        scopes = [
            'https://www.googleapis.com/auth/spreadsheets'
        ]

        creds = Credentials.from_service_account_info(
            creds_info,
            scopes=scopes
        )

        gc = gspread.authorize(creds)

        # 스프레드시트 열기
        sh = gc.open_by_key(spreadsheet_id)

        # 시트 찾기
        try:
            worksheet = sh.worksheet("시트1")
        except gspread.exceptions.WorksheetNotFound:
            logger.warning(
                "'시트1'을 찾지 못해 첫 번째 시트를 사용합니다."
            )
            worksheet = sh.get_worksheet(0)

        # AI 응답 생성
        result = get_ai_response(word)

        # B열 업데이트
        worksheet.update_cell(row_index, 2, result)

        logger.info(f"업데이트 성공: {word} -> {result}")

        return jsonify({
            "status": "success",
            "result": result
        }), 200

    except Exception as e:
        logger.error(f"Server Error: {str(e)}")

        return jsonify({
            "error": str(e)
        }), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))

    app.run(
        host="0.0.0.0",
        port=port
    )