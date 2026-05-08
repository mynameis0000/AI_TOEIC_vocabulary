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


# 홈 테스트용
@app.route('/')
def home():
    return "Server Running"


# Gemini API 호출 함수
def get_ai_response(word):

    try:
        api_key = os.environ.get("GEMINI_API_KEY")

        if not api_key:
            logger.error("API KEY missing")
            return "API KEY 오류"

        url = (
            "https://generativelanguage.googleapis.com/"
            f"v1beta/models/gemini-pro:generateContent?key={api_key}"
        )

        headers = {
            "Content-Type": "application/json"
        }

        data = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": f"{word} 뜻과 예문을 알려줘"
                        }
                    ]
                }
            ]
        }

        # response 반드시 여기서 생성
        response = requests.post(
            url,
            headers=headers,
            json=data,
            timeout=30
        )

        logger.info(f"Gemini Status: {response.status_code}")
        logger.info(response.text)

        # quota 초과 처리
        if response.status_code == 429:
            return "API 사용량 초과. 잠시 후 다시 시도해주세요."

        # 일반 오류 처리
        if response.status_code != 200:
            return f"API 오류: {response.text}"

        result = response.json()

        # 응답 구조 검사
        if "candidates" not in result:
            return "AI 응답 형식 오류"

        return result["candidates"][0]["content"]["parts"][0]["text"]

    except Exception as e:

        logger.error(f"AI Error: {str(e)}")

        return "AI 분석 오류"


# Webhook 엔드포인트
@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        data = request.get_json()

        if not data:
            return jsonify({
                "error": "No JSON data"
            }), 400

        word = data.get('word')
        spreadsheet_id = data.get('spreadsheetId')
        row_index = data.get('rowIndex')

        logger.info(
            f"Received: {word}, "
            f"Spreadsheet: {spreadsheet_id}, "
            f"Row: {row_index}"
        )

        # 필수 데이터 체크
        if not all([word, spreadsheet_id, row_index]):
            return jsonify({
                "error": "Missing data"
            }), 400

        # row_index 숫자 변환
        row_index = int(row_index)

        # Google Sheets 인증 정보
        creds_raw = os.environ.get(
            'GOOGLE_SHEETS_CREDENTIALS'
        )

        if not creds_raw:
            logger.error(
                "GOOGLE_SHEETS_CREDENTIALS missing"
            )

            return jsonify({
                "error": "Auth config missing"
            }), 500

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
                "'시트1' 없음 → 첫 번째 시트 사용"
            )

            worksheet = sh.get_worksheet(0)

        # AI 결과 생성
        result = get_ai_response(word)

        # B열 업데이트
        worksheet.update_cell(row_index, 2, result)

        logger.info(
            f"Success: {word} updated at row {row_index}"
        )

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

    port = int(
        os.environ.get("PORT", 10000)
    )

    app.run(
        host="0.0.0.0",
        port=port
    )