import os
import json
import logging
import requests

from flask import Flask, request, jsonify
import gspread
from google.oauth2.service_account import Credentials

# 로그 설정 (Render 대시보드에서 확인 가능)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

def get_ai_response(word):
    """Gemini API를 사용하여 단어의 뜻과 예문 생성"""
    try:
        genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
        model = genai.GenerativeModel('gemini-1.5-flash') # 안정적인 최신 모델
        prompt = f"영어 단어 '{word}'의 뜻과 예문을 한국어로 아주 짧게 알려줘. 형식: 뜻 / 예문"
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        logger.error(f"AI Error: {str(e)}")
        return "AI 분석 실패"

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        # 1. Apps Script에서 보낸 데이터 수신
        data = request.get_json()
        word = data.get('word')
        spreadsheet_id = data.get('spreadsheetId')
        row_index = data.get('rowIndex')

        if not all([word, spreadsheet_id, row_index]):
            return jsonify({"error": "Missing data"}), 400

        # 2. 구글 서비스 계정 인증 (환경 변수)
        creds_raw = os.environ.get('GOOGLE_SHEETS_CREDENTIALS')
        if not creds_raw:
            return jsonify({"error": "Credentials not found"}), 500
            
        creds_info = json.loads(creds_raw)
        scopes = ['https://www.googleapis.com/auth/spreadsheets']
        creds = Credentials.from_service_account_info(creds_info, scopes=scopes)
        client = gspread.authorize(creds)
        
        # 3. 구글 시트 연결 및 기록
        sh = client.open_by_key(spreadsheet_id)
        worksheet = sh.worksheet("시트1") # 시트 이름이 다르면 수정하세요
        
        # AI 결과 생성 및 업데이트
        result = get_ai_response(word)
        worksheet.update_cell(row_index, 2, result) # B열(2열)에 기록
        
        logger.info(f"Success: {word} updated at row {row_index}")
        return jsonify({"status": "success"}), 200

    except Exception as e:
        logger.error(f"Server Error: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)