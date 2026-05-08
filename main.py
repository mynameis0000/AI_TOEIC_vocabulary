import os
import json
import logging
import requests
import gspread

from flask import Flask, request, jsonify
from dotenv import load_dotenv
from google.oauth2.service_account import Credentials

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)


def get_ai_response(word):

    try:
        api_key = os.getenv("GEMINI_API_KEY")

        url = (
            "https://generativelanguage.googleapis.com/"
            f"v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
        )

        headers = {
            "Content-Type": "application/json"
        }

        prompt = f"""
입력 단어: {word}

반드시 아래 형식으로만 답변:

뜻 | 품사 | 짧은 영어 예문

예시:
사과 | 명사 | I ate an apple.

설명 금지.
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
            json=data
        )

        if response.status_code != 200:
            logger.error(response.text)
            return None

        result = response.json()

        text = result["candidates"][0]["content"]["parts"][0]["text"]

        return text.strip()

    except Exception as e:
        logger.error(f"AI Error: {str(e)}")
        return None


@app.route("/webhook", methods=["POST"])
def webhook():

    try:
        data = request.get_json()

        word = data.get("word")
        spreadsheet_id = data.get("spreadsheetId")
        row_index = data.get("rowIndex")

        logger.info(f"Received word: {word}")

        if not all([word, spreadsheet_id, row_index]):
            return jsonify({
                "error": "Missing data"
            }), 400

        # Google Sheets 인증
        creds_raw = os.getenv("GOOGLE_SHEETS_CREDENTIALS")

        creds_info = json.loads(creds_raw)

        scopes = [
            "https://www.googleapis.com/auth/spreadsheets"
        ]

        creds = Credentials.from_service_account_info(
            creds_info,
            scopes=scopes
        )

        gc = gspread.authorize(creds)

        sh = gc.open_by_key(spreadsheet_id)

        try:
            worksheet = sh.worksheet("시트1")

        except:
            worksheet = sh.get_worksheet(0)

        # Gemini 분석
        ai_result = get_ai_response(word)

        if not ai_result:
            return jsonify({
                "error": "AI failed"
            }), 500

        # 결과 분리
        parts = [p.strip() for p in ai_result.split("|")]

        meaning = parts[0] if len(parts) > 0 else "-"
        pos = parts[1] if len(parts) > 1 else "-"
        example = parts[2] if len(parts) > 2 else "-"

        # B/C/D열 저장
        worksheet.update(
            f"B{row_index}:D{row_index}",
            [[meaning, pos, example]]
        )

        logger.info(f"Updated row {row_index}")

        return jsonify({
            "status": "success"
        }), 200

    except Exception as e:

        logger.error(str(e))

        return jsonify({
            "error": str(e)
        }), 500


if __name__ == "__main__":

    port = int(os.environ.get("PORT", 5000))

    app.run(
        host="0.0.0.0",
        port=port
    )