import os
import json
import logging
from flask import Flask, request, jsonify
import google.generativeai as genai
import gspread
from google.oauth2.service_account import Credentials
from google.generativeai import client

# 로그 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

def get_ai_response(word):
    try:
        # 함수 안에서 매번 설정을 초기화하여 충돌을 피합니다.
        api_key = os.environ.get("GEMINI_API_KEY")
        genai.configure(api_key=api_key)
        
        # 가장 호환성이 좋은 기본 모델명 사용
        model = genai.GenerativeModel('gemini-pro') 
        
        response = model.generate_content(f"{word} 뜻과 예문")
        return response.text
    except Exception as e:
        # 에러가 나면 정확히 어떤 라이브러리 단계에서 나는지 로그를 찍습니다.
        print(f"DEBUG ERROR: {str(e)}")
        return f"분석 에러"

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        # 데이터 수신
        data = request.get_json()
        word = data.get('word')
        spreadsheet_id = data.get('spreadsheetId')
        row_index = data.get('rowIndex')

        logger.info(f"데이터 수신: {word}, ID: {spreadsheet_id}, Row: {row_index}")

        if not all([word, spreadsheet_id, row_index]):
            return jsonify({"error": "Missing data"}), 400

        # 구글 인증
        creds_raw = os.environ.get('GOOGLE_SHEETS_CREDENTIALS')
        if not creds_raw:
            logger.error("GOOGLE_SHEETS_CREDENTIALS Env Var missing")
            return jsonify({"error": "Auth config missing"}), 500
            
        creds_info = json.loads(creds_raw)
        scopes = ['https://www.googleapis.com/auth/spreadsheets']
        creds = Credentials.from_service_account_info(creds_info, scopes=scopes)
        client = gspread.authorize(creds)
        
        # 시트 열기 및 업데이트
        sh = client.open_by_key(spreadsheet_id)
        try:
            worksheet = sh.worksheet("시트1")
        except gspread.exceptions.WorksheetNotFound:
            logger.warning("'시트1'을 찾지 못해 첫 번째 시트를 사용합니다.")
            worksheet = sh.get_worksheet(0)
        
        # AI 결과 생성
        result = get_ai_response(word)
        
        # B열(2번) 업데이트
        worksheet.update_cell(row_index, 2, result)
        
        logger.info(f"업데이트 성공: {word} -> {result}")
        return jsonify({"status": "success", "result": result}), 200

    except Exception as e:
        logger.error(f"Server Error: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

    # FORCE UPDATE: 2026-05-08-01